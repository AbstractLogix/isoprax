# Quickstart: Admission Timestamp Integrity

```bash
uv run pytest -q tests/test_stage1_admission.py
uv run ruff check isoprax/admission.py tests/test_stage1_admission.py
uv run pytest -q
uv run ruff check .
```
