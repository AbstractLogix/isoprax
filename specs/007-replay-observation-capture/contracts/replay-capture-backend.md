# Replay Capture Backend Contract

The replay-capture backend is the single deployment and observation effect boundary. It receives immutable lane and upstream evidence inputs and returns observed deployment and telemetry facts. It must not mutate those inputs or decide the terminal outcome class.

## Input

- `lane`: one frozen `ReplayLaneDefinition`.
- `qualification_report`: the associated feature 005 build-qualification report.
- `execution`: one feature 006 `ExecutionEvidenceRecord` for the lane commit.

## Result facts

The backend result supplies:

- one `DeploymentEvidence`, including target, deployed commit, ordered timestamps, disposition, and immutable evidence reference when succeeded;
- one optional `ObservationEvidence`, including score/window timestamps, completeness, monitoring, validity, threshold-met result, allowed-scope declaration, diagnostic reason, and a mapping of declared artifact paths to byte payloads or unreadable markers.

## Required behavior

- The backend must report the actual deployed commit and target; the core censors the lane if either is missing, mismatched, or unverifiable.
- A deployment not reported as `succeeded` cannot have an observed outcome.
- Observation evidence can be reduced only after a successful attributable deployment and only when the full frozen window is complete, monitored, valid, inside the predeclared bounds, and within allowed scope.
- The backend must not use private third-party production data or privileged telemetry. The core treats asserted prohibited scope, missing scope evidence, or prohibited input as censored.
- Backend exceptions, malformed results, and missing observation results are retained as censored evidence with explicit diagnostics.
- `threshold_met` is a fact under the frozen threshold rule. The backend cannot supply a replacement threshold, horizon, workload, schema, revision, or service.

## Core guarantees

- Equivalent frozen inputs and validated backend facts produce the same lane identity.
- A changed material input produces a different identity or a censored record.
- Every request produces exactly one terminal `ReplayCaptureRecord`.
- The output is replay-observation evidence only and never an admission or conformance decision.
