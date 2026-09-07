from isoprax.commensurability import (
    Attestation,
    OutcomeDefinition,
    Threshold,
    Window,
    check_commensurable,
)


def definition(identifier="a", **changes):
    values = {
        "id": identifier,
        "event": "defect detected",
        "observation_process": {"kind": "telemetry", "parameters": {"source": "ci"}},
        "window": Window(7, "day", "after_change"),
        "thresholds": (Threshold("error_rate", ">", 0.2, 60, "second"),),
    }
    values.update(changes)
    return OutcomeDefinition(**values)


def test_structured_definitions_ignore_threshold_serialization_order():
    left = definition()
    right = definition(
        "b",
        thresholds=(Threshold("error_rate", ">", 0.2, 60, "second"),),
    )

    result = check_commensurable(left, right)

    assert result.level == "direct"
    assert result.pooling_allowed


def test_window_mismatch_is_bridgeable_but_not_automatically_poolable():
    result = check_commensurable(
        definition(),
        definition("b", window=Window(90, "day", "after_change")),
    )

    assert result.level == "bridgeable"
    assert result.differing_fields == ["window"]
    assert not result.pooling_allowed


def test_retained_observations_make_bridgeable_path_explicit():
    result = check_commensurable(
        definition(),
        definition("b", window=Window(90, "day", "after_change")),
        retained_observations=True,
    )

    assert result.level == "bridgeable"
    assert result.pooling_allowed


def test_attestation_requires_named_provenance_and_matching_definitions():
    result = check_commensurable(
        definition(),
        definition("b", window=Window(90, "day", "after_change")),
        attestation=Attestation(
            "reviewer", "same event semantics", "a", "b", "review/42"
        ),
    )

    assert result.level == "attested"
    assert result.commensurable
    assert result.attestation is not None


def test_event_mismatch_is_irreducible_even_with_attestation():
    result = check_commensurable(
        definition(),
        definition("b", event="different event"),
        attestation=Attestation("reviewer", "not enough", "a", "b", "review/43"),
    )

    assert result.level == "irreducible"
    assert not result.pooling_allowed
