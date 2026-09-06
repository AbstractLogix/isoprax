from dataclasses import replace

import pytest

from isoprax.admission import SplitDefinition
from isoprax.corpus_assembly import (
    CorpusAssemblyProfile,
    ReplayCaptureInput,
    assemble_corpus,
)
from isoprax.replay_capture import (
    DeploymentEvidence,
    ObservationEvidence,
    ReplayCaptureRecord,
    ReplayLaneDefinition,
)


def profile(**changes):
    base = CorpusAssemblyProfile(
        expected_system_id="system-a",
        horizon_rule="PT10M",
        threshold_version="threshold-v1",
        release_scope="public synthetic replay evidence",
        allowed_prediction_fields=frozenset({"diff_size"}),
        forbidden_prediction_fields=frozenset({"future"}),
        split_definitions=(
            SplitDefinition(
                "train", "2026-09-01T00:00:00+00:00", "2026-09-10T00:00:00+00:00"
            ),
            SplitDefinition(
                "calibration_fit",
                "2026-09-10T00:00:00+00:00",
                "2026-09-15T00:00:00+00:00",
            ),
            SplitDefinition(
                "calibration_gate",
                "2026-09-15T00:00:00+00:00",
                "2026-09-20T00:00:00+00:00",
            ),
            SplitDefinition(
                "test", "2026-09-20T00:00:00+00:00", "2026-09-30T00:00:00+00:00"
            ),
        ),
        published_artifacts=("manifest.json",),
    )
    return replace(base, **changes)


def capture(**changes):
    lane = ReplayLaneDefinition(
        "system-a",
        "service-a",
        "change-a",
        "workload-v1",
        "PT10M",
        "threshold-v1",
        "v1",
        "public synthetic replay evidence",
        "2026-09-02T00:00:00Z",
        "2026-09-02T00:00:00Z",
        "2026-09-02T00:10:00Z",
    )
    deployment = DeploymentEvidence(
        "target-a",
        "change-a",
        "succeeded",
        "2026-09-02T00:00:01Z",
        "2026-09-02T00:00:02Z",
        "deployment-a",
    )
    observation = ObservationEvidence(
        "2026-09-02T00:00:00Z",
        "2026-09-02T00:00:00Z",
        "2026-09-02T00:10:00Z",
        True,
        True,
        True,
        True,
        False,
        False,
        "public synthetic replay evidence",
        (),
        {},
        "observed",
    )
    base = ReplayCaptureRecord(
        "capture-a",
        lane,
        "qualification-a",
        "execution-a",
        deployment,
        observation,
        (),
        "observed_positive",
        None,
    )
    return replace(base, **changes)


def item(capture_record=None, **changes):
    base = ReplayCaptureInput(
        capture_record or capture(),
        {"diff_size": 4},
        {"diff_size": "2026-09-02T00:00:00Z"},
    )
    return replace(base, **changes)


def test_assembles_deterministic_lineage_complete_row():
    first = assemble_corpus(profile(), [item()])
    same = assemble_corpus(profile(), [item()])

    assert len(first.rows) == 1
    assert first.rows[0].change_id == "change-a"
    assert first.rows[0].change_group_id == "change-a"
    assert first.rows[0].outcome_class == "observed_positive"
    assert first.rows[0].linkage_bases == ("immutable_capture_lineage",)
    assert first.rows[0].row_id == same.rows[0].row_id
    assert first.claim_scope == "corpus_assembly_evidence_only"


def test_preserves_censoring_and_orders_unordered_inputs():
    censored = capture(outcome_class="censored", censor_reason="monitoring gap")
    second = item(censored)
    first = item(capture(lane=replace(capture().lane, commit="change-b")))
    report = assemble_corpus(profile(), [second, first])

    assert [row.change_id for row in report.rows] == ["change-a", "change-b"]
    assert report.rows[0].outcome_class == "censored"
    assert report.rows[0].censor_reason == "monitoring gap"


def test_rejects_invalid_profile_capture_field_and_split_inputs():
    foreign = item(capture(lane=replace(capture().lane, system_id="other")))
    duplicate = [item(), item()]
    forbidden = item(
        prediction_fields={"future": 1},
        field_observed_at={"future": "2026-09-02T00:00:00Z"},
    )
    late = item(field_observed_at={"diff_size": "2026-09-02T00:00:01Z"})
    outside = item(
        capture(
            lane=replace(
                capture().lane,
                score_time="2026-10-01T00:00:00Z",
                window_start="2026-10-01T00:00:00Z",
                window_end="2026-10-01T00:10:00Z",
            )
        )
    )

    for inputs in ([foreign], [forbidden], [late], [outside]):
        report = assemble_corpus(profile(), inputs)
        assert not report.rows
        assert report.rejections

    duplicate_report = assemble_corpus(profile(), duplicate)
    assert len(duplicate_report.rows) == 1
    assert len(duplicate_report.rejections) == 1
    assert "duplicate" in duplicate_report.rejections[0].reason


def test_rejects_wrong_claim_scope_or_missing_lineage_without_raw_payloads():
    wrong_scope = item(capture(claim_scope="other"))
    missing_lineage = item(capture(deployment=None))
    report = assemble_corpus(profile(), [wrong_scope, missing_lineage])

    assert len(report.rejections) == 2
    assert all(rejection.reason for rejection in report.rejections)
    assert report.manifest_input["release_scope"] == "public synthetic replay evidence"


def test_profile_and_remaining_invalid_contract_paths_are_fail_closed():
    with pytest.raises(ValueError, match="metadata"):
        profile(expected_system_id="")
    with pytest.raises(ValueError, match="published"):
        profile(published_artifacts=())
    with pytest.raises(ValueError, match="must not overlap"):
        profile(
            split_definitions=(
                SplitDefinition(
                    "train",
                    "2026-09-01T00:00:00+00:00",
                    "2026-09-11T00:00:00+00:00",
                ),
                *profile().split_definitions[1:],
            )
        )

    too_late = item(
        capture(
            lane=replace(
                capture().lane,
                score_time="2026-09-09T23:00:00Z",
                window_start="2026-09-09T23:00:00Z",
                window_end="2026-09-10T01:00:00Z",
            )
        )
    )
    invalid_cases = (
        replace(item(), capture="bad"),
        replace(item(), capture=capture(outcome_class="unknown")),
        replace(item(), capture=capture(outcome_class="censored", censor_reason=None)),
        replace(item(), prediction_fields=[]),
        replace(item(), field_observed_at={"diff_size": "not-a-time"}),
        too_late,
    )
    for invalid in invalid_cases:
        report = assemble_corpus(profile(), [invalid])
        assert not report.rows
        assert len(report.rejections) == 1
