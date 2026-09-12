"""Fail CI when any production module falls below the branch-aware threshold."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _production_modules(source_root: Path) -> set[Path]:
    root = source_root.resolve()
    return {path.resolve() for path in root.glob("*.py") if path.name != "__init__.py"}


def _reported_production_files(report: dict, source_root: Path):
    root = source_root.resolve()
    for filename, details in report["files"].items():
        path = Path(filename).resolve()
        try:
            path.relative_to(root)
        except ValueError:
            continue
        if path.suffix == ".py" and path.name != "__init__.py":
            yield path, details


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("--source-root", type=Path, default=Path("isoprax"))
    parser.add_argument("--minimum", type=float, default=95.0)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    failures: list[str] = []
    expected = _production_modules(args.source_root)
    reported = dict(_reported_production_files(report, args.source_root))
    for path in sorted(expected - set(reported)):
        failures.append(f"{path}: missing coverage data")
    for path, details in sorted(reported.items()):
        covered = details["summary"]["percent_covered"]
        if covered < args.minimum:
            failures.append(f"{path}: {covered:.2f}% < {args.minimum:.2f}%")
    if failures:
        print("Per-module coverage gate failed:")
        print("\n".join(failures))
        return 1
    print(f"Every production module meets {args.minimum:.2f}% branch-aware coverage.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
