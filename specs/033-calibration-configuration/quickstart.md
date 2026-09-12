# Quickstart: Cross-Family Calibration Controls

```python
report = cross_family_report(
    left_family,
    left_definition,
    left_scores,
    left_outcomes,
    right_family,
    right_definition,
    right_scores,
    right_outcomes,
    min_events=500,
    n_bins=10,
    max_ece=0.05,
)
```

The report exposes these values for review.
