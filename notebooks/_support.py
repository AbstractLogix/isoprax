"""Small shared utilities for offline, verifier-backed notebooks."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from apps.evidence_workbench.datasets import (
    ChartProjection,
    DatasetVerification,
    _is_url,
    project_dataset_charts,
    required_dataset_path_fields,
    verify_local_dataset,
)


@dataclass(frozen=True)
class NotebookReview:
    """One verifier result and only the chart projections it authorizes."""

    verification: DatasetVerification
    charts: tuple[ChartProjection, ...]


def find_repo_root(start: Path, configured: str | None = None) -> Path:
    """Find the checkout root, honoring an explicit cross-environment override."""

    if configured:
        candidate = Path(configured).expanduser().resolve()
        if _is_repo_root(candidate):
            return candidate
        raise FileNotFoundError(
            f"ISOPRAX_REPO_ROOT is not a repository root: {candidate}"
        )

    initial = Path(start).expanduser().resolve()
    for candidate in (initial, *initial.parents):
        if _is_repo_root(candidate):
            return candidate
    raise FileNotFoundError(
        f"repository root not found above {initial}; set ISOPRAX_REPO_ROOT"
    )


def resolve_data_root(repo_root: Path, configured: str | None = None) -> Path:
    """Resolve the optional local data directory without assuming an OS path."""

    raw = (
        Path(configured).expanduser()
        if configured and configured.strip()
        else Path("data")
    )
    if not raw.is_absolute():
        raw = repo_root / raw
    return raw.resolve()


def data_root_from_environment(repo_root: Path) -> Path:
    """Resolve ISOPRAX_DATA_DIR, defaulting to the checkout's ignored data/ folder."""

    return resolve_data_root(repo_root, os.environ.get("ISOPRAX_DATA_DIR"))


def review_dataset(
    dataset_id: str,
    paths: Mapping[str, str | Path | None],
    repo_root: Path,
) -> NotebookReview:
    """Preflight local inputs, then reuse the workbench verifier and chart seams."""

    try:
        required_fields = required_dataset_path_fields(dataset_id)
    except ValueError as error:
        return NotebookReview(
            DatasetVerification(dataset_id, "unavailable", None, str(error)), ()
        )

    normalized = {
        key: str(value) if isinstance(value, Path) else value
        for key, value in paths.items()
    }
    missing: list[str] = []
    for field in required_fields:
        value = paths.get(field)
        if value is None or not str(value).strip():
            missing.append(f"{field}: path not configured")
            continue
        raw = str(value).strip()
        if _is_url(raw):
            return NotebookReview(
                DatasetVerification(
                    dataset_id,
                    "unavailable",
                    None,
                    f"{field} must be a local file path; URLs are not supported",
                ),
                (),
            )
        local_path = Path(raw).expanduser()
        if not local_path.is_absolute():
            local_path = repo_root / local_path
        local_path = local_path.resolve()
        if not local_path.is_file():
            missing.append(f"{field}: {local_path}")
        else:
            normalized[field] = str(local_path)

    if missing:
        return NotebookReview(
            DatasetVerification(
                dataset_id,
                "not_run",
                None,
                "Not run; configure existing local input(s): " + "; ".join(missing),
            ),
            (),
        )

    verification = verify_local_dataset(dataset_id, normalized, repo_root)
    return NotebookReview(verification, project_dataset_charts(verification))


def display_review(review: NotebookReview) -> int:
    """Render status, report, and authorized report-derived charts in a notebook."""

    from IPython.display import Markdown, display

    verification = review.verification
    display(Markdown(f"**Verification status:** `{verification.status}`"))
    if verification.message:
        display(Markdown(verification.message))
    if verification.report is not None:
        display(verification.report)
    if not review.charts:
        if verification.status not in {"verified", "verified_with_warnings"}:
            display(
                Markdown(
                    "No success chart is shown because no verified report is available."
                )
            )
        return 0

    import matplotlib.pyplot as plt

    for projection in review.charts:
        labels, values = zip(*projection.points, strict=True)
        figure, axis = plt.subplots(
            figsize=(9, max(3.0, 0.34 * len(labels))), constrained_layout=True
        )
        axis.barh(labels, values, color="#3178a8")
        axis.set_title(projection.title)
        axis.set_xlabel(projection.y_label)
        axis.set_ylabel(projection.x_label)
        axis.grid(axis="x", linestyle=":", alpha=0.35)
        display(figure)
        plt.close(figure)
    return len(review.charts)


def _is_repo_root(candidate: Path) -> bool:
    return (candidate / "pyproject.toml").is_file() and (candidate / "isoprax").is_dir()
