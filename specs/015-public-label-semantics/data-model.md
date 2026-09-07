# Data Model: Public Label-Semantics and Split-Sensitivity Evidence

## PublicLabelProcedure

- `split_strategy`: `temporal`, `random`, or `unknown`
- `split_reference`: stable description or empty when unknown
- `model_version`: stable identifier or `unknown`
- `adaptation_policy`: declared policy or `unknown`

## PublicLabelDefinition

- `source_id`, `published_version`, `retrieval_reference`, `license_status`,
  `snapshot_checksum`
- structured `OutcomeDefinition`
- `procedure`
- `retained_observations`: boolean
- `bridge_provenance`: stable reference or empty
- `available`: boolean

## PublicLabelComparison

- ordered source identifiers
- `status`: `direct`, `bridgeable`, `irreducible`, or `unavailable`
- sorted differing dimensions
- reason and `pooling_permitted` (always false for this evidence report)

## PublicLabelSemanticsReport

- sorted source records
- deterministic pairwise comparisons
- source statuses and reasons
- fixed claim boundary: public label semantics evidence only
