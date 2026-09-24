"""Offline verification for MetroPT-3 observations and external failure anchors."""

from __future__ import annotations

import csv
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from .commensurability import ObservationProcess, OutcomeDefinition, Threshold, Window
from .public_dataset import sha256_path, unique_errors

METROPT3_COLUMNS = (
    "",
    "timestamp",
    "TP2",
    "TP3",
    "H1",
    "DV_pressure",
    "Reservoirs",
    "Oil_temperature",
    "Motor_current",
    "COMP",
    "DV_eletric",
    "Towers",
    "MPG",
    "LPS",
    "Pressure_switch",
    "Oil_level",
    "Caudal_impulses",
)
METROPT3_EXPECTED_SHA256 = (
    "db30ccb4ea402e3c8bf2c99db06e288d4f2a772f6928f9dbe26a920d69793e24"
)
METROPT3_CLAIM_BOUNDARY = (
    "External-anchor-dependent single-compressor observation evidence only; "
    "unanchored rows are censored and no predictive efficacy or Semantic/Full "
    "Conformance claim is made."
)
METROPT3_EXPECTED_INTERVAL_ROWS = {
    "F1": 8657,
    "F2": 2360,
    "F3": 17315,
    "F4": 1622,
}


@dataclass(frozen=True)
class MetroPT3FailureInterval:
    """Source-reported interval without an assumed timezone."""

    anchor_id: str
    start: datetime
    end: datetime
    source_reference: str

    def __post_init__(self) -> None:
        _require_timezone_naive(self.start, "failure interval start")
        _require_timezone_naive(self.end, "failure interval end")


@dataclass(frozen=True)
class MetroPT3Expectations:
    sha256: str | None = METROPT3_EXPECTED_SHA256
    row_count: int | None = 1_516_948
    column_count: int | None = 17
    expected_interval_rows: tuple[tuple[str, int], ...] | None = tuple(
        METROPT3_EXPECTED_INTERVAL_ROWS.items()
    )


METROPT3_EXPECTATIONS = MetroPT3Expectations()


