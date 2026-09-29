from __future__ import annotations

from types import SimpleNamespace

import pytest

from isoprax.commensurability import (
    IncommensurableError,
    OutcomeDefinition,
    check_commensurable,
)
from isoprax.evaluation import authorized_pooled_ece, expected_calibration_error
from isoprax.semantic_types import (
    _EVIDENCE_SEAL,
    CalibrationEvidence,
    CalibrationPolicy,
    CommensurabilityEvidence,
    PooledComparisonAuthorization,
    authorize_pooled_comparison,
    calibration_sample_digest,
    establish_calibration,
    establish_commensurability,
)


class LeftOutcome:
    """Static marker for the left declared outcome family."""


class RightOutcome:
    """Static marker for the right declared outcome family."""


@pytest.mark.parametrize(
    "args, error, message",
    [
        ((True, 10, 0.05), TypeError, "min_events"),
        ((-1, 10, 0.05), ValueError, "min_events"),
        ((500, True, 0.05), TypeError, "n_bins"),
        ((500, 0, 0.05), ValueError, "n_bins"),
        ((500, 10, True), TypeError, "max_ece"),
        ((500, 10, float("nan")), ValueError, "max_ece"),
        ((500, 10, 1.1), ValueError, "max_ece"),
    ],
)
def test_calibration_policy_rejects_invalid_values(args, error, message):
    with pytest.raises(error, match=message):
        CalibrationPolicy(*args)


@pytest.mark.parametrize(
    "definition_id, definition_digest, sample_digest, qualification, message",
    [
        (
            " ",
            "definition-digest",
            "sample-digest",
            SimpleNamespace(passes=True, n_events=500, n_bins=10, max_ece=0.05),
            "definition ID",
        ),
        (
            "left",
            "",
            "sample-digest",
            SimpleNamespace(passes=True, n_events=500, n_bins=10, max_ece=0.05),
            "definition-content digest",
        ),
        (
            "left",
            "definition-digest",
            "",
            SimpleNamespace(passes=True, n_events=500, n_bins=10, max_ece=0.05),
            "sample digest",
        ),
        (
            "left",
            "definition-digest",
            "sample-digest",
            SimpleNamespace(passes=False, n_events=500, n_bins=10, max_ece=0.05),
            "passing qualification",
        ),
        (
            "left",
            "definition-digest",
            "sample-digest",
            SimpleNamespace(passes=True, n_events=499, n_bins=10, max_ece=0.05),
            "event policy",
        ),
        (
            "left",
            "definition-digest",
            "sample-digest",
            SimpleNamespace(passes=True, n_events=500, n_bins=5, max_ece=0.05),
            "match its policy",
        ),
        (
            "left",
            "definition-digest",
            "sample-digest",
            SimpleNamespace(passes=True, n_events=500, n_bins=10, max_ece=0.1),
            "match its policy",
        ),
    ],
)
def test_calibration_evidence_rechecks_its_bound_invariants(
    definition_id, definition_digest, sample_digest, qualification, message
):
    with pytest.raises(ValueError, match=message):
        CalibrationEvidence(
            _EVIDENCE_SEAL,
            definition_id,
            definition_digest,
            qualification,
            sample_digest,
            CalibrationPolicy(500, 10, 0.05),
        )


def _definition(
    identifier: str, *, event: str = "defect detected"
) -> OutcomeDefinition:
    return OutcomeDefinition(
        id=identifier,
        event=event,
        observation_process={"kind": "telemetry", "parameters": {"source": "ci"}},
        window={"duration": 7, "unit": "day", "anchor": "after_change"},
    )


def _passing_calibration(
    definition: OutcomeDefinition, tag: type[object]
) -> CalibrationEvidence[object]:
    scores = [float(index % 2) for index in range(500)]
    outcomes = [index % 2 for index in range(500)]
    return establish_calibration(
        definition,
        scores,
        outcomes,
        tag=tag,
    )


def test_authorized_pooling_requires_bound_commensurability_and_calibration():
    left = _definition("left")
    right = _definition("right")
    scores = [float(index % 2) for index in range(500)]
    outcomes = [index % 2 for index in range(500)]
    commensurability = establish_commensurability(
        left,
        right,
        left_tag=LeftOutcome,
        right_tag=RightOutcome,
    )
    left_calibration = establish_calibration(left, scores, outcomes, tag=LeftOutcome)
    right_calibration = establish_calibration(right, scores, outcomes, tag=RightOutcome)

    authorization = authorize_pooled_comparison(
        commensurability,
        left_calibration,
        right_calibration,
    )

    assert authorization.left_definition_id == "left"
    assert authorization.right_definition_id == "right"
    assert authorization.left_definition_content_digest == (
        left_calibration.definition_content_digest
    )
    assert authorization.right_definition_content_digest == (
        right_calibration.definition_content_digest
    )
    assert (
        left_calibration.calibration_policy_digest
        == left_calibration.calibration_policy.digest
    )
    assert (
        authorized_pooled_ece(
            authorization,
            scores,
            outcomes,
            scores,
            outcomes,
        )
        == 0.0
    )


