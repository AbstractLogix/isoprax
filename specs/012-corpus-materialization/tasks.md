# Tasks: Reproducible Public Corpus Materialization

**Input**: Design documents from `/specs/012-corpus-materialization/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/library-contract.md`

**Tests**: Include focused deterministic and rejection-path tests per constitution Principle III.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Align feature pointer and add deterministic test scaffolding.

- [ ] T001 Confirm feature context points to `specs/012-corpus-materialization` in `.specify/feature.json`
- [ ] T002 [P] Add/update public corpus exports in `isoprax/__init__.py`
- [ ] T003 [P] Create test scaffold file `tests/test_public_corpus.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build shared contracts and deterministic normalization helpers required by all story behavior.

- [ ] T004 Create `PublicCorpusSnapshot` and `PublicCorpusRecord` dataclasses in `isoprax/public_corpus.py`
- [ ] T005 [P] Implement RFC3339 UTC timestamp parsing helper in `isoprax/public_corpus.py`
- [ ] T006 [P] Implement canonical payload hashing helper in `isoprax/public_corpus.py`
- [ ] T007 Implement shared validation guards (public-only scope, private/privileged rejection, artifact integrity) in `isoprax/public_corpus.py`

**Checkpoint**: Foundational validation and deterministic identity helpers exist.

---

## Phase 3: User Story 1 - Reproduce a public corpus artifact (Priority: P1) 🎯 MVP

**Goal**: Produce deterministic, reviewable public corpus records with explicit censored/withheld handling from accepted public evidence.

**Independent Test**: Equivalent input permutations produce identical ordered output and identities; unsafe/mismatched inputs fail closed.

### Tests for User Story 1

- [ ] T008 [P] [US1] Add deterministic ordering + identity stability tests in `tests/test_public_corpus.py`
- [ ] T009 [P] [US1] Add censored/unavailable preservation tests in `tests/test_public_corpus.py`
- [ ] T010 [P] [US1] Add rejection-path tests for private/privileged/credential-bearing/malformed evidence in `tests/test_public_corpus.py`
- [ ] T011 [P] [US1] Add rejection-path tests for duplicate snapshots and invalid timestamps in `tests/test_public_corpus.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `normalize_public_corpus()` in `isoprax/public_corpus.py` using deterministic sort and identity hashing
- [ ] T013 [US1] Ensure preserved fields (`score_time`, `window_end`, `outcome_class`, `censor_reason`, `split`, `change_group_id`) are copied verbatim in `isoprax/public_corpus.py`
- [ ] T014 [US1] Add explicit evidence-only claim boundary (`public_corpus_evidence_only`) in `isoprax/public_corpus.py`
- [ ] T015 [US1] Wire exports for new public corpus types/functions in `isoprax/__init__.py`

**Checkpoint**: User Story 1 is independently testable and deterministic.

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Validate full repository quality gates and update feature docs for implementation traceability.

- [ ] T016 [P] Add implementation notes to `specs/012-corpus-materialization/quickstart.md`
- [ ] T017 Run focused tests `tests/test_public_corpus.py` and related module tests
- [ ] T018 Run repository coverage gate (`make coverage`) and ensure >=95% branch-aware thresholds
- [ ] T019 Run lint checks (`uv run ruff check .`) and resolve any feature-related diagnostics

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1**: Start immediately.
- **Phase 2**: Depends on Phase 1 completion.
- **Phase 3 (US1)**: Depends on Phase 2 completion.
- **Phase 4**: Depends on Phase 3 completion.

### User Story Dependencies

- **US1**: No dependency on additional stories; this is the MVP.

### Within User Story 1

- Write tests first (T008–T011), observe failures, then implement (T012–T015).
- Keep deterministic helpers reusable from foundational tasks.

### Parallel Opportunities

- T002, T003 can run in parallel after T001.
- T005 and T006 can run in parallel once dataclasses exist (T004).
- T008–T011 can run in parallel as they target separate scenarios in one file.

---

## Parallel Example: User Story 1

- Run T008 + T009 in parallel while drafting deterministic and preservation coverage.
- Run T010 + T011 in parallel to complete rejection-path matrix.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Setup and Foundational phases.
2. Implement and validate US1.
3. Run full quality gates and publish results.

### Incremental Delivery

1. Land deterministic core types and helpers.
2. Land normalization behavior with full rejection matrix.
3. Land exports and docs; then run full validation.

---

## Notes

- All tasks include concrete file paths.
- `[P]` indicates parallelizable work.
- US1 is the only story in this spec and is independently shippable.
