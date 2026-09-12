"""Create a Rekor-backed in-toto attestation for a Stage 2 predeclaration."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from isoprax.external_anchor import (
    DEFAULT_SUBJECT_NAME,
    IN_TOTO_STATEMENT_TYPE,
    PREDICATE_TYPE,
)
from isoprax.identity import content_hash


def _predeclaration_hash(predeclaration: dict[str, object]) -> str:
    payload = {
        key: value for key, value in predeclaration.items() if key != "artifact_hash"
    }
    return content_hash(payload)


def _statement(predeclaration: dict[str, object]) -> dict[str, object]:
    artifact_hash = str(predeclaration.get("artifact_hash", "")).strip()
    if not artifact_hash or _predeclaration_hash(predeclaration) != artifact_hash:
        raise ValueError("predeclaration artifact hash does not match its content")
    commit = str(predeclaration.get("predeclaration_commit", "")).strip()
    if not commit:
        raise ValueError("predeclaration_commit is required")
    return {
        "_type": IN_TOTO_STATEMENT_TYPE,
        "subject": [
            {"name": DEFAULT_SUBJECT_NAME, "digest": {"sha256": artifact_hash}}
        ],
        "predicateType": PREDICATE_TYPE,
        "predicate": {
            "artifact_hash": artifact_hash,
            "predeclaration_commit": commit,
            "external_anchor_reference": predeclaration.get(
                "external_anchor_reference", ""
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("predeclaration", type=Path)
    parser.add_argument("--bundle", type=Path, required=True)
    args = parser.parse_args()

    predeclaration = json.loads(args.predeclaration.read_text(encoding="utf-8"))
    if not isinstance(predeclaration, dict):
        raise ValueError("predeclaration must be a JSON object")
    statement = _statement(predeclaration)
    args.bundle.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix=".json", delete=False
    ) as predicate_file:
        json.dump(statement, predicate_file, indent=2, sort_keys=True)
        predicate_file.write("\n")
        predicate_path = Path(predicate_file.name)
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "sigstore",
                "attest",
                "--predicate",
                str(predicate_path),
                "--predicate-type",
                "https://isoprax.dev/predicates/stage2-predeclaration/v1",
                "--bundle",
                str(args.bundle),
                "--overwrite",
                str(args.predeclaration),
            ],
            check=True,
        )
    finally:
        predicate_path.unlink(missing_ok=True)
    print(json.dumps({"bundle": str(args.bundle), "status": "created"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
