# JEPA Unified Predictor Quickstart

Run from `/home/oscar/projects/isoprax`.

## Focused validation

```sh
uv run pytest -q tests/test_jepa.py
```

Expected result: all JEPA training, readout, persistence, calibration, determinism,
and fail-closed conformance tests pass.

## Repository validation

```sh
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

The existing admission/evaluation suite is intentionally included: no JEPA change
should alter the existing 800-row floor, calibration utilities, or existing signal
contracts.

## Evidence boundary

The quickstart demonstrates a deterministic reference backend and Structural
conformance evidence only. It does not train a GPU model, use a real replay corpus,
or establish Semantic/Full Conformance or predictive efficacy.
