# Quickstart: Replay Corpus Assembly

## Prerequisites

- A synced environment: uv sync --group dev
- Frozen replay capture records from feature 007
- A predeclared one-system assembly profile and score-time field evidence

## Focused validation

```bash
uv run pytest tests/test_corpus_assembly.py -q
```

Expected result: valid capture inputs become deterministic Stage 1-compatible rows; censored captures stay censored; invalid lineage, profile, field-time, split, duplicate-change, and scope inputs are explicitly rejected.

Then run direct boundaries:

```bash
uv run pytest tests/test_replay_capture.py tests/test_stage1_admission.py tests/test_corpus_assembly.py -q
uv run ruff check isoprax/corpus_assembly.py tests/test_corpus_assembly.py
```
