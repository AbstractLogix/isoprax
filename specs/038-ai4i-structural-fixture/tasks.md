---

description: "Task list for the offline AI4I 2020 structural fixture and commensurability checks"
---

# Tasks: AI4I 2020 Structural Fixture

**Input**: Design documents from `/specs/038-ai4i-structural-fixture/`

**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`,
`contracts/ai4i2020-verifier.md`, and `quickstart.md`

**Tests**: Included because the specification requires focused conformance tests
for source integrity, malformed records, label semantics, and non-poolable
outcome definitions.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the reviewable provenance boundary without fetching or
vendoring the external snapshot.

- [x] T001 [P] Add the pinned UCI/Kaggle source metadata, checksums, expected
  structural summary, and claim boundary to `examples/ai4i2020/manifest.json`
- [x] T002 [P] Document manual retrieval, offline verification, label leakage,
  and non-efficacy boundaries in `examples/ai4i2020/README.md`

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define the dependency-light verifier contract and test seams before
story-specific integration.

- [x] T003 [P] Add the verifier contract and expected report fields to
  `specs/038-ai4i-structural-fixture/contracts/ai4i2020-verifier.md` and keep
  `specs/038-ai4i-structural-fixture/quickstart.md` aligned with the CLI

**Checkpoint**: Provenance and operator-facing boundaries are explicit; no
network or data-science dependency is introduced.

## Phase 3: User Story 1 - Verify a pinned public snapshot offline (Priority: P1) 🎯 MVP

**Goal**: Verify a locally supplied AI4I CSV deterministically and fail closed on
source, schema, or row-level integrity problems.

**Independent Test**: Run `tests/test_ai4i2020.py` against small local CSV fixtures
and run the CLI against the downloaded UCI CSV; valid pinned data verifies and
malformed or changed data does not.

### Tests for User Story 1

- [x] T004 [P] [US1] Add parser, BOM-tolerant header, row-domain, duplicate-UDI,
  checksum, missing-file, and no-repair tests in `tests/test_ai4i2020.py`

### Implementation for User Story 1

- [x] T005 [US1] Implement `AI4I2020Expectations`,
  `AI4I2020VerificationReport`, canonical schema constants, CSV parsing, SHA-256
  verification, structural counts, and deterministic failure reasons in
  `isoprax/ai4i2020.py`
- [x] T006 [US1] Implement the offline JSON-reporting command with zero exit only
  for verified input in `scripts/verify_ai4i2020.py`

**Checkpoint**: User Story 1 is independently usable as an offline integrity
check and never downloads, drops, or relabels source rows.

## Phase 4: User Story 2 - Exercise outcome commensurability boundaries (Priority: P1)

**Goal**: Represent the composite and mode labels as distinct outcomes and prove
that related events remain non-poolable.

**Independent Test**: Compare the AI4I composite definition, a mode definition,
and the existing JIT defect definition; every event/process mismatch remains
irreducible with pooling disabled.

### Tests for User Story 2

- [x] T007 [P] [US2] Add outcome-definition, label-column separation, composite
  mismatch, multi-mode, and AI4I-versus-JIT irreducible commensurability tests in
  `tests/test_ai4i2020.py`

### Implementation for User Story 2

- [x] T008 [US2] Implement explicit AI4I composite/mode
  `OutcomeDefinition` values and the label/feature constants in
  `isoprax/ai4i2020.py`, preserving current-process sensor scope and disallowing
  pooling through the existing commensurability check
- [x] T009 [US2] Export the verifier, summary, schema constants, and outcome
  definition factory from `isoprax/__init__.py`

**Checkpoint**: User Stories 1 and 2 preserve source labels and report the
intended irreducible/non-poolable semantics without any efficacy claim.

## Phase 5: User Story 3 - Review bounded evidence and claim limits (Priority: P2)

**Goal**: Make the source identity, expected result, and structural-only boundary
reproducible for reviewers.

**Independent Test**: Review the manifest and quickstart, run the CLI on a local
artifact, and confirm the JSON report contains the documented fields and claim
boundary.

### Tests for User Story 3

- [x] T010 [P] [US3] Add manifest consistency and CLI JSON/exit-status tests in
  `tests/test_ai4i2020.py`

### Implementation for User Story 3

- [x] T011 [US3] Align `examples/ai4i2020/manifest.json`,
  `examples/ai4i2020/README.md`, and the feature quickstart with the implemented
  report fields and observed UCI snapshot counts
- [x] T012 [US3] Add the AI4I structural-fixture boundary and manual verification
  command to `README.md` without implying replay, efficacy, or Semantic/Full
  evidence

**Checkpoint**: Reviewers can reproduce the bounded structural result from a
local artifact and distinguish it from evidence-scale Isoprax evaluation.

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verify the complete feature and preserve unrelated work.

- [x] T013 [P] Run the focused AI4I tests and CLI against the pinned UCI artifact;
  record the observed verification output in
  `specs/038-ai4i-structural-fixture/quickstart.md`
- [x] T014 Run the full `uv run pytest -q`, `uv run ruff check .`,
  `uv run pre-commit run --all-files`, and `git diff --check`; do not modify the
  existing user-owned `.gitignore` edit
- [x] T015 Run Spec Kit convergence review and append any remaining implementation
  gaps to `specs/038-ai4i-structural-fixture/tasks.md`
- [x] T016 [US1] Reuse the shared chunked SHA-256 helper in the AI4I verifier and
  test the hash failure through that seam.

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: T001 and T002 can run in parallel.
- **Foundational (Phase 2)**: T003 follows the design artifacts and precedes
  implementation; it does not depend on network access.
- **User Story 1 (Phase 3)**: T004 must be written before T005; T006 follows the
  verifier API from T005.
- **User Story 2 (Phase 4)**: T007 must be written before T008; T009 follows the
  public API from T005 and T008.
- **User Story 3 (Phase 5)**: T010 follows the CLI and manifest shape; T011 and
  T012 update documentation after the implementation is stable.
- **Polish (Phase 6)**: Depends on all desired user stories.

### Parallel Opportunities

- T001 and T002 touch independent documentation files.
- T004 and T007 are separate test additions but must each precede their matching
  implementation task.
- T010 can be prepared independently once the report contract is fixed.
- T013 and other read-only documentation checks can run independently before the
  full repository gate in T014.

## Implementation Strategy

### MVP First (User Stories 1 and 2)

1. Complete the provenance setup and contract.
2. Write and run the offline verifier tests before implementation.
3. Implement the verifier and CLI, then verify the downloaded UCI CSV.
4. Add outcome definitions and prove composite/mode/JIT pooling is blocked.
5. Stop and validate the structural fixture before adding documentation polish.

### Incremental Delivery

1. Deliver source/schema verification as the MVP.
2. Add commensurability and label-leakage tests.
3. Add reviewer-facing manifest/README updates.
4. Run focused and full repository gates; preserve the existing `.gitignore` edit.

## Notes

- The full external CSV is intentionally not checked in.
- The verifier must preserve the published 27 composite/mode discrepancies.
- Passing this feature does not make the dataset a replay corpus or an efficacy
  corpus.
