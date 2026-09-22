# Data Model: AI4I 2020 Structural Fixture

## `AI4I2020Expectations`

Pinned structural expectations for the source artifact: CSV checksum, row and
column counts, composite failure count, per-mode counts, multi-mode count, and
both directions of composite/mode disagreement. Tests for small local fixtures
must provide their own explicit checksum and expected summary; unpinned
verification is not a successful result.

## `AI4I2020VerificationReport`

Immutable report containing the supplied path, observed CSV checksum, parsed row
and column counts, composite and mode counts, multi-mode rows, mismatch counts,
named invariant errors, and a structural-only claim boundary. `verified` is true
only when parsing succeeds, all invariants pass, and the pinned expectations match.

## `AI4I2020OutcomeDefinitions`

The composite `Machine failure` and five mode labels are separate
`OutcomeDefinition` values. They share a declared manufacturing sensor-snapshot
observation process and current process-cycle window, but their event names differ.
The existing commensurability check therefore classifies comparisons as
irreducible and disallows pooled reasoning.

## CSV schema

- Identifiers: `UDI`, `Product ID`
- Product field: `Type` (`L`, `M`, or `H`)
- Sensor/process fields: air temperature, process temperature, rotational speed,
  torque, and tool wear
- Outcome fields: `Machine failure`, `TWF`, `HDF`, `PWF`, `OSF`, and `RNF`

The outcome fields are not prediction inputs. The verifier exposes the separation
so callers cannot mistake target components for non-leaking features.

## Invariants

- The canonical header has exactly 14 columns; a UTF-8 BOM is accepted only as a
  transport prefix, not as a different column name.
- Every UDI is a unique positive integer; product types and binary labels are
  restricted to their published domains.
- Numeric process fields parse as finite numbers.
- No row is dropped or relabeled after parsing begins.
- A source mismatch, malformed row, or structural disagreement makes the report
  unverified and records a reason.
- A verified report remains public synthetic structural evidence only; it does not
  provide replay lineage, temporal forecasting evidence, calibration evidence, or
  predictive efficacy.
