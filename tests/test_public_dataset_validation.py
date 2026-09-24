from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

import pytest

from isoprax.ai4i2020 import ai4i2020_outcome_definitions
from isoprax.apachejit import (
    APACHEJIT_COLUMNS,
    ApacheJITExpectations,
    apachejit_outcome_definition,
    verify_apachejit_csv,
)
from isoprax.commensurability import check_commensurable
from isoprax.jepa import JEPA_DEFECT_RISK, JEPA_OPERATIONAL_FAILURE
from isoprax.metropt3 import (
    METROPT3_COLUMNS,
    MetroPT3Expectations,
    MetroPT3FailureInterval,
    metropt3_outcome_definition,
    read_metropt3_intervals,
    verify_metropt3_csv,
)
from isoprax.nasa_cmaps import cmapss_outcome_definitions, verify_cmapss
from scripts.verify_public_dataset import main as verify_public_dataset_cli


def _apache_row(
    commit: str, project: str = "apache/test", buggy: str = "False"
) -> list[str]:
    return [commit, project, buggy, "False", "2019", "1550000000", *(["1"] * 12)]


def _write_apache(path: Path, rows: list[list[str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(APACHEJIT_COLUMNS)
        writer.writerows(rows)


def _apache_expectations(rows: int) -> ApacheJITExpectations:
    return ApacheJITExpectations(
        sha256=None,
        row_count=rows,
        column_count=18,
        project_count=1,
        unique_commit_count=rows,
        buggy_count=0,
        clean_count=rows,
        timestamp_inversion_count=0,
        year_epoch_mismatch_count=0,
        project_counts=(("apache/test", rows),),
    )


def test_apachejit_validates_schema_identity_and_counts(tmp_path: Path) -> None:
    path = tmp_path / "apache.csv"
    _write_apache(path, [_apache_row("a" * 40), _apache_row("b" * 40)])

    report = verify_apachejit_csv(path, expectations=_apache_expectations(2))

    assert report.verified
    assert report.unique_commit_count == 2
    assert dict(report.project_counts) == {"apache/test": 2}


def test_apachejit_reports_project_positive_yield_including_zero_yield(
    tmp_path: Path,
) -> None:
    path = tmp_path / "apache-projects.csv"
    _write_apache(
        path,
        [
            _apache_row("a" * 40, "apache/positive", "True"),
            _apache_row("b" * 40, "apache/positive", "False"),
            _apache_row("c" * 40, "apache/zero", "False"),
        ],
    )
    expectations = ApacheJITExpectations(
        sha256=None,
        row_count=3,
        column_count=18,
        project_count=2,
        unique_commit_count=3,
        buggy_count=1,
        clean_count=2,
        timestamp_inversion_count=0,
        year_epoch_mismatch_count=0,
        project_counts=(("apache/positive", 2), ("apache/zero", 1)),
    )

    report = verify_apachejit_csv(path, expectations=expectations)

    assert report.verified
    assert dict(report.project_positive_yield) == {
        "apache/positive": 0.5,
        "apache/zero": 0.0,
    }
    assert report.to_dict()["diagnostics"]["project_positive_yield"] == {
        "apache/positive": 0.5,
        "apache/zero": 0.0,
    }


def test_apachejit_rejects_duplicate_bad_label_and_numeric_field(
    tmp_path: Path,
) -> None:
    path = tmp_path / "apache.csv"
    row = _apache_row("c" * 40, buggy="MAYBE")
    row[6] = "nan"
    _write_apache(path, [_apache_row("a" * 40), _apache_row("a" * 40), row])

    report = verify_apachejit_csv(path, expectations=ApacheJITExpectations(sha256=None))

    assert not report.verified
    assert any("buggy and fix" in error for error in report.errors)
    assert any("duplicate commit_id" in error for error in report.errors)


def test_apachejit_changed_bytes_fail_canonical_identity(tmp_path: Path) -> None:
    path = tmp_path / "apache.csv"
    _write_apache(path, [_apache_row("a" * 40)])

    report = verify_apachejit_csv(path)

    assert not report.verified
    assert any("sha256 mismatch" in error for error in report.errors)


def test_apachejit_exercises_empty_header_shape_and_all_row_diagnostics(
    tmp_path: Path,
) -> None:
    empty = tmp_path / "empty.csv"
    empty.write_text("", encoding="utf-8")
    assert (
        "CSV is empty"
        in verify_apachejit_csv(
            empty, expectations=ApacheJITExpectations(sha256=None)
        ).errors
    )

    malformed = tmp_path / "malformed.csv"
    malformed.write_text(",wrong\n1,2\n", encoding="utf-8")
    report = verify_apachejit_csv(
        malformed, expectations=ApacheJITExpectations(sha256=None)
    )
    assert any("header mismatch" in error for error in report.errors)
    assert any("expected 18" in error for error in report.errors)

    valid = _apache_row("d" * 40, buggy="True")
    valid[4] = "2019"
    valid[5] = "1550000001"
    inverted = _apache_row("e" * 40)
    inverted[4] = "2000"
    inverted[5] = "1550000000"
    diagnostic = tmp_path / "diagnostic.csv"
    _write_apache(diagnostic, [valid, inverted])
    report = verify_apachejit_csv(
        diagnostic,
        expectations=ApacheJITExpectations(
            sha256=None,
            row_count=None,
            column_count=None,
            project_count=None,
            unique_commit_count=None,
            buggy_count=None,
            clean_count=None,
            timestamp_inversion_count=None,
            year_epoch_mismatch_count=None,
            project_counts=None,
        ),
    )
    assert report.verified
    assert report.timestamp_inversion_count == 1
    assert report.year_epoch_mismatch_count == 1
    assert report.warnings
    payload = report.to_dict()
    assert payload["dataset_id"] == "apachejit"
    assert payload["observed"]["row_count"] == 2
    assert payload["diagnostics"]["timestamp_inversion_count"] == 1


def test_apachejit_rejects_each_row_scalar_error_and_missing_source(
    tmp_path: Path,
) -> None:
    cases = [
        ("short", _apache_row("f" * 40)[:-1]),
        ("bad commit", _apache_row("not-a-sha")),
        ("empty project", _apache_row("1" * 40, project="")),
        ("bad time", [*_apache_row("2" * 40)[:4], "bad", "1550000000", *(["1"] * 12)]),
        ("bad epoch", [*_apache_row("3" * 40)[:5], "bad", *(["1"] * 12)]),
        (
            "unrepresentable epoch",
            [*_apache_row("7" * 40)[:5], "999999999999999999999999", *(["1"] * 12)],
        ),
        ("bad range", [*_apache_row("4" * 40)[:4], "1969", "1", *(["1"] * 12)]),
        ("bad number", [*_apache_row("5" * 40)[:6], "bad", *(["1"] * 11)]),
        ("not finite", [*_apache_row("6" * 40)[:6], "inf", *(["1"] * 11)]),
    ]
    path = tmp_path / "scalar-errors.csv"
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(APACHEJIT_COLUMNS)
        for _, row in cases:
            writer.writerow(row)
    report = verify_apachejit_csv(
        path,
        expectations=ApacheJITExpectations(
            sha256=None,
            row_count=None,
            column_count=None,
            project_count=None,
            unique_commit_count=None,
            buggy_count=None,
            clean_count=None,
            timestamp_inversion_count=None,
            year_epoch_mismatch_count=None,
            project_counts=None,
        ),
    )
    assert not report.verified
    assert len(report.errors) >= len(cases)
    assert not verify_apachejit_csv(tmp_path / "missing.csv").verified


def _trajectory_row(unit: int, cycle: int) -> str:
    return " ".join([str(unit), str(cycle), *(["0.0"] * 24)])


def _write_lines(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_cmapss_checks_cycles_and_rul_alignment(tmp_path: Path) -> None:
    train = tmp_path / "train.txt"
    test = tmp_path / "test.txt"
    rul = tmp_path / "rul.txt"
    _write_lines(train, [_trajectory_row(1, 1), _trajectory_row(1, 2)])
    _write_lines(test, [_trajectory_row(2, 1), _trajectory_row(2, 3)])
    _write_lines(rul, ["4"])

    report = verify_cmapss(
        "FD001",
        train,
        test,
        rul,
        expectations={
            "train_rows": 2,
            "train_units": 1,
            "test_rows": 2,
            "test_units": 1,
            "rul_count": 1,
        },
    )

    assert not report.verified
    assert any("cycle gap" in error for error in report.errors)


def test_cmapss_accepts_valid_train_test_and_rul_artifacts(tmp_path: Path) -> None:
    train = tmp_path / "train.txt"
    test = tmp_path / "test.txt"
    rul = tmp_path / "rul.txt"
    _write_lines(train, [_trajectory_row(1, 1), _trajectory_row(1, 2)])
    _write_lines(test, [_trajectory_row(2, 1), _trajectory_row(2, 2)])
    _write_lines(rul, ["5"])

    report = verify_cmapss(
        "FD001",
        train,
        test,
        rul,
        expectations={
            "train_sha256": None,
            "test_sha256": None,
            "rul_sha256": None,
            "train_rows": 2,
            "train_units": 1,
            "test_rows": 2,
            "test_units": 1,
            "rul_count": 1,
        },
    )

    assert report.verified
    assert report.train_units == 1
    assert report.test_units == report.rul_count == 1


def test_cmapss_outcomes_are_separate_from_jit() -> None:
    result = check_commensurable(
        apachejit_outcome_definition(), cmapss_outcome_definitions()["rul"]
    )

    assert result.level == "irreducible"
    assert not result.pooling_allowed


def test_cmapss_rejects_missing_unknown_and_malformed_artifacts(tmp_path: Path) -> None:
    unknown = verify_cmapss("FD999", tmp_path / "a", tmp_path / "b", tmp_path / "c")
    assert not unknown.verified
    assert "unknown dataset" in unknown.errors[0]

    missing = verify_cmapss("FD001", tmp_path / "a", tmp_path / "b", tmp_path / "c")
    assert not missing.verified
    assert any("does not exist" in error for error in missing.errors)
    assert missing.to_dict()["dataset_id"] == "cmapss-fd001"

    train = tmp_path / "bad-train.txt"
    test = tmp_path / "bad-test.txt"
    rul = tmp_path / "bad-rul.txt"
    _write_lines(
        train,
        [
            "",
            "1 1 0",
            "bad " + " ".join(["0"] * 25),
            "1.5 1 " + " ".join(["0"] * 24),
            "0 1 " + " ".join(["0"] * 24),
            "1 1 " + " ".join(["nan"] + ["0"] * 23),
            _trajectory_row(1, 1),
            _trajectory_row(1, 3),
        ],
    )
    _write_lines(test, [_trajectory_row(2, 1)])
    _write_lines(rul, ["", "bad", "-1", "nan", "5"])
    report = verify_cmapss(
        "FD001",
        train,
        test,
        rul,
        expectations={"train_sha256": "wrong", "train_rows": None},
    )
    assert not report.verified
    assert any("sha256 mismatch" in error for error in report.errors)
    assert any("expected 26" in error for error in report.errors)
    assert any("non-numeric" in error for error in report.errors)
    assert any("unit and cycle must be integers" in error for error in report.errors)
    assert any("must be finite" in error for error in report.errors)
    assert any("must be positive" in error for error in report.errors)
    assert any("cycle gap" in error for error in report.errors)
    assert any("RUL row" in error for error in report.errors)


def test_cmapss_outcome_definitions_are_serializable() -> None:
    definitions = cmapss_outcome_definitions()
    assert set(definitions) == {"run_to_failure", "rul"}
    assert definitions["rul"].to_dict()["id"].startswith("cmapss.")


def test_cmapss_handles_hash_and_decode_failures(tmp_path: Path, monkeypatch) -> None:
    train = tmp_path / "train.txt"
    test = tmp_path / "test.txt"
    rul = tmp_path / "rul.txt"
    _write_lines(train, [_trajectory_row(1, 1)])
    _write_lines(test, [_trajectory_row(1, 1)])
    _write_lines(rul, ["1"])

    def fail_hash(_path: Path) -> str:
        raise OSError("hash unavailable")

    monkeypatch.setattr("isoprax.nasa_cmaps.sha256_path", fail_hash)
    report = verify_cmapss(
        "FD001",
        train,
        test,
        rul,
        expectations={
            "train_sha256": "expected",
            "test_sha256": "expected",
            "rul_sha256": "expected",
        },
    )
    assert any("hash unavailable" in error for error in report.errors)

    invalid = tmp_path / "invalid.txt"
    invalid.write_bytes(b"\xff\xfe")
    monkeypatch.setattr("isoprax.nasa_cmaps.sha256_path", lambda _path: "hash")
    report = verify_cmapss(
        "FD001",
        invalid,
        invalid,
        invalid,
        expectations={"train_rows": None, "test_rows": None, "rul_count": None},
    )
    assert any("parsing failed" in error for error in report.errors)


def _write_metro(path: Path, rows: list[list[str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(METROPT3_COLUMNS)
        writer.writerows(rows)


def _metro_row(index: str, timestamp: str) -> list[str]:
    return [index, timestamp, *(["1.0"] * 15)]


def _metro_expectations(rows: int) -> MetroPT3Expectations:
    return MetroPT3Expectations(
        sha256=None,
        row_count=rows,
        column_count=17,
        expected_interval_rows=(("F1", 1),),
    )


def test_metropt3_requires_explicit_anchor_and_preserves_uncovered_rows(
    tmp_path: Path,
) -> None:
    path = tmp_path / "metro.csv"
    _write_metro(
        path,
        [
            _metro_row("0", "2020-01-01 00:00:00"),
            _metro_row("1", "2020-01-01 00:00:10"),
        ],
    )

    report = verify_metropt3_csv(
        path,
        (),
        expectations=MetroPT3Expectations(
            sha256=None, row_count=2, column_count=17, expected_interval_rows=None
        ),
    )

    assert not report.verified
    assert any("anchors are required" in error for error in report.errors)
    assert report.interval_coverage == ()


def test_metropt3_counts_first_valid_row_after_malformed_leading_row(
    tmp_path: Path,
) -> None:
    path = tmp_path / "metro-leading-invalid.csv"
    malformed = _metro_row("0", "2020-01-01 00:00:00")
    malformed[2] = "not-a-number"
    _write_metro(
        path,
        [malformed, _metro_row("1", "2020-01-01 00:00:10")],
    )
    interval = MetroPT3FailureInterval(
        "F1", datetime(2020, 1, 1, 0, 0, 10), datetime(2020, 1, 1, 0, 0, 10), "report"
    )

    report = verify_metropt3_csv(
        path,
        (interval,),
        expectations=MetroPT3Expectations(
            sha256=None,
            row_count=2,
            column_count=17,
            expected_interval_rows=(("F1", 1),),
        ),
    )

    assert not report.verified
    assert dict(report.interval_coverage) == {"F1": 1}
    assert any("not-a-number" in error for error in report.errors)


def test_metropt3_rejects_whitespace_aliases_for_anchor_identity(
    tmp_path: Path,
) -> None:
    path = tmp_path / "metro-anchor-alias.csv"
    _write_metro(path, [_metro_row("0", "2020-01-01 00:00:00")])
    start = datetime(2020, 1, 1)
    intervals = (
        MetroPT3FailureInterval("F1", start, start, "report-1"),
        MetroPT3FailureInterval("F1 ", start, start, "report-2"),
    )

    report = verify_metropt3_csv(
        path,
        intervals,
        expectations=MetroPT3Expectations(
            sha256=None, row_count=1, column_count=17, expected_interval_rows=None
        ),
    )

    assert not report.verified
    assert any("whitespace" in error for error in report.errors)
    assert any("duplicate" in error for error in report.errors)


def test_metropt3_accepts_valid_rows_with_explicit_anchor_coverage(
    tmp_path: Path,
) -> None:
    path = tmp_path / "valid-metro.csv"
    _write_metro(
        path,
        [
            _metro_row("0", "2020-01-01 00:00:00"),
            _metro_row("1", "2020-01-01 00:00:10"),
            _metro_row("2", "2020-01-01 00:00:20"),
        ],
    )
    interval = MetroPT3FailureInterval(
        "F1", datetime(2020, 1, 1), datetime(2020, 1, 1, 0, 0, 10), "report"
    )

    report = verify_metropt3_csv(
        path,
        (interval,),
        expectations=MetroPT3Expectations(
            sha256=None,
            row_count=3,
            column_count=17,
            expected_interval_rows=(("F1", 2),),
        ),
    )

    assert report.verified
    assert report.monotonic
    assert dict(report.interval_coverage) == {"F1": 2}
    assert dict(report.gap_counts_seconds) == {10.0: 2}


def test_metropt3_rejects_non_monotonic_time_and_bad_anchor(tmp_path: Path) -> None:
    path = tmp_path / "metro.csv"
    _write_metro(
        path,
        [
            _metro_row("0", "2020-01-01 00:00:10"),
            _metro_row("1", "2020-01-01 00:00:00"),
        ],
    )
    interval = MetroPT3FailureInterval(
        "F1", datetime(2020, 1, 1, 0, 0, 5), datetime(2020, 1, 1, 0, 0, 0), "report"
    )

    report = verify_metropt3_csv(
        path,
        (interval,),
        expectations=MetroPT3Expectations(
            sha256=None, row_count=2, column_count=17, expected_interval_rows=None
        ),
    )

    assert not report.verified
    assert any("not monotonic" in error for error in report.errors)
    assert any("start is after end" in error for error in report.errors)


def test_metropt3_rejects_timezone_qualified_source_times(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="timezone-naive"):
        MetroPT3FailureInterval(
            "F1",
            datetime.fromisoformat("2020-01-01T03:00:00+03:00"),
            datetime(2020, 1, 1, 0, 0, 10),
            "report",
        )

    path = tmp_path / "metro-aware-timestamp.csv"
    _write_metro(path, [_metro_row("0", "2020-01-01T00:00:00Z")])
    interval = MetroPT3FailureInterval(
        "F1", datetime(2020, 1, 1), datetime(2020, 1, 1, 0, 0, 10), "report"
    )
    report = verify_metropt3_csv(
        path,
        (interval,),
        expectations=MetroPT3Expectations(
            sha256=None, row_count=1, column_count=17, expected_interval_rows=None
        ),
    )

    assert not report.verified
    assert any("timezone-naive" in error for error in report.errors)
    assert report.unique_timestamps == 0


def test_metropt3_checks_header_rows_identity_cadence_and_anchor_coverage(
    tmp_path: Path,
) -> None:
    empty = tmp_path / "empty-metro.csv"
    empty.write_text("", encoding="utf-8")
    report = verify_metropt3_csv(
        empty,
        (),
        expectations=MetroPT3Expectations(
            sha256=None, row_count=None, column_count=None, expected_interval_rows=None
        ),
    )
    assert "CSV is empty" in report.errors

    bad = tmp_path / "bad-metro.csv"
    with bad.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["wrong"])
        writer.writerow(["0"] * 16)
    report = verify_metropt3_csv(
        bad,
        (),
        expectations=MetroPT3Expectations(
            sha256=None, row_count=None, column_count=17, expected_interval_rows=None
        ),
    )
    assert any("header mismatch" in error for error in report.errors)
    assert any("expected 17" in error for error in report.errors)

    valid = tmp_path / "valid-metro.csv"
    rows = [
        _metro_row("0", "2020-01-01T00:00:00"),
        _metro_row("0", "2020-01-01 00:00:10"),
        _metro_row("2", "2020-01-01 00:00:20"),
        _metro_row("3", "2020-01-01 00:00:10"),
    ]
    rows[2][2] = "inf"
    _write_metro(valid, rows)
    interval = MetroPT3FailureInterval(
        "F1",
        datetime(2020, 1, 1, 0, 0),
        datetime(2020, 1, 1, 0, 0, 15),
        "https://archive.ics.uci.edu/dataset/791/metropt3%2Bdataset",
    )
    report = verify_metropt3_csv(
        valid,
        (interval,),
        expectations=MetroPT3Expectations(
            sha256=None,
            row_count=4,
            column_count=17,
            expected_interval_rows=(("F1", 2),),
        ),
    )
    assert not report.verified
    assert any("duplicate row identifier" in error for error in report.errors)
    assert any("duplicate timestamp" in error for error in report.errors)
    assert any("must be finite" in error for error in report.errors)
    payload = report.to_dict()
    assert payload["dataset_id"] == "metropt3"
    assert payload["observed"]["unique_timestamps"] == 2
    assert "gap_counts_seconds" in payload["diagnostics"]


def test_metropt3_interval_validation_is_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "metro.csv"
    _write_metro(path, [_metro_row("0", "2020-01-01 00:00:00")])
    intervals = (
        MetroPT3FailureInterval("", datetime(2020, 1, 1), datetime(2020, 1, 1), ""),
        MetroPT3FailureInterval(
            "F1", datetime(2020, 1, 1), datetime(2020, 1, 1), "report"
        ),
        MetroPT3FailureInterval(
            "F1", datetime(2020, 1, 1), datetime(2019, 1, 1), "report"
        ),
    )
    report = verify_metropt3_csv(
        path,
        intervals,
        expectations=MetroPT3Expectations(
            sha256=None, row_count=1, column_count=17, expected_interval_rows=None
        ),
    )
    assert not report.verified
    assert any("anchor_id is required" in error for error in report.errors)
    assert any("duplicate" in error for error in report.errors)
    assert any("source_reference is required" in error for error in report.errors)


def test_metropt3_handles_missing_hash_and_csv_failures(
    tmp_path: Path, monkeypatch
) -> None:
    missing = verify_metropt3_csv(tmp_path / "missing.csv", ())
    assert not missing.verified

    path = tmp_path / "unreadable-metro.csv"
    _write_metro(path, [_metro_row("0", "2020-01-01 00:00:00")])

    def fail_hash(_path: Path) -> str:
        raise OSError("hash unavailable")

    monkeypatch.setattr("isoprax.metropt3.sha256_path", fail_hash)
    report = verify_metropt3_csv(
        path,
        (),
        expectations=MetroPT3Expectations(
            sha256=None, row_count=None, column_count=None, expected_interval_rows=None
        ),
    )
    assert "cannot be read" in report.errors[0]

    malformed = tmp_path / "malformed-metro.csv"
    malformed.write_text(
        ',timestamp,TP2,TP3,H1,DV_pressure,Reservoirs,Oil_temperature,Motor_current,COMP,DV_eletric,Towers,MPG,LPS,Pressure_switch,Oil_level,Caudal_impulses\n"',
        encoding="utf-8",
    )
    monkeypatch.setattr("isoprax.metropt3.sha256_path", lambda _path: "hash")
    report = verify_metropt3_csv(
        malformed,
        (),
        expectations=MetroPT3Expectations(
            sha256=None, row_count=None, column_count=None, expected_interval_rows=None
        ),
    )
    assert any("CSV parsing failed" in error for error in report.errors)


def test_metropt3_outcome_is_irreducible_against_ai4i() -> None:
    result = check_commensurable(
        metropt3_outcome_definition(), ai4i2020_outcome_definitions()["Machine failure"]
    )

    assert result.level == "irreducible"
    assert not result.pooling_allowed


def test_public_dataset_outcomes_do_not_pool_with_existing_jepa_families() -> None:
    definitions = (
        apachejit_outcome_definition(),
        cmapss_outcome_definitions()["rul"],
        metropt3_outcome_definition(),
        ai4i2020_outcome_definitions()["Machine failure"],
        JEPA_DEFECT_RISK,
        JEPA_OPERATIONAL_FAILURE,
    )
    for left_index, left in enumerate(definitions):
        for right in definitions[left_index + 1 :]:
            result = check_commensurable(left, right)
            assert result.level == "irreducible"
            assert not result.pooling_allowed


def test_cli_returns_contract_json_and_nonzero_for_invalid_artifact(
    tmp_path: Path, capsys
) -> None:
    source = tmp_path / "invalid.csv"
    source.write_text("wrong,header\n", encoding="utf-8")

    exit_code = verify_public_dataset_cli(["apachejit", str(source), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["dataset_id"] == "apachejit"
    assert payload["verified"] is False
    assert payload["artifact"]["path"] == str(source)
    assert payload["observed"]
    assert payload["diagnostics"]
    assert payload["errors"]


def test_cli_rejects_malformed_interval_manifest_without_escaping(
    tmp_path: Path, capsys
) -> None:
    malformed_manifests = (
        (
            [{"anchor_id": "F1", "start": "2020-01-01T00:00:00Z"}],
            "missing required fields",
        ),
        (
            [
                {
                    "anchor_id": "F1",
                    "start": None,
                    "end": "2020-01-01T00:00:10Z",
                    "source_reference": "report",
                }
            ],
            "interval field start must be a string",
        ),
        (
            [
                {
                    "anchor_id": "F1",
                    "start": "2020-01-01T00:00:00Z",
                    "end": "2020-01-01T00:00:10",
                    "source_reference": "report",
                }
            ],
            "timezone-naive",
        ),
    )
    source = tmp_path / "missing.csv"
    for index, (manifest_data, expected_error) in enumerate(malformed_manifests):
        manifest = tmp_path / f"intervals-{index}.json"
        manifest.write_text(json.dumps(manifest_data), encoding="utf-8")

        exit_code = verify_public_dataset_cli(
            ["metropt3", str(source), "--intervals", str(manifest), "--json"]
        )
        payload = json.loads(capsys.readouterr().out)

        assert exit_code == 1
        assert payload["dataset_id"] == "metropt3"
        assert payload["verified"] is False
        assert payload["artifact"]["path"] == str(source)
        assert any(expected_error in error for error in payload["errors"])


def test_cli_accepts_published_timezone_unqualified_metropt3_intervals(
    tmp_path: Path, capsys
) -> None:
    root = Path(__file__).parents[1]
    source = tmp_path / "missing.csv"
    manifest = root / "examples/metropt3/failure_intervals.json"

    exit_code = verify_public_dataset_cli(
        ["metropt3", str(source), "--intervals", str(manifest), "--json"]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["verified"] is False
    assert any("source file does not exist" in error for error in payload["errors"])
    assert all("interval manifest error" not in error for error in payload["errors"])


def test_read_metropt3_intervals_parses_timezone_unqualified_source_data(
    tmp_path: Path,
) -> None:
    manifest = tmp_path / "intervals.json"
    manifest.write_text(
        json.dumps(
            [
                {
                    "anchor_id": "F1",
                    "start": "2020-04-18T00:00:00",
                    "end": "2020-04-18T23:59:00",
                    "source_reference": "uci-record",
                }
            ]
        ),
        encoding="utf-8",
    )

    intervals = read_metropt3_intervals(manifest)

    assert len(intervals) == 1
    assert intervals[0].anchor_id == "F1"
    assert intervals[0].start == datetime(2020, 4, 18)
    assert intervals[0].end == datetime(2020, 4, 18, 23, 59)


@pytest.mark.parametrize(
    ("payload", "message"),
    (
        ({}, "JSON list"),
        ([1], "each interval must be a JSON object"),
        ([{"anchor_id": "F1"}], "missing required fields"),
        (
            [
                {
                    "anchor_id": "F1",
                    "start": None,
                    "end": "2020-04-18T00:10:00",
                    "source_reference": "uci-record",
                }
            ],
            "interval field start must be a string",
        ),
        (
            [
                {
                    "anchor_id": "F1",
                    "start": "2020-04-18T00:00:00Z",
                    "end": "2020-04-18T00:10:00",
                    "source_reference": "uci-record",
                }
            ],
            "timezone-naive",
        ),
    ),
)
def test_read_metropt3_intervals_rejects_malformed_manifest_shapes(
    tmp_path: Path, payload: object, message: str
) -> None:
    manifest = tmp_path / "intervals.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        read_metropt3_intervals(manifest)


def test_read_metropt3_intervals_propagates_missing_and_invalid_json(
    tmp_path: Path,
) -> None:
    with pytest.raises(FileNotFoundError):
        read_metropt3_intervals(tmp_path / "missing.json")

    invalid = tmp_path / "invalid.json"
    invalid.write_text("{", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        read_metropt3_intervals(invalid)


def test_manifests_and_ledger_are_explicit() -> None:
    root = Path(__file__).parents[1]
    apache = json.loads((root / "examples/apachejit/manifest.json").read_text())
    ledger = json.loads(
        (root / "examples/public-datasets/decision-ledger.json").read_text()
    )

    for dataset in ("apachejit", "cmapss", "metropt3"):
        manifest = json.loads((root / f"examples/{dataset}/manifest.json").read_text())
        assert manifest["canonical_source"]
        assert manifest["discovery_source"]
        assert manifest.get("artifact_sha256") or manifest.get("artifacts")
        assert manifest["claim_boundary"]
    assert apache["evidence_class"] == "repository-derived"
    assert len(ledger["decisions"]) >= 8
    assert all(
        entry.get("artifact_identity") and entry.get("outcome_definition")
        for entry in ledger["decisions"]
    )
    assert {entry["status"] for entry in ledger["decisions"]} >= {
        "deferred",
        "fixture-only",
    }
