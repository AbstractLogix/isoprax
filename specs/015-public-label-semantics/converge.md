# Convergence: Public Label-Semantics and Split-Sensitivity Evidence

Implementation evidence:

- `uv run ruff check ...` passed for changed Python files.
- `uv run pytest tests/test_public_label_evidence.py -q --no-cov` passed with 9 tests.
- `uv run pytest -q` passed with 216 tests and 97.33% total branch-aware coverage.
- `uv run coverage json -o coverage.json && uv run python scripts/check_module_coverage.py coverage.json --minimum 95` passed; every production module met the threshold and the new public-label module reached 98%.
- The report sorts source identifiers, preserves procedure metadata, and keeps
  `pooling_permitted=False` for every comparison.

The public-data acquisition questions remain intentionally deferred: no network
source snapshot or real-world label claim is bundled by Feature 015. The
existing example manifest remains blocked until a licensed, versioned snapshot
is supplied.
