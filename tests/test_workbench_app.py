from __future__ import annotations

from pathlib import Path

import pytest

from apps.evidence_workbench.datasets import DatasetVerification
from apps.evidence_workbench.repository import (
    CoverageReview,
    GraphifySnapshot,
    GraphLink,
    GraphNeighborhood,
    GraphNode,
    LocalActionResult,
)

AppTest = pytest.importorskip(
    "streamlit.testing.v1", reason="the workbench UI is an optional extra"
).AppTest

APP_PATH = Path(__file__).resolve().parents[1] / "apps/evidence_workbench/app.py"


@pytest.mark.parametrize(
    ("view", "dataset_id", "report"),
    (
        (
            "AI4I 2020",
            "ai4i2020",
            {
                "row_count": 10,
                "machine_failure_count": 2,
                "mode_counts": {"TWF": 1, "HDF": 1},
                "multi_mode_row_count": 0,
                "failure_without_mode_count": 0,
                "mode_without_failure_count": 0,
                "composite_mismatch_count": 0,
            },
        ),
        (
            "ApacheJIT",
            "apachejit",
            {
                "row_count": 3,
                "project_count": 2,
                "buggy_count": 1,
                "project_counts": {"p/a": 2, "p/b": 1},
                "project_buggy_counts": {"p/a": 1},
                "project_positive_yield": {"p/a": 0.5, "p/b": 0.0},
            },
        ),
        (
            "NASA C-MAPSS",
            "cmapss",
            {
                "dataset": "FD001",
                "train_rows": 10,
                "train_units": 2,
                "test_rows": 4,
                "test_units": 2,
                "rul_count": 2,
            },
        ),
        (
            "MetroPT-3",
            "metropt3",
            {
                "row_count": 10,
                "unique_timestamps": 10,
                "interval_coverage": {"F1": 2, "F2": 0},
                "gap_counts_seconds": {10.0: 8, 30.0: 1},
            },
        ),
    ),
)
def test_verified_dataset_pages_render_report_charts_without_ui_errors(
    view: str, dataset_id: str, report: dict[str, object]
) -> None:
    app = AppTest.from_file(str(APP_PATH), default_timeout=20).run()
    app.session_state[f"workbench_verification_{dataset_id}"] = {
        "dataset_id": dataset_id,
        "status": "verified_with_warnings",
        "report": {
            "verified": True,
            "errors": [],
            "warnings": ["review cadence"],
            **report,
        },
        "message": None,
    }

    app.radio[0].set_value(view).run()

    assert not app.exception
    assert any(item.value == "Verified report charts" for item in app.subheader)
    assert any("review cadence" in item.value for item in app.warning)


def test_failed_dataset_report_stays_visible_without_charts() -> None:
    app = AppTest.from_file(str(APP_PATH), default_timeout=20).run()
    app.session_state["workbench_verification_ai4i2020"] = {
        "dataset_id": "ai4i2020",
        "status": "failed",
        "report": {"verified": False, "errors": ["hash mismatch"], "warnings": []},
        "message": None,
    }

    app.radio[0].set_value("AI4I 2020").run()

    assert not app.exception
    assert any("hash mismatch" in item.value for item in app.error)
    assert not any(item.value == "Verified report charts" for item in app.subheader)


def test_missing_ai4i_path_is_unavailable_without_ui_error() -> None:
    app = AppTest.from_file(str(APP_PATH), default_timeout=20).run()
    app.radio[0].set_value("AI4I 2020").run()
    next(
        button for button in app.button if button.label == "Verify local files"
    ).click().run()

    assert not app.exception
    assert any(
        "required local path for csv is missing" in item.value for item in app.warning
    )


