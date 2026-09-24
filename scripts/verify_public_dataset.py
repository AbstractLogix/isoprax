#!/usr/bin/env python3
"""Run Isoprax public-dataset verifiers against explicit local artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from isoprax.apachejit import verify_apachejit_csv
from isoprax.metropt3 import read_metropt3_intervals, verify_metropt3_csv
from isoprax.nasa_cmaps import verify_cmapss


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    apache = subparsers.add_parser("apachejit", help="verify ApacheJIT CSV")
    apache.add_argument("path", type=Path)
    apache.add_argument("--json", action="store_true", dest="as_json")

    cmapss = subparsers.add_parser("cmapss", help="verify one NASA C-MAPSS subset")
    cmapss.add_argument(
        "--dataset", required=True, choices=("FD001", "FD002", "FD003", "FD004")
    )
    cmapss.add_argument("--train", required=True, type=Path)
    cmapss.add_argument("--test", required=True, type=Path)
    cmapss.add_argument("--rul", required=True, type=Path)
    cmapss.add_argument("--json", action="store_true", dest="as_json")

    metro = subparsers.add_parser("metropt3", help="verify MetroPT-3 CSV and anchors")
    metro.add_argument("path", type=Path)
    metro.add_argument("--intervals", required=True, type=Path)
    metro.add_argument("--json", action="store_true", dest="as_json")

    args = parser.parse_args(argv)
    if args.command == "apachejit":
        report = verify_apachejit_csv(args.path)
    elif args.command == "cmapss":
        report = verify_cmapss(args.dataset, args.train, args.test, args.rul)
    else:
        try:
            intervals = read_metropt3_intervals(args.intervals)
            report = verify_metropt3_csv(args.path, intervals)
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
            payload: dict[str, Any] = {
                "dataset_id": "metropt3",
                "verified": False,
                "artifact": {"path": str(args.path), "sha256": ""},
                "observed": {},
                "diagnostics": {},
                "errors": [f"interval manifest error: {error}"],
                "warnings": [],
            }
            return _emit(payload, args.as_json)
    return _emit(report.to_dict(), args.as_json)


def _emit(payload: dict[str, Any], as_json: bool) -> int:
    if as_json:
        print(json.dumps(payload, sort_keys=True))
    else:
        print(
            f"{payload.get('dataset', payload.get('dataset_id', 'dataset'))}: {'VERIFIED' if payload.get('verified') else 'FAILED'}"
        )
        for error in payload.get("errors", []):
            print(f"error: {error}")
        for warning in payload.get("warnings", []):
            print(f"warning: {warning}")
    return 0 if payload.get("verified") else 1


if __name__ == "__main__":
    raise SystemExit(main())
