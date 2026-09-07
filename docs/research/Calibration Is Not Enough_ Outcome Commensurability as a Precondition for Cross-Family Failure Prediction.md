# Calibration Is Not Enough: Outcome Commensurability as a Precondition for Cross-Family Failure Prediction

## Abstract

Just-in-Time (JIT) software defect prediction and AIOps operational-failure prediction are established but largely separate research families, developed with different benchmarks and vocabularies. Recent work illustrates both sides of that separation: ReDef studies code-change representations and high-confidence repository-derived defect labels (Nam et al., 2026), while AIOpsLab provides an operational environment for deploying services, injecting faults, generating workloads, exporting telemetry, and evaluating agents (Shetty et al., 2024; Chen et al., 2025). They nonetheless share an abstract structure: ingest an event, compare it against historical outcomes, emit a score, and learn from the observed result. We formalize that shared structure as an implementation-independent conformance contract spanning both families, and isolate a precondition for meaningful cross-family probabilistic comparison: the outcome definitions must be commensurable.

Calibration is widely and correctly treated as necessary for interpreting and comparing predicted probabilities. We argue that it is not sufficient. Calibration is a property of a probability relative to its own event definition: a perfectly calibrated forecast of “this commit was later linked to a fix” and a perfectly calibrated forecast of “a telemetry threshold was crossed” are both correct and remain incommensurable, because the mismatch is in what is predicted rather than how well. The failure is silent: the arithmetic yields a tidy joint ranking without establishing a common semantic interpretation. We therefore introduce outcome commensurability as a second, independent necessary condition, make the event definition an explicit and mechanically checkable object, and make cross-family comparison conditional on it. This motivates a split between Structural conformance, in which one contract governs both families, and Semantic conformance, in which their scores are actually comparable.

The public benchmark pairings considered here do not provide the shared observation semantics required for a Semantic claim. ReDef's repository-derived labels and AIOpsLab's operational fault-and-telemetry environment serve different evaluation purposes; neither should be treated as a shared outcome definition merely because both produce prediction targets. Calibration, corpus size, and record linkage do not by themselves repair that mismatch. We report a reference implementation that demonstrates the distinction by failing it deliberately: its two baseline strategies carry non-commensurable outcome definitions, so it withholds pooled cross-family figures and self-reports Structural conformance only. We identify deterministic replay under a single observation process as a concrete route to a Semantic claim, and specify the predeclaration and admission discipline such a self-constructed corpus requires.

## 1. Introduction

Software changes and operational failures are closely related in practice but are usually studied through different predictive tasks. Just-in-Time defect prediction estimates the risk associated with a code change, often using repository history, change metrics, or learned code representations. AIOps failure prediction estimates the risk associated with a running system, using telemetry, execution records, and operational history. Both families seek to support decisions before an adverse outcome occurs, yet their models, benchmarks, and evaluation conventions have largely developed independently.

This separation creates an interoperability problem. A system may produce a risk score for a commit and an anomaly score for a running service, but the existence of two scores does not establish that they can be compared. Even when both are represented as probabilities, their numerical similarity may conceal a difference in the events being predicted. A probability of 0.8 that a commit will later be linked to a defect fix is not necessarily comparable to a probability of 0.8 that a service will cross a failure threshold within an hour. The two forecasts may each be well calibrated while answering different questions.

Calibration is therefore necessary but insufficient for the intended form of cross-family comparison. A calibrated forecast relates predicted probability to observed frequency under a particular outcome definition. It does not establish that two outcome definitions denote the same event. This distinction matters whenever scores are jointly ranked, thresholded, aggregated, or used to reason about the relative risk of changes and operational states. Without a common outcome semantics, such operations may be numerically well formed while lacking the interpretation attributed to them.

We call the missing condition **outcome commensurability**. Two outcome definitions are commensurable when they denote the same adverse event under the same observation process, observation-window semantics, and thresholds, while permitting different conditioning information. Under this formulation, a Change-family model and an Operational-family model may use different inputs and techniques but still predict the same outcome. For example, one model may estimate whether a predeclared runtime failure will occur after a deployment, while another estimates whether that same failure will occur given the current operational state. The distinction between the models lies in what they know, not in what their probabilities mean.

