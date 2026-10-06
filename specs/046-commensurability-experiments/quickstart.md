# Quickstart: Commensurability Experiments

Run from the repository root:

```bash
uv run python -m isoprax.research_experiments --output docs/research/experimental-results.json
```

The runner uses fixed synthetic inputs, fixed sample sizes, and fixed bootstrap seeds. It does not access the network or load a private model. It fits the existing deterministic JEPA reference backend once.

Run focused checks:

```bash
uv run pytest -o addopts= tests/test_research_experiments.py tests/test_jepa.py tests/test_haskell_semantic_oracle.py -q
uv run ruff check isoprax/research_experiments.py tests/test_research_experiments.py
```

The result includes per-lane Benchmark A metrics, separate family/horizon target metrics, a declared same-target mixture control, and policy challenge-set counts. Do not read the different-family or different-horizon score ranks as a common risk ranking. Read [the evidence report](../../docs/research/experimental-evidence.md) before using the output.
