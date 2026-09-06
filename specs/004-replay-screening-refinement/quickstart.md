# Quickstart: Replay Screening Refinement

1. Supply estimated recent buildable-window commits, a positive-event rate, legal instruments, replay-readiness evidence, and sampled metadata fields.
2. Call `screen_early_candidate()` with 002's adequacy floor and feature allowlist.
3. Treat eligibility as early only; the record must state measured qualification is deferred.
4. Run `uv run pytest tests/test_replay_selection.py -q`.
