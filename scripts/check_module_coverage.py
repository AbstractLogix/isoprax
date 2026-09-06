"""Fail CI when any production module falls below the branch-aware threshold."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("--minimum", type=float, default=95.0)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    failures: list[str] = []
    for filename, details in sorted(report["files"].items()):
        path = Path(filename)
        if path.parent.name != "isoprax" or path.name == "__init__.py":
            continue
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
