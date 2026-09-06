from dataclasses import replace

import pytest

from isoprax.admission import (
    AdmissionProfile,
    AdmissionReport,
    CorpusProvenance,
    GateResult,
    PredeclarationEvidence,
    SplitDefinition,
    evaluate_admission,
)
from isoprax.corpus_assembly import (
    CorpusAssemblyProfile,
    ReplayCaptureInput,
    assemble_corpus,
)
from isoprax.evidence_reporting import EvidenceReportProfile, build_evidence_report
from isoprax.replay_capture import (
    DeploymentEvidence,
    ObservationArtifactEvidence,
    ObservationEvidence,
    ReplayCaptureRecord,
    ReplayLaneDefinition,
)


def splits():
    return (
        SplitDefinition("train", "2026-09-01T00:00:00+00:00", "2026-09-10T00:00:00+00:00"),
        SplitDefinition("calibration_fit", "2026-09-10T00:00:00+00:00", "2026-09-15T00:00:00+00:00"),
        SplitDefinition("calibration_gate", "2026-09-15T00:00:00+00:00", "2026-09-20T00:00:00+00:00"),
        SplitDefinition("test", "2026-09-20T00:00:00+00:00", "2026-09-30T00:00:00+00:00"),
    )


def capture(**changes):
    lane = ReplayLaneDefinition("system-a", "service-a", "change-a", "workload-v1", "PT10M", "threshold-v1", "v1", "public synthetic replay evidence", "2026-09-02T00:00:00Z", "2026-09-02T00:00:00Z", "2026-09-02T00:10:00Z")
    deployment = DeploymentEvidence("target-a", "change-a", "succeeded", "2026-09-02T00:00:01Z", "2026-09-02T00:00:02Z", "deployment-a")
    observation = ObservationEvidence("2026-09-02T00:00:00Z", "2026-09-02T00:00:00Z", "2026-09-02T00:10:00Z", True, True, True, True, False, False, "public synthetic replay evidence", (), {"secret": b"payload"}, "observed")
    base = ReplayCaptureRecord("capture-a", lane, "qualification-a", "execution-a", deployment, observation, (), "observed_positive", None)
    return replace(base, **changes)


def assembly_profile():
    return CorpusAssemblyProfile("system-a", "PT10M", "threshold-v1", "public synthetic replay evidence", frozenset({"diff_size"}), frozenset({"future"}), splits(), ("manifest.json",))


def inputs(capture_record=None):
    return [ReplayCaptureInput(capture_record or capture(), {"diff_size": 4}, {"diff_size": "2026-09-02T00:00:00Z"})]


def report_profile(assembly):
    return EvidenceReportProfile(assembly.profile_identity, "public synthetic replay evidence", "predeclaration-hash", "anchor://predeclaration", ("manifest.json",), ("build_qualification", "runner_execution", "capture_artifacts"))


def admission_profile():
    return AdmissionProfile(frozenset({"diff_size"}), frozenset({"future"}), "PT10M", True, 0, 0, splits(), "public synthetic replay evidence", True, expected_system_id="system-a", predeclaration_evidence=PredeclarationEvidence("predeclaration-hash", "anchor://predeclaration", "2026-08-01T00:00:00+00:00", "2026-09-01T00:00:00+00:00"), corpus_provenance=CorpusProvenance("system-a", False, False), published_artifacts=("manifest.json",))


def evidence():
    assembled = assemble_corpus(assembly_profile(), inputs())
    profile = admission_profile()
    return assembled, profile, evaluate_admission(list(assembled.rows), profile)


def test_builds_deterministic_safe_report():
    assembled, profile, admission = evidence()
    first = build_evidence_report(report_profile(assembled), assembled, [capture()], profile, admission)
    second = build_evidence_report(report_profile(assembled), assembled, [capture()], profile, admission)

    assert first.report_identity == second.report_identity
    assert first.to_dict() == second.to_dict()
    assert first.status == "blocked"
    assert first.capture_evidence[0]["execution_identity"] == "execution-a"
    assert "diff_size" not in str(first.to_dict())
    assert "payload" not in str(first.to_dict())
    assert "Semantic" in first.claim_boundary