This paper introduces Isoprax, an implementation-independent conformance contract designed to make that distinction explicit. The contract unifies event ingestion, strategy execution, signal provenance, historical storage, outcome feedback, and evaluation obligations across the Change and Operational families. More importantly, it separates **Structural conformance** from **Semantic conformance**. Structural conformance establishes that both families can operate through the same contract. Semantic conformance additionally requires commensurable outcome definitions and calibrated probabilities before cross-family comparison is permitted.

The distinction is not merely terminological. A shared interface can successfully normalize events, execute strategies, persist signals, and calibrate outputs while still producing probabilities of different outcomes. Such an implementation has achieved structural interoperability but has not established semantic comparability. Isoprax makes this boundary explicit and requires implementations to report it rather than treating a shared score range as sufficient evidence of unification.

The reference implementation demonstrates this boundary using deliberately non-commensurable baseline outcome definitions. Both prediction families operate through the shared contract, but the implementation rejects pooled cross-family reporting and declares Structural conformance only. This is an intentional negative result: the system demonstrates that it can enforce the precondition for comparison rather than silently producing an invalid joint figure. The implementation does not claim real-world predictive superiority or Semantic conformance.

The same distinction constrains empirical validation. Established change-prediction benchmarks commonly derive labels from repository archaeology, such as fix-linkage heuristics, while operational benchmarks derive labels from runtime observations. Joining records from these sources may establish a relationship between changes and incidents, but it does not automatically make their outcome definitions equivalent. We therefore distinguish real-data Structural validation from Semantic validation and identify deterministic replay under a shared observation process as a concrete route to constructing the latter. Because such a corpus is self-constructed, its admission criteria, outcome definitions, thresholds, observation windows, censoring rules, and evaluation plan must be declared before acquisition and preserved as auditable evidence.

### Contributions

This paper makes four contributions:

1. **A cross-family conformance contract.** We formalize a shared, implementation-independent structure for Change-family and Operational-family prediction, without prescribing a particular model, programming language, storage system, or deployment architecture.

2. **Outcome commensurability as a necessary condition.** We distinguish probability calibration from outcome equivalence and formalize the conditions under which scores from different prediction families may be interpreted and compared as probabilities of the same event.

3. **A Structural/Semantic conformance distinction.** We define separate conformance claims for shared-contract interoperability and meaningful cross-family comparability, making the latter conditional on explicit outcome definitions and calibration evidence.

4. **A reference implementation and evidence boundary.** We demonstrate the shared contract and its refusal to pool non-commensurable scores, and define a staged validation path that separates synthetic structural evidence, real-data admission and evaluation, and future shared-outcome Semantic validation.

The contribution is not a new defect predictor, anomaly detector, calibration algorithm, or claim of improved predictive accuracy. It is a contract and an interoperability argument: **a common prediction interface does not establish a common predicted outcome, and calibration cannot supply the missing semantics.**

## 2. Related Work and Positioning

We organize the relevant literature around four separable questions rather than treating all prior work as evidence for one claim.

1. **Predictive methods.** JIT defect-prediction work, including JIT-Fine and ReDef, studies how code changes, representations, and model families support change-level risk prediction. JIT-Fine is also a useful reminder that defect prediction and defect localization can share inputs while targeting different units and decisions (Ni et al., 2022). ReDef is especially relevant to label quality and change semantics: its revert-anchored corpus and counterfactual probes test whether models respond to code modifications rather than superficial cues (Nam et al., 2026). These targets remain repository-derived defect labels, not runtime events observed after deployment.

2. **Evaluation and calibration.** Calibration and discrimination determine whether a model's score is useful as a probability or ranking signal relative to its declared target. They do not determine whether two targets are the same estimand. Data-splitting choices can materially affect reported AIOps performance, so the split protocol is itself part of the evidence boundary (Lyu et al., 2021). Interpretation adds a related but distinct concern: consistency across learners, samples, and time affects whether explanations are stable enough to support analysis (Lyu et al., 2022). Adaptation adds a temporal-validity concern: operational data evolve, and full-history versus sliding-window retraining can change the model's effective population and evaluation behavior (Poenaru-Olaru et al., 2024). Isoprax therefore treats calibration, split discipline, interpretation stability, and model-version/adaptation policy as evaluation evidence—not as cross-family label-equivalence tests.

