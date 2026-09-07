import pytest

from isoprax.baseline_strategies import HistoricalMeanForecastStrategy
from isoprax.events import MetricSample
from isoprax.kb import SQLiteKB
from isoprax.signals import ForecastSignal


def test_forecast_strategy_round_trips_without_probability_score():
    history = [
        MetricSample(resource_id="r", resource_type="service", value=value)
        for value in (10.0, 12.0, 14.0)
    ]
    strategy = HistoricalMeanForecastStrategy()
    signal = strategy.forecast(history, {})

    assert isinstance(signal, ForecastSignal)
    assert not hasattr(signal, "score")
    with SQLiteKB() as kb:
        event = history[-1]
        kb.store_event(event)
        kb.store_signal(event.id, signal)
        restored = kb.get_signal(event.id, strategy.strategy_id)

    assert isinstance(restored, ForecastSignal)
    assert restored.to_dict() == signal.to_dict()


def test_forecast_strategy_requires_history():
    with pytest.raises(ValueError, match="history"):
        HistoricalMeanForecastStrategy().forecast([], {})


def test_forecast_signal_migrates_existing_non_nullable_score_schema(tmp_path):
    import sqlite3

    path = tmp_path / "legacy.db"
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE events (
            id TEXT PRIMARY KEY, event_type TEXT NOT NULL, family TEXT NOT NULL,
            timestamp TEXT NOT NULL, source TEXT, payload TEXT NOT NULL
        );
        CREATE TABLE signals (
            event_id TEXT NOT NULL, strategy_id TEXT NOT NULL,
            strategy_version TEXT, family TEXT, score REAL NOT NULL,
            explanation TEXT NOT NULL, calibration_status TEXT,
            payload TEXT NOT NULL
        );
        """
    )
    connection.commit()
    connection.close()

    history = [
        MetricSample(resource_id="r", resource_type="service", value=value)
        for value in (1.0, 2.0)
    ]
    strategy = HistoricalMeanForecastStrategy()
    signal = strategy.forecast(history, {})
    with SQLiteKB(str(path)) as kb:
        for event in history:
            kb.store_event(event)
        kb.store_signal(history[-1].id, signal)

        assert kb.get_signal(history[-1].id, strategy.strategy_id) == signal
