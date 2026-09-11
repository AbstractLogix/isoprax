# Data Model: Admission Timestamp Integrity

All admission split, score, prediction-observation, and predeclaration times
are parsed as timezone-aware UTC datetimes. `Z` is normalized to `+00:00`;
naive and non-UTC values are invalid.
