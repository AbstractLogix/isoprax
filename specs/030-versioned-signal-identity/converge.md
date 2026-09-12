# Convergence

SQLite now persists signals under `(event_id, strategy_id,
strategy_version)`. Reads without a version remain convenient for the
single-version case and fail closed when multiple versions exist. Outcomes
carry the selected signal version, and labeled-pair queries require an
explicit version when labels span versions. Legacy rows are migrated only when
their version and outcome linkage are unambiguous.
