"""
Isoprax Knowledge-Base contract (spec Section 6) and Outcome/feedback
contract (spec Section 7).

The spec defines the KB as a set of *capabilities*, not a schema, so this
module defines an abstract interface and ships one reference implementation
(SQLite). The capabilities that matter for conformance:
  - retrieve events by id; query by time range, type, and family
  - preserve event -> signal -> outcome linkage
  - support time-ordered retrieval (for time-sliced evaluation, spec 8)
  - preserve extension fields without loss (spec 4.4)
"""

from __future__ import annotations

import json
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

from .events import Event, Family
from .signals import (
    AnomalySignal,
    CalibrationStatus,
    ForecastSignal,
    ProbabilitySignal,
    RiskSignal,
    Signal,
)


@dataclass
class Outcome:
    """Observed real-world result following a Signal (spec Section 7).

    MUST record the Outcome Definition under which occurrence was determined
    (spec 7): an outcome determined under one definition cannot calibrate or
    evaluate signals emitted under a different, non-commensurable one.
    """

    event_id: str
    signal_strategy_id: str
    predicted_condition_occurred: bool
    outcome_definition_id: str = ""
    action_taken: Optional[str] = None
    resolved: Optional[bool] = None
    feedback_timestamp: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.outcome_definition_id:
            raise ValueError(
                "Outcome MUST record the outcome_definition_id under which "
                "occurrence was determined (spec 7)"
            )


