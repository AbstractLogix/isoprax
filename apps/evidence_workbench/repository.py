"""Read-only repository review helpers and explicit local actions."""

from __future__ import annotations

import json
import math
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

LocalAction = Literal["demo", "coverage"]
ActionStatus = Literal["passed", "failed", "timed_out", "unavailable"]

MAX_ACTION_OUTPUT_CHARS = 20_000
MAX_COVERAGE_BYTES = 32 * 1024 * 1024
MAX_GRAPH_BYTES = 8 * 1024 * 1024
MAX_NEIGHBORHOOD_NODES = 60
MAX_NEIGHBORHOOD_LINKS = 200
MAX_GRAPH_SEARCH_RESULTS = 50
MINIMUM_COVERAGE_PERCENT = 95.0
ACTION_COMMANDS: dict[LocalAction, tuple[tuple[str, ...], int]] = {
    "demo": (("uv", "run", "python", "examples/demo_cross_family.py"), 120),
    "coverage": (("make", "coverage"), 600),
}


@dataclass(frozen=True)
class LocalActionResult:
    action: LocalAction
    status: ActionStatus
    started_at: str
    finished_at: str
    return_code: int | None
    output: str


CoverageStatus = Literal["current", "historical", "stale", "missing", "invalid"]
GraphStatus = Literal["current", "potentially_stale", "missing", "invalid"]


@dataclass(frozen=True)
class CoverageReview:
    status: CoverageStatus
    generated_at: str | None
    modules: tuple[tuple[str, float], ...]
    missing_modules: tuple[str, ...]
    message: str | None = None


@dataclass(frozen=True)
class GraphNode:
    node_id: str
    label: str
    source_file: str
    source_location: str


@dataclass(frozen=True)
class GraphLink:
    source: str
    target: str
    relation: str


@dataclass(frozen=True)
class GraphifySnapshot:
    status: GraphStatus
    built_at_commit: str | None
    node_count: int
    link_count: int
    nodes: tuple[GraphNode, ...]
    links: tuple[GraphLink, ...]
    message: str | None = None


@dataclass(frozen=True)
class GraphNeighborhood:
    dot: str
    node_count: int
    link_count: int
    truncated: bool


