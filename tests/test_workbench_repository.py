from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

import pytest

from apps.evidence_workbench.repository import (
    MAX_ACTION_OUTPUT_CHARS,
    MAX_COVERAGE_BYTES,
    MAX_GRAPH_BYTES,
    MAX_NEIGHBORHOOD_LINKS,
    MAX_NEIGHBORHOOD_NODES,
    GraphifySnapshot,
    GraphLink,
    GraphNode,
    LocalActionResult,
    graphify_neighborhood,
    read_coverage_review,
    read_graphify_snapshot,
    run_local_action,
    search_graphify_nodes,
)


def test_demo_action_uses_fixed_local_command_and_captures_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args[0], 0, "synthetic demo\n", "")

    monkeypatch.setattr("apps.evidence_workbench.repository.subprocess.run", fake_run)

    result = run_local_action("demo", tmp_path)

    assert result.status == "passed"
    assert result.return_code == 0
    assert result.output == "synthetic demo\n"
    args, kwargs = calls[0]
    assert args == (("uv", "run", "python", "examples/demo_cross_family.py"),)
    assert kwargs["cwd"] == tmp_path.resolve()
    assert kwargs["shell"] is False
    assert kwargs["capture_output"] is True
    assert kwargs["text"] is True
    assert kwargs["timeout"] == 120


def test_coverage_action_uses_only_repository_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    observed: dict[str, object] = {}

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        observed.update(command=args[0], **kwargs)
        return subprocess.CompletedProcess(args[0], 1, "test output", "gate failed")

    monkeypatch.setattr("apps.evidence_workbench.repository.subprocess.run", fake_run)

    result = run_local_action("coverage", tmp_path)

    assert result.status == "failed"
    assert result.return_code == 1
    assert "test output" in result.output
    assert "gate failed" in result.output
    assert observed["command"] == ("make", "coverage")
    assert observed["timeout"] == 600
    assert observed["shell"] is False


def test_unknown_action_is_rejected_without_running_a_command(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def unexpected_run(*args: object, **kwargs: object) -> None:
        pytest.fail("an unknown action must never reach subprocess.run")

    monkeypatch.setattr(
        "apps.evidence_workbench.repository.subprocess.run", unexpected_run
    )

    with pytest.raises(ValueError, match="unsupported local action"):
        run_local_action("make all", tmp_path)


def test_timeout_is_reported_with_partial_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fake_run(*args: object, **kwargs: object) -> None:
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"], output=b"partial")

    monkeypatch.setattr("apps.evidence_workbench.repository.subprocess.run", fake_run)

    result = run_local_action("coverage", tmp_path)

    assert result.status == "timed_out"
    assert result.return_code is None
    assert "partial" in result.output


def test_missing_command_is_reported_as_unavailable(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fake_run(*args: object, **kwargs: object) -> None:
        raise FileNotFoundError("make")

    monkeypatch.setattr("apps.evidence_workbench.repository.subprocess.run", fake_run)

    result = run_local_action("coverage", tmp_path)

    assert result.status == "unavailable"
    assert result.return_code is None
    assert "make" in result.output


def test_action_output_is_truncated_to_bounded_tail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    output = "x" * (MAX_ACTION_OUTPUT_CHARS + 100)

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args[0], 0, output, "")

    monkeypatch.setattr("apps.evidence_workbench.repository.subprocess.run", fake_run)

    result = run_local_action("demo", tmp_path)

    assert len(result.output) == MAX_ACTION_OUTPUT_CHARS
    assert result.output.endswith("x" * 50)
    assert "truncated" in result.output


def _write_coverage_report(
    root: Path,
    *,
    timestamp: str = "2026-02-01T00:00:00",
    branch_coverage: bool = True,
    include_beta: bool = True,
) -> None:
    package = root / "isoprax"
    package.mkdir(exist_ok=True)
    (package / "alpha.py").write_text("", encoding="utf-8")
    (package / "beta.py").write_text("", encoding="utf-8")
    files = {
        "isoprax/alpha.py": {"summary": {"percent_covered": 97.5}},
    }
    if include_beta:
        files["isoprax/beta.py"] = {"summary": {"percent_covered": 91.0}}
    report_path = root / "coverage.json"
    report_path.write_text(
        json.dumps(
            {
                "meta": {
                    "branch_coverage": branch_coverage,
                    "timestamp": timestamp,
                },
                "files": files,
            }
        ),
        encoding="utf-8",
    )
    timestamp_epoch = datetime.fromisoformat(timestamp).astimezone().timestamp()
    os.utime(report_path, (timestamp_epoch, timestamp_epoch))


def test_coverage_review_distinguishes_current_from_historical_artifact(
    tmp_path: Path,
) -> None:
    _write_coverage_report(tmp_path)
    action = LocalActionResult(
        "coverage",
        "passed",
        "2026-01-01T00:00:00+00:00",
        "2026-02-01T06:00:00+00:00",
        0,
        "gate passed",
    )

    current = read_coverage_review(tmp_path, action)
    historical = read_coverage_review(tmp_path)

    assert current.status == "current"
    assert current.modules == (("isoprax/alpha", 97.5), ("isoprax/beta", 91.0))
    assert historical.status == "historical"
    assert historical.generated_at == "2026-02-01T00:00:00"


def test_coverage_review_is_stale_after_failed_or_nonrefreshing_run(
    tmp_path: Path,
) -> None:
    _write_coverage_report(tmp_path)
    failed = LocalActionResult(
        "coverage",
        "failed",
        "2026-03-01T00:00:00+00:00",
        "2026-03-01T00:01:00+00:00",
        1,
        "test failed",
    )

    assert read_coverage_review(tmp_path, failed).status == "stale"


def test_coverage_review_rejects_artifact_timestamp_outside_current_run(
    tmp_path: Path,
) -> None:
    _write_coverage_report(tmp_path, timestamp="2026-12-01T00:00:00")
    action = LocalActionResult(
        "coverage",
        "passed",
        "2026-01-01T00:00:00+00:00",
        "2026-02-01T06:00:00+00:00",
        0,
        "gate passed",
    )

    assert read_coverage_review(tmp_path, action).status == "stale"


@pytest.mark.parametrize(
    ("branch_coverage", "include_beta", "expected_status"),
    ((False, True, "invalid"), (True, False, "historical")),
)
def test_coverage_review_fails_closed_on_branch_metadata_and_shows_missing_modules(
    tmp_path: Path,
    branch_coverage: bool,
    include_beta: bool,
    expected_status: str,
) -> None:
    _write_coverage_report(
        tmp_path, branch_coverage=branch_coverage, include_beta=include_beta
    )

    review = read_coverage_review(tmp_path)

    assert review.status == expected_status
    if include_beta:
        assert review.missing_modules == ()
    else:
        assert review.missing_modules == ("isoprax/beta",)
        assert "1 production module" in (review.message or "")


def test_coverage_review_reports_missing_and_malformed_artifacts(
    tmp_path: Path,
) -> None:
    assert read_coverage_review(tmp_path).status == "missing"
    (tmp_path / "coverage.json").write_text("not json", encoding="utf-8")
    assert read_coverage_review(tmp_path).status == "invalid"


def test_coverage_review_rejects_oversized_artifact(tmp_path: Path) -> None:
    path = tmp_path / "coverage.json"
    path.write_bytes(b" " * (MAX_COVERAGE_BYTES + 1))

    assert read_coverage_review(tmp_path).status == "invalid"


def _write_graph(
    path: Path, nodes: list[dict[str, str]], links: list[dict[str, str]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"built_at_commit": "abc123", "nodes": nodes, "links": links}),
        encoding="utf-8",
    )


