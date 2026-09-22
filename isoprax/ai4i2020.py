"""Offline provenance and structural checks for the AI4I 2020 CSV."""

from __future__ import annotations

import csv
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .commensurability import ObservationProcess, OutcomeDefinition, Threshold, Window
from .public_dataset import sha256_path, unique_errors

AI4I2020_COLUMNS = (
    "UDI",
    "Product ID",
    "Type",
    "Air temperature [K]",
    "Process temperature [K]",
    "Rotational speed [rpm]",
    "Torque [Nm]",
    "Tool wear [min]",
    "Machine failure",
    "TWF",
    "HDF",
    "PWF",
    "OSF",
    "RNF",
)
AI4I2020_IDENTIFIER_COLUMNS = ("UDI", "Product ID")
AI4I2020_FEATURE_COLUMNS = (
    "Type",
    "Air temperature [K]",
    "Process temperature [K]",
    "Rotational speed [rpm]",
    "Torque [Nm]",
    "Tool wear [min]",
)
AI4I2020_MODE_COLUMNS = ("TWF", "HDF", "PWF", "OSF", "RNF")
AI4I2020_LABEL_COLUMNS = ("Machine failure", *AI4I2020_MODE_COLUMNS)
AI4I2020_INTEGER_COLUMNS = ("UDI", "Rotational speed [rpm]", "Tool wear [min]")
AI4I2020_CLAIM_BOUNDARY = (
    "Public synthetic structural and label-semantics evidence only; not replay "
    "evidence, predictive efficacy, or Semantic/Full Conformance."
)
AI4I2020_EXPECTED_CSV_SHA256 = (
    "dc6630cd9b1f0f853922fad78a1b6436570d3f1ec863f1dd5c4340ac56bc8a8e"
)


@dataclass(frozen=True)
class AI4I2020Expectations:
    """Pinned values for the authoritative UCI CSV snapshot."""

    csv_sha256: str | None = AI4I2020_EXPECTED_CSV_SHA256
    row_count: int | None = 10_000
    column_count: int | None = 14
    machine_failure_count: int | None = 339
    mode_counts: tuple[tuple[str, int], ...] = (
        ("TWF", 46),
        ("HDF", 115),
        ("PWF", 95),
        ("OSF", 98),
        ("RNF", 19),
    )
    multi_mode_row_count: int | None = 24
    failure_without_mode_count: int | None = 9
    mode_without_failure_count: int | None = 18
    composite_mismatch_count: int | None = 27

    def __post_init__(self) -> None:
        if not self.csv_sha256 or not self.csv_sha256.strip():
            raise ValueError("csv_sha256 is required for fail-closed verification")
        object.__setattr__(self, "mode_counts", tuple(self.mode_counts))


AI4I2020_EXPECTATIONS = AI4I2020Expectations()


@dataclass(frozen=True)
class AI4I2020VerificationReport:
    """Deterministic verification output for one local CSV path."""

    path: str
    csv_sha256: str
    row_count: int
    column_count: int
    machine_failure_count: int
    mode_counts: tuple[tuple[str, int], ...]
    multi_mode_row_count: int
    failure_without_mode_count: int
    mode_without_failure_count: int
    composite_mismatch_count: int
    errors: tuple[str, ...] = ()
    claim_boundary: str = AI4I2020_CLAIM_BOUNDARY

    @property
    def verified(self) -> bool:
        return not self.errors

    @property
    def machine_failure_rate(self) -> float:
        return self.machine_failure_count / self.row_count if self.row_count else 0.0

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["verified"] = self.verified
        payload["machine_failure_rate"] = self.machine_failure_rate
        payload["mode_counts"] = dict(self.mode_counts)
        return payload


