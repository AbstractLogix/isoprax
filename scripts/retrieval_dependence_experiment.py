"""Run the pre-registered synthetic retrieval/interpretation pilot.

This runner uses local prompted selectors as bounded proxies. It does not
reproduce UNREAL, expose a retrieval product, or establish field performance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable, Sequence

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
PREREGISTRATION = ROOT / "specs/047-retrieval-selection-dependence/preregistration.json"
MODEL_X = "qwen3.5:9b"
MODEL_Y = "gemma4:e2b"
MODEL_DIGESTS = {
    MODEL_X: "6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7",
    MODEL_Y: "7fbdbf8f5e45a75bb122155ed546e765b4d9c53a1285f62fd9f506baa1c5a47e",
}
SEED = 47047
MODEL_SEED = 47048
BOOTSTRAP_SEED = 47049
BOOTSTRAP_REPLICATES = 2_000
NUM_PREDICT = 512
PROMPT_VERSION = "retrieval-dependence-prompt-v2"
MODEL_SERVER_VERSION = "0.20.4"
BUDGETS = (1, 2, 4, 8, 16)
PAIR_BUDGETS = (2, 4, 8, 16)
STRATA = (
    "clean",
    "misleading",
    "duplicate_shared_upstream",
    "conflicting",
    "unknown_source_status",
    "wrong_initial_hypothesis",
)
CAUSES = (
    "bearing_wear",
    "lubrication_loss",
    "sensor_fault",
    "normal_operation",
)
CONDITIONS = {
    "A": {"selector": "BM25", "selector_model": "BM25-v1", "interpreter": MODEL_X},
    "B": {
        "selector": "prompted_model_y",
        "selector_model": MODEL_Y,
        "interpreter": MODEL_X,
    },
    "C": {
        "selector": "prompted_model_x",
        "selector_model": MODEL_X,
        "interpreter": MODEL_X,
    },
    "D": {
        "selector": "prompted_model_x",
        "selector_model": MODEL_X,
        "interpreter": MODEL_Y,
    },
}

CAUSE_TEXT = {
    "bearing_wear": (
        "Teardown found abrasive pitting on the drive-end bearing race. Replacing that "
        "bearing removed the vibration at the next inspection.",
        "A repeat inspection found spalling on the same bearing surface and elevated "
        "bearing-frequency vibration on a calibrated reference instrument.",
    ),
    "lubrication_loss": (
        "The lubricant reservoir was below its minimum mark and the pump inlet was dry. "
        "Restoring the specified lubricant stopped the temperature rise.",
        "A maintenance sample confirmed lubricant starvation at the affected housing; "
        "the replenishment record matches the measured temperature recovery.",
    ),
    "sensor_fault": (
        "A certified external instrument showed normal shaft motion. The installed "
        "accelerometer had a cracked cable that produced the reported spikes.",
        "A bench check reproduced the vibration alarm by flexing the damaged sensor lead; "
        "a separate reference sensor remained within baseline.",
    ),
    "normal_operation": (
        "Independent inspection found no damage or overheating. The measured vibration "
        "matched this unit's documented normal operating baseline.",
        "A second calibrated survey confirmed normal operation under the same load and "
        "found no abnormal vibration or temperature.",
    ),
}

DISTRACTION_TEXT = {
    "bearing_wear": "A nearby bearing on a different unit had visible wear during last month's service.",
    "lubrication_loss": "An unrelated service log mentions a low lubricant warning on another unit.",
    "sensor_fault": "A spare sensor from another unit failed a bench test after this report was filed.",
    "normal_operation": "A routine inspection on another unit recorded readings within its normal range.",
}


class ExperimentError(RuntimeError):
    """Raised when a required comparison cannot be run without guessing."""


class OllamaClient:
    """Small local-only client for the pinned Ollama model revisions."""

    def __init__(self, base_url: str = "http://127.0.0.1:11434", timeout: int = 300):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        if urllib.parse.urlparse(self.base_url).hostname not in {
            "127.0.0.1",
            "localhost",
            "::1",
        }:
            raise ExperimentError(
                "the benchmark sends prompts only to a local Ollama service"
            )

    def server_version(self) -> str:
        request = urllib.request.Request(f"{self.base_url}/api/version")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.load(response)
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            raise ExperimentError(
                f"cannot read local model service version: {exc}"
            ) from exc
        version = payload.get("version") if isinstance(payload, dict) else None
        if not isinstance(version, str):
            raise ExperimentError("local model service returned no version")
        return version

    def _post(self, route: str, payload: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            f"{self.base_url}{route}",
            data=json.dumps(payload, sort_keys=True).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                value = json.load(response)
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            raise ExperimentError(
                f"local model request failed at {route}: {exc}"
            ) from exc
        if not isinstance(value, dict):
            raise ExperimentError(
                f"local model returned a non-object response at {route}"
            )
        return value

    def model_digests(self) -> dict[str, str]:
        request = urllib.request.Request(f"{self.base_url}/api/tags")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.load(response)
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            raise ExperimentError(f"cannot read local model revisions: {exc}") from exc
        return {
            str(item["name"]): str(item["digest"])
            for item in payload.get("models", [])
            if isinstance(item, dict) and "name" in item and "digest" in item
        }

    def chat(
        self,
        model: str,
        system: str,
        user: str,
        seed: int,
        num_predict: int = NUM_PREDICT,
    ) -> dict[str, Any]:
        response = self._post(
            "/api/chat",
            {
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "format": "json",
                "think": False,
                "stream": False,
                "keep_alive": "10m",
                "options": {
                    "temperature": 0,
                    "top_p": 1,
                    "seed": seed,
                    "num_ctx": 4096,
                    "num_predict": num_predict,
                },
            },
        )
        message = response.get("message")
        if not isinstance(message, dict) or not isinstance(message.get("content"), str):
            raise ExperimentError(f"{model} returned no text content")
        return {
            "content": message["content"],
            "prompt_eval_count": response.get("prompt_eval_count"),
            "eval_count": response.get("eval_count"),
            "done_reason": response.get("done_reason"),
        }


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def digest_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def load_preregistration() -> dict[str, Any]:
    try:
        value = json.loads(PREREGISTRATION.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExperimentError(f"cannot read the frozen preregistration: {exc}") from exc
    if not isinstance(value, dict):
        raise ExperimentError("the frozen preregistration must be a JSON object")
    expected = {
        "study_id": "synthetic-retrieval-dependence-pilot-v1",
        "models": {
            "X": {"tag": MODEL_X, "ollama_manifest_sha256": MODEL_DIGESTS[MODEL_X]},
            "Y": {"tag": MODEL_Y, "ollama_manifest_sha256": MODEL_DIGESTS[MODEL_Y]},
        },
        "case_count": 36,
        "items_per_case": 16,
        "strata": list(STRATA),
        "budgets": list(BUDGETS),
        "replicates": BOOTSTRAP_REPLICATES,
    }
    actual = {
        "study_id": value.get("study_id"),
        "models": {
            name: {
                "tag": value.get("models", {}).get(name, {}).get("tag"),
                "ollama_manifest_sha256": value.get("models", {})
                .get(name, {})
                .get("ollama_manifest_sha256"),
            }
            for name in ("X", "Y")
        },
        "case_count": value.get("case_design", {}).get("case_count"),
        "items_per_case": value.get("case_design", {}).get("items_per_case"),
        "strata": value.get("case_design", {}).get("strata"),
        "budgets": value.get("case_design", {}).get("budgets"),
        "replicates": value.get("primary_analysis", {})
        .get("bootstrap", {})
        .get("replicates"),
    }
    if actual != expected:
        raise ExperimentError(
            "runner settings differ from the committed preregistration"
        )
    return value


def _source_id(case_id: str, n: int) -> str:
    return f"{case_id}-source-{n:02d}"


def _item(
    case_id: str,
    n: int,
    text: str,
    *,
    relevance: str,
    source_status: str = "verified",
    source_number: int | None = None,
    claim_id: str | None = None,
    supports_claim: bool = False,
    misleading: bool = False,
    wrong_hypothesis_support: bool = False,
    contradicts_wrong_hypothesis: bool = False,
    duplicate_group: str | None = None,
    unknown_lineage: bool = False,
) -> dict[str, Any]:
    item_id = f"{case_id}-I{n:02d}"
    if unknown_lineage:
        source_record_id = None
        upstream_source_ids: list[str] = []
        derivation_links: list[str] = []
    else:
        source = _source_id(case_id, source_number if source_number is not None else n)
        source_record_id = source
        upstream_source_ids = [source]
        derivation_links = []
    return {
        "item_id": item_id,
        "case_id": case_id,
        "source_record_id": source_record_id,
        "upstream_source_ids": upstream_source_ids,
        "derivation_links": derivation_links,
        "duplicate_group": duplicate_group,
        "text": text,
        "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "relevance_label": relevance,
        "source_status": source_status,
        "operation_use_labels": {
            "corroborate_root_cause": {
                "supports_claim": supports_claim,
                "claim_id": claim_id,
            }
        },
        "misleading_label": misleading,
        "supports_wrong_hypothesis": wrong_hypothesis_support,
        "contradicts_wrong_hypothesis": contradicts_wrong_hypothesis,
    }


def generate_cases(seed: int = SEED) -> list[dict[str, Any]]:
    """Create the locked 36-case fixture with labels outside model-visible fields."""
    rng = np.random.default_rng(seed)
    cases: list[dict[str, Any]] = []
    for stratum_index, stratum in enumerate(STRATA):
        for replica in range(6):
            case_number = stratum_index * 6 + replica + 1
            case_id = f"RD-{case_number:03d}"
            gold = CAUSES[(stratum_index + replica) % len(CAUSES)]
            wrong = CAUSES[(CAUSES.index(gold) + 1) % len(CAUSES)]
            replica_split = {0: "development", 1: "rule_authoring"}.get(
                replica, "heldout"
            )
            primary_text, corroborating_text = CAUSE_TEXT[gold]
            items = [
                _item(
                    case_id,
                    1,
                    primary_text,
                    relevance="decisive",
                    source_number=1,
                    claim_id=gold,
                    supports_claim=True,
                    contradicts_wrong_hypothesis=(
                        stratum == "wrong_initial_hypothesis"
                    ),
                ),
                _item(
                    case_id,
                    2,
                    corroborating_text,
                    relevance="decisive",
                    source_number=2,
                    claim_id=gold,
                    supports_claim=True,
                    contradicts_wrong_hypothesis=(
                        stratum == "wrong_initial_hypothesis"
                    ),
                ),
                _item(
                    case_id,
                    3,
                    f"A preliminary note says the vibration may be associated with {gold.replace('_', ' ')}; it requests a follow-up measurement.",
                    relevance="relevant_nondecisive",
                    source_number=3,
                    claim_id=gold,
                    supports_claim=False,
                ),
                _item(
                    case_id,
                    4,
                    "The operator logged a routine shift change with no measurement for this unit.",
                    relevance="irrelevant",
                    source_number=4,
                    claim_id=CAUSES[(CAUSES.index(gold) + 2) % len(CAUSES)],
                ),
                _item(
                    case_id,
                    5,
                    DISTRACTION_TEXT[wrong],
                    relevance="plausible_distraction",
                    source_number=5,
                    claim_id=wrong,
                ),
                _item(
                    case_id,
                    6,
                    "A delivery record confirms the inspection team arrived before the scheduled service window.",
                    relevance="irrelevant",
                    source_number=6,
                    claim_id=CAUSES[(CAUSES.index(gold) + 3) % len(CAUSES)],
                ),
                _item(
                    case_id,
                    7,
                    f"A non-decisive trend chart shows a small change that is compatible with {gold.replace('_', ' ')} or normal load variation.",
                    relevance="relevant_nondecisive",
                    source_number=7,
                    claim_id=gold,
                ),
                _item(
                    case_id,
                    8,
                    "A parts invoice lists a filter replacement but contains no test result for the reported vibration.",
                    relevance="irrelevant",
                    source_number=8,
                    claim_id=wrong,
                ),
                _item(
                    case_id,
                    9,
                    f"A maintenance note from another unit describes {wrong.replace('_', ' ')}; the unit identifier does not match this case.",
                    relevance="misleading",
                    source_status="invalid",
                    source_number=9,
                    claim_id=wrong,
                    misleading=True,
                    wrong_hypothesis_support=(stratum == "wrong_initial_hypothesis"),
                ),
                _item(
                    case_id,
                    10,
                    "A calibration certificate confirms the reference instrument was within its inspection interval.",
                    relevance="context_only",
                    source_number=10,
                    claim_id=gold,
                ),
                _item(
                    case_id,
                    11,
                    f"A second non-decisive observation mentions {gold.replace('_', ' ')} but does not identify the source of the reported signal.",
                    relevance="relevant_nondecisive",
                    source_number=11,
                    claim_id=gold,
                ),
                _item(
                    case_id,
                    12,
                    "The production schedule shows the unit was operating at the declared load.",
                    relevance="context_only",
                    source_number=12,
                    claim_id=gold,
                ),
                _item(
                    case_id,
                    13,
                    f"An older report from a different date attributes a similar alarm to {wrong.replace('_', ' ')}.",
                    relevance="plausible_distraction",
                    source_number=13,
                    claim_id=wrong,
                ),
                _item(
                    case_id,
                    14,
                    "A signed checklist confirms that a visual inspection was completed, but it records no finding.",
                    relevance="context_only",
                    source_number=14,
                    claim_id=gold,
                ),
                _item(
                    case_id,
                    15,
                    "A sensor timestamp is two minutes later than the maintenance note; the sequence does not resolve the cause.",
                    relevance="plausible_distraction",
                    source_number=15,
                    claim_id=CAUSES[(CAUSES.index(gold) + 2) % len(CAUSES)],
                ),
                _item(
                    case_id,
                    16,
                    "The work order was closed after a supervisor reviewed the documentation.",
                    relevance="irrelevant",
                    source_number=16,
                    claim_id=wrong,
                ),
            ]

            if stratum == "misleading":
                items[8]["text"] = (
                    f"A field report states that {wrong.replace('_', ' ')} caused this exact unit's alarm; "
                    "the report was later invalidated because its unit identifier was copied from another record."
                )
            elif stratum == "duplicate_shared_upstream":
                duplicate = dict(items[0])
                duplicate["item_id"] = f"{case_id}-I09"
                duplicate["text"] = f"Duplicate copy: {items[0]['text']}"
                duplicate["text_sha256"] = hashlib.sha256(
                    duplicate["text"].encode()
                ).hexdigest()
                duplicate["duplicate_group"] = f"{case_id}-duplicate-1"
                duplicate["derivation_links"] = [items[0]["item_id"]]
                items[8] = duplicate
                items[0]["duplicate_group"] = f"{case_id}-duplicate-1"
            elif stratum == "conflicting":
                items[8] = _item(
                    case_id,
                    9,
                    f"A signed report for this unit attributes the same alarm to {wrong.replace('_', ' ')}; a second lab report disputes its measurement.",
                    relevance="conflicting",
                    source_status="conflicting",
                    source_number=9,
                    claim_id=wrong,
                )
            elif stratum == "unknown_source_status":
                items[8] = _item(
                    case_id,
                    9,
                    f"An unattributed note says {gold.replace('_', ' ')} may explain the alarm, but its author and source record are missing.",
                    relevance="relevant_nondecisive",
                    source_status="unknown",
                    claim_id=gold,
                    unknown_lineage=True,
                )
            elif stratum == "wrong_initial_hypothesis":
                items[8]["text"] = (
                    f"A preliminary note proposes {wrong.replace('_', ' ')} as a cause, but it predates "
                    "the reference inspection and has no confirming measurement."
                )
                items[8]["relevance_label"] = "misleading"
                items[8]["misleading_label"] = True
                items[8]["wrong_hypothesis_support"] = True

            permutation = rng.permutation(len(items)).tolist()
            shuffled = [items[index] for index in permutation]
            wrong_hypothesis = wrong if stratum == "wrong_initial_hypothesis" else None
            cases.append(
                {
                    "case_id": case_id,
                    "stratum": stratum,
                    "split": replica_split,
                    "query": (
                        "A rotating unit has an abnormal vibration or temperature report. "
                        "Use the evidence to identify the root cause: bearing wear, lubrication loss, "
                        "sensor fault, or normal operation."
                    ),
                    "initial_hypothesis": wrong_hypothesis,
                    "second_round_query": (
                        f"Reconsider the same unit. The frozen initial hypothesis is {wrong.replace('_', ' ')}. "
                        "Select evidence that can support or challenge it."
                        if wrong_hypothesis
                        else None
                    ),
                    "gold_required_items": [items[0]["item_id"], items[1]["item_id"]],
                    "gold_root_cause": gold,
                    "gold_sufficient_evidence": True,
                    "audit": {
                        "independent_review_pass": bool(
                            (stratum_index + replica) % 2 == 0
                        ),
                        "label_review": "generator-invariant-checked; not independently expert-adjudicated",
                    },
                    "items": shuffled,
                }
            )
    return cases


def _visible_case(case: dict[str, Any]) -> dict[str, Any]:
    """Return only fields permitted in selector and interpreter prompts."""
    return {
        "case_id": case["case_id"],
        "question": case["query"],
        "items": [
            {"item_id": item["item_id"], "text": item["text"]} for item in case["items"]
        ],
    }


def selector_prompt(
    case: dict[str, Any], second_round: bool = False
) -> tuple[str, str]:
    visible = _visible_case(case)
    query = case["query"]
    if second_round:
        if not case["second_round_query"]:
            raise ValueError(
                "second-round selection is only defined for wrong-hypothesis cases"
            )
        query = case["second_round_query"]
    user = canonical_json({**visible, "question": query})
    system = (
        "You are a synthetic evidence selector. Rank every supplied item from most useful to least useful "
        "for answering the question. Use only the item IDs and text. Do not invent IDs, omit items, infer "
        "source validity from wording, or write an answer. Return JSON with one key named ranking containing "
        "each supplied item ID exactly once."
    )
    return system, user


def interpreter_prompt(
    case: dict[str, Any], selected_items: Sequence[dict[str, Any]], pad_count: int = 0
) -> tuple[str, str]:
    items = [
        {"item_id": item["item_id"], "text": item["text"]} for item in selected_items
    ]
    user = canonical_json(
        {
            "case_id": case["case_id"],
            "question": case["query"],
            "allowed_root_causes": list(CAUSES),
            "evidence": items,
        }
    )
    if pad_count or "NON-EVIDENCE PADDING" in user:
        user += (
            "\nEND_EVIDENCE\nNON-EVIDENCE PADDING (ignore; not a source):"
            + " pad" * pad_count
        )
    system = (
        "You are a synthetic evidence interpreter. Rank all four allowed root causes from most to least "
        "supported by the supplied evidence. Do not infer source validity or hidden labels. Abstain when "
        "the evidence is insufficient or unresolved. Return JSON with keys ranking (a permutation of all "
        "four allowed labels) and abstain (boolean)."
    )
    if pad_count or "NON-EVIDENCE PADDING" in user:
        system += " Ignore all repeated text after END_EVIDENCE; it is padding and is not evidence."
    return system, user


def _seed_for(*parts: str) -> int:
    material = "|".join((str(MODEL_SEED), *parts)).encode("utf-8")
    return (
        MODEL_SEED
        + int.from_bytes(hashlib.sha256(material).digest()[:4], "big") % 1_000_000
    )


def _parse_json_object(content: str) -> dict[str, Any]:
    normalized = content.strip()
    if normalized.startswith(chr(96) * 3) and normalized.endswith(chr(96) * 3):
        lines = normalized.splitlines()
        if len(lines) >= 3 and lines[0].startswith(chr(96) * 3):
            normalized = "\n".join(lines[1:-1]).strip()
    try:
        value = json.loads(normalized)
    except json.JSONDecodeError as exc:
        raise ExperimentError(f"model output is not JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ExperimentError("model JSON output is not an object")
    return value


def _model_ranking(
    client: OllamaClient,
    model: str,
    case: dict[str, Any],
    *,
    second_round: bool = False,
    phase: str = "selector",
) -> dict[str, Any]:
    system, user = selector_prompt(case, second_round=second_round)
    ids = [item["item_id"] for item in case["items"]]
    attempts: list[dict[str, Any]] = []
    for attempt in range(2):
        adjusted_user = user
        if attempt:
            adjusted_user += (
                "\nThe previous output contained duplicate or missing IDs. Return one JSON object "
                "with a ranking array. Include every supplied item ID once. Do not use code fences "
                "or add explanations."
            )
        response = client.chat(
            model,
            system,
            adjusted_user,
            _seed_for(phase, case["case_id"], str(attempt)),
        )
        attempts.append(
            {
                "prompt_sha256": hashlib.sha256(adjusted_user.encode()).hexdigest(),
                "content": response["content"],
                "done_reason": response.get("done_reason"),
                "eval_count": response.get("eval_count"),
            }
        )
        try:
            output = _parse_json_object(response["content"])
            ranking = output.get("ranking")
            if not isinstance(ranking, list):
                raise ExperimentError("selector ranking must be a list of item IDs")
            unique_ids: list[str] = []
            seen_ids: set[str] = set()
            unknown_ids: list[str] = []
            repeated_ids: list[str] = []
            for item_id in ranking:
                if not isinstance(item_id, str) or item_id not in ids:
                    unknown_ids.append(str(item_id))
                elif item_id in seen_ids:
                    repeated_ids.append(item_id)
                else:
                    unique_ids.append(item_id)
                    seen_ids.add(item_id)
            if not unique_ids:
                raise ExperimentError("selector returned no recognized item IDs")
            missing_ids = [item_id for item_id in ids if item_id not in seen_ids]
            normalized_ranking = [*unique_ids, *missing_ids]
            ranking_repair = {
                "applied": bool(unknown_ids or repeated_ids or missing_ids),
                "raw_exact_permutation": (
                    len(ranking) == len(ids)
                    and not unknown_ids
                    and not repeated_ids
                    and not missing_ids
                ),
                "repeated_ids": repeated_ids,
                "unknown_ids": unknown_ids,
                "missing_ids_appended_in_input_order": missing_ids,
            }
            return {
                "ranking": normalized_ranking,
                "scores": [
                    1.0 / math.log2(rank + 1)
                    for rank in range(1, len(normalized_ranking) + 1)
                ],
                "score_basis": "rank-derived 1/log2(rank+1); not model confidence",
                "model": model,
                "second_round": second_round,
                "attempts": attempts,
                "ranking_repair": ranking_repair,
                "prompt_sha256": attempts[-1]["prompt_sha256"],
                "prompt_eval_count": response["prompt_eval_count"],
                "eval_count": response["eval_count"],
            }
        except ExperimentError as exc:
            if attempt:
                raise ExperimentError(
                    f"{model} selector failed twice for {case['case_id']}: {exc}"
                ) from exc
    raise ExperimentError("unreachable selector parse state")


def bm25_ranking(case: dict[str, Any]) -> dict[str, Any]:
    """Rank one 16-item case with fixed BM25 k1=1.2 and b=0.75."""
    query_terms = re.findall(r"[a-z0-9]+", case["query"].lower())
    tokenized = [
        re.findall(r"[a-z0-9]+", item["text"].lower()) for item in case["items"]
    ]
    lengths = [len(tokens) for tokens in tokenized]
    average_length = sum(lengths) / len(lengths) if lengths else 0.0
    document_frequency: Counter[str] = Counter()
    for tokens in tokenized:
        document_frequency.update(set(tokens))
    scores: list[tuple[str, float]] = []
    for item, tokens, length in zip(case["items"], tokenized, lengths, strict=True):
        term_counts = Counter(tokens)
        score = 0.0
        for term in query_terms:
            frequency = term_counts[term]
            if not frequency:
                continue
            df = document_frequency[term]
            inverse_frequency = math.log1p((len(tokenized) - df + 0.5) / (df + 0.5))
            denominator = frequency + 1.2 * (
                1.0 - 0.75 + 0.75 * length / average_length
            )
            score += inverse_frequency * frequency * 2.2 / denominator
        scores.append((item["item_id"], score))
    scores.sort(key=lambda value: (-value[1], value[0]))
    return {
        "ranking": [item_id for item_id, _ in scores],
        "scores": [score for _, score in scores],
        "score_basis": "BM25 raw score, k1=1.2, b=0.75, case-local index",
        "model": "BM25-v1",
        "second_round": False,
        "attempts": [],
        "prompt_sha256": None,
        "prompt_eval_count": None,
        "eval_count": None,
    }


def _model_interpretation(
    client: OllamaClient,
    model: str,
    case: dict[str, Any],
    selected_items: Sequence[dict[str, Any]],
    *,
    pad_count: int = 0,
    phase: str = "interpretation",
    token_count_only: bool = False,
) -> dict[str, Any]:
    system, user = interpreter_prompt(case, selected_items, pad_count=pad_count)
    attempts: list[dict[str, Any]] = []
    limit = 1 if token_count_only else 2
    for attempt in range(limit):
        adjusted_user = user
        if attempt:
            adjusted_user += (
                "\nReturn exactly one JSON object with ranking and abstain keys. "
                "Rank each allowed cause once and set abstain to true or false. "
                "Do not use code fences or add explanations."
            )
        response = client.chat(
            model,
            system,
            adjusted_user,
            _seed_for(
                phase,
                case["case_id"],
                ",".join(item["item_id"] for item in selected_items),
                str(attempt),
            ),
            num_predict=1 if token_count_only else NUM_PREDICT,
        )
        attempts.append(
            {
                "prompt_sha256": hashlib.sha256(adjusted_user.encode()).hexdigest(),
                "content": response["content"],
                "done_reason": response.get("done_reason"),
                "eval_count": response.get("eval_count"),
            }
        )
        if token_count_only:
            if not isinstance(response["prompt_eval_count"], int):
                raise ExperimentError("Ollama did not report prompt_eval_count")
            return {
                "prompt_eval_count": response["prompt_eval_count"],
                "prompt_sha256": attempts[-1]["prompt_sha256"],
            }
        try:
            output = _parse_json_object(response["content"])
            ranking = output.get("ranking")
            abstain = output.get("abstain")
            if (
                not isinstance(ranking, list)
                or len(ranking) != len(CAUSES)
                or len(set(ranking)) != len(CAUSES)
                or set(ranking) != set(CAUSES)
                or not isinstance(abstain, bool)
            ):
                raise ExperimentError(
                    "interpreter output must rank all causes and set abstain"
                )
            return {
                "ranking": ranking,
                "abstain": abstain,
                "answer": None if abstain else ranking[0],
                "model": model,
                "attempts": attempts,
                "prompt_sha256": attempts[-1]["prompt_sha256"],
                "prompt_eval_count": response["prompt_eval_count"],
                "eval_count": response["eval_count"],
            }
        except ExperimentError as exc:
            if attempt:
                raise ExperimentError(
                    f"{model} interpreter failed twice for {case['case_id']}: {exc}"
                ) from exc
    raise ExperimentError("unreachable interpretation parse state")


def _item_map(case: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["item_id"]: item for item in case["items"]}


def validate_case_set(cases: Sequence[dict[str, Any]]) -> None:
    """Check the locked fixture's structure and provenance before model execution."""
    if len(cases) != 36:
        raise ExperimentError(f"expected 36 cases, found {len(cases)}")
    counts = Counter(case["stratum"] for case in cases)
    if set(counts) != set(STRATA) or any(counts[stratum] != 6 for stratum in STRATA):
        raise ExperimentError("case strata differ from the preregistered design")
    for case in cases:
        items = case["items"]
        ids = [item["item_id"] for item in items]
        if len(items) != 16 or len(set(ids)) != 16:
            raise ExperimentError(
                f"{case['case_id']} does not contain 16 unique evidence items"
            )
        if not set(case["gold_required_items"]) <= set(ids):
            raise ExperimentError(f"{case['case_id']} required evidence is missing")
        item_by_id = _item_map(case)
        roots = []
        for item_id in case["gold_required_items"]:
            item = item_by_id[item_id]
            label = item["operation_use_labels"]["corroborate_root_cause"]
            if (
                not label["supports_claim"]
                or label["claim_id"] != case["gold_root_cause"]
            ):
                raise ExperimentError(
                    f"{case['case_id']} required evidence has an inconsistent claim label"
                )
            if item["source_status"] != "verified" or not item["upstream_source_ids"]:
                raise ExperimentError(
                    f"{case['case_id']} required evidence lacks verified source lineage"
                )
            roots.append(tuple(item["upstream_source_ids"]))
        if len(set(roots)) != len(roots):
            raise ExperimentError(
                f"{case['case_id']} required evidence is not source-independent"
            )
        for item in items:
            if item["source_status"] not in {
                "verified",
                "invalid",
                "conflicting",
                "unknown",
            }:
                raise ExperimentError(f"{case['case_id']} has an invalid source status")
            if item["source_status"] == "unknown" and item["upstream_source_ids"]:
                raise ExperimentError(
                    f"{case['case_id']} inferred lineage from unknown source status"
                )


