"""Outcome Definitions and graded commensurability (spec Section 5.6)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


class IncommensurableError(ValueError):
    """Raised when non-commensurable scores would be jointly reasoned about."""


@dataclass(frozen=True)
class ObservationProcess:
    kind: str
    parameters: tuple[tuple[str, str], ...] = ()
    raw: str = ""

    @classmethod
    def from_value(
        cls, value: "ObservationProcess | str | Mapping[str, Any]"
    ) -> "ObservationProcess":
        if isinstance(value, cls):
            return value
        if isinstance(value, Mapping):
            parameters = value.get("parameters", {})
            if isinstance(parameters, list):
                params = tuple((str(item[0]), str(item[1])) for item in parameters)
            else:
                params = tuple(sorted((str(k), str(v)) for k, v in parameters.items()))
            return cls(
                str(value.get("kind", "")).strip().lower(),
                params,
                str(value.get("raw", "")),
            )
        raw = str(value).strip()
        return cls(kind=raw.lower(), raw=raw)

    def canonical(self) -> tuple[Any, ...]:
        return (self.kind.strip().lower(), self.parameters, self.raw.strip().lower())


@dataclass(frozen=True)
class Window:
    duration: float | None
    unit: str
    anchor: str
    raw: str = ""

    @classmethod
    def from_value(cls, value: "Window | str | Mapping[str, Any]") -> "Window":
        if isinstance(value, cls):
            return value
        if isinstance(value, Mapping):
            duration = value.get("duration")
            return cls(
                None if duration is None else float(duration),
                str(value.get("unit", "")).strip().lower(),
                str(value.get("anchor", "")).strip().lower(),
                str(value.get("raw", "")),
            )
        raw = str(value).strip()
        return cls(None, "", raw.lower(), raw)

    def canonical(self) -> tuple[Any, ...]:
        return (self.duration, self.unit.strip().lower(), self.anchor.strip().lower())


@dataclass(frozen=True)
class Threshold:
    metric: str
    operator: str
    value: float | str | None
    sustain: float | None = None
    sustain_unit: str = ""
    raw: str = ""

    @classmethod
    def from_value(cls, value: "Threshold | str | Mapping[str, Any]") -> "Threshold":
        if isinstance(value, cls):
            return value
        if isinstance(value, Mapping):
            return cls(
                str(value.get("metric", "")).strip().lower(),
                str(value.get("operator", "")).strip(),
                value.get("value"),
                None if value.get("sustain") is None else float(value["sustain"]),
                str(value.get("sustain_unit", "")).strip().lower(),
                str(value.get("raw", "")),
            )
        raw = str(value).strip()
        return cls(metric=raw.lower(), operator="", value=None, raw=raw)

    def canonical(self) -> tuple[Any, ...]:
        return (
            self.metric.strip().lower(),
            self.operator.strip(),
            self.value,
            self.sustain,
            self.sustain_unit.strip().lower(),
        )


@dataclass(frozen=True)
class Attestation:
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


def _coerce_thresholds(
    value: str | list[Any] | tuple[Any, ...],
) -> tuple[Threshold, ...]:
    if isinstance(value, str):
        return () if not value.strip() else (Threshold.from_value(value),)
    return tuple(Threshold.from_value(item) for item in value)


@dataclass(frozen=True)
class OutcomeDefinition:
    """Declares the event a probability describes (spec 5.6.1)."""

    id: str
    event: str
    observation_process: ObservationProcess | str | Mapping[str, Any]
    window: Window | str | Mapping[str, Any]
    thresholds: tuple[Threshold, ...] | list[Any] | str = ()
    description: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "event", self.event.strip().lower())
        object.__setattr__(
            self,
            "observation_process",
            ObservationProcess.from_value(self.observation_process),
        )
        object.__setattr__(self, "window", Window.from_value(self.window))
        object.__setattr__(self, "thresholds", _coerce_thresholds(self.thresholds))

    def comparison_key(self) -> tuple[Any, ...]:
        return (
            self.event,
            self.observation_process.canonical(),
            self.window.canonical(),
            tuple(sorted(threshold.canonical() for threshold in self.thresholds)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "event": self.event,
            "observation_process": asdict(self.observation_process),
            "window": asdict(self.window),
            "thresholds": [asdict(threshold) for threshold in self.thresholds],
            "description": self.description,
        }


@dataclass
class CommensurabilityResult:
    commensurable: bool
    left_id: str
    right_id: str
    differing_fields: list[str] = field(default_factory=list)
    reason: str = ""
    level: str = "irreducible"
    pooling_allowed: bool = False
    attestation: Attestation | None = None


def check_commensurable(
    a: OutcomeDefinition,
    b: OutcomeDefinition,
    *,
    attestation: Attestation | None = None,
    retained_observations: bool = False,
) -> CommensurabilityResult:
    """Compare definitions and classify the mismatch instead of flattening it."""

    fields = ("event", "observation_process", "window", "thresholds")
    left = a.comparison_key()
    right = b.comparison_key()
    differing = [name for name, x, y in zip(fields, left, right) if x != y]
    if not differing:
        return CommensurabilityResult(
            True, a.id, b.id, [], "same structured definition", "direct", True
        )

    if attestation is not None:
        attestation.validate(a.id, b.id)
        if set(differing).issubset({"window", "thresholds"}):
            return CommensurabilityResult(
                True,
                a.id,
                b.id,
                differing,
                "attested equivalent definitions",
                "attested",
                True,
                attestation,
            )

    if set(differing).issubset({"window", "thresholds"}):
        return CommensurabilityResult(
            False,
            a.id,
            b.id,
            differing,
            "window/threshold mismatch may be re-derived from retained observations",
            "bridgeable",
            bool(retained_observations),
            attestation,
        )

    return CommensurabilityResult(
        False,
        a.id,
        b.id,
        differing,
        "event or observation process mismatch is irreducible; calibration does not lift this",
        "irreducible",
        False,
        attestation,
    )


def require_commensurable(a: OutcomeDefinition, b: OutcomeDefinition) -> None:
    result = check_commensurable(a, b)
    if not result.pooling_allowed:
        raise IncommensurableError(result.reason)


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
