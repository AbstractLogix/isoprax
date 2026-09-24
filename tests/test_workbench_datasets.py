from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from apps.evidence_workbench.datasets import (
    DatasetVerification,
    load_example_catalog,
    not_run_verification,
    project_dataset_charts,
    verify_local_dataset,
)


def _write_manifests(root: Path) -> None:
    manifests = {
        "ai4i2020": {
            "dataset_id": "ai4i2020",
            "source": {"retrieval_reference": "https://example.org/ai4i"},
            "claim_boundary": "synthetic structural evidence only",
        },
        "apachejit": {
            "dataset_id": "apachejit",
            "canonical_source": "https://example.org/apachejit",
            "claim_boundary": "repository-derived labels only",
        },
        "cmapss": {
            "dataset_id": "cmapss",
            "canonical_source": "https://example.org/cmapss",
            "claim_boundary": "simulated RUL evidence only",
        },
        "metropt3": {
            "dataset_id": "metropt3",
            "canonical_source": "https://example.org/metropt3",
            "claim_boundary": "externally anchored evidence only",
        },
    }
    for dataset_id, manifest in manifests.items():
        directory = root / "examples" / dataset_id
        directory.mkdir(parents=True)
        (directory / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_example_catalog_uses_each_manifest_and_preserves_distinct_outcomes(
    tmp_path: Path,
) -> None:
    _write_manifests(tmp_path)

    examples = load_example_catalog(tmp_path)

    assert [example.dataset_id for example in examples] == [
        "ai4i2020",
        "apachejit",
        "cmapss",
        "metropt3",
    ]
    by_id = {example.dataset_id: example for example in examples}
    assert by_id["ai4i2020"].source_reference == "https://example.org/ai4i"
    assert by_id["ai4i2020"].claim_boundary == "synthetic structural evidence only"
    assert "current process cycle" in by_id["ai4i2020"].outcome_summary
    assert "runtime failure" in by_id["apachejit"].outcome_summary
    assert "simulated" in by_id["cmapss"].outcome_summary.lower()
    assert "censored" in by_id["metropt3"].outcome_summary


def test_example_catalog_rejects_invalid_manifest_instead_of_inventing_metadata(
    tmp_path: Path,
) -> None:
    _write_manifests(tmp_path)
    (tmp_path / "examples/metropt3/manifest.json").write_text(
        "not json", encoding="utf-8"
    )

    with pytest.raises(ValueError, match="metropt3.*manifest"):
        load_example_catalog(tmp_path)


@pytest.mark.parametrize(
    ("dataset_id", "paths", "verifier_name"),
    (
        ("ai4i2020", {"csv": "ai4i.csv"}, "verify_ai4i2020_csv"),
        ("apachejit", {"csv": "jit.csv"}, "verify_apachejit_csv"),
        (
            "cmapss",
            {
                "dataset": "FD001",
                "train": "train.txt",
                "test": "test.txt",
                "rul": "rul.txt",
            },
            "verify_cmapss",
        ),
        (
            "metropt3",
            {"csv": "metro.csv", "intervals": "intervals.json"},
            "verify_metropt3_csv",
        ),
    ),
)
def test_local_verification_dispatches_existing_verifier_and_preserves_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    dataset_id: str,
    paths: dict[str, str],
    verifier_name: str,
) -> None:
    from apps.evidence_workbench import datasets

    if dataset_id == "metropt3":
        (tmp_path / "intervals.json").write_text("[]", encoding="utf-8")
    payload = {"verified": True, "errors": [], "warnings": ["review cadence"]}
    report = SimpleNamespace(
        verified=True,
        errors=(),
        warnings=("review cadence",),
        to_dict=lambda: payload,
    )
    captured: dict[str, Any] = {}

    def fake_verifier(*args: Any) -> SimpleNamespace:
        captured["args"] = args
        return report

    monkeypatch.setattr(datasets, verifier_name, fake_verifier)

    result = verify_local_dataset(dataset_id, paths, tmp_path)

    assert result.status == "verified_with_warnings"
    assert result.report is payload
    assert result.message is None
    expected_args = {
        "ai4i2020": (tmp_path / "ai4i.csv",),
        "apachejit": (tmp_path / "jit.csv",),
        "cmapss": (
            "FD001",
            tmp_path / "train.txt",
            tmp_path / "test.txt",
            tmp_path / "rul.txt",
        ),
        "metropt3": (tmp_path / "metro.csv", ()),
    }
    assert captured["args"] == expected_args[dataset_id]


def test_missing_inputs_are_unavailable_without_zero_or_verified_report(
    tmp_path: Path,
) -> None:
    result = verify_local_dataset("cmapss", {"dataset": "FD001"}, tmp_path)

    assert result.status == "unavailable"
    assert result.report is None
    assert "train" in (result.message or "")