def test_irreducible_definitions_cannot_produce_pooling_evidence():
    with pytest.raises(IncommensurableError):
        establish_commensurability(
            _definition("left"),
            _definition("right", event="different event"),
            left_tag=LeftOutcome,
            right_tag=RightOutcome,
        )


def test_retained_observations_cannot_create_pooling_evidence():
    with pytest.raises(IncommensurableError):
        establish_commensurability(
            _definition("left"),
            OutcomeDefinition("right", "defect detected", "telemetry", "90 days"),
            left_tag=LeftOutcome,
            right_tag=RightOutcome,
            retained_observations=True,
        )


def test_failed_calibration_cannot_produce_calibration_evidence():
    with pytest.raises(ValueError, match="insufficient labeled events"):
        establish_calibration(
            _definition("left"),
            [0.2],
            [0],
            tag=LeftOutcome,
        )


def test_fractional_calibration_outcomes_are_rejected_before_normalization():
    definition = _definition("left")
    scores = [float(index % 2) for index in range(500)]
    fractional_outcomes = [float(index % 2) + 0.25 for index in range(500)]

    with pytest.raises(ValueError, match="binary integers"):
        establish_calibration(
            definition,
            scores,
            fractional_outcomes,  # type: ignore[arg-type]
            tag=LeftOutcome,
        )

    with pytest.raises(ValueError, match="binary integers"):
        calibration_sample_digest(scores, fractional_outcomes)  # type: ignore[arg-type]


def test_concrete_definition_id_mismatch_is_rejected_at_runtime():
    left = _definition("left")
    right = _definition("right")
    relation = establish_commensurability(
        left,
        right,
        left_tag=LeftOutcome,
        right_tag=RightOutcome,
    )
    wrong_left = _passing_calibration(_definition("not-left"), LeftOutcome)
    right_calibration = _passing_calibration(right, RightOutcome)

    with pytest.raises(ValueError, match="left calibration evidence"):
        authorize_pooled_comparison(relation, wrong_left, right_calibration)

    left_calibration = _passing_calibration(left, LeftOutcome)
    wrong_right = _passing_calibration(_definition("not-right"), RightOutcome)
    with pytest.raises(ValueError, match="right calibration evidence"):
        authorize_pooled_comparison(relation, left_calibration, wrong_right)


def test_reused_definition_id_with_different_content_cannot_reuse_evidence():
    current_left = _definition("left", event="new semantics")
    right = _definition("right", event="new semantics")
    old_left = _definition("left", event="old semantics")
    scores = [float(index % 2) for index in range(500)]
    outcomes = [index % 2 for index in range(500)]
    relation = establish_commensurability(
        current_left,
        right,
        left_tag=LeftOutcome,
        right_tag=RightOutcome,
    )

    with pytest.raises(ValueError, match="left calibration evidence.*content"):
        authorize_pooled_comparison(
            relation,
            establish_calibration(old_left, scores, outcomes, tag=LeftOutcome),
            establish_calibration(right, scores, outcomes, tag=RightOutcome),
        )


def test_right_reused_definition_id_with_different_content_cannot_reuse_evidence():
    left = _definition("left", event="new semantics")
    current_right = _definition("right", event="new semantics")
    old_right = _definition("right", event="old semantics")
    relation = establish_commensurability(
        left,
        current_right,
        left_tag=LeftOutcome,
        right_tag=RightOutcome,
    )

    with pytest.raises(ValueError, match="right calibration evidence.*content"):
        authorize_pooled_comparison(
            relation,
            _passing_calibration(left, LeftOutcome),
            _passing_calibration(old_right, RightOutcome),
        )


@pytest.mark.parametrize(
    "right_policy",
    [
        {"min_events": 400, "n_bins": 5, "max_ece": 1.0},
        {"min_events": 500, "n_bins": 10, "max_ece": 1.0},
        {"min_events": 500, "n_bins": 5, "max_ece": 0.9},
    ],
)
def test_authorization_rejects_different_calibration_policies(right_policy):
    left = _definition("left")
    right = _definition("right")
    scores = [float(index % 2) for index in range(500)]
    outcomes = [index % 2 for index in range(500)]
    relation = establish_commensurability(
        left,
        right,
        left_tag=LeftOutcome,
        right_tag=RightOutcome,
    )
    left_calibration = establish_calibration(
        left,
        scores,
        outcomes,
        tag=LeftOutcome,
        min_events=500,
        n_bins=5,
        max_ece=1.0,
    )
    right_calibration = establish_calibration(
        right,
        scores,
        outcomes,
        tag=RightOutcome,
        **right_policy,
    )

    with pytest.raises(ValueError, match="calibration policies must match"):
        authorize_pooled_comparison(relation, left_calibration, right_calibration)


