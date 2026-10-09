# Data Model: Research Paper Evidence Integrity

## Claim

Each claim has: `id`, exact wording, category, assumptions, source repositories and commits, input artifact paths and SHA-256 hashes, protocol path and digest, result or counterexample, uncertainty, threats to validity, qualification status, and manuscript location.

## Artifact

Each artifact has: repository, immutable commit or source version, relative path, original-byte SHA-256, optional compressed-package path and digest, record count or row structure when known, and access status.

## Protocol

Each protocol has: command, source path, source digest, sampling unit, metric definitions, seeds and resample count where applicable, and expected outputs.

## Evidence Category

Allowed values: `definition`, `repository-result`, `synthetic-finding`, `literature-supported`, `external-validation`, `hypothesis`, and `unavailable`.

## Qualification Status

Allowed values: `supported-within-scope`, `reproduced-not-replicated`, `candidate-contribution`, `descriptive-only`, `not-supported`, `unresolved`, and `excluded-from-main-paper`.

## Counterexample

Each counterexample has: case ID, targeted claim, declared inputs, expected operation, observed checker/policy result, whether the result challenges permission or refusal, and interpretation limit.
