# Flagship replication — 2026-10-10

## Scope

This package reproduces the flagship's synthetic Benchmark A and its 23-case operation-gate challenge. It does not reproduce the six-role model study, Tev1 calibration results, retrieval studies, acquisition studies, or the separate v2 operation-policy challenge.

The package retains the 36-row claim registry. The integrity runner checks the 24 flagship claims. It lists the 12 companion claims as out of scope and does not require their files.

## Clean checkout commands

From the repository root in a full-history checkout:

```sh
uv sync --locked --group dev --extra gpu
uv run python scripts/flagship_paper_integrity.py
uv run python scripts/flagship_paper_integrity.py --check-only
uv run pytest --no-cov -q tests/test_flagship_paper_integrity.py tests/test_research_experiments.py
uv run ruff check scripts/flagship_paper_integrity.py tests/test_flagship_paper_integrity.py
uv run ruff format --check scripts/flagship_paper_integrity.py tests/test_flagship_paper_integrity.py
uv run pytest tests -q --cov-report=xml
```

The first integrity command writes `paper-recomputed-results.json` and `paper-recomputed-tables.md`. The second checks them without writing. The runner makes no model calls, network calls, or private repository requests. It needs no GitHub credentials.

The focused provenance test reads Git history to confirm that the standalone runner exists at its stated introduction commit. A shallow clone does not contain enough history for that test or for the repository's predeclaration ancestry tests. The claim registry identifies the earlier research source commit, the runner's introduction commit, and SHA-256 values for checked-out artifacts. Record the validation commit with `git rev-parse HEAD` and the linked CI run after checks complete; do not embed that commit in the self-hashed registry.

## Reproduced numeric claims

Benchmark A uses 100 synthetic cases per lane. Each lane reports mean forecast 0.800, event rate 0.800, and Brier score 0.160. ROC AUC is unavailable because the forecasts are constant. The different-target result is the exact equal-weight mixture `synthetic.mixture.change-30d-and-operational-30m.equal-weight`, with weights 0.5 and 0.5. It is not a common-event probability. The same-target control uses `synthetic.shared.threshold-breach.30m` for both lanes and its pooled record.

The operation-gate table is rebuilt from all 23 saved case records. It recomputes false permissions, unnecessary refusals, and interpretation errors for the four named rules. It does not report ranking or decision changes. It does not use the aggregate summary in the source file as its case-level result.

The result summary preserves the frozen case rows and reports the measured counts. The source data and experiment modules are hashed. The checker pins only the three result sections required by the paper. A change to an unrelated result section does not affect the flagship check; a change to a used section fails it.

## Integrity limits

- These are deterministic synthetic demonstrations, not field estimates.
- The operation cases were authored within the project. Their expected labels were not independently adjudicated.
- Re-running source code checks calculation and byte identity. It does not prove that real event declarations or observation processes are true.
- Passing this package is not independent scientific review.
