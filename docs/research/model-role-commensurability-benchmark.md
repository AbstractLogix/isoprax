# Model-Role and Score-Commensurability Benchmark

**Status:** Design and runner in progress. No model-role findings are available yet.

**Evidence class:** Synthetic. This study tests the named local model revisions on authored fixtures. It does not establish broad model-family or field performance.

## Research questions

1. Does Tev1 produce calibrated probabilities across binary, categorical, and ordinal question families?
2. Can an EmbeddingGemma similarity score, a model-reported probability, and a critic judgment predict the same evidence-relevance target?
3. Do Qwen, Gemma, and Guardian judgments show independent errors on the same cases, and does a declared pool improve held-out results?
4. Does Qwen2.5-Coder change performance by task family?
5. Does a common numeric range or model ID support any cross-target interpretation by itself?

The answer to question 5 is no by design. The study tests predictive behavior on named targets. It does not infer semantic equivalence from score shape, model role, or identity.

## Model roles and known lineage

| Model | Declared role in this study | Native output | Lineage recorded |
|---|---|---|---|
| `qwen3.5:9b` | General reasoning baseline | Prompted probability and label | Exact revision; Qwen family |
| `gemma4:e4b` | General-model comparison | Prompted probability and label | Exact revision; Gemma 4 family |
| `qwen2.5-coder:7b` | Coding and debugging comparison | Prompted probability and label | Exact revision; Qwen2.5 family |
| `embeddinggemma-2:740m-bf16` | Evidence retrieval | Query/document similarity | Same EmbeddingGemma 2 740M model variant; Linux-compatible precision tag |
| `tev1:4b` | Decision probability | Question-type-specific outcome probabilities | Fine-tuned from Qwen3.5-4B |
| `granite4.1-guardian:8b` | Critic and relevance judge | Binary yes/no score | Fine-tuned from Granite 4.1 8B |

Both `embeddinggemma-2:740m` and the proposed `embeddinggemma-2:740m-bf16` tag failed to load on the active Linux Ollama service. A compatible build is still being checked. The experiment will not substitute another embedding model without a dated protocol amendment. Freeze the exact manifest digest for every available model and the Ollama version before scored calls.

