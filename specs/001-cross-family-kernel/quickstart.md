# Quickstart

```sh
uv sync --group dev
uv run ruff check .
uv run ruff format --check .
uv run pytest tests -q
uv run python examples/demo_cross_family.py
uv run pre-commit run --all-files
```

Expected result: the test suite passes and the demo reports Structural
conformance while withholding a pooled figure for its non-commensurable
baseline Outcome Definitions.

## Continuation checks

Before adding new Stage 0 work, confirm these invariants still hold:

- Conformance tests stay green (`25 passed` or higher as suite grows).
- Demo output includes:
  - calibration diagnostics for each family,
  - `commensurable: False` for the baseline pair,
  - `pooled figure WITHHELD`, and
  - declarable class limited to `Cross-Family Conformance (Structural)`.
- No docs or code path upgrades this claim to Semantic or Full without new,
  reproducible evidence artifacts.
