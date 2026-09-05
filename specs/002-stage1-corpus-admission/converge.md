# Convergence: Stage 1 Corpus Admission and Replay Evidence

## Current status

- Stage 1 spec package created and aligned with repository constitution.
- Prior archive decisions migrated into Isoprax-compatible requirements and
  planning artifacts.
- Scope boundaries explicitly preserved (no JEPA/profile implementation import).
- `isoprax/admission.py` implemented with deterministic admission gates and
  manifest output.
- `tests/test_stage1_admission.py` added with coverage for lineage, leakage,
  censoring, split/follow-up, horizon freeze, adequacy, single-system boundary,
  clustered-by-change, determinism, and non-promotion claim posture.

## Remaining gates

- Decide first production admission profile values (final horizon rule/value and
  adequacy thresholds) for real corpus execution.
- Validate full repository checks and keep convergence evidence current as Stage
  1 implementation expands.

## Validation evidence (2026-09-05)

- `uv run ruff check isoprax tests` passed.
- `uv run pytest tests -q` passed (38 tests).
- `uv run ruff check .` passed.
- `uv run python examples/demo_cross_family.py` passed and preserved Stage 0
  Structural claim boundary (`pooled figure WITHHELD` for non-commensurable
  baseline Outcome Definitions).