3. **Outcome and label semantics.** Repository archaeology, revert evidence, and SZZ-style fix linkage are observation processes for constructing change-family labels. Their validity and noise properties are important, but they should not be silently equated with telemetry-defined operational outcomes. The relevant question for Isoprax is not which label source is universally superior; it is whether the source, window, threshold, censoring, and prediction-time rules define the same event for the proposed comparison.

4. **Cross-family evidence infrastructure.** The AIOpsLab vision paper describes design principles for autonomous-cloud evaluation and a prototype that orchestrates applications, fault injection, and agent interaction (Shetty et al., 2024). The subsequent AIOpsLab framework makes that infrastructure concrete: it deploys microservice environments, injects faults, generates workloads, exports telemetry, and evaluates agents (Chen et al., 2025). Isoprax is complementary rather than a replacement: AIOpsLab can supply an operational replay/evaluation environment, while Isoprax specifies the outcome-comparability contract, provenance requirements, and refusal rule for cross-family pooling.

The novelty claim is consequently narrow. We do not claim to introduce fault injection, telemetry collection, JIT prediction, calibration, or replay infrastructure. We claim an explicit contract boundary: those components may produce valid family-specific evidence without thereby establishing that their probabilities refer to a common outcome.

## 3. Problem Statement

Let a prediction strategy emit a score \(p \in [0,1]\) for an outcome \(Y\), conditioned on information \(X\). Calibration concerns the relationship between the stated probability and the observed frequency of \(Y\). For example, a calibrated strategy that assigns probability 0.8 should observe the corresponding event approximately 80% of the time among comparable predictions assigned that probability.

Now consider two strategies:

\[
p_C = P(Y_C = 1 \mid X_C)
\]

\[
p_O = P(Y_O = 1 \mid X_O)
\]

where \(C\) denotes the Change family and \(O\) denotes the Operational family. Both strategies may be calibrated relative to their respective outcomes. Nevertheless, calibration alone does not imply:

\[
Y_C \equiv Y_O
\]

If \(Y_C\) denotes a repository-derived defect label and \(Y_O\) denotes a runtime threshold crossing, the two probabilities refer to different events. Their numerical values may be compared arithmetically, but that comparison does not establish a common failure-risk interpretation.

The problem addressed by this paper is therefore not whether two models can emit probabilities in the same range. It is whether a system can determine, before permitting cross-family comparison, that those probabilities refer to commensurable outcomes.

## 4. Outcome Commensurability

An **Outcome Definition** specifies the event whose probability a score denotes. At minimum, it includes the adverse event, the observation process used to determine occurrence, the observation-window semantics, and any applicable thresholds.

Two Outcome Definitions are commensurable when they denote the same event under equivalent observation semantics, while allowing the prediction strategies to differ in their conditioning information. The contract requires this relationship to be declared and mechanically checked rather than inferred from the existence of calibrated scores.

This yields two independent obligations. First, the score must be calibrated relative to its declared outcome. Second, the outcome definitions must be commensurable. Neither obligation substitutes for the other. A perfectly calibrated score can still predict the wrong event for a proposed comparison, while a shared outcome definition does not make an uncalibrated score a reliable probability.

The contract consequently prohibits pooled ranking, aggregation, and cross-family threshold comparison when the outcome definitions are non-commensurable. Separately scoped reporting remains permitted. This is the central behavioral distinction between Structural and Semantic conformance.

## 5. Reference Implementation and Evaluation Boundary

The reference implementation is intended to demonstrate the contract rather than establish a new predictive-performance benchmark. Its baseline Change and Operational strategies emit signals through a shared interface, use common persistence and calibration machinery, and retain explicit outcome-definition provenance.

The baseline outcomes are deliberately non-commensurable. The implementation therefore withholds pooled cross-family figures and reports Structural conformance only. This behavior is the principal evidence for the contract's semantic gate: a structurally unified system can recognize that its scores do not support the stronger comparison claim.

