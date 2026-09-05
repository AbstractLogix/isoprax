# Library Contract

The public `isoprax` package accepts only the three normalized event types.
Risk and anomaly signals must carry a valid Outcome Definition identifier;
Forecast signals must not carry a probability score. Consumers must call the
mechanical commensurability guard before any cross-family aggregation, ranking,
thresholding, or joint reasoning. The SQLite KB rejects outcomes whose
Outcome Definition differs from their originating signal.
