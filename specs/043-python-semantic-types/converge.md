# Convergence Record: Strongly Typed Python Semantic Core

**Status**: Implemented locally; branch review remediation complete; hosted CI pending.

## Scope and outcome

Reviewed all 14 functional requirements, 9 measurable success criteria, 9 acceptance scenarios, the 5 constitution principles, and the plan's language, dependency, scope, and compatibility decisions. The requirements checklist is complete. The two-axis branch reviews found and drove fixes for seven semantic gaps: pooled authorization did not bind later vectors to calibration samples; retained observations could upgrade mismatched definitions; free-text attestations could upgrade mismatched definitions; incomplete definitions could compare equal; unknown semantic mapping keys were silently discarded; fractional calibration labels were truncated; and direct `Threshold` construction could bypass field validation. The earlier mixed-threshold ordering defect remains fixed as well.

Python now stores normalized outcome values, rejects incomplete and unknown semantic inputs, represents commensurability with a closed result union, and provides generic evidence gates with runtime definition-ID and canonical sample-digest checks. Attestations retain provenance but cannot upgrade mismatched definitions; bridgeable outcomes remain non-poolable until a future operation actually re-derives them under a shared definition. Calibration labels must be exact binary integers. Strict mypy covers `isoprax/commensurability.py`, `isoprax/semantic_types.py`, `isoprax/evaluation.py`, and `isoprax/admission.py`. Property tests exercise eight core invariants at 1,000 generated examples each. Seven expected-failure programs and one valid program test the evidence type boundary.

The maintained Haskell package, CI workflow, differential runner, fixture directory, benchmark script, and active usage guide were removed. The experiment assessment and verification record remain under `specs/042-haskell-semantics-kernel/`.

## Verification obtained

- `uv lock --check`: passed; 230 locked packages resolved.
- `uv run mypy`: passed with zero diagnostics across all four declared files; local run remained below one second.
- `uv run ruff check .` and `uv run ruff format --check .`: passed.
- `uv run pytest tests -q --cov-report=xml`: 610 passed, 1 skipped in 36.45 seconds; 97.94% branch-aware overall coverage.
- `scripts/check_module_coverage.py coverage.json --minimum 95`: passed for every production module.
- `scripts/check_notebooks.py`: all 5 notebooks passed.
- `examples/demo_cross_family.py`: passed and continued to report the Stage 0 Structural boundary with non-commensurable pooled figures withheld.
- Positive and expected-failure mypy examples passed as part of the test suite.
- The pre-change implementation reproduced `TypeError: '<' not supported between instances of 'str' and 'int'` for mixed numeric/text threshold values; the total sort key and regression remain covered.
- Review regressions prove that substituted samples, mismatched attestations, unknown semantic fields, fractional calibration labels, invalid direct threshold values, retained-observation-only pooling, and incomplete outcome definitions all fail closed.
- `uv run pre-commit run --all-files`: passed after the final code change; the same repository contract checks run on commit.

## Remaining external gate

Hosted CI has not run for this branch. Its full Python version matrix and standard hosted-runner timing remain unverified. This record does not claim hosted validation or a merge.
