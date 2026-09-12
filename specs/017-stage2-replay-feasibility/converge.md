# Convergence

The repeatability-first extension is implemented through the sealed baseline
artifacts in `docs/stage2/whoami-repeatability-data-v1.json` and
`docs/stage2/whoami-repeatability-data-v2.json`. The v2 baseline contains
nine raw p99 runs across three revisions, including a same-revision outlier;
its content hash is recorded in the threshold derivation decision.

The next thresholded lane is predeclared in
`docs/stage2/whoami-pilot-predeclaration-v3.json`. Its threshold is the
resolved scalar `0.00210252` seconds (`median + 3 * IQR`), while the
derivation description and baseline hash remain auditable metadata. v2 data
is not relabeled. The reducer recomputes complete-record labels from the
structured threshold and rejects mismatched recorded labels.

The reducer also publishes a deterministic bootstrap yield estimate. The
historical v2 pilot remains `no_positive_events` and therefore has no finite
implied corpus size.

The 30-revision v3 acquisition, repeated-lane report, and requirement for at
least five positive and five negative outcomes remain open in T044. No corpus
evaluation or Semantic claim is emitted before those gates pass.
