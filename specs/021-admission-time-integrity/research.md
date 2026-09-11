# Research: Admission Timestamp Integrity

`events.Event` already requires RFC 3339 UTC, while admission used bare
`datetime.fromisoformat`, which accepts naive values. The split gate compared
those values with aware row timestamps outside a guarded block, producing a
runtime `TypeError` instead of a deterministic failed gate.
