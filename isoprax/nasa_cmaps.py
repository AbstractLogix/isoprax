"""Offline verification for NASA C-MAPSS trajectory and RUL artifacts."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .commensurability import ObservationProcess, OutcomeDefinition, Threshold, Window
from .public_dataset import sha256_path, unique_errors

CMAPSS_CLAIM_BOUNDARY = (
    "Simulated run-to-failure and RUL structural evidence only; not real-fleet "
    "predictive efficacy or Semantic/Full Conformance."
)
CMAPSS_EXPECTATIONS: dict[str, dict[str, Any]] = {
    "FD001": {
        "train_sha256": "963b5e22825b34d8b21c69e1aeb4af3e647050eb672ee8834ba4b5d91d2de0f8",
        "test_sha256": "3cda7109ce17bafb5443f2ac926cfcf88154b941b8c4cf95eb55d1ddd6f52851",
        "rul_sha256": "a19c8ec94931949d0485bdc35118206e9c81c4547b422efb9cf86f4ceddbceca",
        "train_rows": 20631,
        "train_units": 100,
        "test_rows": 13096,
        "test_units": 100,
        "rul_count": 100,
    },
    "FD002": {
        "train_sha256": "dac6c4dbc4e7c1bdeb5747da3d313d05c395bb99801b44a002b26a2ba13d788f",
        "test_sha256": "de7b5bf7e998a985c378488480528b7c02cff1406a46740def362dda8d9b4e02",
        "rul_sha256": "c851dd96a6ea6998d3c4a8f834d3c8013aa90e93a6ed950dc826ad0655b2906b",
        "train_rows": 53759,
        "train_units": 260,
        "test_rows": 33991,
        "test_units": 259,
        "rul_count": 259,
    },
    "FD003": {
        "train_sha256": "2abbe9968cc5e8eb091980f51b20f62bb4127336d3482cb52071d53bf23329e2",
        "test_sha256": "299babd63c8d987cef079c4a425429f33b3a34797d803bbe2ad48c29dbd0d790",
        "rul_sha256": "df1e0566306b174a2de41c67a3e7a51877889598b78643fc3e5685259091b7cb",
        "train_rows": 24720,
        "train_units": 100,
        "test_rows": 16596,
        "test_units": 100,
        "rul_count": 100,
    },
    "FD004": {
        "train_sha256": "27ef6160b6a1dcb2613a88de9c239f763b223f02cdc41dc5cdedc5dc189b6218",
        "test_sha256": "1dc675fff0624bac10786927c6715b37d1297657137400d2b1a3138d777a3ba5",
        "rul_sha256": "196b836b85a95ac7fdbbf29c5fdf1657382eafa445644d114ffaaf50dc2975e1",
        "train_rows": 61249,
        "train_units": 249,
        "test_rows": 41214,
        "test_units": 248,
        "rul_count": 248,
    },
}


@dataclass(frozen=True)
class CMapssVerificationReport:
    dataset: str
    train_path: str
    test_path: str
    rul_path: str
    train_sha256: str
    test_sha256: str
    rul_sha256: str
    train_rows: int
    train_units: int
    test_rows: int
    test_units: int
    rul_count: int
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    claim_boundary: str = CMAPSS_CLAIM_BOUNDARY

    @property
    def verified(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["verified"] = self.verified
        payload["dataset_id"] = f"cmapss-{self.dataset.lower()}"
        payload["artifact"] = {
            "train": {"path": self.train_path, "sha256": self.train_sha256},
            "test": {"path": self.test_path, "sha256": self.test_sha256},
            "rul": {"path": self.rul_path, "sha256": self.rul_sha256},
        }
        payload["observed"] = {
            "train_rows": self.train_rows,
            "train_units": self.train_units,
            "test_rows": self.test_rows,
            "test_units": self.test_units,
            "rul_count": self.rul_count,
        }
        payload["diagnostics"] = {}
        return payload


def verify_cmapss(
    dataset: str,
    train_path: str | Path,
    test_path: str | Path,
    rul_path: str | Path,
    *,
    expectations: dict[str, Any] | None = None,
) -> CMapssVerificationReport:
    dataset = dataset.upper()
    expected = (
        expectations if expectations is not None else CMAPSS_EXPECTATIONS.get(dataset)
    )
    if expected is None:
        return _empty_report(
            dataset,
            train_path,
            test_path,
            rul_path,
            ("unknown dataset; expected FD001-FD004",),
        )
    paths = (Path(train_path), Path(test_path), Path(rul_path))
    hashes: list[str] = []
    errors: list[str] = []
    for path in paths:
        if not path.is_file():
            errors.append(f"source file does not exist: {path}")
            hashes.append("")
        else:
            try:
                hashes.append(sha256_path(path))
            except OSError as error:
                errors.append(f"source file cannot be read: {error}")
                hashes.append("")
    for name, actual, key in zip(
        ("train", "test", "rul"), hashes, ("train_sha256", "test_sha256", "rul_sha256")
    ):
        if expected.get(key) and actual != expected[key]:
            errors.append(
                f"{name}_sha256 mismatch: expected {expected[key]}, got {actual}"
            )
    train_rows, train_units, train_errors = _parse_trajectory(paths[0], "train")
    test_rows, test_units, test_errors = _parse_trajectory(paths[1], "test")
    rul_count, rul_errors = _parse_rul(paths[2])
    errors.extend((*train_errors, *test_errors, *rul_errors))
    if rul_count != test_units:
        errors.append(
            f"rul_count mismatch: expected one RUL value per test unit ({test_units}), got {rul_count}"
        )
    for name, actual, key in (
        ("train_rows", train_rows, "train_rows"),
        ("train_units", train_units, "train_units"),
        ("test_rows", test_rows, "test_rows"),
        ("test_units", test_units, "test_units"),
        ("rul_count", rul_count, "rul_count"),
    ):
        if expected.get(key) is not None and actual != expected[key]:
            errors.append(f"{name} mismatch: expected {expected[key]}, got {actual}")
    return CMapssVerificationReport(
        dataset,
        str(paths[0]),
        str(paths[1]),
        str(paths[2]),
        hashes[0],
        hashes[1],
        hashes[2],
        train_rows,
        train_units,
        test_rows,
        test_units,
        rul_count,
        unique_errors(errors),
    )


def cmapss_outcome_definitions() -> dict[str, OutcomeDefinition]:
    process = ObservationProcess(
        "cmapss engine trajectory", parameters=(("dataset", "cmapss"),)
    )
    return {
        "run_to_failure": OutcomeDefinition(
            "cmapss.run_to_failure.v1",
            "simulated engine run reaches failure",
            process,
            Window(None, "trajectory", "engine_unit"),
            (Threshold("terminal_failure", "=", 1),),
            "Simulated training trajectory terminal failure.",
        ),
        "rul": OutcomeDefinition(
            "cmapss.remaining_useful_life.v1",
            "remaining useful life at test observation",
            process,
            Window(1, "cycle", "engine_unit"),
            (Threshold("rul", ">=", 0),),
            "Right-censored simulated test trajectory RUL evidence.",
        ),
    }


def _parse_trajectory(path: Path, label: str) -> tuple[int, int, tuple[str, ...]]:
    if not path.is_file():
        return 0, 0, (f"{label} file does not exist: {path}",)
    rows = units = 0
    last_cycles: dict[int, int] = {}
    errors: list[str] = []
    try:
        with path.open("r", encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, start=1):
                if not line.strip():
                    continue
                fields = line.split()
                if len(fields) != 26:
                    errors.append(
                        f"{label} row {line_number}: expected 26 numeric fields, got {len(fields)}"
                    )
                    continue
                try:
                    values = [float(value) for value in fields]
                    if not values[0].is_integer() or not values[1].is_integer():
                        errors.append(
                            f"{label} row {line_number}: unit and cycle must be integers"
                        )
                        continue
                    unit = int(values[0])
                    cycle = int(values[1])
                except ValueError:
                    errors.append(f"{label} row {line_number}: non-numeric field")
                    continue
                if not all(math.isfinite(value) for value in values):
                    errors.append(f"{label} row {line_number}: fields must be finite")
                if unit <= 0 or cycle <= 0:
                    errors.append(
                        f"{label} row {line_number}: unit and cycle must be positive"
                    )
                previous = last_cycles.get(unit)
                if previous is None:
                    units += 1
                elif cycle != previous + 1:
                    errors.append(
                        f"{label} row {line_number}: unit {unit} cycle gap or duplicate after {previous}: got {cycle}"
                    )
                last_cycles[unit] = cycle
                rows += 1
    except (OSError, UnicodeError) as error:
        errors.append(f"{label} parsing failed: {error}")
    return rows, units, unique_errors(errors)


def _parse_rul(path: Path) -> tuple[int, tuple[str, ...]]:
    if not path.is_file():
        return 0, (f"RUL file does not exist: {path}",)
    count = 0
    errors: list[str] = []
    try:
        with path.open("r", encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, start=1):
                if not line.strip():
                    continue
                try:
                    value = float(line.strip())
                except ValueError:
                    errors.append(f"RUL row {line_number}: value must be numeric")
                    continue
                if not math.isfinite(value) or value < 0:
                    errors.append(
                        f"RUL row {line_number}: value must be finite and non-negative"
                    )
                count += 1
    except (OSError, UnicodeError) as error:
        errors.append(f"RUL parsing failed: {error}")
    return count, unique_errors(errors)


def _empty_report(
    dataset: str,
    train: str | Path,
    test: str | Path,
    rul: str | Path,
    errors: tuple[str, ...],
) -> CMapssVerificationReport:
    return CMapssVerificationReport(
        dataset, str(train), str(test), str(rul), "", "", "", 0, 0, 0, 0, 0, errors
    )
