# Implementation Plan: Admission Timestamp Integrity

Reuse the event model's UTC validation rule in `admission._parse_iso`, then
catch timestamp parsing failures within `_gate_split_and_followup` so malformed
rows are reported as admission evidence failures. Add direct constructor and
end-to-end gate regression tests.
