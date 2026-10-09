# Model Runtime Qualification Amendment — 2026-10-09

## Scope and result

This amendment resolves the Linux execution blocker for the model-role study with a distinct, officially published Google checkpoint and CPU runtime. It does not claim that this condition is equivalent to either Ollama registry artifact. The model-role preregistration v2 pins this condition before scored calls.

The requested Ollama identity `embeddinggemma-2:740m` and the investigated `embeddinggemma-2:740m-bf16` both fail to load in the selected Linux Ollama 0.40.1 runtime because the registry packages require MLX and this host has no MLX runtime. Their registry manifests remain preserved. The failure is an execution limitation of this host and backend, not evidence that the model family is unavailable elsewhere.

## Qualified alternate condition

Google publishes `google/embeddinggemma-2` at revision `914f7f89142e33e77833254d9c9b90c3cef7303b`. Its official model card documents SentenceTransformers use and query/document task prefixes. We loaded this exact revision through SentenceTransformers and Transformers on WSL2 Linux x86_64 CPU in float32. The preflight produced 768 finite values per input. Repeated token IDs and vectors matched exactly within the same process. The model identity and all 15 checkpoint-file SHA-256 values, plus the environment-lock SHA-256, are frozen in the v2 preregistration.

The research runner's adapter was then exercised on the same three non-scored preflight strings. It reproduced all saved float32 vectors exactly. Its combined identity digest is `03f50c93bf327079f38373e5db2937f7826e487bed9e403f51583821737f8462`. The existing preflight records remain unchanged:

- Input SHA-256: `618de8341e621c88eed7ae3fcbd872a75adf96e71106dab7d307ef027a9221ca`.
- Saved output SHA-256: `347d3ea86aba971a66faf1c032b2873e6930d59308a1b3fe9384f19a4a403b28`.
- Requirements-lock SHA-256: `c9b9ce74de4ea8319ed65a058b8b3025f4206947292076f739a3f02eb1891125`.

The source report [EmbeddingGemma runtime preflight](../experiments/model-runtime/embeddinggemma-2-hf-cpu-preflight-output.json) records the host, package versions, output shape, token IDs, vector digests, and same-process repeat result. The new runner adapter verifies the pinned revision, every listed checkpoint file, every locked package version, CPU placement, float32 dtype, and finite output before returning vectors.

## Compatibility boundaries

- Google documents SentenceTransformers, Transformers, 768-dimensional output, retrieval prefixes, and CPU float32 use in the [EmbeddingGemma 2 model card](https://ai.google.dev/gemma/docs/embeddinggemma/model_card_2).
- Ollama lists the exact requested tag and registry digest in its [EmbeddingGemma 2 library entry](https://ollama.com/library/embeddinggemma-2). Its [MLX runtime announcement](https://ollama.com/blog/mlx) describes MLX use on Apple Silicon. This makes an Apple Silicon Ollama load a supported candidate, but no Mac was available to test the exact tag here.
- The Google checkpoint uses the full upstream safetensors and tokenizer files at a pinned revision. The Ollama registry artifact is a separate package and runtime. The conditions differ in backend and numerical representation. No Ollama vector output was available for tokenizer, normalization, or numerical parity comparison.
- The preflight requested no extra SentenceTransformers normalization; the pipeline returned unit-norm vectors. The model-role runner computes cosine similarity from those vectors. Ollama-side normalization behavior was not measured.
- Same-process repeatability on this WSL2 host is established for the preflight only. Cross-process, cross-host, and cross-backend reproducibility are not established.

## Scoring gate

The prior draft preregistration remains unchanged. Versioned HF CPU amendments preserve every pre-score revision and its hash. The first v2 and v2.1 freezes were superseded before scoring to add runtime-artifact checks and exact runtime-matrix enforcement. The v2.2 runtime guard then stopped before scoring because its dtype label did not match the adapter's `float32` value. No benchmark case or gold-bearing prompt was sent by those attempts.

The final [v2.3 preregistration](../../specs/047-retrieval-selection-dependence/model-role-preregistration-v2.3.json) has SHA-256 `dc1f009389566e4a2cf1ff5e465c3b2bfb2e41e9b5af7a13ab980ce96b838436`. It records the HF CPU condition, five Ollama identities, all checkpoint and package hashes, the generated case-set and prompt digests, evaluator source hashes, and six runtime preflight artifact hashes. Before model scoring, the runner checks those file hashes, the source hashes, the exact Python/platform/package/runtime matrix, all six model identities, and the generated case and prompt digests. The final preflight passed for Ollama 0.40.1 and every frozen model identity. No scored calls have been made as of this amendment.

The Guardian runtime received a separate non-scored output-schema smoke test. Its raw output parsed as a documented binary critic judgment. No gold label or performance metric was assigned. The record is `../experiments/model-runtime/granite-guardian-output-schema-preflight-2026-10-09.json`.
