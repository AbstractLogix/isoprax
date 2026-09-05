# Quickstart: Stage 1 Corpus Admission Spec Work

## Baseline validation (current repository)

```sh
uv run ruff check .
uv run pytest tests -q
uv run python examples/demo_cross_family.py
```

## Spec continuation checklist

Before implementation begins for this feature:

- Confirm `spec.md`, `research.md`, `plan.md`, and `tasks.md` are internally
  consistent.
- Confirm admission gates cover lineage, censoring, leakage, split freezing,
  adequacy, and claim discipline.
- Confirm Stage 0 claim boundary remains unchanged by Stage 1 planning text.

## Expected outcome

A planning-complete Stage 1 specification package exists under
`specs/002-stage1-corpus-admission/` and is ready for implementation without
re-deriving archived decisions.
