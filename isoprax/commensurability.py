"""
Outcome Definitions and the commensurability test (spec Section 5.6).

This module exists because a `score` is meaningless without a declared answer
to "probability of *what*". Calibration aligns a number with a frequency
WITHIN an event definition; it says nothing about whether two numbers describe
the same event. Two perfectly calibrated forecasts of different events are both
correct and remain incommensurable -- and the arithmetic gives no warning.

So the event definition is made an explicit object, and cross-family comparison
is made conditional on a mechanical test rather than an assertion.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


class IncommensurableError(ValueError):
    """Raised when scores from non-commensurable Outcome Definitions would be
    compared, aggregated, or jointly ranked (spec 5.6.3)."""


@dataclass(frozen=True)
class OutcomeDefinition:
    """Specifies WHICH event a score is the probability of (spec 5.6.1).

    Commensurability turns on `event`, `observation_process`, `window`, and
    `thresholds` -- NOT on `id` or `description`, which are labels for humans.
    Two definitions may differ freely in what CONDITIONS the prediction (that
    is the Change/Operational distinction); they must not differ in what is
    PREDICTED.
    """

    id: str
    event: str  # the adverse event, precisely stated
    observation_process: str  # how occurrence is detected
    window: str  # observation period, relative to the event
    thresholds: str = ""  # parameters the process applies, if any
    description: str = ""  # human note; not part of the test

    def comparison_key(self) -> tuple[str, str, str, str]:
        """The tuple the commensurability test compares (spec 5.6.2)."""
        return (
            self.event.strip().lower(),
            self.observation_process.strip().lower(),
            self.window.strip().lower(),
            self.thresholds.strip().lower(),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CommensurabilityResult:
    commensurable: bool
    left_id: str
    right_id: str
    differing_fields: list[str] = field(default_factory=list)
    reason: str = ""


def check_commensurable(
    a: OutcomeDefinition, b: OutcomeDefinition
) -> CommensurabilityResult:
    """Mechanical commensurability test (spec 5.6.2).

    MUST be evaluated, not asserted, and the result MUST be exposed.
    """
    fields = ("event", "observation_process", "window", "thresholds")
    ka, kb = a.comparison_key(), b.comparison_key()
    differing = [f for f, x, y in zip(fields, ka, kb) if x != y]
    if not differing:
        return CommensurabilityResult(
            True,
            a.id,
            b.id,
            [],
            "same event, process, window and thresholds -> comparable",
        )
    return CommensurabilityResult(
        False,
        a.id,
        b.id,
        differing,
        "differ in "
        + ", ".join(differing)
        + " -> scores denote different events and MUST NOT be compared "
        "(spec 5.6.3); calibration does not lift this",
    )


def require_commensurable(a: OutcomeDefinition, b: OutcomeDefinition) -> None:
    """Guard for any operation that would jointly reason over two families'
    scores. Raises IncommensurableError when the test fails (spec 5.6.3)."""
    res = check_commensurable(a, b)
    if not res.commensurable:
        raise IncommensurableError(res.reason)


class OutcomeDefinitionRegistry:
    """Resolves the `outcome_definition_id` carried on Signals (spec 5.2, 6).

    The KB contract requires stored scores to remain interpretable after the
    Strategy that produced them is gone, so definitions are persisted
    separately from the Strategies that reference them.
    """

    def __init__(self) -> None:
        self._defs: dict[str, OutcomeDefinition] = {}

    def register(self, d: OutcomeDefinition) -> OutcomeDefinition:
        existing = self._defs.get(d.id)
        if existing is not None and existing != d:
            raise ValueError(
                f"outcome definition id '{d.id}' already registered with "
                "different content; ids MUST be stable"
            )
        self._defs[d.id] = d
        return d

    def resolve(self, definition_id: str) -> OutcomeDefinition:
        if definition_id not in self._defs:
            raise KeyError(
                f"unresolvable outcome_definition_id '{definition_id}': a score "
                "without a resolvable Outcome Definition is uninterpretable "
                "(spec 5.2)"
            )
        return self._defs[definition_id]

    def __contains__(self, definition_id: object) -> bool:
        return definition_id in self._defs

    def ids(self) -> list[str]:
        return sorted(self._defs)
