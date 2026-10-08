# Implementation Plan: Retrieval and Interpretation Dependence Benchmark

**Branch**: codex/047-retrieval-selection-benchmark
**Date**: 2026-10-08
**Spec**: [spec.md](spec.md)

## Summary

Implement and execute the frozen synthetic benchmark in the research protocol. Use pinned local language models through the Ollama API, a BM25 baseline, and a prompted-selector proxy. Keep the work research-only. Do not implement a retrieval product or runtime policy.

## Scope

This slice generates a seeded synthetic case set, runs the predeclared selector/interpreter conditions and budgets, compares operation rules, and writes replayable results and an evidence report. It does not reproduce UNREAL or establish general model behavior.

The local Ollama interface does not expose hidden representations. Condition C therefore uses a prompted Model X selector proxy. Condition B uses a distinct prompted Model Y selector; it is not retrieval-specialized. These deviations are frozen in the preregistration and limit the claim.

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

## Project Structure

- **docs/research/retrieval-selection-dependence.md**: literature context, repository results, hypotheses, boundaries, and recommendation.
- **docs/research/retrieval-selection-dependence-benchmark.md**: conditions, case protocol, measures, rules, analysis, falsification, and next-slice plan.
- **specs/047-retrieval-selection-dependence/preregistration.json**: frozen pilot configuration, models, splits, thresholds, and analysis choices.
- **scripts/retrieval_dependence_experiment.py**: local deterministic case generation, model calls, metrics, policies, and report rendering.
- **tests/test_retrieval_dependence_experiment.py**: focused checks for evidence boundaries and calculations.
- **specs/047-retrieval-selection-dependence/**: scope, plan, task record, research source, data model, quickstart, checklist, and convergence record.
- **docs/research/README.md**: entry points to the new research thread.

## Validation

Run the focused unit tests. Run the full benchmark twice using the frozen local model digests and seeds. Compare the canonical case, selection, and result digests. Check the report against machine-readable metrics and run git diff --check.

## Complexity Tracking

No exception. The runner uses the existing standard library, NumPy, and scikit-learn dependencies. Ollama is an explicit local research effect, not a project runtime dependency. The model proxy limitation remains visible in the report.