def verify_ai4i2020_csv(
    path: str | Path | None,
    *,
    expectations: AI4I2020Expectations = AI4I2020_EXPECTATIONS,
) -> AI4I2020VerificationReport:
    """Verify a local AI4I CSV, reporting an unavailable snapshot when absent."""

    if path is None:
        return _empty_report(
            None, ("external snapshot unavailable: no local CSV path provided",)
        )
    source = Path(path)
    if not source.is_file():
        return _empty_report(source, (f"source file does not exist: {source}",))

    try:
        csv_sha256 = sha256_path(source)
    except OSError as error:
        return _empty_report(source, (f"source file cannot be read: {error}",))

    errors: list[str] = []
    if csv_sha256 != expectations.csv_sha256:
        errors.append(
            f"csv_sha256 mismatch: expected {expectations.csv_sha256}, got {csv_sha256}"
        )

    row_count = 0
    column_count = 0
    machine_failure_count = 0
    mode_counts = {column: 0 for column in AI4I2020_MODE_COLUMNS}
    multi_mode_row_count = 0
    failure_without_mode_count = 0
    mode_without_failure_count = 0

    try:
        with source.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.reader(stream, strict=True)
            try:
                header = next(reader)
            except StopIteration:
                errors.append("CSV is empty")
            else:
                column_count = len(header)
                if tuple(header) != AI4I2020_COLUMNS:
                    errors.append(
                        "header mismatch: expected canonical AI4I 2020 columns"
                    )
                seen_udis: set[int] = set()
                for line_number, row in enumerate(reader, start=2):
                    row_count += 1
                    if len(row) != len(AI4I2020_COLUMNS):
                        errors.append(
                            f"row {line_number} has {len(row)} fields; expected "
                            f"{len(AI4I2020_COLUMNS)}"
                        )
                        continue
                    try:
                        udi, machine_failure, modes = _parse_row(row)
                    except ValueError as error:
                        errors.append(f"row {line_number}: {error}")
                        continue
                    if udi in seen_udis:
                        errors.append(f"row {line_number}: duplicate UDI {udi}")
                    seen_udis.add(udi)
                    machine_failure_count += machine_failure
                    for column, value in zip(AI4I2020_MODE_COLUMNS, modes):
                        mode_counts[column] += value
                    mode_total = sum(modes)
                    if mode_total > 1:
                        multi_mode_row_count += 1
                    if machine_failure and mode_total == 0:
                        failure_without_mode_count += 1
                    if not machine_failure and mode_total > 0:
                        mode_without_failure_count += 1
    except (OSError, UnicodeError, csv.Error) as error:
        errors.append(f"CSV parsing failed: {error}")

    composite_mismatch_count = failure_without_mode_count + mode_without_failure_count
    _compare_expectations(
        errors,
        expectations,
        csv_sha256=csv_sha256,
        row_count=row_count,
        column_count=column_count,
        machine_failure_count=machine_failure_count,
        mode_counts=tuple(mode_counts.items()),
        multi_mode_row_count=multi_mode_row_count,
        failure_without_mode_count=failure_without_mode_count,
        mode_without_failure_count=mode_without_failure_count,
        composite_mismatch_count=composite_mismatch_count,
    )
    return AI4I2020VerificationReport(
        path=str(source),
        csv_sha256=csv_sha256,
        row_count=row_count,
        column_count=column_count,
        machine_failure_count=machine_failure_count,
        mode_counts=tuple(mode_counts.items()),
        multi_mode_row_count=multi_mode_row_count,
        failure_without_mode_count=failure_without_mode_count,
        mode_without_failure_count=mode_without_failure_count,
        composite_mismatch_count=composite_mismatch_count,
        errors=unique_errors(errors),
    )


