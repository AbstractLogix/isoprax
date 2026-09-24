from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

import numpy as np
import pytest

from isoprax.ai4i2020 import (
    AI4I2020_FEATURE_COLUMNS,
    AI4I2020_IDENTIFIER_COLUMNS,
    AI4I2020_LABEL_COLUMNS,
)
from isoprax.apachejit import APACHEJIT_COLUMNS
from isoprax.metropt3 import MetroPT3FailureInterval
from notebooks import _analysis


def test_model_feature_lists_exclude_identifiers_and_outcome_leakage() -> None:
    assert set(_analysis.AI4I_MODEL_FEATURES) == set(AI4I2020_FEATURE_COLUMNS)
    assert not set(_analysis.AI4I_MODEL_FEATURES) & set(AI4I2020_IDENTIFIER_COLUMNS)
    assert not set(_analysis.AI4I_MODEL_FEATURES) & set(AI4I2020_LABEL_COLUMNS)

    assert set(_analysis.APACHEJIT_MODEL_FEATURES) == {
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
    }
    assert set(_analysis.APACHEJIT_MODEL_FEATURES) <= set(APACHEJIT_COLUMNS)
    assert not set(_analysis.APACHEJIT_MODEL_FEATURES) & {
        "commit_id",
        "project",
        "buggy",
        "fix",
        "year",
        "author_date",
    }


def test_ordered_holdout_sorts_by_identifier_and_keeps_groups_in_one_partition() -> (
    None
):
    values = np.asarray([5, 2, 4, 1, 3])

    train, test = _analysis.ordered_holdout_indices(values, train_fraction=0.6)

    assert values[train].tolist() == [1, 2, 3]
    assert values[test].tolist() == [4, 5]
    assert set(train).isdisjoint(test)


def test_ordered_holdout_rejects_invalid_fraction_and_duplicate_order_keys() -> None:
    with pytest.raises(ValueError, match="train_fraction"):
        _analysis.ordered_holdout_indices(np.arange(4), train_fraction=1.0)
    with pytest.raises(ValueError, match="unique"):
        _analysis.ordered_holdout_indices(np.asarray([1, 2, 2, 4]))


def test_timestamp_holdout_uses_strict_cutoff_and_never_splits_equal_timestamps() -> (
    None
):
    timestamps = np.asarray([20, 10, 30, 20, 40], dtype=np.int64)

    train, test = _analysis.timestamp_holdout_indices(timestamps, cutoff=30)

    assert timestamps[train].tolist() == [20, 10, 20]
    assert timestamps[test].tolist() == [30, 40]
    assert set(train).isdisjoint(test)


def test_binary_metrics_reports_scores_and_fixed_threshold_counts() -> None:
    report = _analysis.binary_classification_metrics(
        np.asarray([0, 0, 1, 1]),
        np.asarray([0.1, 0.6, 0.4, 0.9]),
        threshold=0.5,
    )

    assert report["n"] == 4
    assert report["positive_count"] == 2
    assert report["prevalence"] == 0.5
    assert report["average_precision"] == pytest.approx(5 / 6)
    assert report["roc_auc"] == pytest.approx(0.75)
    assert report["brier_score"] == pytest.approx(0.185)
    assert (report["tn"], report["fp"], report["fn"], report["tp"]) == (1, 1, 1, 1)


def test_binary_metrics_marks_unsupported_class_metrics_not_estimable() -> None:
    report = _analysis.binary_classification_metrics(
        np.asarray([0, 0, 0]), np.asarray([0.1, 0.2, 0.3])
    )

    assert report["average_precision"] is None
    assert (
        report["average_precision_reason"] == "test partition has no positive examples"
    )
    assert report["roc_auc"] is None
    assert report["roc_auc_reason"] == "test partition contains only one class"
    assert report["brier_score"] == pytest.approx((0.01 + 0.04 + 0.09) / 3)


def test_cmapss_training_rul_is_derived_within_each_engine() -> None:
    unit_ids = np.asarray([1, 1, 1, 2, 2])
    cycles = np.asarray([1, 2, 4, 1, 3])

    assert _analysis.derive_cmapss_training_rul(unit_ids, cycles).tolist() == [
        3,
        2,
        0,
        2,
        0,
    ]


def test_cmapss_test_rul_aligns_to_final_rows_in_first_seen_unit_order() -> None:
    unit_ids = np.asarray([2, 1, 2, 1, 3, 3])
    cycles = np.asarray([1, 1, 3, 4, 1, 2])
    rul = np.asarray([11, 22, 33])

    final_indices, aligned_rul = _analysis.align_cmapss_test_rul(unit_ids, cycles, rul)

    assert final_indices.tolist() == [2, 3, 5]
    assert aligned_rul.tolist() == [11, 22, 33]
    with pytest.raises(ValueError, match="one value per test unit"):
        _analysis.align_cmapss_test_rul(unit_ids, cycles, rul[:2])


def test_regression_metrics_reports_mae_rmse_and_support() -> None:
    report = _analysis.regression_metrics(np.asarray([1, 3]), np.asarray([2, 5]))

    assert report == {"n": 2, "mae": 1.5, "rmse": pytest.approx(2.5**0.5)}


def test_metropt3_chunk_summary_is_weighted_and_contains_only_anchor_context(
    tmp_path: Path,
) -> None:
    pytest.importorskip("pandas")
    path = tmp_path / "metro.csv"
    fields = ("timestamp", "TP2", "TP3", "Motor_current", "DV_pressure")
    rows = [
        ("2020-04-18 00:00:00", 2, 4, 2, 0),
        ("2020-04-18 00:00:30", 4, 6, 4, 0),
        ("2020-04-18 00:01:00", 6, 8, 6, 1),
        ("2020-04-18 02:00:00", 8, 10, 8, 1),
    ]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(fields)
        writer.writerows(rows)
    anchor = MetroPT3FailureInterval(
        "F1",
        datetime(2020, 4, 18, 0, 0),
        datetime(2020, 4, 18, 0, 1),
        "fixture",
    )

    views = _analysis.read_metropt3_views(
        path,
        (anchor,),
        chunksize=1,
        window_margin_seconds=3 * 60 * 60,
    )

    assert views.hourly.loc[datetime(2020, 4, 18, 0), "TP2"] == pytest.approx(4)
    assert views.hourly.loc[datetime(2020, 4, 18, 2), "TP2"] == pytest.approx(8)
    assert views.interval_minutes["F1"].loc[
        datetime(2020, 4, 18, 0), "TP2"
    ] == pytest.approx(3)
    assert "label" not in views.hourly.columns
    assert set(views.interval_minutes) == {"F1"}
