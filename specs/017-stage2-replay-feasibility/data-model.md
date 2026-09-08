# Data Model: Stage 2 Deterministic Replay Feasibility

## ReplayPilotProfile

The immutable predeclared configuration for one bounded pilot.

- `profile_identity`: deterministic identity of the canonical profile
- `candidate_id`: screened public candidate identity
- `system_id`, `service_id`: one system boundary and service
- `selected_commits`: ordered immutable revisions to replay
- `workload_reference`: declared workload identity
- `outcome_definitions`: Change and Operational definitions, including
  structured event, observation process, window, and thresholds
- `horizon_rule`, `threshold_version`, `capture_schema_version`: frozen
  semantic and serialization versions
- `allowed_evidence_scope`, `published_artifacts`: release boundary
- `predeclaration_artifact_hash`, `external_anchor_reference`,
  `predeclaration_commit`, `corpus_data_commits`: ordering evidence
- `allowed_prediction_fields`, `forbidden_prediction_fields`: prediction-time
  information boundary
- `declared_thresholds`: minimum pilot counts/rates and repeatability criteria

Validation rules:

- exactly one system/service boundary is allowed;
- selected revisions are unique and non-empty;
- predeclaration and external anchor metadata are non-empty;
- the two family definitions must be directly or attested commensurable for a
  complete shared-label lane;
- split, horizon, threshold, schema, and release values are frozen before
  collection.

## ReplayTerminalRecord

The one terminal result associated with a selected revision. The existing
`ReplayCaptureRecord` is the source of capture and observation lineage.

- `commit`, `lane_identity`, `run_identity`
- `capture`: existing replay capture record
- `terminal_status`: `observed_positive`, `observed_negative`, `censored`, or
  `blocked-before-compilation`
- `stage`: the terminal stage that produced the result
- `reason`: required for censored and blocked results
- `started_at`, `completed_at`: execution timing for throughput
- `artifact_manifest`: hashes and public-scope state
- `change_label`, `operational_label`: explicit labels derived from the shared
  observation process; complete records must carry equal labels
- `shared_observation_identity`: canonical identity linking both labels to the
  same event/process/window/threshold semantics
- `prediction_field_names`: fields admitted before score time

Validation rules:

- one record per selected commit;
- complete positive/negative records require complete shared observation
  evidence;
- complete records require prediction-field evidence whose observation times do
  not exceed score time;
- censored and blocked records cannot be treated as negative outcomes;
- private or privileged observation evidence is non-releasable.

## RepeatabilityCheck

The deterministic comparison of two or more executions with the same frozen
lane inputs.

- `lane_identity`
- `run_identities`
- `outcome_agreement`
- `label_agreement`
- `artifact_agreement`
- `discrepancies`: stable field/reason entries
- `status`: `pass`, `fail`, or `inconclusive`

## FeasibilityReport

The deterministic, claim-bounded result for a pilot.

- `report_identity`
- `profile_identity`
- `status`: `feasible`, `inconclusive`, or `blocked`
- `counts`: selected, terminal, build, deployment, complete-window,
  positive, negative, censored, blocked, and withheld counts
- `rates`: explicitly denominated rates, never survivor-only rates
- `temporal_coverage`: declared split/window coverage and gaps
- `throughput`: per-stage elapsed time and resource/cost estimate
- `repeatability`: repeat checks and discrepancies
- `release_readiness`: public/private/privileged and artifact-manifest results
- `gates`: machine-readable pass/fail/inconclusive reasons
- `extrapolation`: assumptions and uncertainty for a proposed full corpus
- `claim_boundary`: feasibility only; no Semantic or pooled-performance claim

Identity rule: the report identity is a hash of canonical profile identity,
ordered terminal records, repeatability results, counts, rates, gates,
extrapolation, and claim boundary. It must not include raw private payloads.

## State transitions

```text
predeclared -> running -> complete
                    \\-> censored
                    \\-> blocked-before-compilation

complete + all declared gates pass         -> feasible
complete + underpowered/unstable evidence  -> inconclusive
any invalid ordering/scope/provenance      -> blocked
```
