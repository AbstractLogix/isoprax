# Quickstart: Replay Observation Capture

## Prerequisites

- A synced project environment: `uv sync --group dev`
- A qualified `BuildQualificationReport` from feature 005
- A successful `ExecutionEvidenceRecord` from feature 006 for the same prepared revision
- A frozen one-service `ReplayLaneDefinition`
- A deterministic test backend that reports deployment and observation facts without using private production data or privileged telemetry

## Focused validation

Run the feature conformance tests:

```bash
uv run pytest tests/test_replay_capture.py -q
```

Expected result: a complete attributable fixture lane is observed-positive or observed-negative under its frozen rule. Build ineligibility, deployment failure, attribution mismatch, rollback/replacement, telemetry gaps, incomplete windows, invalid evidence, and prohibited scope each retain exactly one censored record.

Then run the directly related boundaries and lint:

```bash
uv run pytest tests/test_build_qualification.py tests/test_hermetic_runner.py tests/test_replay_capture.py -q
uv run ruff check isoprax/replay_capture.py tests/test_replay_capture.py
```

See [data-model.md](data-model.md) for record constraints and the [replay-capture backend contract](contracts/replay-capture-backend.md) for effect-boundary behavior.
