# Feature Specification: Release Metadata Integrity

**Feature Branch**: `032-release-metadata`

## Summary

Publish the accumulated hardening work as version `0.2.0` with a descriptive
changelog entry, and make tagged releases fail when the tag, package version,
or release notes disagree.

## Acceptance scenarios

1. `pyproject.toml` and `isoprax.__version__` report `0.2.0`.
2. `CHANGELOG.md` contains a dated `0.2.0` entry naming the mechanisms and
   constraints changed.
3. The release metadata command accepts `v0.2.0` and rejects mismatched tags,
   missing entries, and empty/generic release notes.

## Claim boundary

This validates release bookkeeping only. It does not prove the contents of a
release passed external CI, deployment, or independent review.
