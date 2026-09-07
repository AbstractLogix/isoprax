# Feature 014 Validation Quickstart

All commands run from the repository root and use the project’s `uv`
environment.

## Prerequisites

- Python 3.10–3.14 supported by the lockfile.
- Existing development dependencies installed through `uv`.
- No network access is required for the normative, structured-definition,
  calibration, strategy, or synthetic pooling-harm checks.

## Focused validation

Run the focused feature tests after implementation:

```bash
uv run pytest tests/test_normative_citations.py \
  tests/test_commensurability.py \
  tests/test_evaluation.py \
  tests/test_forecast_strategy.py \
  tests/test_pooling_harm.py
```

Expected result: all tests pass; unresolved citations, degenerate calibration,
invalid attestation, non-commensurable pooling, or ForecastSignal score
insertion fail explicitly.

## Demonstration

```bash
uv run python examples/demo_cross_family.py
```

Expected output includes graded commensurability, separate calibration and
discrimination status, a seven-day/ninety-day pooling-harm summary, and a
ForecastStrategy round-trip. It must not report Semantic/Full Conformance from
these results.

## Public-label evidence

Run the manifest validation command/test with the recorded public evidence
package. Expected outcomes are `reproduced` when all source and license
prerequisites are present, otherwise explicit `blocked` or `inconclusive`.
Neither outcome may be converted into a real-world conformance claim.

## Broader gates

After focused checks pass, run the repository’s documented `uv` pytest and
coverage commands. Report focused and broad results separately; do not turn a
blocked public-data check into a passing evidence claim.
