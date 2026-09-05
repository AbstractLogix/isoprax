"""
Isoprax Signal output contract (spec Section 5.2, 5.3).

Signal hierarchy mirrors the spec's separation of quantities:

  Signal (base)            -- explanation + provenance, common to all
    ProbabilitySignal      -- carries `score`: P(adverse outcome), in [0,1].
                              This is the calibrated, cross-family-comparable
                              quantity governed by spec 5.3.
      RiskSignal           -- Change family
      AnomalySignal        -- Operational family
    ForecastSignal         -- carries `interval_confidence` (nominal coverage),
                              NOT `score`. Per spec 5.2, coverage and outcome
                              probability are different quantities and MUST NOT
                              be compared as though they were the same axis.

The calibration_status field lets an implementation be honest at Core level
(spec 5.3): uncalibrated scores are permitted, undeclared ones are not.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Optional

from .events import Family


class CalibrationStatus(str, Enum):
    CALIBRATED = "calibrated"
    UNCALIBRATED = "uncalibrated"  # permitted at Core level if DECLARED


@dataclass
class Signal:
    """Fields common to every Signal (spec 5.2)."""

    explanation: str  # non-empty, non-constant (spec 5.2)
    strategy_id: str
    strategy_version: str
    family: Family

    def __post_init__(self) -> None:
        if not self.explanation or not self.explanation.strip():
            raise ValueError("Signal.explanation MUST be non-empty (spec 5.2)")

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["family"] = self.family.value
        if "calibration_status" in d and d["calibration_status"] is not None:
            d["calibration_status"] = (
                d["calibration_status"].value
                if hasattr(d["calibration_status"], "value")
                else d["calibration_status"]
            )
        return d


@dataclass
class ProbabilitySignal(Signal):
    """Signals whose `score` is P(adverse event).

    Comparable across Implementations and Families ONLY where the corresponding
    Outcome Definitions are commensurable (spec 5.2, 5.3, 5.6). The score is
    calibrated relative to its OWN outcome_definition_id -- that identifier is
    what makes the number interpretable at all.
    """

    score: float = 0.0
    outcome_definition_id: str = ""  # spec 5.2: MUST resolve to a definition
    calibration_status: CalibrationStatus = CalibrationStatus.UNCALIBRATED
    calibration_method: Optional[str] = None  # e.g. "isotonic", "platt"

    def __post_init__(self) -> None:
        super().__post_init__()
        if not (0.0 <= self.score <= 1.0):
            raise ValueError(f"score must be in [0,1], got {self.score}")
        if not self.outcome_definition_id:
            raise ValueError(
                "ProbabilitySignal MUST carry an outcome_definition_id "
                "(spec 5.2): a score without a resolvable Outcome Definition "
                "is uninterpretable"
            )


@dataclass
class RiskSignal(ProbabilitySignal):
    """Change family: P(this change is defect-inducing)."""

    pass


@dataclass
class AnomalySignal(ProbabilitySignal):
    """Operational family: P(this run/resource experiences the adverse outcome)."""

    pass


@dataclass
class ForecastSignal(Signal):
    """Operational family. Carries a prediction with an interval, NOT a
    probability score (spec 5.2). `interval_confidence` is nominal coverage."""

    predicted_value: float = 0.0
    interval_low: float = 0.0
    interval_high: float = 0.0
    interval_confidence: float = 0.0  # nominal coverage in [0,1] -- NOT a score
    technique: str = ""  # spec 5.4: the technique ACTUALLY used

    def __post_init__(self) -> None:
        super().__post_init__()
        if not (0.0 <= self.interval_confidence <= 1.0):
            raise ValueError(
                f"interval_confidence must be in [0,1], got {self.interval_confidence}"
            )
        if not self.technique:
            raise ValueError("ForecastSignal MUST report the technique used (spec 5.4)")
        if self.interval_low > self.interval_high:
            raise ValueError("interval_low MUST NOT exceed interval_high")

    def __setattr__(self, name: str, value: Any) -> None:
        # spec 5.2: a ForecastSignal MUST NOT carry a `score` field.
        if name == "score":
            raise AttributeError(
                "ForecastSignal MUST NOT carry a 'score' (spec 5.2): interval "
                "coverage and outcome probability are different quantities"
            )
        super().__setattr__(name, value)
