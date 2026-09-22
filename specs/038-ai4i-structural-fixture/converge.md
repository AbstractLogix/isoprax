# Convergence

The AI4I 2020 fixture implementation matches the feature contract. It verifies
an explicitly supplied local CSV against the pinned UCI checksum and structural
summary, accepts the published BOM, rejects malformed or changed input, and
preserves the 27 composite/mode discrepancies and 24 multi-mode rows without
repair. The composite and mode outcomes remain separate and non-poolable, and
the AI4I outcome definitions remain non-commensurable with the existing JIT
defect definition.

All feature tasks are checked. Focused verification passes with 16 tests and
100% branch-aware coverage for `isoprax.ai4i2020`. The live pinned UCI artifact
verified with 10,000 rows, 339 machine failures, and CSV SHA-256
`dc6630cd9b1f0f853922fad78a1b6436570d3f1ec863f1dd5c4340ac56bc8a8e`. The full
repository suite passes with 455 tests and one skip, 97.99% branch-aware
coverage, Ruff, pre-commit, JSON validation, and `git diff --check` clean.

This remains public synthetic structural/label-semantics evidence only. It does
not establish replay lineage, forecasting, predictive efficacy, or
Semantic/Full Conformance.

## Architecture review (2026-09-22)

The AI4I verifier now uses the shared chunked SHA-256 helper rather than
loading the complete CSV into memory. Dataset-specific parsing and reports stay
separate because their schemas and outcome evidence differ; their outcome
definitions still meet at Isoprax's existing `OutcomeDefinition` and
commensurability interface. Structural verification is deliberately not an
adapter into public-corpus admission: split, horizon, lineage, and evidence
requirements remain separate gates. The focused AI4I tests pass (16 tests), and
the full suite passes with 474 tests passed, 1 skipped, and 98.01% aggregate
branch-aware coverage.

After this follow-up, the full suite passes with 475 tests passed and one
skipped; AI4I remains at 100% branch-aware module coverage.
