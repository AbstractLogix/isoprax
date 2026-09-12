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


def test_whoami_pilot_publishes_non_estimable_yield_when_all_events_are_negative():
    data = json.loads(_PILOT.DATA_PATH.read_text(encoding="utf-8"))

    estimate = _PILOT._yield_estimate(data)

    assert estimate["status"] == "no_positive_events"
    assert estimate["implied_records"]["point_estimate"] is None
    assert estimate["planning_target"] == {"negative": 5, "positive": 5}


def test_checked_in_whoami_report_publishes_the_same_yield_estimate():
    data = json.loads(_PILOT.DATA_PATH.read_text(encoding="utf-8"))
    report_path = _PILOT.ROOT / "docs/stage2/whoami-pilot-report-v2.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert report["yield_estimate"] == _PILOT._yield_estimate(data)


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
    assert provenance.anchored is False


def test_thresholded_v3_predeclaration_is_sealed_without_relabeling_v2():
    path = _PILOT.ROOT / "docs/stage2/whoami-pilot-predeclaration-v3.json"
    predecl = json.loads(path.read_text(encoding="utf-8"))

    assert _PILOT._predeclaration_hash(predecl) == predecl["artifact_hash"]
    assert predecl["supersedes"] == "whoami-pilot-predeclaration-v2.json"
    assert predecl["outcome_definitions"]["thresholds"][0]["value"] == 0.00210252
    provenance = _PILOT._validate_predeclaration(
        predecl,
        _PILOT._git_output("rev-parse", "HEAD"),
        predeclaration_path=path,
    )

    assert provenance.ancestry_ok is True
    assert provenance.anchored is False


def test_unverified_anchor_produces_inconclusive_report_without_feasibility():
    predecl = _predeclaration()
    provenance = _PILOT._validate_predeclaration(
        predecl, "b8bd8cb9178ae936ebcabd54645633d5046ac018"
    )

    report = _PILOT._inconclusive_report(
        predecl, provenance, "b8bd8cb9178ae936ebcabd54645633d5046ac018"
    )

    assert report["status"] == "inconclusive"
    assert report["external_anchor_status"] == "unverified"
    assert report["external_anchor_verification"]["status"] == "unverified"
    assert "yield_estimate" not in report
    assert "feasibility_report" not in report
