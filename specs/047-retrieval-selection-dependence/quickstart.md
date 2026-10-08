# Quickstart: Retrieval and Interpretation Dependence

This feature records the research note, a pre-registered synthetic benchmark, its runner, and the results report.

## Review the current artifacts

1. Read [the research note](../../docs/research/retrieval-selection-dependence.md) for the paper scope, prior repository evidence, open hypotheses, and recommendation.
2. Read [the benchmark protocol](../../docs/research/retrieval-selection-dependence-benchmark.md) for conditions A-D, case design, budgets, metrics, and falsification.
3. Read [the benchmark data model](data-model.md) before interpreting the records.

## Run the synthetic benchmark

1. Start the local Ollama service.
2. Run `uv run python -m scripts.retrieval_dependence_experiment --output /tmp/retrieval-run-1.json`.
3. Repeat with `--output /tmp/retrieval-run-2.json`.
4. Finalize both runs with `uv run python -m scripts.retrieval_dependence_experiment --finalize-runs /tmp/retrieval-run-1.json /tmp/retrieval-run-2.json --output docs/research/retrieval-selection-dependence-results.json --report docs/research/retrieval-selection-dependence-results.md`.
5. Use only the model revisions and analysis frozen in [the preregistration](preregistration.json).

The runner fails if the local model digests do not match. Results are synthetic. The prompted-selector proxy does not reproduce UNREAL or test hidden-state retrieval. Do not send a policy to Semadmit based on this pilot alone.