def test_reports_unavailable_and_censoring_without_upgrading_claims():
    censored = capture(outcome_class="censored", censor_reason="monitoring gap")
    assembled = assemble_corpus(assembly_profile(), inputs(censored))
    profile = admission_profile()
    result = build_evidence_report(report_profile(assembled), assembled, [censored], profile, evaluate_admission(list(assembled.rows), profile))

    assert result.status == "blocked"
    assert result.counts["censored"] == 1
    assert any(item.category == "capture_artifacts" for item in result.unavailable_evidence)
    assert "Full Conformance" in result.claim_boundary


def test_distinguishes_complete_admission_evidence_from_inconclusive():
    assembled, profile, admission = evidence()
    passed = AdmissionReport(
        True,
        (GateResult("all", True, "passed"),),
        admission.counts_by_split,
        admission.manifest,
    )
    complete_profile = replace(
        report_profile(assembled),
        required_evidence_categories=("build_qualification", "runner_execution"),
    )
    assert (
        build_evidence_report(complete_profile, assembled, [capture()], profile, passed).status
        == "admission_evidence"
    )
    assert (
        build_evidence_report(report_profile(assembled), assembled, [capture()], profile, passed).status
        == "inconclusive"
    )


@pytest.mark.parametrize(
    "profile_change, assembly_change, capture_change, admission_profile_change",
    [
        ({"release_scope": "other"}, {}, {}, {}),
        ({}, {"claim_scope": "other"}, {}, {}),
        ({}, {}, {"claim_scope": "other"}, {}),
        ({}, {}, {}, {"corpus_provenance": CorpusProvenance("system-a", True, False)}),
    ],
)
def test_rejects_unsafe_reporting_inputs(profile_change, assembly_change, capture_change, admission_profile_change):
    assembled, profile, admission = evidence()
    with pytest.raises(ValueError):
        build_evidence_report(replace(report_profile(assembled), **profile_change), replace(assembled, **assembly_change), [replace(capture(), **capture_change)], replace(profile, **admission_profile_change), admission)


def test_rejects_remaining_profile_and_capture_contract_failures():
    assembled, profile, admission = evidence()
    report_profile_value = report_profile(assembled)
    with pytest.raises(ValueError):
        EvidenceReportProfile("", "scope", "hash", "anchor", ("artifact",), ("runner",))
    with pytest.raises(ValueError):
        EvidenceReportProfile("id", "scope", "hash", "anchor", ("artifact", "artifact"), ("runner",))
    cases = (
        (replace(assembled, manifest_input={**assembled.manifest_input, "published_artifacts": ()}), [capture()], profile),
        (assembled, [capture()], replace(profile, published_artifacts=("other",))),
        (assembled, [capture()], replace(profile, predeclaration_evidence=None)),
        (assembled, [capture()], replace(profile, corpus_provenance=None)),
        (assembled, [replace(capture(), deployment=None)], profile),
        (assembled, [replace(capture(), observation=replace(capture().observation, uses_private_production_data=True))], profile),
        (assembled, [], profile),
        (assembled, [capture(), capture()], profile),
        (assembled, [replace(capture(), lane_identity="other")], profile),
    )
    for candidate_assembly, captures, candidate_profile in cases:
        with pytest.raises(ValueError):
            build_evidence_report(report_profile_value, candidate_assembly, captures, candidate_profile, admission)


def test_collected_artifacts_complete_the_required_evidence_category():
    assembled, profile, admission = evidence()
    complete_capture = replace(
        capture(),
        artifacts=(ObservationArtifactEvidence("result.json", "collected", "a" * 64, 1),),
    )
    passed = AdmissionReport(True, (), admission.counts_by_split, admission.manifest)
    result = build_evidence_report(report_profile(assembled), assembled, [complete_capture], profile, passed)

    assert result.status == "admission_evidence"
    assert not result.unavailable_evidence


def test_blank_build_or_runner_references_are_explicitly_unavailable():
    incomplete = capture(qualification_report_hash="", execution_identity="")
    assembled = assemble_corpus(assembly_profile(), inputs(incomplete))
    profile = admission_profile()
    admission = evaluate_admission(list(assembled.rows), profile)
    passed = AdmissionReport(True, (), admission.counts_by_split, admission.manifest)
    report = build_evidence_report(
        replace(
            report_profile(assembled),
            required_evidence_categories=("build_qualification", "runner_execution"),
        ),
        assembled,
        [incomplete],
        profile,
        passed,
    )

    assert report.status == "inconclusive"
    assert {item.category for item in report.unavailable_evidence} == {
        "build_qualification",
        "runner_execution",
    }
