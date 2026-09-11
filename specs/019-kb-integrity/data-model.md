# Data Model: Durable Knowledge-Base Integrity

## Signal identity

`(event_id, strategy_id)` is the durable signal identity used by the existing
retrieval and labeling APIs. The SQLite schema enforces it with a unique
constraint.

## Immutable payload identities

Events and Outcome Definitions retain their existing primary identifiers. A
retry with equivalent serialized content is accepted without inserting a
second row. A different payload for the same identifier is rejected.
