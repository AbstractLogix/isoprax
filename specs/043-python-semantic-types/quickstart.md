# Quickstart: Strongly Typed Python Semantic Core

From the repository root:

```bash
uv sync --group dev
uv run mypy
uv run pytest -q tests/test_commensurability.py tests/test_semantic_types.py tests/test_evaluation.py
```

The mypy configuration checks the declared semantic files in strict mode. The focused tests cover normalized fields, legacy input forms, malformed-input rejection, commensurability evidence, evidence-to-ID binding, calibration qualification, and the Structural conformance ceiling. The positive type fixture must pass; each expected-failure fixture must fail for its named type mismatch.

Run the repository CI-equivalent checks before delivery:

```bash
uv lock --check
uv run ruff check .
uv run pytest tests -q
uv run python examples/demo_cross_family.py
```

The Haskell workflow is retired; `specs/042-haskell-semantics-kernel/assessment.md` retains the completed experiment's recorded results.
