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


def _signal(score: float = 0.5, strategy_version: str = "1") -> RiskSignal:
    return RiskSignal(
        score=score,
        explanation="bounded test signal",
        strategy_id="strategy.v1",
        strategy_version=strategy_version,
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


def test_signal_versions_coexist_but_unversioned_reads_are_ambiguous():
    with SQLiteKB() as kb:
        kb.store_outcome_definition(_definition())
        event = _event()
        kb.store_event(event)
        v1 = _signal(0.5, "1")
        v2 = _signal(0.9, "2")
        kb.store_signal(event.id, v1)
        kb.store_signal(event.id, v2)

        assert kb.get_signal(event.id, v1.strategy_id, "1") == v1
        assert kb.get_signal(event.id, v1.strategy_id, "2") == v2
        with pytest.raises(ValueError, match="strategy_version is required"):
            kb.get_signal(event.id, v1.strategy_id)

        with pytest.raises(ValueError, match="strategy_version is required"):
            kb.store_outcome(
                Outcome(event.id, v1.strategy_id, True, v1.outcome_definition_id)
            )
        kb.store_outcome(
            Outcome(
                event.id,
                v1.strategy_id,
                True,
                v1.outcome_definition_id,
                signal_strategy_version="1",
            )
        )
        kb.store_outcome(
            Outcome(
                event.id,
                v2.strategy_id,
                False,
                v2.outcome_definition_id,
                signal_strategy_version="2",
            )
        )
        with pytest.raises(ValueError, match="span multiple versions"):
            kb.get_labeled_pairs(v1.strategy_id)
        assert kb.get_labeled_pairs(v1.strategy_id, "1") == [(0.5, 1)]
        assert kb.get_labeled_pairs(v1.strategy_id, "2") == [(0.9, 0)]


def test_old_signal_table_migrates_to_versioned_identity(tmp_path):
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
        ('event-1', 'strategy.v1', '2', 'change', 0.9, 'x', NULL, '{}');
        """
    )
    conn.commit()
    conn.close()

    with SQLiteKB(path) as kb:
        assert kb.conn.execute("SELECT COUNT(*) FROM signals").fetchone()[0] == 2
        assert (
            kb.conn.execute(
                "SELECT COUNT(*) FROM pragma_index_list('signals') "
                "WHERE name='idx_signals_event_strategy_version'"
            ).fetchone()[0]
            == 1
        )


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


def test_malformed_stored_payload_is_rejected():
    with pytest.raises(ValueError, match="stored KB payload is not valid JSON"):
        SQLiteKB._payload_matches("{", {})


def _legacy_database(
    path, *, signal_version="1", outcome_event_id=None, outcome_strategy_id=None
):
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
        CREATE TABLE outcomes (
            event_id TEXT NOT NULL, signal_strategy_id TEXT NOT NULL,
            predicted_condition_occurred INTEGER NOT NULL,
            outcome_definition_id TEXT NOT NULL, action_taken TEXT,
            resolved INTEGER, feedback_timestamp TEXT
        );
        """
    )
    conn.execute(
        "INSERT INTO signals VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("event-1", "strategy.v1", signal_version, "change", 0.5, "x", None, "{}"),
    )
    if outcome_event_id is not None:
        conn.execute(
            "INSERT INTO outcomes VALUES (?, ?, ?, ?, ?, ?, ?)",
            (outcome_event_id, outcome_strategy_id, 1, "defect.v1", None, None, None),
        )
    conn.commit()
    conn.close()


def test_legacy_signal_without_version_fails_closed(tmp_path):
    path = str(tmp_path / "legacy.db")
    _legacy_database(path, signal_version=None)

    with pytest.raises(ValueError, match="missing strategy_version"):
        SQLiteKB(path)


def test_legacy_outcome_version_is_backfilled(tmp_path):
    path = str(tmp_path / "legacy.db")
    _legacy_database(
        path, outcome_event_id="event-1", outcome_strategy_id="strategy.v1"
    )

    with SQLiteKB(path) as kb:
        row = kb.conn.execute("SELECT signal_strategy_version FROM outcomes").fetchone()
        assert row[0] == "1"


def test_unlinkable_legacy_outcome_fails_closed(tmp_path):
    path = str(tmp_path / "legacy.db")
    _legacy_database(
        path, outcome_event_id="missing", outcome_strategy_id="strategy.v1"
    )

    with pytest.raises(ValueError, match="exactly one signal version"):
        SQLiteKB(path)


def test_signal_lookup_and_pair_filters_reject_blank_versions():
    with SQLiteKB() as kb:
        with pytest.raises(ValueError, match="strategy_version must be non-empty"):
            kb.get_signal("event", "strategy", "")
        with pytest.raises(ValueError, match="strategy_version must be non-empty"):
            kb.get_labeled_pairs("strategy", "")
        assert kb.get_signal("missing", "strategy") is None


def test_outcome_version_must_match_an_existing_signal():
    with SQLiteKB() as kb:
        kb.store_outcome_definition(_definition())
        event = _event()
        signal = _signal()
        kb.store_event(event)
        kb.store_signal(event.id, signal)

        with pytest.raises(ValueError, match="strategy_version must be non-empty"):
            kb.store_outcome(
                Outcome(
                    event.id,
                    signal.strategy_id,
                    True,
                    signal.outcome_definition_id,
                    signal_strategy_version="",
                )
            )
        with pytest.raises(KeyError, match="requested signal version"):
            kb.store_outcome(
                Outcome(
                    event.id,
                    signal.strategy_id,
                    True,
                    signal.outcome_definition_id,
                    signal_strategy_version="2",
                )
            )
