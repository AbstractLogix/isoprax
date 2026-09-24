"""Deterministic, notebook-only analysis primitives for verified local corpora."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

from isoprax.ai4i2020 import AI4I2020_FEATURE_COLUMNS
from isoprax.metropt3 import MetroPT3FailureInterval

AI4I_MODEL_FEATURES = AI4I2020_FEATURE_COLUMNS
APACHEJIT_MODEL_FEATURES = (
    "la",
    "ld",
    "nf",
    "nd",
    "ns",
    "ent",
    "ndev",
    "age",
    "nuc",
    "aexp",
    "arexp",
    "asexp",
)
CMAPSS_COLUMNS = (
    "unit_number",
    "cycle",
    "setting_1",
    "setting_2",
    "setting_3",
    *(f"sensor_{index}" for index in range(1, 22)),
)
CMAPSS_MODEL_FEATURES = CMAPSS_COLUMNS[1:]


@dataclass(frozen=True)
class MetroPT3Views:
    """Chunk-reduced sensor means; interval views contain no inferred labels."""

    hourly: Any
    interval_minutes: dict[str, Any]


def ordered_holdout_indices(
    order_values: Iterable[int | float], *, train_fraction: float = 0.8
) -> tuple[np.ndarray, np.ndarray]:
    """Split a unique ordered key without mixing earlier/later observations."""

    values = np.asarray(tuple(order_values), dtype=float)
    if values.ndim != 1 or len(values) < 2 or not np.isfinite(values).all():
        raise ValueError("order_values must contain at least two finite values")
    if not 0.0 < train_fraction < 1.0:
        raise ValueError("train_fraction must be strictly between zero and one")
    if len(np.unique(values)) != len(values):
        raise ValueError("order_values must be unique")

    sorted_indices = np.argsort(values, kind="stable")
    split_at = min(max(int(len(values) * train_fraction), 1), len(values) - 1)
    return sorted_indices[:split_at], sorted_indices[split_at:]


def timestamp_holdout_indices(
    timestamps: Iterable[int | float], *, cutoff: int | float
) -> tuple[np.ndarray, np.ndarray]:
    """Place all equal timestamps on one side of a deterministic UTC cutoff."""

    values = np.asarray(tuple(timestamps), dtype=float)
    if values.ndim != 1 or len(values) < 2 or not np.isfinite(values).all():
        raise ValueError("timestamps must contain at least two finite values")
    if not np.isfinite(cutoff):
        raise ValueError("cutoff must be finite")

    train_indices = np.flatnonzero(values < cutoff)
    test_indices = np.flatnonzero(values >= cutoff)
    if not len(train_indices) or not len(test_indices):
        raise ValueError("cutoff must leave rows in both train and test partitions")
    return train_indices, test_indices


def binary_classification_metrics(
    outcomes: Iterable[int],
    probabilities: Iterable[float],
    *,
    threshold: float = 0.5,
) -> dict[str, int | float | None | str]:
    """Return support-aware binary scores and one prespecified confusion table."""

    y_true = np.asarray(tuple(outcomes))
    y_score = np.asarray(tuple(probabilities), dtype=float)
    if y_true.ndim != 1 or y_score.ndim != 1 or len(y_true) != len(y_score):
        raise ValueError("outcomes and probabilities must be equal-length vectors")
    if not len(y_true):
        raise ValueError("classification metrics require at least one test row")
    if set(np.unique(y_true).tolist()) - {0, 1}:
        raise ValueError("outcomes must be binary values 0 or 1")
    if not np.isfinite(y_score).all() or (y_score < 0).any() or (y_score > 1).any():
        raise ValueError("probabilities must be finite values between zero and one")
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between zero and one")

    y_true = y_true.astype(np.int8, copy=False)
    positive_count = int(y_true.sum())
    negative_count = len(y_true) - positive_count
    prediction = y_score >= threshold
    actual = y_true == 1
    both_classes = positive_count > 0 and negative_count > 0

    return {
        "n": len(y_true),
        "positive_count": positive_count,
        "negative_count": negative_count,
        "prevalence": positive_count / len(y_true),
        "average_precision": (
            float(average_precision_score(y_true, y_score)) if positive_count else None
        ),
        "average_precision_reason": (
            None if positive_count else "test partition has no positive examples"
        ),
        "roc_auc": float(roc_auc_score(y_true, y_score)) if both_classes else None,
        "roc_auc_reason": (
            None if both_classes else "test partition contains only one class"
        ),
        "brier_score": float(brier_score_loss(y_true, y_score)),
        "threshold": float(threshold),
        "tn": int((~actual & ~prediction).sum()),
        "fp": int((~actual & prediction).sum()),
        "fn": int((actual & ~prediction).sum()),
        "tp": int((actual & prediction).sum()),
    }


def derive_cmapss_training_rul(
    unit_ids: Iterable[int], cycles: Iterable[int]
) -> np.ndarray:
    """Derive per-row training RUL from each run-to-failure unit's last cycle."""

    units = np.asarray(tuple(unit_ids))
    cycle_values = np.asarray(tuple(cycles), dtype=float)
    if units.ndim != 1 or cycle_values.ndim != 1 or len(units) != len(cycle_values):
        raise ValueError("unit_ids and cycles must be equal-length vectors")
    if not len(units) or not np.isfinite(cycle_values).all():
        raise ValueError("training trajectories must contain finite cycle values")
    if (cycle_values < 0).any():
        raise ValueError("cycle values must be non-negative")

    last_cycle_by_unit = {
        unit: float(cycle_values[units == unit].max()) for unit in np.unique(units)
    }
    return np.asarray(
        [last_cycle_by_unit[unit] - cycle for unit, cycle in zip(units, cycle_values)],
        dtype=float,
    )


