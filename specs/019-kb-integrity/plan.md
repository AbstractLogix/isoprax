# Implementation Plan: Durable Knowledge-Base Integrity

## Design

Harden `SQLiteKB` at the persistence boundary. New schemas include a unique
signal identity constraint. Existing schemas are checked for duplicate signal
identities before the nullable-score migration and index creation; any
violation raises a domain error. Event and Outcome Definition writes compare
the persisted canonical payload before accepting an idempotent retry or
rejecting a conflicting replacement.

## Validation

- Focused KB regression tests cover idempotent and conflicting writes.
- A migration test covers legacy duplicate signal rows.
- Full pytest, coverage, Ruff, and demo checks must pass.
