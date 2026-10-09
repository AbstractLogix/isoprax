from __future__ import annotations

import gzip
import hashlib
import json
import statistics

import pytest

from scripts import paper_integrity as integrity


def test_binary_metrics_skip_invalid_and_report_constant_auc() -> None:
    rows = [
        {"gold": False, "p": 0.5, "valid": True},
        {"gold": True, "p": 0.5, "valid": True},
        {"gold": True, "p": 0.99, "valid": False},
    ]

    result = integrity._binary_metrics(rows)

    assert result["n"] == 2
    assert result["positive_count"] == 1
    assert result["accuracy"] == 0.5
    assert result["auc"] == 0.5
    assert result["ece"] == 0.0


def test_auc_is_unavailable_when_one_class_is_present() -> None:
    assert integrity._auc([1, 1], [0.1, 0.9]) is None
    assert integrity._auc([0, 1], [0.4, 0.4]) == 0.5


def test_rank_ties_use_stable_item_id_order() -> None:
    rows = [
        {
            "query_id": "q1",
            "item_id": "A",
            "gold": False,
            "raw_score": 0.5,
            "valid": True,
        },
        {
            "query_id": "q1",
            "item_id": "B",
            "gold": True,
            "raw_score": 0.5,
            "valid": True,
        },
        {
            "query_id": "q1",
            "item_id": "C",
            "gold": False,
            "raw_score": 0.1,
            "valid": True,
        },
        {
            "query_id": "q1",
            "item_id": "D",
            "gold": False,
            "raw_score": 0.1,
            "valid": True,
        },
        {
            "query_id": "q1",
            "item_id": "E",
            "gold": False,
            "raw_score": 0.1,
            "valid": True,
        },
        {
            "query_id": "q1",
            "item_id": "F",
            "gold": False,
            "raw_score": 0.1,
            "valid": True,
        },
        {
            "query_id": "q1",
            "item_id": "G",
            "gold": False,
            "raw_score": 0.1,
            "valid": True,
        },
        {
            "query_id": "q1",
            "item_id": "H",
            "gold": False,
            "raw_score": 0.1,
            "valid": True,
        },
    ]

    result = integrity._rank_metrics(rows, "raw_score", seed=7)

    assert result["top_item_by_query"] == {"q1": "A"}
    assert result["mrr"] == 0.5


def test_bootstrap_resamples_whole_query_clusters() -> None:
    rows = [
        {"query_id": "q1", "value": 2},
        {"query_id": "q1", "value": 2},
        {"query_id": "q2", "value": 8},
    ]

    def cluster_mean(sample: list[dict[str, int | str]]) -> float:
        counts = {"q1": 0, "q2": 0}
        for row in sample:
            counts[str(row["query_id"])] += 1
        assert counts["q1"] % 2 == 0
        assert counts["q2"] in {0, 1, 2}
        return statistics.mean(int(row["value"]) for row in sample)

    interval = integrity._bootstrap(rows, cluster_mean, seed=19, reps=50)
    repeated = integrity._bootstrap(rows, cluster_mean, seed=19, reps=50)
    assert interval is not None
    assert interval == repeated


def test_calibration_fit_uses_only_development_rows() -> None:
    development = [
        {
            "case_id": "dev-a",
            "split": "development",
            "raw_score": 0.0,
            "gold": False,
            "valid": True,
        },
        {
            "case_id": "dev-b",
            "split": "development",
            "raw_score": 1.0,
            "gold": True,
            "valid": True,
        },
    ]
    heldout = [
        {
            "case_id": "test-a",
            "split": "heldout",
            "raw_score": 0.25,
            "gold": True,
            "valid": True,
        },
        {
            "case_id": "test-b",
            "split": "heldout",
            "raw_score": 0.75,
            "gold": False,
            "valid": True,
        },
    ]
    rows = development + heldout
    assert integrity._assert_disjoint_splits(rows, (), "case_id") == 2
    fit_rows = [row for row in rows if row["split"] == "development"]
    first = integrity._fit_platt(fit_rows)

    heldout[0]["gold"] = False
    heldout[1]["gold"] = True
    second = integrity._fit_platt(
        [row for row in rows if row["split"] == "development"]
    )

    assert first.intercept_.tolist() == second.intercept_.tolist()
    assert first.coef_.tolist() == second.coef_.tolist()


