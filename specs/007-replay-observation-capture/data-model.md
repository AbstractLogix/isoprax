# Data Model: Replay Observation Capture

## ReplayLaneDefinition

Frozen input for exactly one capture lane.

| Field | Rules |
|---|---|
| `system_id` | Non-blank; one source system |
| `service_id` | Non-blank; one service |
| `commit` | Non-blank; must match execution evidence |
| `workload_reference` | Non-blank immutable reference |
| `horizon_rule` | Non-blank frozen rule |
| `outcome_threshold_rule` | Non-blank frozen rule |
| `capture_schema_version` | Non-blank immutable schema identifier |
| `allowed_evidence_scope` | Non-blank release/evidence scope that forbids private production data and privileged telemetry |

## DeploymentEvidence

Facts reported for one attempted deployment.

| Field | Rules |
|---|---|
| `target_id` | Non-blank attributable target identifier |
| `deployed_commit` | Must equal lane commit |
| `started_at`, `completed_at` | RFC 3339 UTC timestamps, ordered |
| `disposition` | `succeeded`, `failed`, `unverifiable`, `rolled_back`, or `replaced` |
| `evidence_reference` | Non-blank immutable reference when deployment succeeds |

Only `succeeded` can lead to an observed outcome. Every other disposition is censored.

## ObservationArtifactEvidence

One declared observation artifact.

| Field | Rules |
|---|---|
| `path` | Unique relative path |
| `state` | `collected`, `missing`, or `unreadable` |
| `sha256`, `byte_count` | Required only for collected byte payloads |

## ObservationEvidence

Backend-reported outcome facts for the frozen window: score time, window start/end, completion/monitoring/validity flags, threshold-met result, an evidence-scope declaration that exactly matches the lane, diagnostic reason, and artifact payloads. Its timestamps must be RFC 3339 UTC, ordered, and exactly match the frozen lane bounds.

## ReplayCaptureRecord

Immutable terminal evidence for one requested lane: lane identity; copied frozen definition; qualification report and execution identities; deployment and observation evidence or their explicit unavailability; outcome class; censor reason when censored; and `claim_scope=replay_observation_evidence_only`.

### Terminal state mapping

```text
unqualified preparation / non-success execution / mismatched upstream evidence
  -> censored
failed, unverifiable, rolled-back, or replaced deployment
  -> censored
incomplete, invalid, out-of-window, unavailable, or prohibited observation evidence
  -> censored
complete, attributable, allowed observation evidence + threshold met
  -> observed_positive
complete, attributable, allowed observation evidence + threshold not met
  -> observed_negative
```

## Relationships

`BuildQualificationReport` -> `ExecutionEvidenceRecord` -> `ReplayLaneDefinition` -> `DeploymentEvidence` -> `ObservationEvidence` -> `ReplayCaptureRecord`.

The deterministic lane identity binds the definition, qualified upstream identities, and validated deployment/observation facts. Artifact identity is separate so unavailable evidence remains explicit.
