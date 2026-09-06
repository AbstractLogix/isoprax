# Convergence: Hermetic Runner Integration

**Date**: 2026-09-06
**Outcome**: Converged

## Scope assessed

The implementation was checked against FR-001 through FR-009, all three user
stories, the stated edge cases, the plan's injected-backend boundary, and the
project constitution.

## Evidence obtained

- `uv run pytest tests/test_hermetic_runner.py -q --no-cov` — 6 passed.
- `uv run pytest tests -q` — 95 passed; 97.64% total coverage.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — 99 files already formatted.
- `uv run python examples/demo_cross_family.py` — completed; it continues to
  declare only Structural cross-family conformance and withholds pooled figures.
- `git diff --check` — passed.

## Result

`isoprax.hermetic_runner` is a deterministic adapter around one injected
external backend. It validates the preparation-bound digest, frozen command,
prepared source commit, non-root/read-only/isolated/network-disabled controls,
timeout, and canonical limits before treating a command as started. It records
an immutable execution and command identity, maps pre-start problems to
`blocked-before-compilation`, maps post-start non-success outcomes to
`censored`, and preserves declared artifact collection states and content
identities.

No container engine, registry, live workload/deployment runner, corpus-admission
decision, build qualification decision, or Isoprax conformance upgrade was
introduced. Those remain outside this feature's scope.