class KnowledgeBase(ABC):
    @abstractmethod
    def store_event(self, event: Event) -> None: ...

    @abstractmethod
    def store_signal(self, event_id: str, signal: Signal) -> None: ...

    @abstractmethod
    def store_outcome(self, outcome: Outcome) -> None: ...

    def get_event(self, event_id: str) -> Optional[dict[str, Any]]: ...

    def get_signal(self, event_id: str, strategy_id: str) -> Optional[Signal]: ...

    @abstractmethod
    def query_events(
        self,
        family: Optional[Family] = None,
        event_type: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> list[dict[str, Any]]: ...

    @abstractmethod
    def store_outcome_definition(self, definition) -> None:
        """Persist an Outcome Definition so stored scores stay interpretable
        after the emitting Strategy is gone (spec 6)."""
        ...

    @abstractmethod
    def get_outcome_definition(self, definition_id: str):
        """Resolve the identifier carried on Signals (spec 5.2, 6)."""
        ...

    @abstractmethod
    def get_labeled_pairs(self, strategy_id: str) -> list[tuple[float, int]]:
        """Return (score, actual_outcome) pairs for calibration/eval (spec 5.3, 8).

        Pairs are scoped to ONE strategy and therefore to one Outcome
        Definition; mixing definitions here would silently corrupt calibration
        (spec 7).
        """
        ...


class SQLiteKB(KnowledgeBase):
    """Reference KB implementation. Any store meeting the interface conforms."""

    def __init__(self, path: str = ":memory:") -> None:
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def close(self) -> None:
        """Release the SQLite connection owned by this reference store."""
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def __enter__(self) -> "SQLiteKB":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()

    def _init_schema(self) -> None:
        c = self.conn.cursor()
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                family TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                source TEXT,
                payload TEXT NOT NULL          -- full event incl. extension fields
            );
            CREATE INDEX IF NOT EXISTS idx_events_time ON events(timestamp);
            CREATE INDEX IF NOT EXISTS idx_events_family ON events(family);

            CREATE TABLE IF NOT EXISTS outcome_definitions (
                id TEXT PRIMARY KEY,
                payload TEXT NOT NULL          -- full definition (spec 6)
            );

            CREATE TABLE IF NOT EXISTS signals (
                event_id TEXT NOT NULL,
                strategy_id TEXT NOT NULL,
                strategy_version TEXT,
                family TEXT,
                score REAL,
                explanation TEXT NOT NULL,
                calibration_status TEXT,
                payload TEXT NOT NULL,
                FOREIGN KEY(event_id) REFERENCES events(id)
            );

            CREATE TABLE IF NOT EXISTS outcomes (
                event_id TEXT NOT NULL,
                signal_strategy_id TEXT NOT NULL,
                predicted_condition_occurred INTEGER NOT NULL,
                outcome_definition_id TEXT NOT NULL,
                action_taken TEXT,
                resolved INTEGER,
                feedback_timestamp TEXT,
                FOREIGN KEY(event_id) REFERENCES events(id)
            );
            """
        )
        self.conn.commit()

    def store_event(self, event: Event) -> None:
        d = event.to_dict()
        self.conn.execute(
            "INSERT OR REPLACE INTO events (id, event_type, family, timestamp, source, payload)"
            " VALUES (?,?,?,?,?,?)",
            (
                d["id"],
                d["event_type"],
                d["family"],
                d["timestamp"],
                d.get("source"),
                json.dumps(d),
            ),
        )
        self.conn.commit()

    def store_signal(self, event_id: str, signal: Signal) -> None:
        if self.get_event(event_id) is None:
            raise KeyError(f"cannot store a signal for unknown event '{event_id}'")
        if isinstance(signal, ProbabilitySignal):
            # A probability is not interpretable unless its declared outcome
            # definition is resolvable at the time it is persisted (spec 5.2).
            self.get_outcome_definition(signal.outcome_definition_id)
        d = signal.to_dict()
        self.conn.execute(
            "INSERT INTO signals (event_id, strategy_id, strategy_version, family,"
            " score, explanation, calibration_status, payload) VALUES (?,?,?,?,?,?,?,?)",
            (
                event_id,
                d["strategy_id"],
                d["strategy_version"],
                d["family"],
                d.get("score"),
                d["explanation"],
                d.get("calibration_status"),
                json.dumps(d),
            ),
        )
        self.conn.commit()

    def get_signal(self, event_id: str, strategy_id: str) -> Optional[Signal]:
        row = self.conn.execute(
            "SELECT payload FROM signals WHERE event_id=? AND strategy_id=? "
            "ORDER BY rowid DESC LIMIT 1",
            (event_id, strategy_id),
        ).fetchone()
        if row is None:
            return None
        payload = json.loads(row["payload"])
        payload["family"] = Family(payload["family"])
        if "calibration_status" in payload:
            payload["calibration_status"] = CalibrationStatus(
                payload["calibration_status"]
            )
        if "predicted_value" in payload:
            return ForecastSignal(**payload)
        signal_type = (
            RiskSignal if payload["family"] == Family.CHANGE else AnomalySignal
        )
        return signal_type(**payload)

    def store_outcome(self, outcome: Outcome) -> None:
        rows = self.conn.execute(
            "SELECT payload FROM signals WHERE event_id=? AND strategy_id=?",
            (outcome.event_id, outcome.signal_strategy_id),
        ).fetchall()
        if not rows:
            raise KeyError(
                "cannot store an outcome without its originating event signal"
            )
        for row in rows:
            signal = json.loads(row["payload"])
            if signal.get("outcome_definition_id") != outcome.outcome_definition_id:
                raise ValueError(
                    "Outcome Definition does not match the originating Signal "
                    "(specs 5.6.1 and 7)"
                )
        self.get_outcome_definition(outcome.outcome_definition_id)
        self.conn.execute(
            "INSERT INTO outcomes (event_id, signal_strategy_id,"
            " predicted_condition_occurred, outcome_definition_id,"
            " action_taken, resolved, feedback_timestamp)"
            " VALUES (?,?,?,?,?,?,?)",
            (
                outcome.event_id,
                outcome.signal_strategy_id,
                int(outcome.predicted_condition_occurred),
                outcome.outcome_definition_id,
                outcome.action_taken,
                None if outcome.resolved is None else int(outcome.resolved),
                outcome.feedback_timestamp,
            ),
        )
        self.conn.commit()

    def store_outcome_definition(self, definition) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO outcome_definitions (id, payload) VALUES (?,?)",
            (definition.id, json.dumps(definition.to_dict())),
        )
        self.conn.commit()

    def get_outcome_definition(self, definition_id: str):
        from .commensurability import OutcomeDefinition

        row = self.conn.execute(
            "SELECT payload FROM outcome_definitions WHERE id=?", (definition_id,)
        ).fetchone()
        if row is None:
            raise KeyError(
                f"unresolvable outcome_definition_id '{definition_id}' (spec 5.2)"
            )
        return OutcomeDefinition(**json.loads(row["payload"]))

    def get_event(self, event_id: str) -> Optional[dict[str, Any]]:
        row = self.conn.execute(
            "SELECT payload FROM events WHERE id=?", (event_id,)
        ).fetchone()
        return json.loads(row["payload"]) if row else None

    def query_events(self, family=None, event_type=None, start=None, end=None):
        q = "SELECT payload FROM events WHERE 1=1"
        params: list[Any] = []
        if family:
            q += " AND family=?"
            params.append(family.value)
        if event_type:
            q += " AND event_type=?"
            params.append(event_type)
        if start:
            q += " AND timestamp>=?"
            params.append(start)
        if end:
            q += " AND timestamp<=?"
            params.append(end)
        q += " ORDER BY timestamp ASC"  # time-ordered (spec 6)
        rows = self.conn.execute(q, params).fetchall()
        return [json.loads(r["payload"]) for r in rows]

    def get_labeled_pairs(self, strategy_id: str) -> list[tuple[float, int]]:
        rows = self.conn.execute(
            "SELECT s.score AS score, o.predicted_condition_occurred AS actual "
            "FROM signals s JOIN outcomes o "
            "ON s.event_id=o.event_id AND s.strategy_id=o.signal_strategy_id "
            "WHERE s.strategy_id=?",
            (strategy_id,),
        ).fetchall()
        return [(r["score"], r["actual"]) for r in rows]
