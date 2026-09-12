# Feature Specification: Complete Module Coverage Gate

**Feature Branch**: `034-coverage-completeness`

## Summary

Make the per-module coverage gate compare the production source tree with the
coverage report. A module absent from the report must fail the gate instead of
being silently skipped.

## Acceptance scenarios

1. Every `.py` production module except `__init__.py` is expected in the
   coverage report.
2. A missing module entry fails with an explicit path and reason.
3. Reported modules still fail when their branch-aware percentage is below the
   configured minimum.

## Claim boundary

This detects coverage-report blind spots. Passing the gate is not proof of
behavioral completeness or correctness.