def _source_roots(item: dict[str, Any]) -> set[str]:
    return set(item["upstream_source_ids"])


def _retrieval_metrics(
    case: dict[str, Any], ranking: Sequence[str], budget: int
) -> dict[str, Any]:
    item_by_id = _item_map(case)
    selected = list(ranking[:budget])
    relevant_ids = {
        item["item_id"]
        for item in case["items"]
        if item["relevance_label"] in {"decisive", "relevant_nondecisive"}
    }
    required = set(case["gold_required_items"])
    selected_set = set(selected)
    misleading_ranks = [
        ranking.index(item["item_id"]) + 1
        for item in case["items"]
        if item["misleading_label"]
    ]
    required_ranks = [ranking.index(item_id) + 1 for item_id in required]
    selected_required_ranks = [rank for rank in required_ranks if rank <= budget]
    misleading_outranks_decisive = bool(selected_required_ranks) and any(
        rank <= budget and rank < max(selected_required_ranks)
        for rank in misleading_ranks
    )
    missing_required = not required <= selected_set
    relevant_selected = sum(item_id in relevant_ids for item_id in selected)
    source_ids = (
        set().union(*(_source_roots(item_by_id[item_id]) for item_id in selected))
        if selected
        else set()
    )
    return {
        "budget": budget,
        "selected_ids": selected,
        "relevant_count": len(relevant_ids),
        "relevant_selected": relevant_selected,
        "recall_at_k": relevant_selected / len(relevant_ids) if relevant_ids else None,
        "precision_at_k": relevant_selected / budget if budget else None,
        "required_item_ids": sorted(required),
        "required_item_ranks": {
            item_id: ranking.index(item_id) + 1 for item_id in sorted(required)
        },
        "complete_evidence_recall": required <= selected_set,
        "misleading_selected": sum(
            item_by_id[item_id]["misleading_label"] for item_id in selected
        ),
        "duplicate_selected": sum(
            item_by_id[item_id]["duplicate_group"] is not None for item_id in selected
        ),
        "conflicting_selected": sum(
            item_by_id[item_id]["source_status"] == "conflicting"
            for item_id in selected
        ),
        "shared_upstream_selected": budget - len(source_ids) if source_ids else budget,
        "missing_required": missing_required,
        "misleading_outranks_decisive": misleading_outranks_decisive,
        "retrieval_error": missing_required or misleading_outranks_decisive,
    }


