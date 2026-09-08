# Quickstart: Stage 2 Replay Feasibility

This feature is an offline, deterministic evidence reducer. It does not
download a project, start a container, or require production telemetry.
Execution effects are supplied by the existing injected replay backend.

## Prerequisites

- Python 3.10–3.14 managed with `uv`
- a screened public candidate and a predeclaration artifact
- a bounded set of immutable commits
- replay capture records produced by the existing hermetic/build/capture
  contracts

## Focused validation

After implementation, run the feature tests with the repository's normal
coverage options disabled for the focused loop:

```bash
uv run pytest -o addopts= tests/test_stage2_feasibility.py -q
uv run pytest -o addopts= tests/test_stage2_pilot_integration.py -q
uv run ruff check isoprax/stage2_feasibility.py tests/test_stage2_feasibility.py
```

The focused tests should cover:

1. a feasible pilot with complete positive and negative captures;
2. censored and blocked-before-compilation records retained in denominators;
3. invalid predeclaration ordering and scope rejected;
4. direct, attested, bridgeable, and irreducible definition comparisons;
5. repeated-lane disagreement producing `inconclusive` or a failed gate;
6. private/privileged evidence producing `blocked`;
7. post-score prediction fields and missing artifact lineage being rejected;
8. deterministic report identity and derived temporal coverage being
   independently revalidated.

`tests/test_stage2_pilot_integration.py` exercises the full injected path:
build preparation and qualification, hermetic execution evidence, replay
deployment/observation capture, terminal-record normalization, and feasibility
report validation. It is intentionally synthetic; a passing result proves the
pipeline wiring, not real-project replay throughput.

## Full validation

```bash
uv run pytest
uv run ruff check .
```

The resulting report is feasibility evidence only. It must not be used to
publish pooled cross-family scores, Semantic conformance, or full-corpus
adequacy.