def test_authorized_pooled_ece_uses_the_bound_calibration_policy():
    left = _definition("left")
    right = _definition("right")
    scores = [0.09] * 250 + [0.11] * 250
    outcomes = [0] * 250 + [1] * 250
    relation = establish_commensurability(
        left,
        right,
        left_tag=LeftOutcome,
        right_tag=RightOutcome,
    )
    left_calibration = establish_calibration(
        left,
        scores,
        outcomes,
        tag=LeftOutcome,
        min_events=500,
        n_bins=5,
        max_ece=1.0,
    )
    right_calibration = establish_calibration(
        right,
        scores,
        outcomes,
        tag=RightOutcome,
        min_events=500,
        n_bins=5,
        max_ece=1.0,
    )
    authorization = authorize_pooled_comparison(
        relation, left_calibration, right_calibration
    )

    assert authorization.calibration_policy == CalibrationPolicy(500, 5, 1.0)
    assert (
        authorization.calibration_policy_digest
        == authorization.calibration_policy.digest
    )
    expected = expected_calibration_error(
        [*scores, *scores], [*outcomes, *outcomes], n_bins=5
    )
    assert (
        authorized_pooled_ece(authorization, scores, outcomes, scores, outcomes)
        == expected
    )
    with pytest.raises(TypeError, match="unexpected keyword argument"):
        authorized_pooled_ece(
            authorization,
            scores,
            outcomes,
            scores,
            outcomes,
            n_bins=10,  # type: ignore[call-arg]
        )


def test_evidence_tokens_cannot_be_forged_with_an_unrecognized_seal():
    with pytest.raises(TypeError, match="validator"):
        CalibrationEvidence(
            object(),
            "left",
            "definition-digest",
            object(),
            "sample-digest",
            CalibrationPolicy(500, 10, 0.05),
        )  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="validator"):
        CommensurabilityEvidence(
            object(),
            "left",
            "right",
            "left-content",
            "right-content",
            object(),
        )  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="validator"):
        PooledComparisonAuthorization(
            object(),
            "left",
            "right",
            "left-content",
            "right-content",
            "left-digest",
            "right-digest",
            CalibrationPolicy(500, 10, 0.05),
        )  # type: ignore[arg-type]


def test_evidence_constructor_rechecks_poolability_and_result_ids():
    left = _definition("left")
    right = _definition("right")
    direct_result = check_commensurable(left, right)
    assert direct_result.pooling_allowed

    with pytest.raises(ValueError, match="IDs do not match"):
        CommensurabilityEvidence(
            _EVIDENCE_SEAL,
            "other",
            "right",
            "left-content",
            "right-content",
            direct_result,
        )
    with pytest.raises(ValueError, match="definition-content digests"):
        CommensurabilityEvidence(
            _EVIDENCE_SEAL,
            "left",
            "right",
            "",
            "right-content",
            direct_result,
        )
    irreducible = check_commensurable(left, _definition("different", event="other"))
    with pytest.raises(ValueError, match="must permit pooling"):
        CommensurabilityEvidence(
            _EVIDENCE_SEAL,
            "left",
            "different",
            "left-content",
            "different-content",
            irreducible,
        )  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "definition_digest, sample_digest, message",
    [
        ("", "right-content", "definition-content digests"),
        ("left-content", "", "calibration sample digests"),
    ],
)
def test_pooled_authorization_constructor_rechecks_bound_digests(
    definition_digest, sample_digest, message
):
    with pytest.raises(ValueError, match=message):
        PooledComparisonAuthorization(
            _EVIDENCE_SEAL,
            "left",
            "right",
            definition_digest,
            "right-content",
            sample_digest,
            "right-sample",
            CalibrationPolicy(500, 10, 0.05),
        )


def test_authorized_pooled_ece_rejects_unpaired_input_lengths():
    left = _definition("left")
    right = _definition("right")
    relation = establish_commensurability(
        left,
        right,
        left_tag=LeftOutcome,
        right_tag=RightOutcome,
    )
    authorization = authorize_pooled_comparison(
        relation,
        _passing_calibration(left, LeftOutcome),
        _passing_calibration(right, RightOutcome),
    )

    with pytest.raises(ValueError, match="left scores and outcomes"):
        authorized_pooled_ece(authorization, [0.1], [], [0.1], [0])


def test_authorized_pooled_ece_rejects_samples_outside_calibration_evidence():
    left = _definition("left")
    right = _definition("right")
    scores = [float(index % 2) for index in range(500)]
    outcomes = [index % 2 for index in range(500)]
    relation = establish_commensurability(
        left,
        right,
        left_tag=LeftOutcome,
        right_tag=RightOutcome,
    )
    authorization = authorize_pooled_comparison(
        relation,
        establish_calibration(left, scores, outcomes, tag=LeftOutcome),
        establish_calibration(right, scores, outcomes, tag=RightOutcome),
    )

    with pytest.raises(ValueError, match="left pooled samples do not match"):
        authorized_pooled_ece(authorization, [0.99], [0], [0.01], [1])
    with pytest.raises(ValueError, match="right pooled samples do not match"):
        authorized_pooled_ece(authorization, scores, outcomes, [0.01], [1])
