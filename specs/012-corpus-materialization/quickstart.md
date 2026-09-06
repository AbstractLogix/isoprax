# Quickstart: Reproducible Public Corpus Materialization

## Prerequisites

- Repository cloned locally.
- Python environment managed with `uv`.
- Feature branch checked out: `012-corpus-materialization`.

## Baseline validation

Run the existing quality gates before implementation updates:

```sh
uv run ruff check .
uv run pytest tests -q
uv run python examples/demo_cross_family.py
```

## Feature validation flow (after implementation)

1. Execute focused tests for materialization behavior:

```sh
uv run pytest tests/test_public_corpus.py -q
```

1. Execute full coverage gate:

```sh
make coverage
```

1. Confirm deterministic behavior manually in tests:
   - equivalent input permutations produce identical manifest hash/identity,
   - censored/unavailable inputs remain explicit in withheld inventory,
   - unsafe or mismatched evidence is rejected with no output substitution.

## Expected outcomes

- Public corpus materialization is deterministic and offline.
- Manifest outputs preserve original observed/censored semantics.
- Claim boundary remains evidence-only and does not imply conformance upgrade.

## References

- Spec: [spec.md](spec.md)
- Plan: [plan.md](plan.md)
- Data model: [data-model.md](data-model.md)
- Contract: [contracts/library-contract.md](contracts/library-contract.md)
