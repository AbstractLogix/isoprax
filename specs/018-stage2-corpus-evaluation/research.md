# Research Notes: Stage 2 Corpus Evaluation Gate

## Decision

Start with a deterministic corpus/evaluation reducer rather than a new public
adapter. The merged feasibility pilot proves lane mechanics but has only
negative labels, so it cannot support qualified calibration, discrimination, or
Semantic evaluation.

## Existing seams

- `stage2_feasibility.py` provides terminal records, lineage, censoring, and
  the feasibility claim boundary.
- `corpus_assembly.py` and `admission.py` provide corpus row and provenance
  contracts.
- `per_family_evaluation.py` provides family-scoped evaluation primitives.
- `public_label_evidence.py` provides public label-semantics evidence.

## Decisions still requiring evidence

1. Which public replay corpus has enough positive and negative observations.
2. Whether the selected corpus supports a defensible time split without leakage.
3. Which discrimination metric is stable under the available class balance.
4. Whether the evidence package is sufficient for a later Semantic claim review.

These are gates, not defaults. This feature must report them as unresolved or
blocked until measured.
