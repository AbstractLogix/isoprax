# Quickstart: Stage 2 Corpus Evaluation Gate

This feature is a deterministic evidence reducer. It does not acquire a
corpus or claim Semantic Conformance.

## Planned checks

```bash
uv run pytest -o addopts= tests/test_stage2_corpus_evaluation.py -q
uv run ruff check isoprax/stage2_corpus_evaluation.py tests/test_stage2_corpus_evaluation.py
uv run pytest
uv run ruff check .
```

The first implementation must include a passing per-family case, a
constant-score rejection, split leakage rejection, missing-label-yield
inconclusive result, incompatible-pooling rejection, and independent report
validation.
