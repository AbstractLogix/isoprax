# Quickstart: Stage 1 Per-Family Evaluation

Run from repository root.

## 1) Focused contract tests

```sh
uv run pytest tests/test_per_family_evaluation.py -q
```

## 2) Full lint and tests

```sh
make lint
make test
```

## 3) Coverage gate

```sh
make coverage
```

## Expected outcomes

- Per-family evaluation returns deterministic identities for equivalent input.
- Non-admission or rule violations fail closed.
- Missing required evidence is explicit and produces `inconclusive`.
- Claim boundary remains below Semantic/Full conformance.
