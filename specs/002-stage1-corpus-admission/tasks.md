# Tasks: Stage 1 Corpus Admission and Replay Evidence

## Phase 1: Setup and spec consistency

- [x] T001 Validate 002 artifact consistency across `spec.md`, `research.md`,
      `data-model.md`, and `contracts/library-contract.md`
- [x] T001a Confirm Stage 1 implementation authority decision is recorded before
      code work starts (dependency gate from `spec.md`)
- [x] T002 Define admission module skeleton and public API shape in
      `isoprax/admission.py`

## Phase 2: Admission gate core (TDD)

- [x] T003 [P] Add tests for lineage-chain required fields and immutable-link
      validation in `tests/test_stage1_admission.py`
- [x] T004 [P] Add tests for prediction-time leakage allowlist/forbidden-field
      checks in `tests/test_stage1_admission.py`
- [x] T005 Add tests for outcome classification and censoring exclusions in
      `tests/test_stage1_admission.py`
- [x] T006 Add tests for frozen chronological split and follow-up completeness
      in `tests/test_stage1_admission.py`
- [x] T006a Add tests for fixed horizon predeclaration and post-outcome horizon
      retuning rejection in `tests/test_stage1_admission.py`
- [x] T006b Add tests for four-split chronology constraints and overlap
      rejection in `tests/test_stage1_admission.py`
- [x] T007 Implement deterministic admission gate logic in
      `isoprax/admission.py`

## Phase 3: Manifest and reporting

- [x] T008 Add admission manifest structure and deterministic gate report output
      in `isoprax/admission.py`
- [x] T009 Add tests asserting deterministic repeated-run output identity in
      `tests/test_stage1_admission.py`
- [x] T010 Add tests that admission output never upgrades conformance class in
      `tests/test_stage1_admission.py`
- [x] T010a Add tests for single-system boundary enforcement and cross-system
      pooling rejection in `tests/test_stage1_admission.py`
- [x] T010b Add tests for clustered-by-change constraints when multiple
      observations derive from one change in `tests/test_stage1_admission.py`
- [x] T010c Add tests for release-scope metadata presence and threshold-freeze
      metadata validation in `tests/test_stage1_admission.py`

## Phase 4: Integration and documentation

- [x] T011 Integrate Stage 1 admission checks with existing Stage 0 entities
      (`events`, `signals`, `kb`) where needed
- [x] T012 Update README with Stage 1 admission scope statement and
      non-promotion claim boundary note
- [x] T012a Document independence and private-data exclusion constraints for
      Stage 1 evidence artifacts
- [x] T013 Run full validation (`ruff`, `pytest`, demo) and record evidence in
      `specs/002-stage1-corpus-admission/converge.md`

## Requirement traceability notes

- Lineage/linkage: FR-001, FR-015 → T003, T007
- Leakage control: FR-003, FR-016, FR-017 → T004, T007
- Censoring/outcome class: FR-002, FR-008, FR-009, FR-010 → T005, T007
- Split/horizon/calibration discipline: FR-004, FR-011, FR-012, FR-013, FR-018
  → T006, T006a, T006b, T007
- Deterministic reporting/claim boundary: FR-006, FR-020, FR-021 → T008, T009,
  T010
- Corpus-boundary/governance: FR-019, FR-022, FR-023, FR-024, FR-025 → T010a,
  T010b, T010c, T012a

## Phase 5: Convergence

- [x] T014 Record score-time provenance for every prediction field and reject fields observed after score time per FR-003 and FR-017 (missing).
- [x] T015 Require build, deployment, and monitoring evidence and enforce censorship when any required outcome evidence is unavailable per FR-009 and FR-010 (missing).
- [x] T016 Require and validate distinct calibration-fit and calibration-gate evidence tied to the corresponding chronological splits per FR-013 (missing).
- [x] T017 Require provenance that excludes private production data and privileged telemetry, and enforce anchored predeclaration before corpus collection for horizon and threshold rules per FR-018, FR-023, and FR-025 (missing).
- [x] T018 Include validated provenance, predeclaration, and publishable-artifact metadata in deterministic manifests per FR-014 and FR-024 (partial).
- [x] T019 Update completed feature status and convergence evidence with the obtained validation result per T013 (partial).
