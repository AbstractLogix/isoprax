from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from isoprax.ai4i2020 import (
    AI4I2020_COLUMNS,
    AI4I2020_EXPECTATIONS,
    AI4I2020_FEATURE_COLUMNS,
    AI4I2020_LABEL_COLUMNS,
    AI4I2020_MODE_COLUMNS,
    AI4I2020Expectations,
    ai4i2020_outcome_definitions,
    verify_ai4i2020_csv,
)
from isoprax.commensurability import check_commensurable
from isoprax.jepa import JEPA_DEFECT_RISK

ROOT = Path(__file__).resolve().parents[1]
HEADER = ",".join(AI4I2020_COLUMNS)


def _row(
    udi: int,
    *,
    product_type: str = "L",
    product_id: str | None = None,
    machine_failure: int = 0,
    modes: tuple[int, int, int, int, int] = (0, 0, 0, 0, 0),
) -> str:
    product_id = product_id or f"{product_type}{udi:05d}"
    return ",".join(
        [
            str(udi),
            product_id,
            product_type,
            "300.0",
            "310.0",
            "1500",
            "40.0",
            "10",
            str(machine_failure),
            *(str(value) for value in modes),
        ]
    )


def _write_csv(
    tmp_path: Path, rows: list[str], *, bom: bool = False, name: str = "ai4i2020.csv"
) -> Path:
    path = tmp_path / name
    content = "\n".join([HEADER, *rows]) + "\n"
    path.write_text(content, encoding="utf-8-sig" if bom else "utf-8")
    return path


def _small_expectations(
    path: Path,
    *,
    row_count: int,
    machine_failure_count: int,
    mode_counts: tuple[tuple[str, int], ...],
    multi_mode_row_count: int,
    failure_without_mode_count: int,
    mode_without_failure_count: int,
):
    return AI4I2020Expectations(
        csv_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        row_count=row_count,
        column_count=len(AI4I2020_COLUMNS),
        machine_failure_count=machine_failure_count,
        mode_counts=mode_counts,
        multi_mode_row_count=multi_mode_row_count,
        failure_without_mode_count=failure_without_mode_count,
        mode_without_failure_count=mode_without_failure_count,
        composite_mismatch_count=(
            failure_without_mode_count + mode_without_failure_count
        ),
    )


def test_valid_local_rows_are_summarized_without_repair(tmp_path: Path):
    path = _write_csv(
        tmp_path,
        [
            _row(1),
            _row(2, machine_failure=1, modes=(1, 0, 0, 0, 0)),
            _row(3, machine_failure=1),
            _row(4, modes=(0, 1, 0, 0, 0)),
            _row(5, machine_failure=1, modes=(0, 1, 1, 0, 0)),
        ],
    )

    report = verify_ai4i2020_csv(
        path,
        expectations=_small_expectations(
            path,
            row_count=5,
            machine_failure_count=3,
            mode_counts=(("TWF", 1), ("HDF", 2), ("PWF", 1), ("OSF", 0), ("RNF", 0)),
            multi_mode_row_count=1,
            failure_without_mode_count=1,
            mode_without_failure_count=1,
        ),
    )

    assert report.verified
    assert report.row_count == 5
    assert report.machine_failure_count == 3
    assert report.mode_counts == (
        ("TWF", 1),
        ("HDF", 2),
        ("PWF", 1),
        ("OSF", 0),
        ("RNF", 0),
    )
    assert report.multi_mode_row_count == 1
    assert report.failure_without_mode_count == 1
    assert report.mode_without_failure_count == 1
    assert report.composite_mismatch_count == 2
    assert report.to_dict()["claim_boundary"].startswith("Public synthetic")


def test_published_bom_header_is_accepted(tmp_path: Path):
    path = _write_csv(tmp_path, [_row(1)], bom=True)
    report = verify_ai4i2020_csv(
        path,
        expectations=_small_expectations(
            path,
            row_count=1,
            machine_failure_count=0,
            mode_counts=(("TWF", 0), ("HDF", 0), ("PWF", 0), ("OSF", 0), ("RNF", 0)),
            multi_mode_row_count=0,
            failure_without_mode_count=0,
            mode_without_failure_count=0,
        ),
    )

    assert report.verified
    assert report.column_count == len(AI4I2020_COLUMNS)


def test_schema_and_row_domain_errors_fail_closed(tmp_path: Path):
    path = _write_csv(
        tmp_path,
        [
            _row(1, product_type="Z", product_id="L00001"),
            _row(1),
            _row(1),
            _row(3, product_id="Lbad"),
            _row(2, machine_failure=2),
        ],
    )

    report = verify_ai4i2020_csv(path)

    assert not report.verified
    assert any("product type" in error for error in report.errors)
    assert any("duplicate UDI" in error for error in report.errors)
    assert any("binary" in error for error in report.errors)


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        (0, "not-an-int", "UDI"),
        (0, "-1", "positive"),
        (3, "nan", "finite"),
        (3, "not-a-number", "numeric"),
        (5, "1500.5", "integer"),
        (7, "10.5", "integer"),
    ],
)
def test_invalid_numeric_fields_fail_closed(
    tmp_path: Path, field: int, value: str, reason: str
):
    fields = _row(1).split(",")
    fields[field] = value
    report = verify_ai4i2020_csv(
        _write_csv(tmp_path, [",".join(fields)], name=f"invalid-{field}.csv")
    )

    assert not report.verified
    assert any(reason in error for error in report.errors)


