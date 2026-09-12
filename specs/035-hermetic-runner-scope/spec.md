# Feature Specification: Explicit Hermetic Runner Scope

**Feature Branch**: `035-hermetic-runner-scope`

## Summary

Make the reference implementation's hermetic-runner boundary explicit. The
module validates evidence from an injected external backend; it does not
provision or invoke Docker, Podman, or another container engine.

## Acceptance scenarios

1. The module documentation states that runner invocation is supplied by the
   integrating environment.
2. Execution evidence remains fail-closed when the injected backend reports
   missing or mismatched controls.
3. Documentation does not describe injected-fixture evidence as proof that the
   reference implementation itself provides hermetic execution.

## Claim boundary

This clarifies scope and prevents a module name from implying a capability that
is not implemented. It does not add a container runtime or prove isolation.