@pytest.mark.parametrize("status", ("verified_with_warnings", "failed"))
@pytest.mark.parametrize(
    ("view", "dataset_id", "fields", "expected_paths"),
    (
        (
            "AI4I 2020",
            "ai4i2020",
            (("AI4I CSV path", "input.csv"),),
            {"csv": "input.csv"},
        ),
        (
            "ApacheJIT",
            "apachejit",
            (("ApacheJIT CSV path", "commits.csv"),),
            {"csv": "commits.csv"},
        ),
        (
            "NASA C-MAPSS",
            "cmapss",
            (
                ("Train file path", "train.txt"),
                ("Test file path", "test.txt"),
                ("RUL file path", "rul.txt"),
            ),
            {
                "dataset": "FD001",
                "train": "train.txt",
                "test": "test.txt",
                "rul": "rul.txt",
            },
        ),
        (
            "MetroPT-3",
            "metropt3",
            (("MetroPT-3 CSV path", "sensor.csv"),),
            {
                "csv": "sensor.csv",
                "intervals": "examples/metropt3/failure_intervals.json",
            },
        ),
    ),
)
def test_dataset_forms_forward_paths_and_display_verifier_diagnostics(
    monkeypatch: pytest.MonkeyPatch,
    status: str,
    view: str,
    dataset_id: str,
    fields: tuple[tuple[str, str], ...],
    expected_paths: dict[str, str],
) -> None:
    from apps.evidence_workbench import datasets

    calls: list[tuple[str, dict[str, str]]] = []

    def fake_verify(
        actual_dataset_id: str, paths: dict[str, str], _root: Path
    ) -> DatasetVerification:
        calls.append((actual_dataset_id, paths))
        failed = status == "failed"
        report = {
            "verified": not failed,
            "errors": ["fixture verifier error"] if failed else [],
            "warnings": [] if failed else ["fixture verifier warning"],
        }
        return DatasetVerification(actual_dataset_id, status, report)  # type: ignore[arg-type]

    monkeypatch.setattr(datasets, "verify_local_dataset", fake_verify)
    app = AppTest.from_file(str(APP_PATH), default_timeout=20).run()
    app.radio[0].set_value(view).run()
    for label, value in fields:
        next(item for item in app.text_input if item.label == label).set_value(
            value
        ).run()
    next(
        button for button in app.button if button.label == "Verify local files"
    ).click().run()

    assert not app.exception
    assert calls == [(dataset_id, expected_paths)]
    if status == "failed":
        assert any("fixture verifier error" in item.value for item in app.error)
        assert not any(item.value == "Verified report charts" for item in app.subheader)
    else:
        assert any("fixture verifier warning" in item.value for item in app.warning)
        assert any("Verified with diagnostics" in item.value for item in app.warning)


@pytest.mark.parametrize("status", ("passed", "failed"))
def test_repository_gate_runs_only_after_click_and_reports_its_result(
    monkeypatch: pytest.MonkeyPatch, status: str
) -> None:
    from apps.evidence_workbench import repository_view

    calls: list[str] = []

    def fake_action(action: str, _root: Path) -> LocalActionResult:
        calls.append(action)
        return LocalActionResult(
            "coverage",
            status,  # type: ignore[arg-type]
            "2026-01-01T00:00:00+00:00",
            "2026-01-01T00:01:00+00:00",
            0 if status == "passed" else 1,
            "gate output",
        )

    monkeypatch.setattr(repository_view, "run_local_action", fake_action)
    monkeypatch.setattr(
        repository_view,
        "read_coverage_review",
        lambda _root, _action: CoverageReview(
            "current" if status == "passed" else "stale",
            "2026-01-01T00:00:30",
            (("isoprax/example", 91.0),),
            (),
        ),
    )
    monkeypatch.setattr(repository_view, "read_git_state", lambda _root: (None, None))
    monkeypatch.setattr(
        repository_view,
        "read_graphify_snapshot",
        lambda *_args: GraphifySnapshot("missing", None, 0, 0, (), (), "missing"),
    )
    app = AppTest.from_file(str(APP_PATH), default_timeout=20).run()
    app.radio[0].set_value("Repository Review").run()
    assert calls == []

    next(
        button for button in app.button if button.label == "Run coverage gate"
    ).click().run()

    assert not app.exception
    assert calls == ["coverage"]
    expected = (
        "passed in this session"
        if status == "passed"
        else "latest coverage gate failed"
    )
    assert any(expected in item.value for item in (*app.success, *app.error))
    assert any("below the 95% gate metric" in item.value for item in app.warning)


def test_graphify_search_renders_only_the_bounded_neighborhood(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from apps.evidence_workbench import repository_view

    center = GraphNode("center", "CoreVerifier", "isoprax/verify.py", "L10")
    neighbor = GraphNode("neighbor", "Report", "isoprax/report.py", "L20")
    snapshot = GraphifySnapshot(
        "potentially_stale",
        "old-commit",
        2,
        1,
        (center, neighbor),
        (GraphLink("center", "neighbor", "calls"),),
    )
    monkeypatch.setattr(repository_view, "read_git_state", lambda _root: ("new", True))
    monkeypatch.setattr(
        repository_view, "read_graphify_snapshot", lambda *_args: snapshot
    )
    monkeypatch.setattr(
        repository_view,
        "search_graphify_nodes",
        lambda _snapshot, query: (center,) if "core" in query.casefold() else (),
    )
    monkeypatch.setattr(
        repository_view,
        "graphify_neighborhood",
        lambda *_args: GraphNeighborhood("digraph G { a -> b; }", 2, 1, False),
    )
    app = AppTest.from_file(str(APP_PATH), default_timeout=20).run()
    app.radio[0].set_value("Repository Review").run()
    app.text_input[0].set_value("core verifier").run()

    assert not app.exception
    assert any("may be stale" in item.value for item in app.warning)
    assert app.selectbox
