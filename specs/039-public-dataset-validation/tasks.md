# Tasks: Evidence-Bounded Dataset Examples

**Input**: Design documents from `/specs/039-public-dataset-validation/`

**Prerequisites**: `spec.md`, `research.md`, `plan.md`, `data-model.md`, and
`contracts/verification-report.md`

**Scope note**: AI4I 2020 is the first example and is already implemented and
converged under [Feature 038](../038-ai4i-structural-fixture/). The tasks here
record its integration boundaries and the additional ApacheJIT, C-MAPSS, and
MetroPT-3 implementations without duplicating Feature 038's AI4I task history.

## Phase 1: Foundational contracts

- [x] T001 [P] Add shared streaming-hash and stable error-deduplication helpers in `isoprax/public_dataset.py`; keep typed reports in each dataset verifier.
- [x] T002 [P] Add ApacheJIT, C-MAPSS, and MetroPT-3 outcome-definition factories using existing evidence/commensurability types in `isoprax/apachejit.py`, `isoprax/nasa_cmaps.py`, and `isoprax/metropt3.py`.
- [x] T003 [P] Add canonical source, mirror, license, hash, evidence class, and claim-boundary manifests under `examples/{apachejit,cmapss,metropt3}/manifest.json`.
- [x] T004 Add the screened-candidate decision ledger under `examples/public-datasets/decision-ledger.json`, preserving accepted, fixture-only, deferred, and rejected statuses.

## Phase 2: User Story 1 - Verify a canonical JIT snapshot (P1)

**Goal**: Verify ApacheJIT locally with exact schema, identity, labels, metrics,
hash, and auditable artifact diagnostics.

**Independent test**: A canonical downloaded CSV passes; changed bytes,
malformed rows, duplicate commit IDs, bad booleans, bad timestamps, and bad
numeric fields fail closed with named errors.

- [x] T005 [P] [US1] Write focused ApacheJIT acceptance and rejection tests in `tests/test_public_dataset_validation.py` before implementation.
- [x] T006 [US1] Implement streaming ApacheJIT CSV parsing, canonical hash/count checks, duplicate identity detection, label validation, finite metric validation, file-order inversion counting, and year/epoch diagnostics in `isoprax/apachejit.py`.
- [x] T007 [US1] Export ApacheJIT verifier/report/outcome APIs from `isoprax/__init__.py`.
- [x] T008 [US1] Add the ApacheJIT CLI subcommand and JSON report rendering in `scripts/verify_public_dataset.py`.
- [x] T009 [US1] Run the ApacheJIT verifier against the downloaded canonical mirror and record the observed result in `specs/039-public-dataset-validation/quickstart.md`.

## Phase 3: User Story 2 - Validate temporal operational fixtures (P1)

**Goal**: Preserve C-MAPSS unit/cycle mechanics and MetroPT-3 time/anchor
semantics without inferring labels or negatives.

**Independent test**: Canonical C-MAPSS subsets pass; broken cycles and RUL
alignment fail. MetroPT-3 passes only with explicit four-interval anchors and
reports cadence/coverage; absent anchors remain incomplete.

- [x] T010 [P] [US2] Write C-MAPSS and MetroPT-3 acceptance/rejection tests, including cycle gaps, RUL mismatch, non-monotonic timestamps, missing anchors, and uncovered-row censoring, in `tests/test_public_dataset_validation.py`.
- [x] T011 [US2] Implement C-MAPSS whitespace parsing, per-unit contiguous-cycle checks, train/test/RUL alignment, pinned hashes, and separate run-to-failure/RUL outcome definitions in `isoprax/nasa_cmaps.py`.
- [x] T012 [US2] Implement MetroPT-3 CSV streaming, header/schema checks, unique identity/time checks, cadence diagnostics, explicit interval-anchor validation, coverage counts, and external air-leak outcome definition in `isoprax/metropt3.py`.
- [x] T013 [US2] Export C-MAPSS and MetroPT-3 verifier/report/outcome APIs from `isoprax/__init__.py`.
- [x] T014 [US2] Add C-MAPSS and MetroPT-3 CLI subcommands and fail-closed exit status in `scripts/verify_public_dataset.py`.
- [x] T015 [US2] Add the explicit MetroPT-3 interval-anchor file under `examples/metropt3/failure_intervals.json` and verify all four downloaded C-MAPSS subsets plus MetroPT-3.