def align_cmapss_test_rul(
    unit_ids: Iterable[int],
    cycles: Iterable[int],
    official_rul: Iterable[int | float],
) -> tuple[np.ndarray, np.ndarray]:
    """Pair each official RUL value with that unit's final row in first-seen order."""

    units = np.asarray(tuple(unit_ids))
    cycle_values = np.asarray(tuple(cycles), dtype=float)
    targets = np.asarray(tuple(official_rul), dtype=float)
    if units.ndim != 1 or cycle_values.ndim != 1 or len(units) != len(cycle_values):
        raise ValueError("unit_ids and cycles must be equal-length vectors")
    if not len(units) or not np.isfinite(cycle_values).all():
        raise ValueError("test trajectories must contain finite cycle values")
    if not np.isfinite(targets).all() or (targets < 0).any():
        raise ValueError("official RUL values must be finite and non-negative")

    unit_order = list(dict.fromkeys(units.tolist()))
    if len(targets) != len(unit_order):
        raise ValueError("official RUL requires one value per test unit")

    final_indices: list[int] = []
    for unit in unit_order:
        indices = np.flatnonzero(units == unit)
        maximum_cycle = cycle_values[indices].max()
        final_rows = indices[cycle_values[indices] == maximum_cycle]
        if len(final_rows) != 1:
            raise ValueError(f"test unit {unit} has duplicate final-cycle rows")
        final_indices.append(int(final_rows[0]))
    return np.asarray(final_indices, dtype=int), targets


def regression_metrics(
    outcomes: Iterable[int | float], predictions: Iterable[int | float]
) -> dict[str, int | float]:
    """Return MAE/RMSE and test support for a numeric held-out target."""

    actual = np.asarray(tuple(outcomes), dtype=float)
    predicted = np.asarray(tuple(predictions), dtype=float)
    if actual.ndim != 1 or predicted.ndim != 1 or len(actual) != len(predicted):
        raise ValueError("outcomes and predictions must be equal-length vectors")
    if (
        not len(actual)
        or not np.isfinite(actual).all()
        or not np.isfinite(predicted).all()
    ):
        raise ValueError("regression metrics require finite non-empty vectors")
    errors = predicted - actual
    return {
        "n": len(actual),
        "mae": float(np.abs(errors).mean()),
        "rmse": float(np.sqrt(np.square(errors).mean())),
    }


def read_metropt3_views(
    path: str | Path,
    intervals: Iterable[MetroPT3FailureInterval],
    *,
    sensor_columns: tuple[str, ...] = (
        "TP2",
        "TP3",
        "Motor_current",
        "DV_pressure",
    ),
    chunksize: int = 100_000,
    window_margin_seconds: int = 21_600,
) -> MetroPT3Views:
    """Stream MetroPT-3, returning count-weighted hourly and anchor-minute means.

    Only timestamps, selected sensor columns, and time-bin aggregates are retained.
    No outcome column is created: timestamps outside source intervals stay censored.
    """

    import pandas as pd

    source = Path(path)
    anchors = tuple(intervals)
    if chunksize < 1:
        raise ValueError("chunksize must be positive")
    if window_margin_seconds < 0:
        raise ValueError("window_margin_seconds must be non-negative")
    if len({anchor.anchor_id for anchor in anchors}) != len(anchors):
        raise ValueError("anchor ids must be unique")

    selected_columns = ("timestamp", *sensor_columns)
    hourly_sums: list[Any] = []
    hourly_counts: list[Any] = []
    minute_sums: dict[str, list[Any]] = {anchor.anchor_id: [] for anchor in anchors}
    minute_counts: dict[str, list[Any]] = {anchor.anchor_id: [] for anchor in anchors}

    for frame in pd.read_csv(
        source, usecols=list(selected_columns), chunksize=chunksize
    ):
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="raise")
        for column in sensor_columns:
            frame[column] = pd.to_numeric(frame[column], errors="raise")

        hour_bins = frame["timestamp"].dt.floor("h")
        hourly_sums.append(frame[list(sensor_columns)].groupby(hour_bins).sum())
        hourly_counts.append(frame[list(sensor_columns)].groupby(hour_bins).count())

        for anchor in anchors:
            start = pd.Timestamp(anchor.start) - pd.Timedelta(
                seconds=window_margin_seconds
            )
            end = pd.Timestamp(anchor.end) + pd.Timedelta(seconds=window_margin_seconds)
            in_window = frame.loc[
                frame["timestamp"].between(start, end, inclusive="both")
            ]
            if in_window.empty:
                continue
            minute_bins = in_window["timestamp"].dt.floor("min")
            minute_sums[anchor.anchor_id].append(
                in_window[list(sensor_columns)].groupby(minute_bins).sum()
            )
            minute_counts[anchor.anchor_id].append(
                in_window[list(sensor_columns)].groupby(minute_bins).count()
            )

    hourly = _combine_time_bin_parts(hourly_sums, hourly_counts, "hourly")
    anchor_views = {
        anchor.anchor_id: _combine_time_bin_parts(
            minute_sums[anchor.anchor_id],
            minute_counts[anchor.anchor_id],
            f"anchor {anchor.anchor_id}",
        )
        for anchor in anchors
    }
    return MetroPT3Views(hourly, anchor_views)


def _combine_time_bin_parts(
    sums: list[Any], counts: list[Any], description: str
) -> Any:
    import pandas as pd

    if not sums:
        if description.startswith("anchor "):
            return pd.DataFrame()
        raise ValueError("MetroPT-3 contains no timestamped rows")
    total_sum = pd.concat(sums).groupby(level=0, sort=True).sum()
    total_count = pd.concat(counts).groupby(level=0, sort=True).sum()
    result = total_sum.div(total_count)
    result.index.name = "timestamp"
    return result
