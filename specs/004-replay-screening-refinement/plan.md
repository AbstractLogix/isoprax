# Implementation Plan: Replay Screening Refinement

**Branch**: `004-replay-screening-refinement` | **Date**: 2026-09-05 | **Spec**: [spec.md](spec.md)

## Summary

Add an early-only deterministic API: estimated buildable-window supply, governing source-build terms, replay-readiness evidence, and metadata. This refinement does not execute or interpret builds; it adds `screen_early_candidate()` while tightening 003 screening inputs (reference build sample + per-commit prediction-field samples) rather than introducing a replay environment.

## Technical Context

**Language/Version**: Python >=3.10,<3.15
**Dependencies**: standard library and `isoprax.replay_selection`
**Storage**: frozen dataclass records
**Testing**: pytest focused conformance tests
**Target**: offline/local library
**Constraints**: deterministic, no network/replay/corpus collection; keep 003 screen semantics and record shapes while evolving required inputs.

## Constitution Check

- Specification Authority: pass — the early-screen contract is explicit.
- Honest Conformance: pass — early eligibility is distinguished from measurement.
- Contract-First Testing: pass — rejection and deferred state are tested.
- Deterministic Core: pass — caller-supplied records only.
- Minimal Reference Scope: pass — no execution environment is added.

## Project Structure

```text
isoprax/replay_selection.py
tests/test_replay_selection.py
specs/004-replay-screening-refinement/{spec,plan,data-model,quickstart,tasks}.md
```
