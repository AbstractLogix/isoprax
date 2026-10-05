# Quickstart: Review the IsoPrax Scope Refinement

## Prerequisites

- Read the project constitution and the vendored IsoPrax v0.3 POC for normative claims.
- Use the research map at [`docs/research/README.md`](../../docs/research/README.md).

## Review sequence

1. Read the mission and current evidence summary in `README.md`.
2. Read [`project-scope-and-architecture.md`](../../docs/research/project-scope-and-architecture.md) for module dispositions and program boundaries.
3. Read [`evidence-commensurability.md`](../../docs/research/evidence-commensurability.md) and [`operation-specific-commensurability.md`](../../docs/research/operation-specific-commensurability.md) for the proposed research contract.
4. Read the benchmark, shared-model experiment, and falsification criteria before interpreting a future aggregate result.
5. Follow every literature link from its claim to the primary source. Keep analogies separate from established IsoPrax evidence.

## Reproduce the existing synthetic example

From the repository root, run:

```sh
uv run python examples/demo_cross_family.py
```

The demo includes an existing synthetic pooling-harm fixture. It does not run the proposed shared-model experiment and does not establish real-world efficacy or Semantic/Full Conformance.

## Review checks

- Confirm the README presents the mission before Stage 0/1/2 details.
- Confirm module dispositions cite existing files and do not move code.
- Confirm the benchmark declares its seven-day and ninety-day target windows separately.
- Confirm the experiment uses per-family results and treats shared model identity as insufficient evidence of shared outcome semantics.
- Confirm each proposed conclusion has an explicit falsifier and claim boundary.
