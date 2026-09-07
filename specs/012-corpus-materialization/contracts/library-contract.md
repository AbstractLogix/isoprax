# Library Contract: Public Corpus Materialization

## Scope

Define deterministic, offline interfaces for producing a reviewable public corpus
artifact from accepted evidence records without changing outcomes or escalating
conformance claims.

## Proposed interfaces

### Materialization profile contract

```text
PublicCorpusMaterializationProfile:
  profile_identity: str
  expected_system_id: str
  release_scope: str
  horizon_rule: str
  threshold_version: str
  published_artifacts: tuple[str, ...]
```

### Input snapshot contract

```text
PublicCorpusSnapshot:
  system_id: str
  source_reference: str
  threshold_rule: str
  score_time: str
  window_end: str
  outcome_class: str
  censor_reason: str | null
  split: "train" | "calibration_fit" | "calibration_gate" | "test"
  change_group_id: str
  artifacts: tuple[str, ...]
  valid: bool
  uses_private_data: bool
  uses_privileged_telemetry: bool
```

### Materialized record contract

```text
PublicCorpusRecord:
  identity: str
  system_id: str
  source_reference: str
  threshold_rule: str
  score_time: str
  window_end: str
  outcome_class: str
  censor_reason: str | null
  split: str
  change_group_id: str
  artifact_count: int
  claim_scope: "public_corpus_evidence_only"
```

### Report contract

```text
PublicCorpusReport:
  materialization_identity: str
  records: tuple[PublicCorpusRecord, ...]
  withheld: tuple[WithheldEvidenceRecord, ...]
  counts: dict[str, int]
  claim_scope: "public_corpus_evidence_only"
```

```text
materialize_public_corpus(profile, snapshots) -> PublicCorpusReport
```

## Behavioral guarantees

1. Equivalent valid inputs MUST yield identical `materialization_identity` and
   record ordering.
2. Invalid, unsafe, or mismatched inputs MUST be withheld/rejected with explicit
   reasons.
3. No network I/O, no score recomputation, and no admission/conformance
   escalation are permitted.
4. All timestamps MUST parse as RFC3339 UTC (`...Z`) and preserve original
   value fields in outputs.
