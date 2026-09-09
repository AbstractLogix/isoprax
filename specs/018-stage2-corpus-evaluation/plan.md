# Implementation Plan: Stage 2 Corpus Evaluation Gate

**Branch**: `codex/018-stage2-corpus-evaluation` | **Spec**: [spec.md](spec.md)

## Design

Add a pure `stage2_corpus_evaluation.py` reducer that consumes released Stage 2
terminal summaries and existing per-family evaluation inputs. It validates
corpus provenance and split integrity first, then calculates or delegates
family-scoped calibration/discrimination evidence. A constant-score predictor
must fail the non-degeneracy gate even when its calibration error is low.

The reducer will not acquire data, choose a cloud runner, or infer semantic
equivalence. Existing `stage2_feasibility.py`, `corpus_assembly.py`,
`public_label_evidence.py`, and `per_family_evaluation.py` remain the source
contracts.

## Project Structure

```text
specs/018-stage2-corpus-evaluation/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── converge.md
└── tasks.md

isoprax/stage2_corpus_evaluation.py
tests/test_stage2_corpus_evaluation.py
```

## Quality Gates

- Focused rejection-path tests before implementation completion.
- Full pytest with the repository coverage and per-module gates.
- Ruff and pre-commit hooks.
- No Semantic or pooled claim in demo, README, or report output.
