# Quickstart: Evaluation Diagnostic Input Integrity

```bash
uv run pytest -q tests/test_conformance.py
uv run ruff check isoprax/evaluation.py examples/demo_cross_family.py
uv run pytest -q
uv run ruff check .
```