def test_empty_header_shape_and_csv_syntax_fail_closed(tmp_path: Path):
    empty = tmp_path / "empty.csv"
    empty.write_text("", encoding="utf-8")
    empty_report = verify_ai4i2020_csv(empty)
    assert any("CSV is empty" in error for error in empty_report.errors)

    bad_shape = tmp_path / "bad-shape.csv"
    bad_shape.write_text("wrong-header\n1,2\n", encoding="utf-8")
    shape_report = verify_ai4i2020_csv(bad_shape)
    assert any("header mismatch" in error for error in shape_report.errors)
    assert any("fields" in error for error in shape_report.errors)

    bad_csv = tmp_path / "bad-csv.csv"
    bad_csv.write_text(f'{HEADER}\n"unterminated\n', encoding="utf-8")
    csv_report = verify_ai4i2020_csv(bad_csv)
    assert any("CSV parsing failed" in error for error in csv_report.errors)


def test_read_error_and_matching_expectations_are_handled(tmp_path: Path):
    path = _write_csv(tmp_path, [_row(1)])
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    expectations = AI4I2020_EXPECTATIONS.__class__(
        csv_sha256=digest,
        row_count=1,
        column_count=14,
        machine_failure_count=0,
        mode_counts=(("TWF", 0), ("HDF", 0), ("PWF", 0), ("OSF", 0), ("RNF", 0)),
        multi_mode_row_count=0,
        failure_without_mode_count=0,
        mode_without_failure_count=0,
        composite_mismatch_count=0,
    )
    report = verify_ai4i2020_csv(path, expectations=expectations)
    assert report.verified

    with patch(
        "isoprax.ai4i2020.sha256_path", side_effect=OSError("permission denied")
    ):
        read_error = verify_ai4i2020_csv(path)
    assert any("cannot be read" in error for error in read_error.errors)


def test_missing_file_and_default_pinned_expectations_fail_closed(tmp_path: Path):
    missing = verify_ai4i2020_csv(tmp_path / "missing.csv")
    assert not missing.verified
    assert any("does not exist" in error for error in missing.errors)

    small = verify_ai4i2020_csv(_write_csv(tmp_path, [_row(1)]))
    assert not small.verified
    assert any("csv_sha256" in error for error in small.errors)
    assert any("row_count" in error for error in small.errors)


def test_feature_and_label_columns_are_disjoint():
    assert set(AI4I2020_FEATURE_COLUMNS).isdisjoint(AI4I2020_LABEL_COLUMNS)
    assert AI4I2020_LABEL_COLUMNS == ("Machine failure", *AI4I2020_MODE_COLUMNS)


def test_outcome_definitions_keep_composite_and_modes_irreducible():
    definitions = ai4i2020_outcome_definitions()

    result = check_commensurable(definitions["Machine failure"], definitions["TWF"])
    assert not result.commensurable
    assert result.level == "irreducible"
    assert result.pooling_allowed is False
    assert "event" in result.differing_fields

    jit_result = check_commensurable(definitions["Machine failure"], JEPA_DEFECT_RISK)
    assert not jit_result.commensurable
    assert jit_result.pooling_allowed is False
    assert "observation_process" in jit_result.differing_fields


def test_manifest_matches_pinned_expectations():
    manifest = json.loads(
        (ROOT / "examples/ai4i2020/manifest.json").read_text(encoding="utf-8")
    )
    snapshot = manifest["snapshot"]

    assert manifest["source"]["csv_sha256"] == AI4I2020_EXPECTATIONS.csv_sha256
    assert snapshot["row_count"] == AI4I2020_EXPECTATIONS.row_count
    assert snapshot["column_count"] == AI4I2020_EXPECTATIONS.column_count
    assert snapshot["mode_counts"] == dict(AI4I2020_EXPECTATIONS.mode_counts)
    assert snapshot["composite_mismatch_count"] == (
        AI4I2020_EXPECTATIONS.composite_mismatch_count
    )
    with pytest.raises(ValueError, match="csv_sha256"):
        AI4I2020Expectations(csv_sha256="")


def test_cli_reports_json_and_nonzero_for_unverified_input(tmp_path: Path):
    path = _write_csv(tmp_path, [_row(1)])
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts/verify_ai4i2020.py"), str(path)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert payload["verified"] is False
    assert payload["errors"]


def test_cli_without_local_path_reports_unavailable_snapshot():
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts/verify_ai4i2020.py")],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert payload["verified"] is False
    assert payload["path"] == ""
    assert payload["errors"] == [
        "external snapshot unavailable: no local CSV path provided"
    ]
