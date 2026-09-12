# Research and Decisions

## Decision: reuse existing parameter names and defaults

The cross-family function delegates to `check_calibration_conformance`, so
matching its names avoids a second configuration vocabulary and keeps default
behavior unchanged.

## Decision: report configuration alongside diagnostics

A threshold that cannot be reconstructed from the report weakens an otherwise
auditable conformance result. The selected values are therefore part of the
report object and rendered output.
