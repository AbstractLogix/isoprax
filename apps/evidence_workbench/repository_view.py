"""Streamlit presentation for independent repository-health signals."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pandas as pd
import streamlit as st

from apps.evidence_workbench.repository import (
    MINIMUM_COVERAGE_PERCENT,
    CoverageReview,
    LocalActionResult,
    graphify_neighborhood,
    read_coverage_review,
    read_git_state,
    read_graphify_snapshot,
    run_local_action,
    search_graphify_nodes,
)


def render_repository_review(repo_root: Path) -> None:
    st.title("Repository Review")
    st.warning(
        "Test execution, saved coverage, and Graphify structure are separate "
        "signals. None is evidence of predictive efficacy or conformance."
    )
    st.subheader("Branch-aware coverage")
    st.caption(
        "Run the repository's fixed `make coverage` gate explicitly. The workbench "
        "does not execute tests on page load."
    )
    if st.button("Run coverage gate", type="primary", key="run_coverage_gate"):
        with st.spinner("Running the repository coverage gate…"):
            result = run_local_action("coverage", repo_root)
            st.session_state["workbench_coverage_action"] = asdict(result)

    action = _saved_coverage_action(st.session_state.get("workbench_coverage_action"))
    if action is None:
        st.info("No coverage gate has run in this session.")
    else:
        _render_action(action)
        if action.status == "passed":
            st.success("The coverage gate passed in this session.")
        elif action.status == "failed":
            st.error(
                "The latest coverage gate failed; any older artifact stays historical."
            )
        else:
            st.warning("The latest coverage gate did not produce a confirmed pass.")

    _render_coverage_review(read_coverage_review(repo_root, action))
    st.divider()
    _render_graphify_review(repo_root)


def _saved_coverage_action(value: object) -> LocalActionResult | None:
    if not isinstance(value, dict) or value.get("action") != "coverage":
        return None
    try:
        return LocalActionResult(**value)
    except TypeError:
        return None


def _render_action(action: LocalActionResult) -> None:
    if action.output:
        with st.expander("Coverage gate output", expanded=True):
            st.code(action.output, language="text")


def _render_coverage_review(coverage: CoverageReview) -> None:
    if coverage.status == "current":
        st.success("Coverage artifact was refreshed by this session's gate run.")
    elif coverage.status == "historical":
        st.info("Historical coverage artifact; not current test status.")
    elif coverage.status == "stale":
        st.warning("Coverage artifact is stale relative to the latest gate attempt.")
    elif coverage.status == "missing":
        st.info("No saved coverage artifact is available.")
    else:
        st.error("Saved coverage artifact is invalid or not branch-aware.")
    if coverage.generated_at:
        st.caption(f"Artifact timestamp: {coverage.generated_at}")
    if coverage.message:
        st.warning(coverage.message)
    if coverage.missing_modules:
        st.caption(
            "Modules without a coverage value remain unknown: "
            + ", ".join(coverage.missing_modules)
        )
    if not coverage.modules:
        return

    st.markdown("#### Per-module coverage gate metric")
    st.caption(
        f"Bars use coverage.py's combined `percent_covered` in branch mode; "
        f"the per-module gate threshold is {MINIMUM_COVERAGE_PERCENT:.0f}%. "
        "Saved values retain the artifact status shown above."
    )
    ordered = sorted(coverage.modules, key=lambda row: (row[1], row[0]))
    below_threshold = tuple(
        (module, percent)
        for module, percent in ordered
        if percent < MINIMUM_COVERAGE_PERCENT
    )
    if below_threshold:
        st.warning(
            f"{len(below_threshold)} reported module(s) are below the "
            f"{MINIMUM_COVERAGE_PERCENT:.0f}% gate metric. Artifact freshness "
            "and the current gate result are shown separately above."
        )
    show_all = st.checkbox("Show every reported production module", value=False)
    visible = ordered if show_all else ordered[:15]
    frame = pd.DataFrame(
        [
            {
                "Module": f"⚠ {module}"
                if percent < MINIMUM_COVERAGE_PERCENT
                else module,
                "Coverage (%)": percent,
            }
            for module, percent in visible
        ]
    )
    st.bar_chart(
        frame,
        x="Module",
        y="Coverage (%)",
        horizontal=True,
        height=min(950, max(320, len(visible) * 22)),
    )
    if ordered:
        module, percent = ordered[0]
        st.caption(
            f"Lowest reported module: `{module}` at {percent:.2f}%. "
            f"Showing {len(visible)} of {len(ordered)} reported modules."
        )


def _render_graphify_review(repo_root: Path) -> None:
    st.subheader("Graphify code neighborhood")
    current_commit, dirty = read_git_state(repo_root)
    snapshot = read_graphify_snapshot(
        repo_root / "graphify-out" / "graph.json", current_commit, dirty
    )
    if snapshot.status == "missing":
        st.info(
            "No local Graphify index is available. The workbench will not generate one."
        )
        return
    if snapshot.status == "invalid":
        st.warning(snapshot.message or "Graphify index is invalid.")
        return
    if snapshot.status == "current":
        st.success("Graphify index matches the current clean commit.")
    else:
        st.warning(
            "Graphify index may be stale; its neighborhood is an orientation aid, "
            "not verified current architecture."
        )
    st.caption(
        f"Built at `{snapshot.built_at_commit}` · {snapshot.node_count:,} nodes · "
        f"{snapshot.link_count:,} links · source capped at 8 MiB."
    )
    query = st.text_input(
        "Search indexed symbols or source paths", key="graphify_query"
    )
    matches = search_graphify_nodes(snapshot, query)
    if not query.strip():
        st.caption(
            "Enter a label or file fragment to inspect a bounded one-hop neighborhood."
        )
        return
    if not matches:
        st.info("No matching Graphify nodes.")
        return
    selected = st.selectbox(
        "Matching nodes",
        matches,
        format_func=lambda node: (
            f"{node.label} — {node.source_file or 'source unknown'}"
        ),
    )
    neighborhood = graphify_neighborhood(snapshot, selected.node_id)
    if neighborhood is None:
        st.info("No neighborhood is available for that node.")
        return
    if neighborhood.truncated:
        st.caption("Neighborhood truncated at 60 nodes or 200 links.")
    st.graphviz_chart(neighborhood.dot)
