#!/usr/bin/env python3
"""Measure one-shot Haskell CLI startup against Python in-process decisions."""

from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import math
import os
import platform
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "haskell" / "isoprax-kernel"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_python_reference() -> Any:
    oracle_path = ROOT / "tests" / "haskell_kernel_oracle.py"
    spec = importlib.util.spec_from_file_location("haskell_kernel_oracle", oracle_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load Python oracle at {oracle_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.python_reference


python_reference = _load_python_reference()


def _kernel_command() -> list[str]:
    configured = os.environ.get("ISOPRAX_KERNEL_COMMAND")
    if configured:
        return shlex.split(configured)
    binary = os.environ.get("ISOPRAX_KERNEL_BIN")
    if binary:
        return [binary]
    cabal = shutil.which("cabal")
    if cabal is None:
        raise SystemExit(
            "Haskell CLI unavailable; build the package or set ISOPRAX_KERNEL_BIN"
        )
    result = subprocess.run(
        [cabal, "list-bin", "isoprax-kernel"],
        cwd=PACKAGE,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(f"cabal list-bin failed: {result.stderr.strip()}")
    return [result.stdout.strip()]


def _definitions() -> tuple[dict[str, Any], dict[str, Any]]:
    common = {
        "event": "defect_detected",
        "observation_process": {
            "kind": "build outcome",
            "parameters": {"source": "benchmark"},
        },
        "window": {"duration": 7, "unit": "day", "anchor": "after_change"},
        "thresholds": [{"metric": "severity", "operator": ">=", "value": 2}],
    }
    return ({"id": "left", **common}, {"id": "right", **common})


def _workloads() -> dict[str, dict[str, Any]]:
    left, right = _definitions()
    return {
        "commensurability": {
            "version": 1,
            "operation": "commensurability",
            "left": left,
            "right": right,
        },
        "identity": {
            "version": 1,
            "operation": "identity",
            "value": {
                "definition": left,
                "evidence": {"source": "benchmark-fixture", "verified": True},
            },
        },
    }


def _run_kernel(command: list[str], request_line: str) -> dict[str, Any]:
    result = subprocess.run(
        command,
        cwd=PACKAGE,
        input=request_line + "\n",
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"kernel exited {result.returncode}: {result.stderr.strip()}"
        )
    try:
        response = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"kernel returned non-JSON output: {result.stdout[:200]!r}"
        ) from error
    if response.get("version") != 1 or "error" in response:
        raise RuntimeError(f"kernel rejected benchmark request: {response!r}")
    return response


def _run_python(request_line: str) -> dict[str, Any]:
    request = json.loads(request_line)
    return python_reference(request)


def _elapsed_ms(action: Any) -> float:
    started = time.perf_counter_ns()
    action()
    return (time.perf_counter_ns() - started) / 1_000_000


def _percentile(samples: list[float], percentile: float) -> float:
    ordered = sorted(samples)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return round(ordered[index], 4)


def _python_dependency_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for package in ("numpy", "scipy", "scikit-learn", "rfc8785"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = "unreported"
    return versions


def _measure(
    command: list[str], request: dict[str, Any], iterations: int
) -> dict[str, Any]:
    request_line = json.dumps(
        request, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )

    def kernel_call() -> dict[str, Any]:
        return _run_kernel(command, request_line)

    def python_call() -> dict[str, Any]:
        return _run_python(request_line)

    kernel_first = _elapsed_ms(kernel_call)
    kernel_samples = [_elapsed_ms(kernel_call) for _ in range(iterations)]
    python_first = _elapsed_ms(python_call)
    python_samples = [_elapsed_ms(python_call) for _ in range(iterations)]
    return {
        "haskell_cli": {
            "first_process_ms": round(kernel_first, 4),
            "warm_process_invocations": iterations,
            "p50_ms": _percentile(kernel_samples, 0.50),
            "p95_ms": _percentile(kernel_samples, 0.95),
        },
        "python_in_process": {
            "first_call_ms": round(python_first, 4),
            "warm_calls": iterations,
            "p50_ms": _percentile(python_samples, 0.50),
            "p95_ms": _percentile(python_samples, 0.95),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=100)
    args = parser.parse_args()
    if args.iterations < 100:
        parser.error("--iterations must be at least 100")

    command = _kernel_command()
    reports = {
        name: _measure(command, request, args.iterations)
        for name, request in _workloads().items()
    }
    print(
        json.dumps(
            {
                "schema_version": 1,
                "runtime": {
                    "python": sys.version.split()[0],
                    "python_dependencies": _python_dependency_versions(),
                    "platform": platform.platform(),
                    "processor": platform.processor() or "unreported",
                    "logical_cpus": os.cpu_count(),
                    "ghc": subprocess.run(
                        ["ghc", "--numeric-version"],
                        capture_output=True,
                        text=True,
                        check=False,
                    ).stdout.strip()
                    or "unreported",
                    "cabal": subprocess.run(
                        ["cabal", "--numeric-version"],
                        capture_output=True,
                        text=True,
                        check=False,
                    ).stdout.strip()
                    or "unreported",
                    "kernel_command": command,
                },
                "method": (
                    "Each Haskell sample starts a fresh CLI process. Warm means measured after "
                    "the first process, not a persistent server. Python samples run the matching "
                    "JSON request through the in-process reference adapter."
                ),
                "workloads": reports,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
