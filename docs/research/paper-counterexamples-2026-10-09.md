# Counterexamples and failure cases — 2026-10-09

These cases challenge both permission and refusal behavior. Cases marked **formal** are logical constructions. Cases marked **synthetic result** are checked repository fixtures. None is field evidence.

| Case | Construction | Operation and expected result | What it challenges |
|---|---|---|---|
| CE1: calibrated, distinct event | Two forecasts are calibrated to their own targets; one target is a repository-linked defect, the other a telemetry threshold event. | Do not interpret as one common event. Separate calibration is valid; common-event pooling is unsupported. | Calibration is not target equivalence. |
| CE2: same event text, different process | Both declarations say “service unavailable,” but one labels from sampled logs and one from complete request traces with different censoring. | Withhold comparison until the observation processes are shown equivalent or mapped. | Exact text can produce a false permission if process metadata is missing. |
| CE3: same outcome, different horizon | One prediction concerns an event within 30 minutes and another within 24 hours. | Do not pool as the same forecast target. A nested-horizon relationship may support a separately defined bridge, not direct equality. | Identical event name does not erase horizon semantics. |
| CE4: declared mixture | Choose the Change lane with weight 0.5 or Operational lane with weight 0.5, then observe that chosen lane's outcome. | Report the expected metric for this predeclared mixture. Do not rename it a common event. | Prohibiting every cross-target summary would be too strict. |
| CE5: shared lineage, correlated errors | Two models share data, labels, prompts, or upstream representation. | Measure paired errors on common cases; do not infer independence from distinct model IDs. | Model identity is not an independence certificate. |
| CE6: distinct families, shared data dependence | Different model families are trained or prompted on overlapping sources and share the same mislabeled examples. | Model-family diversity does not imply independent evidence. | Different names can hide common data dependence. |
| CE7: ranking useful, probability poor | Scores strictly rank examples but are not calibrated probabilities. | Ranking may be permitted for an explicit ranking objective; probability pooling is not. | One global “commensurable” bit is too coarse. |
| CE8: calibration good, ranking useless | A constant base-rate predictor can be calibrated in the aggregate but cannot discriminate examples. | Do not infer ranking value from calibration alone. | Calibration does not establish utility for every operation. |
| CE9: better accuracy, worse proper score | On the frozen model-role synthetic relevance target, the probability pool has perfect threshold accuracy while its Brier and log loss exceed the Qwen component's. | Consider decision objective and proper score separately; the numeric scale alone does not select a valid pool. | Classification accuracy can conceal probability degradation. |
| CE10: operation-specific gate | In the 23-case authored challenge it permits the cases labeled valid and refuses those labeled invalid. | Descriptive result only; require prospectively held-out independent cases before a general value claim. | A candidate rule may match its own challenge without generalizing. |
| CE11: deceptive declarations | Two pipelines have different real targets but submit the same incomplete structured declaration. | Current checker can permit because it trusts the declarations. | False permission risk; declaration truth is outside the checker. |
| CE12: synonymous valid target | Equivalent events use different text labels with no machine-readable mapping. | Current checker can refuse although a reviewer may establish equivalence. | False refusal risk; current checker has no semantic bridge authorization path. |

## Repository observations

- Benchmark A supplies CE1 and a same-target control. The permitted numeric mixture is explicitly declared.
- The shared-model experiment tests different families, different horizons, and a same-target control, but all records are synthetic.
- `isoprax/commensurability.py` returns direct commensurability on structured equality and withholds pooling for mismatches. It cannot establish declaration truth. It does not currently allow an attested semantic equivalence to reverse a mismatch.
- The 23-case gate challenge supplies a CE10 result, not an independent estimate of a general false-permission rate.

## Prospective falsification set

Before any new scored results, preregister independently authored paired cases that vary one field at a time: event, observation process, window, threshold, population, forecast horizon, prediction time, overlap/dependence, ranking objective, mixture weights, and semantic-equivalence evidence. Blind the implementation authors to evaluator labels. Include positive equivalence cases with distinct wording and negative cases with identical wording but different observation processes. Score false permission, unnecessary refusal, interpretation errors, ranking changes, and predeclared decisions. Freeze the case set and analysis before running the candidate rule.
