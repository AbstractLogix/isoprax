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
