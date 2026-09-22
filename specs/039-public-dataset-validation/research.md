# Research: Evidence-Bounded Dataset Examples

AI4I 2020 is the initial synthetic structural/label-semantics example and is
documented in [Feature 038](../038-ai4i-structural-fixture/). The decisions
below record the next screened candidates that extend the same evidence-bounded
approach; they do not define one shared schema or outcome.

## Decision 1: Integrate ApacheJIT as the primary JIT corpus

- **Decision**: Use the Kaggle ApacheJIT mirror only as a reproducible
  materialization of the canonical Zenodo artifact, and implement an offline
  verifier for `apachejit_total.csv`.
- **Rationale**: The downloaded Kaggle file has 106,674 rows, 18 columns,
  106,674 unique commit IDs, 15 Apache projects, 28,239 `buggy=True` rows,
  78,435 clean rows, and SHA-256
  `5097cbbbab8c4611a709b3cf95ac5c9fe5f62e619bab081911a2a247ddbed4e0`.
  Its MD5 exactly matches the canonical Zenodo file
  (`98e102741020b3b13798d1e10a350689`), which is stronger evidence than a
  Kaggle card alone. The artifact contains commit identifiers, project IDs,
  author epochs, and a published `buggy` outcome.
- **Authoritative references**:
  - Zenodo record: https://zenodo.org/records/5907002
  - Kaggle mirror: https://www.kaggle.com/datasets/behnamrr/apachejit-total-commits
- **Limits**: The outcome is repository-derived and not an observed runtime
  failure. The verifier does not re-run SZZ, infer fix linkage, or claim that
  `buggy` is commensurable with an operational failure. File order is not time
  order; 53,487 adjacent timestamp inversions are reported. The published
  `year` field disagrees with the UTC epoch year for 1,314 rows and is retained
  as a reported artifact inconsistency. `apache/hadoop` has zero positive rows,
  so pooled counts cannot substitute for per-project adequacy.

## Decision 2: Integrate NASA C-MAPSS as a temporal mechanics fixture

- **Decision**: Verify the four C-MAPSS families offline, including train/test
  trajectory shape and RUL alignment, but classify the evidence as simulated
  run-to-failure structural/RUL evidence.
- **Rationale**: The files provide explicit unit identity, cycle order, train
  trajectories that reach simulated failure, held-out test trajectories, and
  one RUL value per test unit. Observed artifacts contain contiguous cycles and
  26 numeric fields. This directly exercises time-safe grouping and future
  horizon mechanics unavailable in AI4I.
- **Authoritative references**:
  - NASA data portal: https://data.nasa.gov/dataset/prognostics
  - Kaggle mirror: https://www.kaggle.com/datasets/behrad3d/nasa-cmaps
- **Limits**: C-MAPSS is simulated, not real fleet telemetry. The verifier
  checks observed file counts instead of trusting the copied readme; in the
  downloaded FD004 snapshot the train/test unit counts are 249/248 and the RUL
  file has 248 values. RUL is not silently converted to a binary event without
  a separately frozen threshold and retained observations.

## Decision 3: Integrate MetroPT-3 as an external-anchor-dependent operational fixture

- **Decision**: Verify the raw MetroPT-3 stream and explicit failure intervals,
  but do not treat unanchored rows as negatives or claim fully labeled efficacy.
- **Rationale**: The canonical UCI artifact has 1,516,948 rows, 17 columns,
  monotonic unique timestamps, and one compressor stream spanning February to
  September 2020. The external failure report supplies four air-leak intervals;
  observed coverage is 8,657, 2,360, 17,315, and 1,622 rows respectively. The
  data is operationally grounded and tests observation windows, censoring, and
  external anchors better than synthetic AIOps logs. UCI presents the timestamp
  and failure intervals as date/time values without timezone information, so
  the verifier compares them as published and does not assign UTC.
- **Authoritative references**:
  - UCI record: https://archive.ics.uci.edu/dataset/791/metropt3%2Bdataset
  - Kaggle mirror: https://www.kaggle.com/datasets/joebeachcapital/metropt-3-dataset
  - UCI dataset DOI: https://doi.org/10.24432/C5VW3R
- **Limits**: The CSV has no in-file failure label; UCI supplies the four air-leak
  intervals as failure reports. The card says 1 Hz, but the
  observed dominant timestamp gap is 10 seconds with additional irregular gaps;
  the verifier reports cadence rather than normalizing it. One stream/system
  cannot establish cross-system generalization. The published time values do
  not establish a timezone; offset-qualified inputs require an authoritative
  mapping before they can be compared.

## Decision 4: Defer or reject the remaining first-pass candidates

| Candidate | Decision | Reason |
|---|---|---|
| AIOps Log Monitoring & Failure Detection | Structural-only/deferred | 1,746 rows from one host, one project, one instance over roughly two days; failure status is present but incident horizons and external provenance are not established. |
| Synthetic Kubernetes & Istio Logs | Fixture-only | 1,000 explicitly synthetic rows; useful for parser/order tests, not external evidence. |
| IoT-Integrated Predictive Maintenance | Fixture-only | 1,800 simulated rows from three machines; useful time/entity mechanics, not provenance-grade evidence. |
| Commit Instances | Rejected for primary JIT | The downloaded files contain process features and `contains_bug`, but no commit ID, project ID, or timestamp; one inspected project also has a constant target. |
| Bug prediction dataset | Deferred control | Historical class-level snapshots and cumulative metrics, not commit-level outcomes; semicolon-delimited and lacking a direct JIT event unit. |
| Ansible defect prediction | Deferred secondary JIT/IaC family | Strong repository/commit/file fields and 227,272 rows, but `failure_prone` is a file-level historical label whose exact time horizon and induction procedure require the original Zenodo artifacts. |
| Software Defect Analysis Dataset | Not admitted | Kaggle download/API access returned 403 during screening; provenance and file-level label linkage were not independently verified. |
| NASA/PROMISE static defects | Baseline-only | Credible static module labels, but no temporal change or commit lineage. |

## Rejected implementation scope

No model benchmark, cross-family pooled score, or automatic download is part of
this feature. Validation is limited to source identity, structure, temporal
ordering, label/anchor semantics, leakage boundaries, and explicit evidence
classification.
