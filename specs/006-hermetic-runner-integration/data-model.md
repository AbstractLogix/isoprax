# Data Model: Hermetic Runner Integration

## ApprovedRunnerConfiguration

Frozen configuration for one execution attempt.

| Field | Rules |
|---|---|
| `immutable_identity` | Non-blank, digest-pinned identity (`@sha256:`) |
| `command` | Non-empty predeclared command tuple |
| `timeout_seconds` | Positive integer |
| `resource_limits` | Non-empty canonical key/value limits |
| `network_disabled` | Must be true |
| `source_read_only` | Must be true |
| `work_storage_isolated` | Must be true |
| `non_root` | Must be true |
| `declared_artifacts` | Duplicate-free relative output paths |

## EffectiveRunnerControls

Controls reported by the backend for the attempted execution, including the frozen command and source commit. Each value must match the approved configuration and selected revision before a command can be considered started.

## ExecutionEvidenceRecord

Immutable evidence for exactly one attempt. It links `preparation_hash`, `commit`, configuration identity, command identity, effective controls, terminal status and reason, duration, command-start state, and artifact evidence.

State mapping:

```text
invalid preparation/configuration/effective controls/source/backend unavailable
  -> blocked-before-compilation
started build exits, times out, or is interrupted
  -> censored
started build exits successfully
  -> success
```

## ArtifactEvidence

One collection record for every declared artifact with a `state` of `collected`, `missing`, or `unreadable`. Collected artifacts contain SHA-256 and byte length; non-collected artifacts contain no content identity.

## Relationships

`BuildPreparation` (feature 005) -> `ApprovedRunnerConfiguration` -> `ExecutionEvidenceRecord` -> zero or more `ArtifactEvidence` records. The deterministic execution identity binds the preparation, commit, configuration, and effective controls.
