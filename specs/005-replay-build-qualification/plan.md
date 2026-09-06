# Implementation Plan: Hermetic Replay Build Qualification

**Branch**: `005-replay-build-qualification` | **Date**: 2026-09-05 | **Spec**: [spec.md](spec.md)

## Summary

Add a deterministic library module that validates and hashes prepared samples, performs no direct container work, invokes an injected runner only after fail-closed preflight, and reduces all row results into an evidence-bounded qualification report.

## Technical Context

**Language/Version**: Python >=3.10,<3.15
**Dependencies**: standard library and existing Isoprax records
**Storage**: frozen dataclasses and canonical JSON hashes
**Testing**: pytest focused conformance tests
**Target**: offline/local library
**Constraints**: no network, Docker client, candidate selection, or corpus collection.

## Constitution Check

- Specification Authority: pass — predeclared evidence is required before execution.
- Honest Conformance: pass — outputs are build evidence only.
- Contract-First Testing: pass — each preflight, classification, and incomplete-report path is tested.
- Deterministic Core: pass — injected effects and canonical reduction.
- Minimal Reference Scope: pass — no corpus or model functionality.

## Source Impact

```text
isoprax/build_qualification.py
isoprax/__init__.py
tests/test_build_qualification.py
```
