# Calibration Is Not Enough: Outcome Commensurability as a Precondition for Cross-Family Failure Prediction

## Abstract

Probabilistic forecasts are calibrated relative to specified outcomes. Calibration alone does not show that forecasts from different prediction tasks measure the same event. We examine this distinction for just-in-time software defect prediction and operational failure prediction, where labels, observation processes, and prediction windows can differ. The statistical premise is established background; this paper does not claim it as a new calibration theorem. Its proposed contribution is narrower: an explicit, operation-sensitive contract for declaring when direct comparison or pooling is supported, plus a deterministic implementation and synthetic challenge. In Benchmark A, two lanes each produced mean forecast 0.8, event rate 0.8, and Brier score 0.16, while their event definitions, observation processes, thresholds, and windows differed. A same-target control used the same numeric setup. The different-target summary is valid only as its named equal-weight mixture estimand, not as a forecast of one common event. In a finite, internally authored policy challenge, the operation-specific rule made fewer false permissions than the tested simpler rules; the fixture does not establish general superiority or field value. The checker validates declarations, not the truth of measurement pipelines. Independent scientific review and external validation remain open. [[C9]] [[C10]]

**Keywords:** forecast calibration; outcome definition; commensurability; software defect prediction; operational failure prediction; reproducibility

## Introduction

Just-in-time software defect prediction (JIT-DP) and operational failure prediction use different prediction tasks. JIT-DP often predicts whether a code change will later receive a defect-related label (Ni et al., 2022; Nam et al., 2026). Operational prediction may forecast a service or system event from logs, metrics, traces, or injected faults (Chen et al., 2025; Shetty et al., 2024; Yang et al., 2026). These fields have different data and evaluation practices. A score from each field can be represented as a probability without making the events equivalent. These studies illustrate task-specific settings; they do not themselves pair their labels into one shared target. [[L5]] [[L6]] [[L9]] [[L10]] [[L11]] [[L15]]

This paper asks a limited question: what must be declared before a system treats forecasts as predictions of one common event? Our central premise is that calibration is target-relative. A forecast may be calibrated for its own outcome while another calibrated forecast concerns a different outcome. Proper scoring rules evaluate forecasts against realized outcomes, but they do not erase differences in the outcome variables being scored. [[C1]] [[L1]] [[L16]]

We call the proposed declaration-and-operation conditions an **outcome-commensurability contract**. The contract is not a new statistical law and does not replace construct validity, measurement invariance, estimand definition, or forecast-combination theory. It makes a subset of those concerns explicit in a software-checkable interface. The checker can compare declarations; it cannot establish that the declarations accurately describe how labels were produced. [[C11]]

The paper has two research questions:

- **RQ1:** Can equal numeric forecasts and equal calibration summaries support a common-event interpretation when target definitions differ?
- **RQ2:** On the authored challenge, how does operation-specific gating compare with simpler rules on false permission, unnecessary refusal, and interpretation errors?

Our experiments are deterministic and synthetic. They demonstrate cases in which the contract distinguishes direct same-event pooling from a named mixture. They do not measure production prediction performance, establish an operational policy, or validate JIT/AIOps outcome equivalence. The model-role, retrieval, and acquisition studies are separate evidence and are not used to answer these research questions.

## Related work

Calibration and post-processing methods are established for forecasts of declared labels (Guo et al., 2017). Proper scoring rules such as Brier score and logarithmic score assess predictive distributions against observations (Gneiting and Raftery, 2007). Neither calibration nor a proper score makes distinct observations the same random variable. [[L1]] [[L16]]

Forecast combination is also established (Bates and Granger, 1969; Ranjan and Gneiting, 2010). Its validity depends on the combination target and the forecast construction. A combination defined for the same event differs from a summary over a declared mixture of event types. The latter can be useful, but it estimates the named mixture and does not become a forecast of one event. [[L2]] [[L3]]

The concern overlaps with construct validity and measurement invariance. Construct validity asks whether observations support the intended interpretation (Cronbach and Meehl, 1955). Measurement invariance asks whether measurements have comparable meaning across groups or conditions (Vandenberg and Lance, 2000). Software-engineering guidance also treats construct validity as a core threat to claims based on empirical indicators (Sjøberg and Bergersen, 2023). Recent work makes a related case for construct validity in LLM benchmarks (Bean et al., 2025). These are related foundations, not synonyms for the proposed contract, and this study does not conduct a psychometric invariance test. [[L4]] [[L18]] [[L19]] [[L20]]