@dataclass(frozen=True)
class MetroPT3VerificationReport:
    path: str
    sha256: str
    row_count: int
    column_count: int
    unique_row_ids: int
    unique_timestamps: int
    monotonic: bool
    interval_coverage: tuple[tuple[str, int], ...]
    gap_counts_seconds: tuple[tuple[float, int], ...]
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    claim_boundary: str = METROPT3_CLAIM_BOUNDARY

    @property
    def verified(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["verified"] = self.verified
        payload["dataset_id"] = "metropt3"
        payload["artifact"] = {"path": self.path, "sha256": self.sha256}
        payload["interval_coverage"] = dict(self.interval_coverage)
        payload["gap_counts_seconds"] = dict(self.gap_counts_seconds)
        payload["observed"] = {
            "row_count": self.row_count,
            "column_count": self.column_count,
            "unique_row_ids": self.unique_row_ids,
            "unique_timestamps": self.unique_timestamps,
            "monotonic": self.monotonic,
        }
        payload["diagnostics"] = {
            "interval_coverage": dict(self.interval_coverage),
            "gap_counts_seconds": dict(self.gap_counts_seconds),
        }
        return payload


def verify_metropt3_csv(
    path: str | Path,
    intervals: Iterable[MetroPT3FailureInterval] | None,
    *,
    expectations: MetroPT3Expectations = METROPT3_EXPECTATIONS,
) -> MetroPT3VerificationReport:
    source = Path(path)
    if not source.is_file():
        return _empty_report(source, (f"source file does not exist: {source}",))
    try:
        digest = sha256_path(source)
    except OSError as error:
        return _empty_report(source, (f"source file cannot be read: {error}",))
    errors: list[str] = []
    if expectations.sha256 is not None and digest != expectations.sha256:
        errors.append(f"sha256 mismatch: expected {expectations.sha256}, got {digest}")
    anchors = tuple(intervals or ())
    errors.extend(_validate_intervals(anchors))
    row_count = column_count = 0
    row_ids: set[str] = set()
    timestamps: set[datetime] = set()
    previous: datetime | None = None
    monotonic = True
    gaps: dict[float, int] = {}
    coverage: dict[str, int] = {}
    coverage_intervals: list[MetroPT3FailureInterval] = []
    for interval in anchors:
        anchor_id = interval.anchor_id
        if isinstance(anchor_id, str) and anchor_id and anchor_id == anchor_id.strip():
            if anchor_id not in coverage:
                coverage[anchor_id] = 0
                coverage_intervals.append(interval)
    try:
        with source.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.reader(stream, strict=True)
            try:
                header = next(reader)
            except StopIteration:
                errors.append("CSV is empty")
            else:
                column_count = len(header)
                if tuple(header) != METROPT3_COLUMNS:
                    errors.append(
                        "header mismatch: expected canonical MetroPT-3 columns"
                    )
                for line_number, row in enumerate(reader, start=2):
                    row_count += 1
                    if len(row) != len(METROPT3_COLUMNS):
                        errors.append(
                            f"row {line_number} has {len(row)} fields; expected {len(METROPT3_COLUMNS)}"
                        )
                        continue
                    try:
                        row_id = row[0].strip()
                        timestamp = datetime.fromisoformat(
                            row[1].strip().replace("Z", "+00:00")
                        )
                        _require_timezone_naive(timestamp, "CSV timestamp")
                        if not row_id:
                            raise ValueError("row identifier is required")
                        for column, value in zip(METROPT3_COLUMNS[2:], row[2:]):
                            number = float(value)
                            if not math.isfinite(number):
                                raise ValueError(f"{column} must be finite")
                    except (TypeError, ValueError) as error:
                        errors.append(f"row {line_number}: {error}")
                        continue
                    if row_id in row_ids:
                        errors.append(
                            f"row {line_number}: duplicate row identifier {row_id}"
                        )
                    if timestamp in timestamps:
                        errors.append(
                            f"row {line_number}: duplicate timestamp {timestamp.isoformat()}"
                        )
                    row_ids.add(row_id)
                    timestamps.add(timestamp)
                    if previous is not None:
                        delta = (timestamp - previous).total_seconds()
                        if delta < 0:
                            monotonic = False
                            errors.append(
                                f"row {line_number}: timestamps are not monotonic"
                            )
                        else:
                            gaps[delta] = gaps.get(delta, 0) + 1
                    previous = timestamp
                    for interval in coverage_intervals:
                        anchor_id = interval.anchor_id
                        if (
                            isinstance(anchor_id, str)
                            and anchor_id in coverage
                            and interval.start <= timestamp <= interval.end
                        ):
                            coverage[anchor_id] += 1
    except (OSError, UnicodeError, csv.Error) as error:
        errors.append(f"CSV parsing failed: {error}")
    if not anchors:
        errors.append(
            "external failure interval anchors are required; no negatives inferred"
        )
    if expectations.row_count is not None and row_count != expectations.row_count:
        errors.append(
            f"row_count mismatch: expected {expectations.row_count}, got {row_count}"
        )
    if (
        expectations.column_count is not None
        and column_count != expectations.column_count
    ):
        errors.append(
            f"column_count mismatch: expected {expectations.column_count}, got {column_count}"
        )
    if expectations.expected_interval_rows is not None:
        for anchor_id, expected_count in expectations.expected_interval_rows:
            actual = coverage.get(anchor_id)
            if actual != expected_count:
                errors.append(
                    f"interval {anchor_id} coverage mismatch: expected {expected_count}, got {actual}"
                )
    warnings = (
        ("timestamp cadence is reported as observed; it is not normalized",)
        if gaps
        else ()
    )
    return MetroPT3VerificationReport(
        str(source),
        digest,
        row_count,
        column_count,
        len(row_ids),
        len(timestamps),
        monotonic,
        tuple(sorted(coverage.items())),
        tuple(sorted(gaps.items())),
        unique_errors(errors),
        warnings,
    )


def metropt3_outcome_definition() -> OutcomeDefinition:
    return OutcomeDefinition(
        "metropt3.external_air_leak.v1",
        "air leak reported by an external maintenance interval",
        ObservationProcess(
            "metropt3 compressor stream",
            parameters=(("dataset", "metropt3"), ("anchor", "external_report")),
        ),
        Window(None, "reported_interval", "external_anchor"),
        (Threshold("external_failure_interval", "=", 1),),
        "Positive coverage is limited to explicit externally reported air-leak intervals; other rows are censored.",
    )


def read_metropt3_intervals(
    path: str | Path,
) -> tuple[MetroPT3FailureInterval, ...]:
    """Read the explicit, timezone-unqualified external interval manifest."""

    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("interval manifest must be a JSON list")
    required_fields = ("anchor_id", "start", "end", "source_reference")
    intervals: list[MetroPT3FailureInterval] = []
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("each interval must be a JSON object")
        missing_fields = tuple(field for field in required_fields if field not in item)
        if missing_fields:
            raise ValueError(
                f"interval is missing required fields: {', '.join(missing_fields)}"
            )
        for field in required_fields:
            if not isinstance(item[field], str):
                raise ValueError(f"interval field {field} must be a string")
        intervals.append(
            MetroPT3FailureInterval(
                item["anchor_id"],
                datetime.fromisoformat(item["start"].replace("Z", "+00:00")),
                datetime.fromisoformat(item["end"].replace("Z", "+00:00")),
                item["source_reference"],
            )
        )
    return tuple(intervals)


def _require_timezone_naive(value: datetime, field: str) -> None:
    if value.tzinfo is not None and value.utcoffset() is not None:
        raise ValueError(
            f"{field} must be timezone-naive; the UCI source does not specify a timezone"
        )


def _validate_intervals(
    intervals: tuple[MetroPT3FailureInterval, ...],
) -> tuple[str, ...]:
    errors: list[str] = []
    seen: set[str] = set()
    for interval in intervals:
        anchor_id = interval.anchor_id
        if not isinstance(anchor_id, str):
            errors.append("failure interval anchor_id must be a string")
        else:
            canonical_id = anchor_id.strip()
            if not canonical_id:
                errors.append("failure interval anchor_id is required")
            else:
                if anchor_id != canonical_id:
                    errors.append(
                        "failure interval anchor_id must not contain surrounding whitespace"
                    )
                if canonical_id in seen:
                    errors.append(
                        f"duplicate failure interval anchor_id {canonical_id}"
                    )
                seen.add(canonical_id)
        if interval.start > interval.end:
            errors.append(f"failure interval {interval.anchor_id} start is after end")
        if (
            not isinstance(interval.source_reference, str)
            or not interval.source_reference.strip()
        ):
            errors.append(
                f"failure interval {interval.anchor_id} source_reference is required"
            )
    return unique_errors(errors)


def _empty_report(path: Path, errors: tuple[str, ...]) -> MetroPT3VerificationReport:
    return MetroPT3VerificationReport(str(path), "", 0, 0, 0, 0, False, (), (), errors)
