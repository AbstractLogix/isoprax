# Research and Decisions

## Decision: validate at tag time

Every feature branch need not invent a release number, but a published tag
must not silently reuse a stale package version or generic notes. The validator
is therefore attached to the release event and remains usable locally.

## Decision: retain a small version bump

The merged work is backward-compatible hardening and evidence-contract work,
so `0.2.0` records a substantive minor release without implying a conformance
class upgrade.
