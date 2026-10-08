# Convergence: Retrieval and Interpretation Dependence Research Design

**Date**: 2026-10-08
**Feature**: [spec.md](spec.md)
**Outcome**: Research-design slice converged; the prompted retrieval pilot is reported; the model-role experiment remains pending.

## Scope checked

The initial convergence check covered the literature note, benchmark protocol, Spec Kit artifacts, and research index. Later addenda record the prompted benchmark execution and Bouleusis raw-record analysis. The separately preregistered model-role experiment is not complete.

## Requirements and plan review

| Source | Result | Evidence |
|---|---|---|
| FR-001-FR-002 | Satisfied | The research note separates paper evidence, repository evidence, new findings, and open hypotheses; it uses the arXiv v1 title and does not attribute H1-H5 to the paper. |
| FR-003-FR-006 | Satisfied | The protocol defines conditions A-D, case types and provenance, separate evidence properties, budgets, and retrieval, interpretation, and dependence measures. |
| FR-007 | Satisfied | The protocol compares naive aggregation, one global shared-lineage label, a metadata-only rule, and an operation-specific rule on held-out cases. |
| FR-008-FR-009 | Satisfied | The protocol, plan, tasks, and quickstart define the study. The two-run report preserves a complete-result mismatch and limits claims to the synthetic fixture. |
| FR-010-FR-011 | Satisfied | The documents keep selection out of Bouleusis, runtime enforcement with Semadmit, and require a reproducible result before a handoff. |
| FR-012-FR-013 | Satisfied | The protocol defines selector-pair corroboration with controls matched to realized item and token budgets, plus a held-out calibration test against audited source status. |
| SC-001-SC-006 | Satisfied | The paper claims, metric boundaries, comparison rules, next-slice steps, and research-only recommendation are stated. |
| Constitution I-V | Satisfied | The slice changes no normative runtime behavior, labels evidence limits, and adds no retrieval or trust implementation. |

## Findings

The original documentation slice is complete. The local prompted pilot has run twice; its cases and selection traces match, while interpretation results do not. The result report records that limitation and makes no runtime enforcement recommendation.

## Validation

- Reviewed the primary arXiv version 1 source for the paper title, method, reported results, and stated limits.
- Checked local Markdown links and whitespace in the changed documents.
- The commit hook's IsoPrax contract checks passed. No software tests were added for this document-only slice.

## Original next slice

Implement and run the synthetic benchmark defined in [the protocol](../../docs/research/retrieval-selection-dependence-benchmark.md). Preserve the stated model and source lineage, held-out policy cases, budgets, metrics, uncertainty, and falsification rules.

That pilot is now complete and reported below. The outstanding slice is the separately preregistered model-role experiment. It remains blocked from scored calls until every requested role has an exact model identity, including the EmbeddingGemma alternative.

## Addendum: Bouleusis measurement-validity scope

The user supplied a separate retrieval sweep summary. The raw JSONL was found
in the Bouleusis checkout at
`docs/experiments/evidence-selection-sweep-2026-10-08.jsonl`. The report records
its SHA-256 and preserves 170 per-run outcomes in a derived file.

| Requirement | Result | Evidence |
|---|---|---|
| FR-022-FR-024 | Satisfied | The report recomputes recall and success from raw records, reconstructs false-belief claims from events, separates six measurement concepts, and counts one independent bug despite ten order/identifier variants. |
| FR-025 | Satisfied as a prospective draft | The iterative protocol defines a 20-bug minimum panel, equal-budget and repeat-reasoning controls, separate costs and outcomes, and pre-run decision criteria. Exact bug IDs and revisions remain to be frozen before execution. |
| FR-026 | Satisfied | The report makes no Semadmit independence recommendation from selector identity and requires cross-bug held-out error evidence plus simpler-rule comparisons. |
| SC-012-SC-013 | Satisfied | The report assesses all six requested claims and the proposed protocol is linked from the research map and quickstart. |

The supplied summary placed full context alongside the 540-byte condition.
Raw records instead log those ten runs separately as `unbounded`, with 660
selected bytes. The reanalysis treats this as a summary-labeling discrepancy,
not corruption of the raw experiment records. It leaves the JSONL unchanged
and compares only Random, Lexical, EmbeddingGemma 2, and the Fixture-order
positive control under the matched 540-byte budget. The reported 540-byte and
all-evidence selector aggregates reproduce. No new Bouleusis experiment was
run. This addendum does not complete the pending Feature 047 local-model
benchmark and does not authorize a runtime rule. The next research step is to
freeze and run the separate multi-bug iterative-retrieval design in Bouleusis,
then assess its held-out results in IsoPrax.
