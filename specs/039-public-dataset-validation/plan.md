# Implementation Plan: Evidence-Bounded Dataset Examples

**Branch**: `039-public-dataset-validation` | **Date**: 2026-09-22 | **Spec**: [spec.md](spec.md)

## Summary

Apply one evidence-bounded integration pattern across four complementary
examples: the existing AI4I 2020 synthetic structural/label-semantics fixture,
ApacheJIT repository-derived JIT labels, NASA C-MAPSS simulated
run-to-failure/RUL trajectories, and MetroPT-3 externally anchored air-leak
intervals. Add or retain manifests, a decision ledger, separate outcome
definitions, focused rejection-path tests, and local-only verification that
reports structural/evidence status without downloading, repairing, relabeling,
or silently dropping data. Feature 038 remains the detailed AI4I
implementation record; this feature defines the shared overview and extension
principles.

## Technical Context

**Language/Version**: Python 3.10-3.14, standard library for the new verifier
core

**Primary Dependencies**: Existing Isoprax domain modules; no new runtime
dependency; `pytest`, Ruff, and `uv` remain development tooling

**Storage**: Explicit local CSV/TXT/JSON artifacts; no database and no
vendored public datasets

**Testing**: Focused pytest contract tests, CLI smoke tests, repository Ruff,
pre-commit, and the existing branch-aware coverage gate

**Target Platform**: Linux/WSL and other Python-supported environments with
local files; network access is neither required nor used

**Project Type**: Python library plus small verification CLI and checked-in
evidence manifests

**Performance Goals**: Stream large CSV/TXT artifacts without loading complete
files into memory; MetroPT-3 exact duplicate checks retain identity sets, so
memory scales with the distinct row and timestamp counts

**Constraints**: Fail closed on malformed identity, schema, time, hash, and
anchor evidence. The implementation must not infer negatives, normalize broken
records, or convert structural verification into efficacy/conformance claims.

**Scale/Scope**: 10k AI4I rows, 106k ApacheJIT rows, approximately 180k
C-MAPSS trajectory rows across four subsets, and approximately 1.5M MetroPT-3
observations.

## Constitution Check

All gates pass before implementation:

1. **Specification Authority**: Every verifier rule maps to FR-001 through
   FR-011 and the existing outcome/commensurability contracts. No Kaggle card
   is treated as normative.
2. **Honest Conformance**: Reports carry evidence class and claim boundary;
   AI4I is synthetic, ApacheJIT is repository-derived, C-MAPSS is simulated,
   and MetroPT-3 is external-anchor-dependent. No efficacy, Semantic, or Full
   Conformance claim is produced.
3. **Contract-First Testing**: Tests cover valid snapshots and malformed,
   duplicate, hash, ordering, RUL, and missing-anchor rejection paths.
4. **Deterministic Core, Explicit Effects**: Verifiers take explicit paths and
   interval inputs, use only deterministic standard-library parsing, and make
   no network calls or automatic repairs.
5. **Minimal Reference Scope**: Dataset-specific parsing remains in narrow
   modules; no generic ingestion layer is added. Deferred datasets are
   represented in the ledger rather than absorbed into runtime code.

## Project Structure

```text
isoprax/
├── ai4i2020.py                  # existing synthetic snapshot and label verifier
├── apachejit.py                 # ApacheJIT schema/hash/label verifier
├── nasa_cmaps.py                # C-MAPSS trajectory/RUL verifier
├── metropt3.py                  # MetroPT-3 stream/anchor verifier
├── public_dataset.py            # shared hashing/error-deduplication helpers
├── public_label_evidence.py     # existing outcome/evidence boundary
└── __init__.py                  # public exports

scripts/
├── verify_ai4i2020.py           # offline AI4I CLI
└── verify_public_dataset.py     # offline CLI with JSON output

examples/
├── ai4i2020/manifest.json
├── apachejit/manifest.json
├── cmapss/manifest.json
├── metropt3/manifest.json
├── metropt3/failure_intervals.json
└── public-datasets/decision-ledger.json

tests/
├── test_ai4i2020.py             # existing AI4I structural/label checks
└── test_public_dataset_validation.py

specs/039-public-dataset-validation/
├── data-model.md
├── contracts/verification-report.md
├── quickstart.md
└── tasks.md
```

**Structure Decision**: Keep dataset-specific parsing and typed report models
in focused library modules. The three public-data verifiers introduced here
share no generic ingestion framework because identity, time, censoring, and
label semantics differ materially. Their reports serialize to the common CLI
envelope, while `public_dataset.py` contains only shared hashing and
error-deduplication helpers. The CLI is an explicit adapter over the verifier
modules, not a network client or benchmark runner.

AI4I uses the same evidence boundaries and shared hash and error-deduplication
helpers but retains its own parser, report, and verifier. Its detailed
acceptance record is in Feature 038.

## Design Details

- Hashes and observed canonical counts are constants in each verifier and are
  reported in the result. A caller may pass a non-canonical fixture only when
  tests explicitly disable canonical identity checking; the production CLI
  always checks the pinned artifact.
- Reports contain `verified`, `errors`, and auditable observed counts. A
  malformed input can never become valid by dropping a row.
- ApacheJIT keeps file-order timestamp inversions and year/epoch mismatches as
  diagnostics. It does not sort records or rewrite the published year.
- C-MAPSS parses whitespace records, validates contiguous cycles per unit, and
  aligns test units to RUL values by observed unit order. It does not derive a
  binary failure label from RUL.
- MetroPT-3 accepts an explicit UCI-sourced interval manifest. It counts rows covered by
  each interval but returns no negative label for rows outside the intervals.
- Outcome definitions are separate and are passed through the existing
  commensurability guard. A numeric score range never makes the families
  poolable.

## Complexity Tracking

No constitution violations or additional architectural complexity are
introduced.
