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

- Stage 1 real-data validation is not implemented.
- Semantic conformance needs a shared Outcome Definition from a deterministic
  replay corpus; external candidate screening, predeclaration, and
  JEPA/profile work are
  not copied into this Stage 0 repository.
- No Full Conformance claim is available: only two of three strategy types are
  implemented and all evidence is synthetic.

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
