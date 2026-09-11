import copy
import importlib.util
import json
from pathlib import Path

import pytest

_SCRIPT_PATH = Path(__file__).parents[1] / "scripts/run_stage2_whoami_pilot.py"
_SPEC = importlib.util.spec_from_file_location("run_stage2_whoami_pilot", _SCRIPT_PATH)
assert _SPEC and _SPEC.loader
_PILOT = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PILOT)


def _predeclaration() -> dict[str, object]:
    return json.loads(_PILOT.PREDECLARATION_PATH.read_text(encoding="utf-8"))


def test_published_predeclaration_hash_matches_its_content():
    predecl = _predeclaration()
    assert _PILOT._predeclaration_hash(predecl) == predecl["artifact_hash"]


def test_tampered_predeclaration_is_rejected_before_provenance():
    predecl = copy.deepcopy(_predeclaration())
    predecl["workload"]["requests_per_commit"] = 121

    with pytest.raises(ValueError, match="artifact hash"):
        _PILOT._validate_predeclaration(
            predecl, "b8bd8cb9178ae936ebcabd54645633d5046ac018"
        )


def test_profile_definitions_use_declared_semantics():
    predecl = _predeclaration()
    definitions = predecl["outcome_definitions"]

    change = _PILOT._definition("change", definitions, "change_family")
    operational = _PILOT._definition("operational", definitions, "operational_family")

    assert change.observation_process.kind == definitions["observation_process"].lower()
    assert change.window.duration == definitions["window"]["duration"]
    assert change.thresholds[0].value == definitions["thresholds"][0]["value"]
    assert change.description == definitions["change_family"]
    assert operational.description == definitions["operational_family"]


def test_committed_predeclaration_passes_hash_and_ancestry_verification():
    provenance = _PILOT._validate_predeclaration(
        _predeclaration(), "b8bd8cb9178ae936ebcabd54645633d5046ac018"
    )

    assert provenance.ancestry_ok is True
    assert provenance.predeclared_before_data is True
