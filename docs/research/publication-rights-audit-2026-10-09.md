# Publication rights and artifact-scope audit — 2026-10-09

## Release scope

The repository owner authorized public release of four selected original Bouleusis research records. The exact paths, source commit, source hashes, release license, and authorization date are recorded in [`manifest.json`](../experiments/bouleusis-2026-10-08-raw/manifest.json) and its [README](../experiments/bouleusis-2026-10-08-raw/README.md). CC BY 4.0 applies only to those four lossless data snapshots.

The authorization does not cover Bouleusis source code, Bouleusis assurance source files, model weights, or third-party corpora. The source repository's `NOASSERTION` metadata remains preserved; it is not replaced by the separate, narrow release permission. No private source code, model weights, or original training corpora are included in the selected-data package.

## Model-role records

The companion study uses outputs from [Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B), [Gemma 4 E4B](https://huggingface.co/google/gemma-4-E4B), [Qwen2.5-Coder-7B](https://huggingface.co/Qwen/Qwen2.5-Coder-7B), [EmbeddingGemma 2](https://huggingface.co/google/embeddinggemma-2), [Tev1-4B](https://huggingface.co/togethercomputer/Tev1-4B-experimental), and [Granite Guardian 4.1 8B](https://huggingface.co/ibm-granite/granite-guardian-4.1-8b). The checked Qwen, Gemma 4, EmbeddingGemma 2, and Granite Guardian model cards identify Apache 2.0 terms. Those model licenses are not applied to Tev1 or to the experiment records by inference.

The [Tev1 project](https://github.com/togethercomputer/tev1) states that its code and original documentation are MIT licensed, while third-party datasets and model weights have separate terms. The [Tev1 model card](https://huggingface.co/togethercomputer/Tev1-4B-experimental) states that the release license for the fine-tuned weights is being finalized. The local Ollama package used for the experiment displayed Apache 2.0 text for its `tev1:4b` tag. The observed local manifest digest and limits are recorded in [the runtime license audit](../experiments/model-runtime/tev1-license-audit-2026-10-09.json). That local file does not settle the upstream fine-tune terms or provide a separate license for model-generated outputs.

The model-role inputs are authored synthetic cases. The recorded runs contain generated scores, labels, and short model responses; they do not package model weights or Tev1 training data. This review did not find an explicit output-reuse license for the Tev1 records. Therefore:

- the Bouleusis CC BY 4.0 grant must not be applied to model-role records;
- the results must not be described as licensed under a model-weight license without a separate basis;
- no blanket reuse license is asserted for the frozen model-role output files;
- public deposit of those raw output files remains blocked until the release basis is confirmed or the files are excluded.

The main manuscript does not rely on the six-role model study for its Benchmark A or policy-challenge claims. The model-role study remains companion research and is not evidence of real-world JIT/AIOps performance.

## Secret, privacy, and third-party review

The integrity runner scans selected JSONL snapshots and model-role run files for common credential patterns, email addresses, URLs, and local home-directory paths. This is a limited pattern scan, not a rights opinion. It cannot find every secret, personal identifier, or copied passage.

The packaged Bouleusis files are synthetic experiment records. The model-role case prompts and labels are authored synthetic fixtures. The package contains no model weights or third-party training corpora. The model output records need a separate, explicit release decision as stated above. No third-party paper text, proprietary corpus, or model card text is copied into the data files by this audit.

## Decision

The selected Bouleusis raw-data release has an explicit, narrow authorization and license. The broader public replication package is **not ready for permanent public deposit** while it includes the frozen model-role outputs without a resolved reuse basis. A clean-checkout computational pass does not resolve this distribution question.
