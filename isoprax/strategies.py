"""
Isoprax Strategy contract (spec Section 5).

Three abstract strategy types. Internals are a black box (spec 5.1); the
framework observes only declared inputs, the Signal output, and declared
external dependencies (5.5). This is the abstraction boundary that makes
the framework language/accelerator-neutral (spec Appendix D).

Also provides a Calibrator so strategies can honestly satisfy 5.3.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

import numpy as np
from sklearn.isotonic import IsotonicRegression

from .events import ChangeEvent, MetricSample, RunEvent
from .signals import (
    AnomalySignal,
    ForecastSignal,
    RiskSignal,
)


class Calibrator:
    """Isotonic calibration (spec 5.3). Maps raw scores -> calibrated probs.

    Kept deliberately simple: fit on (raw_score, actual_outcome) history,
    then transform new raw scores. Reports itself as a declared method so
    Signals can state calibration_method honestly.
    """

    method_name = "isotonic"

    def __init__(self) -> None:
        self._iso: Optional[IsotonicRegression] = None

    def fit(self, raw_scores: list[float], outcomes: list[int]) -> "Calibrator":
        if len(set(outcomes)) < 2:
            # Not enough signal to calibrate; leave unfitted (honest).
            self._iso = None
            return self
        self._iso = IsotonicRegression(out_of_bounds="clip")
        self._iso.fit(np.asarray(raw_scores), np.asarray(outcomes))
        return self

    @property
    def is_fitted(self) -> bool:
        return self._iso is not None

    def transform(self, raw: float) -> float:
        if self._iso is None:
            return raw
        return float(self._iso.predict([raw])[0])


class RiskStrategy(ABC):
    """Change family (spec 5.1)."""

    strategy_id: str = "abstract.risk"
    strategy_version: str = "0"
    declares_external_dependency: bool = False  # spec 5.5

    @abstractmethod
    def score(self, event: ChangeEvent, context: dict[str, Any]) -> RiskSignal: ...


class AnomalyStrategy(ABC):
    """Operational family (spec 5.1)."""

    strategy_id: str = "abstract.anomaly"
    strategy_version: str = "0"
    declares_external_dependency: bool = False

    @abstractmethod
    def evaluate(self, event: RunEvent, context: dict[str, Any]) -> AnomalySignal: ...


class ForecastStrategy(ABC):
    """Operational family (spec 5.1, 5.4)."""

    strategy_id: str = "abstract.forecast"
    strategy_version: str = "0"
    declares_external_dependency: bool = False

    @abstractmethod
    def forecast(
        self, history: list[MetricSample], context: dict[str, Any]
    ) -> ForecastSignal: ...
