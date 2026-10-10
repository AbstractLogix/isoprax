# Tev1 output-rights assessment — 2026-10-10

## Status

**Companion model output rights remain unresolved.** The flagship paper contains no Tev1 output or model weights, so this question does not block its standalone replication.

## Evidence checked

- The [official Tev1 model card](https://huggingface.co/togethercomputer/Tev1-4B-experimental) says the base Qwen3.5-4B model is Apache-2.0 and the release license for the fine-tuned Tev1 weights is still being finalized. It also says dataset sources retain their own terms; it gives no blanket training-data license.
- The [official Together Tev1 repository](https://github.com/togethercomputer/tev1) says its code and original documentation are MIT licensed. It says third-party datasets and model weights have separate terms. Its [source record](https://github.com/togethercomputer/tev1/blob/main/DATA_SOURCES.md) records mixed and incomplete source licenses. A code license is not a model-weight or output license.
- The [Ollama `tev1:4b` page](https://ollama.com/library/tev1%3A4b) lists Apache-2.0 text attributed to Alibaba Cloud and MIT text attributed to `open-jev contributors`. It does not map those texts to the fine-tuned weights or state an output license.
- A direct local `ollama show --license tev1:4b` inspection on 2026-10-10 returned both Apache-2.0 and MIT license texts. `ollama list` showed tag `tev1:4b`, ID prefix `9b5bb969e46c`. The recorded local manifest digest is `9b5bb969e46c4b776826d6f2d401e22893205693f172653af6254897255025b8`.
- The previous local audit, dated 2026-10-09, recorded only the Apache text and already marked output rights unresolved. The new direct inspection adds the MIT text but does not resolve what it covers.

## Permission boundaries

| Question | Finding |
|---|---|
| Download and execute | Public distribution and local execution are technically available. The reviewed sources do not identify an unambiguous license grant for the fine-tuned weights. Access is not treated here as proof of legal permission. |
| Redistribute model weights | Not cleared. Do not include or redistribute Tev1 weights in the research package. |
| Publish generated predictions, numerical scores, or short responses | Unresolved. No reviewed source states which terms govern these outputs or clearly grants/limits publication and reuse. Do not infer that a pending weight license prohibits outputs; do not infer that public availability permits output publication. |
| License original prompts and expected labels | The study's authored synthetic prompts and reference labels are separate original research materials. Their authors may license material they own. This does not assign rights to model outputs, model weights, or training data. |
| Embedded third-party material | No third-party training data or weights are included in the research package. No systematic output-similarity or third-party-text review was found. Short responses can still reproduce material; the records have not been cleared on that basis. |

The synthetic prompts, numerical predictions, and short responses are distinct from model weights and training data. A license on the prompt and reference labels would not settle the status of generated text or scores.

## Public record and handling

The frozen model-role outputs are already exposed in public draft PR [#54](https://github.com/AbstractLogix/isoprax/pull/54) as compressed run parts with a manifest and replay summary. This assessment does not overwrite, delete, or rewrite those records. The records are not covered by the separate Bouleusis CC BY 4.0 data authorization. The standalone flagship branch includes none of them.

## Clarification request draft — not sent

**Subject:** Tev1-4B-experimental: publication of authored synthetic evaluation outputs

We used a local `tev1:4b` distribution to score authored synthetic prompts. The proposed research record contains the authored prompts and reference labels, numerical probabilities or scores, and short model responses. It contains no Tev1 weights and no Tev1 training data.

Which terms and version, if any, govern publication and reuse of these generated predictions, numerical scores, and short responses? Does a specific license apply to the fine-tuned weights, the Ollama conversion, the outputs, or different parts separately? Please identify any required attribution, limits on quoting or redistributing generated text, and any restriction from third-party training sources that applies to these outputs. We are not asking to redistribute weights or training datasets.

This request is a draft. It has not been sent.
