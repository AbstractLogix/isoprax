# Typed Evidence Contract

## Purpose

The typed evidence API provides a statically checked route for code that combines declared outcome families. Dynamic input must still pass through runtime validation and identity binding.

## Construction

1. Parse/construct each `OutcomeDefinition`; malformed raw values raise a documented `ValueError` or `TypeError` and yield no validated definition.
2. Call the commensurability evidence factory with the left and right definitions and their caller-defined marker types. Irreducible and bridgeable results raise `IncommensurableError`; retained observations do not substitute for outcomes re-derived under a shared definition.
3. Call the calibration evidence factory with each definition and score/outcome vectors. Failed calibration cannot yield `CalibrationEvidence`; passing evidence binds the exact normalized sample digest.
4. Call pooled authorization with commensurability evidence and left/right calibration evidence. Static marker mismatches are type errors; concrete ID or orientation mismatches raise `ValueError`.
5. Call pooled evaluation with the authorized samples. A vector whose digest differs from calibration evidence raises `ValueError`.

## Guarantees and limits

- A checked call cannot omit a required evidence value.
- Generic marker parameters reject known left/right evidence mixups during static checking.
- Factories bind evidence to concrete IDs at runtime; this is authoritative for dynamically loaded records.
- Pooled authorization binds the exact score/outcome samples. This does not independently prove the samples' external provenance.
- Existing `check_commensurable`, `require_commensurable`, and report output values remain compatible.
- Python callers can intentionally bypass static guarantees with untyped code, `Any`, or casts. No annotation is represented as runtime proof by itself.
- Stage 0 conformance remains Structural.
