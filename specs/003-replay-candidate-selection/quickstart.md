# Quickstart: Replay Candidate Selection and Predeclaration

1. Create a candidate dictionary or dataclass-like object with the required screen inputs, including sampled build outcomes and prediction-time field names for every sampled commit.
2. Call `screen_candidate()` or `screen_candidates()` with 002's adequacy floor, its prediction-time field allowlist, and exactly 200 build-success rates from an unrelated stable reference project. The derived Screen 3 floor is frozen in the returned record.
3. Build a `PredeclarationArtifact` with the required fields: soak rule, thresholds, censoring rule, adequacy floor, and ablation plan.
4. Call `hash_predeclaration_artifact()` to compute the artifact hash and `evaluate_predeclaration_provenance()` with a repository path to execute Git ancestry checks and validate an independent external anchor.
5. Use `record_exclusion_entry()` to create structural or commensurability exclusions without pending or deferral language.
6. Run the focused tests in `tests/test_replay_selection.py` and keep the implementation offline by design.