Software prediction studies also face label and evaluation risks. Defect labels can depend on collection and linking methods (Herbold et al., 2022); AIOps results can depend on data splits (Lyu et al., 2021), interpretation practice (Lyu et al., 2022), and adaptation to change (Poenaru-Olaru et al., 2024). Recent autonomous-cloud diagnosis work extends this operational line but does not pair its outcomes with JIT targets. Those works motivate explicit outcome and observation declarations, but they do not establish that any two datasets are commensurable. [[L5]] [[L6]] [[L7]] [[L8]] [[L15]]

The contribution claimed here is an executable, operation-aware declaration contract and a falsifiable synthetic demonstration. The novelty claim is intentionally modest. Whether this software contribution adds value beyond established construct-validity and measurement frameworks requires independent review and cases that were not authored by the proposing team.

## Formal problem

Let a forecast be a probability \(p\) for a binary outcome \(Y\). Calibration for that outcome means that forecasts at level \(p\) agree with the conditional event frequency under the relevant population and information regime; for example, \(\mathbb{E}[Y \mid p] = p\) under the stated conditions. This relation is indexed by \(Y\). It does not imply that another outcome \(Z\) equals \(Y\), has the same measurement process, or answers the same decision question. [[C1]]

We represent a target declaration as:

\[
T = (E, O, W, H, \tau, P, I),
\]

where \(E\) is the event rule, \(O\) the observation process, \(W\) the time window, \(H\) the horizon, \(\tau\) any threshold or event boundary, \(P\) the target population, and \(I\) the information available at prediction time. A declaration may need further fields for a domain, censoring, label adjudication, or versioning. The tuple is a contract schema, not a complete theory of measurement.

We distinguish four operations:

- **Calibration assessment:** compare a forecast with outcomes for its declared target.
- **Direct same-event pooling:** combine forecast probabilities as if they estimate one event.
- **Ranking:** order items under a declared ranking target and population.
- **Decision comparison:** compare actions using a declared action set, state mapping, and common utility or loss.

The proposed contract permits direct same-event pooling only when the required target semantics match and the selected operation permits pooling. A different-event summary may still be reported if it has a predeclared mixture estimand and weights. A decision comparison across distinct events can also be meaningful when both are mapped to common states, actions, and utilities. That utility comparison does not make the event probabilities interchangeable. The current reference implementation does not implement a general utility bridge, so it does not certify one.

### Counterexamples to overbroad claims

Two forecasts can each report \(p=0.8\) and be calibrated when their respective event rates are 0.8, yet one can concern a defect-fix link within a window and another a telemetry threshold crossing within a different window. Their numeric equality does not make them forecasts of the same event. Benchmark A instantiates this construction. [[C9]]

Conversely, different event labels can support a legitimate common decision comparison. For example, a short-horizon stockout and a longer-horizon service failure may trigger actions with known costs. Expected utility can be compared if each forecast is mapped to a common action and state space and the utility is declared. This supports decision comparison, not direct probability pooling.

Identical event wording can hide different observation processes. Complete request traces and sampled logs can produce different label sensitivity or censoring even if both labels are called “service unavailable.” Equal text is therefore insufficient when the observation process differs or is unknown.

Different horizons may be related by a survival or hazard model. If the model and assumptions support a transformation, a separate bridge can define comparable horizon risks. The transformed forecasts then depend on that bridge and its validation; horizon mismatch is not repaired by renaming the target.

Two forecasts can concern the same event but use different information sets. Their predictive performance can be compared on a common evaluation population, but their conditioning information, calibration, and error dependence still need to be reported. Same target does not establish equal information, independent errors, or equal decision value.

Finally, a predeclared random mixture over target types can define a valid aggregate estimand. Its probability is the weighted mean for that mixture. It is not the probability of a common event unless a separate semantic construction establishes one.

## Contract and implementation

The public specification distinguishes structural conformance from semantic conformance. Structural conformance means that records follow a declared shared interface. It does not mean that two outputs predict the same event. The reference checker compares structured outcome declarations and requested operations. It can reject a mismatch that is represented in those declarations. It cannot inspect a real measurement pipeline and prove the declaration true. It can also refuse a valid semantic bridge if that bridge is absent from the supported schema. [[C11]]

The operation-gating proposal is therefore a conservative interface rule, not a universal semantic oracle. A false permission can encourage an unsupported interpretation. An unnecessary refusal can block a valid operation, especially a utility comparison supported by an explicit bridge. The policy trade-off must be tested on independently adjudicated cases; matching metadata is not ground truth.

## Experimental protocol

