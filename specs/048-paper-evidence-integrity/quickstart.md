# Quickstart: Research Paper Evidence Integrity

From the repository root, run:

```sh
uv run python scripts/paper_integrity.py
uv run pytest --no-cov tests/test_paper_integrity.py
```

The command verifies the artifact manifest and model-role archives, recomputes the registered raw-record counts and results, and checks every numeric claim marked as used in the main manuscript. It must fail if a file hash changes or a numeric claim lacks a reproducible protocol.

No model call, network request, or change to frozen runs is needed.
