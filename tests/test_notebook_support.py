from __future__ import annotations

from pathlib import Path

import pytest

from apps.evidence_workbench import datasets
from apps.evidence_workbench.datasets import ChartProjection, DatasetVerification
from notebooks import _support


def _make_repo_root(path: Path) -> Path:
    path.mkdir(parents=True)
    (path / "pyproject.toml").write_text(
        "[project]\nname='fixture'\n", encoding="utf-8"
    )
    (path / "isoprax").mkdir()
    return path


def test_required_dataset_path_fields_share_the_verifier_contract() -> None:
    assert datasets.required_dataset_path_fields("ai4i2020") == ("csv",)
    assert datasets.required_dataset_path_fields("cmapss") == ("train", "test", "rul")

    with pytest.raises(ValueError, match="unsupported dataset"):
        datasets.required_dataset_path_fields("unknown")


def test_repo_root_is_found_from_nested_and_configured_paths(tmp_path: Path) -> None:
    root = _make_repo_root(tmp_path / "checkout")
    nested = root / "notebooks" / "nested"
    nested.mkdir(parents=True)

    assert _support.find_repo_root(nested) == root
    assert _support.find_repo_root(tmp_path, configured=str(root)) == root


def test_repo_root_rejects_invalid_configured_directory(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="repository root"):
        _support.find_repo_root(tmp_path, configured=str(tmp_path))


def test_data_root_resolves_relative_and_absolute_paths_with_spaces(
    tmp_path: Path,
) -> None:
    root = _make_repo_root(tmp_path / "repo root")
    external = tmp_path / "corpus files"

    assert _support.resolve_data_root(root, "local data") == root / "local data"
    assert _support.resolve_data_root(root, str(external)) == external
    assert _support.resolve_data_root(root, None) == root / "data"


@pytest.mark.parametrize(
    ("dataset_id", "paths"),
    [
        ("ai4i2020", {"csv": "data/ai4i2020.csv"}),
        ("apachejit", {"csv": "data/apachejit.csv"}),
        ("cmapss", {"dataset": "FD001", "train": "train.txt"}),
        ("metropt3", {"csv": "data/metro.csv"}),
    ],
)
def test_unconfigured_dataset_files_stay_not_run_without_calling_verifier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    dataset_id: str,
    paths: dict[str, str],
) -> None:
    def unexpected_call(*_args: object, **_kwargs: object) -> DatasetVerification:
        pytest.fail("verifier must not run until every local input exists")

    monkeypatch.setattr(_support, "verify_local_dataset", unexpected_call)

    review = _support.review_dataset(dataset_id, paths, tmp_path)

    assert review.verification.status == "not_run"
    assert review.verification.report is None
    assert review.charts == ()
    assert review.verification.message


def test_verified_local_dataset_uses_shared_report_chart_projection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "file with spaces.csv"
    source.write_text("fixture", encoding="utf-8")
    report = DatasetVerification("ai4i2020", "verified", {"verified": True})
    chart = ChartProjection("Machine failure", "Label", "Rows", (("Yes", 1),))
    captured: dict[str, object] = {}

    def verify(dataset_id: str, paths: object, root: Path) -> DatasetVerification:
        captured["dataset_id"] = dataset_id
        captured["paths"] = paths
        captured["root"] = root
        return report

    monkeypatch.setattr(_support, "verify_local_dataset", verify)
    monkeypatch.setattr(_support, "project_dataset_charts", lambda _report: (chart,))

    review = _support.review_dataset("ai4i2020", {"csv": source}, tmp_path)

    assert review.verification is report
    assert review.charts == (chart,)
    assert captured["paths"] == {"csv": str(source.resolve())}
    assert captured["root"] == tmp_path


def test_failed_report_never_gets_success_charts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "ai4i.csv"
    source.write_text("fixture", encoding="utf-8")
    failed = DatasetVerification(
        "ai4i2020", "failed", {"verified": False, "errors": ["hash mismatch"]}
    )
    monkeypatch.setattr(_support, "verify_local_dataset", lambda *_args: failed)

    review = _support.review_dataset("ai4i2020", {"csv": source}, tmp_path)

    assert review.verification.status == "failed"
    assert review.charts == ()


def test_urls_are_unavailable_and_never_reach_verifier(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        _support,
        "verify_local_dataset",
        lambda *_args: pytest.fail("URL must not reach verifier"),
    )

    review = _support.review_dataset(
        "ai4i2020", {"csv": "https://example.test/ai4i.csv"}, tmp_path
    )

    assert review.verification.status == "unavailable"
    assert "URL" in (review.verification.message or "")
    assert review.charts == ()


def test_windows_drive_path_is_not_misclassified_as_a_url(tmp_path: Path) -> None:
    review = _support.review_dataset(
        "ai4i2020", {"csv": r"C:\research data\ai4i2020.csv"}, tmp_path
    )

    assert review.verification.status == "not_run"
    assert "URL" not in (review.verification.message or "")
