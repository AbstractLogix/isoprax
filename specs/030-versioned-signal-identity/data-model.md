# Data Model

The signal identity is:

```text
(event_id, strategy_id, strategy_version)
```

`signals` enforces that tuple as unique and non-null. `outcomes` stores
`signal_strategy_version` beside its event and strategy identifiers. The
`Outcome` value object keeps the field optional for backwards-compatible
single-version calls, but persistence resolves or rejects ambiguity rather
than guessing.
