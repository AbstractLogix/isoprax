# Research and Decisions

## Decision: fail closed on ambiguous reads

Returning the newest row made `ORDER BY rowid DESC` conceal which strategy
version generated a result. Explicit version selection is safer for evidence
and keeps calibration denominators reproducible.

## Decision: reject unresolvable legacy data

SQLite cannot infer a missing strategy version or choose among multiple
signals for an old outcome. Such rows are rejected during migration instead
of being assigned a synthetic version or duplicated across versions.
