# Convergence

`cross_family_report` now accepts the same `min_events`, `n_bins`, and
`max_ece` controls as `check_calibration_conformance`. It uses the selected
bin count for ECE and stores all three values in the returned report and its
rendered audit text.
