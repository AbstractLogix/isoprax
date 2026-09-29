# Typed Evidence Contract

## Purpose

The typed evidence API provides a statically checked route for code that combines declared outcome families. Dynamic input must still pass through runtime validation and identity binding.

## Construction

1. Parse/construct each `OutcomeDefinition`; malformed raw values raise a documented `ValueError` or `TypeError` and yield no validated definition.
2. Call the commensurability evidence factory with the left and right definitions and their caller-defined marker types. Irreducible and bridgeable results raise `IncommensurableError`; retained observations do not substitute for outcomes re-derived under a shared definition. Evidence records each definition's normalized semantic-content digest as well as its ID.
3. Call the calibration evidence factory with each definition, score/outcome vectors, and optional `min_events`, `n_bins`, and `max_ece`. Failed calibration cannot yield `CalibrationEvidence`; passing evidence binds the definition ID, semantic-content digest, exact normalized sample digest, and a `CalibrationPolicy` digest.
4. Call pooled authorization with commensurability evidence and left/right calibration evidence. Static marker mismatches are type errors; concrete ID, semantic-content, or orientation mismatches and unequal calibration policies raise `ValueError`.
5. Call pooled evaluation with the authorized samples. A vector whose digest differs from calibration evidence raises `ValueError`; evaluation uses the authorized policy's `n_bins` and accepts no replacement bin count.

## Independent CI oracle

The Haskell oracle consumes shared fixtures and independently derives normalized definition digests, calibration sample and policy digests, direct commensurability, calibration eligibility, pooled authorization, and policy-bound pooled ECE. Its evidence constructors are opaque; generated properties and compile-fail examples protect the API boundary. CI runs the oracle only when semantic implementation, fixture, contract, or oracle paths change. The Python runtime does not invoke or depend on Haskell.

## Guarantees and limits

- A checked call cannot omit a required evidence value.
- Generic marker parameters reject known left/right evidence mixups during static checking.
- Factories bind evidence to concrete IDs and normalized definition semantics at runtime; this is authoritative for dynamically loaded records.
- Pooled authorization binds the exact score/outcome samples and shared calibration policy. This does not independently prove the samples' external provenance.
- `cross_family_report` remains a diagnostic facade: its `pooled_ece` is not an authorization result, may be present for uncalibrated but directly commensurable inputs, and is withheld for non-commensurable inputs.
- Existing `check_commensurable`, `require_commensurable`, and report output fields remain compatible.
- Python callers can intentionally bypass static guarantees with untyped code, `Any`, or casts. No annotation is represented as runtime proof by itself.
- Stage 0 conformance remains Structural.