Benchmark A is generated deterministically by the repository experiment runner. It uses synthetic binary outcomes and fixed forecasts. The Change lane declares a fix-linked defect event with a thirty-day window. The Operational lane declares a threshold-breach event observed through an operational process with a thirty-minute window. The same-target positive control uses one shared threshold-breach target in two lanes. A 50:50 different-target mixture and a same-target positive-control mixture are reported with exact target IDs and weights. [[C9]]

The operation-rule challenge contains internally authored cases labeled as valid or invalid for specified operations. Four rules are compared: naive aggregation, one global label, a metadata-only rule, and operation-specific gating. Outcomes in this challenge are finite case counts, not estimates of error rates on an external case population. The reference outcomes have not been independently adjudicated. [[C10]]

Generative AI assistance supported technical drafting and code preparation for this research package. The accountable human author must review and approve the final manuscript, analyses, and disclosure before submission.

No production dataset, natural-language target assessment, prospective operational decision, or independently authored test set was used. No sample-size or power claim is made for field validity. The exact runner, frozen inputs, and table generator are included in the replication package.

## Results

### Forecast targets

The two distinct-target lanes each have 100 observations, mean forecast 0.800, event rate 0.800, and Brier score 0.160. The two same-target controls have the same summaries. The forecasts are constant, so ROC AUC is not available. These equal summaries do not identify a common event. The different-target aggregate is valid only for the declared 50:50 mixture target shown below. [[C9]]

## Table 1. Synthetic forecast targets and declared mixtures [[C9]]

| Condition | Exact target ID | n | Mean forecast | Event rate | Brier | ROC AUC | Evidence |
|---|---|---:|---:|---:|---:|---|---|
| change | `synthetic.change.fix-linked-defect.30d` | 100 | 0.800 | 0.800 | 0.160 | not available (constant scores) | [[C9]] |
| operational | `synthetic.operations.threshold-breach.30m` | 100 | 0.800 | 0.800 | 0.160 | not available (constant scores) | [[C9]] |
| control-a (positive control) | `synthetic.shared.threshold-breach.30m` | 100 | 0.800 | 0.800 | 0.160 | not available (constant scores) | [[C9]] |
| control-b (positive control) | `synthetic.shared.threshold-breach.30m` | 100 | 0.800 | 0.800 | 0.160 | not available (constant scores) | [[C9]] |
| Different-target numeric mixture | `synthetic.mixture.change-30d-and-operational-30m.equal-weight` | 200 | 0.800 | 0.800 | 0.160 | not available (constant scores) | [[C9]] |
| Same-target positive-control mixture | `synthetic.shared.threshold-breach.30m` | 200 | 0.800 | 0.800 | 0.160 | not available (constant scores) | [[C9]] |

The two target-specific lane risks differ in event, observation process, threshold, and window. The different-target mean is a 50:50 mixture over those lane risks. Its exact estimand is the target ID shown. It is not the probability of one shared event. [[C9]]

### Operation-specific gating

On the 23 internally authored cases, operation-specific gating made no false permissions, unnecessary refusals, or interpretation errors. Metadata-only gating also made no unnecessary refusals or interpretation errors, but it made five false permissions. The global-label and naive rules made more errors on this fixture. These descriptive results do not show general superiority: case construction and expected labels were controlled by the same project, and saved per-case rows do not support independent recomputation of ranking-change or decision-change totals. [[C10]]

## Table 2. Operation-specific rule challenge [[C10]]

The 23 cases were internally authored. Counts are descriptive and are not estimated population rates. [[C10]]

| Rule | False permissions / invalid cases | Unnecessary refusals / valid cases | Interpretation errors / cases | Evidence |
|---|---:|---:|---:|---|
| global label | 7/12 | 3/11 | 3/23 | [[C10]] |
| metadata only | 5/12 | 0/11 | 0/23 | [[C10]] |
| naive aggregation | 12/12 | 0/11 | 8/23 | [[C10]] |
| operation specific | 0/12 | 0/11 | 0/23 | [[C10]] |

## Discussion

The synthetic benchmark shows why calibration summaries cannot establish target equivalence. It does not estimate the frequency or cost of cross-family aggregation errors in practice. The main empirical result is a counterexample to the sufficiency claim: separate calibration can coexist with distinct target semantics. This result was built into a deterministic fixture and should be read as a reproducible demonstration, not as a surprising population discovery. [[C9]]

The policy challenge gives limited evidence that operation-specific conditions can distinguish cases that simpler rules miss in this fixture. It does not show that the operation-specific rule is necessary in general: the metadata-only baseline matched it on unnecessary refusals and interpretation errors here. A new blinded case set could show the simpler rule performs equally well, or that the current rule refuses valid operations. Such a result would weaken the complexity argument. [[C10]]

