"""Verify a locally supplied AI4I 2020 CSV and print a JSON report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from isoprax.ai4i2020 import verify_ai4i2020_csv


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify a local AI4I 2020 CSV without network access."
    )
    parser.add_argument("csv_path", nargs="?", type=Path)
    args = parser.parse_args(arguments)
    report = verify_ai4i2020_csv(args.csv_path)
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    return 0 if report.verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
