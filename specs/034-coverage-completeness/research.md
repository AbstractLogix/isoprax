# Research and Decisions

## Decision: derive expectations from source

Iterating only the report cannot detect an unimported, renamed, or newly added
module. The source tree is the authoritative expected set; the report remains
the evidence being checked.

## Decision: keep the existing scope

The gate covers flat production modules under `isoprax` and continues to omit
`__init__.py`, matching the current CI contract without adding exclusions for
missing modules.