def test_not_run_and_failed_states_do_not_invent_success_or_zero_counts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from apps.evidence_workbench import datasets

    not_run = not_run_verification("ai4i2020")
    assert not_run.status == "not_run"
    assert not_run.report is None

    payload = {"verified": False, "errors": ["hash mismatch"], "warnings": []}
    report = SimpleNamespace(
        verified=False,
        errors=("hash mismatch",),
        warnings=(),
        to_dict=lambda: payload,
    )
    monkeypatch.setattr(datasets, "verify_ai4i2020_csv", lambda _path: report)

    failed = verify_local_dataset("ai4i2020", {"csv": "data.csv"}, tmp_path)

    assert failed.status == "failed"
    assert failed.report is payload
    assert failed.report["errors"] == ["hash mismatch"]


def test_url_path_is_rejected_before_verifier_is_called(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from apps.evidence_workbench import datasets

    def unexpected_call(*args: object) -> None:
        pytest.fail("URL paths must not reach a dataset verifier")

    monkeypatch.setattr(datasets, "verify_ai4i2020_csv", unexpected_call)

    result = verify_local_dataset(
        "ai4i2020", {"csv": "https://example.org/data.csv"}, tmp_path
    )

    assert result.status == "unavailable"
    assert "local file" in (result.message or "")


def test_windows_drive_path_is_not_rejected_as_a_url(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from apps.evidence_workbench import datasets

    payload = {"verified": True, "errors": [], "warnings": []}
    report = SimpleNamespace(
        verified=True,
        errors=(),
        warnings=(),
        to_dict=lambda: payload,
    )
    monkeypatch.setattr(datasets, "verify_ai4i2020_csv", lambda _path: report)

    result = verify_local_dataset(
        "ai4i2020", {"csv": r"C:\research data\ai4i2020.csv"}, tmp_path
    )

    assert result.status == "verified"


def _verified(dataset_id: str, **fields: object) -> DatasetVerification:
    return DatasetVerification(dataset_id, "verified", {"verified": True, **fields})


def test_ai4i_charts_keep_composite_and_overlapping_modes_distinct() -> None:
    charts = project_dataset_charts(
        _verified(
            "ai4i2020",
            row_count=100,
            machine_failure_count=12,
            mode_counts={"TWF": 4, "HDF": 3},
            multi_mode_row_count=2,
            failure_without_mode_count=1,
            mode_without_failure_count=2,
            composite_mismatch_count=3,
        )
    )

    assert len(charts) == 2
    assert charts[0].points == (
        ("Machine failure", 12),
        ("TWF", 4),
        ("HDF", 3),
        ("Rows with multiple modes", 2),
    )
    assert charts[1].points == (
        ("Failure without mode", 1),
        ("Mode without failure", 2),
        ("Total mismatches", 3),
    )
    assert "overlap" in charts[0].title.lower()


def test_apachejit_charts_keep_zero_yield_projects_and_volume_visible() -> None:
    charts = project_dataset_charts(
        _verified(
            "apachejit",
            row_count=6,
            project_count=2,
            buggy_count=2,
            project_counts={"apache/zero": 2, "apache/positive": 4},
            project_buggy_counts={"apache/positive": 2},
            project_positive_yield={"apache/zero": 0.0, "apache/positive": 0.5},
        )
    )

    assert charts[0].points == (("apache/positive", 4), ("apache/zero", 2))
    assert charts[1].points == (("apache/positive", 50.0), ("apache/zero", 0.0))
    assert "observed" in charts[1].title.lower()


def test_cmapss_charts_show_split_counts_and_test_rul_alignment() -> None:
    charts = project_dataset_charts(
        _verified(
            "cmapss",
            dataset="FD001",
            train_rows=1000,
            train_units=100,
            test_rows=300,
            test_units=100,
            rul_count=100,
        )
    )

    assert charts[0].points == (("Train", 1000), ("Held-out test", 300))
    assert charts[1].points == (
        ("Train units", 100),
        ("Held-out test units", 100),
        ("RUL values", 100),
    )


def test_metropt3_charts_show_anchor_coverage_and_observed_cadence() -> None:
    charts = project_dataset_charts(
        _verified(
            "metropt3",
            row_count=20,
            unique_timestamps=20,
            interval_coverage={"F1": 3, "F2": 0},
            gap_counts_seconds={10.0: 16, 30.0: 3},
        )
    )

    assert charts[0].points == (("F1", 3), ("F2", 0))
    assert charts[1].points == (("10 s", 16), ("30 s", 3))


def test_metropt3_single_observation_has_no_invented_cadence_point() -> None:
    charts = project_dataset_charts(
        _verified(
            "metropt3",
            row_count=1,
            unique_timestamps=1,
            interval_coverage={"F1": 1},
            gap_counts_seconds={},
        )
    )

    assert len(charts) == 1
    assert charts[0].points == (("F1", 1),)


@pytest.mark.parametrize("status", ("failed", "unavailable", "not_run"))
def test_charts_are_withheld_without_verified_reports(status: str) -> None:
    verification = DatasetVerification(
        "ai4i2020", status, {"verified": True, "row_count": 100}
    )  # type: ignore[arg-type]

    assert project_dataset_charts(verification) == ()


def test_internally_inconsistent_success_report_does_not_produce_charts() -> None:
    verification = _verified(
        "cmapss",
        dataset="FD001",
        train_rows=100,
        train_units=10,
        test_rows=20,
        test_units=9,
        rul_count=10,
    )

    assert project_dataset_charts(verification) == ()
