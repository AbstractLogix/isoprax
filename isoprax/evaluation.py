"""
Isoprax evaluation discipline (spec Section 8) and calibration diagnostics
(spec 5.3).

Provides:
  - brier_score / reliability_curve: calibration diagnostics a conforming
    implementation MUST be able to expose (5.3)
  - time_sliced_split: time-ordered train/test split (8.1) -- NOT shuffled
  - paired_comparison: paired significance test between two strategies (8.2)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy import stats
from sklearn.metrics import roc_auc_score


def _diagnostic_arrays(scores, outcomes, *, allow_empty: bool = True):
    try:
        score_count = len(scores)
        outcome_count = len(outcomes)
    except TypeError as error:
        raise ValueError("scores and outcomes must be sized sequences") from error
    if score_count != outcome_count:
        raise ValueError("scores and outcomes must have equal length")
    if not allow_empty and score_count == 0:
        raise ValueError("scores and outcomes must not be empty")
    try:
        score_array = np.asarray(scores, dtype=float)
        outcome_array = np.asarray(outcomes, dtype=float)
    except (TypeError, ValueError) as error:
        raise ValueError(
            "scores and outcomes must be flat numeric sequences"
        ) from error
    if score_array.ndim != 1 or outcome_array.ndim != 1:
        raise ValueError("scores and outcomes must be one-dimensional")
    if not np.all(np.isfinite(score_array)):
        raise ValueError("scores must be finite")
    if np.any((score_array < 0.0) | (score_array > 1.0)):
        raise ValueError("scores must be in [0, 1]")
    if not np.all(np.isin(outcome_array, (0.0, 1.0))):
        raise ValueError("outcomes must be binary 0 or 1")
    return score_array, outcome_array


def brier_score(scores: list[float], outcomes: list[int]) -> float:
    s, y = _diagnostic_arrays(scores, outcomes, allow_empty=False)
    return float(np.mean((s - y) ** 2))


@dataclass
class ReliabilityBin:
    bin_low: float
    bin_high: float
    mean_predicted: float
    empirical_frequency: float
    count: int


def reliability_curve(scores, outcomes, n_bins: int = 10) -> list[ReliabilityBin]:
    """Data behind a reliability diagram (spec 5.3): for each score bin, the
    mean predicted probability vs the observed empirical frequency. A well-
    calibrated strategy has mean_predicted ~= empirical_frequency per bin."""
    if not isinstance(n_bins, int) or isinstance(n_bins, bool) or n_bins < 1:
        raise ValueError("n_bins must be a positive integer")
    s, y = _diagnostic_arrays(scores, outcomes)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    out = []
    for i in range(n_bins):
        lo, hi = edges[i], edges[i + 1]
        mask = (s >= lo) & (s < hi) if i < n_bins - 1 else (s >= lo) & (s <= hi)
        if mask.sum() == 0:
            continue
        out.append(
            ReliabilityBin(
                bin_low=float(lo),
                bin_high=float(hi),
                mean_predicted=float(s[mask].mean()),
                empirical_frequency=float(y[mask].mean()),
                count=int(mask.sum()),
            )
        )
    return out


def expected_calibration_error(scores, outcomes, n_bins: int = 10) -> float:
    """ECE: weighted average gap between confidence and accuracy across bins."""
    bins = reliability_curve(scores, outcomes, n_bins)
    total = sum(b.count for b in bins) or 1
    return float(
        sum(b.count * abs(b.mean_predicted - b.empirical_frequency) for b in bins)
        / total
    )


def time_sliced_split(events: list[dict], train_frac: float = 0.7):
    """Time-ordered split (spec 8.1). Assumes events already time-sorted or
    sorts them; NEVER shuffles."""
    if (
        isinstance(train_frac, bool)
        or not isinstance(train_frac, (int, float))
        or not np.isfinite(train_frac)
        or not 0.0 < train_frac < 1.0
    ):
        raise ValueError("train_frac must be strictly between 0 and 1")
    ordered = sorted(events, key=lambda e: e["timestamp"])
    k = int(len(ordered) * train_frac)
    return ordered[:k], ordered[k:]


@dataclass
class ComparisonResult:
    baseline_brier: float
    candidate_brier: float
    statistic: float
    p_value: float
    test: str
    verdict: str


def paired_comparison(
    baseline_errs: list[float], candidate_errs: list[float]
) -> ComparisonResult:
    """Paired significance test between two strategies' per-item squared errors
    (spec 8.2). Uses Wilcoxon signed-rank (non-parametric, no normality
    assumption). Reports both Brier scores and the test outcome -- never a
    single accuracy number as the sole basis for an improvement claim."""
    b = np.asarray(baseline_errs, dtype=float)
    c = np.asarray(candidate_errs, dtype=float)
    if len(b) != len(c):
        raise ValueError("paired test requires equal-length paired errors")
    if not len(b):
        raise ValueError("paired test requires non-empty paired errors")
    if not np.all(np.isfinite(b)) or not np.all(np.isfinite(c)):
        raise ValueError("paired errors must be finite")
    # Wilcoxon requires some non-zero differences
    diffs = b - c
    if np.allclose(diffs, 0):
        stat, p = 0.0, 1.0
    else:
        stat, p = stats.wilcoxon(b, c)
    bb, cb = float(b.mean()), float(c.mean())
    if p < 0.05 and cb < bb:
        verdict = "candidate significantly better (lower Brier)"
    elif p < 0.05 and cb > bb:
        verdict = "candidate significantly worse"
    else:
        verdict = "no significant difference"
    return ComparisonResult(
        baseline_brier=bb,
        candidate_brier=cb,
        statistic=float(stat),
        p_value=float(p),
        test="wilcoxon_signed_rank",
        verdict=verdict,
    )


# --- Conformance check for the calibration obligation (spec 5.3) -------------

CONFORMANCE_MIN_EVENTS = 500
CONFORMANCE_N_BINS = 10
CONFORMANCE_MAX_ECE = 0.05


@dataclass
class CalibrationConformance:
    """Result of the objective calibration test in spec 5.3."""

    passes: bool
    ece: float
    brier: float
    n_events: int
    n_bins: int
    max_ece: float
    reason: str
    auc: float | None = None
    score_variance: float = 0.0
    positive_events: int = 0
    negative_events: int = 0
    discrimination_passes: bool = False

    def as_declaration(self) -> str:
        """The calibration qualifier an implementation MUST declare (spec 3.3)."""
        return "calibrated" if self.passes else "uncalibrated"


def check_calibration_conformance(
    scores,
    outcomes,
    min_events: int = CONFORMANCE_MIN_EVENTS,
    n_bins: int = CONFORMANCE_N_BINS,
    max_ece: float = CONFORMANCE_MAX_ECE,
) -> CalibrationConformance:
    """Objective calibration test (spec 5.3).

    An implementation may claim calibrated scores only if it has at least
    `min_events` outcome-labeled events AND its ECE over `n_bins` equal-width
    bins does not exceed `max_ece`. Otherwise it MUST declare its scores
    uncalibrated -- which is a conformant, honest outcome, not a failure.

    Parameters are reported back so conformance claims stay auditable.
    """
    if len(scores) != len(outcomes):
        raise ValueError("scores and outcomes must have equal length")
    if any(score < 0.0 or score > 1.0 for score in scores):
        raise ValueError("scores must be in [0, 1]")
    if any(outcome not in {0, 1} for outcome in outcomes):
        raise ValueError("outcomes must be binary 0 or 1")
    n = len(scores)
    score_array = np.asarray(scores, dtype=float)
    outcome_array = np.asarray(outcomes, dtype=int)
    score_variance = float(score_array.var()) if n else 0.0
    positive_events = int(outcome_array.sum()) if n else 0
    negative_events = n - positive_events
    auc = (
        float(roc_auc_score(outcome_array, score_array))
        if positive_events and negative_events
        else None
    )
    discrimination_passes = (
        auc is not None and np.isfinite(auc) and score_variance > 0.0
    )
    ece = expected_calibration_error(scores, outcomes, n_bins) if n else 1.0
    brier = brier_score(scores, outcomes) if n else 1.0
    if n < min_events:
        return CalibrationConformance(
            False,
            ece,
            brier,
            n,
            n_bins,
            max_ece,
            f"insufficient labeled events ({n} < {min_events}) "
            f"-> MUST declare uncalibrated",
            auc,
            score_variance,
            positive_events,
            negative_events,
            discrimination_passes,
        )
    if len(set(outcomes)) < 2:
        return CalibrationConformance(
            False,
            ece,
            brier,
            n,
            n_bins,
            max_ece,
            "only one observed outcome class -> MUST declare uncalibrated",
            auc,
            score_variance,
            positive_events,
            negative_events,
            discrimination_passes,
        )
    if ece > max_ece:
        return CalibrationConformance(
            False,
            ece,
            brier,
            n,
            n_bins,
            max_ece,
            f"ECE {ece:.4f} exceeds {max_ece} -> MUST declare uncalibrated",
            auc,
            score_variance,
            positive_events,
            negative_events,
            discrimination_passes,
        )
    if not discrimination_passes:
        return CalibrationConformance(
            False,
            ece,
            brier,
            n,
            n_bins,
            max_ece,
            "calibration passed but discrimination is degenerate or unavailable "
            "-> MUST NOT declare calibrated",
            auc,
            score_variance,
            positive_events,
            negative_events,
            False,
        )
    return CalibrationConformance(
        True,
        ece,
        brier,
        n,
        n_bins,
        max_ece,
        f"ECE {ece:.4f} <= {max_ece} and AUC {auc:.4f} over {n} events -> calibrated",
        auc,
        score_variance,
        positive_events,
        negative_events,
        True,
    )


# --- Cross-family reporting under commensurability (spec 5.6.3, 8.5) --------


@dataclass
class CrossFamilyReport:
    """A conformant cross-family result (spec Section 8, obligation 5).

    Always states both Outcome Definitions and the commensurability test
    result. Aggregation across families is populated ONLY when the definitions
    are commensurable; otherwise per-family figures are reported and the
    aggregate is withheld.
    """

    left_family: str
    right_family: str
    left_definition_id: str
    right_definition_id: str
    commensurable: bool
    commensurability_reason: str
    left_ece: float
    right_ece: float
    left_n: int
    right_n: int
    pooled_ece: Optional[float] = None  # None when non-commensurable
    declarable_class: str = ""
    commensurability_level: str = "irreducible"
    calibration_min_events: int = CONFORMANCE_MIN_EVENTS
    calibration_n_bins: int = CONFORMANCE_N_BINS
    calibration_max_ece: float = CONFORMANCE_MAX_ECE

    def render(self) -> str:
        lines = [
            f"  {self.left_family:12s} def={self.left_definition_id} "
            f"ECE={self.left_ece:.4f} n={self.left_n}",
            f"  {self.right_family:12s} def={self.right_definition_id} "
            f"ECE={self.right_ece:.4f} n={self.right_n}",
            "  calibration conformance: "
            f"min_events={self.calibration_min_events}, "
            f"n_bins={self.calibration_n_bins}, "
            f"max_ece={self.calibration_max_ece}",
            f"  commensurable: {self.commensurable} — {self.commensurability_reason}",
            f"  commensurability level: {self.commensurability_level}",
        ]
        if self.pooled_ece is None:
            lines.append(
                "  pooled figure WITHHELD: scores denote different events (spec 5.6.3)"
            )
        else:
            lines.append(
                f"  pooled ECE={self.pooled_ece:.4f} (definitions "
                "commensurable, pooling permitted)"
            )
        lines.append(f"  -> declarable: {self.declarable_class}")
        return "\n".join(lines)


def cross_family_report(
    left_family,
    left_def,
    left_scores,
    left_outcomes,
    right_family,
    right_def,
    right_scores,
    right_outcomes,
    *,
    attestation=None,
    retained_observations: bool = False,
    min_events: int = CONFORMANCE_MIN_EVENTS,
    n_bins: int = CONFORMANCE_N_BINS,
    max_ece: float = CONFORMANCE_MAX_ECE,
) -> CrossFamilyReport:
    """Build a conformant cross-family result.

    Refuses to pool scores across non-commensurable Outcome Definitions
    (spec 5.6.3) and derives the declarable conformance class (spec 3.3).
    """
    from .commensurability import check_commensurable

    res = check_commensurable(
        left_def,
        right_def,
        attestation=attestation,
        retained_observations=retained_observations,
    )
    l_ece = expected_calibration_error(left_scores, left_outcomes, n_bins)
    r_ece = expected_calibration_error(right_scores, right_outcomes, n_bins)
    l_ok = check_calibration_conformance(
        left_scores,
        left_outcomes,
        min_events=min_events,
        n_bins=n_bins,
        max_ece=max_ece,
    ).passes
    r_ok = check_calibration_conformance(
        right_scores,
        right_outcomes,
        min_events=min_events,
        n_bins=n_bins,
        max_ece=max_ece,
    ).passes
    calibrated = l_ok and r_ok

    pooled = None
    if res.pooling_allowed:
        pooled = expected_calibration_error(
            list(left_scores) + list(right_scores),
            list(left_outcomes) + list(right_outcomes),
            n_bins,
        )

    cls = "Cross-Family Conformance (Structural)"
    if res.commensurable:
        cls += ", commensurability established but Semantic/Full claims are outside Stage 0"
    elif res.pooling_allowed:
        cls += ", pooling permitted by retained-observation evidence"
    if not calibrated:
        cls += ", uncalibrated"

    return CrossFamilyReport(
        left_family=left_family,
        right_family=right_family,
        left_definition_id=left_def.id,
        right_definition_id=right_def.id,
        commensurable=res.commensurable,
        commensurability_reason=res.reason,
        left_ece=l_ece,
        right_ece=r_ece,
        left_n=len(left_scores),
        right_n=len(right_scores),
        calibration_min_events=min_events,
        calibration_n_bins=n_bins,
        calibration_max_ece=max_ece,
        commensurability_level=res.level,
        pooled_ece=pooled,
        declarable_class=cls,
    )
