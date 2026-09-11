# Quickstart: Stage 2 Predeclaration Integrity

```bash
uv run pytest -q tests/test_stage2_whoami_pilot.py tests/test_stage2_feasibility.py
uv run python scripts/run_stage2_whoami_pilot.py --output /tmp/whoami-report.json
uv run pytest -q
uv run ruff check .
```

With the current published artifact, the command writes an explicit
`inconclusive` report because its public-commit anchor is not independently
verified. No feasibility report is emitted until an external attestation is
verified.
