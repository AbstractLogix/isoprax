# EmbeddingGemma Runtime Qualification and Proposed Amendment

**Status:** Proposed amendment only. It is not frozen or effective. No scored model-role calls were made.

**Evidence class:** Runtime and artifact inspection. No retrieval outcomes were scored.

## Result

The requested Ollama condition remains unavailable in the selected Linux runtime. Google documents a Transformers/SentenceTransformers path for its pinned upstream checkpoint, but that runner has not been executed here and would be a different experimental condition. The source relationship is strong enough to justify a proposed alternate condition; it does not establish output equivalence with either Ollama tag. The model-role study remains blocked until the amendment, software environment, and complete six-model preregistration are frozen.

## Runtime and artifact record

The active host is WSL2 on x86_64 with an AMD Ryzen 9 5900X, 31 GiB system memory, and Ollama 0.40.1. `ollama list` contains no EmbeddingGemma identity. The prior load attempts for `embeddinggemma-2:740m` and `embeddinggemma-2:740m-bf16` returned an MLX-unavailable error. There is no macOS/MLX host attached to this task. The M1 8 GB option was not run; its peak memory and replay behavior are unknown.

The raw Ollama registry manifests were fetched on 2026-10-08 and are preserved losslessly as gzip-compressed HTTP response bodies under `docs/experiments/model-runtime/`. Decompress each `.json.gz` file to verify the raw manifest SHA-256 below.

| Registry identity | Manifest SHA-256 | Model config | Tensor layers and aggregate bytes |
|---|---|---|---:|
| `embeddinggemma-2:740m` | `969600645b5240cbf78f46456c819f38bea9f59c3e34a2993a0ae54334e3db04` ([manifest](../experiments/model-runtime/ollama-embeddinggemma-2-740m-manifest.json.gz)) | NVFP4 quantization config, SHA-256 `f440a5e27d63cfcafc24f923dd9ea12d9da465c02a967cab017dc89faeef5c57` ([config](../experiments/model-runtime/ollama-embeddinggemma-2-740m-model-config.json.gz)) | 1,376; 1,293,022,548 |
| `embeddinggemma-2:740m-bf16` | `54d809644cd8a4e4547a6cdcf165e91b13d89e86d5c30fc4fe2f147f0b2f82f1` ([manifest](../experiments/model-runtime/ollama-embeddinggemma-2-740m-bf16-manifest.json.gz)) | BF16 config, SHA-256 `0673b3292afd69e1dc67bd113debeaa5ce82b36d9834c2071e552156e052e92b` ([config](../experiments/model-runtime/ollama-embeddinggemma-2-740m-bf16-model-config.json.gz)) | 1,376; 1,488,913,304 |

Each manifest contains the per-layer digests. The small model-config blobs are also preserved and their hashes match their registry layer digests. The two tags share the same tokenizer JSON digest, `4d777ef5bdc1aa36227abdfb77c3e49e7b9c892d16e1b6bda41c393504828be4`.

The proposed Linux alternative is the official Google checkpoint `google/embeddinggemma-2` at Hugging Face revision `914f7f89142e33e77833254d9c9b90c3cef7303b`. Its `model.safetensors` SHA-256 is `197a32965d4b1105faf060417baa899e193fb73cd401f42ec9295234d5553d79` (1,488,915,288 bytes). Its tokenizer JSON has the same SHA-256 listed above. The pinned identity record is [here](../experiments/model-runtime/google-embeddinggemma-2-hf-checkpoint-identity.json), SHA-256 `7d923c0c4a76ddf7bf8810000d6c4295383a7f08c234bf55de15d7d51b1e4740`. The BF16 Ollama config parses identically to the pinned Google `config.json`. The artifact packaging is different: Ollama exposes per-tensor layers, while the source checkpoint is one safetensors file. Aggregate size and config agreement do not prove tensor-by-tensor or output equivalence. No embedding outputs were compared.

## Proposed alternate condition

If approved before any scored replacement-model output, replace only the EmbeddingGemma runner condition with:

- **Checkpoint:** `google/embeddinggemma-2`, revision `914f7f89142e33e77833254d9c9b90c3cef7303b`, with the weight and tokenizer hashes above.
- **Runner:** SentenceTransformers/Transformers with PyTorch on Linux CPU, using a dependency lock recorded before execution.
- **Precision:** float32 on CPU, following Google's published guidance. Do not use float16.
- **Task input:** `task: search result | query: ...` for each query and `title: none | text: ...` for each untitled evidence item.
- **Output:** full 768-dimensional embedding; L2 normalization enabled before cosine similarity.
- **Context cap:** 8,192 tokens. The pinned config reports `max_position_embeddings=262144`, while the Google model card specifies an 8,192-token input window. Use the published 8,192-token limit and record truncation; do not infer a larger effective limit from the config field.
- **Identity label:** `google/embeddinggemma-2@914f7f89142e33e77833254d9c9b90c3cef7303b; PyTorch CPU; float32`. Do not label it as the Ollama `embeddinggemma-2:740m` condition.

Google documents a Transformers/SentenceTransformers path, text-only loading, retrieval prefixes, 768-dimensional output, normalization, and float32 CPU use. These documents establish that the runner is a supported candidate; this environment has not loaded the checkpoint or measured its memory, latency, tokenization, or deterministic replay.

## Comparability and hypothesis status

This change would preserve the retrieval-ranking and common relevance-target questions for a named upstream checkpoint. It would not answer whether the blocked Ollama NVFP4 or BF16 packages produce the same scores, rankings, or numerical outputs. Results would apply only to the pinned Google checkpoint and the frozen CPU runner. Model identity alone still would not permit score pooling or semantic equivalence.

The Tev1 calibration, Qwen/Gemma/Guardian dependence, critic comparison, and coding-specialization hypotheses remain testable under their original declared targets. They remain unrun because the complete study requires all identities and the complete preregistration to be frozen before scoring.

## Freeze gates

Before scoring, record and hash the package lock, Python and OS versions, runner code, model snapshot files, input and prompt hashes, precision, context/truncation behavior, normalization, seeds, and analysis version. Run a non-scored runtime preflight against fixed synthetic strings, record the exact 768-value output digest for each string and repeated-run equality, then freeze the full study. Preserve all preflight output separately from scored results. Do not use the preflight to change cases, targets, weights, thresholds, or success criteria.

No preregistration freeze SHA exists. No scored replacement-model calls, full study runs, held-out metrics, or two-run reproducibility results exist.

## Source records

- Ollama manifest snapshots and model config blobs: `docs/experiments/model-runtime/ollama-embeddinggemma-2-740m-*`.
- Pinned Google checkpoint identity record: `docs/experiments/model-runtime/google-embeddinggemma-2-hf-checkpoint-identity.json`.
- Google model card: [EmbeddingGemma 2](https://ai.google.dev/gemma/docs/embeddinggemma/model_card_2).
- Official Transformers model documentation: [EmbeddingGemma 2](https://huggingface.co/docs/transformers/en/model_doc/embedding_gemma2).
- Pinned checkpoint: [google/embeddinggemma-2 at the recorded revision](https://huggingface.co/google/embeddinggemma-2/tree/914f7f89142e33e77833254d9c9b90c3cef7303b).

**Disposition:** Keep model-role scoring blocked. This amendment is proposed, not approved or frozen.