def ai4i2020_outcome_definitions() -> dict[str, OutcomeDefinition]:
    """Return separate current-cycle definitions for all AI4I labels."""

    events = {
        "Machine failure": "machine failure during current process cycle",
        "TWF": "tool wear failure during current process cycle",
        "HDF": "heat dissipation failure during current process cycle",
        "PWF": "power failure during current process cycle",
        "OSF": "overstrain failure during current process cycle",
        "RNF": "random failure during current process cycle",
    }
    process = ObservationProcess(
        "ai4i2020 sensor snapshot",
        parameters=(
            ("dataset", "ai4i2020"),
            ("scope", "current process cycle"),
        ),
    )
    window = Window(1, "process_cycle", "sensor_snapshot")
    definitions: dict[str, OutcomeDefinition] = {}
    for label, event in events.items():
        identifier = label.lower().replace(" ", "_")
        definitions[label] = OutcomeDefinition(
            id=f"ai4i2020.{identifier}.v1",
            event=event,
            observation_process=process,
            window=window,
            thresholds=(Threshold(identifier, "=", 1),),
            description="AI4I 2020 synthetic structural fixture outcome.",
        )
    return definitions


def _parse_row(row: list[str]) -> tuple[int, int, tuple[int, ...]]:
    try:
        udi = int(row[0])
    except ValueError as error:
        raise ValueError("UDI must be an integer") from error
    if udi <= 0:
        raise ValueError("UDI must be positive")
    product_id = row[1]
    if re.fullmatch(r"[LMH]\d{5}", product_id) is None:
        raise ValueError("Product ID must match [LMH] followed by five digits")
    if row[2] not in {"L", "M", "H"}:
        raise ValueError("product type must be L, M, or H")

    for column in AI4I2020_COLUMNS[3:8]:
        value = row[AI4I2020_COLUMNS.index(column)]
        try:
            numeric = float(value)
        except ValueError as error:
            raise ValueError(f"{column} must be numeric") from error
        if not math.isfinite(numeric):
            raise ValueError(f"{column} must be finite")
        if column in AI4I2020_INTEGER_COLUMNS and not numeric.is_integer():
            raise ValueError(f"{column} must be an integer")

    labels: list[int] = []
    for column in AI4I2020_LABEL_COLUMNS:
        value = row[AI4I2020_COLUMNS.index(column)]
        if value not in {"0", "1"}:
            raise ValueError(f"{column} label must be binary 0/1")
        labels.append(int(value))
    return udi, labels[0], tuple(labels[1:])


def _empty_report(
    path: Path | None, errors: tuple[str, ...]
) -> AI4I2020VerificationReport:
    return AI4I2020VerificationReport(
        path=str(path) if path is not None else "",
        csv_sha256="",
        row_count=0,
        column_count=0,
        machine_failure_count=0,
        mode_counts=tuple((column, 0) for column in AI4I2020_MODE_COLUMNS),
        multi_mode_row_count=0,
        failure_without_mode_count=0,
        mode_without_failure_count=0,
        composite_mismatch_count=0,
        errors=errors,
    )


def _compare_expectations(
    errors: list[str],
    expectations: AI4I2020Expectations,
    **actual: object,
) -> None:
    expected_values = {
        "csv_sha256": expectations.csv_sha256,
        "row_count": expectations.row_count,
        "column_count": expectations.column_count,
        "machine_failure_count": expectations.machine_failure_count,
        "mode_counts": expectations.mode_counts,
        "multi_mode_row_count": expectations.multi_mode_row_count,
        "failure_without_mode_count": expectations.failure_without_mode_count,
        "mode_without_failure_count": expectations.mode_without_failure_count,
        "composite_mismatch_count": expectations.composite_mismatch_count,
    }
    for name, expected in expected_values.items():
        if expected is not None and actual[name] != expected:
            errors.append(f"{name} mismatch: expected {expected}, got {actual[name]}")


__all__ = [
    "AI4I2020_CLAIM_BOUNDARY",
    "AI4I2020_COLUMNS",
    "AI4I2020_EXPECTATIONS",
    "AI4I2020_EXPECTED_CSV_SHA256",
    "AI4I2020_FEATURE_COLUMNS",
    "AI4I2020_IDENTIFIER_COLUMNS",
    "AI4I2020_LABEL_COLUMNS",
    "AI4I2020_MODE_COLUMNS",
    "AI4I2020Expectations",
    "AI4I2020VerificationReport",
    "ai4i2020_outcome_definitions",
    "verify_ai4i2020_csv",
]