def run_local_action(action: str, repo_root: Path) -> LocalActionResult:
    """Run one fixed, local repository action and capture a bounded result."""

    if action not in ACTION_COMMANDS:
        raise ValueError(f"unsupported local action: {action}")
    action_name = action
    command, timeout = ACTION_COMMANDS[action_name]  # type: ignore[index]
    started_at = _now()

    try:
        completed = subprocess.run(
            command,
            cwd=repo_root.resolve(),
            capture_output=True,
            check=False,
            shell=False,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        return LocalActionResult(
            action_name,
            "timed_out",
            started_at,
            _now(),
            None,
            _bounded_output(_join_output(error.output, error.stderr)),
        )
    except OSError as error:
        return LocalActionResult(
            action_name,
            "unavailable",
            started_at,
            _now(),
            None,
            _bounded_output(str(error)),
        )

    output = _bounded_output(_join_output(completed.stdout, completed.stderr))
    return LocalActionResult(
        action_name,
        "passed" if completed.returncode == 0 else "failed",
        started_at,
        _now(),
        completed.returncode,
        output,
    )


def _join_output(stdout: str | bytes | None, stderr: str | bytes | None) -> str:
    parts = [_as_text(part) for part in (stdout, stderr) if part]
    return "\n".join(parts)


def _as_text(value: str | bytes) -> str:
    return (
        value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value
    )


def _bounded_output(output: str) -> str:
    if len(output) <= MAX_ACTION_OUTPUT_CHARS:
        return output
    marker = "[earlier output truncated]\n"
    return marker + output[-(MAX_ACTION_OUTPUT_CHARS - len(marker)) :]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_coverage_review(
    repo_root: Path, action: LocalActionResult | None = None
) -> CoverageReview:
    """Read branch-aware coverage while keeping artifact age separate from run status."""

    path = repo_root / "coverage.json"
    try:
        modified_at = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
        if path.stat().st_size > MAX_COVERAGE_BYTES:
            return CoverageReview(
                "invalid", None, (), (), "coverage.json exceeds the size limit"
            )
        raw = path.read_bytes()
    except FileNotFoundError:
        return CoverageReview("missing", None, (), (), "coverage.json is not present")
    except OSError as error:
        return CoverageReview(
            "invalid", None, (), (), f"coverage.json cannot be read: {error}"
        )
    if len(raw) > MAX_COVERAGE_BYTES:
        return CoverageReview(
            "invalid", None, (), (), "coverage.json exceeds the size limit"
        )
    try:
        payload = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError) as error:
        return CoverageReview(
            "invalid", None, (), (), f"coverage.json is invalid: {error}"
        )

    if not isinstance(payload, dict):
        return CoverageReview(
            "invalid", None, (), (), "coverage report must be a JSON object"
        )
    meta = payload.get("meta")
    files = payload.get("files")
    if (
        not isinstance(meta, dict)
        or meta.get("branch_coverage") is not True
        or not isinstance(meta.get("timestamp"), str)
        or not isinstance(files, dict)
    ):
        return CoverageReview(
            "invalid",
            None,
            (),
            (),
            "coverage report lacks branch-aware metadata or files",
        )
    generated_at = meta["timestamp"]
    try:
        generated = _parse_timestamp(generated_at)
    except ValueError:
        return CoverageReview(
            "invalid", generated_at, (), (), "coverage timestamp is invalid"
        )

    expected_paths = {
        candidate.resolve(): candidate.relative_to(repo_root).with_suffix("").as_posix()
        for candidate in (repo_root / "isoprax").glob("*.py")
        if candidate.name != "__init__.py"
    }
    if not expected_paths:
        return CoverageReview(
            "invalid", generated_at, (), (), "no production modules were found"
        )

    observed: dict[Path, float] = {}
    for filename, details in files.items():
        if not isinstance(filename, str) or not isinstance(details, dict):
            continue
        candidate = Path(filename)
        resolved = (
            candidate if candidate.is_absolute() else repo_root / candidate
        ).resolve()
        if resolved not in expected_paths:
            continue
        summary = details.get("summary")
        percent = summary.get("percent_covered") if isinstance(summary, dict) else None
        if (
            isinstance(percent, bool)
            or not isinstance(percent, (int, float))
            or not math.isfinite(percent)
            or not 0 <= percent <= 100
        ):
            return CoverageReview(
                "invalid",
                generated_at,
                (),
                (),
                f"coverage value for {filename} is invalid",
            )
        observed[resolved] = float(percent)

    missing = tuple(
        sorted(
            name
            for resolved, name in expected_paths.items()
            if resolved not in observed
        )
    )
    modules = tuple(
        sorted(
            (expected_paths[resolved], percent)
            for resolved, percent in observed.items()
        )
    )
    status: CoverageStatus
    if action is None or action.action != "coverage":
        status = "historical"
    elif action.status == "passed" and action.return_code == 0:
        try:
            started = _parse_timestamp(action.started_at)
            finished = _parse_timestamp(action.finished_at)
        except (TypeError, ValueError):
            started = None
            finished = None
        status = (
            "current"
            if (
                started is not None
                and finished is not None
                and started <= generated <= finished
                and modified_at >= started
                and modified_at <= finished
            )
            else "stale"
        )
    else:
        status = "stale"
    message = (
        f"coverage data is missing for {len(missing)} production module(s)"
        if missing
        else None
    )
    return CoverageReview(status, generated_at, modules, missing, message)


def read_graphify_snapshot(
    path: Path, current_commit: str | None, working_tree_dirty: bool | None
) -> GraphifySnapshot:
    """Read a bounded Graphify JSON snapshot and label unverifiable freshness."""

    try:
        if path.stat().st_size > MAX_GRAPH_BYTES:
            return _empty_graph("Graphify JSON exceeds the configured size limit")
        raw = path.read_bytes()
    except FileNotFoundError:
        return _empty_graph("graphify-out/graph.json is not present", status="missing")
    except OSError as error:
        return _empty_graph(f"Graphify JSON cannot be read: {error}")
    if len(raw) > MAX_GRAPH_BYTES:
        return _empty_graph("Graphify JSON exceeds the configured size limit")
    try:
        payload = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError):
        return _empty_graph("Graphify JSON is malformed")
    if not isinstance(payload, dict):
        return _empty_graph("Graphify JSON must be an object")
    built_at_commit = payload.get("built_at_commit")
    raw_nodes, raw_links = payload.get("nodes"), payload.get("links")
    if (
        not isinstance(built_at_commit, str)
        or not built_at_commit.strip()
        or not isinstance(raw_nodes, list)
        or not isinstance(raw_links, list)
    ):
        return _empty_graph("Graphify JSON lacks commit, node, or link metadata")

    nodes: list[GraphNode] = []
    node_ids: set[str] = set()
    for node in raw_nodes:
        if not isinstance(node, dict):
            return _empty_graph("Graphify node has an invalid shape")
        node_id, label = node.get("id"), node.get("label")
        if (
            not isinstance(node_id, str)
            or not node_id
            or node_id in node_ids
            or not isinstance(label, str)
            or not label
        ):
            return _empty_graph("Graphify node identity or label is invalid")
        node_ids.add(node_id)
        nodes.append(
            GraphNode(
                node_id,
                label,
                _optional_text(node.get("source_file")),
                _optional_text(node.get("source_location")),
            )
        )

    links: list[GraphLink] = []
    for link in raw_links:
        if not isinstance(link, dict):
            return _empty_graph("Graphify link has an invalid shape")
        source, target, relation = (
            link.get("source"),
            link.get("target"),
            link.get("relation"),
        )
        if (
            not isinstance(source, str)
            or source not in node_ids
            or not isinstance(target, str)
            or target not in node_ids
            or not isinstance(relation, str)
            or not relation
        ):
            return _empty_graph("Graphify link endpoint or relation is invalid")
        links.append(GraphLink(source, target, relation))

    status: GraphStatus = (
        "current"
        if current_commit == built_at_commit and working_tree_dirty is False
        else "potentially_stale"
    )
    message = None
    if status == "potentially_stale":
        message = "commit or working-tree state does not prove this graph is current"
    return GraphifySnapshot(
        status,
        built_at_commit,
        len(nodes),
        len(links),
        tuple(nodes),
        tuple(links),
        message,
    )


