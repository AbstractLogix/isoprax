from __future__ import annotations

import json
import math
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from tests.haskell_kernel_oracle import OracleError, python_reference

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "haskell" / "isoprax-kernel"
FIXTURES = ROOT / "tests" / "reference"


class DuplicateKey(ValueError):
    pass


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKey(key)
        result[key] = value
    return result


def _fixture_oracle(path: Path) -> tuple[str, dict[str, Any] | None]:
    raw = path.read_text(encoding="utf-8")
    try:
        request = json.loads(raw, object_pairs_hook=_unique_pairs)
    except DuplicateKey:
        return raw, {"error": {"category": "duplicate_key"}}
    try:
        return raw, python_reference(request)
    except OracleError as error:
        return raw, {"error": {"category": error.category}}


def _compact_json(raw: str) -> str:
    """Remove JSON whitespace while preserving duplicate keys and number lexemes."""
    compact: list[str] = []
    in_string = False
    escaped = False
    for character in raw:
        if in_string:
            compact.append(character)
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
        elif character == '"':
            in_string = True
            compact.append(character)
        elif not character.isspace():
            compact.append(character)
    return "".join(compact)


def _command() -> list[str]:
    configured = os.environ.get("ISOPRAX_KERNEL_COMMAND")
    if configured:
        return shlex.split(configured)
    binary = os.environ.get("ISOPRAX_KERNEL_BIN")
    if binary:
        return [binary]
    cabal = shutil.which("cabal")
    if cabal is None:
        pytest.skip(
            "Haskell CLI unavailable; this differential test is not counted as "
            "passing. Set ISOPRAX_KERNEL_COMMAND or ISOPRAX_KERNEL_BIN, or "
            "install the pinned GHC/Cabal toolchain"
        )
    result = subprocess.run(
        [cabal, "list-bin", "isoprax-kernel"],
        cwd=PACKAGE,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.skip(
            "Haskell CLI unavailable; auto-detected Cabal could not resolve the "
            f"kernel package: {result.stderr.strip()}"
        )
    return [result.stdout.strip()]


def _assert_equal(actual: Any, expected: Any, path: str = "$") -> None:
    if isinstance(actual, dict) and isinstance(expected, dict):
        assert actual.keys() == expected.keys(), f"{path}: keys differ"
        for key in expected:
            _assert_equal(actual[key], expected[key], f"{path}.{key}")
    elif isinstance(actual, list) and isinstance(expected, list):
        assert len(actual) == len(expected), f"{path}: lengths differ"
        for index, (left, right) in enumerate(zip(actual, expected, strict=True)):
            _assert_equal(left, right, f"{path}[{index}]")
    elif isinstance(actual, bool) or isinstance(expected, bool):
        assert actual is expected, f"{path}: {actual!r} != {expected!r}"
    elif isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
        assert math.isclose(float(actual), float(expected), rel_tol=0, abs_tol=1e-12), (
            f"{path}: {actual!r} != {expected!r}"
        )
    else:
        assert actual == expected, f"{path}: {actual!r} != {expected!r}"


def test_shared_python_haskell_fixtures() -> None:
    fixture_paths = sorted(FIXTURES.rglob("*.json"))
    assert fixture_paths, "reference fixture corpus is empty"
    fixture_data = [_fixture_oracle(path) for path in fixture_paths]
    raw_requests = [_compact_json(raw) for raw, _ in fixture_data]
    process = subprocess.run(
        _command(),
        cwd=PACKAGE,
        input="\n".join(raw_requests) + "\n",
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert process.returncode == 0, process.stderr
    response_lines = process.stdout.splitlines()
    assert len(response_lines) == len(fixture_data), (
        f"CLI returned {len(response_lines)} responses for {len(fixture_data)} fixtures: "
        f"{process.stderr}"
    )
    for path, response_line, (_, expected) in zip(
        fixture_paths, response_lines, fixture_data, strict=True
    ):
        actual = json.loads(response_line)
        assert actual.pop("version") == 1, f"{path}: unexpected protocol version"
        if expected is None:
            continue
        if "error" in expected:
            assert (
                actual.get("error", {}).get("category") == expected["error"]["category"]
            ), path
        else:
            assert "error" not in actual, f"{path}: unexpected error {actual['error']}"
            _assert_equal(actual, expected, str(path.relative_to(ROOT)))
