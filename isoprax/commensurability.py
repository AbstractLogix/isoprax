"""Outcome definitions and graded commensurability (Isoprax spec Section 5.6)."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import (
    Literal,
    TypeAlias,
    cast,
)

ThresholdValue: TypeAlias = int | float | str | None
DefinitionField: TypeAlias = Literal[
    "event", "observation_process", "window", "thresholds"
]
CommensurabilityLevel: TypeAlias = Literal["direct", "bridgeable", "irreducible"]


class IncommensurableError(ValueError):
    """Raised when non-commensurable scores would be jointly reasoned about."""


def _as_string_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a mapping")
    entries = cast(Mapping[object, object], value)
    if any(not isinstance(key, str) for key in entries):
        raise TypeError(f"{field_name} keys must be strings")
    return cast(Mapping[str, object], entries)


def _reject_unknown_fields(
    data: Mapping[str, object], field_name: str, allowed: frozenset[str]
) -> None:
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise ValueError(f"{field_name} contains unsupported fields: {unknown}")


def _string_value(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    return value


def _optional_number(value: object, field_name: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be a finite number or null")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field_name} must be finite")
    return number


@dataclass(frozen=True)
class ObservationProcess:
    kind: str
    parameters: tuple[tuple[str, str], ...] = ()
    raw: str = ""

    def __post_init__(self) -> None:
        kind = _string_value(self.kind, "observation_process.kind").strip().lower()
        if not kind:
            raise ValueError("observation_process.kind must not be empty")
        raw = _string_value(self.raw, "observation_process.raw")
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "raw", raw)

    @classmethod
    def from_value(cls, value: ObservationInput) -> ObservationProcess:
        if isinstance(value, cls):
            return value
        if isinstance(value, Mapping):
            data = _as_string_mapping(value, "observation_process")
            _reject_unknown_fields(
                data,
                "observation_process",
                frozenset({"kind", "parameters", "raw"}),
            )
            parameters = data.get("parameters", {})
            if isinstance(parameters, Mapping):
                parameter_map = _as_string_mapping(
                    parameters, "observation_process.parameters"
                )
                params = tuple(
                    sorted((key, str(item)) for key, item in parameter_map.items())
                )
            elif isinstance(parameters, (list, tuple)):
                pairs: list[tuple[str, str]] = []
                for item in parameters:
                    if not isinstance(item, (list, tuple)) or len(item) != 2:
                        raise TypeError(
                            "observation_process.parameters entries must be pairs"
                        )
                    pairs.append((str(item[0]), str(item[1])))
                params = tuple(pairs)
            else:
                raise TypeError(
                    "observation_process.parameters must be a mapping or pair list"
                )
            return cls(
                _string_value(data.get("kind", ""), "observation_process.kind")
                .strip()
                .lower(),
                params,
                _string_value(data.get("raw", ""), "observation_process.raw"),
            )
        if not isinstance(value, str):
            raise TypeError("observation_process must be a string or mapping")
        raw = value.strip()
        return cls(kind=raw.lower(), raw=raw)

    def canonical(self) -> tuple[str, tuple[tuple[str, str], ...], str]:
        return (self.kind.strip().lower(), self.parameters, self.raw.strip().lower())


@dataclass(frozen=True)
class Window:
    duration: float | None
    unit: str
    anchor: str
    raw: str = ""

    def __post_init__(self) -> None:
        duration = _optional_number(self.duration, "window.duration")
        if duration is not None and duration < 0:
            raise ValueError("window.duration must not be negative")
        unit = _string_value(self.unit, "window.unit").strip().lower()
        anchor = _string_value(self.anchor, "window.anchor").strip().lower()
        raw = _string_value(self.raw, "window.raw")
        if not anchor:
            raise ValueError("window.anchor must not be empty")
        if duration is not None and not unit:
            raise ValueError("window.unit is required when duration is set")
        if not unit and not raw:
            raise ValueError("window requires a unit or legacy description")
        object.__setattr__(self, "duration", duration)
        object.__setattr__(self, "unit", unit)
        object.__setattr__(self, "anchor", anchor)
        object.__setattr__(self, "raw", raw)

    @classmethod
    def from_value(cls, value: WindowInput) -> Window:
        if isinstance(value, cls):
            return value
        if isinstance(value, Mapping):
            data = _as_string_mapping(value, "window")
            _reject_unknown_fields(
                data,
                "window",
                frozenset({"duration", "unit", "anchor", "raw"}),
            )
            return cls(
                _optional_number(data.get("duration"), "window.duration"),
                _string_value(data.get("unit", ""), "window.unit").strip().lower(),
                _string_value(data.get("anchor", ""), "window.anchor").strip().lower(),
                _string_value(data.get("raw", ""), "window.raw"),
            )
        if not isinstance(value, str):
            raise TypeError("window must be a string or mapping")
        raw = value.strip()
        return cls(None, "", raw.lower(), raw)

    def canonical(self) -> tuple[float | None, str, str]:
        return (self.duration, self.unit.strip().lower(), self.anchor.strip().lower())


@dataclass(frozen=True)
class Threshold:
    metric: str
    operator: str
    value: ThresholdValue
    sustain: float | None = None
    sustain_unit: str = ""
    raw: str = ""

    def __post_init__(self) -> None:
        metric = _string_value(self.metric, "threshold.metric").strip().lower()
        if not metric:
            raise ValueError("threshold.metric must not be empty")
        operator = _string_value(self.operator, "threshold.operator").strip()
        value = self.value
        if isinstance(value, bool) or not isinstance(
            value, (int, float, str, type(None))
        ):
            raise TypeError("threshold.value must be a number, string, or null")
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("threshold.value must be finite")
        sustain = _optional_number(self.sustain, "threshold.sustain")
        if sustain is not None and sustain < 0:
            raise ValueError("threshold.sustain must not be negative")
        sustain_unit = (
            _string_value(self.sustain_unit, "threshold.sustain_unit").strip().lower()
        )
        raw = _string_value(self.raw, "threshold.raw")
        object.__setattr__(self, "metric", metric)
        object.__setattr__(self, "operator", operator)
        object.__setattr__(self, "sustain", sustain)
        object.__setattr__(self, "sustain_unit", sustain_unit)
        object.__setattr__(self, "raw", raw)

    @classmethod
    def from_value(cls, value: ThresholdInput) -> Threshold:
        if isinstance(value, cls):
            return value
        if isinstance(value, Mapping):
            data = _as_string_mapping(value, "threshold")
            _reject_unknown_fields(
                data,
                "threshold",
                frozenset(
                    {"metric", "operator", "value", "sustain", "sustain_unit", "raw"}
                ),
            )
            threshold_value = data.get("value")
            if isinstance(threshold_value, bool) or not isinstance(
                threshold_value, (int, float, str, type(None))
            ):
                raise TypeError("threshold.value must be a number, string, or null")
            if isinstance(threshold_value, float) and not math.isfinite(
                threshold_value
            ):
                raise ValueError("threshold.value must be finite")
            return cls(
                _string_value(data.get("metric", ""), "threshold.metric")
                .strip()
                .lower(),
                _string_value(data.get("operator", ""), "threshold.operator").strip(),
                threshold_value,
                _optional_number(data.get("sustain"), "threshold.sustain"),
                _string_value(data.get("sustain_unit", ""), "threshold.sustain_unit")
                .strip()
                .lower(),
                _string_value(data.get("raw", ""), "threshold.raw"),
            )
        if not isinstance(value, str):
            raise TypeError("threshold must be a string or mapping")
        raw = value.strip()
        return cls(metric=raw.lower(), operator="", value=None, raw=raw)

    def canonical(
        self,
    ) -> tuple[str, str, ThresholdValue, float | None, str]:
        return (
            self.metric.strip().lower(),
            self.operator.strip(),
            self.value,
            self.sustain,
            self.sustain_unit.strip().lower(),
        )


ObservationInput: TypeAlias = ObservationProcess | str | Mapping[str, object]
WindowInput: TypeAlias = Window | str | Mapping[str, object]
ThresholdInput: TypeAlias = Threshold | str | Mapping[str, object]
ThresholdsInput: TypeAlias = tuple[ThresholdInput, ...] | list[ThresholdInput] | str


@dataclass(frozen=True)
class Attestation:
    """Provenance metadata that cannot override fieldwise commensurability."""

    attestor: str
    justification: str
    left_definition_id: str
    right_definition_id: str
    provenance: str

    def validate(self, left: str, right: str) -> None:
        if not all(
            value.strip()
            for value in (
                self.attestor,
                self.justification,
                self.provenance,
                self.left_definition_id,
                self.right_definition_id,
            )
        ):
            raise ValueError("attestation requires named provenance and justification")
        if {self.left_definition_id, self.right_definition_id} != {left, right}:
            raise ValueError("attestation definitions do not match comparison")


def _coerce_thresholds(value: ThresholdsInput) -> tuple[Threshold, ...]:
    if isinstance(value, str):
        return () if not value.strip() else (Threshold.from_value(value),)
    if not isinstance(value, (list, tuple)):
        raise TypeError("thresholds must be a string, list, or tuple")
    return tuple(Threshold.from_value(item) for item in value)


@dataclass(frozen=True, init=False)
class OutcomeDefinition:
    """A normalized declaration of the event a probability describes."""

    id: str
    event: str
    observation_process: ObservationProcess
    window: Window
    thresholds: tuple[Threshold, ...]
    description: str

    def __init__(
        self,
        id: str,
        event: str,
        observation_process: ObservationInput,
        window: WindowInput,
        thresholds: ThresholdsInput = (),
        description: str = "",
    ) -> None:
        identifier = _string_value(id, "id")
        if not identifier.strip():
            raise ValueError("outcome definition id must not be empty")
        normalized_event = _string_value(event, "event").strip().lower()
        if not normalized_event:
            raise ValueError("event must not be empty")
        object.__setattr__(self, "id", identifier)
        object.__setattr__(self, "event", normalized_event)
        object.__setattr__(
            self,
            "observation_process",
            ObservationProcess.from_value(observation_process),
        )
        object.__setattr__(self, "window", Window.from_value(window))
        object.__setattr__(self, "thresholds", _coerce_thresholds(thresholds))
        object.__setattr__(
            self, "description", _string_value(description, "description")
        )

    def comparison_key(self) -> tuple[object, ...]:
        canonical_thresholds = tuple(
            sorted(
                (threshold.canonical() for threshold in self.thresholds),
                key=repr,
            )
        )
        return (
            self.event,
            self.observation_process.canonical(),
            self.window.canonical(),
            canonical_thresholds,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "event": self.event,
            "observation_process": {
                "kind": self.observation_process.kind,
                "parameters": self.observation_process.parameters,
                "raw": self.observation_process.raw,
            },
            "window": {
                "duration": self.window.duration,
                "unit": self.window.unit,
                "anchor": self.window.anchor,
                "raw": self.window.raw,
            },
            "thresholds": [
                {
                    "metric": threshold.metric,
                    "operator": threshold.operator,
                    "value": threshold.value,
                    "sustain": threshold.sustain,
                    "sustain_unit": threshold.sustain_unit,
                    "raw": threshold.raw,
                }
                for threshold in self.thresholds
            ],
            "description": self.description,
        }


@dataclass(frozen=True)
class DirectCommensurability:
    left_id: str
    right_id: str
    differing_fields: list[DefinitionField]
    reason: str
    commensurable: Literal[True] = field(default=True, init=False)
    level: Literal["direct"] = field(default="direct", init=False)
    pooling_allowed: Literal[True] = field(default=True, init=False)
    attestation: Attestation | None = field(default=None, init=False)


@dataclass(frozen=True)
class BridgeableCommensurability:
    left_id: str
    right_id: str
    differing_fields: list[DefinitionField]
    reason: str
    attestation: Attestation | None = None
    commensurable: Literal[False] = field(default=False, init=False)
    level: Literal["bridgeable"] = field(default="bridgeable", init=False)
    pooling_allowed: Literal[False] = field(default=False, init=False)


@dataclass(frozen=True)
class BridgeableWithObservations:
    left_id: str
    right_id: str
    differing_fields: list[DefinitionField]
    reason: str
    attestation: Attestation | None = None
    commensurable: Literal[False] = field(default=False, init=False)
    level: Literal["bridgeable"] = field(default="bridgeable", init=False)
    pooling_allowed: Literal[False] = field(default=False, init=False)


@dataclass(frozen=True)
class IrreducibleCommensurability:
    left_id: str
    right_id: str
    differing_fields: list[DefinitionField]
    reason: str
    attestation: Attestation | None = None
    commensurable: Literal[False] = field(default=False, init=False)
    level: Literal["irreducible"] = field(default="irreducible", init=False)
    pooling_allowed: Literal[False] = field(default=False, init=False)


CommensurabilityResult: TypeAlias = (
    DirectCommensurability
    | BridgeableCommensurability
    | BridgeableWithObservations
    | IrreducibleCommensurability
)
PoolableCommensurabilityResult: TypeAlias = DirectCommensurability


def check_commensurable(
    a: OutcomeDefinition,
    b: OutcomeDefinition,
    *,
    attestation: Attestation | None = None,
    retained_observations: bool = False,
) -> CommensurabilityResult:
    """Compare definitions; attestations do not override field differences."""

    fields: tuple[DefinitionField, ...] = (
        "event",
        "observation_process",
        "window",
        "thresholds",
    )
    left = a.comparison_key()
    right = b.comparison_key()
    differing: list[DefinitionField] = [
        name
        for name, left_value, right_value in zip(fields, left, right)
        if left_value != right_value
    ]
    if not differing:
        return DirectCommensurability(a.id, b.id, [], "same structured definition")

    if attestation is not None:
        attestation.validate(a.id, b.id)

    if set(differing).issubset({"window", "thresholds"}):
        bridge_reason = (
            "window/threshold mismatch may be re-derived from retained observations"
        )
        bridge_type = (
            BridgeableWithObservations
            if retained_observations
            else BridgeableCommensurability
        )
        return bridge_type(a.id, b.id, differing, bridge_reason, attestation)

    return IrreducibleCommensurability(
        a.id,
        b.id,
        differing,
        "event or observation process mismatch is irreducible; calibration does not lift this",
        attestation,
    )


def require_commensurable(
    a: OutcomeDefinition,
    b: OutcomeDefinition,
    *,
    attestation: Attestation | None = None,
    retained_observations: bool = False,
) -> PoolableCommensurabilityResult:
    """Require the same pooling policy exposed by ``check_commensurable``."""
    result = check_commensurable(
        a,
        b,
        attestation=attestation,
        retained_observations=retained_observations,
    )
    if not result.pooling_allowed:
        raise IncommensurableError(result.reason)
    return result


class OutcomeDefinitionRegistry:
    """Resolves persisted Outcome Definitions carried by Signals (spec 6)."""

    def __init__(self) -> None:
        self._defs: dict[str, OutcomeDefinition] = {}

    def register(self, definition: OutcomeDefinition) -> OutcomeDefinition:
        existing = self._defs.get(definition.id)
        if existing is not None and existing != definition:
            raise ValueError(
                f"outcome definition id '{definition.id}' already registered with different content"
            )
        self._defs[definition.id] = definition
        return definition

    def resolve(self, definition_id: str) -> OutcomeDefinition:
        if definition_id not in self._defs:
            raise KeyError(f"unresolvable outcome_definition_id '{definition_id}'")
        return self._defs[definition_id]

    def __contains__(self, definition_id: object) -> bool:
        return definition_id in self._defs

    def ids(self) -> list[str]:
        return sorted(self._defs)
