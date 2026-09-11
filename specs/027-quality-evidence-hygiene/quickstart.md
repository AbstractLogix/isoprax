# Quickstart: Quality and Release Evidence Hygiene

```bash
uv run pytest -q tests/test_replay_selection.py tests/test_release_metadata.py
uv run mutmut print-time-estimates
uv run mutmut run
uv run pytest -q
uv run ruff check .
```

Mutation output is test-strength evidence only; it does not establish a
conformance class. On the current locked environment, mutmut generates the
full package scope but its stats phase is blocked by a NumPy/scikit-learn
reload incompatibility in mutmut's in-process runner; treat that result as
inconclusive until the runner/dependency combination is upgraded.