## Phase 4: User Story 3 - Publish admission decisions and claim boundaries (P2)

**Goal**: Make corpus identity, evidence class, outcome definitions, and
cross-family non-poolability reviewable.

**Independent test**: Manifests and the decision ledger classify every screened
candidate; outcome-definition comparisons remain irreducible where event or
observation process differs.

- [x] T016 [P] [US3] Add manifest/ledger shape and claim-boundary tests in `tests/test_public_dataset_validation.py`.
- [x] T017 [US3] Add explicit commensurability tests proving ApacheJIT, C-MAPSS, MetroPT-3, AI4I, and existing JEPA family outcomes do not authorize cross-family pooling in `tests/test_public_dataset_validation.py`.
- [x] T018 [US3] Document source hierarchy, licenses, hashes, observed counts, verification commands, and non-claims in `specs/039-public-dataset-validation/quickstart.md` and the root `README.md`.

## Phase 5: Verification and convergence

- [x] T019 Run focused tests and inspect the diff; fix only feature-scoped failures.
- [x] T020 Run repository quality gates with `uv`, including tests, Ruff, pre-commit, lock consistency, and branch-aware coverage.
- [x] T021 Run Spec Kit convergence against `spec.md`, `plan.md`, and `tasks.md`; append and complete any discovered gap before reporting completion.
- [x] T022 [US2] Preserve MetroPT-3 interval times as published without assigning UTC, retain the UCI source reference, and name the reported air-leak event accurately.
- [x] T023 [US1/US2] Reject unrepresentable ApacheJIT epochs and fractional C-MAPSS unit/cycle identifiers.
- [x] T024 [US3] Complete decision-ledger artifact identity/outcome fields, add observed C-MAPSS counts and license qualification, and record downloaded-artifact verification results.
- [x] T025 Update completed feature status and write the review convergence record after repository checks.
- [x] T026 [US2] Reject missing or non-string MetroPT-3 interval fields at the CLI input seam and preserve the fail-closed report contract.
- [x] T027 [US3] Reframe the shared specification and root README around all four dataset examples while preserving Feature 038 as the AI4I implementation record in `specs/039-public-dataset-validation/spec.md` and `README.md`.

## Phase 6: Convergence

- [x] T028 [US2] Harden MetroPT-3 anchor identity, advance the temporal baseline for every valid row, and report interval coverage for the first valid row after malformed records; add whitespace-alias, cadence, and leading-invalid-row regressions per FR-005/FR-006.
- [x] T029 [US1] Report ApacheJIT per-project positive-yield fractions for every project, including zero-positive projects, in structured/JSON diagnostics and verify a multi-project fixture per FR-003.
- [x] T030 [US2] Add a standalone passing C-MAPSS train/test/RUL fixture that proves contiguous-cycle and RUL alignment acceptance per US2/AC1 and SC-002.
- [x] T031 [US2] Add a standalone passing MetroPT-3 fixture with explicit anchors and exact interval coverage, preserving out-of-anchor observations as censored per US2/AC2, FR-006, and SC-003.
- [x] T032 [US1] Make the no-local-path AI4I CLI case report the unavailable snapshot without network access, and cover it with a subprocess regression test per Feature 038 US1/AC3.
- [x] T033 [US2] Reject timezone-qualified MetroPT-3 CSV timestamps and interval anchors because the UCI source does not specify a timezone; preserve the source-reported date/time values without conversion.

## Dependencies and execution order

- T001-T004 form the foundation. T005/T010/T016/T017 may be authored in
  parallel, but implementation follows their tests.
- User Story 1 and User Story 2 are independent after the foundation and may
  be implemented in parallel; their shared CLI/export edits must be merged
  carefully.
- User Story 3 depends on the outcome factories and manifests from Stories 1
  and 2.
- T019-T021 are final gates and must run after all implementation tasks.
