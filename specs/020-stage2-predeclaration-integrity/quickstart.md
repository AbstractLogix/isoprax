# Quickstart: Stage 2 Predeclaration Integrity

```bash
uv run pytest -q tests/test_stage2_whoami_pilot.py tests/test_stage2_feasibility.py
uv run python scripts/run_stage2_whoami_pilot.py --output /tmp/whoami-report.json
uv run pytest -q
uv run ruff check .
```

The generated report remains feasibility-only evidence.