def test_graphify_snapshot_checks_commit_cleanliness_schema_and_search(
    tmp_path: Path,
) -> None:
    graph_path = tmp_path / "graph.json"
    _write_graph(
        graph_path,
        [
            {"id": "root", "label": 'Safe "center"', "source_file": "app.py"},
            {"id": "child", "label": "Verifier", "source_file": "verify.py"},
        ],
        [{"source": "root", "target": "child", "relation": "calls"}],
    )

    fresh = read_graphify_snapshot(graph_path, "abc123", False)
    stale = read_graphify_snapshot(graph_path, "abc123", True)
    matches = search_graphify_nodes(stale, "verif")
    neighborhood = graphify_neighborhood(stale, "root")

    assert fresh.status == "current"
    assert stale.status == "potentially_stale"
    assert [node.label for node in matches] == ["Verifier"]
    assert neighborhood is not None
    assert neighborhood.node_count == 2
    assert neighborhood.link_count == 1
    assert 'Safe \\"center\\"' in neighborhood.dot
    assert "calls" in neighborhood.dot


def test_graphify_rejects_bad_endpoints_missing_and_oversized_artifacts(
    tmp_path: Path,
) -> None:
    graph_path = tmp_path / "graph.json"
    _write_graph(
        graph_path,
        [{"id": "root", "label": "Root"}],
        [{"source": "root", "target": "absent", "relation": "calls"}],
    )
    assert read_graphify_snapshot(graph_path, "abc123", False).status == "invalid"
    assert (
        read_graphify_snapshot(tmp_path / "missing.json", None, None).status
        == "missing"
    )
    graph_path.write_bytes(b" " * (MAX_GRAPH_BYTES + 1))
    assert read_graphify_snapshot(graph_path, "abc123", False).status == "invalid"


def test_graphify_search_caps_matching_results() -> None:
    nodes = tuple(
        GraphNode(str(index), "Verifier", "verify.py", f"L{index}")
        for index in range(100)
    )
    snapshot = GraphifySnapshot("current", "abc123", 100, 0, nodes, ())

    assert len(search_graphify_nodes(snapshot, "verifier")) == 50


@pytest.mark.parametrize("edge_count", (MAX_NEIGHBORHOOD_LINKS + 1,))
def test_graphify_neighborhood_caps_nodes_and_edges(edge_count: int) -> None:
    nodes = tuple(
        GraphNode(str(index), f"Node {index}", "source.py", f"L{index}")
        for index in range(MAX_NEIGHBORHOOD_NODES + 20)
    )
    links = tuple(
        GraphLink("0", str(index), "calls")
        for index in range(1, MAX_NEIGHBORHOOD_NODES + 20)
    ) + tuple(GraphLink("0", "1", "uses") for _ in range(edge_count))
    snapshot = GraphifySnapshot(
        "current", "abc123", len(nodes), len(links), nodes, links
    )

    neighborhood = graphify_neighborhood(snapshot, "0")

    assert neighborhood is not None
    assert neighborhood.node_count == MAX_NEIGHBORHOOD_NODES
    assert neighborhood.link_count == MAX_NEIGHBORHOOD_LINKS
    assert neighborhood.truncated is True
    assert neighborhood.dot.count(" -> ") == MAX_NEIGHBORHOOD_LINKS
