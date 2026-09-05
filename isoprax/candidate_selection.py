"""Compatibility wrapper for replay candidate screening logic."""

from .replay_selection import (
    CandidateRecord,
    ScreeningResult,
    evaluate_candidate_screening,
    screen_candidate,
    screen_candidate_system,
    screen_candidates,
)

__all__ = [
    "CandidateRecord",
    "ScreeningResult",
    "evaluate_candidate_screening",
    "screen_candidate",
    "screen_candidate_system",
    "screen_candidates",
]