def _acceptable_abstention(
    case: dict[str, Any], selected: Sequence[dict[str, Any]]
) -> bool:
    ids = {item["item_id"] for item in selected}
    sufficient = set(case["gold_required_items"]) <= ids
    unresolved = any(
        item["source_status"] in {"conflicting", "unknown"} for item in selected
    )
    return not sufficient or unresolved


def _interpretation_metrics(
    case: dict[str, Any], selected: Sequence[dict[str, Any]], output: dict[str, Any]
) -> dict[str, Any]:
    correct = output["answer"] == case["gold_root_cause"]
    acceptable_abstention = _acceptable_abstention(case, selected)
    wrong_non_abstention = not output["abstain"] and not correct
    unnecessary_abstention = output["abstain"] and not acceptable_abstention
    error = wrong_non_abstention or unnecessary_abstention
    return {
        "answer": output["answer"],
        "ranking": output["ranking"],
        "correct_root_cause": correct,
        "correct_root_rank": output["ranking"].index(case["gold_root_cause"]) + 1,
        "abstain": output["abstain"],
        "acceptable_abstention": acceptable_abstention,
        "false_belief": wrong_non_abstention,
        "unnecessary_abstention": unnecessary_abstention,
        "interpretation_error": error,
        "task_success": correct or (output["abstain"] and acceptable_abstention),
    }


def _error_association(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    with_retrieval_error = [row for row in rows if row["retrieval"]["retrieval_error"]]
    without_retrieval_error = [
        row for row in rows if not row["retrieval"]["retrieval_error"]
    ]
    p_with = (
        sum(
            row["interpretation"]["interpretation_error"]
            for row in with_retrieval_error
        )
        / len(with_retrieval_error)
        if with_retrieval_error
        else None
    )
    p_without = (
        sum(
            row["interpretation"]["interpretation_error"]
            for row in without_retrieval_error
        )
        / len(without_retrieval_error)
        if without_retrieval_error
        else None
    )
    retrieval = [int(row["retrieval"]["retrieval_error"]) for row in rows]
    interpretation = [
        int(row["interpretation"]["interpretation_error"]) for row in rows
    ]
    correlation = None
    if len(rows) > 1 and len(set(retrieval)) > 1 and len(set(interpretation)) > 1:
        correlation = float(np.corrcoef(retrieval, interpretation)[0, 1])
    return {
        "n": len(rows),
        "retrieval_error_n": len(with_retrieval_error),
        "no_retrieval_error_n": len(without_retrieval_error),
        "p_interpretation_error_given_retrieval_error": p_with,
        "p_interpretation_error_given_no_retrieval_error": p_without,
        "conditional_risk_difference": p_with - p_without
        if p_with is not None and p_without is not None
        else None,
        "binary_error_correlation": correlation,
    }


def _stratified_bootstrap_ci(
    rows: Sequence[dict[str, Any]],
    statistic: Callable[[Sequence[dict[str, Any]]], float | None],
    seed: int,
    replicates: int = BOOTSTRAP_REPLICATES,
) -> dict[str, Any]:
    by_stratum: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_stratum[row["stratum"]].append(row)
    if not by_stratum:
        return {
            "method": "stratified paired case bootstrap",
            "interval_95": None,
            "usable_resamples": 0,
        }
    rng = np.random.default_rng(seed)
    values: list[float] = []
    for _ in range(replicates):
        sample: list[dict[str, Any]] = []
        for group in by_stratum.values():
            indexes = rng.integers(0, len(group), size=len(group))
            sample.extend(group[int(index)] for index in indexes)
        value = statistic(sample)
        if value is not None and math.isfinite(value):
            values.append(float(value))
    interval = (
        [float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))]
        if values
        else None
    )
    return {
        "method": "95% percentile bootstrap, paired by case and stratified by case type",
        "replicates": replicates,
        "interval_95": interval,
        "usable_resamples": len(values),
    }


def _metric_rate(rows: Sequence[dict[str, Any]], path: tuple[str, str]) -> float | None:
    if not rows:
        return None
    return sum(bool(row[path[0]][path[1]]) for row in rows) / len(rows)


