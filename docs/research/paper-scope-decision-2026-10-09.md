# Paper scope decision — 2026-10-09

## Decision

Keep the cross-family evidence-contract paper and the model-role study separate.

The main paper asks whether a probability score and its calibration support cross-family comparison when outcome meanings differ. Benchmark A directly tests that question with two declared targets and a same-target control. The operation-rule challenge tests whether explicit operation conditions catch fixture-defined invalid use. Neither experiment establishes behavior on production JIT or AIOps data.

The model-role experiment asks whether model identity, specialization, probability outputs, embedding scores, and critic judgments support calibration, pooling, or independence claims. It uses authored synthetic tasks and synthetic relevance labels. It does not test JIT/AIOps outcome equivalence, so it cannot support the main paper's cross-family empirical claim.

## Allocation

| Evidence | Main paper | Companion model-role study | Reason |
|---|---:|---:|---|
| Benchmark A and same-target control | Yes | No | Direct test of same numeric forecasts under distinct or shared target declarations. |
| 23-case operation-rule challenge | Yes, limited | No | Directly compares rules for the contract's operation-specific conditions; cases are internally authored. |
| Tev1 family calibration | No | Yes | Tests one model-role probability source on authored question families. |
| Embedding cosine vs model/critic scores | No | Yes | Compares score roles against synthetic relevance judgments, not cross-family runtime outcomes. |
| Judge disagreement and equal-weight pool | No | Yes | Tests a common authored relevance target among judges only. |
| Coder vs general-model ranking | No | Yes | Tests specialization on the authored selection cases. |
| Bouleusis retrieval and acquisition | No | Separate source-specific evidence note | Different task, repository, and question; order trials and fixed bugs limit generalization. |

## Publication position

The main paper's statistical premise is established prior work: calibration and scoring are target-relative. The candidate contribution is an explicit, operation-sensitive evidence contract, its executable check, and a reproducible synthetic challenge. The novelty and usefulness of that contribution remain open for independent scientific review.

No empirical result in this package validates an operational Semadmit rule. The operation-rule comparison uses a finite, internally authored challenge. Four forecast cases with calibration-revision mismatches remain excluded from positive policy-validity claims. The policy evidence remains separate from the model-role results.

Cross-repository assurance from Semadmit PR #10 and Bouleusis PR #4 is recorded in [cross-repository assurance evidence](cross-repository-assurance-evidence-2026-10-09.md) and the claim registry. It supports only bounded software behavior, deterministic evidence admission, and selected epistemic replay invariants. It is not evidence of claim truth, general reasoning accuracy, forecasting performance, scientific validity, or real-world outcome commensurability. Bouleusis PR #4 remained open without independent human review at the checked commit.

The repository owner authorized publication of the four selected original Bouleusis research data files. The source repository's historical `NOASSERTION` metadata is preserved. The selected data have a separate CC BY 4.0 release record and a limited secret/private-identifier scan. The authorization does not include Bouleusis source code or third-party materials. See the [dataset README](../experiments/bouleusis-2026-10-08-raw/README.md) and manifest.

## Submission status

The paper is not submission-ready as a validated cross-family prediction study. A reviewer can assess the contract argument and the synthetic demonstration. Before submission, obtain independent review of novelty and case validity, add independently authored counterexamples and a validated semantic bridge, deposit the exact release with a persistent identifier, and avoid claims of field effectiveness. The selected-data redistribution authorization is recorded; it does not resolve access to the private Bouleusis assurance records for an external reviewer.
