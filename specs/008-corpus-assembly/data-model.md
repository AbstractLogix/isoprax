# Data Model: Replay Corpus Assembly

## CorpusAssemblyProfile

Frozen profile for one candidate corpus: expected system, canonical chronological split definitions, allowed and forbidden prediction fields, frozen horizon rule, threshold identifier, release scope, and publishable artifact references.

## ReplayCaptureInput

One replay capture record plus predeclared prediction fields and one observed-at timestamp for every field. Its capture must have the replay-observation evidence claim scope.

## CandidateCorpusRow

An existing Stage 1 CorpusRow with deterministic row ID, source system, capture-derived change/deployment/observation identities, score time, outcome/censor state, score-time fields, frozen split, and change_group_id equal to the source change.

## AssemblyRejection

A deterministic input identity, failed requirement, safe reason, and no raw restricted payload.

## CorpusAssemblyReport

Profile identity, ordered accepted rows, ordered rejections, counts by outcome class, manifest input, and corpus-assembly-evidence-only claim scope.

## State Mapping

```text
valid capture + matching frozen profile + eligible fields/split/follow-up
  -> accepted candidate row
missing/conflicting lineage, foreign system, duplicate change, profile mismatch,
unsafe field, invalid split/follow-up, or restricted release scope
  -> explicit rejection
censored capture
  -> accepted censored candidate row with unchanged reason
```
