# Tasks: Stage 1 Evidence Reporting

**Input**: Design documents from `/specs/009-evidence-reporting/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, and
`contracts/evidence-reporting.md`

**Tests**: Contract-first tests are required by the constitution and explicitly
requested by the specification.

## Phase 1: Setup

**Purpose**: Establish the active feature and public API boundary.

- [X] T001 Confirm `specs/009-evidence-reporting/` is active in `.specify/feature.json` and preserve the feature contract in `specs/009-evidence-reporting/`.

## Phase 2: Foundational

**Purpose**: Define the deterministic report types and safe canonicalization shared by all stories.

- [X] T002 Create frozen profile, unavailable-evidence, gate-summary, and report dataclasses plus canonical hash helpers in `isoprax/evidence_reporting.py`.
- [X] T003 Export only the evidence-reporting public contract from `isoprax/__init__.py`.

**Checkpoint**: The pure reporting contract exists; user-story behavior can be implemented and tested.

## Phase 3: User Story 1 - Publish a bounded evidence report (Priority: P1) 🎯 MVP

**Goal**: Produce one deterministic, safe public evidence report from matching assembled, captured, and admitted evidence.

**Independent Test**: Equivalent valid inputs in different orders generate equal canonical report dictionaries and report identities without raw fields or payloads.

- [X] T004 [US1] Write failing determinism, public-field, capture-lineage, and raw-payload exclusion tests in `tests/test_evidence_reporting.py`.
- [X] T005 [US1] Implement validated assembly/capture/admission joins and safe capture/gate reductions in `isoprax/evidence_reporting.py`.
- [X] T006 [US1] Implement deterministic canonical public representation and identity generation in `isoprax/evidence_reporting.py`.

**Checkpoint**: A reader can inspect reproducible safe evidence and gate summaries.

## Phase 4: User Story 2 - Interpret incomplete evidence honestly (Priority: P1)

**Goal**: Preserve censoring and unavailable evidence while deriving the fixed evidence-only status and claim boundary.

**Independent Test**: Failed gates produce `blocked`, missing required evidence produces `inconclusive`, and complete passing evidence is only `admission_evidence`.

- [X] T007 [US2] Write failing blocked, inconclusive, censored-count, unavailable-evidence, and claim-boundary tests in `tests/test_evidence_reporting.py`.
- [X] T008 [US2] Implement explicit availability reduction, status derivation, censored summaries, and immutable claim boundary in `isoprax/evidence_reporting.py`.

**Checkpoint**: No report can turn missing or censored evidence into a conformance upgrade.

## Phase 5: User Story 3 - Reject unsafe publication inputs (Priority: P2)

**Goal**: Fail closed for contradictory lineage, unsafe claim scope, mismatched release/artifact metadata, or non-public provenance.

**Independent Test**: Each unsafe fixture raises a specific validation error and returns no report.

- [X] T009 [US3] Write failing unsafe-input tests for identity, capture, claim-scope, scope/artifact, and provenance mismatches in `tests/test_evidence_reporting.py`.
- [X] T010 [US3] Implement fail-closed profile and cross-record validation in `isoprax/evidence_reporting.py`.

**Checkpoint**: Unsafe material cannot be published through the reporting contract.

## Phase 6: Polish & Verification

**Purpose**: Confirm the documented public surface and whole-repository quality gate.

- [X] T011 Update the Stage 1 evidence-reporting boundary in `README.md` only if the public module changes reader-facing capability.
- [X] T012 Run the focused and full validation commands from `specs/009-evidence-reporting/quickstart.md`, record results, and mark completed tasks in `specs/009-evidence-reporting/tasks.md`.

## Dependencies & Execution Order

- Setup → Foundational → US1 → US2 → US3 → verification.
- US2 shares the report constructor created for US1; US3 extends the same validation boundary. This is intentionally sequential to keep one small public module coherent.

## Implementation Strategy

1. Implement the smallest viable report: validated joins, safe reduction, and determinism (US1).
2. Add honest availability/status handling (US2).
3. Harden every cross-record boundary with rejection tests (US3).
4. Run focused then full repository validation; do not describe the report as admission or conformance proof.

## Phase 7: Convergence

- [X] T013 Represent blank build-qualification or runner-execution references as unavailable evidence per FR-003 and US2/AC2 (partial).