The strongest novelty objection is that the paper may restate construct validity, estimand alignment, and measurement-equivalence concerns in a software contract. The strongest formal objection is that a direct same-event pooling gate can conflate forecast equivalence with decision usefulness. A common utility function can support a cross-target decision comparison even where probabilities are not interchangeable. We address this by limiting the proposed refusal to unsupported direct pooling and by identifying utility bridges as a separate, currently unsupported operation. Whether the contract's implementation adds practical value remains unresolved. [[C11]]

## Threats to validity

**Construct validity.** Event and observation-process declarations may omit important features such as censoring, measurement error, case ascertainment, and adjudication. Equal structured values are not proof that the underlying constructs or procedures match. A future study needs independent reviewers and blinded cases, including equal-wording/different-process negatives and different-wording/same-target positives.

**Internal validity.** The forecast experiment uses deterministic synthetic data with fixed forecasts; it has no stochastic training procedure, label noise, deployment shift, or data leakage pathway to estimate. The policy challenge was authored in the same project as the candidate rule. The table reports counts only and cannot establish unbiased policy performance.

**Statistical conclusion validity.** The repeated construction is not a sample from a defined population of JIT/AIOps tasks. No inferential confidence intervals or power claims are made for the main synthetic benchmark. Calibration claims beyond the stated finite empirical frequency are not inferred. Ranking and decision-change totals are unavailable from saved per-case outputs and are omitted. [[C10]]

**External validity.** No production JIT or AIOps targets were paired, and no shared real-world observation process was validated. The results do not establish that any real dataset pair is commensurable or non-commensurable. Related benchmark studies provide context but do not supply evidence for this paper's target mappings. [[L5]] [[L6]] [[L7]] [[L8]] [[L9]] [[L10]] [[L11]]

**Reproducibility.** The source, generated table, and synthetic outcomes can be checked from a clean repository checkout. Hashes establish byte identity, not correctness of target meanings or independence. Provenance records help trace source and derived artifacts; they do not establish claim truth. Dataset and model reporting templates can improve documentation but cannot validate a target declaration. A public-data scan can detect only the patterns it tests. The Bouleusis raw snapshots have a source commit and original hashes; selected original records are released with owner authorization under CC BY 4.0. The private source code and third-party materials are excluded. The dataset README defines the exact license scope. No external data DOI has yet been assigned. [[L12]] [[L13]] [[C14]]

## Limitations and future work

The current contract is intentionally incomplete. It does not establish measurement truth, perform statistical measurement-invariance tests, validate transport between populations, infer causal relationships, or implement general utility transformations. Structured equality can be too strict for semantically equivalent targets and too permissive when declarations omit relevant facts. The present challenge does not settle that trade-off.

The next test should be preregistered and independently authored. It should include semantic bridges, transformation cases, distinct-event utility comparisons, identical labels with different observation processes, and missing or incorrect metadata. Independent reviewers should set reference outcomes before the rule is run. The analysis should compare operation-specific gating with simpler rules and report case-level false permission, unnecessary refusal, interpretation errors, ranking changes, and decision changes only when those outputs and decision rules are fully specified.

## Reproducibility and data availability

The replication instructions, raw record manifest, owner authorization record, recomputation code, generated tables, claim registry, and machine-readable automated review are in the public repository. The raw Bouleusis records are unchanged lossless snapshots from the pinned source commit. The source metadata's `NOASSERTION` value is retained as historical metadata; the public release license and its narrow scope are recorded separately. The integrity runner can reproduce the registered results without access to the private Bouleusis repository. It does not replace independent scientific review.

For eventual journal submission, deposit this exact release in a public repository with a persistent identifier and use that identifier in the Data Availability Statement. The current repository branch does not yet have a DOI.

## Conclusion

Calibration is target-relative. Therefore, calibration alone does not establish that forecasts from different prediction families measure the same event. A named mixture can support a pooled summary for that mixture, while a common utility mapping can support some cross-target decisions; neither operation makes distinct event probabilities interchangeable. The executable contract makes these distinctions explicit for the operations it supports. The synthetic results demonstrate the distinction and expose limitations in the current policy evidence. The contract's novelty, completeness, and operational value remain hypotheses for independent review and prospective testing.

## References

