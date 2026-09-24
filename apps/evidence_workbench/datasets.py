"""Dataset catalog, verifier adapters, and per-example chart projections."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Mapping
from urllib.parse import urlsplit

from isoprax.ai4i2020 import verify_ai4i2020_csv
from isoprax.apachejit import verify_apachejit_csv
from isoprax.metropt3 import read_metropt3_intervals, verify_metropt3_csv
from isoprax.nasa_cmaps import verify_cmapss

VerificationStatus = Literal[
    "not_run", "verified", "verified_with_warnings", "failed", "unavailable"
]


@dataclass(frozen=True)
class ExampleDescription:
    dataset_id: str
    display_name: str
    evidence_class: str
    outcome_summary: str
    manifest_path: str
    source_reference: str
    claim_boundary: str


@dataclass(frozen=True)
class DatasetVerification:
    dataset_id: str
    status: VerificationStatus
    report: dict[str, Any] | None
    message: str | None = None


@dataclass(frozen=True)
class ChartProjection:
    """One report-derived bar chart with explicit categorical axes."""

    title: str
    x_label: str
    y_label: str
    points: tuple[tuple[str, int | float], ...]


_REQUIRED_PATHS: dict[str, tuple[str, ...]] = {
    "ai4i2020": ("csv",),
    "apachejit": ("csv",),
    "cmapss": ("train", "test", "rul"),
    "metropt3": ("csv", "intervals"),
}


_EXAMPLES = (
    (
        "ai4i2020",
        "AI4I 2020",
        "synthetic structural and label-semantics evidence",
        "Synthetic process-cycle observations with a composite machine-failure label and five potentially overlapping mode labels for the current process cycle.",
        "examples/ai4i2020/manifest.json",
    ),
    (
        "apachejit",
        "ApacheJIT",
        "repository-derived commit labels",
        "Bug-inducing commit labels derived from repository history; these are not labels of observed runtime failures.",
        "examples/apachejit/manifest.json",
    ),
    (
        "cmapss",
        "NASA C-MAPSS",
        "simulated run-to-failure and RUL evidence",
        "Simulated engine run-to-failure trajectories with held-out remaining-useful-life files; not real-fleet evidence.",
        "examples/cmapss/manifest.json",
    ),
    (
        "metropt3",
        "MetroPT-3",
        "externally anchored single-stream observations",
        "One compressor stream with externally reported air-leak intervals; observations outside those intervals remain censored.",
        "examples/metropt3/manifest.json",
    ),
)


def load_example_catalog(repo_root: Path) -> tuple[ExampleDescription, ...]:
    """Load source and claim-boundary metadata from the tracked manifests."""

    descriptions: list[ExampleDescription] = []
    for dataset_id, name, evidence_class, outcome, relative_manifest in _EXAMPLES:
        path = repo_root / relative_manifest
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ValueError(
                f"{dataset_id} manifest is unavailable: {error}"
            ) from error
        if not isinstance(manifest, dict) or manifest.get("dataset_id") != dataset_id:
            raise ValueError(f"{dataset_id} manifest has an invalid dataset identity")
        claim_boundary = manifest.get("claim_boundary")
        if not isinstance(claim_boundary, str) or not claim_boundary.strip():
            raise ValueError(f"{dataset_id} manifest has no claim boundary")
        source_reference = _source_reference(manifest)
        descriptions.append(
            ExampleDescription(
                dataset_id,
                name,
                evidence_class,
                outcome,
                relative_manifest,
                source_reference,
                claim_boundary,
            )
        )
    return tuple(descriptions)


def _source_reference(manifest: dict[str, object]) -> str:
    nested_source = manifest.get("source")
    if isinstance(nested_source, dict):
        reference = nested_source.get("retrieval_reference")
    else:
        reference = manifest.get("canonical_source")
    if not isinstance(reference, str) or not reference.startswith("https://"):
        dataset_id = manifest.get("dataset_id", "unknown")
        raise ValueError(f"{dataset_id} manifest has no canonical HTTPS source")
    return reference


def not_run_verification(dataset_id: str) -> DatasetVerification:
    """Represent the absence of a verifier invocation without inventing counts."""

    return DatasetVerification(dataset_id, "not_run", None)


def required_dataset_path_fields(dataset_id: str) -> tuple[str, ...]:
    """Return the local artifact fields required by one dataset verifier."""

    try:
        return _REQUIRED_PATHS[dataset_id]
    except KeyError:
        raise ValueError(f"unsupported dataset: {dataset_id}") from None


def verify_local_dataset(
    dataset_id: str,
    paths: Mapping[str, str],
    repo_root: Path,
) -> DatasetVerification:
    """Call one existing verifier for explicit local paths; never fetch inputs."""

    required = required_dataset_path_fields(dataset_id)
    try:
        local_paths = {
            name: _local_path(paths.get(name), name, repo_root) for name in required
        }
        if dataset_id == "cmapss":
            subset = paths.get("dataset", "").upper()
            if subset not in {"FD001", "FD002", "FD003", "FD004"}:
                raise ValueError("C-MAPSS subset must be FD001, FD002, FD003, or FD004")
            report = verify_cmapss(
                subset,
                local_paths["train"],
                local_paths["test"],
                local_paths["rul"],
            )
        elif dataset_id == "ai4i2020":
            report = verify_ai4i2020_csv(local_paths["csv"])
        elif dataset_id == "apachejit":
            report = verify_apachejit_csv(local_paths["csv"])
        else:
            intervals = read_metropt3_intervals(local_paths["intervals"])
            report = verify_metropt3_csv(local_paths["csv"], intervals)
        payload = report.to_dict()
    except (OSError, TypeError, ValueError, UnicodeError) as error:
        return DatasetVerification(dataset_id, "unavailable", None, str(error))

    if not report.verified:
        status: VerificationStatus = "failed"
    elif payload.get("warnings"):
        status = "verified_with_warnings"
    else:
        status = "verified"
    return DatasetVerification(dataset_id, status, payload)


def project_dataset_charts(
    verification: DatasetVerification,
) -> tuple[ChartProjection, ...]:
    """Project charts only from an internally consistent successful report."""

    if verification.status not in {"verified", "verified_with_warnings"}:
        return ()
    report = verification.report
    if not isinstance(report, Mapping) or report.get("verified") is not True:
        return ()
    try:
        if verification.dataset_id == "ai4i2020":
            return _ai4i_charts(report)
        if verification.dataset_id == "apachejit":
            return _apachejit_charts(report)
        if verification.dataset_id == "cmapss":
            return _cmapss_charts(report)
        if verification.dataset_id == "metropt3":
            return _metropt3_charts(report)
    except (KeyError, TypeError, ValueError, OverflowError):
        return ()
    return ()


def _ai4i_charts(report: Mapping[str, Any]) -> tuple[ChartProjection, ...]:
    rows = _count(report, "row_count")
    failures = _count(report, "machine_failure_count")
    modes = _count_map(report, "mode_counts")
    multi_mode = _count(report, "multi_mode_row_count")
    without_mode = _count(report, "failure_without_mode_count")
    mode_without_failure = _count(report, "mode_without_failure_count")
    mismatch = _count(report, "composite_mismatch_count")
    if (
        rows is None
        or rows == 0
        or failures is None
        or modes is None
        or not modes
        or multi_mode is None
        or without_mode is None
        or mode_without_failure is None
        or mismatch != without_mode + mode_without_failure
        or any(
            count > rows
            for count in (
                failures,
                multi_mode,
                without_mode,
                mode_without_failure,
                mismatch,
                *modes.values(),
            )
        )
    ):
        return ()
    labels = (
        ("Machine failure", failures),
        *tuple(modes.items()),
        ("Rows with multiple modes", multi_mode),
    )
    discrepancies = (
        ("Failure without mode", without_mode),
        ("Mode without failure", mode_without_failure),
        ("Total mismatches", mismatch),
    )
    return (
        ChartProjection(
            "Composite, mode, and overlap counts (labels may overlap)",
            "Outcome label",
            "Observed rows",
            labels,
        ),
        ChartProjection(
            "Composite/mode label discrepancies",
            "Discrepancy",
            "Observed rows",
            discrepancies,
        ),
    )


def _apachejit_charts(report: Mapping[str, Any]) -> tuple[ChartProjection, ...]:
    rows = _count(report, "row_count")
    project_count = _count(report, "project_count")
    buggy_count = _count(report, "buggy_count")
    volumes = _count_map(report, "project_counts")
    buggy = _count_map(report, "project_buggy_counts")
    yields = report.get("project_positive_yield")
    if (
        rows is None
        or project_count is None
        or buggy_count is None
        or not volumes
        or buggy is None
        or not isinstance(yields, Mapping)
        or sum(volumes.values()) != rows
        or len(volumes) != project_count
        or sum(buggy.values()) != buggy_count
    ):
        return ()
    if set(yields) != set(volumes) or not set(buggy).issubset(volumes):
        return ()
    volume_points: list[tuple[str, int]] = []
    yield_points: list[tuple[str, float]] = []
    for project in sorted(volumes):
        count = volumes[project]
        positive_count = buggy.get(project, 0)
        fraction = yields[project]
        if (
            count == 0
            or positive_count > count
            or type(fraction) not in {int, float}
            or not 0 <= fraction <= 1
            or not math.isfinite(fraction)
            or not math.isclose(fraction, positive_count / count, abs_tol=1e-12)
        ):
            return ()
        volume_points.append((project, count))
        yield_points.append((project, fraction * 100))
    return (
        ChartProjection(
            "Commit volume by project",
            "Project",
            "Observed commits",
            tuple(volume_points),
        ),
        ChartProjection(
            "Observed positive-label fraction by project (not model precision)",
            "Project",
            "Bug-inducing labels (%)",
            tuple(yield_points),
        ),
    )


def _cmapss_charts(report: Mapping[str, Any]) -> tuple[ChartProjection, ...]:
    dataset = report.get("dataset")
    train_rows = _count(report, "train_rows")
    train_units = _count(report, "train_units")
    test_rows = _count(report, "test_rows")
    test_units = _count(report, "test_units")
    rul_count = _count(report, "rul_count")
    if (
        not isinstance(dataset, str)
        or dataset.upper() not in {"FD001", "FD002", "FD003", "FD004"}
        or any(
            value is None or value == 0
            for value in (train_rows, train_units, test_rows, test_units, rul_count)
        )
        or train_units > train_rows
        or test_units > test_rows
        or test_units != rul_count
    ):
        return ()
    assert train_rows is not None
    assert train_units is not None
    assert test_rows is not None
    assert test_units is not None
    assert rul_count is not None
    return (
        ChartProjection(
            f"{dataset.upper()} observation rows by split",
            "Split",
            "Observed rows",
            (("Train", train_rows), ("Held-out test", test_rows)),  # type: ignore[arg-type]
        ),
        ChartProjection(
            f"{dataset.upper()} unit and RUL alignment",
            "Count type",
            "Observed count",
            (
                ("Train units", train_units),
                ("Held-out test units", test_units),
                ("RUL values", rul_count),
            ),  # type: ignore[arg-type]
        ),
    )


def _metropt3_charts(report: Mapping[str, Any]) -> tuple[ChartProjection, ...]:
    row_count = _count(report, "row_count")
    unique_timestamps = _count(report, "unique_timestamps")
    coverage = _count_map(report, "interval_coverage")
    gaps = report.get("gap_counts_seconds")
    if (
        row_count is None
        or row_count == 0
        or unique_timestamps != row_count
        or not coverage
        or any(count > row_count for count in coverage.values())
        or not isinstance(gaps, Mapping)
    ):
        return ()
    gap_points: list[tuple[int | float, str, int]] = []
    for seconds, count in gaps.items():
        if (
            type(seconds) not in {int, float}
            or seconds <= 0
            or (type(seconds) is float and not math.isfinite(seconds))
            or type(count) is not int
            or count < 0
        ):
            return ()
        label = str(seconds) if type(seconds) is int else f"{seconds:g}"
        gap_points.append((seconds, f"{label} s", count))
    if sum(count for _seconds, _label, count in gap_points) != max(
        0, unique_timestamps - 1
    ):
        return ()
    charts = [
        ChartProjection(
            "Rows observed within external failure intervals",
            "External interval anchor",
            "Anchored observations",
            tuple(sorted(coverage.items())),
        )
    ]
    if gap_points:
        charts.append(
            ChartProjection(
                "Observed timestamp-gap frequency",
                "Gap duration",
                "Observed gaps",
                tuple((label, count) for _seconds, label, count in sorted(gap_points)),
            )
        )
    return tuple(charts)


def _count(report: Mapping[str, Any], field: str) -> int | None:
    value = report.get(field)
    return value if type(value) is int and value >= 0 else None


def _count_map(report: Mapping[str, Any], field: str) -> dict[str, int] | None:
    value = report.get(field)
    if not isinstance(value, Mapping):
        return None
    if any(
        not isinstance(label, str)
        or not label.strip()
        or type(count) is not int
        or count < 0
        for label, count in value.items()
    ):
        return None
    return dict(value)


def _local_path(value: object, field: str, repo_root: Path) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"required local path for {field} is missing")
    raw = value.strip()
    if _is_url(raw):
        raise ValueError(f"{field} must be a local file path; URLs are not supported")
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = repo_root / path
    return path.resolve()


def _is_url(value: str) -> bool:
    scheme = urlsplit(value).scheme
    # urlsplit treats a Windows drive prefix (including drive-relative paths)
    # as a URI scheme. Keep these valid local path forms available to Windows users.
    is_windows_drive_path = len(scheme) == 1 and len(value) >= 2 and value[1] == ":"
    return bool(scheme) and not is_windows_drive_path
