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

## Convergence update (2026-09-05)

- Every prediction-time field now carries an observed-at timestamp and is
  rejected when it is later than its row's score time.
- Rows with failed build/deployment evidence or incomplete monitoring must be
  censored; they cannot be admitted as observed outcomes.
- Admission requires split-separated calibration-fit/gate row evidence,
  non-private/non-privileged corpus provenance, anchored predeclaration before
  collection, and at least one declared publishable artifact.
- These records are included in the deterministic admission manifest. Passing
  admission remains evidence infrastructure, not a Semantic or Full claim.
