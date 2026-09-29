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
- `uv run pre-commit run --all-files`: passed after the semantic implementation change. The post-T028 local commit-hook rerun exercised the full suite but fell below the coverage floor because this local environment omitted CI's `gpu` extra; `isoprax/eb_jepa.py` consequently had only 30% coverage.
- `uv run --python 3.10/3.12/3.14 pytest tests/test_semantic_typecheck.py -q --no-cov`: both type-fixture tests passed on each runtime after T028.

## Remaining external gate

The first hosted run exposed a mypy environment mismatch: Python 3.14 resolves NumPy 2.5.2 stubs containing Python 3.12 `type` syntax, while the semantic checker intentionally targets Python 3.10. Strict project mypy now runs on the Python 3.10 matrix row, where the lock resolves compatible NumPy 2.2.6 stubs. A later matrix run also showed the positive/negative fixture harness was inheriting that Python 3.10 target on Python 3.12 and 3.14. The harness now uses the matrix interpreter's target for those fixtures; the configured strict project check remains at Python 3.10. The refreshed hosted full matrix, including GPU-backed coverage, is pending. This record does not claim hosted validation or a merge.

## Typed evidence integrity review follow-up (2026-09-29)

The typed evidence path now binds definition IDs, normalized definition-content digests, exact calibration sample digests, and a shared `CalibrationPolicy` (`min_events`, `n_bins`, `max_ece`). Authorization rejects same-ID semantic changes and policy mismatches. Authorized pooled ECE takes its bin count from the token. Direct `ObservationProcess` construction validates tuple-pair shape and string values, sorts the pairs, and rejects duplicates. `cross_family_report.pooled_ece` remains a documented same-call diagnostic for directly commensurable inputs, including uncalibrated inputs; its calculation is isolated in a low-level helper, and the unreachable retained-observation report branch is removed.

Verification obtained for this follow-up:

- `uv run pytest -q --no-cov tests/test_commensurability.py tests/test_semantic_types.py tests/test_commensurability_properties.py tests/test_semantic_typecheck.py tests/test_conformance.py`: 110 passed.
- `uv run mypy`: passed with zero diagnostics across the four declared semantic files.
- Focused Ruff lint and format checks for the eight changed Python source/test modules and the positive type fixture: passed.
- `git diff --check`: passed.
- `uv run python examples/demo_cross_family.py`: passed; it continued to withhold pooled output for non-commensurable synthetic definitions and remained Structural.

The full repository suite and hosted CI were not rerun for this focused follow-up. They remain external verification gates; this record makes no new full-suite or hosted-validation claim.

## CI-only semantic oracle follow-up (2026-09-29)

The earlier removal of the maintained Haskell package is superseded by this narrower decision: retain a small independent Haskell oracle only in CI, with no Python runtime dependency. The oracle covers normalized definition identity, calibration sample and policy binding, opaque evidence construction, pooled authorization, generated semantic invariants, compile-fail API checks, and differential evaluation of five shared contract fixtures. The workflow runs these checks when the semantic contract, its tests, fixtures, oracle, or workflow changes.

Local verification for this slice:

- The Python evidence, commensurability, type-boundary, and conformance tests passed: 122 tests.
- Strict mypy, focused Ruff lint/format, `uv lock --check`, YAML parsing, fixture projections, and `git diff --check` passed.
- The synthetic cross-family demo passed and continued to withhold pooling for non-commensurable definitions.
- The repository suite passed 587 tests with 4 skipped; pytest exited at the aggregate 95% coverage gate with 94.06%. The local environment lacks CI's `gpu` extra, leaving `isoprax/eb_jepa.py` at 30%; the changed `isoprax/semantic_types.py` reached 100% coverage.
- GHC and Cabal are unavailable in the local environment. Haskell compilation, QuickCheck, compile-fail checks, and cross-runtime differential execution must be confirmed by the hosted PR workflow before merging.