def search_graphify_nodes(
    snapshot: GraphifySnapshot, query: str
) -> tuple[GraphNode, ...]:
    """Search labels/source paths literally and return a stable bounded result."""

    needle = query.strip().casefold()
    if not needle or snapshot.status in {"missing", "invalid"}:
        return ()
    matches = [
        node
        for node in snapshot.nodes
        if needle in node.label.casefold() or needle in node.source_file.casefold()
    ]
    matches.sort(
        key=lambda node: (node.label.casefold(), node.source_file, node.node_id)
    )
    return tuple(matches[:MAX_GRAPH_SEARCH_RESULTS])


def graphify_neighborhood(
    snapshot: GraphifySnapshot, node_id: str
) -> GraphNeighborhood | None:
    """Return a one-hop DOT view with synthetic IDs and strict size bounds."""

    node_by_id = {node.node_id: node for node in snapshot.nodes}
    center = node_by_id.get(node_id)
    if center is None or snapshot.status in {"missing", "invalid"}:
        return None
    adjacent_ids = {
        link.target if link.source == node_id else link.source
        for link in snapshot.links
        if link.source == node_id or link.target == node_id
    }
    ordered_neighbors = sorted(
        (node_by_id[neighbor] for neighbor in adjacent_ids if neighbor != node_id),
        key=lambda node: (node.label.casefold(), node.source_file, node.node_id),
    )
    selected_nodes = [center, *ordered_neighbors[: MAX_NEIGHBORHOOD_NODES - 1]]
    selected_ids = {node.node_id for node in selected_nodes}
    candidate_links = [
        link
        for link in snapshot.links
        if link.source in selected_ids and link.target in selected_ids
    ]
    selected_links = candidate_links[:MAX_NEIGHBORHOOD_LINKS]
    dot_ids = {node.node_id: f"n{index}" for index, node in enumerate(selected_nodes)}
    lines = ["digraph G {", "  rankdir=LR;", "  node [shape=box];"]
    for node in selected_nodes:
        label = node.label
        source = ":".join(
            part for part in (node.source_file, node.source_location) if part
        )
        if source:
            label = f"{label}\\n{source}"
        lines.append(f"  {dot_ids[node.node_id]} [label={json.dumps(label)}];")
    for link in selected_links:
        lines.append(
            f"  {dot_ids[link.source]} -> {dot_ids[link.target]} "
            f"[label={json.dumps(link.relation)}];"
        )
    lines.append("}")
    truncated = (
        len(ordered_neighbors) > MAX_NEIGHBORHOOD_NODES - 1
        or len(candidate_links) > MAX_NEIGHBORHOOD_LINKS
    )
    return GraphNeighborhood(
        "\n".join(lines), len(selected_nodes), len(selected_links), truncated
    )


def read_git_state(repo_root: Path) -> tuple[str | None, bool | None]:
    """Read only the current commit and whether tracked/untracked files are dirty."""

    try:
        commit = subprocess.run(
            ("git", "rev-parse", "HEAD"),
            cwd=repo_root.resolve(),
            capture_output=True,
            check=True,
            shell=False,
            text=True,
            timeout=5,
        ).stdout.strip()
        status = subprocess.run(
            ("git", "status", "--porcelain", "--untracked-files=normal"),
            cwd=repo_root.resolve(),
            capture_output=True,
            check=True,
            shell=False,
            text=True,
            timeout=5,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return None, None
    return (commit or None), bool(status.strip())


def _parse_timestamp(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    return parsed.astimezone(timezone.utc)


def _optional_text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _empty_graph(message: str, *, status: GraphStatus = "invalid") -> GraphifySnapshot:
    return GraphifySnapshot(status, None, 0, 0, (), (), message)
