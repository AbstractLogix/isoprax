import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from scripts import flagship_paper_integrity as integrity

ROOT = Path(__file__).resolve().parents[1]


def _copy_package(destination: Path) -> Path:
    for relative in integrity.LOCKED_FILES | {
        str(integrity.LOCK),
        str(integrity.RESULTS),
        str(integrity.OUTPUT),
        str(integrity.TABLES),
    }:
        source = ROOT / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return destination


def test_flagship_integrity_reproduces_from_pinned_inputs() -> None:
    result = integrity.run(ROOT, write=False)

    assert result["claim_registry"]["total_claims"] == 36
    assert result["claim_registry"]["flagship_claims"] == 24
    assert result["claim_registry"]["companion_claims_excluded_from_reproduction"] == 12
    assert result["operation_gate_case_count"] == 23
    assert not (ROOT / "docs/experiments").exists()


def test_runner_provenance_uses_its_introduction_commit() -> None:
    registry = json.loads((ROOT / integrity.CLAIMS).read_text(encoding="utf-8"))
    runner_path = "scripts/flagship_paper_integrity.py"
    introduced = subprocess.run(
        ["git", "log", "--diff-filter=A", "--format=%H", "HEAD", "--", runner_path],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    assert introduced == [
        registry["provenance"]["standalone_runner_introduction_commit"]
    ]
    historical_bytes = subprocess.run(
        ["git", "show", f"{introduced[0]}:{runner_path}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    assert historical_bytes

    current_sha256 = hashlib.sha256((ROOT / runner_path).read_bytes()).hexdigest()
    references = [
        artifact
        for claim in registry["claims"]
        if claim["scope"] == "flagship"
        for artifact in claim.get("artifacts", [])
        if artifact.get("path") == runner_path
    ]
    assert len(references) == 21
    assert all(item["source_commit"] == introduced[0] for item in references)
    assert all(item["sha256"] == current_sha256 for item in references)


def test_altered_flagship_result_section_fails(tmp_path: Path) -> None:
    root = _copy_package(tmp_path / "copy")
    result_path = root / integrity.RESULTS
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["benchmark_a"]["lanes"][0]["metrics"]["brier_score"] = 0.99
    result_path.write_text(json.dumps(result), encoding="utf-8")

    with pytest.raises(ValueError, match="selected result section changed"):
        integrity.run(root, write=False)


def test_unrelated_shared_model_section_is_not_an_input(tmp_path: Path) -> None:
    root = _copy_package(tmp_path / "copy")
    result_path = root / integrity.RESULTS
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["shared_model"] = {"status": "deliberately changed outside flagship scope"}
    result_path.write_text(json.dumps(result), encoding="utf-8")

    integrity.run(root, write=False)


def test_companion_claim_cannot_add_local_artifact_dependency(tmp_path: Path) -> None:
    root = _copy_package(tmp_path / "copy")
    registry_path = root / integrity.CLAIMS
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    companion = next(
        claim for claim in registry["claims"] if claim["scope"] == "companion"
    )
    companion["artifacts"][0]["path"] = "docs/experiments/model-role-output.json"
    registry_path.write_text(json.dumps(registry), encoding="utf-8")

    with pytest.raises(ValueError, match="companion claim has a local dependency"):
        integrity._validate_claim_registry(root)


def test_source_hash_change_fails(tmp_path: Path) -> None:
    root = _copy_package(tmp_path / "copy")
    source_path = root / "isoprax/research_experiments.py"
    source_path.write_bytes(source_path.read_bytes() + b"\n# changed\n")

    with pytest.raises(ValueError, match="source hash mismatch"):
        integrity.run(root, write=False)


def test_changed_manuscript_number_fails(tmp_path: Path) -> None:
    root = _copy_package(tmp_path / "copy")
    paper_path = root / integrity.PAPER
    paper = paper_path.read_text(encoding="utf-8")
    paper_path.write_text(paper.replace("0.800", "0.801", 1), encoding="utf-8")

    with pytest.raises(ValueError, match="source hash mismatch"):
        integrity.run(root, write=False)


def test_altered_artifact_hash_fails(tmp_path: Path) -> None:
    root = _copy_package(tmp_path / "copy")
    lock_path = root / integrity.LOCK
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    entry = next(item for item in lock["files"] if item["path"] == "uv.lock")
    entry["sha256"] = "0" * 64
    lock_path.write_text(json.dumps(lock), encoding="utf-8")

    with pytest.raises(ValueError, match="source hash mismatch: uv.lock"):
        integrity.run(root, write=False)
