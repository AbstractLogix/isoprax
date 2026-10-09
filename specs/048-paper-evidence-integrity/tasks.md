# Tasks: Research Paper Evidence Integrity

**Input**: Design documents from `specs/048-paper-evidence-integrity/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`

## Phase 1: Setup

- [x] T001 Create the paper-evidence documentation and snapshot directories in `docs/research/` and `docs/experiments/bouleusis-2026-10-08-raw/`.

## Phase 2: Foundational

- [x] T002 Define the machine-readable claim and artifact schema in `docs/research/paper-claims-evidence.json`.
- [x] T003 Add pinned raw snapshots and source hashes to `docs/experiments/bouleusis-2026-10-08-raw/manifest.json`.

## Phase 3: User Story 1 - Trace a paper claim to its evidence

**Independent Test**: Every main-paper claim ID resolves to a registry record with a valid source, artifact, and qualification.

- [x] T004 [US1] Audit every current citation and relevant new work in `docs/research/literature-citation-audit-2026-10-09.md`.
- [x] T005 [US1] Record the A/B publication decision in `docs/research/paper-scope-decision-2026-10-09.md` and companion outline in `docs/research/model-role-companion-outline-2026-10-09.md`.
- [x] T006 [US1] Revise the main manuscript and map its substantive claims to `docs/research/paper-claims-evidence.json`.

## Phase 4: User Story 2 - Recompute frozen results

**Independent Test**: Hash, count, and recompute checks pass on valid artifacts and fail on altered inputs.

- [x] T007 [P] [US2] Implement raw artifact and registered-claim checks in `scripts/paper_integrity.py`.
- [x] T008 [US2] Add fail-closed tests for hashes, counts, missing metrics, and numeric claim coverage in `tests/test_paper_integrity.py`.
- [x] T009 [US2] Independently recompute the registered raw analyses and retain per-run findings in `docs/research/paper-replication.md`.

## Phase 5: User Story 3 - Assess scope and submission readiness

**Independent Test**: An external reviewer can assess the central contribution, methods, counterexamples, limits, and open questions without treating automation as peer review.

- [x] T010 [P] [US3] Add contract-level counterexamples and permission/refusal risks in `docs/research/paper-counterexamples-2026-10-09.md`.
- [x] T011 [US3] Prepare reviewer questions, threats to validity, and readiness gates in `docs/research/paper-review-packet-2026-10-09.md`.
- [x] T012 [US3] Link the package and evidence-status labels in `docs/research/README.md`.

## Phase 6: Polish and cross-cutting checks

- [x] T013 Run the quickstart checks, repository check, focused diff review, and record the exact outcomes in `docs/research/paper-replication.md`.

## Dependencies and execution order

- T001-T003 precede the user-story work.
- T004-T006 establish literature and scope before manuscript claims are edited.
- T007-T009 depend on the registry and packaged raw inputs.
- T010-T011 use the final contract description and registered evidence.
- T012-T013 finish after all documents and analysis exist.

## Implementation strategy

Complete the claim registry and raw integrity path first. Then revise the manuscript within the evidence boundary, prepare the companion outline and reviewer packet, and run the deterministic checks. Do not score new cases.
