# Corpus Assembly Contract

## Input

Assembly receives one frozen CorpusAssemblyProfile and an ordered or unordered collection of ReplayCaptureInput values.

## Required behavior

- Validate the profile before reduction: one expected system, canonical non-overlapping splits, frozen horizon and threshold metadata, non-empty release scope, and publishable artifact references.
- Accept only replay-observation evidence records with complete immutable lineage.
- Derive one row per change, preserve capture outcome/censor reason, and set change_group_id to the capture change.
- Assign rows from score time to a frozen split; observed outcomes require full capture follow-up inside that split.
- Reject unknown, forbidden, missing-time, or post-score-time fields.
- Return explicit rejections for all invalid inputs and deterministic ordering for accepted and rejected results.
- Never emit an admission, performance, conformance, or automatic-action decision.

## Output

The report contains CorpusRow-compatible accepted rows, safe rejections, class counts, a deterministic profile identity, and manifest metadata suitable for later use by existing helpers.