def summarize_condition_rows(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"n": 0}
    association = _error_association(rows)
    misleading_rows = [
        row for row in rows if row["retrieval"]["misleading_selected"] > 0
    ]
    metrics = {
        "sample_count": len(rows),
        "event_stratum_counts": dict(
            sorted(Counter(row["stratum"] for row in rows).items())
        ),
        "event_rate_retrieval_error": sum(
            row["retrieval"]["retrieval_error"] for row in rows
        )
        / len(rows),
        "event_rate_interpretation_error": sum(
            row["interpretation"]["interpretation_error"] for row in rows
        )
        / len(rows),
        "event_rate_correct_root_cause": sum(
            row["interpretation"]["correct_root_cause"] for row in rows
        )
        / len(rows),
        "task_success_rate": sum(row["interpretation"]["task_success"] for row in rows)
        / len(rows),
        "misleading_evidence_selected_case_count": len(misleading_rows),
        "recovery_rate_after_misleading_evidence_selected": (
            sum(row["interpretation"]["task_success"] for row in misleading_rows)
            / len(misleading_rows)
            if misleading_rows
            else None
        ),
        "event_rate_false_belief": sum(
            row["interpretation"]["false_belief"] for row in rows
        )
        / len(rows),
        "event_rate_abstention": sum(row["interpretation"]["abstain"] for row in rows)
        / len(rows),
        "abstention_quality": (
            sum(
                row["interpretation"]["acceptable_abstention"]
                for row in rows
                if row["interpretation"]["abstain"]
            )
            / sum(row["interpretation"]["abstain"] for row in rows)
            if any(row["interpretation"]["abstain"] for row in rows)
            else None
        ),
        "mean_recall_at_k": float(
            np.mean([row["retrieval"]["recall_at_k"] for row in rows])
        ),
        "mean_precision_at_k": float(
            np.mean([row["retrieval"]["precision_at_k"] for row in rows])
        ),
        "complete_evidence_recall_rate": sum(
            row["retrieval"]["complete_evidence_recall"] for row in rows
        )
        / len(rows),
        "mean_correct_root_rank": float(
            np.mean([row["interpretation"]["correct_root_rank"] for row in rows])
        ),
        "error_association": association,
    }
    metrics["uncertainty"] = {
        "interpretation_error_rate": _stratified_bootstrap_ci(
            rows,
            lambda sample: _metric_rate(
                sample, ("interpretation", "interpretation_error")
            ),
            BOOTSTRAP_SEED,
        ),
        "recall_at_k": _stratified_bootstrap_ci(
            rows,
            lambda sample: float(
                np.mean([row["retrieval"]["recall_at_k"] for row in sample])
            ),
            BOOTSTRAP_SEED + 1,
        ),
        "conditional_risk_difference": _stratified_bootstrap_ci(
            rows,
            lambda sample: _error_association(sample)["conditional_risk_difference"],
            BOOTSTRAP_SEED + 2,
        ),
        "binary_error_correlation": _stratified_bootstrap_ci(
            rows,
            lambda sample: _error_association(sample)["binary_error_correlation"],
            BOOTSTRAP_SEED + 3,
        ),
    }
    return metrics


def _logistic_source_calibration(
    selections: dict[str, dict[str, dict[str, Any]]], cases: Sequence[dict[str, Any]]
) -> dict[str, Any]:
    development = [case for case in cases if case["split"] == "development"]
    heldout = [case for case in cases if case["split"] == "heldout"]
    results: dict[str, Any] = {}
    for selector in ("A", "B", "C"):
        training: list[tuple[str, float, int, str]] = []
        evaluation: list[tuple[str, float, int, str]] = []
        unknown_test_scores: list[float] = []
        unknown_train = 0
        unknown_test = 0
        for case in development:
            trace = selections[selector][case["case_id"]]
            scores = dict(zip(trace["ranking"], trace["scores"], strict=True))
            for item in case["items"]:
                status = item["source_status"]
                if status == "unknown":
                    unknown_train += 1
                    continue
                training.append(
                    (
                        case["case_id"],
                        float(scores[item["item_id"]]),
                        int(status == "verified"),
                        status,
                    )
                )
        for case in heldout:
            trace = selections[selector][case["case_id"]]
            scores = dict(zip(trace["ranking"], trace["scores"], strict=True))
            for item in case["items"]:
                status = item["source_status"]
                if status == "unknown":
                    unknown_test += 1
                    unknown_test_scores.append(float(scores[item["item_id"]]))
                    continue
                evaluation.append(
                    (
                        case["case_id"],
                        float(scores[item["item_id"]]),
                        int(status == "verified"),
                        status,
                    )
                )
        labels = np.asarray([row[2] for row in training], dtype=int)
        values = np.asarray([row[1] for row in training], dtype=float)
        mean = float(values.mean()) if len(values) else 0.0
        scale = float(values.std()) if len(values) and values.std() else 1.0
        if len(set(labels.tolist())) < 2:
            results[selector] = {
                "status": "unavailable; development cases have one source-status class",
                "development_n": len(training),
                "heldout_n": len(evaluation),
                "unknown_development_n": unknown_train,
                "unknown_heldout_n": unknown_test,
            }
            continue
        model = LogisticRegression(
            C=1.0, solver="liblinear", max_iter=1000, random_state=MODEL_SEED
        )
        model.fit(((values - mean) / scale).reshape(-1, 1), labels)
        test_scores = np.asarray([row[1] for row in evaluation], dtype=float)
        test_labels = np.asarray([row[2] for row in evaluation], dtype=int)
        probabilities = model.predict_proba(
            ((test_scores - mean) / scale).reshape(-1, 1)
        )[:, 1]
        brier = float(np.mean((probabilities - test_labels) ** 2))
        prevalence = float(labels.mean())
        base_brier = float(np.mean((prevalence - test_labels) ** 2))
        bins = []
        ece = 0.0
        for index in range(5):
            lower = index / 5
            upper = (index + 1) / 5
            selected = (probabilities >= lower) & (
                probabilities < upper if index < 4 else probabilities <= upper
            )
            count = int(selected.sum())
            observed = float(test_labels[selected].mean()) if count else None
            predicted = float(probabilities[selected].mean()) if count else None
            if count:
                ece += count / len(test_labels) * abs(observed - predicted)
            bins.append(
                {
                    "lower": lower,
                    "upper": upper,
                    "count": count,
                    "observed_verified_rate": observed,
                    "mean_predicted": predicted,
                }
            )
        auc = (
            float(roc_auc_score(test_labels, probabilities))
            if len(set(test_labels.tolist())) == 2
            else None
        )
        results[selector] = {
            "status": "fit on development; evaluated on heldout",
            "mapping": "LogisticRegression(C=1, solver=liblinear) over standardized raw selector score",
            "score_mean": mean,
            "score_scale": scale,
            "development_n": len(training),
            "development_verified_prevalence": prevalence,
            "heldout_n": len(evaluation),
            "heldout_brier_score": brier,
            "training_prevalence_brier_baseline": base_brier,
            "heldout_expected_calibration_error_5_bins": ece,
            "heldout_reliability_bins": bins,
            "heldout_roc_auc": auc,
            "unknown_development_n": unknown_train,
            "unknown_heldout_n": unknown_test,
            "unknown_mean_predicted_verified": (
                float(
                    np.mean(
                        model.predict_proba(
                            ((np.asarray(unknown_test_scores) - mean) / scale).reshape(
                                -1, 1
                            )
                        )[:, 1]
                    )
                )
                if unknown_test
                else None
            ),
        }
    return results


def _metadata_features(
    case: dict[str, Any], selected: Sequence[dict[str, Any]], row: dict[str, Any]
) -> list[float]:
    count = max(1, len(selected))
    known_roots = [
        tuple(item["upstream_source_ids"])
        for item in selected
        if item["upstream_source_ids"]
    ]
    repeated = len(known_roots) - len(set(known_roots))
    return [
        sum(item["source_status"] == "unknown" for item in selected) / count,
        sum(item["source_status"] == "invalid" for item in selected) / count,
        sum(item["source_status"] == "conflicting" for item in selected) / count,
        max(0, repeated) / count,
        len(selected) / 16,
    ]


