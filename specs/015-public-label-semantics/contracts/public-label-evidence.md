# Public Label Evidence Contract

`build_public_label_semantics_report` accepts a finite sequence of supplied
`PublicLabelDefinition` records and returns a deterministic report.

The function MUST:

- reject duplicate source identifiers and negative counts;
- preserve unknown split/model/adaptation metadata;
- classify comparisons from structured definitions and explicit bridge evidence;
- return unavailable comparisons when either source is blocked;
- set `pooling_permitted` to false for every comparison;
- retain the public-label-only claim boundary.

No function in this contract performs network I/O or treats a reproduced label
comparison as Semantic/Full Conformance or predictive efficacy.
