# Convergence: Replay Screening Refinement

## Evidence obtained

- Early screening is deterministic and fail-fast in the documented four-step order.
- The legal screen requires exactly one retrievable governing source-build instrument and retains it on a restriction failure.
- The replay-readiness screen accepts only the three documented classes with an evidence reference.
- Early eligibility is explicitly marked as deferred historical build-rate qualification; caller-supplied build rates do not affect it.
- `uv run pytest tests/test_replay_selection.py -q` passed: 6 tests.
- `uv run pytest tests -q` passed: 57 tests.
- Focused Ruff checks and format checks passed for touched Python files.

## Remaining gate

An eligible early candidate still needs measured historical build-rate qualification using the actual hermetic replay environment. That later evidence is intentionally not claimed here.