The Ollama model cards describe Tev1 as a Qwen3.5 fine-tune, EmbeddingGemma 2 as built on Gemma 4 architecture, and Guardian as a Granite 4.1 fine-tune. They describe Guardian's prescribed output as yes/no, including a context-relevance criterion. The runner uses the documented Guardian scoring block for one evidence item per call. Tev1's `confidence` field measures how concentrated its option probabilities are; it is not the probability that its answer is correct. These statements define recorded metadata and API use. They do not prove empirical error dependence. [Tev1 model card](https://ollama.com/library/tev1:4b), [EmbeddingGemma 2 model card](https://ai.google.dev/gemma/docs/embeddinggemma/model_card_2), [Granite Guardian 4.1 model card](https://ollama.com/library/granite4.1-guardian).

## Study A: Tev1 calibration by question family

Use three authored synthetic families with different outcome structures:

| Family | Output type | Target |
|---|---|---|
| Equipment fault | Binary | Whether the stated fault is present |
| Software fault | Categorical, four classes | Which of four injected defect types explains the behavior |
| Incident severity | Ordinal, four levels | The locked severity class |

Generate 64 cases per family. Use 32 development cases and 32 held-out cases per family, stratified by the locked outcome. Keep all labels out of the model input. Send each question through Tev1's decision interface with its native type. Do not substitute a chat-generated number for Tev1's native probability distribution.

Report per family:

- sample counts, class counts, and event rates;
- Brier score and log loss for binary and categorical probability distributions;
- reliability bins and calibration error where the distribution supports the measure;
- ROC AUC for binary outcomes and one-vs-rest AUC only where class counts allow it;
- ranked probability score and class-threshold calibration for ordinal outcomes;
- 95% case-bootstrap intervals, plus output-invalid counts.

The only cross-family pooled metric is the predeclared equal-weighted expected log loss for a task mixture that selects each of the three families with probability 1/3. The report must show all three family results beside that mixture result. The mixture is a summary of this authored task distribution; it is not one shared event.

## Study B: Retrieval score, model probability, and critic judgment

Generate 32 queries in each of four synthetic domains: equipment investigation, software debugging, policy application, and safety-context review. Each query has eight evidence items. There are 16 development queries and 16 held-out queries per domain. Each case contains relevant evidence, close but irrelevant text, misleading evidence, duplicates, and unrelated evidence. Gold labels separately record relevance, source status, and use for a named operation.

The common target is: **does this item provide information relevant to answering this query?** The target has the same definition in each domain. Source validity and operation use are separate labels and are not substituted for relevance.

Each model keeps its native output:

- EmbeddingGemma returns query/document similarity. Use its documented asymmetric retrieval prefixes: `task: search result | query: ...` and `title: none | text: ...`. Rank items within each query and retain the raw similarity.
- Tev1 returns its native probability for the binary relevance question.
- Qwen3.5, Gemma4, and Qwen2.5-Coder return a declared relevance label and a self-reported probability.
- Guardian returns the prescribed `<score>yes</score>` or `<score>no</score>` relevance judgment, one evidence item per call. It is not asked to report a probability.

Fit one global calibration mapping per numeric score source on development cases. Also fit per-domain mappings on development cases as a diagnostic. Evaluate both only on held-out queries. For Guardian, any calibrated probability is a development-fitted mapping of its yes/no label, not a native Guardian score. Report invalid output and calibration-set class counts.

Report by model and domain:

- recall@k and mean reciprocal rank for retrieval scores;
- Brier score, log loss, reliability bins, calibration error, and ROC AUC when defined for predictions on the common relevance target;
- event rates, case and evidence-item counts, output-invalid counts, and 95% intervals bootstrapped by query;
- changes from global to domain-specific calibration;
- ranking and binary-decision disagreement between score sources.

The pooled relevance metric uses an equal-weighted mixture over the four domains, with weight 1/4 each. Per-domain results remain primary. A calibrated common-target score may support comparison for this relevance event only; it does not make its raw similarity, probability, or judgment interchangeable with a source-validity or operation-permission score.

## Study C: Judgment dependence and pooling

On the same query/item pairs and relevance target, compare Qwen3.5, Gemma4, and Guardian. Report each model alone, paired disagreement, false-positive and false-negative overlap, and the held-out joint-error rate. Estimate each model's error rate on development cases; compare the held-out observed joint error with the product expected under an independence assumption. Bootstrap by query and domain.

Evaluate two predeclared pools:

1. **Majority label**: each model's yes/no judgment counts as one vote; Qwen and Gemma probabilities use a 0.5 threshold. The pool requires valid output from all three models.
2. **Equal-weight probability pool**: average the three development-calibrated probabilities with weights 1/3 each. For Guardian, the probability comes only from the development-fitted mapping of its yes/no output.

Compare each pool with all three component models on held-out Brier score, log loss, accuracy, false-positive rate, false-negative rate, and coverage. A pool that performs better on this one synthetic target does not establish general pooling permission or independence.

## Study D: Specialization by family

Compare Qwen2.5-Coder with Qwen3.5 and Gemma4 on the software-fault family and the same non-code families. Use paired per-case differences and domain-stratified intervals. Report the model-by-family interaction. Do not combine model-family performance into a leaderboard or infer that the coding model's numeric probability has the same calibration outside its tested family.

## Reproducibility and limits

Before scored calls, record the six exact model manifest digests, Ollama version, case and split digests, prompt or query-template hashes, seeds, and analysis version. Run the complete suite twice. Preserve both outputs if any digest differs. Do not change prompts, sample generation, weights, or thresholds after viewing scored outputs; any change requires a dated amendment before a new scored run.

All cases are authored and synthetic. The sample is a pilot, not an independent human-adjudicated corpus. Shared lineage is recorded because it can inform dependence analysis; it is not used as a substitute for paired error measurements. No result in this study authorizes a runtime policy or a Semadmit handoff.
