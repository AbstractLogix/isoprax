# Quickstart: Complete Coverage Gate

```bash
uv run coverage json -o coverage.json
uv run python scripts/check_module_coverage.py coverage.json --minimum 95
```

Use `--source-root` to validate a different production source directory.
