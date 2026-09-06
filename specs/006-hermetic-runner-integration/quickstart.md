# Quickstart: Hermetic Runner Integration

## Prerequisites

- A synced project environment: `uv sync --group dev`
- A valid, non-blocked `BuildPreparation` from feature 005
- A test or approved backend that can report every effective containment control

## Focused validation

Run the feature's conformance tests:

```bash
uv run pytest tests/test_hermetic_runner.py -q
```

Expected result: valid fixture runs retain one `success` or `censored` evidence record per attempt; incomplete configuration, control mismatch, unavailable backend, or missing source evidence is `blocked-before-compilation` before command start.

Then run its existing integration boundary:

```bash
uv run pytest tests/test_build_qualification.py tests/test_hermetic_runner.py -q
uv run ruff check isoprax/hermetic_runner.py tests/test_hermetic_runner.py
```

See [data-model.md](data-model.md) and the [runner contract](contracts/runner-backend.md) for record and backend details.
