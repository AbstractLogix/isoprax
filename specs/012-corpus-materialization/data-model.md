# Data Model: Reproducible Public Corpus Materialization

## Entities

- **PublicCorpusMaterializationProfile**
  - Fields: `profile_identity`, `expected_system_id`, `release_scope`,
    `horizon_rule`, `threshold_version`, `published_artifacts`
  - Rules: metadata must be non-empty and correspond to one frozen profile.

- **MaterializationInputRecord**
  - Fields: `record_identity`, `system_id`, `change_id`, `split`, `score_time`,
    `outcome_class`, `censor_reason`, `lineage_reference`, `artifact_refs`
  - Rules: must originate from accepted assembly/public observation artifacts;
    outcome fields are preserved, not recomputed.

- **WithheldEvidenceRecord**
  - Fields: `input_identity`, `reason`, `constraint_class`
  - Rules: reason is mandatory; one deterministic rejection reason per input.

- **PublicCorpusRecord**
  - Fields: `materialized_id`, canonical projection of accepted input fields,
    `claim_scope` (`public_corpus_evidence_only`)
  - Rules: deterministic ID from canonical payload hash; stable sort key for
    equivalent inputs.

- **PublicCorpusManifest**
  - Fields: `materialization_identity`, `profile_identity`, `counts`,
    `included_records`, `withheld_records`, `published_artifacts`,
    `claim_scope`
  - Rules: byte-identical for equivalent valid inputs; explicit inventories for
    included and withheld evidence.

## Relationships

1. One `PublicCorpusMaterializationProfile` governs many input records.
2. Each `MaterializationInputRecord` becomes either:
   - one `PublicCorpusRecord` (included), or
   - one `WithheldEvidenceRecord` (rejected).
3. One `PublicCorpusManifest` summarizes all included/withheld outputs for a
   single deterministic materialization run.

## State transitions

1. **Received**: input record accepted for validation.
2. **Validated**:
   - profile/scope/lineage/privacy checks pass, or
   - fail-closed rejection with deterministic reason.
3. **Materialized**: accepted records normalized, hashed, and sorted.
4. **Published (local artifact)**: manifest and inventories emitted for review.

## Validation rules mapped to Feature 012

- **FR-001**: Input must match one frozen profile and allowed public scope.
- **FR-002**: Deterministic ordering, hashes, and fixed claim boundary required.
- **FR-003**: Preserve score-time, outcomes, censoring, split, change grouping.
- **FR-004**: Reject mismatch/integrity failures; no substitution for missing data.