- ACM SIGSOFT. Empirical standards and artifact evaluation guidance. https://www2.sigsoft.org/EmpiricalStandards/; https://github.com/acmsigsoft/artifact-evaluation [[L14]]
- Bates, J. M., and Granger, C. W. J. (1969). The combination of forecasts. *Operational Research Quarterly*, 20(4), 451–468. https://doi.org/10.1057/jors.1969.103 [[L2]]
- Bean, A. M., et al. (2025). Measuring what matters: Construct validity in large language model benchmarks. NeurIPS 2025 Track on Datasets and Benchmarks. https://arxiv.org/abs/2511.04703 [[L4]]
- Chen, Y., et al. (2025). AIOpsLab: A holistic framework to evaluate AI agents for enabling autonomous clouds. arXiv:2501.06706. https://arxiv.org/abs/2501.06706 [[L11]]
- Cronbach, L. J., and Meehl, P. E. (1955). Construct validity in psychological tests. *Psychological Bulletin*, 52(4), 281–302. https://doi.org/10.1037/h0040957 [[L18]]
- Gebru, T., et al. (2021). Datasheets for datasets. *Communications of the ACM*, 64(12), 86–92. https://doi.org/10.1145/3458723; Mitchell, M., et al. (2019). Model cards for model reporting. https://arxiv.org/abs/1810.03993 [[L12]]
- Gneiting, T., and Raftery, A. E. (2007). Strictly proper scoring rules, prediction, and estimation. *Journal of the American Statistical Association*, 102(477), 359–378. https://doi.org/10.1198/016214506000001437 [[L1]]
- Guo, C., Pleiss, G., Sun, Y., and Weinberger, K. Q. (2017). On calibration of modern neural networks. *Proceedings of the 34th International Conference on Machine Learning*, 1321–1330. https://proceedings.mlr.press/v70/guo17a.html [[L16]]
- Herbold, S., Trautsch, A., and Trautsch, F. (2022). On the feasibility of SZZ-based data filtering. *Empirical Software Engineering*. https://doi.org/10.1007/s10664-021-10092-4 [[L5]]
- Lyu, Y., et al. (2021). An empirical study of the impact of data splitting decisions on the performance of AIOps solutions. *ACM Transactions on Software Engineering and Methodology*, 30(4). https://doi.org/10.1145/3447876 [[L6]]
- Lyu, Y., et al. (2022). Towards a consistent interpretation of AIOps models. *ACM Transactions on Software Engineering and Methodology*, 31(1), Article 16. https://doi.org/10.1145/3488269 [[L7]]
- Nam, D., Kim, T., Ryu, D., and Baik, J. (2026). ReDef: Do code language models truly understand code changes for just-in-time software defect prediction? *Proceedings of the ACM on Software Engineering*, 3(FSE), Article FSE172. https://doi.org/10.1145/3808179 [[L10]]
- Ni, C., et al. (2022). The best of both worlds: Integrating semantic features with expert features for defect prediction and localization. *Proceedings of ESEC/FSE 2022*, 672–683. https://doi.org/10.1145/3540250.3549165 [[L9]]
- Poenaru-Olaru, L., et al. (2024). Is your anomaly detector ready for change? Adapting AIOps solutions to the real world. *Proceedings of the 2024 IEEE/ACM 3rd International Conference on AI Engineering*, 222–233. https://doi.org/10.1145/3644815.3644961 [[L8]]
- Ranjan, R., and Gneiting, T. (2010). Combining probability forecasts. *Journal of the Royal Statistical Society: Series B*, 72(1), 71–91. https://doi.org/10.1111/j.1467-9868.2009.00726.x [[L3]]
- Shetty, M., et al. (2024). Building AI agents for autonomous clouds: Challenges and design principles. *Proceedings of the ACM Symposium on Cloud Computing*. https://doi.org/10.1145/3698038.3698525 [[L11]]
- Sjøberg, D. I. K., and Bergersen, G. R. (2023). Construct validity in software engineering. *IEEE Transactions on Software Engineering*, 49(3), 1374–1396. https://doi.org/10.1109/TSE.2022.3176725 [[L20]]
- Vandenberg, R. J., and Lance, C. E. (2000). A review and synthesis of the measurement invariance literature: Suggestions, practices, and recommendations for organizational research. *Organizational Research Methods*, 3(1), 4–70. https://doi.org/10.1177/109442810031002 [[L19]]
- W3C. (2013). PROV-DM: The PROV data model. W3C Recommendation. https://www.w3.org/TR/prov-dm/ [[L13]]
- Wilkinson, T., and Ferro, C. A. T. (2026). Calibrated probability forecast sequences and measure-valued martingales. Preprint. https://arxiv.org/abs/2606.31621 [[L17]]
- Yang, P., et al. (2026). AOI: Turning failed trajectories into training signals for autonomous cloud diagnosis. Preprint. https://arxiv.org/abs/2603.03378 [[L15]]