def test_split_validation_rejects_case_leakage() -> None:
    rows = [
        {"domain": "safety", "case_id": "q1", "split": "development"},
        {"domain": "safety", "case_id": "q1", "split": "heldout"},
    ]
    with pytest.raises(ValueError, match="development/held-out leakage"):
        integrity._assert_disjoint_splits(rows, ("domain",), "case_id")


@pytest.mark.parametrize(
    ("model", "score_type", "score", "label", "message"),
    [
        (
            "qwen",
            "self_reported_relevance_probability",
            1.1,
            True,
            r"outside \[0, 1\]",
        ),
        ("embedding", "cosine_similarity", 1.5, None, r"outside \[-1, 1\]"),
        (
            "guardian",
            "binary_critic_judgment",
            0.5,
            True,
            "non-binary score",
        ),
    ],
)
def test_score_semantics_reject_probability_reinterpretation(
    model: str,
    score_type: str,
    score: float,
    label: bool | None,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        integrity._validate_relevance_score(
            {
                "model": model,
                "score_type": score_type,
                "raw_score": score,
                "label": label,
                "valid": True,
            }
        )


def test_numeric_result_without_claim_id_fails_closed() -> None:
    with pytest.raises(ValueError, match="numeric paper claims lack a claim ID"):
        integrity._validate_numeric_coverage("The sample has n=12 cases.", {"C1"})

    integrity._validate_numeric_coverage("The sample has n=12 cases. [[C1]]", {"C1"})


def test_bouleusis_manifest_detects_changed_package_bytes(tmp_path) -> None:
    data = b'{"record_type":"metadata"}\n{"record_type":"run"}\n'
    compressed = gzip.compress(data, mtime=0)
    relative = "docs/experiments/bouleusis-2026-10-08-raw/sample.jsonl.gz"
    artifact = tmp_path / relative
    artifact.parent.mkdir(parents=True)
    artifact.write_bytes(compressed)
    entry = {
        "package_path": relative,
        "package_sha256": hashlib.sha256(compressed).hexdigest(),
        "source_sha256": hashlib.sha256(data).hexdigest(),
        "source_bytes": len(data),
        "source_lines_including_header": 2,
        "source_run_or_record_count": 1,
        "source_commit": "pinned",
        "source_blob_oid": "blob",
        "source_path": "source.jsonl",
    }
    authorization_record = "docs/experiments/bouleusis-2026-10-08-raw/README.md"
    (tmp_path / authorization_record).write_text(
        "owner authorization", encoding="utf-8"
    )
    manifest = {
        "files": [entry],
        "source_license": "NOASSERTION",
        "source_license_context": "The pinned source repository did not assert a license. The repository owner separately authorized public release.",
        "public_release": {
            "data_license": "CC-BY-4.0",
            "data_license_url": "https://creativecommons.org/licenses/by/4.0/",
            "authorization_date": "2026-10-09",
            "authorization_record": authorization_record,
            "authorization_scope": "The repository owner authorized selected original research data.",
            "included_artifacts": [relative],
            "excluded_materials": ["Bouleusis source code", "third-party materials"],
            "license_scope_note": "CC BY 4.0 applies to selected original research data files.",
        },
    }
    manifest_path = tmp_path / integrity.RAW / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    assert (
        integrity.verify_bouleusis_manifest(tmp_path)["files"][0][
            "records_after_header"
        ]
        == 1
    )
    entry["source_run_or_record_count"] = 2
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="raw Bouleusis artifact integrity failed"):
        integrity.verify_bouleusis_manifest(tmp_path)


