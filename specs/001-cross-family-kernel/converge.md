# Convergence: Cross-Family Reference Kernel

## Evidence obtained

- Authoritative v0.3 POC modules were copied into the project and formatted.
- The SQLite KB verifies that an Outcome Definition matches the originating
  probability signal before persisting feedback.
- `uv run ruff check .` and `uv run ruff format --check .` passed.
- `uv run pytest tests -q` passed: 25 tests.
- `uv run python examples/demo_cross_family.py` completed and self-reported
  Cross-Family Conformance (Structural), withholding its pooled figure.
- `uv run pre-commit run --all-files` passed after the formatter repaired a
  generated Spec Kit JSON newline; the hook is installed for this checkout.

## Remaining gates

- Stage 1 real-data validation is implemented in Feature 016 as a separate
  public-data adapter/report slice; this Stage 0 convergence record remains
  limited to the synthetic kernel.
- Semantic conformance needs a shared Outcome Definition from a deterministic
  replay corpus; external candidate screening, predeclaration, and
  JEPA/profile work are
  not copied into this Stage 0 repository.
- No Full Conformance claim is available: only two of three strategy types are
  implemented and all evidence is synthetic.

## Convergence update (2026-09-05)

- Events now reject blank identifiers/sources and malformed or non-UTC RFC 3339
  timestamps before entering the Stage 0 flow.
- Calibration checks reject unequal/non-binary inputs and declare one-class
  evidence uncalibrated; focused tests cover those edge cases.
- The Stage 0 report remains Structural even when synthetic inputs share a
  commensurable definition; it cannot declare Semantic or Full Conformance.
- Time-sliced and paired-comparison utilities now have focused acceptance and
  rejection coverage.

## Continuation backlog (reuse-first)

Next specification work should reuse prior archive decisions where compatible,
not re-derive them from scratch:

1. Stage 1 corpus-acquisition/admission spec (single-system lineage,
  prediction-time leakage controls, censoring rules, split freeze rules,
  adequacy gates, and claim-discipline outputs).
2. Replay capture topology spec (lane isolation, anchor drift quarantine,
  positive-only confirmation replicates, and pilot gates for interference).
3. Release-governance spec for manifest-level reproducibility and explicit
  privacy/release approval recording.

These items are deferred by design under Stage 0 scope and should be created as
new feature specs rather than expanded into this reference kernel.
