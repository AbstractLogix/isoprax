# Quickstart: Versioned Signals

```python
kb.store_signal(event_id, signal_v1)
kb.store_signal(event_id, signal_v2)
kb.get_signal(event_id, signal_v1.strategy_id, "1")
kb.store_outcome(
    Outcome(event_id, strategy_id, True, definition_id,
            signal_strategy_version="1")
)
kb.get_labeled_pairs(strategy_id, "1")
```

Calling `get_signal(event_id, strategy_id)` after storing both versions raises
an ambiguity error. Existing legacy databases are migrated on `SQLiteKB`
initialization.
