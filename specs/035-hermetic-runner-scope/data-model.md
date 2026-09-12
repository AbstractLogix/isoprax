# Data Model

The execution boundary remains:

```text
BuildPreparation + ApprovedRunnerConfiguration
  -> injected RunnerBackend
  -> ExecutionEvidenceRecord
```

The backend is an integration dependency. The record is evidence of reported
controls and outcomes, not an implementation-provided hermeticity proof.
