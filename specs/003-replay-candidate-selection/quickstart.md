# Quickstart: Replay Candidate Selection and Predeclaration

1. Create a candidate dictionary or dataclass-like object with the required screen inputs.
2. Call `screen_candidate()` or `screen_candidates()` to obtain a deterministic pass/fail record for each candidate.
3. Build a `PredeclarationArtifact` with the required fields: soak rule, thresholds, censoring rule, adequacy floor, and ablation plan.
4. Call `hash_predeclaration_artifact()` to compute the artifact hash and `evaluate_predeclaration_provenance()` to validate commit ancestry and external anchors.
5. Use `record_exclusion_entry()` to create structural or commensurability exclusions without pending or deferral language.
6. Run the focused tests in `tests/test_replay_selection.py` and keep the implementation offline by design.
