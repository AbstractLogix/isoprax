"""Offline verification and outcome definitions for the ApacheJIT snapshot."""

from __future__ import annotations

import csv
import math
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .commensurability import ObservationProcess, OutcomeDefinition, Threshold, Window
from .public_dataset import sha256_path, unique_errors

APACHEJIT_COLUMNS = (
    "commit_id",
    "project",
    "buggy",
    "fix",
    "year",
    "author_date",
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
APACHEJIT_EXPECTED_SHA256 = (
    "5097cbbbab8c4611a709b3cf95ac5c9fe5f62e619bab081911a2a247ddbed4e0"
)
APACHEJIT_CLAIM_BOUNDARY = (
    "Repository-derived JIT label evidence only; not an observed runtime failure, "
    "predictive efficacy, or Semantic/Full Conformance claim."
)
_HEX_COMMIT = re.compile(r"^[0-9a-fA-F]{40}$")
_APACHEJIT_PROJECT_COUNTS = (
    ("apache/camel", 22700),
    ("apache/ignite", 12036),
    ("apache/hadoop", 11964),
    ("apache/flink", 11691),
    ("apache/hbase", 8730),
    ("apache/cassandra", 8159),
    ("apache/groovy", 8059),
    ("apache/hive", 6842),
    ("apache/activemq", 6126),
    ("apache/hadoop-hdfs", 2907),
    ("apache/kafka", 2384),
    ("apache/spark", 1465),
    ("apache/zeppelin", 1451),
    ("apache/hadoop-mapreduce", 1321),
    ("apache/zookeeper", 839),
)


@dataclass(frozen=True)
class ApacheJITExpectations:
    sha256: str | None = APACHEJIT_EXPECTED_SHA256
    row_count: int | None = 106_674
    column_count: int | None = 18
    project_count: int | None = 15
    unique_commit_count: int | None = 106_674
    buggy_count: int | None = 28_239
    clean_count: int | None = 78_435
    timestamp_inversion_count: int | None = 53_487
    year_epoch_mismatch_count: int | None = 1_314
    project_counts: tuple[tuple[str, int], ...] | None = _APACHEJIT_PROJECT_COUNTS


APACHEJIT_EXPECTATIONS = ApacheJITExpectations()


@dataclass(frozen=True)
class ApacheJITVerificationReport:
    path: str
    sha256: str
    row_count: int
    column_count: int
    unique_commit_count: int
    project_count: int
    project_counts: tuple[tuple[str, int], ...]
    project_buggy_counts: tuple[tuple[str, int], ...]
    buggy_count: int
    clean_count: int
    timestamp_inversion_count: int
    year_epoch_mismatch_count: int
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    claim_boundary: str = APACHEJIT_CLAIM_BOUNDARY
    project_positive_yield: tuple[tuple[str, float], ...] = ()

    @property
    def verified(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["verified"] = self.verified
        payload["dataset_id"] = "apachejit"
        payload["artifact"] = {"path": self.path, "sha256": self.sha256}
        payload["project_counts"] = dict(self.project_counts)
        payload["project_buggy_counts"] = dict(self.project_buggy_counts)
        payload["project_positive_yield"] = dict(self.project_positive_yield)
        payload["observed"] = {
            "row_count": self.row_count,
            "column_count": self.column_count,
            "unique_commit_count": self.unique_commit_count,
            "project_count": self.project_count,
            "buggy_count": self.buggy_count,
            "clean_count": self.clean_count,
        }
        payload["diagnostics"] = {
            "timestamp_inversion_count": self.timestamp_inversion_count,
            "year_epoch_mismatch_count": self.year_epoch_mismatch_count,
            "project_counts": dict(self.project_counts),
            "project_buggy_counts": dict(self.project_buggy_counts),
            "project_positive_yield": dict(self.project_positive_yield),
        }
        return payload


def verify_apachejit_csv(
    path: str | Path,
    *,
    expectations: ApacheJITExpectations = APACHEJIT_EXPECTATIONS,
) -> ApacheJITVerificationReport:
    """Verify one explicitly supplied ApacheJIT CSV without network access."""

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
    row_count = column_count = buggy_count = clean_count = 0
    inversions = year_mismatches = 0
    seen: set[str] = set()
    project_counts: dict[str, int] = {}
    project_buggy_counts: dict[str, int] = {}
    previous_epoch: int | None = None

    try:
        with source.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.reader(stream, strict=True)
            try:
                header = next(reader)
            except StopIteration:
                errors.append("CSV is empty")
            else:
                column_count = len(header)
                if tuple(header) != APACHEJIT_COLUMNS:
                    errors.append(
                        "header mismatch: expected canonical ApacheJIT columns"
                    )
                for line_number, row in enumerate(reader, start=2):
                    row_count += 1
                    if len(row) != len(APACHEJIT_COLUMNS):
                        errors.append(
                            f"row {line_number} has {len(row)} fields; expected "
                            f"{len(APACHEJIT_COLUMNS)}"
                        )
                        continue
                    try:
                        commit_id, project, buggy, epoch, year = _parse_row(row)
                    except ValueError as error:
                        errors.append(f"row {line_number}: {error}")
                        continue
                    if commit_id in seen:
                        errors.append(
                            f"row {line_number}: duplicate commit_id {commit_id}"
                        )
                    seen.add(commit_id)
                    project_counts[project] = project_counts.get(project, 0) + 1
                    if buggy:
                        buggy_count += 1
                        project_buggy_counts[project] = (
                            project_buggy_counts.get(project, 0) + 1
                        )
                    else:
                        clean_count += 1
                    if previous_epoch is not None and epoch < previous_epoch:
                        inversions += 1
                    previous_epoch = epoch
                    if datetime.fromtimestamp(epoch, timezone.utc).year != year:
                        year_mismatches += 1
    except (OSError, UnicodeError, csv.Error) as error:
        errors.append(f"CSV parsing failed: {error}")

    _compare(
        errors,
        expectations,
        digest=digest,
        row_count=row_count,
        column_count=column_count,
        project_count=len(project_counts),
        unique_commit_count=len(seen),
        buggy_count=buggy_count,
        clean_count=clean_count,
        timestamp_inversion_count=inversions,
        year_epoch_mismatch_count=year_mismatches,
        project_counts=project_counts,
    )
    return ApacheJITVerificationReport(
        str(source),
        digest,
        row_count,
        column_count,
        len(seen),
        len(project_counts),
        tuple(sorted(project_counts.items())),
        tuple(sorted(project_buggy_counts.items())),
        buggy_count,
        clean_count,
        inversions,
        year_mismatches,
        unique_errors(errors),
        warnings=(
            ("file order is not chronological; inversion count is diagnostic",)
            if inversions
            else ()
        ),
        project_positive_yield=tuple(
            sorted(
                (
                    project,
                    project_buggy_counts.get(project, 0) / count,
                )
                for project, count in project_counts.items()
            )
        ),
    )


def apachejit_outcome_definition() -> OutcomeDefinition:
    return OutcomeDefinition(
        id="apachejit.buggy_commit.v1",
        event="repository commit later labeled buggy",
        observation_process=ObservationProcess(
            "repository commit history",
            parameters=(("dataset", "apachejit"), ("label", "buggy")),
        ),
        window=Window(None, "repository_history", "commit"),
        thresholds=(Threshold("buggy", "=", 1),),
        description="Published repository-derived ApacheJIT buggy label.",
    )


def _parse_row(row: list[str]) -> tuple[str, str, bool, int, int]:
    commit_id = row[0].strip()
    if not _HEX_COMMIT.fullmatch(commit_id):
        raise ValueError("commit_id must be a 40-character hexadecimal SHA")
    project = row[1].strip()
    if not project:
        raise ValueError("project is required")
    if row[2] not in {"True", "False"} or row[3] not in {"True", "False"}:
        raise ValueError("buggy and fix must be exactly True or False")
    try:
        year = int(row[4])
        epoch = int(row[5])
    except ValueError as error:
        raise ValueError("year and author_date must be integers") from error
    if year < 1970 or year > 2100 or epoch <= 0:
        raise ValueError("year or author_date is outside the valid range")
    try:
        datetime.fromtimestamp(epoch, timezone.utc)
    except (OverflowError, OSError, ValueError) as error:
        raise ValueError(
            "author_date is outside the supported UTC timestamp range"
        ) from error
    for column, value in zip(APACHEJIT_COLUMNS[6:], row[6:]):
        try:
            parsed = float(value)
        except ValueError as error:
            raise ValueError(f"{column} must be numeric") from error
        if not math.isfinite(parsed):
            raise ValueError(f"{column} must be finite")
    return commit_id, project, row[2] == "True", epoch, year


def _compare(
    errors: list[str], expected: ApacheJITExpectations, **observed: Any
) -> None:
    checks = {
        "row_count": expected.row_count,
        "column_count": expected.column_count,
        "project_count": expected.project_count,
        "unique_commit_count": expected.unique_commit_count,
        "buggy_count": expected.buggy_count,
        "clean_count": expected.clean_count,
        "timestamp_inversion_count": expected.timestamp_inversion_count,
        "year_epoch_mismatch_count": expected.year_epoch_mismatch_count,
    }
    for name, value in checks.items():
        if value is not None and observed[name] != value:
            errors.append(f"{name} mismatch: expected {value}, got {observed[name]}")
    if expected.project_counts is not None:
        actual = tuple(sorted(observed["project_counts"].items()))
        if actual != tuple(sorted(expected.project_counts)):
            errors.append(
                "project_counts mismatch: observed project distribution differs"
            )


def _empty_report(path: Path, errors: tuple[str, ...]) -> ApacheJITVerificationReport:
    return ApacheJITVerificationReport(
        str(path), "", 0, 0, 0, 0, (), (), 0, 0, 0, 0, errors
    )