Real-data validation and Semantic validation are treated as separate stages. Public change and operational datasets can exercise the contract under realistic label noise, class imbalance, and temporal variation, but their results remain separately scoped when their outcome definitions differ. A Semantic claim requires evidence that both families predict a common outcome under a shared observation process.

A concrete route is deterministic replay of code changes in an instrumented environment. The Change family predicts the occurrence of a predeclared runtime event after deployment, while the Operational family predicts that same event from an observed runtime state. Both labels are determined by the same observation semantics. The corpus-construction process must additionally preserve lineage, prediction-time information boundaries, censoring rules, frozen splits, and predeclared admission criteria so that the resulting evidence is auditable.

## 6. Limitations and Future Work

The present contribution establishes a conformance distinction and demonstrates its enforcement; it does not establish that a unified model improves predictive performance or that cross-family joint reasoning produces better operational decisions. Structural conformance is not Semantic conformance, and passing corpus-admission gates does not itself upgrade the conformance class.

The proposed deterministic-replay corpus remains a research objective. Its feasibility depends on historical build reproducibility, deployment and observation costs, sufficient positive-event counts, and the ability to preserve a single observation process across both prediction families. These constraints may limit corpus scale and the generality of any eventual Semantic evaluation.

Future work will evaluate the contract on real per-family datasets, construct and admit a shared-outcome replay corpus, and test whether commensurable Change and Operational signals can support meaningful joint reasoning. The central claim remains independent of those future results: **calibration alone cannot establish that two probabilities predict the same event.**

## References

- Chen, Y., Shetty, M., Somashekar, G., Ma, M., Simmhan, Y., Mace, J., Bansal, C., Wang, R., and Rajmohan, S. (2025). *AIOpsLab: A Holistic Framework to Evaluate AI Agents for Enabling Autonomous Clouds*. arXiv:2501.06706. https://arxiv.org/abs/2501.06706
- Lyu, Y., Li, H., Sayagh, M., Jiang, Z. M., and Hassan, A. E. (2021). *An Empirical Study of the Impact of Data Splitting Decisions on the Performance of AIOps Solutions*. ACM Transactions on Software Engineering and Methodology, 30(4), 1–38. https://doi.org/10.1145/3447876
- Lyu, Y., Rajbahadur, G. K., Lin, D., Chen, B., and Jiang, Z. M. (2022). *Towards a Consistent Interpretation of AIOps Models*. ACM Transactions on Software Engineering and Methodology, 31(1), Article 16, 1–38. https://doi.org/10.1145/3488269
- Ni, C., Wang, W., Yang, K., Xia, X., Liu, K., and Lo, D. (2022). *The Best of Both Worlds: Integrating Semantic Features with Expert Features for Defect Prediction and Localization*. Proceedings of the 30th ACM Joint European Software Engineering Conference and Symposium on the Foundations of Software Engineering (ESEC/FSE 2022), 672–683. https://doi.org/10.1145/3540250.3549165. Replication artifact: https://github.com/jacknichao/JIT-Fine
- Nam, D., Kim, T., Ryu, D., and Baik, J. (2026). *ReDef: Do Code Language Models Truly Understand Code Changes for Just-in-Time Software Defect Prediction?* FSE 2026 Research Papers. DOI: 10.1145/3808179. Preprint: arXiv:2509.09192. https://arxiv.org/abs/2509.09192
- Poenaru-Olaru, L., Karpova, N., Cruz, L., Rellermeyer, J. S., and Van Deursen, A. (2024). *Is Your Anomaly Detector Ready for Change? Adapting AIOps Solutions to the Real World*. Proceedings of the 2024 IEEE/ACM 3rd International Conference on AI Engineering—Software Engineering for AI, 222–233. https://doi.org/10.1145/3644815.3644961
- Shetty, M., Chen, Y., Somashekar, G., Ma, M., Simmhan, Y., Zhang, X., Mace, J., Vandevoorde, D., Las-Casas, P., and Mishra Gupta, S. (2024). *Building AI Agents for Autonomous Clouds: Challenges and Design Principles*. Proceedings of the 2024 ACM Symposium on Cloud Computing. DOI: 10.1145/3698038.3698525.
