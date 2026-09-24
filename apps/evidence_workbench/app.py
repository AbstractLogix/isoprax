"""Streamlit entry point for the local evidence review workbench."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pandas as pd
import streamlit as st

from apps.evidence_workbench.datasets import (
    DatasetVerification,
    ExampleDescription,
    load_example_catalog,
    not_run_verification,
    project_dataset_charts,
    verify_local_dataset,
)
from apps.evidence_workbench.repository import (
    LocalActionResult,
    run_local_action,
)
from apps.evidence_workbench.repository_view import render_repository_review

REPO_ROOT = Path(__file__).resolve().parents[2]
_VIEWS = (
    "Overview",
    "AI4I 2020",
    "ApacheJIT",
    "NASA C-MAPSS",
    "MetroPT-3",
    "Repository Review",
)


def main() -> None:
    st.set_page_config(page_title="Isoprax Evidence Workbench", layout="wide")
    st.sidebar.title("Isoprax")
    selected_view = st.sidebar.radio("Review", _VIEWS, index=0)
    if selected_view == "Overview":
        render_overview()
    elif selected_view == "Repository Review":
        render_repository_review(REPO_ROOT)
    else:
        dataset_id = {
            "AI4I 2020": "ai4i2020",
            "ApacheJIT": "apachejit",
            "NASA C-MAPSS": "cmapss",
            "MetroPT-3": "metropt3",
        }[selected_view]
        render_dataset_page(dataset_id)


def render_overview() -> None:
    st.title("Local Evidence Review Workbench")
    st.write(
        "Explore the repository's distinct evidence examples, inspect local "
        "verifier reports, and review maintainer signals. Nothing is downloaded "
        "or uploaded by this workbench."
    )
    st.warning(
        "Dataset verification is structural evidence only. The examples have "
        "different outcomes and must not be pooled; none establishes predictive "
        "efficacy, production performance, Semantic Conformance, or Full Conformance."
    )

    try:
        examples = load_example_catalog(REPO_ROOT)
    except ValueError as error:
        st.error(f"Example catalog unavailable: {error}")
        return

    st.subheader("Examples")
    for row_start in range(0, len(examples), 2):
        columns = st.columns(2)
        for column, example in zip(columns, examples[row_start : row_start + 2]):
            with column:
                _render_example_card(example)

    st.subheader("Try the synthetic demo")
    st.caption(
        "This runs the existing in-memory cross-family demonstration. It is "
        "separate from all four public-dataset verifications."
    )
    if st.button("Run synthetic demo", type="primary", key="run_synthetic_demo"):
        with st.spinner("Running the local synthetic demonstration…"):
            st.session_state["workbench_demo_result"] = asdict(
                run_local_action("demo", REPO_ROOT)
            )

    result = st.session_state.get("workbench_demo_result")
    if isinstance(result, dict):
        _render_action_result(result, synthetic=True)


def _render_example_card(example: ExampleDescription) -> None:
    st.markdown(f"#### {example.display_name}")
    st.caption(example.evidence_class)
    st.write(example.outcome_summary)
    st.info(example.claim_boundary, icon="ℹ️")
    st.link_button("Canonical source", example.source_reference)
    st.caption(f"Repository manifest: `{example.manifest_path}`")


def render_dataset_page(dataset_id: str) -> None:
    try:
        examples = load_example_catalog(REPO_ROOT)
        example = next(item for item in examples if item.dataset_id == dataset_id)
    except (ValueError, StopIteration) as error:
        st.error(f"Example metadata unavailable: {error}")
        return

    st.title(example.display_name)
    st.caption(example.evidence_class)
    st.write(example.outcome_summary)
    st.info(example.claim_boundary, icon="ℹ️")
    st.link_button("Canonical source", example.source_reference)

    submitted, paths = _dataset_path_form(dataset_id)
    state_key = f"workbench_verification_{dataset_id}"
    if submitted:
        with st.spinner(f"Verifying {example.display_name} local artifacts…"):
            result = verify_local_dataset(dataset_id, paths, REPO_ROOT)
            st.session_state[state_key] = asdict(result)

    saved = st.session_state.get(state_key)
    if isinstance(saved, dict):
        _render_verification(saved)
    else:
        _render_verification(asdict(not_run_verification(dataset_id)))


def _dataset_path_form(dataset_id: str) -> tuple[bool, dict[str, str]]:
    paths: dict[str, str] = {}
    with st.form(f"verify_{dataset_id}"):
        if dataset_id in {"ai4i2020", "apachejit"}:
            label = (
                "AI4I CSV path" if dataset_id == "ai4i2020" else "ApacheJIT CSV path"
            )
            paths["csv"] = st.text_input(label, key=f"{dataset_id}_csv_path")
        elif dataset_id == "cmapss":
            paths["dataset"] = st.selectbox(
                "C-MAPSS subset", ("FD001", "FD002", "FD003", "FD004")
            )
            paths["train"] = st.text_input("Train file path", key="cmapss_train_path")
            paths["test"] = st.text_input("Test file path", key="cmapss_test_path")
            paths["rul"] = st.text_input("RUL file path", key="cmapss_rul_path")
        else:
            paths["csv"] = st.text_input("MetroPT-3 CSV path", key="metropt3_csv_path")
            paths["intervals"] = st.text_input(
                "External interval manifest path",
                value="examples/metropt3/failure_intervals.json",
                key="metropt3_intervals_path",
            )
        submitted = st.form_submit_button("Verify local files", type="primary")
    return submitted, paths


def _render_verification(result: dict[str, object]) -> None:
    status = result.get("status")
    if status == "not_run":
        st.info("Not run. Supply local artifact paths above to begin verification.")
        return
    if status == "verified":
        st.success("Verified against the declared structural checks.")
    elif status == "verified_with_warnings":
        st.warning("Verified with diagnostics that require human review.")
    elif status == "failed":
        st.error(
            "Verification failed. The input is not presented as verified evidence."
        )
    else:
        st.warning(
            f"Verification unavailable: {result.get('message', 'unknown reason')}"
        )

    report = result.get("report")
    if not isinstance(report, dict):
        return
    for error in report.get("errors", []):
        st.error(str(error))
    for warning in report.get("warnings", []):
        st.warning(str(warning))
    _render_dataset_charts(result, report)
    with st.expander("Structured verifier report"):
        st.json(report, expanded=False)


def _render_dataset_charts(
    result: dict[str, object], report: dict[str, object]
) -> None:
    status = result.get("status")
    dataset_id = result.get("dataset_id")
    if status not in {"verified", "verified_with_warnings"}:
        return
    if not isinstance(dataset_id, str):
        st.info("Chart summary unavailable: dataset identity is missing.")
        return

    verification = DatasetVerification(dataset_id, status, report)  # type: ignore[arg-type]
    charts = project_dataset_charts(verification)
    if not charts:
        st.info(
            "Chart summary unavailable: the verifier report is incomplete or inconsistent."
        )
        return

    caveats = {
        "ai4i2020": (
            "Composite and mode labels can overlap; these bars are not mutually "
            "exclusive categories. Discrepancy counts are shown separately."
        ),
        "apachejit": (
            "The positive-label fraction describes repository-derived labels, "
            "not model precision or runtime failure incidence."
        ),
        "cmapss": (
            "Train and held-out test counts describe simulated engine trajectories; "
            "they are not real-fleet or predictive-efficacy results."
        ),
        "metropt3": (
            "Coverage is limited to externally reported intervals. Observations "
            "outside those anchors are censored, not negative examples."
        ),
    }
    caveat = caveats.get(dataset_id)
    if caveat is None:
        st.info("Chart summary unavailable: dataset identity is unsupported.")
        return
    st.subheader("Verified report charts")
    st.caption(caveat)
    for chart in charts:
        st.markdown(f"#### {chart.title}")
        frame = pd.DataFrame(
            [
                {chart.x_label: category, chart.y_label: value}
                for category, value in chart.points
            ]
        )
        st.bar_chart(
            frame,
            x=chart.x_label,
            y=chart.y_label,
            horizontal=True,
            height=250,
        )


def _render_action_result(
    result: dict[str, object] | LocalActionResult, *, synthetic: bool = False
) -> None:
    values = asdict(result) if isinstance(result, LocalActionResult) else result
    label = "Synthetic demo" if synthetic else str(values.get("action", "Action"))
    status = values.get("status")
    if status == "passed":
        extra = " This output is synthetic evidence only." if synthetic else ""
        st.success(f"{label} completed.{extra}")
    elif status == "failed":
        st.error(f"{label} exited with failure; review the captured output.")
    elif status == "timed_out":
        st.warning(f"{label} timed out; the result is incomplete.")
    else:
        st.warning(f"{label} is unavailable; no result was produced.")
    output = values.get("output")
    if isinstance(output, str) and output:
        with st.expander("Captured output", expanded=True):
            st.code(output, language="text")


if __name__ == "__main__":
    main()
