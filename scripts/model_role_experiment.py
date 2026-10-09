"""Run the preregistered synthetic model-role and score-commensurability study."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import re
import statistics
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from scripts import model_role_metrics as metrics
from scripts.model_role_embedding import HuggingFaceSentenceTransformerEmbedder

ROOT = Path(__file__).resolve().parents[1]
PREREG_PATH = (
    ROOT / "specs/047-retrieval-selection-dependence/model-role-preregistration.json"
)
MODEL_KEYS = ("qwen", "gemma", "coder", "embedding", "tev1", "guardian")
JUDGES = ("qwen", "gemma", "guardian")
PROMPT_VERSION = "model-role-relevance-v1"
PROMPT_TEMPLATE = {
    "chat_system": "Estimate each item's relevance probability. Keep source validity and operation use separate.",
    "guardian": "BYOC yes/no relevance judgment in a documented guardian block, one item per call, no thinking.",
    "embedding_query": "task: search result | query: {query}",
    "embedding_document": "title: none | text: {content}",
    "tev1": "native /v1/systemone noul relevance probability",
}


class ExperimentError(RuntimeError):
    """Raised when the study cannot run without guessing."""


class OllamaClient:
    """Small client restricted to a loopback Ollama service."""

    def __init__(self, base_url: str = "http://127.0.0.1:11434", timeout: int = 300):
        host = urllib.parse.urlparse(base_url).hostname
        if host not in {"127.0.0.1", "localhost", "::1"}:
            raise ExperimentError("the study sends prompts only to local Ollama")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _request(
        self, route: str, payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}{route}",
            data=data,
            headers={"Content-Type": "application/json"} if data else {},
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                value = json.load(response)
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            raise ExperimentError(
                f"local Ollama request failed at {route}: {exc}"
            ) from exc
        if not isinstance(value, dict):
            raise ExperimentError(f"local Ollama returned a non-object at {route}")
        return value

    def server_version(self) -> str:
        version = self._request("/api/version").get("version")
        if not isinstance(version, str):
            raise ExperimentError("Ollama returned no version")
        return version

    def model_digests(self, tags: dict[str, str]) -> dict[str, str]:
        result = {}
        for key, tag in tags.items():
            shown = self._request("/api/show", {"model": tag})
            manifests = shown.get("manifests", [])
            selected = [
                m for m in manifests if isinstance(m, dict) and m.get("selected")
            ]
            if len(selected) == 1:
                digest = selected[0].get("digest")
            else:
                listed = self._request("/api/tags").get("models", [])
                matches = [
                    m.get("digest")
                    for m in listed
                    if isinstance(m, dict) and m.get("name") == tag
                ]
                matches = list(dict.fromkeys(matches))
                digest = matches[0] if len(matches) == 1 else None
            if not isinstance(digest, str):
                raise ExperimentError(f"cannot resolve one selected manifest for {tag}")
            result[key] = digest.removeprefix("sha256:")
        return result

    def chat(self, model: str, system: str, user: str, seed: int) -> str:
        return self.chat_messages(
            model,
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            seed,
            json_output=True,
        )

    def chat_messages(
        self,
        model: str,
        messages: list[dict[str, str]],
        seed: int,
        json_output: bool = False,
    ) -> str:
        payload = {
            "model": model,
            "messages": messages,
            "think": False,
            "stream": False,
            "keep_alive": "10m",
            "options": {
                "temperature": 0,
                "top_p": 1,
                "seed": seed,
                "num_ctx": 4096,
                "num_predict": 768,
            },
        }
        if json_output:
            payload["format"] = "json"
        value = self._request("/api/chat", payload)
        message = value.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str):
            raise ExperimentError(f"{model} returned no message content")
        return content

    def system_one(
        self, model: str, state: Any, questions: dict[str, Any], seed: int
    ) -> dict[str, Any]:
        return self._request(
            "/v1/systemone",
            {
                "model": model,
                "state": state,
                "questions": questions,
                "options": {"temperature": 0, "seed": seed},
                "keep_alive": "10m",
            },
        )

    def embed(self, model: str, inputs: list[str]) -> list[list[float]]:
        value = self._request(
            "/api/embed",
            {"model": model, "input": inputs, "truncate": True, "keep_alive": "10m"},
        )
        embeddings = value.get("embeddings")
        if not isinstance(embeddings, list) or len(embeddings) != len(inputs):
            raise ExperimentError(f"{model} returned an invalid embedding batch")
        return embeddings


def load_preregistration(path: Path | None = None) -> dict[str, Any]:
    path = path or PREREG_PATH
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExperimentError(f"cannot read model-role preregistration: {exc}") from exc
    if not isinstance(value, dict):
        raise ExperimentError("model-role preregistration must be an object")
    return value


class ModelRoleClient:
    """Route Ollama roles and one separately pinned HF embedding condition."""

    def __init__(
        self,
        ollama: OllamaClient,
        embedding: HuggingFaceSentenceTransformerEmbedder,
        models: dict[str, Any],
    ) -> None:
        self.ollama = ollama
        self.embedding = embedding
        self.models = models

    def __getattr__(self, name: str) -> Any:
        return getattr(self.ollama, name)

    @property
    def embedding_identity_sha256(self) -> str:
        return self.embedding.identity_sha256

    def model_digests(self, tags: dict[str, str]) -> dict[str, str]:
        ollama_tags = {
            key: tag
            for key, tag in tags.items()
            if self.models[key].get("backend", "ollama") == "ollama"
        }
        result = self.ollama.model_digests(ollama_tags)
        for key in tags.keys() - ollama_tags.keys():
            if key != "embedding" or self.models[key].get("backend") != (
                "sentence-transformers-cpu"
            ):
                raise ExperimentError(f"unsupported model backend for {key}")
            result[key] = self.embedding_identity_sha256
        return result

    def embed(self, model: str, inputs: list[str]) -> list[list[float]]:
        expected_model = self.models["embedding"]["api_model"]
        if model != expected_model:
            raise ExperimentError(
                "embedding request does not match the frozen identity"
            )
        return self.embedding.embed(inputs)

    def embedding_runtime_metadata(self) -> dict[str, Any]:
        return self.embedding.runtime_metadata()


def validate_frozen_plan(prereg: dict[str, Any]) -> None:
    if prereg.get("status") != "frozen before scored calls" or not prereg.get(
        "frozen_date"
    ):
        raise ExperimentError(
            "model-role preregistration must be frozen before scored calls"
        )
    source_hashes = prereg.get("frozen_source_sha256")
    if prereg.get("schema_version") == 2:
        required_sources = {
            "scripts/model_role_experiment.py",
            "scripts/model_role_metrics.py",
            "scripts/model_role_embedding.py",
        }
        if not isinstance(source_hashes, dict) or not required_sources.issubset(
            source_hashes
        ):
            raise ExperimentError(
                "version 2 preregistration needs frozen source hashes"
            )
        if not isinstance(prereg.get("frozen_case_set_sha256"), str) or not isinstance(
            prereg.get("frozen_prompt_template_sha256"), str
        ):
            raise ExperimentError(
                "version 2 preregistration needs frozen case and prompt hashes"
            )
        for key in ("frozen_case_set_sha256", "frozen_prompt_template_sha256"):
            if re.fullmatch(r"[0-9a-f]{64}", prereg[key]) is None:
                raise ExperimentError(f"{key} is not a SHA-256 digest")
        preflight_hashes = prereg.get("preflight_artifacts_sha256")
        required_preflights = {
            "docs/experiments/model-runtime/google-embeddinggemma-2-hf-checkpoint-identity.json",
            "docs/experiments/model-runtime/embeddinggemma-2-hf-cpu-preflight-inputs.json",
            "docs/experiments/model-runtime/embeddinggemma-2-hf-cpu-preflight-output.json",
            "docs/experiments/model-runtime/embeddinggemma-2-hf-cpu-preflight-requirements.txt",
            "docs/experiments/model-runtime/ollama-model-role-load-preflight-2026-10-09.json",
            "docs/experiments/model-runtime/granite-guardian-output-schema-preflight-2026-10-09.json",
        }
        if not isinstance(preflight_hashes, dict) or not required_preflights.issubset(
            preflight_hashes
        ):
            raise ExperimentError(
                "version 2 preregistration needs all runtime preflight hashes"
            )
        for relative_path, expected_hash in preflight_hashes.items():
            if (
                not isinstance(relative_path, str)
                or Path(relative_path).is_absolute()
                or not isinstance(expected_hash, str)
                or re.fullmatch(r"[0-9a-f]{64}", expected_hash) is None
            ):
                raise ExperimentError("runtime preflight hash entry is malformed")
            path = ROOT / relative_path
            try:
                resolved_path = path.resolve()
                resolved_path.relative_to(ROOT.resolve())
                actual_hash = hashlib.sha256(resolved_path.read_bytes()).hexdigest()
            except ValueError as exc:
                raise ExperimentError(
                    "runtime preflight path escapes the repository"
                ) from exc
            except OSError as exc:
                raise ExperimentError(
                    f"cannot read runtime preflight {relative_path}"
                ) from exc
            if actual_hash != expected_hash:
                raise ExperimentError(
                    f"runtime preflight hash mismatch: {relative_path}"
                )
    if source_hashes is None:
        return
    for relative_path, expected_hash in source_hashes.items():
        if (
            not isinstance(relative_path, str)
            or Path(relative_path).is_absolute()
            or not isinstance(expected_hash, str)
            or re.fullmatch(r"[0-9a-f]{64}", expected_hash) is None
        ):
            raise ExperimentError("frozen source hash entry is malformed")
        path = ROOT / relative_path
        try:
            resolved_path = path.resolve()
            resolved_path.relative_to(ROOT.resolve())
            actual_hash = hashlib.sha256(resolved_path.read_bytes()).hexdigest()
        except ValueError as exc:
            raise ExperimentError("frozen source path escapes the repository") from exc
        except OSError as exc:
            raise ExperimentError(f"cannot read frozen source {relative_path}") from exc
        if actual_hash != expected_hash:
            raise ExperimentError(f"frozen source hash mismatch: {relative_path}")


def build_model_role_client(
    prereg: dict[str, Any], base_url: str = "http://127.0.0.1:11434"
) -> Any:
    ollama = OllamaClient(base_url)
    spec = prereg["models"]["embedding"]
    if spec.get("backend", "ollama") == "ollama":
        return ollama
    if spec.get("backend") != "sentence-transformers-cpu":
        raise ExperimentError("unsupported embedding backend")
    lock_path = ROOT / spec["environment_lock_path"]
    try:
        lock_path.resolve().relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ExperimentError(
            "embedding environment lock must be inside the repository"
        ) from exc
    embedder = HuggingFaceSentenceTransformerEmbedder(
        model_id=spec["model_id"],
        revision=spec["revision"],
        files_sha256=spec["checkpoint_files_sha256"],
        dimension=int(spec["dimension"]),
        environment_lock_path=lock_path,
        environment_lock_sha256=spec["environment_lock_sha256"],
    )
    expected_runtime = prereg.get("runtime_matrix", {}).get("embedding", {})
    actual_runtime = embedder.runtime_metadata()
    for key, expected in expected_runtime.items():
        if actual_runtime.get(key) != expected:
            raise ExperimentError(
                f"embedding runtime mismatch for {key}: "
                f"expected {expected}, got {actual_runtime.get(key)}"
            )
    return ModelRoleClient(ollama, embedder, prereg["models"])


def _pin_models(client: Any, prereg: dict[str, Any]) -> tuple[str, dict[str, str]]:
    validate_frozen_plan(prereg)
    models = prereg.get("models", {})
    expected = {}
    for key in MODEL_KEYS:
        spec = models.get(key)
        if (
            not isinstance(spec, dict)
            or not isinstance(spec.get("requested_tag"), str)
            or not isinstance(spec.get("api_model"), str)
            or not spec["api_model"]
        ):
            raise ExperimentError("every model needs requested and API identities")
        backend = spec.get("backend", "ollama")
        if backend == "ollama":
            field, label = "manifest_sha256", "exact manifest digest"
        elif backend == "sentence-transformers-cpu":
            field, label = "identity_sha256", "exact model identity SHA-256"
        else:
            raise ExperimentError(f"unsupported backend for {key}")
        digest = spec.get(field)
        if (
            not isinstance(digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", digest.removeprefix("sha256:")) is None
        ):
            raise ExperimentError(f"every model needs an {label} before scoring")
        expected[key] = digest.removeprefix("sha256:")
    tags = {key: str(models[key]["api_model"]) for key in MODEL_KEYS}
    version = client.server_version()
    if version != prereg.get("service_version"):
        raise ExperimentError(f"Ollama version {version} differs from preregistration")
    digests = client.model_digests(tags)
    if digests != expected:
        raise ExperimentError(
            "one or more selected Ollama model digests differ from preregistration"
        )
    return version, digests


def _native_probabilities(answer: Any, case: dict[str, Any]) -> list[float]:
    if not isinstance(answer, dict):
        raise ValueError("Tev1 answer is not an object")
    labels = case["class_labels"]
    if case["question"]["type"] == "noul":
        p = answer.get("noul")
        if (
            isinstance(p, bool)
            or not isinstance(p, (int, float))
            or not math.isfinite(p)
            or not 0 <= p <= 1
        ):
            raise ValueError("Tev1 returned an invalid native yes/no probability")
        return [1.0 - float(p), float(p)]
    raw = answer.get("probabilities")
    if isinstance(raw, dict):
        if all(label in raw for label in labels):
            probs = [raw[label] for label in labels]
        elif all(str(i) in raw for i in range(len(labels))):
            probs = [raw[str(i)] for i in range(len(labels))]
        else:
            raise ValueError("Tev1 probability keys do not match the declared target")
    elif isinstance(raw, list) and len(raw) == len(labels):
        probs = raw
    else:
        raise ValueError("Tev1 returned no full native probability distribution")
    if any(
        isinstance(p, bool)
        or not isinstance(p, (int, float))
        or not math.isfinite(p)
        or not 0 <= p <= 1
        for p in probs
    ):
        raise ValueError("Tev1 distribution has an invalid probability")
    values = [float(p) for p in probs]
    if abs(sum(values) - 1.0) > 0.02:
        raise ValueError("Tev1 distribution does not sum to one")
    return [p / sum(values) for p in values]


def _decision_question(case: dict[str, Any]) -> dict[str, Any]:
    if case["family"] == "equipment_binary":
        return {
            "type": "noul",
            "instructions": "Is the named bearing fault present?",
            "criteria": {
                "true": "The fault is present.",
                "false": "The fault is absent.",
            },
        }
    if case["family"] == "software_category":
        return {
            "type": "choice",
            "instructions": "Which defect class best explains the behavior?",
            "criteria": case["question"]["criteria"],
        }
    return {
        "type": "score",
        "instructions": "Score the incident severity.",
        "criteria": case["question"]["criteria"],
    }


def _decision_state(case: dict[str, Any]) -> str:
    return case["state"]


def _relevance_state(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "query": case["query"],
        "candidates": [
            {"item_id": i["item_id"], "text": i["text"]} for i in case["items"]
        ],
    }


def _chat_prompt(case: dict[str, Any]) -> str:
    return json.dumps(_relevance_state(case), ensure_ascii=False, sort_keys=True)


def _systemone_relevance(
    client: Any, tag: str, case: dict[str, Any], seed: int
) -> tuple[list[dict[str, Any]], str]:
    state = _relevance_state(case)
    questions = {
        item["item_id"]: {
            "type": "noul",
            "instructions": f"Does evidence {item['item_id']} provide information relevant to answering the query?",
            "criteria": {
                "true": "It bears on the answer to this query.",
                "false": "It does not bear on the answer to this query.",
            },
        }
        for item in case["items"]
    }
    response = client.system_one(tag, state, questions, seed)
    answers = response.get("answers") if isinstance(response, dict) else None
    if not isinstance(answers, dict):
        raise ValueError("Tev1 returned no answers object")
    predictions = []
    for item in case["items"]:
        answer = answers.get(item["item_id"])
        p = answer.get("noul") if isinstance(answer, dict) else None
        if (
            isinstance(p, bool)
            or not isinstance(p, (int, float))
            or not math.isfinite(p)
            or not 0 <= p <= 1
        ):
            raise ValueError("Tev1 returned an invalid relevance probability")
        predictions.append(
            {
                "item_id": item["item_id"],
                "label": p >= 0.5,
                "raw_score": float(p),
                "score_type": "native_tev1_probability",
            }
        )
    return predictions, json.dumps(response, sort_keys=True)


def _embedding_predictions(
    client: Any, tag: str, case: dict[str, Any]
) -> tuple[list[dict[str, Any]], str]:
    inputs = [
        f"task: search result | query: {case['query']}",
        *[f"title: none | text: {item['text']}" for item in case["items"]],
    ]
    vectors = client.embed(tag, inputs)
    if any(
        not isinstance(v, list) or not v or any(not math.isfinite(float(x)) for x in v)
        for v in vectors
    ):
        raise ValueError("embedding model returned a malformed vector")
    query = vectors[0]
    predictions = []
    for item, vector in zip(case["items"], vectors[1:], strict=True):
        if len(vector) != len(query):
            raise ValueError("embedding vector dimensions differ")
        denom = math.sqrt(
            sum(float(x) ** 2 for x in query) * sum(float(x) ** 2 for x in vector)
        )
        if denom == 0:
            raise ValueError("embedding model returned a zero vector")
        score = (
            sum(float(x) * float(y) for x, y in zip(query, vector, strict=True)) / denom
        )
        predictions.append(
            {
                "item_id": item["item_id"],
                "label": None,
                "raw_score": score,
                "score_type": "cosine_similarity",
            }
        )
    return predictions, json.dumps(vectors, separators=(",", ":"))


def _call_chat(
    client: Any, key: str, tag: str, case: dict[str, Any], seed: int
) -> tuple[list[dict[str, Any]], list[str]]:
    system = "Estimate for each evidence item the probability from 0 to 1 that it is relevant to answering the query. Return JSON with `items`, one object per item, and exactly `item_id`, boolean `relevant`, and numeric `probability`. Do not infer source validity or operation permission."
    user = _chat_prompt(case)
    attempts = []
    for attempt in range(2):
        content = client.chat(tag, system, user, seed)
        attempts.append(content)
        try:
            return metrics.parse_chat_items(content, metrics.ITEM_IDS), attempts
        except (ValueError, json.JSONDecodeError):
            if attempt == 0:
                user += "\nReturn all eight candidate IDs once, using the exact JSON fields and types requested."
    raise ValueError("invalid model output after one schema-correction retry")


def _call_guardian(
    client: Any, tag: str, case: dict[str, Any], seed: int
) -> tuple[list[dict[str, Any]], list[str]]:
    predictions = []
    attempts = []
    for index, item in enumerate(case["items"]):
        messages = [
            {
                "role": "user",
                "content": f"Query: {case['query']}\nAssess the relevance of the next evidence item.",
            },
            {"role": "assistant", "content": item["text"]},
            {
                "role": "user",
                "content": "<guardian>Do not think.\n### Criteria: Does this evidence item provide information relevant to answering the query?\n### Scoring Schema: If the preceding assistant message provides information relevant to answering the query, return 'yes'; otherwise return 'no'.\n</guardian>",
            },
        ]
        parsed = None
        for retry in range(2):
            content = client.chat_messages(tag, messages, seed + index * 2 + retry)
            attempts.append(content)
            try:
                parsed = metrics.parse_guardian_score(content)
                break
            except ValueError:
                continue
        if parsed is None:
            raise ValueError("Guardian did not return a valid prescribed yes/no score")
        predictions.append({"item_id": item["item_id"], **parsed})
    return predictions, attempts


def _invalid_rows(
    key: str, case: dict[str, Any], error: str, attempts: list[str] | str
) -> list[dict[str, Any]]:
    return [
        {
            "query_id": case["query_id"],
            "domain": case["domain"],
            "split": case["split"],
            "model": key,
            "item_id": item["item_id"],
            "gold": item["relevant"],
            "raw_score": None,
            "label": None,
            "score_type": "invalid_output",
            "valid": False,
            "error": error,
            "attempt_sha256": [
                hashlib.sha256(x.encode()).hexdigest()
                for x in ([attempts] if isinstance(attempts, str) else attempts)
            ],
            "raw_response": attempts
            if isinstance(attempts, str)
            else attempts[-1]
            if attempts
            else None,
        }
        for item in case["items"]
    ]


def _valid_rows(
    key: str, case: dict[str, Any], predictions: list[dict[str, Any]], raw: str
) -> list[dict[str, Any]]:
    by_id = {item["item_id"]: item for item in case["items"]}
    raw_hash = hashlib.sha256(raw.encode()).hexdigest()
    rows = []
    for pred in predictions:
        row = {
            "query_id": case["query_id"],
            "domain": case["domain"],
            "split": case["split"],
            "model": key,
            "item_id": pred["item_id"],
            "gold": by_id[pred["item_id"]]["relevant"],
            "raw_score": float(pred["raw_score"]),
            "label": pred["label"],
            "score_type": pred["score_type"],
            "valid": True,
            "raw_response_sha256": raw_hash,
        }
        if key != "embedding":
            row["raw_response"] = raw
        rows.append(row)
    return rows


def _tev1_call(
    client: Any, tag: str, case: dict[str, Any], seed: int
) -> tuple[list[dict[str, Any]], str]:
    response = client.system_one(
        tag, _decision_state(case), {"outcome": _decision_question(case)}, seed
    )
    answer = (
        response.get("answers", {}).get("outcome")
        if isinstance(response.get("answers"), dict)
        else None
    )
    probs = _native_probabilities(answer, case)
    return probs, json.dumps(response, ensure_ascii=False, sort_keys=True)


def _analyse_tev1(rows: list[dict[str, Any]]) -> dict[str, Any]:
    result = {}
    family_test_rows = {}
    for family in metrics.TEV1_FAMILIES:
        development = [
            r for r in rows if r["family"] == family and r["split"] == "development"
        ]
        heldout = [r for r in rows if r["family"] == family and r["split"] == "heldout"]
        family_test_rows[family] = heldout
        result[family] = {
            "target_id": family,
            "development": metrics.tev1_calibration_metrics(
                development, seed=47062 + metrics.TEV1_FAMILIES.index(family)
            ),
            "heldout": metrics.tev1_calibration_metrics(
                heldout, seed=47065 + metrics.TEV1_FAMILIES.index(family)
            ),
        }
    mixture_losses = []
    point_losses = [result[f]["heldout"].get("log_loss") for f in metrics.TEV1_FAMILIES]
    if all(value is not None for value in point_losses):
        rng = random.Random(47068)
        for _ in range(2000):
            sampled_losses = []
            for family in metrics.TEV1_FAMILIES:
                family_rows = [r for r in family_test_rows[family] if r["valid"]]
                sample = [rng.choice(family_rows) for _ in family_rows]
                sampled_losses.append(
                    -statistics.mean(
                        math.log(max(1e-12, r["probs"][r["gold_index"]]))
                        for r in sample
                    )
                )
            mixture_losses.append(statistics.mean(sampled_losses))
    result["declared_mixture"] = {
        "estimand": "expected Tev1 log loss when one family is sampled uniformly from the three authored families",
        "weights": {family: 1 / 3 for family in metrics.TEV1_FAMILIES},
        "equal_weight_expected_log_loss": statistics.mean(point_losses)
        if all(v is not None for v in point_losses)
        else None,
        "uncertainty_95": [
            float(np.quantile(mixture_losses, 0.025)),
            float(np.quantile(mixture_losses, 0.975)),
        ]
        if mixture_losses
        else None,
    }
    return result


def _analyse_relevance(rows: list[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    global_maps = {}
    domain_maps = {}
    all_global_scored = {}
    score_types = {
        "qwen": "self_reported_relevance_probability",
        "gemma": "self_reported_relevance_probability",
        "coder": "self_reported_relevance_probability",
        "embedding": "cosine_similarity",
        "tev1": "native_tev1_probability",
        "guardian": "binary_critic_judgment",
    }
    for key in MODEL_KEYS:
        model_rows = [r for r in rows if r["model"] == key]
        dev = [r for r in model_rows if r["split"] == "development"]
        test = [r for r in model_rows if r["split"] == "heldout"]
        global_map, global_scored = metrics.calibration_by_domain(dev, test)
        global_maps[key] = global_map
        all_global_scored[key] = global_scored
        domain_scores = {}
        global_domain_metrics = {}
        for domain in metrics.DOMAINS:
            ddev = [r for r in dev if r["domain"] == domain]
            dtest = [r for r in test if r["domain"] == domain]
            fitted, domain_scored = metrics.calibration_by_domain(ddev, dtest)
            domain_maps[(key, domain)] = fitted
            raw_ranking = metrics.ranking_metrics(dtest)
            calibrated_ranking = metrics.ranking_metrics(
                domain_scored, "calibrated_probability"
            )
            globally_scored_domain = [r for r in global_scored if r["domain"] == domain]
            global_domain_metrics[domain] = metrics.relevance_metrics(
                globally_scored_domain
            )
            domain_scores[domain] = {
                "calibration": fitted,
                "heldout": metrics.relevance_metrics(
                    domain_scored, seed=47064 + metrics.DOMAINS.index(domain)
                ),
                "heldout_binary_decisions": metrics.binary_decision_metrics(
                    domain_scored
                ),
                "global_calibration_heldout": global_domain_metrics[domain],
                "global_calibration_binary_decisions": metrics.binary_decision_metrics(
                    globally_scored_domain
                ),
                "raw_score_discrimination": metrics.raw_score_auc(dtest),
                "raw_ranking": raw_ranking,
                "calibrated_ranking": calibrated_ranking,
                "top_item_changes_after_calibration": sum(
                    raw_ranking["top_item_by_query"].get(q)
                    != calibrated_ranking["top_item_by_query"].get(q)
                    for q in raw_ranking["top_item_by_query"]
                ),
                "binary_decision_changes_after_calibration": sum(
                    row.get("label") is not None
                    and row.get("calibrated_probability") is not None
                    and bool(row["label"]) != (row["calibrated_probability"] >= 0.5)
                    for row in domain_scored
                ),
            }
        result[key] = {
            "native_score_type": score_types[key],
            "global_calibration": global_map,
            "global_calibrated_heldout_by_domain": global_domain_metrics,
            "global_calibrated_equal_domain_mixture": {
                "estimand": "expected heldout metric for the common relevance target over four domains sampled uniformly",
                "weights": {domain: 0.25 for domain in metrics.DOMAINS},
                "metrics": {
                    name: statistics.mean(values)
                    if all(isinstance(value, (int, float)) for value in values)
                    else None
                    for name in ("brier", "log_loss", "auc", "accuracy", "event_rate")
                    for values in [
                        [global_domain_metrics[d].get(name) for d in metrics.DOMAINS]
                    ]
                },
                "uncertainty_95": {
                    name: _domain_mixture_interval(
                        global_scored, name, 47080 + MODEL_KEYS.index(key) * 10 + i
                    )
                    for i, name in enumerate(("brier", "log_loss", "auc"))
                },
            },
            "domains": domain_scores,
        }
    pool_summaries = {}
    judges = {
        key: {
            (r["query_id"], r["item_id"]): r
            for r in all_global_scored[key]
            if r["split"] == "heldout"
        }
        for key in JUDGES
    }
    shared_ids = set.intersection(*(set(values) for values in judges.values()))
    complete = [
        (query_item, [judges[key][query_item] for key in JUDGES])
        for query_item in sorted(shared_ids)
        if all(
            judges[key][query_item]["valid"]
            and judges[key][query_item]["calibrated_probability"] is not None
            for key in JUDGES
        )
    ]
    eligible_by_domain = {
        domain: sum(
            judges["qwen"][query_item]["domain"] == domain for query_item in shared_ids
        )
        for domain in metrics.DOMAINS
    }
    for name, use_probabilities in (
        ("majority_label", False),
        ("equal_weight_calibrated_probability", True),
    ):
        pool_rows = []
        for (query_id, item_id), members in complete:
            labels = [bool(row["label"]) for row in members]
            prediction = sum(labels) >= 2
            p = (
                sum(float(row["calibrated_probability"]) for row in members) / 3
                if use_probabilities
                else float(prediction)
            )
            base = members[0]
            pool_rows.append(
                {
                    "query_id": query_id,
                    "item_id": item_id,
                    "domain": base["domain"],
                    "gold": base["gold"],
                    "valid": True,
                    "calibrated_probability": p,
                    "label": prediction,
                }
            )
        pool_summaries[name] = {
            "estimand": "expected pooled-predictor metric for the common relevance target over four domains sampled uniformly",
            "model_weights": {key: 1 / 3 for key in JUDGES},
            "domain_weights": {domain: 0.25 for domain in metrics.DOMAINS},
            "coverage_items": len(pool_rows),
            "eligible_items": len(shared_ids),
            "coverage": len(pool_rows) / len(shared_ids) if shared_ids else 0.0,
            "coverage_by_domain": {
                domain: sum(r["domain"] == domain for r in pool_rows)
                / max(1, eligible_by_domain[domain])
                for domain in metrics.DOMAINS
            },
            "heldout_by_domain": {
                domain: metrics.relevance_metrics(
                    [r for r in pool_rows if r["domain"] == domain]
                )
                for domain in metrics.DOMAINS
            },
            "binary_decisions_by_domain": {
                domain: metrics.binary_decision_metrics(
                    [r for r in pool_rows if r["domain"] == domain]
                )
                for domain in metrics.DOMAINS
            },
        }
        domain_results = pool_summaries[name]["heldout_by_domain"]
        pool_summaries[name]["equal_weight_domain_mixture"] = {
            metric: statistics.mean(values)
            if all(isinstance(value, (int, float)) for value in values)
            else None
            for metric in ("brier", "log_loss", "auc", "accuracy", "event_rate")
            for values in [[domain_results[d].get(metric) for d in metrics.DOMAINS]]
        }
        pool_summaries[name]["uncertainty_95"] = {
            metric: _domain_mixture_interval(
                pool_rows,
                metric,
                47090
                + list(("majority_label", "equal_weight_calibrated_probability")).index(
                    name
                )
                * 5
                + i,
            )
            for i, metric in enumerate(("brier", "log_loss", "auc"))
        }
        pool_summaries[name]["binary_decisions_equal_weight_domain_mixture"] = {
            metric: statistics.mean(values)
            if all(isinstance(value, (int, float)) for value in values)
            else None
            for metric in ("false_positive_rate", "false_negative_rate")
            for values in [
                [
                    pool_summaries[name]["binary_decisions_by_domain"][d].get(metric)
                    for d in metrics.DOMAINS
                ]
            ]
        }
    result["judge_pools"] = pool_summaries
    result["judge_component_heldout"] = {
        key: result[key]["global_calibrated_equal_domain_mixture"] for key in JUDGES
    }
    result["coder_by_domain"] = {}
    for domain in metrics.DOMAINS:
        domain_comparisons = {}
        for baseline in ("qwen", "gemma"):
            by_model = {}
            for key in ("coder", baseline):
                by_model[key] = {
                    r["query_id"]: [
                        x
                        for x in all_global_scored[key]
                        if x["query_id"] == r["query_id"] and x["domain"] == domain
                    ]
                    for r in all_global_scored[key]
                    if r["split"] == "heldout" and r["domain"] == domain
                }
            shared = sorted(set(by_model["coder"]) & set(by_model[baseline]))
            diffs = []
            rank_disagreements = []
            paired_n = 0
            for query_id in shared:
                coder_items = by_model["coder"][query_id]
                base_items = by_model[baseline][query_id]
                if (
                    len(coder_items) != 8
                    or len(base_items) != 8
                    or not all(r["valid"] for r in coder_items + base_items)
                ):
                    continue
                paired_n += 1
                coder_accuracy = (
                    sum(bool(r["label"]) == bool(r["gold"]) for r in coder_items) / 8
                )
                base_accuracy = (
                    sum(bool(r["label"]) == bool(r["gold"]) for r in base_items) / 8
                )
                diffs.append(coder_accuracy - base_accuracy)
                coder_top = sorted(
                    coder_items, key=lambda r: (-float(r["raw_score"]), r["item_id"])
                )[0]["item_id"]
                base_top = sorted(
                    base_items, key=lambda r: (-float(r["raw_score"]), r["item_id"])
                )[0]["item_id"]
                rank_disagreements.append(coder_top != base_top)
            if diffs:
                rng = __import__("random").Random(47067 + metrics.DOMAINS.index(domain))
                boot = [
                    sum(rng.choices(diffs, k=len(diffs))) / len(diffs)
                    for _ in range(2000)
                ]
                ci = [float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))]
                mean_diff = sum(diffs) / len(diffs)
            else:
                mean_diff, ci = None, None
            domain_comparisons[f"coder_minus_{baseline}"] = {
                "paired_queries": paired_n,
                "paired_accuracy_difference": mean_diff,
                "paired_accuracy_difference_ci95": ci,
                "top_item_disagreement_rate": sum(rank_disagreements)
                / len(rank_disagreements)
                if rank_disagreements
                else None,
            }
        result["coder_by_domain"][domain] = domain_comparisons
    mixture_per_model = {}
    mixture_uncertainty = {}
    for key in MODEL_KEYS:
        mixture_per_model[key] = {}
        mixture_uncertainty[key] = {}
        for name in ("brier", "log_loss", "auc", "accuracy", "event_rate"):
            values = [
                result[key]["domains"][domain]["heldout"].get(name)
                for domain in metrics.DOMAINS
            ]
            mixture_per_model[key][name] = (
                statistics.mean(values)
                if all(isinstance(value, (int, float)) for value in values)
                else None
            )
            if name in {"brier", "log_loss", "auc"}:
                mixture_uncertainty[key][name] = _domain_mixture_interval(
                    all_global_scored[key],
                    name,
                    47070
                    + MODEL_KEYS.index(key) * 10
                    + ("brier", "log_loss", "auc").index(name),
                )
    result["equal_weight_domain_mixture"] = {
        "estimand": "expected relevance metric over four authored domains sampled uniformly",
        "weights": {domain: 1 / 4 for domain in metrics.DOMAINS},
        "per_model": mixture_per_model,
        "uncertainty_95": mixture_uncertainty,
    }
    return {
        "models": result,
        "global_calibration": global_maps,
        "domain_calibration": domain_maps,
    }


def _domain_mixture_interval(
    rows: list[dict[str, Any]], metric: str, seed: int, replicates: int = 2000
) -> list[float] | None:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for row in rows:
        if row.get("valid") and row.get("calibrated_probability") is not None:
            grouped[row["domain"]][row["query_id"]].append(row)
    if any(not grouped[domain] for domain in metrics.DOMAINS):
        return None
    rng = random.Random(seed)
    draws = []
    for _ in range(replicates):
        domain_values = []
        for domain in metrics.DOMAINS:
            keys = list(grouped[domain])
            sample = [
                row
                for query_id in (rng.choice(keys) for _ in keys)
                for row in grouped[domain][query_id]
            ]
            probs = [
                [
                    1.0 - float(row["calibrated_probability"]),
                    float(row["calibrated_probability"]),
                ]
                for row in sample
            ]
            labels = [int(row["gold"]) for row in sample]
            value = metrics._point_metric(probs, labels, metric)
            if value is None:
                break
            domain_values.append(value)
        if len(domain_values) == len(metrics.DOMAINS):
            draws.append(statistics.mean(domain_values))
    return (
        [float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))]
        if draws
        else None
    )


def _dependence(rows: list[dict[str, Any]]) -> dict[str, Any]:
    output = {}
    for left_i, left in enumerate(JUDGES):
        for right in JUDGES[left_i + 1 :]:
            dev = [
                r
                for r in rows
                if r["split"] == "development" and r["model"] in {left, right}
            ]
            test = [
                r
                for r in rows
                if r["split"] == "heldout" and r["model"] in {left, right}
            ]

            def pair_rows(
                source: list[dict[str, Any]],
            ) -> dict[tuple[str, str], dict[str, dict[str, Any]]]:
                paired_rows: dict[tuple[str, str], dict[str, dict[str, Any]]] = (
                    defaultdict(dict)
                )
                for row in source:
                    if row["valid"]:
                        paired_rows[(row["query_id"], row["item_id"])][row["model"]] = (
                            row
                        )
                return paired_rows

            dev_pairs = pair_rows(dev)
            test_pairs = pair_rows(test)
            paired = [
                pair for pair in test_pairs.values() if left in pair and right in pair
            ]
            dev_errors = {key: [] for key in (left, right)}
            for pair in dev_pairs.values():
                for key in (left, right):
                    if key in pair:
                        dev_errors[key].append(pair[key]["label"] != pair[key]["gold"])
            rates = {
                key: sum(values) / len(values) if values else None
                for key, values in dev_errors.items()
            }
            joint_by_query: dict[str, list[bool]] = defaultdict(list)
            false_positive_overlap = false_negative_overlap = 0
            negative_count = positive_count = 0
            for pair in paired:
                lrow, rrow = pair[left], pair[right]
                joint_by_query[lrow["query_id"]].append(
                    bool(
                        lrow["label"] != lrow["gold"] and rrow["label"] != rrow["gold"]
                    )
                )
                if not lrow["gold"]:
                    negative_count += 1
                    false_positive_overlap += int(bool(lrow["label"] and rrow["label"]))
                else:
                    positive_count += 1
                    false_negative_overlap += int(
                        bool(not lrow["label"] and not rrow["label"])
                    )
            joint = [x for values in joint_by_query.values() for x in values]
            expected = (
                rates[left] * rates[right]
                if rates[left] is not None and rates[right] is not None
                else None
            )
            interval = None
            if joint_by_query:
                import random

                rng = random.Random(47066 + left_i)
                query_ids = list(joint_by_query)
                draws = []
                for _ in range(2000):
                    sample = [
                        value
                        for query_id in (rng.choice(query_ids) for _ in query_ids)
                        for value in joint_by_query[query_id]
                    ]
                    draws.append(sum(sample) / len(sample))
                interval = [
                    float(np.quantile(draws, 0.025)),
                    float(np.quantile(draws, 0.975)),
                ]
            output[f"{left}+{right}"] = {
                "heldout_paired_items": len(paired),
                "heldout_paired_queries": len(joint_by_query),
                "development_error_rates": rates,
                "heldout_joint_error_rate": sum(joint) / len(joint) if joint else None,
                "heldout_joint_error_rate_ci95": interval,
                "joint_error_rate_if_independent": expected,
                "observed_minus_independence": sum(joint) / len(joint) - expected
                if joint and expected is not None
                else None,
                "observed_minus_independence_ci95": [
                    interval[0] - expected,
                    interval[1] - expected,
                ]
                if interval and expected is not None
                else None,
                "false_positive_overlap_count": false_positive_overlap,
                "false_positive_overlap_rate": false_positive_overlap / negative_count
                if negative_count
                else None,
                "false_negative_overlap_count": false_negative_overlap,
                "false_negative_overlap_rate": false_negative_overlap / positive_count
                if positive_count
                else None,
                "interpretation": "paired error evidence on this target only; model identity and lineage do not establish independence",
            }
    return output


def run_suite(
    client: Any | None = None,
    prereg: dict[str, Any] | None = None,
    base_url: str = "http://127.0.0.1:11434",
) -> dict[str, Any]:
    prereg = prereg or load_preregistration()
    validate_frozen_plan(prereg)
    client = client or build_model_role_client(prereg, base_url)
    version, digests = _pin_models(client, prereg)
    tev_cases = metrics.generate_tev1_cases(int(prereg["seeds"]["tev1_cases"]))
    relevance_cases = metrics.generate_relevance_cases(
        int(prereg["seeds"]["relevance_cases"])
    )
    case_set_sha256 = metrics.digest_json(
        {"tev1": tev_cases, "relevance": relevance_cases}
    )
    prompt_template_sha256 = metrics.digest_json(
        {"version": PROMPT_VERSION, **PROMPT_TEMPLATE}
    )
    if prereg.get("schema_version") == 2 and (
        case_set_sha256 != prereg["frozen_case_set_sha256"]
        or prompt_template_sha256 != prereg["frozen_prompt_template_sha256"]
    ):
        raise ExperimentError(
            "generated cases or prompt template differ from preregistration"
        )
    tev_rows, relevance_rows, raw = [], [], {}
    for n, case in enumerate(tev_cases):
        key = case["family"]
        model = prereg["models"]["tev1"]["api_model"]
        try:
            probs, response = _tev1_call(
                client, model, case, int(prereg["seeds"]["calls"]) + n
            )
            gold_index = case["class_labels"].index(case["gold_label"])
            tev_rows.append(
                {
                    "case_id": case["case_id"],
                    "family": key,
                    "split": case["split"],
                    "gold_label": case["gold_label"],
                    "gold_index": gold_index,
                    "probs": probs,
                    "valid": True,
                }
            )
        except (ValueError, KeyError, TypeError) as exc:
            response, probs, gold_index = (
                str(exc),
                None,
                case["class_labels"].index(case["gold_label"]),
            )
            tev_rows.append(
                {
                    "case_id": case["case_id"],
                    "family": key,
                    "split": case["split"],
                    "gold_label": case["gold_label"],
                    "gold_index": gold_index,
                    "probs": None,
                    "valid": False,
                }
            )
        raw[f"tev1:{case['case_id']}"] = response
        if (n + 1) % 8 == 0 or n + 1 == len(tev_cases):
            print(
                f"Tev1 cases complete: {n + 1}/{len(tev_cases)}",
                file=sys.stderr,
                flush=True,
            )
    for n, case in enumerate(relevance_cases):
        for key in MODEL_KEYS:
            tag = prereg["models"][key]["api_model"]
            seed = (
                int(prereg["seeds"]["calls"])
                + 10000
                + n * len(MODEL_KEYS)
                + MODEL_KEYS.index(key)
            )
            attempts: list[str] | str = []
            try:
                if key == "embedding":
                    preds, response = _embedding_predictions(client, tag, case)
                elif key == "tev1":
                    preds, response = _systemone_relevance(client, tag, case, seed)
                elif key == "guardian":
                    preds, attempts = _call_guardian(client, tag, case, seed)
                    response = json.dumps(attempts, ensure_ascii=False)
                else:
                    preds, attempts = _call_chat(client, key, tag, case, seed)
                    response = json.dumps(attempts, ensure_ascii=False)
                relevance_rows.extend(_valid_rows(key, case, preds, response))
            except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
                relevance_rows.extend(_invalid_rows(key, case, str(exc), attempts))
                response = (
                    attempts[-1]
                    if isinstance(attempts, list) and attempts
                    else str(exc)
                )
            raw[f"{key}:{case['query_id']}"] = response
            print(
                f"Relevance cases complete: {n + 1}/{len(relevance_cases)} ({key})",
                file=sys.stderr,
                flush=True,
            )
    tev_summary = _analyse_tev1(tev_rows)
    relevance_summary = _analyse_relevance(relevance_rows)
    result = {
        "schema_version": int(prereg.get("result_schema_version", 1)),
        "study_id": prereg["study_id"],
        "evidence_class": "synthetic",
        "ollama_version": version,
        "model_identity_sha256": digests,
        "embedding_runtime": (
            client.embedding_runtime_metadata()
            if hasattr(client, "embedding_runtime_metadata")
            else None
        ),
        "preregistration_sha256": metrics.digest_json(prereg),
        "case_set_sha256": case_set_sha256,
        "prompt_version": PROMPT_VERSION,
        "prompt_template_sha256": prompt_template_sha256,
        "tev1_rows": tev_rows,
        "relevance_rows": relevance_rows,
        "raw_responses": raw,
        "tev1_summary": tev_summary,
        "relevance_summary": relevance_summary["models"],
        "equal_weight_domain_mixture": relevance_summary["models"][
            "equal_weight_domain_mixture"
        ],
        "judgment_dependence": _dependence(relevance_rows),
        "predictions_sha256": metrics.digest_json(
            {
                "tev1": tev_rows,
                "relevance": [
                    {
                        k: r.get(k)
                        for k in (
                            "query_id",
                            "domain",
                            "split",
                            "model",
                            "item_id",
                            "gold",
                            "raw_score",
                            "label",
                            "score_type",
                            "valid",
                        )
                    }
                    for r in relevance_rows
                ],
            }
        ),
        "raw_response_sha256": metrics.digest_json(raw),
    }
    result["result_sha256"] = metrics.digest_json(result)
    return result


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = metrics.canonical_json(value) + "\n"
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        handle.write(data)
        temp = Path(handle.name)
    os.replace(temp, path)


def finalize_runs(first_path: Path, second_path: Path) -> dict[str, Any]:
    first, second = (
        json.loads(path.read_text(encoding="utf-8"))
        for path in (first_path, second_path)
    )
    for key in (
        "study_id",
        "ollama_version",
        "embedding_runtime",
        "preregistration_sha256",
        "case_set_sha256",
        "model_identity_sha256",
        "prompt_template_sha256",
    ):
        if first.get(key) != second.get(key):
            raise ExperimentError(f"replay mismatch for {key}")
    return {
        "schema_version": 1,
        "study_id": first["study_id"],
        "evidence_class": "synthetic",
        "configuration_match": True,
        "case_set_sha256": first["case_set_sha256"],
        "model_identity_sha256": first["model_identity_sha256"],
        "predictions_match": first["predictions_sha256"]
        == second["predictions_sha256"],
        "raw_responses_match": first["raw_response_sha256"]
        == second["raw_response_sha256"],
        "runs": [
            {
                "file": str(path),
                "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "predictions_sha256": run["predictions_sha256"],
                "raw_response_sha256": run["raw_response_sha256"],
                "tev1_summary": run["tev1_summary"],
                "relevance_summary": run["relevance_summary"],
                "judgment_dependence": run["judgment_dependence"],
            }
            for path, run in ((first_path, first), (second_path, second))
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:11434")
    parser.add_argument("--preregistration", type=Path)
    parser.add_argument(
        "--finalize-runs", nargs=2, type=Path, metavar=("FIRST", "REPLAY")
    )
    args = parser.parse_args(argv)
    if args.finalize_runs:
        result = finalize_runs(*args.finalize_runs)
    else:
        prereg = load_preregistration(args.preregistration)
        result = run_suite(prereg=prereg, base_url=args.base_url)
    _write_json(args.output, result)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
