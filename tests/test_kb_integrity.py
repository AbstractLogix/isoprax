import sqlite3

import pytest

from isoprax.events import ChangeEvent, Family
from isoprax.kb import Outcome, SQLiteKB
from isoprax.signals import RiskSignal


def _definition(identifier: str = "defect.v1", event: str = "defect"):
    from isoprax.commensurability import OutcomeDefinition

    return OutcomeDefinition(
        identifier,
        event,
        "public-observation",
        "10-minute window",
        "threshold-v1",
    )


def _signal(score: float = 0.5) -> RiskSignal:
    return RiskSignal(
        score=score,
        explanation="bounded test signal",
        strategy_id="strategy.v1",
        strategy_version="1",
        family=Family.CHANGE,
        outcome_definition_id="defect.v1",
    )


def _event(change_ref: str = "change-1") -> ChangeEvent:
    return ChangeEvent(id="event-1", repo="repo", change_ref=change_ref)


def test_outcome_definition_retry_is_idempotent_and_conflict_preserves_original():
    with SQLiteKB() as kb:
        original = _definition()
        kb.store_outcome_definition(original)
        kb.store_outcome_definition(original)

        with pytest.raises(ValueError, match="different content"):
            kb.store_outcome_definition(_definition(event="service outage"))

        assert kb.get_outcome_definition(original.id).event == "defect"


def test_event_retry_is_idempotent_and_conflict_preserves_original():
    with SQLiteKB() as kb:
        original = _event()
        kb.store_event(original)
        kb.store_event(original)

        with pytest.raises(ValueError, match="different content"):
            kb.store_event(_event(change_ref="change-2"))

        assert kb.get_event(original.id)["change_ref"] == "change-1"


def test_signal_retry_does_not_duplicate_calibration_pair():
    with SQLiteKB() as kb:
        kb.store_outcome_definition(_definition())
        event = _event()
        signal = _signal()
        kb.store_event(event)
        kb.store_signal(event.id, signal)
        kb.store_signal(event.id, signal)
        kb.store_outcome(
            Outcome(event.id, signal.strategy_id, True, signal.outcome_definition_id)
        )

        assert kb.get_labeled_pairs(signal.strategy_id) == [(0.5, 1)]


def test_conflicting_signal_identity_is_rejected():
    with SQLiteKB() as kb:
        kb.store_outcome_definition(_definition())
        event = _event()
        kb.store_event(event)
        kb.store_signal(event.id, _signal(0.5))

        with pytest.raises(ValueError, match="signal identity"):
            kb.store_signal(event.id, _signal(0.9))

        assert kb.get_signal(event.id, "strategy.v1").score == 0.5


def test_legacy_duplicate_signals_fail_closed_during_migration(tmp_path):
    path = str(tmp_path / "legacy.db")
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE events (
            id TEXT PRIMARY KEY, event_type TEXT NOT NULL, family TEXT NOT NULL,
            timestamp TEXT NOT NULL, source TEXT, payload TEXT NOT NULL
        );
        CREATE TABLE signals (
            event_id TEXT NOT NULL, strategy_id TEXT NOT NULL,
            strategy_version TEXT, family TEXT, score REAL,
            explanation TEXT NOT NULL, calibration_status TEXT,
            payload TEXT NOT NULL
        );
        INSERT INTO signals VALUES
        ('event-1', 'strategy.v1', '1', 'change', 0.5, 'x', NULL, '{}'),
        ('event-1', 'strategy.v1', '1', 'change', 0.9, 'x', NULL, '{}');
        """
    )
    conn.commit()
    conn.close()

    with pytest.raises(ValueError, match="duplicate signal identity"):
        SQLiteKB(path)
