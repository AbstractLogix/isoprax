# Convergence: Replay Candidate Selection and Predeclaration

## Evidence obtained

- Candidate screening is deterministic and fail-fast in the required four-screen
  order, retaining a result for each submitted candidate.
- Screen 3 derives its frozen floor from exactly 200 reference build-success
  observations, rounds the fifth-percentile observation down to two decimals,
  caps it at 0.90, requires a distinct reference project, and rejects clustered
  failures.
- Screen 4 checks each sampled commit's prediction-time field names against the
  supplied allowlist.
- Predeclaration validation hashes the complete artifact, requires an external
  anchor explicitly identified as independent of the project repository and
  clock, and executes `git merge-base --is-ancestor` for every corpus-data
  commit. It rejects corpus commits timestamped before the predeclaration.
- The focused provenance test creates real Git history and verifies the executed
  ancestry path; it also verifies the timestamp rejection path.
- `uv run pytest tests -q` passed: 47 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check` passed for the feature-touched modules and test.

## Scope and remaining gates

- This is evidence-boundary infrastructure only. It does not select a real
  candidate, collect a corpus, establish a public external anchor, or make a
  Semantic or Full Conformance claim.
- A repository-wide format check still identifies pre-existing formatting drift
  in `isoprax/corpus_manifest.py`, `isoprax/replay_constraints.py`, and
  `tests/test_stage1_admission.py`; those unrelated files were not changed by
  this feature.
