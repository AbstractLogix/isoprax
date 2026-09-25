from dataclasses import asdict

import pytest

from isoprax.commensurability import (
    Attestation,
    IncommensurableError,
    ObservationProcess,
    OutcomeDefinition,
    Threshold,
    Window,
    _as_string_mapping,
    _coerce_thresholds,
    check_commensurable,
    require_commensurable,
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


def test_mixed_numeric_and_text_threshold_values_have_deterministic_order():
    numeric = Threshold("error_rate", ">", 1)
    textual = Threshold("error_rate", ">", "unknown")
    left = definition(thresholds=(numeric, textual))
    right = definition("b", thresholds=(textual, numeric))

    assert check_commensurable(left, right).level == "direct"


@pytest.mark.parametrize(
    "changes",
    [
        {"id": " "},
        {"event": " "},
        {"observation_process": " "},
        {"observation_process": {}},
        {"window": " "},
        {"window": {}},
        {"window": {"duration": 7, "unit": "day", "anchor": " "}},
    ],
)
def test_incomplete_outcome_definitions_are_rejected(changes):
    with pytest.raises(ValueError):
        definition(**changes)


def test_incomplete_domain_values_cannot_be_constructed_directly():
    with pytest.raises(ValueError, match="observation_process.kind"):
        ObservationProcess("", (), "")
    with pytest.raises(ValueError, match="window.anchor"):
        Window(None, "", "", "")


@pytest.mark.parametrize(
    "value, extra, error, message",
    [
        (float("nan"), {}, ValueError, "threshold.value must be finite"),
        (True, {}, TypeError, "threshold.value must be a number"),
        (
            0.2,
            {"sustain": float("inf")},
            ValueError,
            "threshold.sustain must be finite",
        ),
        (0.2, {"sustain": -1}, ValueError, "threshold.sustain must not be negative"),
        (
            0.2,
            {"sustain_unit": 42},
            TypeError,
            "threshold.sustain_unit must be a string",
        ),
    ],
)
def test_direct_threshold_construction_rejects_invalid_values(
    value, extra, error, message
):
    with pytest.raises(error, match=message):
        Threshold("rate", ">", value, **extra)


@pytest.mark.parametrize(
    "values, message",
    [
        ((42, ">", 0.2), "threshold.metric must be a string"),
        (("rate", 42, 0.2), "threshold.operator must be a string"),
        (("rate", ">", 0.2, None, "", 42), "threshold.raw must be a string"),
        ((" ", ">", 0.2), "threshold.metric must not be empty"),
    ],
)
def test_direct_threshold_construction_rejects_invalid_text_fields(values, message):
    with pytest.raises((TypeError, ValueError), match=message):
        Threshold(*values)


def test_window_mismatch_is_bridgeable_but_not_automatically_poolable():
    result = check_commensurable(
        definition(),
        definition("b", window=Window(90, "day", "after_change")),
    )

    assert result.level == "bridgeable"
    assert result.differing_fields == ["window"]
    assert not result.pooling_allowed


def test_retained_observations_only_mark_bridgeability():
    result = check_commensurable(
        definition(),
        definition("b", window=Window(90, "day", "after_change")),
        retained_observations=True,
    )

    assert result.level == "bridgeable"
    assert not result.pooling_allowed


def test_retained_observations_do_not_authorize_pooling_before_rederivation():
    left = definition()
    right = definition("b", window=Window(90, "day", "after_change"))

    result = check_commensurable(
        left,
        right,
        retained_observations=True,
    )

    assert result.level == "bridgeable"
    assert not result.commensurable
    assert not result.pooling_allowed
    with pytest.raises(IncommensurableError):
        require_commensurable(left, right, retained_observations=True)


def test_attestation_does_not_upgrade_non_commensurable_definitions():
    result = check_commensurable(
        definition(),
        definition("b", window=Window(90, "day", "after_change")),
        attestation=Attestation(
            "reviewer", "same event semantics", "a", "b", "review/42"
        ),
    )

    assert result.level == "bridgeable"
    assert not result.commensurable
    assert not result.pooling_allowed
    assert result.attestation is not None
    with pytest.raises(IncommensurableError):
        require_commensurable(
            definition(),
            definition("b", window=Window(90, "day", "after_change")),
            attestation=result.attestation,
        )


def test_event_mismatch_is_irreducible_even_with_attestation():
    result = check_commensurable(
        definition(),
        definition("b", event="different event"),
        attestation=Attestation("reviewer", "not enough", "a", "b", "review/43"),
    )

    assert result.level == "irreducible"
    assert not result.pooling_allowed


def test_decision_projection_keeps_the_existing_fields_and_reason_values():
    left = definition("left")
    direct = check_commensurable(left, definition("right"))
    attestation = Attestation("reviewer", "same event", "left", "right", "ref")
    attestation_result = check_commensurable(
        left,
        definition("right", thresholds=(Threshold("error_rate", ">", 0.3),)),
        attestation=attestation,
    )
    bridgeable = check_commensurable(
        left,
        definition("right", window=Window(90, "day", "after_change")),
    )
    bridgeable_with_observations = check_commensurable(
        left,
        definition("right", window=Window(90, "day", "after_change")),
        retained_observations=True,
    )
    irreducible = check_commensurable(left, definition("right", event="other"))

    decision_fields = {
        "commensurable",
        "left_id",
        "right_id",
        "differing_fields",
        "reason",
        "level",
        "pooling_allowed",
        "attestation",
    }
    projections = [
        asdict(result)
        for result in (
            direct,
            attestation_result,
            bridgeable,
            bridgeable_with_observations,
            irreducible,
        )
    ]

    assert all(set(projection) == decision_fields for projection in projections)
    assert [
        (p["commensurable"], p["level"], p["pooling_allowed"]) for p in projections
    ] == [
        (True, "direct", True),
        (False, "bridgeable", False),
        (False, "bridgeable", False),
        (False, "bridgeable", False),
        (False, "irreducible", False),
    ]
    assert [p["reason"] for p in projections] == [
        "same structured definition",
        "window/threshold mismatch may be re-derived from retained observations",
        "window/threshold mismatch may be re-derived from retained observations",
        "window/threshold mismatch may be re-derived from retained observations",
        "event or observation process mismatch is irreducible; calibration does not lift this",
    ]


def test_outcome_definition_stores_normalized_domain_values_and_round_trips():
    definition = OutcomeDefinition(
        id=" normalized ",
        event=" Defect Detected ",
        observation_process={"kind": " TELEMETRY ", "parameters": {"source": "ci"}},
        window={"duration": 7, "unit": " DAY ", "anchor": " AFTER_CHANGE "},
        thresholds=[{"metric": "ERROR_RATE", "operator": ">", "value": 0.2}],
    )

    assert isinstance(definition.observation_process, ObservationProcess)
    assert isinstance(definition.window, Window)
    assert isinstance(definition.thresholds, tuple)
    assert isinstance(definition.thresholds[0], Threshold)
    assert definition.event == "defect detected"
    assert definition.to_dict() == OutcomeDefinition(**definition.to_dict()).to_dict()


def test_malformed_nested_semantic_input_fails_explicitly():
    with pytest.raises(TypeError, match="sample must be a mapping"):
        _as_string_mapping(42, "sample")
    with pytest.raises(TypeError, match="parameters"):
        ObservationProcess.from_value({"kind": "telemetry", "parameters": 42})
    with pytest.raises(TypeError, match="pairs"):
        ObservationProcess.from_value({"kind": "telemetry", "parameters": [["source"]]})
    with pytest.raises(TypeError, match="threshold.value"):
        Threshold.from_value({"metric": "rate", "operator": ">", "value": True})
    with pytest.raises(ValueError, match="finite"):
        Window.from_value({"duration": float("nan"), "unit": "day", "anchor": "x"})
    with pytest.raises(TypeError, match="keys must be strings"):
        ObservationProcess.from_value({1: "telemetry"})
    with pytest.raises(TypeError, match="kind must be a string"):
        ObservationProcess.from_value({"kind": 42})
    with pytest.raises(TypeError, match="duration must be a finite number"):
        Window.from_value({"duration": True, "unit": "day", "anchor": "x"})
    with pytest.raises(TypeError, match="string or mapping"):
        ObservationProcess.from_value(42)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="string or mapping"):
        Window.from_value(42)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="threshold.value must be finite"):
        Threshold.from_value({"metric": "rate", "value": float("nan")})
    with pytest.raises(TypeError, match="threshold must be a string or mapping"):
        Threshold.from_value(42)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="thresholds must be a string, list, or tuple"):
        _coerce_thresholds({"metric": "rate"})  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="named provenance"):
        Attestation("", "reason", "left", "right", "ref").validate("left", "right")
    with pytest.raises(ValueError, match="do not match"):
        Attestation("reviewer", "reason", "other", "right", "ref").validate(
            "left", "right"
        )


@pytest.mark.parametrize(
    "parser, value",
    [
        (
            ObservationProcess.from_value,
            {"kind": "telemetry", "unrecognized_label_rule": "severity=high"},
        ),
        (
            Window.from_value,
            {"duration": 7, "unit": "day", "anchor": "after_change", "timezone": "UTC"},
        ),
        (
            Threshold.from_value,
            {"metric": "rate", "operator": ">", "value": 0.2, "inclusive": True},
        ),
    ],
)
def test_unknown_semantic_mapping_fields_are_rejected(parser, value):
    with pytest.raises(ValueError, match="unsupported fields"):
        parser(value)
