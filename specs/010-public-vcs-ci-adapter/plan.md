# Implementation Plan: Public VCS/CI Evidence Adapter

**Branch**: `010-public-vcs-ci-adapter` | **Date**: 2026-09-06

## Summary

Add one offline normalizer that turns supplied public source/CI metadata into
deterministic safe records. It neither fetches nor executes evidence and
distinguishes unavailable public evidence from unsafe input.

## Technical Context

Python 3.10–3.14, standard library only, pytest/coverage validation, no network
I/O, credentials, payload retention, qualification, admission, or conformance
claim.

## Constitution Check

Pass: deterministic reduction, focused rejection tests, and an immutable
candidate/build-preparation-only claim boundary. No effects or dependencies.

## Design

`PublicEvidenceSnapshot` contains a system ID, immutable revision, public
source/CI references, observed timestamp, and provenance flags.
`normalize_public_evidence()` sorts snapshots deterministically and returns
safe `PublicEvidenceRecord` values. Missing public CI evidence is unavailable;
private, credential-bearing, mutable, malformed, or contradictory evidence is
rejected.

## Project Structure

```text
isoprax/public_evidence.py
tests/test_public_evidence.py
specs/010-public-vcs-ci-adapter/
```
