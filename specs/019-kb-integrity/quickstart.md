# Quickstart: Durable Knowledge-Base Integrity

```bash
uv run pytest -q tests/test_kb_integrity.py tests/test_conformance.py
uv run ruff check isoprax/kb.py tests/test_kb_integrity.py
uv run pytest -q
uv run ruff check .
```

The feature remains evidence storage infrastructure only; it does not widen
any conformance claim.
