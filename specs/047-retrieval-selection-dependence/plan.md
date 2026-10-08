# Implementation Plan: Retrieval and Interpretation Dependence Research Design

**Branch**: codex/047-retrieval-selection-dependence
**Date**: 2026-10-08
**Spec**: [spec.md](spec.md)

## Summary

Publish a literature and repository evidence note, a pre-execution benchmark protocol, and a concrete next-slice plan. Keep the work research-only. Do not implement a retriever or runtime policy in this slice.

## Scope

This slice delivers documents that define the question and prepare a controlled synthetic study. It does not execute a benchmark or claim a new experimental result.

The next slice will implement and run the benchmark from [the protocol](../../docs/research/retrieval-selection-dependence-benchmark.md). That implementation must use a pinned model-native proxy if it does not use UNREAL itself.

## Constitution Check

- **Specification Authority**: PASS. The research does not change the normative IsoPrax contract.
- **Honest Conformance**: PASS. Prior results and paper claims stay within their tested settings. The next benchmark is synthetic.
- **Contract-First Testing**: PASS for this documentation slice. The protocol states the checks and result fields for the future runner.
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
8. Compare selector pairs against equal-budget single selectors for independent corroboration.
9. Test score calibration against held-out source-status labels, not relevance alone.
10. Require a reproducible held-out effect before proposing any Semadmit review.
11. State the next slice as benchmark implementation and execution; do not report results in advance.

## Project Structure

- **docs/research/retrieval-selection-dependence.md**: literature context, repository results, hypotheses, boundaries, and recommendation.
- **docs/research/retrieval-selection-dependence-benchmark.md**: conditions, case protocol, measures, rules, analysis, falsification, and next-slice plan.
- **specs/047-retrieval-selection-dependence/**: scope, plan, task record, research source, data model, quickstart, checklist, and convergence record.
- **docs/research/README.md**: entry points to the new research thread.

## Validation

Review every paper claim against the primary source. Check the listed local paths and links, verify the four conditions and metric definitions against the user request, search for prohibited scope expansion, and run git diff --check. No software test is needed for this document-only slice.

## Complexity Tracking

No exception. The protocol is intentionally a design for a future bounded study. It adds no runtime dependency or implementation.
