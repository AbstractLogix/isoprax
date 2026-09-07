# Evidence and Library Contract

## Citation resolution

The citation verifier accepts the implementation package path and vendored
specification path. It returns a deterministic collection of source location,
full section reference, resolved heading, and status. Any malformed or
unresolved reference exits non-success and reports all failures.

## Outcome-definition comparison

`check_commensurable(left, right, evidence=None)` returns a structured
assessment. The result must expose the comparison level, differing dimensions,
reason, evidence/provenance, and whether pooling is currently allowed.

The legacy boolean field may be retained as a derived compatibility view, but
callers must not lose the graded assessment or use the boolean as the only
explanation.

## Calibration qualification

`check_calibration_conformance(scores, outcomes, ...)` returns calibration and
discrimination diagnostics separately. A calibrated declaration is qualified
only when both gates pass. Constant scores, one-class outcomes, insufficient
samples, invalid AUC, and missing evidence return explicit non-qualified
statuses.

## Forecast strategy and KB round trip

A concrete `ForecastStrategy.forecast(history, context)` returns a
`ForecastSignal` containing predicted value, interval bounds, confidence, and
technique. It does not expose or persist a probability `score`. The signal must
round-trip through `SQLiteKB` without changing fields or provenance.

## Pooling-harm evidence

The deterministic fixture returns per-definition calibration, descriptive
pooled calibration, fixed-k selections, and a positive degradation result. It
must not call the pooled result a conformance or efficacy result.

## Public-label evidence

The public package is manifest-driven. A valid package is reproducible from its
recorded sources and license/provenance facts. Missing, changed, or
incompatible sources return `blocked` or `inconclusive`, never an empty success
or a real-world conformance declaration.
