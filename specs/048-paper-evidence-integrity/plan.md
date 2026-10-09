# Implementation Plan: Research Paper Evidence Integrity

**Branch**: `codex/047-retrieval-selection-benchmark` | **Date**: 2026-10-09 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/048-paper-evidence-integrity/spec.md`

## Summary

Audit and revise the cross-family manuscript, keep the model-role study separate, preserve raw inputs, add a machine-readable claim registry, and provide one deterministic integrity command with focused tests. No model calls or frozen-run changes are required.

## Technical Context

**Language/Version**: Python 3.10+ as supported by the repository

**Primary Dependencies**: Python standard library and existing locked project dependencies

**Storage**: Versioned Markdown, JSON, compressed raw JSONL snapshots, and repository files

**Testing**: `uv run pytest` for focused tests; repository check for final validation

**Target Platform**: Local repository and CI

**Project Type**: Research documentation and deterministic analysis utility

**Performance Goals**: Integrity verification completes without model calls and within ordinary local CI limits

**Constraints**: Preserve PR #54 and all frozen inputs; every data-derived statement must be traceable; no claim of external review or field validation

**Scale/Scope**: Main paper A, companion outline B, eight candidate claims, all pinned raw records needed for the registered findings

## Constitution Check

- **Specification authority**: Pass. This package reports conformance properties and does not change normative Isoprax rules.
- **Honest conformance**: Pass. Synthetic evidence and repository checks remain explicitly scoped.
- **Contract-first testing**: Pass. The integrity command and claim registry receive focused tests for expected results and fail-closed errors.
- **Deterministic core**: Pass. Verification uses fixed local artifacts and no model/network calls.
- **Minimal reference scope**: Pass. No general trust engine, runtime rule, or experimental orchestration is added.
- **Workflow**: Pass. Python execution uses `uv`; frozen model runs are not rerun or modified.

## Project Structure

```text
docs/research/
├── Calibration Is Not Enough_ Outcome Commensurability as a Precondition for Cross-Family Failure Prediction.md
├── paper-scope-decision-2026-10-09.md
├── literature-citation-audit-2026-10-09.md
├── paper-claims-evidence.json
├── paper-counterexamples-2026-10-09.md
├── paper-replication.md
├── paper-review-packet-2026-10-09.md
└── model-role-companion-outline-2026-10-09.md

docs/experiments/bouleusis-2026-10-08-raw/
├── *.jsonl.gz
└── manifest.json

scripts/paper_integrity.py
tests/test_paper_integrity.py
specs/048-paper-evidence-integrity/
```

**Structure Decision**: Keep analysis in one small standalone script, separate from model acquisition and policy-candidate code. Keep the manuscript, registry, literature audit, scope decision, and reviewer materials as separate reviewable documents.

## Risks and Controls

- **Declaration truth is not machine-checkable**: Describe normalized equality as a declaration check; require evidence and review for real semantic equivalence.
- **External raw source access**: Package exact uncompressed records in lossless compressed snapshots and retain the original repository, commit, and hashes.
- **Repeated measures**: Preserve case-level results and use the declared sampling unit; do not treat order perturbations as independent tasks.
- **Missing metrics**: Report unavailable when the raw record lacks required fields.
- **Publication novelty**: Present the contribution as a candidate contract contribution and request independent review; do not claim the measurement principle itself is a new statistical discovery.

## Validation Strategy

Run the integrity command against the packaged inputs, its focused tests, `git diff --check`, and the repository check. Verify the new raw snapshots against the exact source digests. Check the PR head and its review state without merging.
