# Quickstart: Strongly Typed Python Semantic Core

From the repository root:

```bash
uv sync --group dev
uv run mypy
uv run pytest -q tests/test_commensurability.py tests/test_semantic_types.py tests/test_evaluation.py
```

The mypy configuration checks the declared semantic files in strict mode. The focused tests cover normalized fields, legacy input forms, malformed-input rejection, commensurability evidence, ID-plus-definition-content binding, shared calibration-policy binding, exact sample binding, direct observation parameter invariants, and the Structural conformance ceiling. The positive type fixture must pass; each expected-failure fixture must fail for its named type mismatch. Typed pooled ECE takes its bin count from the authorization policy. `cross_family_report.pooled_ece` remains a diagnostic output, not an authorization token.

Run the repository CI-equivalent checks before delivery:

```bash
uv lock --check
uv run ruff check .
uv run pytest tests -q
uv run python examples/demo_cross_family.py
```

The semantic oracle is CI-only and runs when the semantic contract, implementation, or shared fixtures change. To run it locally where GHC 9.14.1 and Cabal 3.16.1.0 are installed:

```bash
cd haskell/semantic-oracle
cabal build all --enable-tests
cabal test all --enable-tests
bash test/compile-fail.sh
```

The Python runtime never invokes the oracle. `specs/042-haskell-semantics-kernel/assessment.md` records the broader experiment and the reason for retaining this smaller CI boundary.
