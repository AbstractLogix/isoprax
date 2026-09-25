from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from isoprax.commensurability import (
    Attestation,
    ObservationProcess,
    OutcomeDefinition,
    Threshold,
    check_commensurable,
)
from isoprax.evaluation import cross_family_report
from isoprax.identity import canonical_json, content_hash


@settings(max_examples=1000, deadline=None)
@given(
    kind=st.text(max_size=30).filter(lambda value: bool(value.strip())),
    key=st.text(max_size=20),
    value=st.text(max_size=30),
)
def test_observation_normalization_is_stable(kind: str, key: str, value: str) -> None:
    original = ObservationProcess.from_value(
        {"kind": f" {kind} ", "parameters": {key: value}}
    )
    assert ObservationProcess.from_value(original).canonical() == original.canonical()


@settings(max_examples=1000, deadline=None)
@given(
    left=st.one_of(st.integers(), st.text(max_size=20)),
    right=st.one_of(st.integers(), st.text(max_size=20)),
)
def test_threshold_order_is_semantically_irrelevant_for_mixed_values(
    left: int | str, right: int | str
) -> None:
    first = Threshold("rate", ">", left)
    second = Threshold("rate", ">", right)
    definition_a = OutcomeDefinition(
        "a", "event", "telemetry", "one day", [first, second]
    )
    definition_b = OutcomeDefinition(
        "b", "event", "telemetry", "one day", [second, first]
    )

    assert check_commensurable(definition_a, definition_b).level == "direct"


@settings(max_examples=1000, deadline=None)
@given(
    left_event=st.text(max_size=30).filter(lambda value: bool(value.strip())),
    right_event=st.text(max_size=30).filter(lambda value: bool(value.strip())),
    left_window=st.text(max_size=20).filter(lambda value: bool(value.strip())),
    right_window=st.text(max_size=20).filter(lambda value: bool(value.strip())),
)
def test_commensurability_is_reflexive_and_symmetric(
    left_event: str,
    right_event: str,
    left_window: str,
    right_window: str,
) -> None:
    left = OutcomeDefinition("left", left_event, "telemetry", left_window)
    right = OutcomeDefinition("right", right_event, "telemetry", right_window)
    self_result = check_commensurable(left, left)
    forward = check_commensurable(left, right)
    reverse = check_commensurable(right, left)

    assert self_result.level == "direct"
    assert forward.level == reverse.level
    assert forward.commensurable == reverse.commensurable
    assert forward.pooling_allowed == reverse.pooling_allowed
    assert forward.differing_fields == reverse.differing_fields


@settings(max_examples=1000, deadline=None)
@given(
    event=st.text(max_size=30).filter(lambda value: bool(value.strip())),
    justification=st.text(max_size=30),
)
def test_event_mismatch_stays_irreducible_even_with_attestation(
    event: str, justification: str
) -> None:
    left = OutcomeDefinition("left", event, "telemetry", "one day")
    right = OutcomeDefinition("right", f"{event}!", "telemetry", "one day")
    result = check_commensurable(
        left,
        right,
        attestation=Attestation(
            "reviewer", justification.strip() or "review", "left", "right", "ref"
        ),
    )

    assert result.level == "irreducible"
    assert not result.pooling_allowed


@settings(max_examples=1000, deadline=None)
@given(
    left=st.text(alphabet="abcdefghijk", min_size=1, max_size=20),
    right=st.text(alphabet="abcdefghijk", min_size=1, max_size=20),
    retained_observations=st.booleans(),
)
def test_window_mismatch_without_rederived_outcomes_fails_closed(
    left: str, right: str, retained_observations: bool
) -> None:
    left_definition = OutcomeDefinition("left", "event", "telemetry", left)
    right_definition = OutcomeDefinition("right", "event", "telemetry", right)
    if left_definition.window.canonical() == right_definition.window.canonical():
        right_definition = OutcomeDefinition("right", "event", "telemetry", f"{right}!")

    result = check_commensurable(
        left_definition,
        right_definition,
        retained_observations=retained_observations,
    )

    assert result.level == "bridgeable"
    assert not result.commensurable
    assert not result.pooling_allowed


@settings(max_examples=1000, deadline=None)
@given(value=st.integers())
def test_malformed_observation_parameters_are_rejected(value: int) -> None:
    try:
        ObservationProcess.from_value({"kind": "telemetry", "parameters": value})
    except TypeError:
        return
    raise AssertionError("malformed observation parameters were accepted")


@settings(max_examples=1000, deadline=None)
@given(
    identifier=st.text(min_size=1, max_size=24).filter(
        lambda value: bool(value.strip())
    ),
    event=st.text(min_size=1, max_size=30).filter(lambda value: bool(value.strip())),
    kind=st.text(min_size=1, max_size=20).filter(lambda value: bool(value.strip())),
    window=st.text(min_size=1, max_size=20).filter(lambda value: bool(value.strip())),
)
def test_normalized_identity_serialization_and_hash_are_deterministic(
    identifier: str, event: str, kind: str, window: str
) -> None:
    definition = OutcomeDefinition(
        identifier,
        event,
        {"kind": f" {kind} ", "parameters": {"source": "ci"}},
        window,
        [Threshold("rate", ">", 0.5)],
    )
    payload = definition.to_dict()
    restored_payload = OutcomeDefinition(**payload).to_dict()

    assert canonical_json(payload) == canonical_json(restored_payload)
    assert content_hash(payload) == content_hash(restored_payload)


@settings(max_examples=1000, deadline=None)
@given(
    event=st.text(max_size=24).filter(lambda value: bool(value.strip())),
    window=st.text(max_size=20).filter(lambda value: bool(value.strip())),
)
def test_calibration_never_upgrades_stage0_structural_claim(
    event: str, window: str
) -> None:
    left = OutcomeDefinition("left", event, "telemetry", window)
    right = OutcomeDefinition("right", event, "telemetry", window)
    report = cross_family_report(
        "change",
        left,
        [0.0, 1.0],
        [0, 1],
        "operational",
        right,
        [0.0, 1.0],
        [0, 1],
        min_events=2,
        n_bins=2,
        max_ece=0.0,
    )

    assert report.pooled_ece == 0.0
    assert report.declarable_class.startswith("Cross-Family Conformance (Structural)")