def _write_test_integrity_lock(root) -> None:
    files = {
        str(integrity.PAPER): "synthetic metric 0.8 [[C1]]\n",
        str(integrity.CLAIMS): '{"mapping":"C1 to the paper"}\n',
        str(integrity.MODEL_PREREG): '{"model":"pinned"}\n',
        "docs/evidence.json": '{"identity":"frozen"}\n',
    }
    artifacts = []
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        artifacts.append(
            {
                "path": relative,
                "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            }
        )
    lock_path = root / integrity.LOCK
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(json.dumps({"artifacts": artifacts}), encoding="utf-8")


def test_integrity_lock_detects_paper_and_artifact_mutations(tmp_path) -> None:
    _write_test_integrity_lock(tmp_path)
    assert integrity.verify_integrity_lock(tmp_path)["status"] == "PASS"

    paper_path = tmp_path / integrity.PAPER
    paper_path.write_text("synthetic metric 0.9 [[C1]]\n", encoding="utf-8")
    with pytest.raises(ValueError, match="digest mismatch"):
        integrity.verify_integrity_lock(tmp_path)

    _write_test_integrity_lock(tmp_path)
    lock_path = tmp_path / integrity.LOCK
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    next(row for row in lock["artifacts"] if row["path"] == "docs/evidence.json")[
        "sha256"
    ] = "0" * 64
    lock_path.write_text(json.dumps(lock), encoding="utf-8")
    with pytest.raises(ValueError, match="digest mismatch: docs/evidence.json"):
        integrity.verify_integrity_lock(tmp_path)

    _write_test_integrity_lock(tmp_path)
    evidence_path = tmp_path / "docs/evidence.json"
    evidence_path.write_text('{"identity":"changed"}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="digest mismatch: docs/evidence.json"):
        integrity.verify_integrity_lock(tmp_path)


def test_claim_registry_rejects_unmapped_paper_claim(tmp_path) -> None:
    paper_path = tmp_path / integrity.PAPER
    paper_path.parent.mkdir(parents=True, exist_ok=True)
    paper_path.write_text("The measured rate is 0.8. [[C1]]\n", encoding="utf-8")
    claim = {
        "id": "C1",
        "wording": "A synthetic measured rate.",
        "category": "synthetic-finding",
        "assumptions": [],
        "source_repository": "local",
        "source_commit": "test",
        "artifacts": [],
        "protocol": {},
        "result_or_counterexample": "fixture result",
        "uncertainty": "none",
        "threats_to_validity": "synthetic fixture",
        "qualification": "descriptive-only",
        "manuscript_section": ["main manuscript: Results"],
    }
    claim_path = tmp_path / integrity.CLAIMS
    claim_path.parent.mkdir(parents=True, exist_ok=True)
    claim_path.write_text(json.dumps({"claims": [claim]}), encoding="utf-8")
    assert integrity.validate_claim_registry(tmp_path)["paper_claim_tags"] == ["C1"]

    claim["manuscript_section"] = ["companion only"]
    claim_path.write_text(json.dumps({"claims": [claim]}), encoding="utf-8")
    with pytest.raises(ValueError, match="not mapped to main manuscript"):
        integrity.validate_claim_registry(tmp_path)


def test_model_role_string_audit_rebuilds_compressed_runs(tmp_path) -> None:
    raw = json.dumps({"raw_responses": {"answer": "synthetic"}}).encode()
    compressed = gzip.compress(raw, mtime=0)
    run_entry = {
        "parts": [
            {
                "path": "docs/experiments/model-role-v2.3-run-1.json.gz.part-00",
                "sha256": hashlib.sha256(compressed).hexdigest(),
                "bytes": len(compressed),
            }
        ],
        "gzip_sha256": hashlib.sha256(compressed).hexdigest(),
        "gzip_bytes": len(compressed),
        "uncompressed_path": "docs/experiments/model-role-v2.3-run-1.json",
        "uncompressed_sha256": hashlib.sha256(raw).hexdigest(),
        "uncompressed_bytes": len(raw),
    }
    second_entry = json.loads(json.dumps(run_entry))
    second_entry["uncompressed_path"] = "docs/experiments/model-role-v2.3-run-2.json"
    second_entry["parts"][0]["path"] = (
        "docs/experiments/model-role-v2.3-run-2.json.gz.part-00"
    )
    for entry in (run_entry, second_entry):
        part_path = tmp_path / entry["parts"][0]["path"]
        part_path.parent.mkdir(parents=True, exist_ok=True)
        part_path.write_bytes(compressed)
    model_manifest_path = tmp_path / integrity.MODEL_MANIFEST
    model_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    model_manifest_path.write_text(
        json.dumps({"runs": {"1": run_entry, "2": second_entry}}),
        encoding="utf-8",
    )

    result = integrity.audit_public_data_strings(tmp_path)

    assert result["status"] == "PASS"
    assert len(result["files"]) == 2
    assert [row["path"] for row in result["files"]] == [
        "docs/experiments/model-role-v2.3-run-1.json",
        "docs/experiments/model-role-v2.3-run-2.json",
    ]


def test_operation_policy_metrics_are_reduced_from_case_records() -> None:
    rows = [
        {
            "evaluator_outcome": {
                "expected_permission": False,
                "expected_decision": False,
                "expected_ranking": None,
            },
            "public_case": {
                "case_id": "invalid",
                "operation": "forecast_pool",
                "context": {"decision_threshold": 0.5},
            },
            "policy_outputs": {
                "naive_aggregation": {
                    "permission": True,
                    "decision": True,
                    "ranking": None,
                    "rule_checks": 0,
                    "public_metadata_bytes": 0,
                    "model_calls": 0,
                },
                "operation_specific": {
                    "permission": False,
                    "decision": False,
                    "ranking": None,
                    "rule_checks": 2,
                    "public_metadata_bytes": 5,
                    "model_calls": 0,
                },
            },
        },
        {
            "evaluator_outcome": {
                "expected_permission": True,
                "expected_decision": True,
                "expected_ranking": "A",
            },
            "public_case": {
                "case_id": "valid",
                "operation": "forecast_pool",
                "context": {"decision_threshold": 0.5, "ranking_estimand": "top-1"},
            },
            "policy_outputs": {
                "naive_aggregation": {
                    "permission": True,
                    "decision": False,
                    "ranking": "B",
                    "rule_checks": 0,
                    "public_metadata_bytes": 0,
                    "model_calls": 0,
                },
                "operation_specific": {
                    "permission": True,
                    "decision": True,
                    "ranking": "A",
                    "rule_checks": 2,
                    "public_metadata_bytes": 5,
                    "model_calls": 0,
                },
            },
        },
    ]

    result = integrity.recompute_policy_case_metrics({"per_case": rows})[
        "forecast_pool"
    ]
    operation = result["policies"]["operation_specific"]

    assert result["n_cases"] == 2
    assert operation["false_permissions"] == 0
    assert operation["unnecessary_refusals"] == 0
    assert operation["decision_interpretation_errors"] == 0
    assert operation["ranking_interpretation_errors"] == 0
    assert operation["ranking_changes_vs_naive"] == 1
    assert operation["decision_changes_vs_naive"] == 2


def test_operation_policy_reducer_fails_when_a_required_metric_is_missing() -> None:
    row = {
        "evaluator_outcome": {"expected_decision": None, "expected_ranking": None},
        "public_case": {
            "case_id": "case-1",
            "operation": "forecast_pool",
            "context": {},
        },
        "policy_outputs": {
            "naive_aggregation": {
                "permission": True,
                "decision": None,
                "ranking": None,
                "rule_checks": 0,
                "public_metadata_bytes": 0,
                "model_calls": 0,
            }
        },
    }

    with pytest.raises(KeyError, match="expected_permission"):
        integrity.recompute_policy_case_metrics({"per_case": [row]})