def _lineage_predictive_value(
    rows: Sequence[dict[str, Any]], case_by_id: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    rows = [row for row in rows if row["budget"] == 4]
    development = [
        row for row in rows if case_by_id[row["case_id"]]["split"] == "development"
    ]
    heldout = [row for row in rows if case_by_id[row["case_id"]]["split"] == "heldout"]
    feature_sets = {
        "source_and_derivation_metadata": lambda row, case: _metadata_features(
            case,
            [
                case_by_id[row["case_id"]]["_item_by_id"][item_id]
                for item_id in row["selected_ids"]
            ],
            row,
        ),
        "metadata_plus_selector_interpreter_lineage": lambda row, case: (
            _metadata_features(
                case,
                [
                    case_by_id[row["case_id"]]["_item_by_id"][item_id]
                    for item_id in row["selected_ids"]
                ],
                row,
            )
            + [
                float(row["selector_model"] == row["interpreter_model"]),
                float(row["selector_model"] == MODEL_Y),
            ]
        ),
    }
    outcomes = np.asarray(
        [int(row["interpretation"]["interpretation_error"]) for row in heldout],
        dtype=int,
    )
    result: dict[str, Any] = {
        "development_case_count": len({row["case_id"] for row in development}),
        "heldout_case_count": len({row["case_id"] for row in heldout}),
        "development_row_count": len(development),
        "heldout_row_count": len(heldout),
        "fit": "LogisticRegression(C=1, solver=liblinear), fixed; no tuning",
        "models": {},
    }
    losses: dict[str, float] = {}
    per_case_losses: dict[str, dict[str, float]] = {}
    for name, feature_fn in feature_sets.items():
        train_x = np.asarray(
            [feature_fn(row, case_by_id[row["case_id"]]) for row in development]
        )
        test_x = np.asarray(
            [feature_fn(row, case_by_id[row["case_id"]]) for row in heldout]
        )
        train_y = np.asarray(
            [int(row["interpretation"]["interpretation_error"]) for row in development]
        )
        if len(set(train_y.tolist())) < 2:
            result["models"][name] = {
                "status": "unavailable; development labels have one class"
            }
            continue
        model = LogisticRegression(
            C=1.0, solver="liblinear", max_iter=1000, random_state=MODEL_SEED
        )
        model.fit(train_x, train_y)
        probabilities = model.predict_proba(test_x)[:, 1]
        losses[name] = float(log_loss(outcomes, probabilities, labels=[0, 1]))
        clipped = np.clip(probabilities, np.finfo(float).eps, 1 - np.finfo(float).eps)
        row_losses = -(
            outcomes * np.log(clipped) + (1 - outcomes) * np.log(1 - clipped)
        )
        grouped_losses: dict[str, list[float]] = defaultdict(list)
        for row, loss in zip(heldout, row_losses, strict=True):
            grouped_losses[row["case_id"]].append(float(loss))
        per_case_losses[name] = {
            case_id: float(np.mean(case_values))
            for case_id, case_values in grouped_losses.items()
        }
        result["models"][name] = {
            "heldout_log_loss": losses[name],
            "feature_count": train_x.shape[1],
            "heldout_brier_score": float(np.mean((probabilities - outcomes) ** 2)),
        }
    if len(losses) == 2:
        changes = [
            {
                "case_id": case_id,
                "stratum": case_by_id[case_id]["stratum"],
                "log_loss_change_after_lineage": (
                    per_case_losses["metadata_plus_selector_interpreter_lineage"][
                        case_id
                    ]
                    - per_case_losses["source_and_derivation_metadata"][case_id]
                ),
            }
            for case_id in sorted(per_case_losses["source_and_derivation_metadata"])
        ]
        result["paired_log_loss_change_after_lineage"] = (
            losses["metadata_plus_selector_interpreter_lineage"]
            - losses["source_and_derivation_metadata"]
        )
        result["per_case_paired_log_loss_change"] = changes
        result["uncertainty"] = _stratified_bootstrap_ci(
            changes,
            lambda sample: (
                float(np.mean([row["log_loss_change_after_lineage"] for row in sample]))
                if sample
                else None
            ),
            BOOTSTRAP_SEED + 4,
        )
    else:
        result["uncertainty"] = {
            "method": "95% percentile paired bootstrap, stratified by held-out case type",
            "interval_95": None,
            "usable_resamples": 0,
        }
    return result


def _upstream_group(item: dict[str, Any]) -> tuple[str, ...] | None:
    roots = tuple(sorted(item["upstream_source_ids"]))
    return roots if roots else None


def _independent_upstream_groups(
    groups: Sequence[tuple[str, ...] | None],
) -> list[tuple[str, ...]]:
    """Keep one record per disjoint upstream lineage, in selection order."""
    independent: list[tuple[str, ...]] = []
    seen_roots: set[str] = set()
    for group in groups:
        if group is None:
            continue
        roots = set(group)
        if not roots or roots & seen_roots:
            continue
        independent.append(group)
        seen_roots.update(roots)
    return independent


def _shared_model(selector_model: str, interpreter_model: str) -> bool:
    return selector_model == interpreter_model and selector_model != "BM25-v1"


def _reference_permission(
    case: dict[str, Any],
    selected: Sequence[dict[str, Any]],
    selector_model: str,
    interpreter_model: str,
) -> bool:
    supporting = [
        item
        for item in selected
        if item["operation_use_labels"]["corroborate_root_cause"]["supports_claim"]
        and item["operation_use_labels"]["corroborate_root_cause"]["claim_id"]
        == case["gold_root_cause"]
    ]
    groups = [
        _upstream_group(item)
        for item in supporting
        if item["source_status"] == "verified" and _upstream_group(item) is not None
    ]
    no_conflict = not any(item["source_status"] == "conflicting" for item in selected)
    all_support_records_verified = all(
        item["source_status"] == "verified" and _upstream_group(item) is not None
        for item in supporting
    )
    review_ok = (
        not _shared_model(selector_model, interpreter_model)
        or case["audit"]["independent_review_pass"]
    )
    return (
        len(_independent_upstream_groups(groups)) >= 2
        and no_conflict
        and all_support_records_verified
        and review_ok
    )


def _policy_permission(
    policy: str,
    case: dict[str, Any],
    selected: Sequence[dict[str, Any]],
    selector_model: str,
    interpreter_model: str,
) -> bool:
    if policy == "naive_aggregation":
        return True
    if policy == "global_label":
        return not _shared_model(selector_model, interpreter_model)
    if policy == "metadata_only":
        groups = [_upstream_group(item) for item in selected]
        return (
            not _shared_model(selector_model, interpreter_model)
            and all(group is not None for group in groups)
            and len(set(groups)) >= 2
            and len(_independent_upstream_groups(groups)) == len(groups)
        )
    if policy == "operation_specific":
        return _reference_permission(case, selected, selector_model, interpreter_model)
    raise ValueError(f"unknown policy: {policy}")


def _policy_rank(
    policy: str,
    case: dict[str, Any],
    selected: Sequence[dict[str, Any]],
    selector_model: str,
    interpreter_model: str,
    score_by_id: dict[str, float],
) -> list[str] | None:
    if not _policy_permission(
        policy, case, selected, selector_model, interpreter_model
    ):
        return None
    votes: Counter[str] = Counter()
    seen_source_roots: set[str] = set()
    for item in selected:
        label = item["operation_use_labels"]["corroborate_root_cause"]["claim_id"]
        if label not in CAUSES:
            continue
        if policy == "operation_specific":
            if (
                item["source_status"] != "verified"
                or not item["operation_use_labels"]["corroborate_root_cause"][
                    "supports_claim"
                ]
            ):
                continue
            group = _upstream_group(item)
            if group is None or set(group) & seen_source_roots:
                continue
            seen_source_roots.update(group)
        weight = score_by_id[item["item_id"]]
        votes[label] += weight
    if not votes:
        return []
    return [
        cause
        for cause, _ in sorted(votes.items(), key=lambda pair: (-pair[1], pair[0]))
    ]


def _policy_decision(
    ranking: list[str] | None,
    policy: str,
    case: dict[str, Any],
    selected: Sequence[dict[str, Any]],
    score_by_id: dict[str, float],
) -> str | None:
    if ranking is None or not ranking:
        return None
    top = ranking[0]
    source_weights: dict[tuple[str, ...] | str, float] = defaultdict(float)
    seen_source_roots: set[str] = set()
    total = 0.0
    for item in selected:
        label = item["operation_use_labels"]["corroborate_root_cause"]["claim_id"]
        group = _upstream_group(item)
        weight = score_by_id[item["item_id"]]
        if policy == "operation_specific":
            if (
                label not in CAUSES
                or item["source_status"] != "verified"
                or not item["operation_use_labels"]["corroborate_root_cause"][
                    "supports_claim"
                ]
                or group is None
                or set(group) & seen_source_roots
            ):
                continue
            seen_source_roots.update(group)
            key: tuple[str, ...] | str = group
            total += weight
            if label == top:
                source_weights[key] += weight
            continue
        if policy in {"naive_aggregation", "global_label"} or group is None:
            key = item["item_id"]
        else:
            key = group
        total += weight
        if label == top:
            source_weights[key] += weight
    top_weight = sum(source_weights.values())
    distinct_sources = len(source_weights)
    share = top_weight / total if total else 0.0
    return top if distinct_sources >= 2 and share >= 0.60 else None


def evaluate_policies(
    case: dict[str, Any],
    selected: Sequence[dict[str, Any]],
    selector_model: str,
    interpreter_model: str,
    score_by_id: dict[str, float],
    interpretation_error: bool,
) -> dict[str, Any]:
    policies = (
        "naive_aggregation",
        "global_label",
        "metadata_only",
        "operation_specific",
    )
    expected = _reference_permission(case, selected, selector_model, interpreter_model)
    naive_rank = _policy_rank(
        "naive_aggregation",
        case,
        selected,
        selector_model,
        interpreter_model,
        score_by_id,
    )
    naive_decision = _policy_decision(
        naive_rank, "naive_aggregation", case, selected, score_by_id
    )
    records: dict[str, Any] = {}
    for policy in policies:
        permit = _policy_permission(
            policy, case, selected, selector_model, interpreter_model
        )
        ranking = _policy_rank(
            policy, case, selected, selector_model, interpreter_model, score_by_id
        )
        decision = _policy_decision(ranking, policy, case, selected, score_by_id)
        records[policy] = {
            "expected_permission": expected,
            "permission": permit,
            "false_permission": permit and not expected,
            "unnecessary_refusal": not permit and expected,
            "evidence_ranking": ranking,
            "ranking_changed_from_naive": ranking != naive_rank,
            "decision": decision,
            "decision_changed_from_naive": decision != naive_decision,
            "interpretation_error": permit and interpretation_error,
        }
    return records


def _policy_summary(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    names = ("naive_aggregation", "global_label", "metadata_only", "operation_specific")
    summaries: dict[str, Any] = {}
    for name in names:
        records = [row["policies"][name] for row in rows]
        invalid = sum(not record["expected_permission"] for record in records)
        valid = len(records) - invalid
        summaries[name] = {
            "record_count": len(records),
            "heldout_case_count": len({row["case_id"] for row in rows}),
            "false_permissions": sum(record["false_permission"] for record in records),
            "invalid_reference_denominator": invalid,
            "false_permission_rate": sum(
                record["false_permission"] for record in records
            )
            / invalid
            if invalid
            else None,
            "unnecessary_refusals": sum(
                record["unnecessary_refusal"] for record in records
            ),
            "valid_reference_denominator": valid,
            "unnecessary_refusal_rate": sum(
                record["unnecessary_refusal"] for record in records
            )
            / valid
            if valid
            else None,
            "interpretation_errors": sum(
                record["interpretation_error"] for record in records
            ),
            "ranking_changed_records_vs_naive": sum(
                record["ranking_changed_from_naive"] for record in records
            ),
            "decision_changed_records_vs_naive": sum(
                record["decision_changed_from_naive"] for record in records
            ),
            "cases_with_decision_change": len(
                {
                    row["case_id"]
                    for row in rows
                    if row["policies"][name]["decision_changed_from_naive"]
                }
            ),
        }
    return summaries


def _selector_pair_order(
    left: dict[str, Any], right: dict[str, Any], budget: int
) -> tuple[list[str], list[str], set[str]]:
    half = budget // 2
    left_ids = left["ranking"][:half]
    right_ids = right["ranking"][:half]
    union = set(left_ids) | set(right_ids)
    left_rank = {item_id: rank for rank, item_id in enumerate(left["ranking"], start=1)}
    right_rank = {
        item_id: rank for rank, item_id in enumerate(right["ranking"], start=1)
    }
    ordered = sorted(
        union,
        key=lambda item_id: (
            min(left_rank.get(item_id, 999), right_rank.get(item_id, 999)),
            item_id,
        ),
    )
    return ordered, left_ids, set(right_ids)


def _pair_prompt_user(case: dict[str, Any], selected: Sequence[dict[str, Any]]) -> str:
    evidence = [{"item_id": item["item_id"], "text": item["text"]} for item in selected]
    return (
        canonical_json(
            {
                "case_id": case["case_id"],
                "question": case["query"],
                "allowed_root_causes": list(CAUSES),
                "evidence": evidence,
            }
        )
        + "\nEND_EVIDENCE\nNON-EVIDENCE PADDING (ignore; not a source):"
    )


def _pair_system() -> str:
    return (
        "You are a synthetic evidence interpreter. Rank all four allowed root causes from most to least "
        "supported by the evidence. Ignore all text after END_EVIDENCE; it is non-evidence token padding. "
        "Return JSON with ranking (a permutation of all four labels) and abstain (boolean)."
    )


def _count_prompt_tokens(
    client: OllamaClient, model: str, system: str, user: str, seed: int
) -> int:
    response = client.chat(model, system, user, seed, num_predict=1)
    count = response["prompt_eval_count"]
    if not isinstance(count, int):
        raise ExperimentError("local service did not return a prompt token count")
    return count


def _pad_to_count(
    client: OllamaClient,
    model: str,
    system: str,
    user: str,
    target: int,
    seed: int,
    base_count: int,
) -> tuple[str, int, int]:
    if base_count > target:
        raise ExperimentError("pair prompt already exceeds the matched token target")
    if base_count == target:
        return user, 0, base_count
    for marker in (" pad", " x", " neutral"):
        amount = max(1, target - base_count)
        for _ in range(5):
            padded = user + marker * amount
            measured = _count_prompt_tokens(client, model, system, padded, seed)
            if measured == target:
                return padded, amount, measured
            amount += target - measured
            if amount <= 0:
                break
    raise ExperimentError(
        f"could not exactly match prompt token count {target} from {base_count}"
    )


def _interpret_pair_context(
    client: OllamaClient,
    model: str,
    case: dict[str, Any],
    selected: Sequence[dict[str, Any]],
    padded_user: str,
    token_count: int,
    phase: str,
) -> dict[str, Any]:
    response = client.chat(
        model, _pair_system(), padded_user, _seed_for(phase, case["case_id"])
    )
    if response["prompt_eval_count"] != token_count:
        raise ExperimentError(
            "interpreted selector-pair prompt did not retain its matched token count"
        )
    output = _parse_json_object(response["content"])
    ranking = output.get("ranking")
    abstain = output.get("abstain")
    if (
        not isinstance(ranking, list)
        or len(ranking) != 4
        or set(ranking) != set(CAUSES)
        or len(set(ranking)) != 4
        or not isinstance(abstain, bool)
    ):
        raise ExperimentError("selector-pair interpreter returned an invalid ranking")
    interpretation = _interpretation_metrics(
        case,
        selected,
        {
            "ranking": ranking,
            "abstain": abstain,
            "answer": None if abstain else ranking[0],
        },
    )
    return {
        "interpretation": interpretation,
        "prompt_sha256": hashlib.sha256(padded_user.encode()).hexdigest(),
        "prompt_eval_count": response["prompt_eval_count"],
        "eval_count": response["eval_count"],
    }


def _pair_probe(
    client: OllamaClient,
    cases: Sequence[dict[str, Any]],
    selections: dict[str, dict[str, dict[str, Any]]],
) -> list[dict[str, Any]]:
    cases_by_stratum = {
        stratum: next(
            case
            for case in cases
            if case["stratum"] == stratum and case["split"] == "heldout"
        )
        for stratum in STRATA
    }
    results: list[dict[str, Any]] = []
    for case in cases_by_stratum.values():
        item_by_id = _item_map(case)
        for left_id, right_id in (("A", "B"), ("A", "C"), ("B", "C")):
            left = selections[left_id][case["case_id"]]
            right = selections[right_id][case["case_id"]]
            for nominal_budget in PAIR_BUDGETS:
                pair_ids, left_half, right_half = _selector_pair_order(
                    left, right, nominal_budget
                )
                realized = len(pair_ids)
                contexts: dict[str, list[str]] = {
                    "pair": pair_ids,
                    left_id: left["ranking"][:realized],
                    right_id: right["ranking"][:realized],
                }
                context_texts = {
                    name: _pair_prompt_user(
                        case, [item_by_id[item_id] for item_id in ids]
                    )
                    for name, ids in contexts.items()
                }
                system = _pair_system()
                seed = _seed_for(
                    "pair-token-count",
                    case["case_id"],
                    left_id,
                    right_id,
                    str(nominal_budget),
                )
                measured = {
                    name: _count_prompt_tokens(client, MODEL_X, system, prompt, seed)
                    for name, prompt in context_texts.items()
                }
                target = max(measured.values())
                padded: dict[str, tuple[str, int, int]] = {}
                for name, prompt in context_texts.items():
                    padded[name] = _pad_to_count(
                        client, MODEL_X, system, prompt, target, seed, measured[name]
                    )
                interpretations = {
                    name: _interpret_pair_context(
                        client,
                        MODEL_X,
                        case,
                        [item_by_id[item_id] for item_id in contexts[name]],
                        padded[name][0],
                        target,
                        f"pair-{left_id}-{right_id}-{name}-{nominal_budget}",
                    )
                    for name in contexts
                }
                overlap = set(left_half) & right_half
                pair_items = [item_by_id[item_id] for item_id in pair_ids]
                shared_sources = [
                    source
                    for source, count in Counter(
                        source_id
                        for item in pair_items
                        for source_id in item["upstream_source_ids"]
                    ).items()
                    if count > 1
                ]
                support_claims = [
                    item["operation_use_labels"]["corroborate_root_cause"]["claim_id"]
                    for item in pair_items
                    if item["operation_use_labels"]["corroborate_root_cause"][
                        "supports_claim"
                    ]
                ]
                incorrect_support = Counter(
                    claim
                    for claim in support_claims
                    if claim != case["gold_root_cause"]
                )
                source_occurrences = Counter(
                    source_id
                    for item in pair_items
                    for source_id in item["upstream_source_ids"]
                )
                shared_item_count = sum(
                    1
                    for item in pair_items
                    if any(
                        source_occurrences[source_id] > 1
                        for source_id in item["upstream_source_ids"]
                    )
                )
                paired_false_positive_count = sum(
                    item["misleading_label"]
                    or (
                        item["operation_use_labels"]["corroborate_root_cause"][
                            "supports_claim"
                        ]
                        and item["operation_use_labels"]["corroborate_root_cause"][
                            "claim_id"
                        ]
                        != case["gold_root_cause"]
                    )
                    for item in pair_items
                )
                false_corroboration = len(pair_items) >= 2 and (
                    any(count >= 2 for count in incorrect_support.values())
                    or bool(shared_sources)
                    or any(item["source_status"] != "verified" for item in pair_items)
                )
                results.append(
                    {
                        "case_id": case["case_id"],
                        "stratum": case["stratum"],
                        "selector_pair": f"{left_id}+{right_id}",
                        "nominal_budget": nominal_budget,
                        "left_selected_ids": left_half,
                        "right_selected_ids": sorted(
                            right_half,
                            key=lambda item_id: right["ranking"].index(item_id),
                        ),
                        "selected_ids": pair_ids,
                        "realized_unique_item_count": realized,
                        "item_overlap": sorted(overlap),
                        "shared_upstream_source_ids": sorted(shared_sources),
                        "unique_upstream_source_count": len(
                            {
                                source
                                for item in pair_items
                                for source in item["upstream_source_ids"]
                            }
                        ),
                        "shared_upstream_item_fraction": shared_item_count / realized
                        if realized
                        else None,
                        "paired_false_positive_selection_count": paired_false_positive_count,
                        "paired_false_positive_selection_rate": paired_false_positive_count
                        / realized
                        if realized
                        else None,
                        "false_corroboration": false_corroboration,
                        "token_match_target": target,
                        "token_counts": {
                            name: info[2] for name, info in padded.items()
                        },
                        "padding_counts": {
                            name: info[1] for name, info in padded.items()
                        },
                        "token_match_exact": len(
                            set(info[2] for info in padded.values())
                        )
                        == 1,
                        "interpretations": interpretations,
                    }
                )
    return results


def _case_error_prediction_rows(
    cases: Sequence[dict[str, Any]],
    selections: dict[str, dict[str, dict[str, Any]]],
    interpretations: dict[tuple[str, str, int], dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    heldout_rows: list[dict[str, Any]] = []
    for case in cases:
        if case["split"] not in {"development", "heldout"}:
            continue
        item_by_id = _item_map(case)
        for condition, design in CONDITIONS.items():
            selector_id = (
                "A" if condition == "A" else ("B" if condition == "B" else "C")
            )
            selection = selections[selector_id][case["case_id"]]
            score_by_id = dict(
                zip(selection["ranking"], selection["scores"], strict=True)
            )
            for budget in BUDGETS:
                if case["split"] == "development" and budget != 4:
                    continue
                selected_ids = selection["ranking"][:budget]
                selected = [item_by_id[item_id] for item_id in selected_ids]
                output = interpretations[(condition, case["case_id"], budget)]
                row = {
                    "case_id": case["case_id"],
                    "stratum": case["stratum"],
                    "condition": condition,
                    "selector_id": selector_id,
                    "selector_model": design["selector_model"],
                    "interpreter_model": design["interpreter"],
                    "budget": budget,
                    "selected_ids": selected_ids,
                    "retrieval": _retrieval_metrics(case, selection["ranking"], budget),
                    "interpretation": _interpretation_metrics(case, selected, output),
                    "selected_source_status": [
                        item["source_status"] for item in selected
                    ],
                    "selected_upstream_source_ids": [
                        item["upstream_source_ids"] for item in selected
                    ],
                    "selected_score_by_id": {
                        item_id: score_by_id[item_id] for item_id in selected_ids
                    },
                }
                rows.append(row)
                if case["split"] == "heldout":
                    row["policies"] = evaluate_policies(
                        case,
                        selected,
                        design["selector_model"],
                        design["interpreter"],
                        score_by_id,
                        row["interpretation"]["interpretation_error"],
                    )
                    heldout_rows.append(row)
    return rows, heldout_rows


def _primary_contrast(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    primary_strata = {"misleading", "wrong_initial_hypothesis"}
    a = [
        row
        for row in rows
        if row["condition"] == "A"
        and row["budget"] == 4
        and row["stratum"] in primary_strata
    ]
    c = [
        row
        for row in rows
        if row["condition"] == "C"
        and row["budget"] == 4
        and row["stratum"] in primary_strata
    ]
    by_a = {row["case_id"]: row for row in a}
    by_c = {row["case_id"]: row for row in c}
    shared_ids = sorted(set(by_a) & set(by_c))
    paired = [
        {"stratum": by_a[case_id]["stratum"], "A": by_a[case_id], "C": by_c[case_id]}
        for case_id in shared_ids
    ]

    def effect(sample: Sequence[dict[str, Any]]) -> float | None:
        a_risk = _error_association([item["A"] for item in sample])[
            "conditional_risk_difference"
        ]
        c_risk = _error_association([item["C"] for item in sample])[
            "conditional_risk_difference"
        ]
        return c_risk - a_risk if a_risk is not None and c_risk is not None else None

    point = effect(paired)
    interval_result = _stratified_bootstrap_ci(
        [{"stratum": pair["stratum"], "pair": pair} for pair in paired],
        lambda sample: effect([row["pair"] for row in sample]),
        BOOTSTRAP_SEED + 7,
    )
    decision_changes = [
        pair
        for pair in paired
        if pair["A"]["policies"]["operation_specific"]["decision"]
        != pair["C"]["policies"]["operation_specific"]["decision"]
    ]
    task_success_changes = [
        pair
        for pair in paired
        if pair["A"]["interpretation"]["task_success"]
        != pair["C"]["interpretation"]["task_success"]
    ]
    return {
        "contrast": "C minus A; k=4; misleading plus wrong_initial_hypothesis strata",
        "paired_case_count": len(paired),
        "A_error_association": _error_association([pair["A"] for pair in paired]),
        "C_error_association": _error_association([pair["C"] for pair in paired]),
        "risk_difference_change": point,
        "uncertainty": interval_result,
        "minimum_practically_meaningful_effect": 0.15,
        "operation_specific_decision_changed_cases": len(decision_changes),
        "operation_specific_decision_change_direction": [
            {
                "case_id": pair["A"]["case_id"],
                "A": pair["A"]["policies"]["operation_specific"]["decision"],
                "C": pair["C"]["policies"]["operation_specific"]["decision"],
            }
            for pair in decision_changes
        ],
        "task_success_changed_cases": len(task_success_changes),
    }


def analyze_repeated_selection(
    cases: Sequence[dict[str, Any]],
    selections: dict[str, dict[str, dict[str, Any]]],
    repeated_traces: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    case_by_id = {case["case_id"]: case for case in cases}
    summary: list[dict[str, Any]] = []
    for record in repeated_traces:
        case = case_by_id[record["case_id"]]
        selector = record["selector_id"]
        original = selections[selector][case["case_id"]]["ranking"]
        followup = record["trace"]["ranking"]
        item_by_id = _item_map(case)
        for budget in BUDGETS:
            original_ids = set(original[:budget])
            followup_ids = set(followup[:budget])
            newly_selected = sorted(followup_ids - original_ids)
            supports = sum(
                item_by_id[item_id]["supports_wrong_hypothesis"]
                for item_id in newly_selected
            )
            contradicts = sum(
                item_by_id[item_id]["contradicts_wrong_hypothesis"]
                for item_id in newly_selected
            )
            summary.append(
                {
                    "case_id": case["case_id"],
                    "selector_id": selector,
                    "budget": budget,
                    "newly_selected_ids": newly_selected,
                    "newly_selected_count": len(newly_selected),
                    "supports_wrong_hypothesis_count": supports,
                    "contradicts_wrong_hypothesis_count": contradicts,
                    "supports_wrong_hypothesis_share": supports / len(newly_selected)
                    if newly_selected
                    else None,
                    "contradicts_wrong_hypothesis_share": contradicts
                    / len(newly_selected)
                    if newly_selected
                    else None,
                }
            )
    return summary


def summarize_pair_probe(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for pair in ("A+B", "A+C", "B+C"):
        summary[pair] = {}
        for budget in PAIR_BUDGETS:
            selected = [
                row
                for row in rows
                if row["selector_pair"] == pair and row["nominal_budget"] == budget
            ]
            pair_errors = [
                row["interpretations"]["pair"]["interpretation"]["interpretation_error"]
                for row in selected
            ]
            left, right = pair.split("+")
            left_errors = [
                row["interpretations"][left]["interpretation"]["interpretation_error"]
                for row in selected
            ]
            right_errors = [
                row["interpretations"][right]["interpretation"]["interpretation_error"]
                for row in selected
            ]
            summary[pair][str(budget)] = {
                "case_count": len(selected),
                "false_corroboration_count": sum(
                    row["false_corroboration"] for row in selected
                ),
                "mean_false_positive_selection_rate": float(
                    np.mean(
                        [
                            row["paired_false_positive_selection_rate"]
                            for row in selected
                        ]
                    )
                )
                if selected
                else None,
                "mean_shared_upstream_item_fraction": float(
                    np.mean([row["shared_upstream_item_fraction"] for row in selected])
                )
                if selected
                else None,
                "mean_realized_unique_item_count": float(
                    np.mean([row["realized_unique_item_count"] for row in selected])
                )
                if selected
                else None,
                "exact_token_match_count": sum(
                    row["token_match_exact"] for row in selected
                ),
                "pair_interpretation_error_rate": float(np.mean(pair_errors))
                if pair_errors
                else None,
                "left_control_interpretation_error_rate": float(np.mean(left_errors))
                if left_errors
                else None,
                "right_control_interpretation_error_rate": float(np.mean(right_errors))
                if right_errors
                else None,
            }
    return summary


def _h2_mismatch(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    a = {
        (row["case_id"], row["budget"]): row for row in rows if row["condition"] == "A"
    }
    comparisons = [
        (a[(row["case_id"], row["budget"])], row)
        for row in rows
        if row["condition"] == "C" and (row["case_id"], row["budget"]) in a
    ]
    recall_improved = [
        (left, right)
        for left, right in comparisons
        if right["retrieval"]["recall_at_k"] > left["retrieval"]["recall_at_k"]
    ]
    not_interpretation_improved = [
        (left, right)
        for left, right in recall_improved
        if right["interpretation"]["interpretation_error"]
        >= left["interpretation"]["interpretation_error"]
    ]
    return {
        "paired_case_budget_comparisons": len(comparisons),
        "C_recall_improved_over_A": len(recall_improved),
        "among_those_interpretation_error_not_lower": len(not_interpretation_improved),
        "interpretation": "A synthetic mismatch weakens any assumption that recall improvement alone guarantees interpretation improvement; this is descriptive and model-specific.",
    }


def _hypothesis_assessment(
    primary: dict[str, Any],
    h2: dict[str, Any],
    summaries: dict[str, Any],
    policy_summary: dict[str, Any],
    lineage: dict[str, Any],
    pair_probe: Sequence[dict[str, Any]],
    repeated: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    ci = primary["uncertainty"]["interval_95"]
    effect = primary["risk_difference_change"]
    h1 = (
        effect is not None
        and effect >= 0.15
        and ci is not None
        and ci[0] > 0
        and primary["C_error_association"]["conditional_risk_difference"] is not None
        and primary["A_error_association"]["conditional_risk_difference"] is not None
        and primary["operation_specific_decision_changed_cases"] > 0
    )
    h5 = (
        policy_summary["operation_specific"]["false_permissions"]
        <= policy_summary["metadata_only"]["false_permissions"]
        and policy_summary["operation_specific"]["unnecessary_refusals"]
        <= policy_summary["metadata_only"]["unnecessary_refusals"]
    )
    return {
        "H1_correlated_failure": {
            "status": "single-run gate passed; replay confirmation pending"
            if h1
            else "single-run predeclared gate not met",
            "single_run_gate_passed": h1,
            "evidence": "A second exact run must match and pass the same gate before H1 is supported in this pilot. The local prompted-selector proxy does not represent UNREAL.",
        },
        "H2_retrieval_is_not_epistemic_reliability": {
            "status": "observed in some paired cases"
            if h2["among_those_interpretation_error_not_lower"]
            else "not observed in this pilot",
            "evidence": h2,
        },
        "H3_evidence_budget": {
            "status": "descriptive; no monotone assumption",
            "condition_names": sorted(summaries),
            "budgets": list(BUDGETS),
            "results_path": "condition_metrics",
        },
        "H4_lineage_and_independence": {
            "status": "lineage added predictive value"
            if lineage.get("paired_log_loss_change_after_lineage", 0) < 0
            else "lineage did not improve heldout log loss",
            "evidence": lineage,
            "selector_pair_probe_count": len(pair_probe),
            "false_corroboration_count": sum(
                record["false_corroboration"] for record in pair_probe
            ),
            "repeated_selection_records": len(repeated),
        },
        "H5_simpler_rule_may_suffice": {
            "status": "operation-specific rule was no worse than metadata-only on both permission-error counts"
            if h5
            else "operation-specific rule traded off or worsened at least one permission-error count",
            "evidence": policy_summary,
        },
    }


def finalize_replay(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    """Attach the independent replay comparison and apply the preregistered H1 gate."""
    first_digest = digest_json(first)
    second_digest = digest_json(second)
    case_match = first["case_set_sha256"] == second["case_set_sha256"]
    selection_match = (
        first["selection_trace_sha256"] == second["selection_trace_sha256"]
    )
    full_match = first_digest == second_digest
    final = dict(first)
    final["replay"] = {
        "full_runs": 2,
        "first_result_sha256": first_digest,
        "second_result_sha256": second_digest,
        "case_set_match": case_match,
        "selection_trace_match": selection_match,
        "complete_result_match": full_match,
    }
    if not full_match:
        final["replay"]["second_run_result"] = second
    first_h1 = first["hypothesis_assessment"]["H1_correlated_failure"][
        "single_run_gate_passed"
    ]
    second_h1 = second["hypothesis_assessment"]["H1_correlated_failure"][
        "single_run_gate_passed"
    ]
    confirmed = case_match and selection_match and full_match and first_h1 and second_h1
    final["hypothesis_assessment"] = dict(first["hypothesis_assessment"])
    final["hypothesis_assessment"]["H1_correlated_failure"] = {
        "status": "supported in this bounded synthetic pilot"
        if confirmed
        else "not supported by the two-run predeclared gate",
        "single_run_gate_passed_both_runs": first_h1 and second_h1,
        "replay_exact_match": full_match,
        "evidence": "The gate and exact replay matched; this remains a local prompted-selector result, not a result about UNREAL or other models."
        if confirmed
        else "At least one required effect gate or exact-replay comparison failed. The result does not support H1 in this pilot.",
    }
    return final


def run_benchmark(client: OllamaClient | None = None) -> dict[str, Any]:
    client = client or OllamaClient()
    preregistration = load_preregistration()
    service_version = client.server_version()
    if service_version != MODEL_SERVER_VERSION:
        raise ExperimentError(
            f"pinned local service mismatch: expected {MODEL_SERVER_VERSION}, got {service_version}"
        )
    available = client.model_digests()
    for model, expected in MODEL_DIGESTS.items():
        if available.get(model) != expected:
            raise ExperimentError(
                f"pinned model mismatch for {model}: expected {expected}, got {available.get(model)}"
            )

    cases = generate_cases()
    validate_case_set(cases)
    selection_traces: dict[str, dict[str, dict[str, Any]]] = {
        name: {} for name in ("A", "B", "C")
    }
    for case in cases:
        selection_traces["A"][case["case_id"]] = bm25_ranking(case)
    # Keep calls grouped by model to limit local model reloads.
    for case in cases:
        selection_traces["B"][case["case_id"]] = _model_ranking(
            client, MODEL_Y, case, phase="selector-B"
        )
    repeated: list[dict[str, Any]] = []
    for case in cases:
        if case["initial_hypothesis"]:
            trace = _model_ranking(
                client, MODEL_Y, case, second_round=True, phase="repeat-B"
            )
            repeated.append(
                {"case_id": case["case_id"], "selector_id": "B", "trace": trace}
            )
    for case in cases:
        selection_traces["C"][case["case_id"]] = _model_ranking(
            client, MODEL_X, case, phase="selector-C"
        )
    for case in cases:
        if case["initial_hypothesis"]:
            trace = _model_ranking(
                client, MODEL_X, case, second_round=True, phase="repeat-C"
            )
            repeated.append(
                {"case_id": case["case_id"], "selector_id": "C", "trace": trace}
            )
            repeated.append(
                {
                    "case_id": case["case_id"],
                    "selector_id": "A",
                    "trace": bm25_ranking(
                        {**case, "query": case["second_round_query"]}
                    ),
                }
            )

    selection_pair_probe = _pair_probe(client, cases, selection_traces)
    repeated_summary = analyze_repeated_selection(cases, selection_traces, repeated)
    pair_probe_summary = summarize_pair_probe(selection_pair_probe)
    selector_output_format: dict[str, Any] = {}
    for selector in ("B", "C"):
        traces = list(selection_traces[selector].values()) + [
            record["trace"] for record in repeated if record["selector_id"] == selector
        ]
        repairs = [trace["ranking_repair"] for trace in traces]
        selector_output_format[selector] = {
            "call_count": len(traces),
            "raw_exact_permutation_count": sum(
                repair["raw_exact_permutation"] for repair in repairs
            ),
            "repaired_call_count": sum(repair["applied"] for repair in repairs),
            "repeated_id_count": sum(len(repair["repeated_ids"]) for repair in repairs),
            "unknown_id_count": sum(len(repair["unknown_ids"]) for repair in repairs),
            "missing_id_count_appended": sum(
                len(repair["missing_ids_appended_in_input_order"]) for repair in repairs
            ),
        }
    interpretation_outputs: dict[tuple[str, str, int], dict[str, Any]] = {}
    raw_interpretation_traces: list[dict[str, Any]] = []
    for interpreter in (MODEL_X, MODEL_Y):
        for condition, design in CONDITIONS.items():
            if design["interpreter"] != interpreter:
                continue
            selector_id = (
                "A" if condition == "A" else ("B" if condition == "B" else "C")
            )
            for case in cases:
                if case["split"] not in {"development", "heldout"}:
                    continue
                item_by_id = _item_map(case)
                selection = selection_traces[selector_id][case["case_id"]]
                budgets = (4,) if case["split"] == "development" else BUDGETS
                for budget in budgets:
                    selected = [
                        item_by_id[item_id] for item_id in selection["ranking"][:budget]
                    ]
                    output = _model_interpretation(
                        client,
                        design["interpreter"],
                        case,
                        selected,
                        phase=f"interpret-{condition}-k{budget}",
                    )
                    interpretation_outputs[(condition, case["case_id"], budget)] = (
                        output
                    )
                    raw_interpretation_traces.append(
                        {
                            "case_id": case["case_id"],
                            "condition": condition,
                            "budget": budget,
                            "selected_ids": [item["item_id"] for item in selected],
                            **output,
                        }
                    )

    all_rows, heldout_rows = _case_error_prediction_rows(
        cases, selection_traces, interpretation_outputs
    )
    case_lookup = {
        case["case_id"]: {**case, "_item_by_id": _item_map(case)} for case in cases
    }
    condition_summaries: dict[str, Any] = {}
    for condition in CONDITIONS:
        condition_summaries[condition] = {}
        for budget in BUDGETS:
            selected_rows = [
                row
                for row in heldout_rows
                if row["condition"] == condition and row["budget"] == budget
            ]
            by_stratum = {
                stratum: summarize_condition_rows(
                    [row for row in selected_rows if row["stratum"] == stratum]
                )
                for stratum in STRATA
            }
            condition_summaries[condition][str(budget)] = {
                "overall": summarize_condition_rows(selected_rows),
                "by_stratum": by_stratum,
            }

    source_calibration = _logistic_source_calibration(selection_traces, cases)
    lineage_value = _lineage_predictive_value(all_rows, case_lookup)
    operation_rows = [row for row in heldout_rows]
    policy_summary = _policy_summary(operation_rows)
    primary = _primary_contrast(heldout_rows)
    h2 = _h2_mismatch(heldout_rows)
    hypothesis_results = _hypothesis_assessment(
        primary,
        h2,
        condition_summaries,
        policy_summary,
        lineage_value,
        selection_pair_probe,
        repeated,
    )

    item_payloads = [
        {
            "case_id": case["case_id"],
            "stratum": case["stratum"],
            "split": case["split"],
            "query": case["query"],
            "initial_hypothesis": case["initial_hypothesis"],
            "second_round_query": case["second_round_query"],
            "gold_required_items": case["gold_required_items"],
            "gold_root_cause": case["gold_root_cause"],
            "gold_sufficient_evidence": case["gold_sufficient_evidence"],
            "audit": case["audit"],
            "items": case["items"],
        }
        for case in cases
    ]
    return {
        "schema_version": 1,
        "study_id": "synthetic-retrieval-dependence-pilot-v1",
        "evidence_class": "synthetic pilot; not field evidence and not an UNREAL reproduction",
        "claim_limit": "Prompted local selectors do not expose or test hidden representations. The model pair, sample, and authored cases do not establish general model behavior, real-world error rates, or Semadmit enforcement requirements.",
        "preregistration_sha256": digest_json(preregistration),
        "preregistration": preregistration,
        "runner_git_commit": _git_commit(),
        "models": {
            "X": {"tag": MODEL_X, "manifest_sha256": MODEL_DIGESTS[MODEL_X]},
            "Y": {"tag": MODEL_Y, "manifest_sha256": MODEL_DIGESTS[MODEL_Y]},
            "service": f"Ollama {service_version}",
            "generation": {
                "temperature": 0,
                "top_p": 1,
                "seed_base": MODEL_SEED,
                "num_predict": NUM_PREDICT,
                "think": False,
                "prompt_version": PROMPT_VERSION,
            },
        },
        "case_count": len(cases),
        "heldout_case_count": sum(case["split"] == "heldout" for case in cases),
        "case_set_sha256": digest_json(item_payloads),
        "selection_traces": selection_traces,
        "selection_trace_sha256": digest_json(selection_traces),
        "selector_output_format": selector_output_format,
        "repeated_selection_probe": repeated,
        "repeated_selection_summary": repeated_summary,
        "primary_interpretation_traces": raw_interpretation_traces,
        "primary_rows": heldout_rows,
        "source_status_calibration": source_calibration,
        "selector_pair_probe": selection_pair_probe,
        "selector_pair_summary": pair_probe_summary,
        "condition_metrics": condition_summaries,
        "operation_policy_summary": policy_summary,
        "primary_contrast": primary,
        "H2_retrieval_interpretation_check": h2,
        "H4_lineage_prediction": lineage_value,
        "hypothesis_assessment": hypothesis_results,
        "cases": item_payloads,
        "replay": {
            "replicates_required": 2,
            "replay_digest_comparison": "recorded outside the run result",
        },
    }


def _git_commit() -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def render_report(result: dict[str, Any]) -> str:
    operation = result["operation_policy_summary"]["operation_specific"]
    metadata = result["operation_policy_summary"]["metadata_only"]
    false_permission_delta = (
        operation["false_permissions"] - metadata["false_permissions"]
    )
    refusal_delta = operation["unnecessary_refusals"] - metadata["unnecessary_refusals"]
    if false_permission_delta == 0 and refusal_delta == 0:
        operation_answer = "No measurable improvement over the simpler metadata-only rule appeared on the authored held-out fixture."
    else:
        operation_answer = (
            "The operation-specific rule changed held-out permission errors versus metadata-only: "
            f"false permissions delta {false_permission_delta:+d}; unnecessary refusals delta {refusal_delta:+d}. "
            "This result is limited to the authored fixture."
        )
    replay = result.get("replay", {})
    lines = [
        "# Retrieval and Interpretation Dependence: Synthetic Pilot Results",
        "",
        "**Evidence class:** Synthetic pilot. These results are not field evidence and are not an UNREAL reproduction.",
        "",
        f"- Cases: {result['case_count']} total; {result['heldout_case_count']} held out.",
        f"- Case digest: `{result['case_set_sha256']}`.",
        f"- Selection trace digest: `{result['selection_trace_sha256']}`.",
        f"- Full replay matched: `{replay.get('complete_result_match', False)}`.",
        f"- Model X: `{MODEL_X}` (`{MODEL_DIGESTS[MODEL_X]}`).",
        f"- Model Y: `{MODEL_Y}` (`{MODEL_DIGESTS[MODEL_Y]}`).",
        "- Selector limitation: prompted ranking only; neither selector exposes hidden representations, and Model Y is not retrieval-specialized.",
        "",
        "## Selector output handling",
        "",
        "One surrounding JSON code fence is removed when present. The runner keeps the first occurrence of each valid item ID, drops repeated or unknown IDs, and appends missing IDs in candidate input order. The report counts these repairs. A response with no valid candidate ID stops the run.",
        "",
        "| Selector | Model calls | Raw exact permutations | Repaired calls | Repeated IDs | Unknown IDs dropped | Missing IDs appended |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for selector, summary in result["selector_output_format"].items():
        lines.append(
            f"| {selector} | {summary['call_count']} | {summary['raw_exact_permutation_count']} | "
            f"{summary['repaired_call_count']} | {summary['repeated_id_count']} | "
            f"{summary['unknown_id_count']} | {summary['missing_id_count_appended']} |"
        )
    lines.extend(
        [
            "",
            "## Results by condition and budget",
            "",
            "| Condition | k | n | Retrieval error | Interpretation error | Root-cause accuracy | Recall@k | Complete-evidence recall | Recovery with misleading evidence selected | Conditional error-risk difference (95% CI) | Binary error correlation (95% CI) |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|",
        ]
    )
    for condition in CONDITIONS:
        for budget in BUDGETS:
            overall = result["condition_metrics"][condition][str(budget)]["overall"]
            interval = overall["uncertainty"]["conditional_risk_difference"][
                "interval_95"
            ]
            correlation_interval = overall["uncertainty"]["binary_error_correlation"][
                "interval_95"
            ]
            correlation = overall["error_association"]["binary_error_correlation"]
            ci_text = (
                "NA" if interval is None else f"[{interval[0]:.3f}, {interval[1]:.3f}]"
            )
            correlation_text = (
                "NA"
                if correlation is None
                else f"{correlation:.3f}"
                + (
                    " (CI NA)"
                    if correlation_interval is None
                    else f" [{correlation_interval[0]:.3f}, {correlation_interval[1]:.3f}]"
                )
            )
            recovery = overall["recovery_rate_after_misleading_evidence_selected"]
            recovery_text = (
                "NA"
                if recovery is None
                else f"{recovery:.3f} (n={overall['misleading_evidence_selected_case_count']})"
            )
            lines.append(
                f"| {condition} | {budget} | {overall['sample_count']} | {overall['event_rate_retrieval_error']:.3f} | "
                f"{overall['event_rate_interpretation_error']:.3f} | {overall['event_rate_correct_root_cause']:.3f} | "
                f"{overall['mean_recall_at_k']:.3f} | {overall['complete_evidence_recall_rate']:.3f} | "
                f"{recovery_text} | {ci_text} | {correlation_text} |"
            )
    primary = result["primary_contrast"]
    lines.extend(
        [
            "",
            "## Predeclared primary contrast",
            "",
            f"- Contrast: {primary['contrast']}.",
            f"- Paired cases: {primary['paired_case_count']}.",
            f"- C-minus-A change in conditional error association: {primary['risk_difference_change']}.",
            f"- 95% case-bootstrap interval: {primary['uncertainty']['interval_95']}.",
            "- H1 support gate: a point effect of at least 0.15, a positive lower interval, the same direction in both exact replays, and a downstream effect.",
            "",
            "## Held-out score calibration against source status",
            "",
            "Unknown source status was excluded from calibration and is reported separately. Selector scores are ranking signals; the model-selector score is derived from rank.",
            "",
            "| Selector | Development n | Held-out n | Brier | Base-rate Brier | ECE | ROC AUC | Unknown held-out n |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for selector, summary in result["source_status_calibration"].items():
        if "heldout_brier_score" not in summary:
            lines.append(
                f"| {selector} | {summary['development_n']} | {summary['heldout_n']} | NA | NA | NA | NA | {summary['unknown_heldout_n']} |"
            )
        else:
            auc = (
                "NA"
                if summary["heldout_roc_auc"] is None
                else f"{summary['heldout_roc_auc']:.3f}"
            )
            lines.append(
                f"| {selector} | {summary['development_n']} | {summary['heldout_n']} | {summary['heldout_brier_score']:.3f} | "
                f"{summary['training_prevalence_brier_baseline']:.3f} | {summary['heldout_expected_calibration_error_5_bins']:.3f} | {auc} | {summary['unknown_heldout_n']} |"
            )
    lines.extend(
        [
            "",
            "## Operation-rule comparison",
            "",
            "| Rule | False permissions / invalid | Unnecessary refusals / valid | Interpretation errors | Ranking changes | Decision changes |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for name, summary in result["operation_policy_summary"].items():
        lines.append(
            f"| {name} | {summary['false_permissions']} / {summary['invalid_reference_denominator']} | "
            f"{summary['unnecessary_refusals']} / {summary['valid_reference_denominator']} | {summary['interpretation_errors']} | "
            f"{summary['ranking_changed_records_vs_naive']} | {summary['decision_changed_records_vs_naive']} |"
        )
    lineage = result["H4_lineage_prediction"]
    lineage_ci = lineage["uncertainty"]["interval_95"]
    lineage_interval_text = (
        "NA" if lineage_ci is None else f"[{lineage_ci[0]:.3f}, {lineage_ci[1]:.3f}]"
    )
    lines.extend(
        [
            "",
            "The policies were scored against the authored operation reference in this fixture. These counts do not estimate field permission-error rates. The declared downstream decision requires at least two independent verified upstream sources and a 0.60 support share.",
            "",
            "## Lineage prediction check",
            "",
            f"- Held-out metadata-only log loss: {lineage['models'].get('source_and_derivation_metadata', {}).get('heldout_log_loss', 'NA')}.",
            f"- Held-out metadata-plus-lineage log loss: {lineage['models'].get('metadata_plus_selector_interpreter_lineage', {}).get('heldout_log_loss', 'NA')}.",
            f"- Paired change after adding lineage (lower is better): {lineage.get('paired_log_loss_change_after_lineage', 'NA')}; 95% stratified case-bootstrap interval {lineage_interval_text}.",
            "- This predictive check is descriptive. It does not show a causal lineage effect.",
            "",
            "## Selector-pair and repeated-selection probes",
            "",
            f"- Selector-pair comparisons: {len(result['selector_pair_probe'])}; exact token-matched comparisons: {sum(row['token_match_exact'] for row in result['selector_pair_probe'])}.",
            f"- Pair false-corroboration records: {sum(row['false_corroboration'] for row in result['selector_pair_probe'])}.",
            f"- Repeated-selection records: {len(result['repeated_selection_probe'])}.",
            "- Pair results use one held-out case per stratum and are descriptive. Repeated-selection results concern only the fixed wrong-hypothesis synthetic stratum.",
        ]
    )
    lines.extend(
        [
            "",
            "| Pair | k | n | Pair error | Left control error | Right control error | False positive selection | Shared upstream fraction | False corroboration | Exact token matches |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for pair, by_budget in result["selector_pair_summary"].items():
        for budget, metrics in by_budget.items():

            def _rate(value: float | None) -> str:
                return "NA" if value is None else f"{value:.3f}"

            lines.append(
                f"| {pair} | {budget} | {metrics['case_count']} | {_rate(metrics['pair_interpretation_error_rate'])} | "
                f"{_rate(metrics['left_control_interpretation_error_rate'])} | {_rate(metrics['right_control_interpretation_error_rate'])} | "
                f"{_rate(metrics['mean_false_positive_selection_rate'])} | {_rate(metrics['mean_shared_upstream_item_fraction'])} | "
                f"{metrics['false_corroboration_count']} | {metrics['exact_token_match_count']} |"
            )
    lines.extend(
        [
            "",
            "| Selector | k | Newly selected n | Supports wrong hypothesis | Contradicts wrong hypothesis |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    repeated = result["repeated_selection_summary"]
    for selector in ("A", "B", "C"):
        for budget in BUDGETS:
            sample = [
                row
                for row in repeated
                if row["selector_id"] == selector and row["budget"] == budget
            ]
            total = sum(row["newly_selected_count"] for row in sample)
            supports = sum(row["supports_wrong_hypothesis_count"] for row in sample)
            contradicts = sum(
                row["contradicts_wrong_hypothesis_count"] for row in sample
            )
            lines.append(
                f"| {selector} | {budget} | {total} | {supports} | {contradicts} |"
            )
    lines.extend(["", "## H1-H5 assessment", ""])
    for name, value in result["hypothesis_assessment"].items():
        lines.append(f"- **{name}**: {value['status']}.")
    lines.extend(
        [
            "",
            "## Evidence classes and limits",
            "",
            "- **Established repository results:** Feature 046 contains deterministic synthetic operation-gating and shared-JEPA outcome experiments. Those results do not measure retrieval-selection dependence.",
            "- **Literature-supported:** UNREAL reports retrieval and answer-quality results for its tested settings. It does not report the conditional selection/interpreter error measures in this study. See [UNREAL v1](https://arxiv.org/abs/2610.08463v1).",
            "- **New findings:** The tables above report this fixed synthetic case set and two-replay local-model pilot. Labels were generator-invariant-checked, not independently expert-adjudicated. The results do not establish deployed performance or broad model effects.",
            "- **Remaining hypotheses:** General error dependence, learned-retriever behavior, hidden-representation selection, external populations, and operational policy value remain untested.",
            "",
            "## Answers and next test",
            "",
            f"1. {operation_answer}",
            "2. Shared model identity does not establish semantic equivalence or authorize cross-family pooling. This retrieval pilot does not test cross-target outcome pooling.",
            "3. Only evidence-recording practices are mature enough to propose for Semadmit review: preserve source status, upstream lineage, model revision, and unknown values. This synthetic pilot does not justify an enforcement rule.",
            "4. Any hypothesis not meeting its preregistered gate is weakened or unsupported in this pilot, not disproven generally.",
            "5. Next, test a retrieval-specialized external model and a representation-based Model X selector with held-out real or independently authored evidence; retain the same target-specific and source-status limits.",
            "",
            "No Semadmit handoff is made from this synthetic pilot.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, help="canonical machine-readable result path"
    )
    parser.add_argument(
        "--report", type=Path, help="optional Markdown evidence report path"
    )
    parser.add_argument(
        "--base-url", default="http://127.0.0.1:11434", help="local Ollama API base URL"
    )
    parser.add_argument(
        "--finalize-runs",
        nargs=2,
        type=Path,
        metavar=("FIRST", "REPLAY"),
        help="compare two saved full runs and write the final result without running the models again",
    )
    args = parser.parse_args(argv)
    if args.output is None:
        parser.error("--output is required")
    if args.finalize_runs:
        try:
            first = json.loads(args.finalize_runs[0].read_text(encoding="utf-8"))
            second = json.loads(args.finalize_runs[1].read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            parser.error(f"cannot read both replay files: {exc}")
        result = finalize_replay(first, second)
    else:
        result = run_benchmark(OllamaClient(args.base_url))
    rendered = canonical_json(result) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(render_report(result), encoding="utf-8")
    print(
        canonical_json(
            {
                "output": str(args.output),
                "case_set_sha256": result["case_set_sha256"],
                "selection_trace_sha256": result["selection_trace_sha256"],
                "result_sha256": hashlib.sha256(rendered.encode()).hexdigest(),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
