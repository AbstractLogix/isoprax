# Quickstart: Retrieval and Interpretation Dependence

This feature records the research note, a pre-registered synthetic benchmark, its runner, and the results report.

## Review the current artifacts

1. Read [the research note](../../docs/research/retrieval-selection-dependence.md) for the paper scope, prior repository evidence, open hypotheses, and recommendation.
2. Read [the benchmark protocol](../../docs/research/retrieval-selection-dependence-benchmark.md) for conditions A-D, case design, budgets, metrics, and falsification.
3. Read [the benchmark data model](data-model.md) before interpreting the records.
4. Read the [two-run synthetic pilot report](../../docs/research/retrieval-selection-dependence-results.md) before using its results. The case set and selector traces matched; interpretation results did not.
5. Read the [Bouleusis measurement-validity assessment](../../docs/research/bouleusis-retrieval-measurement-validity.md)
   and its [prospective iterative-retrieval protocol](../../docs/research/iterative-retrieval-preregistration.md)
   before planning any follow-up run. The supplied sweep has one independent
   bug; the next protocol requires multiple distinct bugs.

## Run the synthetic benchmark

1. Start the local Ollama service.
2. Run `uv run python -m scripts.retrieval_dependence_experiment --output /tmp/retrieval-run-1.json`.
3. Repeat with `--output /tmp/retrieval-run-2.json`.
4. Finalize both runs with `uv run python -m scripts.retrieval_dependence_experiment --finalize-runs /tmp/retrieval-run-1.json /tmp/retrieval-run-2.json --output docs/research/retrieval-selection-dependence-results.json.gz --report docs/research/retrieval-selection-dependence-results.md`.
5. Use only the model revisions and analysis frozen in [the preregistration](preregistration.json).

The runner fails if the local model digests do not match. It reads and writes gzip-compressed JSON when the path ends in `.gz`; compression is deterministic. Results are synthetic. The prompted-selector proxy does not reproduce UNREAL or test hidden-state retrieval. Do not send a policy to Semadmit based on this pilot alone.

## Run the model-role comparison

1. Check [model-role-preregistration.json](model-role-preregistration.json). Do not run scored calls while its status is `draft` or any model digest is null.
2. Run `uv run python -m scripts.model_role_experiment --output docs/research/model-role-run-1.json`.
3. Repeat with `--output docs/research/model-role-run-2.json`.
4. Compare both with `uv run python -m scripts.model_role_experiment --finalize-runs docs/research/model-role-run-1.json docs/research/model-role-run-2.json --output docs/research/model-role-commensurability-results.json`.

The model-role runner uses each model's declared output type. It fits score mappings on development cases and evaluates them on held-out cases. The only pooled metrics are the mixture estimands and weights in the preregistration. These synthetic findings do not establish general calibration, model independence, score interchangeability, or runtime enforcement.

## Review the supplied Bouleusis sweep

The report reanalyzes the raw JSONL from the Bouleusis checkout and records its SHA-256. It distinguishes reproduced counts from the supplied summary's placement of full context alongside the 540-byte condition; raw records show it as a separate unbounded 660-byte reference. Do not count seed or order changes around one bug as independent problems. The iterative protocol is prospective and remains a draft until its task set, revisions, and margins are frozen.

To repeat the raw-record analysis, run `uv run python -m scripts.reanalyze_bouleusis_sweep --input /path/to/bouleusis/docs/experiments/evidence-selection-sweep-2026-10-08.jsonl --output docs/research/bouleusis-retrieval-sweep-reanalysis.json`.
