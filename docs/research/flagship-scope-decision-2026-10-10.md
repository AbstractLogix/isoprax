# Flagship scope decision — 2026-10-10

## Decision

The flagship paper concerns the outcome-commensurability contract, structural versus semantic conformance, and the contract's ability to refuse unsupported direct cross-family comparisons. The six-role model study is companion research. It is not used to support a paper claim about JIT or operational failure prediction.

The standalone package retains all 36 claim records so the research registry remains auditable. It marks 24 claims as flagship and 12 as companion-only. The integrity runner checks only the 24 flagship claims. It keeps companion artifact references as provenance and does not fetch or require their files.

| Evidence | Flagship | Companion or other track | Reason |
|---|---:|---:|---|
| Synthetic Benchmark A and its same-target control | Yes | No | Tests equal calibration summaries under distinct targets and a named mixture. |
| 23-case operation-gate challenge | Yes, descriptive | No | Compares four rules on an internally authored finite challenge. |
| Six-role model outputs and Tev1 question-family scores | No | Yes | Tests model roles on authored synthetic questions, not JIT/AIOps failure outcomes. |
| Embedding, critic, retrieval, and acquisition records | No | Yes | Separate synthetic or source-specific experiments. |
| Semadmit and Bouleusis assurance artifacts | No | Separate assurance evidence | Bounded software and replay checks do not establish claim truth, forecast quality, or cross-family equivalence. |

## Claims and limitations

The retained flagship result is a synthetic counterexample to the sufficiency claim: matching calibration summaries do not make two declared outcomes one common event. The equal-weight pool is reported only as its named mixture estimand. The same-target control is a positive control.

The operation-gate table reports finite counts from 23 cases authored within the project. It does not estimate field error rates or establish general superiority. Ranking and decision changes are not reported because the saved case rows do not independently support those counts.

The paper does not claim that Semadmit enforces this contract, that Bouleusis reasoning is accurate, or that any real-world JIT and AIOps outcomes are commensurable. Four disputed forecast calibration cases remain unresolved and are not part of the flagship claims.

## Publication boundary

No model output or model weight is required by this paper. Tev1's fine-tuned-weight and output terms remain unresolved for the companion study. The standalone branch does not include per-run model responses, model weights, or the separate Bouleusis raw retrieval archive. The registry keeps companion summaries as remote references only.

The paper replication can run from a clean public checkout. No private GitHub access is required. Automated integrity checks do not count as independent scientific review.

## PR history

PR #54 contains the frozen six-role study. PR #55 is stacked on the PR #54 branch and includes 34 changed files. Retargeting #55 to `main` would expose all 82 files in PR #54's diff. This branch starts from `main` and contains only the flagship package. Leave #54 and #55 unchanged; use a new review PR for this isolated work so their commits and CI history remain available.
