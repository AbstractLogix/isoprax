# Implementation Plan: Complete Stage 1 Public-Data Validation

**Branch**: `codex/016-stage1-public-validation` | **Date**: 2026-09-07 | **Spec**: [spec.md](spec.md)

## Summary

Add a deterministic offline adapter/report command for ApacheJIT's Apache
Ignite project and Google Cluster Trace v1. The command reads caller-supplied
public files, computes source identities, constructs `CorpusRow` records with
frozen split and predeclared outcome semantics, runs existing admission and
per-family evaluation, and writes only aggregate evidence.

## Technical Context

**Language/Version**: Python 3.10–3.14

**Dependencies**: Existing standard library, NumPy, SciPy, scikit-learn, and Isoprax contracts

**Storage**: External source files supplied by the operator; checked-in JSON evidence and predeclaration

**Testing**: Small in-memory adapter fixtures, live public-source run, full pytest/coverage, Ruff

**Constraints**: No network in core execution, no raw dataset commit, no family pooling, no semantic claim

## Constitution Check

| Principle | Design response | Result |
| --- | --- | --- |
| Specification Authority | Uses existing Stage 1 admission and per-family contracts. | Pass |
| Honest Conformance | Publishes separate evidence and preserves uncalibrated results. | Pass |
| Contract-First Testing | Source, split, leakage, determinism, and report paths are tested. | Pass |
| Deterministic Core | Source parsing and reduction are deterministic for fixed bytes. | Pass |
| Minimal Reference Scope | Adds two narrow public-file adapters and no online service. | Pass |

## Project Structure

```text
isoprax/stage1_public_validation.py  # adapters and report reducer
scripts/run_stage1_public_validation.py # CLI wrapper
docs/stage1/                         # predeclaration and generated report
tests/test_stage1_public_validation.py
```

## Design

- ApacheJIT: select `apache/ignite`; use commit metrics available at commit
  time, fit isotonic calibration on the frozen calibration-fit period, and
  evaluate the SZZ-style `buggy` label per family.
- Google Trace v1: aggregate task rows by `ParentID`; score from the first
  task observation, label a later resource-threshold crossing, and retain only
  jobs with a later observation. This is an operational threshold outcome, not
  a claim about scheduler failure labels.
- Both adapters use the existing `AdmissionProfile`, `evaluate_admission`,
  `PerFamilyEvaluationProfile`, and `evaluate_per_family` paths.
- The report stores only metadata and aggregate results, not raw prediction
  fields or source rows.
