#!/usr/bin/env python3
"""Run the offline Stage 1 public-data validation adapters."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from isoprax.stage1_public_validation import build_stage1_public_validation_report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apachejit", type=Path, required=True)
    parser.add_argument("--google-trace", type=Path, required=True)
    parser.add_argument(
        "--predeclaration",
        type=Path,
        default=Path("docs/stage1/predeclaration.json"),
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_stage1_public_validation_report(
        args.apachejit,
        args.google_trace,
        predeclaration_path=args.predeclaration,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {"report_identity": report["report_identity"], "output": str(args.output)}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
