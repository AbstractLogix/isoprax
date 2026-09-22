# Data Model: Evidence-Bounded Dataset Examples

## PublicSnapshot

The manifest-level identity of a locally supplied artifact.

| Field | Meaning |
|---|---|
| `dataset_id` | Stable dataset family identifier (`ai4i2020`, `apachejit`, `cmapss-fd001`, `metropt3`) |
| `canonical_source` | Authoritative Zenodo/NASA/UCI URL |
| `discovery_source` | Kaggle discovery/mirror URL |
| `version` | Published version or pinned snapshot description |
| `license` | Source license, not inferred from the mirror |
| `artifact_sha256` | Content identity for the artifact or named file set |
| `evidence_class` | Repository-derived, simulated, external-anchor-dependent, structural-only, deferred, or rejected |
| `claim_boundary` | The strongest claim allowed by the evidence |

## AI4IObservation

One synthetic process-cycle row with a composite machine-failure outcome and
five separate mode indicators. The mode indicators are not prediction inputs
for the composite outcome; Feature 038 contains the verifier-specific contract.

## ApacheJITCommit

One CSV row with the published 18-column schema. `commit_id` is the unique
identity; `project` and `author_date` provide repository and temporal context;
`buggy` and `fix` are preserved published booleans. Numeric process metrics are
validated for finite values but are not reinterpreted.

## CMapssTrajectory

One `(unit, cycle)` row with three operational settings and 21 sensor values.
Training rows are simulated run-to-failure trajectories. Test rows are
right-censored trajectories paired with one RUL value per observed test unit.
Cycle continuity is an integrity invariant, not a claim about physical time.

## MetroPT3Observation

One CSV row keyed by the source row identifier and timestamp, followed by the
published compressor signals. Timestamps must be unique and non-decreasing.
Cadence is measured from adjacent timestamps and reported, not normalized.

## FailureIntervalAnchor

An externally sourced inclusive time interval with a stable `anchor_id`, a
human-readable source reference, and timezone-unqualified start/end values.
The UCI record does not specify a timezone, so verification compares the
published date/time values as written and rejects timezone-qualified values
unless an authoritative mapping is added. Coverage counts are evidence of
overlap only. Observations outside an interval remain unlabeled/censored.

## VerificationReport shape

This is the serialized envelope for the three Feature 039 CLI verifiers, not a
shared runtime class. Each dataset module owns its typed report model and maps
it to this stable CLI shape. The AI4I CLI retains its Feature 038 report
contract.

```text
verified: bool
dataset_id: string
artifact: object
observed: object
diagnostics: object
errors: list[string]
warnings: list[string]
```

`verified` is true only when all required invariants pass. Warnings are
published artifact diagnostics that do not invalidate identity, such as
ApacheJIT file-order inversions or MetroPT-3 irregular cadence. Errors are
actionable failed invariants and are never downgraded to warnings.
