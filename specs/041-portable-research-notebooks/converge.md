# Convergence Record: Guided Research Notebooks

## Result

The implemented Feature 041 scope matches its specification and plan. All five
notebooks run headlessly with no local benchmark data, keep raw-data analysis
behind successful verification, and leave saved outputs and execution counts
empty. Dataset analysis code paths also passed a smoke run against clearly
synthetic temporary fixtures; those runs are software-path checks, not corpus
results.

The first convergence pass found one partial plan gap: the C-MAPSS notebook
showed engine-life and sensor views but omitted a training-RUL distribution
plot. T021 added that train-only view per subset; the test RUL files remain
reserved for held-out evaluation.

## Verification obtained

- `make check`: passed. 564 tests passed and 1 was skipped; total branch-aware
  coverage was 98%, and every production module met the 95% floor. Ruff lint and
  formatting checks passed. The dependency audit found no known vulnerabilities;
  the local `isoprax-reference==0.2.0` package was skipped because it is not
  published on PyPI.
- `make notebook-check`: passed all five notebooks with an empty data directory;
  no outputs were saved.
- Focused notebook/workbench tests: 40 passed.
- Synthetic analysis-branch smoke: passed for AI4I, ApacheJIT, all four
  independent C-MAPSS subsets, and MetroPT-3.
- `uv lock --check` and `git diff --check`: passed.

## Gates not obtained

- No repository `data/` directory or pinned benchmark artifacts were available.
  Therefore none of the actual public-corpus baselines or plots has been run in
  this checkout, and no empirical result is claimed. After obtaining the exact
  expected local artifacts, the notebook verifiers must pass before the
  data-dependent cells can run.
- The configured Ubuntu/Windows and Python 3.10/3.12/3.14 CI matrix was not run
  from this local session. Hosted CI remains the platform-compatibility gate.

## Evidence boundary

These checks establish implementation/test behavior only. They do not establish
predictive efficacy, real-fleet performance, Semantic/Full Conformance, or
commensurability of cross-family scores. MetroPT-3 remains descriptive; rows
outside externally reported intervals remain censored.

## Review follow-up — 2026-09-24

Review found saved execution outputs/counts in three notebooks, inconsistent
kernel display metadata, and a checkout guard that compared the imported
package root to a default derived from that same import. All five notebooks now
have empty saved execution state and consistent kernel metadata. Their setup
locates the checkout from the notebook working directory (or an explicit root),
rejects a conflicting checkout, and then verifies the imported package path.

After these corrections, `make notebook-check` executed all five notebooks
without data files or saved outputs. A focused mismatch probe confirmed the
setup rejects an explicit root from another checkout. The full test suite and
95% per-module branch-coverage gate passed; Ruff lint/format, `uv lock --check`,
and `git diff --check` passed as well.
