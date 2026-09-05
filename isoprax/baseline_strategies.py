"""
Baseline reference strategies (spec: Core/Cross-Family conformance).

Deliberately simple ("zero-ML" per SDS adoption path): the point of the PoC
is to prove that a Change-family strategy and an Operational-family strategy
satisfy the *same* Signal contract and flow through the *same* KB and
calibration path -- i.e. that the cross-family unification is real, not that
the models are good.

Each strategy computes a raw heuristic score, then runs it through a shared
Calibrator so both families emit comparable, calibrated probabilities.
"""

from __future__ import annotations

from typing import Any

from .commensurability import OutcomeDefinition
from .events import ChangeEvent, RunEvent
from .signals import AnomalySignal, CalibrationStatus, RiskSignal
from .strategies import AnomalyStrategy, Calibrator, RiskStrategy

# --- Outcome Definitions for the baselines (spec 5.6.1) ---------------------
# These two are deliberately NON-COMMENSURABLE, and the demo self-reports
# Structural rather than Semantic conformance as a result. That is the point:
# the distinction bites on the specification's own example.

DEFECT_LINKED_FIX = OutcomeDefinition(
    id="defect.fix_linkage.v1",
    event="change is later textually linked to a defect fix",
    observation_process="issue-tracker / commit-message fix linkage (SZZ-style)",
    window="unbounded repository history following the change",
    thresholds="",
    description="Repository-archaeology event. NOT a runtime event.",
)

JOB_RUN_FAILURE = OutcomeDefinition(
    id="operational.run_failure.v1",
    event="job run terminates in a failed state",
    observation_process="scheduler-reported terminal exit status",
    window="the run itself",
    thresholds="exit_status == failed",
    description="Runtime event observed directly from the executing job.",
)


class HeuristicRiskStrategy(RiskStrategy):
    """Change family. Scores a commit's defect risk from cheap change metrics:
    large diffs, many files, off-hours commits, and touching historically
    fragile paths all raise risk. Classic change-level features from the JIT
    defect-prediction literature -- no learned model.
    """

    strategy_id = "baseline.heuristic_risk"
    strategy_version = "0.2"
    outcome_definition = DEFECT_LINKED_FIX

    def __init__(
        self,
        fragile_paths: list[str] | None = None,
        calibrator: Calibrator | None = None,
        outcome_definition: OutcomeDefinition | None = None,
    ) -> None:
        self.fragile_paths = fragile_paths or []
        self.calibrator = calibrator or Calibrator()
        if outcome_definition is not None:
            self.outcome_definition = outcome_definition

    def _raw_score(self, e: ChangeEvent) -> tuple[float, list[str]]:
        reasons = []
        churn = e.loc_added + e.loc_removed
        s = 0.0
        if churn > 200:
            s += 0.35
            reasons.append(f"large churn ({churn} LOC)")
        elif churn > 50:
            s += 0.15
            reasons.append(f"moderate churn ({churn} LOC)")
        if len(e.files_touched) > 8:
            s += 0.2
            reasons.append(f"{len(e.files_touched)} files touched")
        touched_fragile = [
            f
            for f in e.files_touched
            if any(f.startswith(p) for p in self.fragile_paths)
        ]
        if touched_fragile:
            s += 0.3
            reasons.append(f"touches fragile path(s): {touched_fragile}")
        # off-hours heuristic from the RFC3339 timestamp hour
        try:
            hour = int(e.timestamp[11:13])
            if hour >= 22 or hour <= 5:
                s += 0.15
                reasons.append(f"off-hours commit ({hour:02d}h UTC)")
        except (ValueError, IndexError):
            pass
        return min(s, 1.0), reasons

    def score(self, event: ChangeEvent, context: dict[str, Any]) -> RiskSignal:
        raw, reasons = self._raw_score(event)
        if self.calibrator.is_fitted:
            final = self.calibrator.transform(raw)
            status = CalibrationStatus.CALIBRATED
            method = self.calibrator.method_name
        else:
            final = raw
            status = CalibrationStatus.UNCALIBRATED
            method = None
        explanation = (
            "; ".join(reasons) if reasons else "no elevated-risk factors detected"
        )
        return RiskSignal(
            score=final,
            explanation=explanation,
            strategy_id=self.strategy_id,
            strategy_version=self.strategy_version,
            family=event.family,
            outcome_definition_id=self.outcome_definition.id,
            calibration_status=status,
            calibration_method=method,
        )


class DistributionAnomalyStrategy(AnomalyStrategy):
    """Operational family. Flags a job run as anomalous if its duration is a
    high-percentile outlier relative to that job_type's historical duration
    distribution -- dynamic per-job-type thresholding, not a static cutoff.
    Generalizes the anomaly-detection pattern of the operational literature.
    """

    strategy_id = "baseline.distribution_anomaly"
    strategy_version = "0.2"
    outcome_definition = JOB_RUN_FAILURE

    def __init__(
        self,
        history_by_jobtype: dict[str, list[float]] | None = None,
        calibrator: Calibrator | None = None,
        outcome_definition: OutcomeDefinition | None = None,
    ) -> None:
        self.history = history_by_jobtype or {}
        self.calibrator = calibrator or Calibrator()
        if outcome_definition is not None:
            self.outcome_definition = outcome_definition

    def _raw_score(self, e: RunEvent) -> tuple[float, str]:
        durations = self.history.get(e.job_type, [])
        if e.duration is None:
            return 0.0, "no duration recorded"
        if len(durations) < 5:
            return 0.0, f"insufficient history for '{e.job_type}'"
        import numpy as np

        arr = np.asarray(durations)
        mean, std = float(arr.mean()), float(arr.std() or 1.0)
        z = (e.duration - mean) / std
        # squash z into a raw [0,1] via a logistic-ish mapping
        raw = 1.0 / (1.0 + np.exp(-(z - 2.0)))  # centered so z=2 -> ~0.5
        reason = f"duration {e.duration:.1f}s vs job mean {mean:.1f}s (z={z:.2f})"
        return float(raw), reason

    def evaluate(self, event: RunEvent, context: dict[str, Any]) -> AnomalySignal:
        raw, reason = self._raw_score(event)
        if self.calibrator.is_fitted:
            final = self.calibrator.transform(raw)
            status = CalibrationStatus.CALIBRATED
            method = self.calibrator.method_name
        else:
            final = raw
            status = CalibrationStatus.UNCALIBRATED
            method = None
        return AnomalySignal(
            score=final,
            explanation=reason,
            strategy_id=self.strategy_id,
            strategy_version=self.strategy_version,
            family=event.family,
            outcome_definition_id=self.outcome_definition.id,
            calibration_status=status,
            calibration_method=method,
        )
