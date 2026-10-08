# Implementation Plan: Retrieval and Interpretation Dependence Benchmark

**Branch**: codex/047-retrieval-selection-benchmark
**Date**: 2026-10-08
**Spec**: [spec.md](spec.md)

## Summary

Implement and execute the frozen synthetic selection-dependence benchmark plus a bounded model-role experiment. Use pinned local models and preserve the research-only boundary. Do not implement a retrieval product or runtime policy.

## Scope

The selection-dependence track generates a seeded synthetic case set, runs conditions A-D and their budgets, compares operation rules, and writes replayable results. The model-role track tests Tev1 calibration across declared question families, score meaning on a common evidence-relevance target, model-judgment error dependence, and coding specialization. It writes separate replayable results and an evidence report. Both tracks are synthetic. Neither reproduces UNREAL or establishes general model behavior. A separate document-only addendum reanalyzes the Bouleusis raw JSONL and preregisters a future multi-bug iterative-retrieval study; it adds no Bouleusis logic to IsoPrax.

The local Ollama interface does not expose hidden representations. Condition C therefore uses a prompted Model X selector proxy. Condition B uses a distinct prompted Gemma selector; it is not retrieval-specialized. The role track uses the requested Qwen3.5, Gemma4, Qwen2.5-Coder, EmbeddingGemma 2, Tev1, and Granite Guardian models. It evaluates each model in a task suited to its output form; role labels do not rank models or establish independence.

## Constitution Check

- **Specification Authority**: PASS. The research does not change the normative IsoPrax contract.
- **Honest Conformance**: PASS. Prior results and paper claims stay within their tested settings. The next benchmark is synthetic.
- **Contract-First Testing**: PASS. Focused tests cover case generation, prompt isolation, deterministic selectors, metric calculations, and result replay.
- **Deterministic Core, Explicit Effects**: PASS. The future study must pin seeds, inputs, model revisions, and software metadata.
- **Minimal Reference Scope**: PASS. No retrieval product, admission engine, orchestration, or deliberation behavior is added.

## Design Decisions

1. Use the primary arXiv version 1 as the source for paper title, method, results, and limitations.
2. Keep repository results, literature-supported statements, new findings, and hypotheses in separate sections.
3. Define four conditions A-D. Use paired comparisons to isolate selector and interpreter changes.
4. Use a fixed 16-item case pool and top-k budgets 1, 2, 4, 8, and 16.
5. Preserve source and derivation lineage separately from selector and model lineage.
6. Keep relevance, source status, and permission for a named operation as separate fields.
7. Compare three simple alternatives with an operation-specific rule on cases held out from policy authors.
8. Compare selector pairs against single-selector controls matched to the realized item and token budget for independent corroboration.
9. Test score calibration against held-out source-status labels, not relevance alone.
10. Require a reproducible held-out effect before proposing any Semadmit review.
11. State the next slice as benchmark implementation and execution; do not report results in advance.
12. Keep each target-family metric separate. Any pooled metric must name a mixture estimand and predeclared weights.
13. Compare EmbeddingGemma similarity, Tev1 probability, language-model self-reported probability, and Guardian's binary judgment only after naming a common held-out target. Fit score mappings on development data only.
14. Compare Qwen, Gemma, and Guardian errors on the same cases and target. Evaluate any equal-weight vote against each model alone; do not treat distinct model IDs as independent votes.
15. Evaluate Qwen2.5-Coder on software-debugging cases and non-code controls. Report family-specific outcomes, not a raw model leaderboard.
16. Record known lineage separately from exact model identity. Tev1's Qwen3.5 base and EmbeddingGemma 2's Gemma 4 architecture are declared analysis context, not proof of shared errors.

## Project Structure

- **docs/research/retrieval-selection-dependence.md**: literature context, repository results, hypotheses, boundaries, and recommendation.
- **docs/research/retrieval-selection-dependence-benchmark.md**: conditions, case protocol, measures, rules, analysis, falsification, and next-slice plan.
- **specs/047-retrieval-selection-dependence/preregistration.json**: frozen pilot configuration, models, splits, thresholds, and analysis choices.
- **scripts/retrieval_dependence_experiment.py**: local deterministic case generation, model calls, metrics, policies, and report rendering.
- **tests/test_retrieval_dependence_experiment.py**: focused checks for evidence boundaries and calculations.
- **specs/047-retrieval-selection-dependence/model-role-preregistration.json**: frozen model-role targets, families, revisions, splits, metrics, and pooling rules.
- **scripts/model_role_experiment.py**: target-specific synthetic role experiment with Ollama chat, embedding, and Tev1 decision interfaces.
- **tests/test_model_role_experiment.py**: focused checks for role-specific parsing, calibration, dependence, and pooling.
- **docs/research/model-role-commensurability-benchmark.md**: role comparison protocol and model-score boundaries.
- **docs/research/bouleusis-retrieval-measurement-validity.md**: raw-record reanalysis, metric limits, pseudo-replication, and claim assessment.
- **docs/research/bouleusis-retrieval-sweep-reanalysis.json** and **scripts/reanalyze_bouleusis_sweep.py**: source-hashed per-run reanalysis and deterministic validation of the external JSONL.
- **docs/research/iterative-retrieval-preregistration.md**: prospective multi-bug design; exact tasks and revisions must be frozen before execution.
- **specs/047-retrieval-selection-dependence/**: scope, plan, task record, research source, data model, quickstart, checklist, and convergence record.
- **docs/research/README.md**: entry points to the new research thread.

## Validation

Run focused tests. Run each frozen synthetic study twice using the pinned local model digests and seeds. Compare canonical input, trace, and result digests. Check the reports against machine-readable metrics and run git diff --check.

## Complexity Tracking

No exception. The runner uses the existing standard library, NumPy, and scikit-learn dependencies. Ollama is an explicit local research effect, not a project runtime dependency. The model proxy limitation remains visible in the report.
