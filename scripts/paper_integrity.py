"""Recompute and validate the evidence package for the IsoPrax paper.

This command uses only pinned local records. It makes no model or network calls.
It writes a deterministic JSON summary and fails closed on changed inputs,
missing claim tags, unexpected run structure, or result mismatches.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import random
import re
import statistics
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

import numpy as np
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
RAW = Path("docs/experiments/bouleusis-2026-10-08-raw")
MODEL_MANIFEST = Path("docs/experiments/model-role-v2.3-artifact-manifest.json")
MODEL_SUMMARY = Path("docs/experiments/model-role-v2.3-replay-summary.json")
MODEL_PREREG = Path(
    "specs/047-retrieval-selection-dependence/model-role-preregistration-v2.3.json"
)
CLAIMS = Path("docs/research/paper-claims-evidence.json")
LOCK = Path("docs/research/paper-integrity-lock.json")
PAPER = Path(
    "docs/research/Calibration Is Not Enough_ Outcome Commensurability as a Precondition for Cross-Family Failure Prediction.md"
)
OUTPUT = Path("docs/research/paper-recomputed-results.json")
TABLES = Path("docs/research/paper-recomputed-tables.md")
AUTOMATED_REVIEW = Path("docs/research/paper-automated-review.json")
DOMAINS = ("equipment", "software", "policy", "safety")
TEV1_FAMILIES = ("equipment_binary", "software_category", "incident_ordinal")
MODELS = ("qwen", "gemma", "coder", "embedding", "tev1", "guardian")
JUDGES = ("qwen", "gemma", "guardian")
REPLICATES = 2000


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonl(data: bytes) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in data.splitlines() if line.strip()]
    if not rows:
        raise ValueError("empty JSONL artifact")
    return rows


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _digest_json(value: Any) -> str:
    return _sha(_canonical_json(value).encode("utf-8"))


def verify_integrity_lock(root: Path) -> dict[str, Any]:
    """Check the frozen paper, claim registry, and protocol artifact identities."""
    lock = _json(root / LOCK)
    artifacts = lock.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError("integrity lock has no artifact identities")
    checked = []
    paths = set()
    for entry in artifacts:
        relative = entry.get("path")
        expected = entry.get("sha256")
        if not isinstance(relative, str) or not isinstance(expected, str):
            raise ValueError("integrity lock artifact entry is malformed")
        if relative in paths:
            raise ValueError(f"integrity lock repeats artifact: {relative}")
        paths.add(relative)
        path = root / relative
        if not path.is_file():
            raise ValueError(f"integrity lock artifact missing: {relative}")
        actual = _sha(path.read_bytes())
        if actual != expected:
            raise ValueError(f"integrity lock digest mismatch: {relative}")
        checked.append({"path": relative, "sha256": actual})
    required = {str(PAPER), str(CLAIMS), str(MODEL_PREREG)}
    if not required.issubset(paths):
        raise ValueError(
            f"integrity lock omits required frozen artifacts: {sorted(required - paths)}"
        )
    return {"status": "PASS", "artifact_count": len(checked), "artifacts": checked}


def _close(left: float | None, right: float | None, tolerance: float = 1e-10) -> bool:
    return (
        left is not None
        and right is not None
        and math.isclose(left, right, rel_tol=tolerance, abs_tol=tolerance)
    )


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _same_tree(left: Any, right: Any, tolerance: float = 1e-9) -> bool:
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return math.isclose(
            float(left), float(right), rel_tol=tolerance, abs_tol=tolerance
        )
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(
            _same_tree(left[key], right[key], tolerance) for key in left
        )
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(
            _same_tree(a, b, tolerance) for a, b in zip(left, right, strict=True)
        )
    return left == right


def verify_bouleusis_manifest(root: Path) -> dict[str, Any]:
    manifest = _json(root / RAW / "manifest.json")
    result: dict[str, Any] = {"source_commit": None, "files": []}
    for entry in manifest["files"]:
        path = root / entry["package_path"]
        compressed = path.read_bytes()
        if _sha(compressed) != entry["package_sha256"]:
            raise ValueError(
                f"raw Bouleusis artifact integrity failed: {path}: package_sha256"
            )
        try:
            original = gzip.decompress(compressed)
        except (OSError, EOFError) as exc:
            raise ValueError(
                f"raw Bouleusis artifact integrity failed: {path}: invalid gzip data"
            ) from exc
        rows = _jsonl(original)
        checks = {
            "package_sha256": _sha(compressed) == entry["package_sha256"],
            "source_sha256": _sha(original) == entry["source_sha256"],
            "source_bytes": len(original) == entry["source_bytes"],
            "source_lines": len(original.splitlines())
            == entry["source_lines_including_header"],
            "record_count": len(rows) - 1 == entry["source_run_or_record_count"],
            "source_blob": bool(entry["source_blob_oid"]),
        }
        if not all(checks.values()):
            raise ValueError(
                f"raw Bouleusis artifact integrity failed: {path}: {checks}"
            )
        if result["source_commit"] is None:
            result["source_commit"] = entry["source_commit"]
        if entry["source_commit"] != result["source_commit"]:
            raise ValueError("raw snapshot source commits do not match")
        result["files"].append(
            {
                "path": entry["package_path"],
                "source_path": entry["source_path"],
                "source_sha256": entry["source_sha256"],
                "package_sha256": entry["package_sha256"],
                "lines_including_header": len(rows),
                "records_after_header": len(rows) - 1,
                "checks": checks,
            }
        )
    if manifest.get("source_license") != "NOASSERTION" or not all(
        phrase in manifest.get("source_license_context", "")
        for phrase in ("did not assert a license", "separately authorized")
    ):
        raise ValueError(
            "historical source-license metadata changed; review the provenance"
        )
    release = manifest.get("public_release", {})
    authorization_record = release.get("authorization_record")
    included = release.get("included_artifacts", [])
    manifest_paths = sorted(entry["package_path"] for entry in manifest["files"])
    if (
        release.get("data_license") != "CC-BY-4.0"
        or release.get("data_license_url")
        != "https://creativecommons.org/licenses/by/4.0/"
        or release.get("authorization_date") != "2026-10-09"
        or not authorization_record
        or not (root / authorization_record).is_file()
        or sorted(included) != manifest_paths
        or "selected original research data"
        not in release.get("authorization_scope", "")
        or not {"Bouleusis source code", "third-party materials"}.issubset(
            set(release.get("excluded_materials", []))
        )
        or "selected original research data files"
        not in release.get("license_scope_note", "")
    ):
        raise ValueError("public data license or authorization record is incomplete")
    return result


def _load_model_role_archive(root: Path, entry: dict[str, Any]) -> bytes:
    """Rebuild and verify a model run from the compressed files in a clean checkout."""
    parts = []
    for item in entry["parts"]:
        part = (root / item["path"]).read_bytes()
        if _sha(part) != item["sha256"] or len(part) != item["bytes"]:
            raise ValueError(
                f"model-role archive part identity mismatch: {item['path']}"
            )
        parts.append(part)
    compressed = b"".join(parts)
    if (
        _sha(compressed) != entry["gzip_sha256"]
        or len(compressed) != entry["gzip_bytes"]
    ):
        raise ValueError("model-role compressed archive identity mismatch")
    try:
        raw = gzip.decompress(compressed)
    except (OSError, EOFError) as exc:
        raise ValueError("model-role archive is not valid gzip data") from exc
    if (
        _sha(raw) != entry["uncompressed_sha256"]
        or len(raw) != entry["uncompressed_bytes"]
    ):
        raise ValueError("model-role uncompressed archive identity mismatch")
    preserved_path = root / entry["uncompressed_path"]
    if preserved_path.is_file() and raw != preserved_path.read_bytes():
        raise ValueError("model-role archive differs from optional uncompressed copy")
    return raw


def audit_public_data_strings(root: Path) -> dict[str, Any]:
    """Scan released source records for common secret and private-identifier forms."""
    patterns = {
        "credential_pattern": re.compile(
            r"(?i)(api[_ -]?key|client[_ -]?secret|password|bearer\s+|"
            r"gh[pousr]_[A-Za-z0-9]{8,}|sk-[A-Za-z0-9]{8,}|token\s*[:=])"
        ),
        "email_address": re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"),
        "url": re.compile(r"https?://[^\s\"<>]+"),
        "local_home_path": re.compile(r"(?i)(/home/[^/\s]+|C:\\\\Users\\\\[^\\\\\s]+)"),
    }
    scan_inputs = [
        (path.relative_to(root).as_posix(), path.read_bytes(), True)
        for path in sorted((root / RAW).glob("*.jsonl.gz"))
    ]
    model_manifest = _json(root / MODEL_MANIFEST)
    for run in ("1", "2"):
        entry = model_manifest["runs"][run]
        scan_inputs.append(
            (entry["uncompressed_path"], _load_model_role_archive(root, entry), False)
        )
    report = []
    totals = Counter()
    for relative_path, data, is_jsonl_gzip in scan_inputs:
        text_values: list[str] = []

        def collect(value: Any) -> None:
            if isinstance(value, dict):
                for child in value.values():
                    collect(child)
            elif isinstance(value, list):
                for child in value:
                    collect(child)
            elif isinstance(value, str):
                text_values.append(value)

        if is_jsonl_gzip:
            data = gzip.decompress(data)
            for row in _jsonl(data):
                collect(row)
        else:
            collect(json.loads(data))
        counts = {
            name: sum(len(pattern.findall(value)) for value in text_values)
            for name, pattern in patterns.items()
        }
        totals.update(counts)
        report.append(
            {
                "path": relative_path,
                "bytes_scanned": len(data),
                "string_values_scanned": len(text_values),
                "pattern_matches": counts,
            }
        )
    if any(totals.values()):
        raise ValueError(
            f"public-data string audit found possible sensitive text: {dict(totals)}"
        )
    return {
        "status": "PASS",
        "scope": "pattern scan of selected JSONL records and model-role runs rebuilt from pinned compressed archives",
        "limitations": [
            "A pattern scan cannot prove that every field is free of private or third-party content.",
            "The package excludes source code, model weights, and external corpora; model-generated outputs remain experiment records.",
        ],
        "total_pattern_matches": dict(totals),
        "files": report,
    }


def _load_raw(root: Path, package: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    path = root / RAW / package
    rows = _jsonl(gzip.decompress(path.read_bytes()))
    return rows[0], rows[1:]


def _assert_disjoint_splits(
    rows: list[dict[str, Any]], group_fields: tuple[str, ...], item_field: str
) -> int:
    groups: dict[tuple[str, ...], dict[str, set[str]]] = defaultdict(
        lambda: defaultdict(set)
    )
    for row in rows:
        group = tuple(str(row[field]) for field in group_fields)
        split = str(row["split"])
        groups[group][split].add(str(row[item_field]))
    count = 0
    for group, splits in groups.items():
        development = splits.get("development", set())
        heldout = splits.get("heldout", set())
        overlap = development & heldout
        if overlap:
            raise ValueError(
                f"development/held-out leakage for {group}: {sorted(overlap)}"
            )
        count += len(heldout)
    return count


def _validate_relevance_score(row: dict[str, Any]) -> None:
    model = row["model"]
    score_type = row["score_type"]
    expected = {
        "qwen": "self_reported_relevance_probability",
        "gemma": "self_reported_relevance_probability",
        "coder": "self_reported_relevance_probability",
        "embedding": "cosine_similarity",
        "tev1": "native_tev1_probability",
        "guardian": "binary_critic_judgment",
    }
    if model not in expected or score_type != expected[model]:
        raise ValueError(f"score semantic mismatch for {model}: {score_type!r}")
    if not row.get("valid"):
        return
    score = row.get("raw_score")
    if not isinstance(score, (int, float)) or not math.isfinite(float(score)):
        raise ValueError(f"valid {model} output has no finite raw score")
    score = float(score)
    if (
        score_type
        in {
            "self_reported_relevance_probability",
            "native_tev1_probability",
        }
        and not 0.0 <= score <= 1.0
    ):
        raise ValueError(f"probability-like native score is outside [0, 1]: {model}")
    if score_type == "cosine_similarity" and not -1.000001 <= score <= 1.000001:
        raise ValueError("cosine similarity is outside [-1, 1]")
    if score_type == "binary_critic_judgment":
        if score not in {0.0, 1.0} or not isinstance(row.get("label"), bool):
            raise ValueError("binary critic output was encoded as a non-binary score")
    elif model == "embedding":
        if row.get("label") is not None:
            raise ValueError(
                "embedding similarity row must not invent a binary judgment"
            )
    elif not isinstance(row.get("label"), bool):
        raise ValueError(f"valid {model} judgment has no Boolean label")


def _validate_model_role_rows(
    run: dict[str, Any], prereg: dict[str, Any]
) -> dict[str, Any]:
    models = set(prereg["models"])
    domains = set(prereg["common_relevance_target"]["domains"])
    families = prereg["tev1_calibration"]["families"]
    relevance = run["relevance_rows"]
    tev1 = run["tev1_rows"]
    expected_items = int(prereg["common_relevance_target"]["items_per_query"])
    expected_queries = int(prereg["common_relevance_target"]["queries_per_domain"])
    development_queries = int(
        prereg["common_relevance_target"]["development_queries_per_domain"]
    )
    heldout_queries = int(
        prereg["common_relevance_target"]["heldout_queries_per_domain"]
    )
    if set(row["model"] for row in relevance) != models:
        raise ValueError("model-role model set differs from preregistration")
    if set(row["domain"] for row in relevance) != domains:
        raise ValueError("model-role domain set differs from preregistration")
    expected_relevance_rows = (
        len(models) * len(domains) * expected_queries * expected_items
    )
    if len(relevance) != expected_relevance_rows:
        raise ValueError(
            f"model-role relevance count changed: {len(relevance)} != {expected_relevance_rows}"
        )
    primary = [
        (row["model"], row["domain"], row["query_id"], row["item_id"])
        for row in relevance
    ]
    if len(primary) != len(set(primary)):
        raise ValueError("model-role relevance primary keys are duplicated")
    query_groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    item_gold: dict[tuple[str, str, str], dict[str, bool]] = defaultdict(dict)
    split_by_query_item: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    response_hashes: dict[tuple[str, str], set[str]] = defaultdict(set)
    raw_responses = run.get("raw_responses")
    if not isinstance(raw_responses, dict):
        raise ValueError("model-role raw responses are not a keyed object")
    for row in relevance:
        if row.get("split") not in {"development", "heldout"}:
            raise ValueError("model-role relevance row has an unknown split")
        _validate_relevance_score(row)
        qkey = (row["model"], row["domain"], row["query_id"])
        query_groups[qkey].append(row)
        gkey = (row["domain"], row["query_id"])
        prior = item_gold[gkey].get(row["item_id"])
        if prior is not None and prior != row["gold"]:
            raise ValueError("gold relevance labels differ between model roles")
        item_gold[gkey][row["item_id"]] = bool(row["gold"])
        split_by_query_item[gkey].add(str(row["split"]))
        response_key = f"{row['model']}:{row['query_id']}"
        if response_key not in raw_responses:
            raise ValueError(f"raw model response is missing: {response_key}")
        response = raw_responses[response_key]
        if not isinstance(response, str):
            raise ValueError(f"raw model response is not text: {response_key}")
        digest = _sha(response.encode("utf-8"))
        if digest != row.get("raw_response_sha256"):
            raise ValueError(f"raw response digest differs for {response_key}")
        if "raw_response" in row and response != row["raw_response"]:
            raise ValueError(f"raw response text differs for {response_key}")
        response_hashes[(row["model"], row["query_id"])].add(digest)
    expected_group_count = len(models) * len(domains) * expected_queries
    if len(query_groups) != expected_group_count:
        raise ValueError("model-role query group count differs from preregistration")
    for (model, domain, query), group in query_groups.items():
        if (
            len(group) != expected_items
            or len({r["item_id"] for r in group}) != expected_items
        ):
            raise ValueError(f"incomplete item set for {model}/{domain}/{query}")
        if len({r["split"] for r in group}) != 1:
            raise ValueError(f"query split differs within {model}/{domain}/{query}")
    if any(len(hashes) != 1 for hashes in response_hashes.values()):
        raise ValueError("one query has multiple recorded raw-response digests")
    for domain in domains:
        domain_queries = {query for (d, query) in item_gold if d == domain}
        if len(domain_queries) != expected_queries:
            raise ValueError(f"query count changed for domain {domain}")
        for model in models:
            dev = {
                query
                for (m, d, query), group in query_groups.items()
                if m == model and d == domain and group[0]["split"] == "development"
            }
            held = {
                query
                for (m, d, query), group in query_groups.items()
                if m == model and d == domain and group[0]["split"] == "heldout"
            }
            if len(dev) != development_queries or len(held) != heldout_queries:
                raise ValueError(
                    f"development/held-out query counts changed for {model}/{domain}"
                )
            if dev & held:
                raise ValueError(
                    f"development/held-out query leakage for {model}/{domain}"
                )
        if any(
            len(splits) != 1
            for key, splits in split_by_query_item.items()
            if key[0] == domain
        ):
            raise ValueError(f"split assignment differs by model for {domain}")

    invalid_relevance = sum(not bool(row["valid"]) for row in relevance)
    tev_primary = [(row["family"], row["case_id"]) for row in tev1]
    expected_tev_rows = sum(int(info["cases"]) for info in families.values())
    if len(tev1) != expected_tev_rows or len(tev_primary) != len(set(tev_primary)):
        raise ValueError("Tev1 family/case structure changed or repeats a case")
    heldout_case_count = 0
    invalid_tev1 = 0
    for family, info in families.items():
        rows = [row for row in tev1 if row["family"] == family]
        if len(rows) != int(info["cases"]):
            raise ValueError(f"Tev1 case count changed for {family}")
        for split in ("development", "heldout"):
            subset = [row for row in rows if row["split"] == split]
            expected_n = int(info[split])
            if len(subset) != expected_n:
                raise ValueError(f"Tev1 {family}/{split} count changed")
        dev_cases = {row["case_id"] for row in rows if row["split"] == "development"}
        held_cases = {row["case_id"] for row in rows if row["split"] == "heldout"}
        if dev_cases & held_cases:
            raise ValueError(f"Tev1 development/held-out case leakage for {family}")
        heldout_case_count += len(held_cases)
        classes = info["outcome_classes"]
        for row in rows:
            if row["split"] not in {"development", "heldout"}:
                raise ValueError("Tev1 row has an unknown split")
            if row.get("gold_label") not in classes or row.get(
                "gold_index"
            ) != classes.index(row["gold_label"]):
                raise ValueError(
                    f"Tev1 label index does not match {family} class order"
                )
            if not row.get("valid"):
                invalid_tev1 += 1
                continue
            probabilities = row.get("probs")
            if not isinstance(probabilities, list) or len(probabilities) != len(
                classes
            ):
                raise ValueError(
                    f"Tev1 probability vector shape is invalid for {family}"
                )
            if any(
                not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                or not 0.0 <= float(value) <= 1.0
                for value in probabilities
            ) or not math.isclose(sum(probabilities), 1.0, rel_tol=1e-7, abs_tol=1e-7):
                raise ValueError(
                    f"Tev1 output is not a probability vector for {family}"
                )
    return {
        "status": "PASS",
        "relevance_rows": len(relevance),
        "relevance_invalid_outputs": invalid_relevance,
        "relevance_queries": expected_group_count,
        "heldout_query_clusters": len(domains) * heldout_queries,
        "heldout_rows_per_model_domain": expected_items * heldout_queries,
        "tev1_rows": len(tev1),
        "tev1_invalid_outputs": invalid_tev1,
        "tev1_heldout_cases": heldout_case_count,
        "score_types_by_role": {
            model: sorted(
                {row["score_type"] for row in relevance if row["model"] == model}
            )
            for model in sorted(models)
        },
        "split_key_checks": ["model/domain/query_id", "family/case_id"],
        "split_overlap_count": 0,
        "effective_sample_units": {
            "one_bug_retrieval": "one bug; order seeds are repeated perturbations",
            "model_role_relevance": f"{len(domains) * heldout_queries} held-out query clusters; one frozen case set",
            "model_role_tev1": f"{heldout_case_count} held-out authored cases; one frozen case set",
            "independent_model_role_runs": 1,
        },
    }


def validate_model_role_protocol(root: Path, run: dict[str, Any]) -> dict[str, Any]:
    prereg = _json(root / MODEL_PREREG)
    for relative, expected in prereg.get("frozen_source_sha256", {}).items():
        path = root / relative
        if not path.is_file() or _sha(path.read_bytes()) != expected:
            raise ValueError(f"frozen model-role source identity changed: {relative}")
    for relative, expected in prereg.get("preflight_artifacts_sha256", {}).items():
        path = root / relative
        if not path.is_file() or _sha(path.read_bytes()) != expected:
            raise ValueError(
                f"model-role preflight artifact identity changed: {relative}"
            )
    from scripts import model_role_metrics

    generated_cases = {
        "tev1": model_role_metrics.generate_tev1_cases(
            int(prereg["seeds"]["tev1_cases"])
        ),
        "relevance": model_role_metrics.generate_relevance_cases(
            int(prereg["seeds"]["relevance_cases"])
        ),
    }
    case_set_digest = _digest_json(generated_cases)
    if case_set_digest != prereg["frozen_case_set_sha256"]:
        raise ValueError(
            "generated frozen model-role case set does not match preregistration"
        )
    if run.get("study_id") != prereg.get("study_id"):
        raise ValueError("model-role experiment ID differs from preregistration")
    if run.get("evidence_class") != "synthetic":
        raise ValueError("model-role evidence is not explicitly labeled synthetic")
    if run.get("preregistration_sha256") != _digest_json(prereg):
        raise ValueError("model-role preregistration digest does not match raw run")
    if run.get("case_set_sha256") != case_set_digest:
        raise ValueError(
            "model-role case-set identity differs from generated frozen cases"
        )
    if run.get("prompt_template_sha256") != prereg.get("frozen_prompt_template_sha256"):
        raise ValueError("model-role prompt identity differs from preregistration")
    if run.get("prompt_version") != prereg["generation"]["chat_prompt_version"]:
        raise ValueError("model-role prompt version differs from preregistration")
    if run.get("ollama_version") != prereg.get("service_version"):
        raise ValueError("model-role runtime version differs from preregistration")
    expected_models = {
        role: config.get("manifest_sha256", config.get("identity_sha256"))
        for role, config in prereg["models"].items()
    }
    if run.get("model_identity_sha256") != expected_models:
        raise ValueError(
            "model-role model identity digests differ from preregistration"
        )
    row_checks = _validate_model_role_rows(run, prereg)
    return {
        "status": "PASS",
        "study_id": prereg["study_id"],
        "preregistration_sha256": run["preregistration_sha256"],
        "case_set_sha256": case_set_digest,
        "prompt_template_sha256": run["prompt_template_sha256"],
        "model_identity_sha256": expected_models,
        "runtime_version": run["ollama_version"],
        "row_structure": row_checks,
        "source_files_checked": len(prereg.get("frozen_source_sha256", {})),
        "preflight_artifacts_checked": len(
            prereg.get("preflight_artifacts_sha256", {})
        ),
    }


def recompute_selection_sweep(root: Path) -> dict[str, Any]:
    from scripts.reanalyze_bouleusis_sweep import analyze

    _, rows = _load_raw(root, "evidence-selection-sweep-2026-10-08.jsonl.gz")
    with tempfile.TemporaryDirectory(prefix="isoprax-paper-") as temp:
        source = Path(temp) / "selection.jsonl"
        source.write_bytes(
            gzip.decompress(
                (
                    root / RAW / "evidence-selection-sweep-2026-10-08.jsonl.gz"
                ).read_bytes()
            )
        )
        computed = analyze(source)
    saved = _json(root / "docs/research/bouleusis-retrieval-sweep-reanalysis.json")
    if computed != saved:
        raise ValueError(
            "one-bug raw-sweep recomputation differs from saved reanalysis"
        )
    if len(rows) != 170:
        raise ValueError(f"one-bug run count changed: {len(rows)}")
    return {
        "source_of_record": "raw JSONL; existing derived reanalysis independently matched",
        "run_count": len(rows),
        "runs_by_arm_budget": computed["structure"]["runs_by_arm_and_budget"],
        "per_run_outcomes": computed["per_run_outcomes"],
        "condition_summaries": computed["recomputed_condition_summaries"],
        "source_summary_match": True,
    }


def recompute_multibug(root: Path) -> dict[str, Any]:
    metadata, rows = _load_raw(root, "retrieval-multibug-2026-10-08.jsonl.gz")
    if len(rows) != 228 or len({r["case_id"] for r in rows}) != 12:
        raise ValueError("multi-bug run count or case count changed")
    by_condition: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_condition[(row["arm"], row["budget"]["id"])].append(row)
    if len(by_condition) != 19 or any(
        len(group) != 12 for group in by_condition.values()
    ):
        raise ValueError("multi-bug arm/budget/case structure changed")
    summaries = []
    for (arm, budget), group in sorted(by_condition.items()):
        successes = sum(bool(r["debugging_success"]) for r in group)
        summaries.append(
            {
                "arm": arm,
                "budget_id": budget,
                "n_cases": len(group),
                "debugging_success_count": successes,
                "debugging_success_rate": successes / len(group),
                "mean_selected_bytes": statistics.mean(
                    float(r["selected_bytes"]) for r in group
                ),
                "mean_decisive_evidence_recall": statistics.mean(
                    float(r["decisive_evidence_recall"]) for r in group
                ),
                "false_belief_mass_by_case": [
                    {
                        "case_id": r["case_id"],
                        "mass": r["epistemic"]["false_belief_confidence_mass"],
                    }
                    for r in sorted(group, key=lambda item: item["case_id"])
                ],
            }
        )
    per_run = [
        {
            "case_id": r["case_id"],
            "arm": r["arm"],
            "budget_id": r["budget"]["id"],
            "seed": r["seed"],
            "selected_bytes": r["selected_bytes"],
            "decisive_evidence_recall": r["decisive_evidence_recall"],
            "debugging_success": r["debugging_success"],
            "false_belief_confidence_mass": r["epistemic"][
                "false_belief_confidence_mass"
            ],
        }
        for r in rows
    ]
    all_evidence = [s for s in summaries if s["budget_id"] == "all-evidence"]
    if any(s["debugging_success_count"] != 12 for s in all_evidence):
        raise ValueError("all-evidence convergence no longer holds")
    if any(item["false_belief_confidence_mass"] != 0 for item in per_run):
        raise ValueError("multi-bug records contain nonzero false-belief mass")
    return {
        "source_of_record": "raw JSONL",
        "run_count": len(rows),
        "case_count": len({r["case_id"] for r in rows}),
        "arm_budget_counts": [
            {"arm": arm, "budget_id": budget, "n": len(group)}
            for (arm, budget), group in sorted(by_condition.items())
        ],
        "summaries": summaries,
        "per_run_outcomes": per_run,
        "metadata_protocol_sha256": metadata.get("preregistration_sha256"),
        "all_evidence_converges": True,
    }


def recompute_voi(root: Path) -> dict[str, Any]:
    _, rows = _load_raw(root, "evidence-acquisition-voi-2026-10-08.jsonl.gz")
    if len(rows) != 144:
        raise ValueError(f"VOI row count changed: {len(rows)}")
    by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_state: dict[tuple[str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    for r in rows:
        by_policy[r["policy_id"]].append(r)
        by_state[(r["case_id"], r["budget"])][r["policy_id"]] = r
    if len(by_state) != 24 or any(len(x) != 6 for x in by_state.values()):
        raise ValueError("VOI case/budget/policy structure changed")
    voi_id = "deterministic-value-of-information"
    always_id = "always-retrieve-after-abstention"
    if voi_id not in by_policy or always_id not in by_policy:
        raise ValueError("expected VOI policies are missing")
    same_actions = 0
    for policies in by_state.values():
        if policies[voi_id]["chosen_action"] == policies[always_id]["chosen_action"]:
            same_actions += 1
    if same_actions != len(by_state):
        raise ValueError("VOI choices no longer match always-retrieve on every state")
    per_policy = []
    for policy, group in sorted(by_policy.items()):
        successes = sum(bool(r["outcome"]["debugging_success"]) for r in group)
        unnecessary = sum(
            bool(r["changes"]["task_outcome_unnecessary_acquisition"]) for r in group
        )
        per_policy.append(
            {
                "policy_id": policy,
                "n": len(group),
                "debugging_success_count": successes,
                "debugging_success_rate": successes / len(group),
                "mean_actual_acquired_bytes": statistics.mean(
                    r["acquisition_cost"]["actual_acquired_bytes"] for r in group
                ),
                "unnecessary_acquisition_count": unnecessary,
                "false_belief_mass_before": statistics.mean(
                    r["epistemic"]["metrics_before"]["false_belief_confidence_mass"]
                    for r in group
                ),
                "false_belief_mass_after": statistics.mean(
                    r["epistemic"]["metrics_after"]["false_belief_confidence_mass"]
                    for r in group
                ),
            }
        )
    per_run = [
        {
            "run_id": r["run_id"],
            "case_id": r["case_id"],
            "budget": r["budget"],
            "policy_id": r["policy_id"],
            "chosen_action": r["chosen_action"],
            "actual_acquired_bytes": r["acquisition_cost"]["actual_acquired_bytes"],
            "debugging_success": r["outcome"]["debugging_success"],
            "task_outcome_unnecessary_acquisition": r["changes"][
                "task_outcome_unnecessary_acquisition"
            ],
            "false_belief_mass_before": r["epistemic"]["metrics_before"][
                "false_belief_confidence_mass"
            ],
            "false_belief_mass_after": r["epistemic"]["metrics_after"][
                "false_belief_confidence_mass"
            ],
        }
        for r in rows
    ]
    return {
        "source_of_record": "raw JSONL",
        "run_count": len(rows),
        "state_count": len(by_state),
        "policy_count": len(by_policy),
        "deterministic_voi_matches_always_retrieve_states": same_actions,
        "policy_summaries": per_policy,
        "per_run_outcomes": per_run,
    }


def _auc(labels: list[int], scores: list[float]) -> float | None:
    pos = [s for y, s in zip(labels, scores, strict=True) if y == 1]
    neg = [s for y, s in zip(labels, scores, strict=True) if y == 0]
    if not pos or not neg:
        return None
    order = sorted(range(len(scores)), key=lambda i: scores[i])
    rank_sum = 0.0
    index = 0
    while index < len(order):
        end = index + 1
        while end < len(order) and scores[order[end]] == scores[order[index]]:
            end += 1
        mean_rank = (index + 1 + end) / 2
        rank_sum += mean_rank * sum(labels[order[pos]] for pos in range(index, end))
        index = end
    return (rank_sum - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def _binary_metrics(
    rows: list[dict[str, Any]], probability_key: str = "p"
) -> dict[str, Any]:
    valid = [
        r for r in rows if r.get("valid", True) and r.get(probability_key) is not None
    ]
    if not valid:
        return {
            "n": 0,
            "brier": None,
            "log_loss": None,
            "accuracy": None,
            "event_rate": None,
            "auc": None,
            "ece": None,
        }
    ys = [int(bool(r["gold"])) for r in valid]
    ps = [min(1 - 1e-12, max(1e-12, float(r[probability_key]))) for r in valid]
    predicted = [int(p >= 0.5) for p in ps]
    brier = statistics.mean(
        (p - y) ** 2 + ((1 - p) - (1 - y)) ** 2 for p, y in zip(ps, ys, strict=True)
    )
    logloss = -statistics.mean(
        math.log(p if y else 1 - p) for p, y in zip(ps, ys, strict=True)
    )
    confidences = [max(p, 1 - p) for p in ps]
    correct = [int(a == b) for a, b in zip(predicted, ys, strict=True)]
    ece = 0.0
    for i in range(5):
        members = [
            j
            for j, conf in enumerate(confidences)
            if i / 5 <= conf and (conf <= (i + 1) / 5 if i == 4 else conf < (i + 1) / 5)
        ]
        if members:
            ece += (
                len(members)
                / len(valid)
                * abs(
                    statistics.mean(correct[j] for j in members)
                    - statistics.mean(confidences[j] for j in members)
                )
            )
    return {
        "n": len(valid),
        "positive_count": sum(ys),
        "event_rate": statistics.mean(ys),
        "brier": brier,
        "log_loss": logloss,
        "accuracy": statistics.mean(
            int(a == b) for a, b in zip(predicted, ys, strict=True)
        ),
        "auc": _auc(ys, ps),
        "ece": ece,
    }


def _binary_value(rows: list[dict[str, Any]], key: str) -> float | None:
    valid = [r for r in rows if r.get("valid", True) and r.get("p") is not None]
    if not valid:
        return None
    ys = [int(bool(r["gold"])) for r in valid]
    ps = [min(1 - 1e-12, max(1e-12, float(r["p"]))) for r in valid]
    if key == "brier":
        return statistics.mean(
            (p - y) ** 2 + ((1 - p) - (1 - y)) ** 2 for p, y in zip(ps, ys, strict=True)
        )
    if key == "log_loss":
        return -statistics.mean(
            math.log(p if y else 1 - p) for p, y in zip(ps, ys, strict=True)
        )
    if key == "auc":
        return _auc(ys, ps)
    if key == "accuracy":
        return statistics.mean(
            int((p >= 0.5) == bool(y)) for p, y in zip(ps, ys, strict=True)
        )
    if key == "event_rate":
        return statistics.mean(ys)
    raise ValueError(f"unsupported binary metric: {key}")


def _bootstrap(
    rows: list[dict[str, Any]],
    fn: Callable[[list[dict[str, Any]]], float | None],
    seed: int,
    reps: int = REPLICATES,
    group_key: str = "query_id",
) -> list[float] | None:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for index, row in enumerate(rows):
        groups[str(row.get(group_key, row.get("case_id", index)))].append(row)
    keys = list(groups)
    if not keys:
        return None
    rng = random.Random(seed)
    vals = []
    for _ in range(reps):
        sample = [
            item for key in (rng.choice(keys) for _ in keys) for item in groups[key]
        ]
        value = fn(sample)
        if value is not None and math.isfinite(value):
            vals.append(value)
    if not vals:
        return None
    return [float(np.quantile(vals, 0.025)), float(np.quantile(vals, 0.975))]


def _metrics_with_uncertainty(
    rows: list[dict[str, Any]], seed: int, group_key: str = "query_id"
) -> dict[str, Any]:
    point = _binary_metrics(rows)
    point["query_count"] = len(
        {
            r["query_id"]
            for r in rows
            if r.get("valid", True) and r.get("p") is not None and "query_id" in r
        }
    )
    point["invalid_count"] = sum(not r.get("valid", True) for r in rows)
    result = dict(point)
    result["uncertainty_95"] = {
        key: _bootstrap(
            rows,
            lambda sample, name=key: _binary_value(sample, name),
            seed + i,
            group_key=group_key,
        )
        for i, key in enumerate(("brier", "log_loss", "auc"))
    }
    return result


def _mixture_interval(
    rows: list[dict[str, Any]], metric: str, seed: int
) -> list[float] | None:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for row in rows:
        if row.get("valid") and row.get("p") is not None:
            grouped[row["domain"]][row["query_id"]].append(row)
    if any(not grouped[domain] for domain in DOMAINS):
        return None
    rng = random.Random(seed)
    draws = []
    for _ in range(REPLICATES):
        values = []
        for domain in DOMAINS:
            keys = list(grouped[domain])
            sample = [
                item
                for query in (rng.choice(keys) for _ in keys)
                for item in grouped[domain][query]
            ]
            score = _binary_value(sample, metric)
            if score is None:
                break
            values.append(score)
        if len(values) == len(DOMAINS):
            draws.append(statistics.mean(values))
    return (
        [float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))]
        if draws
        else None
    )


def _rank_metrics(
    rows: list[dict[str, Any]], score_key: str, seed: int
) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("valid") and row.get(score_key) is not None:
            grouped[row["query_id"]].append(row)
    query_values: list[tuple[float, dict[int, float]]] = []
    tops: dict[str, str] = {}
    for query, items in sorted(grouped.items()):
        if len(items) != 8:
            continue
        ranked = sorted(
            items, key=lambda item: (-float(item[score_key]), item["item_id"])
        )
        relevant = {item["item_id"] for item in items if item["gold"]}
        ranks = [i + 1 for i, item in enumerate(ranked) if item["item_id"] in relevant]
        query_values.append(
            (
                1 / min(ranks) if ranks else 0.0,
                {
                    k: len({r["item_id"] for r in ranked[:k]} & relevant)
                    / max(1, len(relevant))
                    for k in (1, 3, 5)
                },
            )
        )
        tops[query] = ranked[0]["item_id"]
    if not query_values:
        return {
            "query_count": len(grouped),
            "ranked_query_count": 0,
            "mrr": None,
            "recall_at_k": {},
            "top_item_by_query": tops,
        }
    rng = random.Random(seed)
    draws = {"mrr": [], 1: [], 3: [], 5: []}
    for _ in range(REPLICATES):
        sample = [rng.choice(query_values) for _ in query_values]
        draws["mrr"].append(statistics.mean(x[0] for x in sample))
        for k in (1, 3, 5):
            draws[k].append(statistics.mean(x[1][k] for x in sample))
    return {
        "query_count": len(grouped),
        "ranked_query_count": len(query_values),
        "mrr": statistics.mean(x[0] for x in query_values),
        "recall_at_k": {
            str(k): statistics.mean(x[1][k] for x in query_values) for k in (1, 3, 5)
        },
        "uncertainty_95": {
            "mrr": [
                float(np.quantile(draws["mrr"], 0.025)),
                float(np.quantile(draws["mrr"], 0.975)),
            ],
            "recall_at_k": {
                str(k): [
                    float(np.quantile(draws[k], 0.025)),
                    float(np.quantile(draws[k], 0.975)),
                ]
                for k in (1, 3, 5)
            },
        },
        "top_item_by_query": tops,
    }


def _tev1_metrics(rows: list[dict[str, Any]], seed: int) -> dict[str, Any]:
    valid = [r for r in rows if r.get("valid") and r.get("probs") is not None]
    if not valid:
        return {"n": 0}
    classes = len(valid[0]["probs"])
    labels = [int(r["gold_index"]) for r in valid]
    matrix = []
    for row in valid:
        p = [max(1e-12, float(x)) for x in row["probs"]]
        total = sum(p)
        matrix.append([x / total for x in p])
    brier = statistics.mean(
        sum((p[k] - int(y == k)) ** 2 for k in range(classes))
        for p, y in zip(matrix, labels, strict=True)
    )
    logloss = -statistics.mean(
        math.log(p[y]) for p, y in zip(matrix, labels, strict=True)
    )
    top = [max(range(classes), key=lambda j: p[j]) for p in matrix]
    confidence = [max(p) for p in matrix]
    ece = 0.0
    for i in range(5):
        selected = [
            j
            for j, c in enumerate(confidence)
            if i / 5 <= c and (c <= (i + 1) / 5 if i == 4 else c < (i + 1) / 5)
        ]
        if selected:
            ece += (
                len(selected)
                / len(valid)
                * abs(
                    statistics.mean(top[j] == labels[j] for j in selected)
                    - statistics.mean(confidence[j] for j in selected)
                )
            )
    aucs = []
    for k in range(classes):
        area = _auc([int(y == k) for y in labels], [p[k] for p in matrix])
        if area is not None:
            aucs.append(area)
    rows_for_boot = [
        dict(
            r,
            _brier=sum(
                (matrix[i][k] - int(labels[i] == k)) ** 2 for k in range(classes)
            ),
            _logloss=-math.log(matrix[i][labels[i]]),
        )
        for i, r in enumerate(valid)
    ]

    def macro_auc(sample: list[dict[str, Any]]) -> float | None:
        if not sample:
            return None
        sample_labels = [int(r["gold_index"]) for r in sample]
        areas = []
        for klass in range(classes):
            area = _auc(
                [int(y == klass) for y in sample_labels],
                [float(r["probs"][klass]) for r in sample],
            )
            if area is not None:
                areas.append(area)
        return statistics.mean(areas) if areas else None

    return {
        "n": len(valid),
        "invalid_count": len(rows) - len(valid),
        "class_counts": dict(Counter(str(r["gold_label"]) for r in valid)),
        "event_rate": sum(
            1 for r in valid if str(r["gold_label"]).lower() in {"true", "yes", "1"}
        )
        / len(valid)
        if set(str(r["gold_label"]).lower() for r in valid)
        <= {"true", "false", "yes", "no", "1", "0"}
        else None,
        "accuracy": statistics.mean(a == b for a, b in zip(top, labels, strict=True)),
        "brier": brier,
        "log_loss": logloss,
        "ece": ece,
        "macro_ovr_auc": statistics.mean(aucs) if aucs else None,
        "uncertainty_95": {
            "brier": _bootstrap(
                rows_for_boot,
                lambda sample: statistics.mean(r["_brier"] for r in sample),
                seed,
                group_key="case_id",
            ),
            "log_loss": _bootstrap(
                rows_for_boot,
                lambda sample: statistics.mean(r["_logloss"] for r in sample),
                seed,
                group_key="case_id",
            ),
            "macro_ovr_auc": _bootstrap(valid, macro_auc, seed, group_key="case_id"),
        },
    }


def _fit_platt(development_rows: list[dict[str, Any]]) -> LogisticRegression:
    """Fit the frozen calibration form from development rows only."""
    usable = [
        r for r in development_rows if r.get("valid") and r.get("raw_score") is not None
    ]
    if len({bool(r["gold"]) for r in usable}) < 2:
        raise ValueError("development calibration rows must include both classes")
    calibrator = LogisticRegression(
        C=1.0, solver="liblinear", max_iter=1000, random_state=47063
    )
    calibrator.fit(
        [[float(r["raw_score"])] for r in usable], [int(r["gold"]) for r in usable]
    )
    return calibrator


def recompute_model_role(root: Path) -> dict[str, Any]:
    manifest = _json(root / MODEL_MANIFEST)
    if set(manifest.get("runs", {})) != {"1", "2"}:
        raise ValueError("model-role run manifest must identify runs 1 and 2")
    run_payloads = []
    run_data = []
    for run in ("1", "2"):
        entry = manifest["runs"][run]
        raw = _load_model_role_archive(root, entry)
        run_payloads.append(raw)
        run_data.append(json.loads(raw))
    if run_payloads[0] != run_payloads[1]:
        raise ValueError("frozen model-role replay artifacts are not byte-identical")
    run = run_data[0]
    model_validation = validate_model_role_protocol(root, run)
    expected_predictions_digest = _digest_json(
        {
            "tev1": run["tev1_rows"],
            "relevance": [
                {
                    key: row.get(key)
                    for key in (
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
                for row in run["relevance_rows"]
            ],
        }
    )
    if run.get("predictions_sha256") != expected_predictions_digest:
        raise ValueError("model-role predictions digest does not recompute")
    if run.get("raw_response_sha256") != _digest_json(run["raw_responses"]):
        raise ValueError("model-role raw-response digest does not recompute")
    result_for_hash = dict(run)
    recorded_result_digest = result_for_hash.pop("result_sha256", None)
    if recorded_result_digest != _digest_json(result_for_hash):
        raise ValueError("model-role result digest does not recompute")
    tev1 = {}
    for fi, family in enumerate(TEV1_FAMILIES):
        tev1[family] = {}
        for split in ("development", "heldout"):
            rows = [
                r
                for r in run["tev1_rows"]
                if r["family"] == family and r["split"] == split
            ]
            metrics = _tev1_metrics(
                rows, 47062 + fi if split == "development" else 47065 + fi
            )
            saved = run["tev1_summary"][family][split]
            for key, source in (
                ("n", "count"),
                ("accuracy", "accuracy"),
                ("brier", "brier"),
                ("log_loss", "log_loss"),
                ("ece", "expected_calibration_error"),
            ):
                if key == "n":
                    if metrics[key] != saved[source]:
                        raise ValueError(f"Tev1 {family}/{split} {key} mismatch")
                elif not _close(metrics.get(key), saved.get(source)):
                    raise ValueError(f"Tev1 {family}/{split} {key} mismatch")
            ci_map = {"brier": "brier", "log_loss": "log_loss", "macro_ovr_auc": "auc"}
            for own, other in ci_map.items():
                if not _same_tree(
                    metrics["uncertainty_95"][own], saved["uncertainty_95"].get(other)
                ):
                    raise ValueError(
                        f"Tev1 {family}/{split} {own} confidence interval mismatch"
                    )
            tev1[family][split] = metrics
    tev1_test_rows = {
        family: [
            r
            for r in run["tev1_rows"]
            if r["family"] == family and r["split"] == "heldout" and r["valid"]
        ]
        for family in TEV1_FAMILIES
    }
    mixture_losses = [tev1[family]["heldout"]["log_loss"] for family in TEV1_FAMILIES]
    mix_rng = random.Random(47068)
    mix_draws = []
    for _ in range(REPLICATES):
        sampled = []
        for family in TEV1_FAMILIES:
            group = tev1_test_rows[family]
            sample = [mix_rng.choice(group) for _ in group]
            sampled.append(
                -statistics.mean(
                    math.log(max(1e-12, float(r["probs"][r["gold_index"]])))
                    for r in sample
                )
            )
        mix_draws.append(statistics.mean(sampled))
    tev1_mixture = {
        "estimand": "expected Tev1 log loss when one family is sampled uniformly from the three authored families",
        "weights": {family: 1 / 3 for family in TEV1_FAMILIES},
        "equal_weight_expected_log_loss": statistics.mean(mixture_losses),
        "uncertainty_95": [
            float(np.quantile(mix_draws, 0.025)),
            float(np.quantile(mix_draws, 0.975)),
        ],
    }
    stored_mix = run["tev1_summary"]["declared_mixture"]
    if not _close(
        tev1_mixture["equal_weight_expected_log_loss"],
        stored_mix["equal_weight_expected_log_loss"],
    ):
        raise ValueError("Tev1 predeclared equal-family mixture does not recompute")
    # Fit the preregistered Platt calibrator anew from raw development scores.
    scored_by_model: dict[str, list[dict[str, Any]]] = {}
    per_model = {}
    for model in MODELS:
        rows = [r for r in run["relevance_rows"] if r["model"] == model]
        dev = [r for r in rows if r["split"] == "development" and r["valid"]]
        held = [r for r in rows if r["split"] == "heldout" and r["valid"]]
        calibrator = _fit_platt(dev)
        global_scored = []
        global_probs = calibrator.predict_proba(
            [[float(r["raw_score"])] for r in held]
        )[:, 1]
        for row, probability in zip(held, global_probs, strict=True):
            item = dict(row)
            item["p"] = float(probability)
            global_scored.append(item)
        scored_by_model[model] = global_scored
        domain_results = {}
        for di, domain in enumerate(DOMAINS):
            ddev = [r for r in dev if r["domain"] == domain]
            dheld = [r for r in held if r["domain"] == domain]
            local = _fit_platt(ddev)
            local_scored = []
            local_probs = local.predict_proba([[float(r["raw_score"])] for r in dheld])[
                :, 1
            ]
            for row, probability in zip(dheld, local_probs, strict=True):
                item = dict(row)
                item["p"] = float(probability)
                local_scored.append(item)
            global_domain = [r for r in global_scored if r["domain"] == domain]
            domain_results[domain] = {
                "n_development": len(ddev),
                "n_heldout": len(dheld),
                "event_count": sum(bool(r["gold"]) for r in dheld),
                "score_type": dheld[0]["score_type"] if dheld else None,
                "raw_score_auc": _auc(
                    [int(r["gold"]) for r in dheld],
                    [float(r["raw_score"]) for r in dheld],
                ),
                "domain_calibrated": _metrics_with_uncertainty(
                    local_scored, 47064 + di
                ),
                "global_calibrated": _metrics_with_uncertainty(global_domain, 47064),
                "raw_ranking": _rank_metrics(dheld, "raw_score", 47065),
                "calibrated_ranking": _rank_metrics(local_scored, "p", 47065),
                "invalid_heldout_count": sum(
                    not r["valid"]
                    for r in rows
                    if r["domain"] == domain and r["split"] == "heldout"
                ),
            }
            saved_domain = run["relevance_summary"][model]["domains"][domain]
            for own, other in (
                ("domain_calibrated", "heldout"),
                ("global_calibrated", "global_calibration_heldout"),
            ):
                computed = domain_results[domain][own]
                archived = saved_domain[other]
                field_map = {
                    "n": "count",
                    "event_rate": "event_rate",
                    "brier": "brier",
                    "log_loss": "log_loss",
                    "accuracy": "accuracy",
                    "auc": "auc",
                    "ece": "expected_calibration_error",
                    "query_count": "query_count",
                    "invalid_count": "invalid_count",
                }
                for lhs, rhs in field_map.items():
                    if lhs in computed and not _same_tree(
                        computed[lhs], archived.get(rhs)
                    ):
                        raise ValueError(
                            f"model-role {model}/{domain}/{own} {lhs} mismatch"
                        )
                for metric in ("brier", "log_loss", "auc"):
                    if not _same_tree(
                        computed["uncertainty_95"][metric],
                        archived["uncertainty_95"].get(metric),
                    ):
                        raise ValueError(
                            f"model-role {model}/{domain}/{own} {metric} interval mismatch"
                        )
            for own, other in (
                ("raw_ranking", "raw_ranking"),
                ("calibrated_ranking", "calibrated_ranking"),
            ):
                computed = domain_results[domain][own]
                archived = saved_domain[other]
                for key in (
                    "query_count",
                    "ranked_query_count",
                    "incomplete_query_count",
                    "mrr",
                    "recall_at_k",
                    "uncertainty_95",
                    "top_item_by_query",
                ):
                    if key in computed and not _same_tree(
                        computed[key], archived.get(key)
                    ):
                        raise ValueError(
                            f"model-role {model}/{domain}/{own} {key} mismatch"
                        )
        per_model[model] = {
            "native_score_types": sorted({r["score_type"] for r in rows}),
            "domains": domain_results,
        }
    # Pair the original hard judgments by query/item. Do not interpret the pairs as independent.
    dependence = {}
    for i, left in enumerate(JUDGES):
        for right in JUDGES[i + 1 :]:
            lrows = {
                (r["query_id"], r["item_id"]): r
                for r in run["relevance_rows"]
                if r["model"] == left and r["split"] == "heldout" and r["valid"]
            }
            rrows = {
                (r["query_id"], r["item_id"]): r
                for r in run["relevance_rows"]
                if r["model"] == right and r["split"] == "heldout" and r["valid"]
            }
            common = sorted(set(lrows) & set(rrows))
            errors_left = [lrows[k]["label"] != lrows[k]["gold"] for k in common]
            errors_right = [rrows[k]["label"] != rrows[k]["gold"] for k in common]
            paired_rows = [
                {"query_id": k[0], "joint": a and b}
                for k, a, b in zip(common, errors_left, errors_right, strict=True)
            ]
            query_ids = sorted({r["query_id"] for r in paired_rows})
            by_query_detail = {
                query: {
                    "query_id": query,
                    "paired_items": 0,
                    "label_disagreement_count": 0,
                    "left_error_count": 0,
                    "right_error_count": 0,
                    "joint_error_count": 0,
                }
                for query in query_ids
            }
            per_item = []
            for key, left_error, right_error in zip(
                common, errors_left, errors_right, strict=True
            ):
                query_id, item_id = key
                left_label = lrows[key]["label"]
                right_label = rrows[key]["label"]
                disagreement = left_label != right_label
                joint_error = left_error and right_error
                detail = by_query_detail[query_id]
                detail["paired_items"] += 1
                detail["label_disagreement_count"] += int(disagreement)
                detail["left_error_count"] += int(left_error)
                detail["right_error_count"] += int(right_error)
                detail["joint_error_count"] += int(joint_error)
                per_item.append(
                    {
                        "query_id": query_id,
                        "item_id": item_id,
                        "gold": lrows[key]["gold"],
                        "left_label": left_label,
                        "right_label": right_label,
                        "left_error": left_error,
                        "right_error": right_error,
                        "joint_error": joint_error,
                    }
                )
            interval = None
            if query_ids:
                rng = random.Random(47066 + i)
                values = []
                by_query = defaultdict(list)
                for row in paired_rows:
                    by_query[row["query_id"]].append(row["joint"])
                for _ in range(REPLICATES):
                    sample = [
                        x
                        for query in (rng.choice(query_ids) for _ in query_ids)
                        for x in by_query[query]
                    ]
                    values.append(sum(sample) / len(sample))
                interval = [
                    float(np.quantile(values, 0.025)),
                    float(np.quantile(values, 0.975)),
                ]
            dependence[f"{left}+{right}"] = {
                "paired_items": len(common),
                "paired_queries": len({k[0] for k in common}),
                "label_disagreement_count": sum(
                    lrows[k]["label"] != rrows[k]["label"] for k in common
                ),
                "joint_error_count": sum(
                    a and b for a, b in zip(errors_left, errors_right, strict=True)
                ),
                "left_error_count": sum(errors_left),
                "right_error_count": sum(errors_right),
                "heldout_joint_error_rate": statistics.mean(
                    a and b for a, b in zip(errors_left, errors_right, strict=True)
                )
                if common
                else None,
                "heldout_joint_error_rate_query_bootstrap_95": interval,
                "zero_joint_errors_are_not_independence_evidence": True,
                "per_query": [by_query_detail[q] for q in query_ids],
                "per_item": per_item,
            }
    # Declared common-relevance estimand: equal-weight mean of domains, then metrics.
    judges = {m: scored_by_model[m] for m in JUDGES}
    keysets = [{(r["query_id"], r["item_id"]) for r in judges[m]} for m in JUDGES]
    common = sorted(set.intersection(*keysets))
    pool = []
    for query, item in common:
        members = [
            next(
                r for r in judges[m] if r["query_id"] == query and r["item_id"] == item
            )
            for m in JUDGES
        ]
        p = statistics.mean(float(r["p"]) for r in members)
        base = members[0]
        pool.append(
            {
                "query_id": query,
                "item_id": item,
                "domain": base["domain"],
                "gold": base["gold"],
                "valid": True,
                "p": p,
            }
        )
    pool_by_domain = {
        d: _metrics_with_uncertainty([r for r in pool if r["domain"] == d], 47064)
        for d in DOMAINS
    }
    individual_global = {
        m: {
            d: _metrics_with_uncertainty(
                [r for r in scored_by_model[m] if r["domain"] == d], 47064
            )
            for d in DOMAINS
        }
        for m in JUDGES
    }
    equal_domain = {
        key: statistics.mean(pool_by_domain[d][key] for d in DOMAINS)
        for key in ("brier", "log_loss", "auc", "accuracy", "event_rate")
    }
    stored_pool = run["relevance_summary"]["judge_pools"][
        "equal_weight_calibrated_probability"
    ]
    if not _same_tree(equal_domain, stored_pool["equal_weight_domain_mixture"]):
        raise ValueError(
            "equal-weight probability pool metrics differ from frozen report"
        )
    individual_equal = {
        m: {
            key: statistics.mean(individual_global[m][d][key] for d in DOMAINS)
            for key in equal_domain
        }
        for m in JUDGES
    }
    equal_domain_uncertainty = {
        "equal_weight_probability_pool": {
            key: _mixture_interval(pool, key, 47095 + i)
            for i, key in enumerate(("brier", "log_loss", "auc"))
        },
        "individual_judges": {
            model: {
                key: _mixture_interval(
                    scored_by_model[model], key, 47070 + MODELS.index(model) * 10 + i
                )
                for i, key in enumerate(("brier", "log_loss", "auc"))
            }
            for model in MODELS
        },
    }
    if not _same_tree(
        equal_domain_uncertainty["equal_weight_probability_pool"],
        stored_pool["uncertainty_95"],
    ):
        raise ValueError(
            "equal-weight probability pool intervals differ from frozen report"
        )
    coder_gemma = {}
    for baseline in ("qwen", "gemma"):
        comparisons = []
        for domain in DOMAINS:
            cr = [
                r
                for r in run["relevance_rows"]
                if r["model"] == "coder"
                and r["domain"] == domain
                and r["split"] == "heldout"
            ]
            br = [
                r
                for r in run["relevance_rows"]
                if r["model"] == baseline
                and r["domain"] == domain
                and r["split"] == "heldout"
            ]
            ct = _rank_metrics(cr, "raw_score", 47065)["top_item_by_query"]
            bt = _rank_metrics(br, "raw_score", 47065)["top_item_by_query"]
            comparisons.extend(
                (domain, q, ct[q], bt[q]) for q in sorted(set(ct) & set(bt))
            )
        per_query = [
            {
                "domain": domain,
                "query_id": query_id,
                "coder_top_item": coder_item,
                "baseline_top_item": baseline_item,
                "disagrees": coder_item != baseline_item,
            }
            for domain, query_id, coder_item, baseline_item in comparisons
        ]
        coder_gemma[baseline] = {
            "paired_queries": len(comparisons),
            "top_item_disagreements": sum(a != b for _, _, a, b in comparisons),
            "by_domain": {
                d: {
                    "n": sum(x[0] == d for x in comparisons),
                    "disagreements": sum(
                        x[0] == d and x[2] != x[3] for x in comparisons
                    ),
                }
                for d in DOMAINS
            },
            "per_query": per_query,
        }
    return {
        "source_of_record": "two preserved raw run artifacts; metrics independently recomputed from rows",
        "exact_replay": {
            "uncompressed_sha256_run_1": _sha(run_payloads[0]),
            "uncompressed_sha256_run_2": _sha(run_payloads[1]),
            "byte_identical": True,
            "tev1_rows_per_run": len(run["tev1_rows"]),
            "relevance_rows_per_run": len(run["relevance_rows"]),
            "raw_responses_per_run": len(run["raw_responses"]),
            "independent_run_count": 1,
            "case_level_differences": 0,
            "run_commit_timing": "preregistration bytes hashed before scored calls; Git commit was made after Run 1 began",
        },
        "protocol_validation": model_validation,
        "invalid_outputs": {
            "tev1": sum(not r["valid"] for r in run["tev1_rows"]),
            "relevance": sum(not r["valid"] for r in run["relevance_rows"]),
        },
        "tev1_by_family_and_split": tev1,
        "tev1_declared_equal_family_mixture": tev1_mixture,
        "relevance_by_model_and_domain": per_model,
        "relevance_equal_weight_domain_mixtures": {
            "estimand": "expected held-out metric for common authored relevance target with each of four named domains sampled uniformly",
            "domain_weights": {d: 0.25 for d in DOMAINS},
            "aggregation_note": "Brier, log loss, accuracy, and event rate are equal-domain weighted means; AUC is the macro mean of within-domain AUCs, not an item-level pooled AUC.",
            "per_model": {
                model: {
                    key: statistics.mean(
                        per_model[model]["domains"][d]["domain_calibrated"][key]
                        for d in DOMAINS
                    )
                    for key in ("brier", "log_loss", "auc", "accuracy", "event_rate")
                }
                for model in MODELS
            },
            "global_calibration_per_domain_metrics": {
                model: {
                    key: statistics.mean(
                        per_model[model]["domains"][d]["global_calibrated"][key]
                        for d in DOMAINS
                    )
                    for key in ("brier", "log_loss", "auc", "accuracy", "event_rate")
                }
                for model in MODELS
            },
            "uncertainty_95": equal_domain_uncertainty["individual_judges"],
        },
        "judge_dependence": dependence,
        "equal_weight_calibrated_probability_pool": {
            "estimand": "expected metric for the common authored relevance target over four domains sampled uniformly; scores from the three named judges are averaged with equal predeclared weights after development-only calibration",
            "model_weights": {m: 1 / 3 for m in JUDGES},
            "domain_weights": {d: 0.25 for d in DOMAINS},
            "n": len(pool),
            "n_query_clusters": len({r["query_id"] for r in pool}),
            "auc_aggregation": "equal-weight macro average of within-domain AUCs",
            "by_domain": pool_by_domain,
            "equal_domain_metrics": equal_domain,
            "uncertainty_95": equal_domain_uncertainty["equal_weight_probability_pool"],
            "individual_judge_equal_domain_metrics": individual_equal,
        },
        "specialization_top_item_comparison": coder_gemma,
    }


def _numeric_claim_lines(paper: str) -> list[tuple[int, str]]:
    lines = []
    in_references = False
    for n, line in enumerate(paper.splitlines(), start=1):
        if line.strip().lower() == "## references":
            in_references = True
        if in_references or not line.strip() or line.lstrip().startswith("#"):
            continue
        claim_text = re.sub(r"\[\[(?:C|L)\d+\]\]", "", line)
        claim_text = re.sub(r"\bRQ\d+\b", "", claim_text, flags=re.IGNORECASE)
        if re.search(r"\d", claim_text):
            lines.append((n, line))
    return lines


def _validate_numeric_coverage(paper: str, known_ids: set[str]) -> None:
    tagged = set(re.findall(r"\[\[(C\d+|L\d+)\]\]", paper))
    if tagged - known_ids:
        raise ValueError(f"unknown claim tags: {sorted(tagged - known_ids)}")
    uncovered = [
        (n, line)
        for n, line in _numeric_claim_lines(paper)
        if not re.search(r"\[\[(?:C|L)\d+\]\]", line)
    ]
    if uncovered:
        raise ValueError(f"numeric paper claims lack a claim ID: {uncovered}")


def validate_claim_registry(root: Path) -> dict[str, Any]:
    registry = _json(root / CLAIMS)
    claims = registry.get("claims")
    if not isinstance(claims, list) or not claims:
        raise ValueError("claim registry is missing claims")
    ids = [c.get("id") for c in claims]
    if len(ids) != len(set(ids)):
        raise ValueError("claim IDs are not unique")
    required = {
        "id",
        "wording",
        "category",
        "assumptions",
        "source_repository",
        "source_commit",
        "artifacts",
        "protocol",
        "result_or_counterexample",
        "uncertainty",
        "threats_to_validity",
        "qualification",
        "manuscript_section",
    }
    for claim in claims:
        missing = required - set(claim)
        if missing:
            raise ValueError(f"claim {claim.get('id')} misses fields {sorted(missing)}")
        for artifact in claim["artifacts"]:
            if artifact.get("path"):
                path = root / artifact["path"]
                if not path.is_file():
                    raise ValueError(f"claim {claim['id']} artifact missing: {path}")
                if (
                    artifact.get("sha256")
                    and _sha(path.read_bytes()) != artifact["sha256"]
                ):
                    raise ValueError(
                        f"claim {claim['id']} artifact digest changed: {artifact['path']}"
                    )
    paper = (root / PAPER).read_text(encoding="utf-8")
    known = set(ids)
    tagged = set(re.findall(r"\[\[(C\d+|L\d+)\]\]", paper))
    unknown = tagged - known
    expected = {
        claim["id"]
        for claim in claims
        if any(
            section == "main manuscript" or section.startswith("main manuscript:")
            for section in claim["manuscript_section"]
        )
    }
    missing = expected - tagged
    unmapped = tagged - expected
    if unknown or missing or unmapped:
        raise ValueError(
            "claim tag mismatch: "
            f"unknown={sorted(unknown)}, unused={sorted(missing)}, "
            f"not mapped to main manuscript={sorted(unmapped)}"
        )
    _validate_numeric_coverage(paper, known)
    return {
        "claim_count": len(claims),
        "registered_ids": ids,
        "paper_claim_tags": sorted(tagged),
        "numeric_claim_lines_checked": len(_numeric_claim_lines(paper)),
        "all_claim_artifacts_resolve": True,
    }


def _fmt(value: Any, places: int = 3) -> str:
    return "not available" if value is None else f"{float(value):.{places}f}"


def _render_main_tables(benchmark_a: dict[str, Any], gate: dict[str, Any]) -> str:
    def metrics_row(
        label: str, target_id: str, metrics: dict[str, Any], claim: str
    ) -> str:
        auc = (
            "not available (constant scores)"
            if metrics.get("roc_auc") is None
            else _fmt(metrics["roc_auc"])
        )
        return (
            f"| {label} | `{target_id}` | {metrics['n']} | "
            f"{_fmt(metrics['mean_forecast'])} | {_fmt(metrics['event_rate'])} | "
            f"{_fmt(metrics['brier_score'])} | {auc} | [[{claim}]] |"
        )

    rows = [
        "| Condition | Exact target ID | n | Mean forecast | Event rate | Brier | ROC AUC | Evidence |",
        "|---|---|---:|---:|---:|---:|---|---|",
    ]
    for lane in benchmark_a["lanes"]:
        rows.append(
            metrics_row(
                lane["lane"],
                lane["outcome_definition"]["id"],
                lane["metrics"],
                "C9",
            )
        )
    control = benchmark_a["valid_same_target_control"]
    for lane in control["lanes"]:
        rows.append(
            metrics_row(
                f"{lane['lane']} (positive control)",
                lane["outcome_definition"]["id"],
                lane["metrics"],
                "C9",
            )
        )
    rows.append(
        metrics_row(
            "Different-target numeric mixture",
            benchmark_a["declared_numeric_mixture"]["target_definition"]["id"],
            benchmark_a["declared_numeric_mixture"]["metrics"],
            "C9",
        )
    )
    rows.append(
        metrics_row(
            "Same-target positive-control mixture",
            control["target"]["id"],
            control["metrics"],
            "C9",
        )
    )
    table_a = "\n".join(rows)

    rows = [
        "| Rule | False permissions / invalid cases | Unnecessary refusals / valid cases | Interpretation errors / cases | Evidence |",
        "|---|---:|---:|---:|---|",
    ]
    for policy, result in gate["by_policy"].items():
        rows.append(
            f"| {policy.replace('_', ' ')} | {result['false_permissions']}/"
            f"{result['invalid_case_denominator']} | {result['unnecessary_refusals']}/"
            f"{result['valid_case_denominator']} | {result['interpretation_errors']}/"
            f"{result['case_count']} | [[C10]] |"
        )
    table_b = "\n".join(rows)
    return (
        "# Recomputed manuscript tables\n\n"
        "Generated by `scripts/paper_integrity.py` from the deterministic Benchmark A and saved operation-gate case rows. "
        "Ranking-change and decision-change totals are omitted because the saved case rows do not contain the per-case outputs needed to reduce them.\n\n"
        "## Table 1. Synthetic forecast targets and declared mixtures [[C9]]\n\n"
        + table_a
        + "\n\nThe two target-specific lane risks differ in event, observation process, threshold, and window. The different-target mean is a 50:50 mixture over those lane risks; its exact estimand is the target ID shown. It is not the probability of one shared event.\n\n"
        "## Table 2. Operation-specific rule challenge [[C10]]\n\n"
        "The 23 cases were internally authored. The table reports descriptive counts, not estimated population rates.\n\n"
        + table_b
        + "\n\n## Separated evidence\n\n"
        "Model-role, retrieval, acquisition, and the 36-row operation-policy v2 results are not evidence for the main manuscript. Their raw outcomes and recomputed metrics remain in `paper-recomputed-results.json` and the source-specific research note."
    )


def _markdown_tables(document: str) -> list[str]:
    tables = []
    current = []
    for line in document.splitlines():
        if line.startswith("|"):
            current.append(line)
        elif current:
            tables.append("\n".join(current))
            current = []
    if current:
        tables.append("\n".join(current))
    return tables


def _write_or_check(path: Path, content: str, write: bool) -> None:
    if write:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return
    if not path.is_file() or path.read_text(encoding="utf-8") != content:
        raise ValueError(f"generated artifact is stale or changed: {path}")


def recompute_policy_case_metrics(result: dict[str, Any]) -> dict[str, Any]:
    """Independently reduce the frozen operation-policy per-case outcomes."""
    cases = result["per_case"]
    families = sorted({row["public_case"]["operation"] for row in cases})
    summaries = {}
    for family in families:
        rows = [row for row in cases if row["public_case"]["operation"] == family]
        policies = sorted(
            set.intersection(*(set(row["policy_outputs"]) for row in rows))
        )
        valid = [row for row in rows if row["evaluator_outcome"]["expected_permission"]]
        invalid = [
            row for row in rows if not row["evaluator_outcome"]["expected_permission"]
        ]
        ranking = [
            row
            for row in rows
            if row["public_case"].get("context", {}).get("ranking_estimand")
        ]
        decisions = [
            row
            for row in rows
            if "decision_threshold" in row["public_case"].get("context", {})
        ]
        family_result = {"n_cases": len(rows), "policies": {}}
        for policy in policies:
            outputs = {
                row["public_case"]["case_id"]: row["policy_outputs"][policy]
                for row in rows
            }
            labels = {
                row["public_case"]["case_id"]: row["evaluator_outcome"] for row in rows
            }
            ids = [row["public_case"]["case_id"] for row in rows]
            decision_ids = [
                cid
                for cid in ids
                if labels[cid]["expected_decision"] is not None
                and outputs[cid]["decision"] is not None
            ]
            ranking_ids = [
                cid
                for cid in ids
                if labels[cid]["expected_ranking"] is not None
                and outputs[cid]["ranking"] is not None
            ]
            false_permissions = sum(
                bool(row["policy_outputs"][policy]["permission"]) for row in invalid
            )
            unnecessary_refusals = sum(
                not bool(row["policy_outputs"][policy]["permission"]) for row in valid
            )
            family_result["policies"][policy] = {
                "false_permissions": false_permissions,
                "false_permission_denominator": len(invalid),
                "false_permission_rate": _ratio(false_permissions, len(invalid)),
                "unnecessary_refusals": unnecessary_refusals,
                "unnecessary_refusal_denominator": len(valid),
                "unnecessary_refusal_rate": _ratio(unnecessary_refusals, len(valid)),
                "valid_use_coverage": _ratio(
                    len(valid) - unnecessary_refusals, len(valid)
                ),
                "decision_interpretation_errors": sum(
                    outputs[cid]["decision"] != labels[cid]["expected_decision"]
                    for cid in decision_ids
                ),
                "decision_interpretation_denominator": len(decision_ids),
                "ranking_interpretation_errors": sum(
                    outputs[cid]["ranking"] != labels[cid]["expected_ranking"]
                    for cid in ranking_ids
                ),
                "ranking_interpretation_denominator": len(ranking_ids),
                "ranking_changes_vs_naive": sum(
                    outputs[row["public_case"]["case_id"]]["ranking"]
                    != row["policy_outputs"]["naive_aggregation"]["ranking"]
                    for row in ranking
                ),
                "ranking_change_denominator": len(ranking),
                "decision_changes_vs_naive": sum(
                    outputs[row["public_case"]["case_id"]]["decision"]
                    != row["policy_outputs"]["naive_aggregation"]["decision"]
                    for row in decisions
                ),
                "decision_change_denominator": len(decisions),
                "mean_rule_checks": _ratio(
                    sum(outputs[cid]["rule_checks"] for cid in ids), len(ids)
                ),
                "mean_public_metadata_bytes": _ratio(
                    sum(outputs[cid]["public_metadata_bytes"] for cid in ids), len(ids)
                ),
                "model_calls": sum(outputs[cid]["model_calls"] for cid in ids),
                "manual_reviews": 0,
            }
        family_result["ranking_estimand_cases"] = len(ranking)
        family_result["declared_decision_cases"] = len(decisions)
        summaries[family] = family_result
    return summaries


def recompute_gate_case_metrics(result: dict[str, Any]) -> dict[str, Any]:
    """Reduce the saved 23-case gate challenge fields that exist per case."""
    gate = result["gate_comparison"]
    cases = gate["cases"]
    summaries = {}
    for policy in sorted(gate["rules"]):
        invalid = [case for case in cases if not case["expected_permission"]]
        valid = [case for case in cases if case["expected_permission"]]
        false_permissions = sum(bool(case["permissions"][policy]) for case in invalid)
        unnecessary_refusals = sum(
            not bool(case["permissions"][policy]) for case in valid
        )
        interpretation_errors = sum(
            case["interpretations"][policy] != case["expected_target_relationship"]
            for case in cases
        )
        summaries[policy] = {
            "case_count": len(cases),
            "false_permissions": false_permissions,
            "invalid_case_denominator": len(invalid),
            "false_permission_rate": _ratio(false_permissions, len(invalid)),
            "unnecessary_refusals": unnecessary_refusals,
            "valid_case_denominator": len(valid),
            "unnecessary_refusal_rate": _ratio(unnecessary_refusals, len(valid)),
            "interpretation_errors": interpretation_errors,
            "interpretation_error_rate": _ratio(interpretation_errors, len(cases)),
            "ranking_and_decision_counts_recomputed_from_case_rows": False,
        }
        stored = gate["summary"][policy]
        for field in (
            "case_count",
            "false_permissions",
            "invalid_case_denominator",
            "unnecessary_refusals",
            "valid_case_denominator",
            "interpretation_errors",
        ):
            if summaries[policy][field] != stored[field]:
                raise ValueError(
                    f"gate challenge {policy}/{field} differs from case-level reduction"
                )
    return {
        "source": "23 saved case records in experimental-results.json",
        "by_policy": summaries,
        "not_recomputable_from_saved_case_rows": [
            "ranking_changed_cases",
            "decision_changed_records",
        ],
    }


def run(root: Path = ROOT, write: bool = True) -> dict[str, Any]:
    root = root.resolve()
    integrity_lock = verify_integrity_lock(root)
    raw = verify_bouleusis_manifest(root)
    data_audit = audit_public_data_strings(root)
    one_bug = recompute_selection_sweep(root)
    multibug = recompute_multibug(root)
    voi = recompute_voi(root)
    model = recompute_model_role(root)
    # Re-run deterministic repository experiments and compare against checked-in results.
    from isoprax.research_experiments import canonical_json, run_all_experiments
    from scripts.operation_policy_challenge import run as run_policy_challenge

    benchmark = run_all_experiments()
    if canonical_json(benchmark) != canonical_json(
        _json(root / "docs/research/experimental-results.json")
    ):
        raise ValueError("deterministic IsoPrax research results changed")
    gate_case_metrics = recompute_gate_case_metrics(benchmark)
    policy = run_policy_challenge()
    frozen_policy = _json(
        root / "docs/experiments/operation-policy-challenge-v2-results.json"
    )
    if policy != frozen_policy:
        raise ValueError("operation-policy challenge result no longer recomputes")
    policy_case_metrics = recompute_policy_case_metrics(frozen_policy)
    excluded_forecast_cases = ["FP02", "FP03", "FP05", "FP06"]
    forecast_case_operations = {
        row["public_case"]["case_id"]: row["public_case"]["operation"]
        for row in frozen_policy["per_case"]
    }
    if any(
        forecast_case_operations.get(case_id) != "forecast_pool"
        for case_id in excluded_forecast_cases
    ):
        raise ValueError(
            "predeclared forecast revision exclusions are missing or changed"
        )
    for family, computed in policy_case_metrics.items():
        stored = frozen_policy["candidate_metrics"][family]
        for field, value in computed.items():
            if field not in ("policies",):
                if not _same_tree(value, stored.get(field)):
                    raise ValueError(
                        f"operation-policy {family}/{field} differs from independent case reduction"
                    )
        for name, metrics in computed["policies"].items():
            for field, value in metrics.items():
                if not _same_tree(value, stored["policies"][name].get(field)):
                    raise ValueError(
                        f"operation-policy {family}/{name}/{field} differs from independent case reduction"
                    )
    claims = validate_claim_registry(root)
    rendered_tables = _render_main_tables(benchmark["benchmark_a"], gate_case_metrics)
    paper = (root / PAPER).read_text(encoding="utf-8")
    for table in _markdown_tables(rendered_tables):
        if table not in paper:
            raise ValueError(
                "main manuscript table does not match raw-result table renderer"
            )
    automated_review = {
        "status": "PASS",
        "review_type": "automated evidence and artifact checks",
        "independent_scientific_review": "not completed",
        "failures": [],
        "checks": [
            {"id": "frozen-integrity-lock", "status": "PASS"},
            {"id": "raw-source-hashes-and-record-counts", "status": "PASS"},
            {"id": "public-data-sensitive-string-scan", "status": "PASS"},
            {"id": "experiment-and-model-identities", "status": "PASS"},
            {"id": "development-heldout-split-checks", "status": "PASS"},
            {"id": "raw-result-recomputation", "status": "PASS"},
            {"id": "claim-and-numeric-coverage", "status": "PASS"},
            {"id": "generated-manuscript-tables", "status": "PASS"},
        ],
        "limitations": [
            "All new experiments use synthetic, authored records or a fixed finite challenge.",
            "Byte-identical model runs are one repeated execution on one frozen case set, not independent replication.",
            "The 23-case challenge was authored within the project and was not independently adjudicated.",
            "The 23-case saved rows omit the per-case ranking and decision outputs needed to reproduce those totals independently.",
            "A string scan cannot establish that all privacy, copyright, or third-party rights questions are resolved.",
            "Automated checks do not establish construct validity, operational value, or independent peer review.",
        ],
        "review_questions": [
            "Does an executable operation-sensitive declaration contract add a publishable contribution beyond measurement and construct-validity frameworks?",
            "Are the authored expected labels and valid semantic bridges correct under independent review?",
            "Would a simpler rule achieve comparable permission and coverage results on independently authored cases?",
            "Which data and generated model outputs should be deposited with a persistent identifier before submission?",
        ],
    }
    output = {
        "schema_version": 1,
        "protocol": "scripts/paper_integrity.py; raw-first recomputation with fixed sampling units and seeds",
        "evidence_status": "reproduced for the exact pinned synthetic records; not an independent scientific replication",
        "integrity_lock": integrity_lock,
        "raw_bouleusis_manifest": raw,
        "public_data_string_audit": data_audit,
        "one_bug_selection_sweep": one_bug,
        "multi_bug_retrieval": multibug,
        "acquisition_voi": voi,
        "model_role": model,
        "operation_policy_case_recompute": {
            "source": "frozen per_case outcomes; independently reduced",
            "evidence_class": frozen_policy["evidence_class"],
            "by_operation": policy_case_metrics,
            "positive_validity_exclusions": {
                "forecast_pool_case_ids": excluded_forecast_cases,
                "reason": "model-score and calibration target revisions differ; report descriptively only",
            },
        },
        "operation_gate_case_recompute": gate_case_metrics,
        "deterministic_isoprax_experiments": {
            "benchmark_a_match": True,
            "benchmark_a": benchmark["benchmark_a"],
            "operation_gate_and_policy_results_match": True,
        },
        "claim_registry_check": claims,
        "automated_review": automated_review,
        "unavailable_from_raw_records": [
            "field-level error rates for the operation-specific policy",
            "decision-change probability and abstention-resolution probability in the acquisition audit (records label these predictions not modeled)",
            "ranking-change and decision-change totals from independent reduction of the 23 saved operation-gate case rows",
            "independent replication on new cases, new tasks, new machines, or new model versions",
        ],
    }
    output_text = (
        json.dumps(output, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    )
    review_text = (
        json.dumps(automated_review, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    _write_or_check(root / OUTPUT, output_text, write)
    _write_or_check(root / TABLES, rendered_tables + "\n", write)
    _write_or_check(root / AUTOMATED_REVIEW, review_text, write)
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="verify without replacing the JSON summary",
    )
    args = parser.parse_args(argv)
    try:
        result = run(args.root, write=not args.check_only)
    except Exception as exc:
        failure_report = {
            "status": "FAIL",
            "review_type": "automated evidence and artifact checks",
            "independent_scientific_review": "not completed",
            "failures": [{"type": type(exc).__name__, "message": str(exc)}],
            "limitations": [
                "A failed automated check is not a scientific peer-review result."
            ],
            "review_questions": [],
        }
        path = args.root.resolve() / AUTOMATED_REVIEW
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(failure_report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"PAPER INTEGRITY FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(
        f"PAPER INTEGRITY PASS: {len(result['claim_registry_check']['registered_ids'])} claims; {result['one_bug_selection_sweep']['run_count']} one-bug raw runs; {result['multi_bug_retrieval']['run_count']} multi-bug raw runs; {result['acquisition_voi']['run_count']} VOI raw runs; model-role replay is byte-identical."
    )
    if not args.check_only:
        print(f"Wrote {OUTPUT}, {TABLES}, and {AUTOMATED_REVIEW}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
