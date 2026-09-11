"""Deterministic evidence fixtures for the commensurability argument."""

from __future__ import annotations

from dataclasses import dataclass

from .evaluation import expected_calibration_error


@dataclass(frozen=True)
class PoolingHarmEvidence:
    left_window: str
    right_window: str
    left_ece: float
    right_ece: float
    pooled_ece: float
    k: int
    per_family_macro_precision: float
    pooled_macro_precision: float
    degradation: float
    left_selected: tuple[str, ...]
    right_selected: tuple[str, ...]
    pooled_selected: tuple[str, ...]
    claim_boundary: str


def _family_rows(prefix: str, base_score: float, positives: int, total: int):
    step = 0.0001 / max(total, 1)
    return [
        (
            f"{prefix}-{index:03d}",
            base_score + (index - (total - 1) / 2) * step,
            int(index >= total - positives),
        )
        for index in range(total)
    ]


def _top_k(rows, k: int) -> tuple[str, ...]:
    return tuple(
        event_id
        for event_id, _score, _outcome in sorted(
            rows, key=lambda row: (-row[1], row[0])
        )[:k]
    )


def _macro_precision(rows, selected: tuple[str, ...]) -> float:
    outcome_by_id = {event_id: outcome for event_id, _score, outcome in rows}
    if not selected:
        return 0.0
    return sum(outcome_by_id.get(event_id, 0) for event_id in selected) / len(selected)


def build_pooling_harm_evidence(total: int = 100, k: int = 20) -> PoolingHarmEvidence:
    """Build a fixed same-event fixture with calibrated but non-comparable scores.

    The 7-day family has a 0.60 event rate and the 90-day family a 0.90 event
    rate. Each score is calibrated within its own definition, and pooled ECE is
    low, but pooled ranking selects only the higher-scale family and halves
    macro per-family top-k precision. Scores are strictly ordered so selection
    does not depend on event-ID tie-breaking.
    """

    left = _family_rows("seven-day", 0.58, int(total * 0.60), total)
    right = _family_rows("ninety-day", 0.88, int(total * 0.90), total)
    pooled = left + right
    left_selected = _top_k(left, k)
    right_selected = _top_k(right, k)
    pooled_selected = _top_k(pooled, 2 * k)
    per_family = (
        _macro_precision(left, left_selected) + _macro_precision(right, right_selected)
    ) / 2
    pooled_macro = (
        _macro_precision(left, pooled_selected)
        + _macro_precision(right, pooled_selected)
    ) / 2
    return PoolingHarmEvidence(
        left_window="7 days",
        right_window="90 days",
        left_ece=expected_calibration_error(
            [row[1] for row in left], [row[2] for row in left]
        ),
        right_ece=expected_calibration_error(
            [row[1] for row in right], [row[2] for row in right]
        ),
        pooled_ece=expected_calibration_error(
            [row[1] for row in pooled], [row[2] for row in pooled]
        ),
        k=k,
        per_family_macro_precision=per_family,
        pooled_macro_precision=pooled_macro,
        degradation=per_family - pooled_macro,
        left_selected=left_selected,
        right_selected=right_selected,
        pooled_selected=pooled_selected,
        claim_boundary="synthetic pooling-harm evidence; not Semantic/Full Conformance or efficacy",
    )
