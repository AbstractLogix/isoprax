from __future__ import annotations

from pathlib import Path

from mypy import api

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "pyproject.toml"
TYPECHECK = ROOT / "tests" / "typecheck"


def _check(*paths: Path) -> tuple[str, str, int]:
    return api.run(
        [
            "--config-file",
            str(CONFIG),
            *(str(path) for path in paths),
        ]
    )


def test_valid_typed_evidence_example_passes_mypy() -> None:
    stdout, stderr, status = _check(TYPECHECK / "valid.py")
    assert status == 0, stdout + stderr


def test_unsafe_evidence_examples_fail_for_expected_reasons() -> None:
    cases = {
        "missing_calibration.py": "Missing positional argument",
        "mismatched_calibration.py": "incompatible type",
        "swapped_calibration.py": "incompatible type",
        "raw_outcome.py": "incompatible type",
        "plain_result_without_proof.py": "incompatible type",
        "forge_calibration.py": "Missing positional argument",
        "forge_authorization.py": "Missing positional argument",
    }
    paths = tuple(TYPECHECK / name for name in cases)
    stdout, stderr, status = _check(*paths)
    output = stdout + stderr

    assert status != 0
    for name, diagnostic in cases.items():
        assert name in output
        assert diagnostic.lower() in output.lower()
    assert output.count(": error:") >= len(cases)
