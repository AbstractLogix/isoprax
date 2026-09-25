from __future__ import annotations

import pytest

from isoprax.commensurability import (
    IncommensurableError,
    OutcomeDefinition,
    check_commensurable,
)
from isoprax.evaluation import authorized_pooled_ece
from isoprax.semantic_types import (
    _EVIDENCE_SEAL,
    CalibrationEvidence,
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


def test_evidence_tokens_cannot_be_forged_with_an_unrecognized_seal():
    with pytest.raises(TypeError, match="validator"):
        CalibrationEvidence(object(), "left", object(), "digest")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="validator"):
        CommensurabilityEvidence(object(), "left", "right", object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="validator"):
        PooledComparisonAuthorization(
            object(), "left", "right", "left-digest", "right-digest"
        )  # type: ignore[arg-type]


def test_evidence_constructor_rechecks_poolability_and_result_ids():
    left = _definition("left")
    right = _definition("right")
    direct_result = check_commensurable(left, right)
    assert direct_result.pooling_allowed

    with pytest.raises(ValueError, match="IDs do not match"):
        CommensurabilityEvidence(_EVIDENCE_SEAL, "other", "right", direct_result)
    irreducible = check_commensurable(left, _definition("different", event="other"))
    with pytest.raises(ValueError, match="must permit pooling"):
        CommensurabilityEvidence(_EVIDENCE_SEAL, "left", "different", irreducible)  # type: ignore[arg-type]


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
