# Isoprax: A Cross-Family Conformance Contract for Predictive Change-and-Failure Analysis

**Specification version:** 0.3 (Draft)
**Status:** Working Draft — soliciting feedback
**Document type:** Open specification (implementation-independent)

---

## Abstract

Just-in-Time (JIT) software defect prediction and AIOps operational-failure prediction are two mature but largely siloed research families. The former predicts whether a *code change* is defect-inducing; the latter predicts whether a *running system* is trending toward failure. They have developed in separate venues, with separate benchmarks, vocabularies, and tooling — yet they share a common abstract structure: ingest an event, compare it against historical outcomes using a technique appropriate to the data, emit a signal, and learn from the observed result.

This specification does **not** claim to invent that structure, nor the individual disciplines it depends on (calibration, time-sliced evaluation, feedback-driven learning) — all of which are established in the prior art cited herein. Its contribution is threefold: (1) the formalization of the shared structure as a single implementation-independent **conformance contract** spanning both families; (2) the position that **calibration is a necessary condition** for comparing signals across implementations and across families; and (3) the identification of **outcome commensurability as the second, independent necessary condition** — and the demonstration that calibration alone is insufficient without it.

The third point is the specification's sharpest claim, and it constrains the first two. Calibration is a property of a probability *relative to its own event definition*. A perfectly calibrated forecast of "this commit was later textually linked to a fix" and a perfectly calibrated forecast of "a threshold was crossed within this observation window" are both correct and remain incommensurable, because the mismatch is in **what is predicted**, not in **how well**. Cross-family scores are therefore comparable only when both families' outcomes are defined by the same observation process. A contract that required calibration alone would license comparisons that are numerically tidy and semantically empty.

The goal is *semantic* interoperability — signals that mean the same thing — rather than merely *syntactic* interoperability — signals of the same shape.

This specification mandates no particular machine-learning technique, storage technology, programming language, or integration.

---

## 1. Terminology and Conventions

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in RFC 2119.

Sections or statements marked *(non-normative)* are explanatory and impose no conformance requirement.

### 1.1 Defined Terms

- **Implementation** — any software system claiming conformance to this specification.
- **Family** — one of the two predictive problem domains this contract unifies: the **Change family** (JIT defect/change-risk prediction) and the **Operational family** (AIOps failure/anomaly/capacity prediction).
- **Event** — a normalized record of something that occurred, conforming to one of the event schemas in Section 4.
- **Strategy** — a pluggable analytical component that consumes events and historical context and emits a Signal (Section 5).
- **Signal** — the output of a Strategy: a calibrated assessment with an associated explanation.
- **Knowledge Base (KB)** — the store of historical events, signals, and outcomes (Section 6).
- **Outcome** — the observed real-world result following a Signal, recorded to enable learning (Section 7).
- **Outcome Definition** — the declared specification of *which event* a Signal's score is a probability of: the event, the observation process that detects it, the observation window, and any thresholds. Distinct from the Outcome itself, which is one observed instance (Section 5.6).
- **Commensurable** — two Outcome Definitions are commensurable when they denote the same event detected by the same observation process under the same window and thresholds, differing only in what conditions the prediction. Scores are comparable only across commensurable Outcome Definitions (Section 5.6).
- **Calibration** — the property that a stated probability corresponds to observed empirical frequency, *relative to its own Outcome Definition* (Section 5.3).
- **Adapter** — a component translating a specific external system's data into normalized Events. Out of scope for conformance except as noted in Section 4.4.

---

## 2. Background and Relationship to Prior Work *(non-normative)*

This specification is deliberately built *on top of* an existing body of work rather than in competition with it. Understanding that foundation is essential to understanding what this contract does and does not claim.

### 2.1 The Change Family
JIT defect prediction predicts defect-inducing changes at commit time. The broader software-defect-prediction literature has, for decades, emphasized two problems this contract inherits directly: severe class imbalance (defective modules/changes are a small minority) and the inadequacy of single point-estimate accuracy comparisons, motivating rigorous statistical evaluation (the Khoshgoftaar et al. line of work on feature selection, class imbalance, and statistical testing in defect prediction; and the JIT-specific lineage including JITLine, JIT-Fine, and JITBot). More recent work applies pretrained code representations and few-shot / interpretable methods to the same problem.

### 2.2 The Operational Family
AIOps failure management is a mature, surveyed field. Recent surveys catalog the full pipeline (anomaly detection, root-cause analysis, remediation), increasingly in the context of large language models (e.g., the 2024 J.ACM *Survey of AIOps for Failure Management in the Era of Large Language Models*). Open platforms and benchmarks exist (e.g., AIOpsLab; large-scale real-world AIOps benchmark datasets; microservice failure-diagnosis benchmarks), though standardized, reproducible evaluation of *remediation effectiveness* remains an acknowledged gap.

### 2.3 The Established Disciplines This Contract Elevates
Three practices this contract makes *normative* are **not novel to this specification** and are credited as prior art:

- **Time-sliced evaluation / non-stationarity.** The impact of data-splitting decisions on AIOps model performance is an established empirical result (Lyu, Sayagh, Jiang, Hassan et al., ACM TOSEM 2021), as is the challenge of adapting anomaly detectors to distribution change ("Is Your Anomaly Detector Ready for Change?", 2023). Reproducibility and randomization concerns in predictive software engineering are likewise documented (Liem & Panichella, 2020).
- **Consistent / reproducible model interpretation.** Controlling randomness from learners, hyperparameter tuning, and data sampling to obtain consistent interpretations is established (Lyu, Rajbahadur, Lin, Chen, Jiang, "Towards a Consistent Interpretation of AIOps Models," ACM TOSEM 2021).
- **Calibration reporting.** Reporting calibration (reliability curves, Brier score) alongside discrimination is standard practice in clinical machine learning reporting guidelines and general ML reproducibility recommendations.

### 2.4 The Gap This Contract Addresses
Across the surveyed prior art, the two families remain **disjoint**: separate venues, separate benchmarks, separate vocabularies. Existing benchmarks and platforms are almost exclusively *operational-only* or *code-only*; none provides a single conformance target under which a risky commit and a failing job are instances of one contract, comparable on equal terms. This specification addresses precisely that gap. Its novelty is unification and the interoperability argument — not the constituent disciplines.

---

## 3. Scope and Conformance Overview

### 3.1 In Scope
1. The normalized cross-family event model (Section 4).
2. The Strategy interface contract and Signal output (Section 5).
3. The knowledge-base data contract (Section 6).
4. The outcome/feedback contract (Section 7).
5. The behavioral obligations: calibration (5.3), evaluation discipline (8), and feedback (7).

### 3.2 Out of Scope
- The internal algorithm of any Strategy (rule-based, statistical, ML, or LLM-based are all permitted).
- Storage technology, provided the KB contract is met.
- Wire protocol or transport between components.
- User interface or notification channel.
- Adapter internals for specific external systems.

### 3.3 Conformance Classes *(normative)*
The classes are strictly nested: Full ⊃ Cross-Family (Semantic) ⊃ Cross-Family (Structural) ⊃ Core. An Implementation MUST declare the highest class it satisfies, together with the calibration qualifier defined below.

- **Core Conformance** — satisfies all MUST requirements in Sections 4–7 for at least one event type and one Strategy type within a single Family.
- **Cross-Family Conformance (Structural)** — satisfies Core Conformance for at least one Strategy type in *each* Family (Change and Operational), demonstrating that the same contract, knowledge base, and calibration machinery govern both.
- **Cross-Family Conformance (Semantic)** — satisfies the Structural class *and* the outcome-commensurability requirement of Section 5.6: both families' Outcome Definitions are commensurable, so scores from the two families denote probabilities of the same event and may be compared, thresholded, and jointly reasoned about.
- **Full Conformance** — satisfies Cross-Family Conformance (Semantic) for all three Strategy types, emits calibrated scores meeting the objective test in 5.3, and satisfies the evaluation obligations in Section 8.

**The Structural/Semantic distinction is load-bearing, not bureaucratic.** An Implementation can route a commit-risk model and a job-failure model through one contract, calibrate both, and still be unable to compare their outputs — because the two models predict different events. Structural conformance is a real and useful achievement; it is *not* the unification this specification is ultimately about, and an Implementation MUST NOT describe Structural conformance as demonstrating cross-family comparability.

**Calibration qualifier.** An Implementation whose Signals are not demonstrably calibrated under 5.3 MUST append the qualifier *uncalibrated* to its declared class (e.g., "Cross-Family Conformance (Structural), uncalibrated"). This qualifier is mandatory, not cosmetic: it is how an honest early-stage Implementation accurately reports broad structural coverage without implying comparable scores. Semantic and Full Conformance are unavailable to an uncalibrated Implementation by definition.

An Implementation MUST document its conformance class, its calibration qualifier if applicable, the Outcome Definitions it uses per Family, and the event/Strategy types and Families it supports.

---

## 4. Normalized Cross-Family Event Model *(normative)*

### 4.1 General Requirements
All data entering a conforming Implementation MUST be represented as one of exactly three event types: **ChangeEvent** (Change family), **RunEvent** or **MetricSample** (Operational family). An Implementation MUST reject or coerce input that cannot be represented as one of these; it MUST NOT introduce a fourth top-level event type to bypass the contract.

Every event MUST carry:
- A globally unique identifier (`id`), stable across restarts.
- A timestamp (`timestamp`) in RFC 3339 format, UTC.
- A `source` string identifying the originating adapter or system.
- A `family` discriminator (`change` or `operational`).

Timestamps MUST NOT be used as identifiers. Two events with the same timestamp MUST have distinct `id` values.

**Family is determined by event type, not independently assigned.** ChangeEvent is always `change`; RunEvent and MetricSample are always `operational`. An Implementation MUST derive `family` from the event type rather than accepting it as independent input. Where `family` is carried explicitly (e.g., in a serialized representation or a stored record, so consumers can filter without type introspection), it MUST agree with the event type; an Implementation encountering a mismatch MUST reject the event rather than trusting the stated value.

*(Non-normative: `family` is redundant with the event type by construction. It is retained as an explicit field because the knowledge-base contract (Section 6) requires querying by family, and requiring every consumer to infer family from type would push that logic into every query path.)*

### 4.2 ChangeEvent (Change family)
Represents a unit of source-code change. MUST include `id`, `timestamp`, `source`, `family`, `repo`, `change_ref`; SHOULD include `author`, `files_touched`, `loc_added`, `loc_removed`; MAY include `linked_ticket_ids`, `ci_result`, `deploy_result`, `features`.

### 4.3 RunEvent and MetricSample (Operational family)
**RunEvent** represents a single execution of a job, task, or service invocation. MUST include `id`, `timestamp`, `source`, `family`, `job_type`, `exit_status`; SHOULD include `duration`, `resource_metrics`.

**MetricSample** represents one time-series observation. MUST include `id`, `timestamp`, `source`, `family`, `resource_id`, `resource_type`, `value`; SHOULD include `unit`.

### 4.4 Extensibility
An Implementation MAY attach arbitrary additional data through a single designated extensible field (`features` for ChangeEvent, `resource_metrics` for RunEvent, or an analogous namespaced map). Consumers MUST NOT be required to understand extension fields to process mandatory fields. Extension fields MUST NOT duplicate or override mandatory fields.

*(Non-normative: this is how stack-specific data travels through the contract without polluting the normative schema, and how two adapters from different ecosystems produce interoperable events.)*

---

## 5. Strategy Contract *(normative)*

### 5.1 Strategy Types
- **RiskStrategy** (Change family) — consumes a ChangeEvent plus historical context, emits a RiskSignal.
- **AnomalyStrategy** (Operational family) — consumes a RunEvent or MetricSample stream plus historical context, emits an AnomalySignal.
- **ForecastStrategy** (Operational family) — consumes MetricSample history, emits a ForecastSignal.

An Implementation supporting a Strategy type MUST accept the corresponding event type(s) and produce the corresponding Signal type.

### 5.2 Signal Output
Every Signal MUST include:
- `explanation` — a non-empty, human-readable justification referencing the factors driving the assessment. MUST NOT be a generic constant string.
- `strategy_id`, `strategy_version`, and `family` — for provenance and reproducibility.

**RiskSignal and AnomalySignal** MUST additionally include:
- `score` — a real number in [0, 1] denoting the probability that the adverse event occurs.
- `outcome_definition_id` — an identifier resolving to the Outcome Definition (5.6.1) that specifies *which* event the score is a probability of. A score without a resolvable Outcome Definition is uninterpretable and MUST NOT be emitted.

The `score` is governed by the calibration obligation (5.3) and is comparable across Implementations and across Families **only where the corresponding Outcome Definitions are commensurable** (5.6).

**ForecastSignal** MUST additionally include predicted value(s), a prediction interval, an `interval_confidence` (the nominal coverage of that interval, in [0, 1]), and a `technique` field naming the method actually used for that series.

A ForecastSignal MUST NOT carry a `score` field. `interval_confidence` is a coverage level, not an outcome probability: the two quantities answer different questions and are not interchangeable. An Implementation MUST NOT compare, threshold, or aggregate an `interval_confidence` against a RiskSignal or AnomalySignal `score` as though they were the same quantity.

*(Non-normative: this separation protects the claim in 5.3. If a "0.8" meant an 80% chance of failure in one Signal and 80% interval coverage in another, cross-family comparability would be nominal rather than real. Forecasts contribute to the contract through the events and outcomes they inform, not by emitting a probability on the same axis as the other two Signal types.)*

### 5.3 Calibration Obligation *(normative, behavioral)*
Calibration is the **first** of two necessary conditions for comparable Signals. It is necessary and *not* sufficient: calibration is a property of a probability relative to its own Outcome Definition, so calibrating two forecasts of different events yields two correct, incommensurable numbers. Section 5.6 supplies the second condition. Neither alone licenses cross-family comparison.

- A RiskStrategy or AnomalyStrategy claiming calibrated scores MUST satisfy the following objective test: on a held-out evaluation set of at least **500 outcome-labeled events**, binned into **10 equal-width score bins over [0, 1]**, the **Expected Calibration Error (ECE) MUST NOT exceed 0.05**, where ECE is the count-weighted mean absolute difference between mean predicted score and observed outcome frequency across non-empty bins.
- An Implementation MUST document the calibration method used (e.g., Platt scaling, isotonic regression, conformal prediction) and MUST expose the calibration diagnostic — the per-bin reliability data, the computed ECE, the Brier score, and the evaluation-set size — on request.
- An Implementation with fewer than 500 outcome-labeled events available, or whose ECE exceeds 0.05, MUST declare its scores **uncalibrated** in the Signal metadata. Such an Implementation MUST NOT claim Full Conformance, but MAY claim Core or Cross-Family Conformance with the uncalibrated qualifier (3.3). *(This relaxation exists so early-stage, small-data deployments can conform honestly rather than being defined out of the standard entirely — the failure mode this contract exists to prevent is a confident-looking uncalibrated score, not an openly declared one.)*
- The thresholds above (500 events, 10 bins, ECE ≤ 0.05) are the default conformance bar. A future revision or an accompanying conformance suite MAY refine them; an Implementation MUST report the parameters it evaluated against so that claims remain auditable.

*(Non-normative rationale: a substantial literature — from clinical-ML reporting guidelines to AIOps model-interpretation studies — establishes that bare classifier outputs and single accuracy figures are misleading and non-comparable. This contract's contribution is not that observation, but its elevation to a cross-family conformance requirement: without a common calibration semantics, a RiskSignal of 0.8 from one system and an AnomalySignal of 0.8 from another cannot be jointly reasoned about. Calibration is what makes the unification meaningful rather than cosmetic.)*

### 5.4 Technique Selection
A ForecastStrategy MUST select the technique appropriate to each series it forecasts and MUST report that technique in the ForecastSignal. The specification does not mandate *how* selection is performed (fixed classification, cross-validated model selection, or otherwise), only that the technique actually used is reported. An Implementation MUST NOT report a technique it did not use.

### 5.5 External Dependencies
A Strategy MAY depend on external services (including remote model APIs), but MUST declare any such dependency in its metadata. An Implementation MUST NOT make an external network call as a mandatory part of core event ingestion, normalization, or KB storage; external calls are permitted only within Strategies that have declared them.

*(Non-normative: this keeps the core contract satisfiable in air-gapped or zero-external-dependency deployments while still permitting LLM-augmented or hosted-model Strategies.)*

### 5.6 Outcome Commensurability *(normative, behavioral — the semantic keystone)*

A `score` is meaningless without a declared answer to "probability of *what*." This section makes that answer explicit and makes cross-family comparison conditional on it.

#### 5.6.1 Declaring the Outcome Definition
Every Strategy emitting a ProbabilitySignal (RiskStrategy, AnomalyStrategy) MUST declare an **Outcome Definition** comprising at minimum:

- `event` — the adverse event whose probability the score denotes, stated precisely enough to be independently evaluated.
- `observation_process` — the mechanism by which occurrence is detected (e.g., telemetry threshold evaluation; issue-tracker linkage; revert detection).
- `window` — the observation period, relative to the predicted-upon event, within which occurrence counts.
- `thresholds` — any parameters the observation process applies, where applicable.

Every ProbabilitySignal MUST carry an identifier resolving to its Outcome Definition, and every Outcome record (Section 7) MUST record the Outcome Definition under which it was determined. An Implementation MUST NOT record an Outcome against a Signal whose Outcome Definition differs from the one used to determine that Outcome.

#### 5.6.2 The commensurability test
Two Outcome Definitions are **commensurable** if and only if they share the same `event`, the same `observation_process`, the same `window` semantics, and the same `thresholds`. They MAY differ in what conditions the prediction — that is precisely the Change/Operational distinction — but MUST NOT differ in what is predicted.

An Implementation MUST evaluate this test mechanically rather than asserting it, and MUST expose the result.

#### 5.6.3 Comparison is conditional
An Implementation MUST NOT compare, threshold against one another, rank jointly, aggregate, or otherwise jointly reason over scores originating from non-commensurable Outcome Definitions, and MUST NOT present such scores as comparable to users. Where an Implementation surfaces scores from non-commensurable definitions in one view, it MUST label them as separately-scoped.

Calibrating both sides does not lift this prohibition. An Implementation MUST NOT cite calibration as grounds for comparing non-commensurable scores.

#### 5.6.4 Consequence for corpora
Because the commensurability test governs the *labeling process* and not the model, it constrains which datasets can support a Semantic conformance claim. In particular, a corpus whose Change-family labels are derived by issue-tracker or fix-linkage heuristics and whose Operational-family labels are derived from runtime telemetry thresholds is **structurally incapable** of supporting a Semantic claim, regardless of corpus size, model quality, or calibration effort — the two label sets denote different events.

*(Non-normative rationale: this is the specification's least intuitive and most consequential requirement. It is tempting to treat calibration as sufficient, because calibrated probabilities are directly comparable **within** an event definition and the arithmetic gives no warning when they are not. The failure is silent: two well-calibrated systems produce a tidy joint ranking that means nothing. Making commensurability a declared, mechanically checkable precondition is what converts the cross-family claim from notational to semantic. It is also why this specification treats a purpose-built corpus with a single shared labeling process as the only presently available route to a Semantic claim — see Appendix D.)*

---

## 6. Knowledge-Base Contract *(normative)*

Regardless of storage technology, an Implementation MUST:
- Retrieve events by `id` and query them by time range, by type, and by `family`.
- Preserve the association between an event, the Signal(s) produced for it, and any recorded Outcome.
- Support time-ordered retrieval to enable time-sliced evaluation (Section 8).
- Preserve extension fields (4.4) without silent loss.

These are capabilities, not a schema. Relational, document, and time-series stores are all permitted.

---

## 7. Outcome and Feedback Contract *(normative, behavioral)*

- For each Signal leading to a recommended action or gating decision, an Implementation MUST provide a mechanism to record the corresponding Outcome (whether the predicted condition occurred, and whether any action resolved it).
- An Outcome record MUST reference the originating event `id`, the Signal that prompted it, and the Outcome Definition (5.6.1) under which occurrence was determined.
- An Implementation MUST NOT use Outcomes determined under one Outcome Definition to calibrate or evaluate Signals emitted under a different, non-commensurable one.
- Recorded Outcomes MUST be available to Strategies as historical context.
- An Implementation providing no path for Outcomes to influence future Signals MUST NOT claim Full Conformance; a one-shot scorer with no feedback path MAY claim Core Conformance only and MUST disclose the absence of a feedback loop.

Collection method is unconstrained (manual entry, automated post-hoc correlation, notification reaction, or observed CI/deploy results all qualify).

---

## 8. Evaluation Discipline *(normative for Full Conformance)*

These obligations codify established prior-art findings (Section 2.3) as conformance requirements. When introducing or replacing a Strategy in a way that affects gating, blocking, or notification behavior, a Full-Conformance Implementation MUST:

1. **Use time-sliced validation.** Evaluation MUST use time-ordered train/test splits. Performance derived from randomly shuffled splits of temporally ordered data MUST NOT be reported as evidence of a Strategy's fitness. *(Established by Lyu et al. 2021 on data-splitting impact; this contract makes it a requirement rather than a recommendation.)*
2. **Report comparatively.** A Strategy change MUST be compared against the prior Strategy or a declared baseline using a paired statistical test or a calibration metric. A single accuracy or F-measure figure MUST NOT be the sole basis for an improvement claim.
3. **Support shadow operation.** A new or changed Strategy MUST be operable in a mode that emits Signals without triggering gating, blocking, or user-facing notifications, for evaluation prior to activation.
4. **Account for false positives.** An Implementation MUST track and be able to report the false-positive rate of each active Strategy.
5. **Report commensurability.** Any reported cross-family result MUST state the Outcome Definitions of both families and the outcome of the commensurability test (5.6.2). A cross-family comparison reported without this statement is not a conformant result. Where the definitions are non-commensurable, results MUST be reported per-family and MUST NOT be aggregated into a single cross-family figure.

---

## 9. Security and Privacy Considerations *(normative)*

- An Implementation MUST NOT transmit source code, diffs, logs, or metric data to an external service except through a Strategy that has declared the external dependency (5.5), and only with deployer configuration permitting it.
- Event identifiers and author identities MAY constitute personal data; an Implementation SHOULD support pseudonymization of author fields where required by the deployer's jurisdiction.
- Extension fields (4.4) MUST receive the same confidentiality controls as mandatory fields.

---

## 10. Versioning and Evolution *(normative)*

- This specification is versioned; an Implementation MUST declare the version it targets.
- Backward-incompatible changes to normative event schemas or Strategy contracts MUST increment the major version.
- An Implementation encountering an event declaring a newer minor version SHOULD process the mandatory fields it understands and preserve unknown fields (per 4.4) rather than reject the event.

---

## Appendix A. Positioning and Contribution *(non-normative)*

The contribution of this specification is narrow and deliberate:

1. **Cross-family unification.** JIT defect prediction (Change family) and AIOps failure prediction (Operational family) are unified under one event → calibrated-signal → feedback contract, so that a risky commit and a failing job are instances of the same conformance target. To the authors' knowledge, existing benchmarks and platforms address one family exclusively; none provides this unified target.
2. **Calibration as the first necessary condition.** The specification argues, and enforces via conformance, that calibrated signals are necessary for comparing predictions across implementations and across families.
3. **Outcome commensurability as the second, independent necessary condition — and the demonstration that calibration alone is insufficient.** Calibration is a property of a probability relative to its own event definition. Two perfectly calibrated forecasts of different events are both correct and remain incommensurable, and the arithmetic gives no warning: the joint ranking looks tidy and means nothing. This specification makes the event definition an explicit, declared, mechanically checkable object, and makes cross-family comparison conditional on it (Section 5.6).

Point 3 is the sharpest claim and it constrains points 1 and 2. It also carries an uncomfortable corollary the specification states plainly (5.6.4): the existing public datasets in the two families cannot jointly support a Semantic cross-family claim, because their labels are produced by different observation processes. A contract that required calibration alone would have licensed exactly that unsound comparison.

The specification explicitly does **not** claim novelty for calibration, time-sliced evaluation, class-imbalance handling, feedback-driven learning, or the individual predictive techniques. These are drawn from and credited to the prior art (Appendix C). The novelty is in their unification, their elevation to a cross-family conformance contract, and the commensurability precondition that governs when that unification is semantic rather than notational.

## Appendix B. Design Rationale *(non-normative)*

Data-format standards alone do not make predictive systems comparable: two systems can emit identically-shaped scores that mean entirely different things. Calibration closes part of that gap and is widely assumed to close all of it. It does not. Calibration aligns a number with a frequency *within* an event definition; it is silent about whether two numbers describe the same event at all.

The contract therefore requires two independent things — calibration (5.3) and commensurability (5.6) — and splits the Cross-Family class accordingly (3.3). The Structural tier records the real engineering achievement of governing both families under one contract. The Semantic tier records the harder claim that the resulting scores can actually be compared. Keeping them separate prevents the most likely misuse of this specification: shipping a Structural implementation and describing it as cross-family comparability.

Both keystones are declared, mechanically checkable, and reported — assertions do not satisfy either.

## Appendix C. Related Work *(non-normative)*

The following are the principal prior-art anchors on which this specification builds. This list is representative, not exhaustive; a full bibliography accompanies the associated paper.

**Change family — defect and JIT prediction.**
- Khoshgoftaar et al. — foundational work on fault-prone module prediction, feature/attribute selection, class imbalance, and statistical testing in software defect prediction.
- JITLine (Pornprasit & Tantithamthavorn, 2021); JIT-Fine (2022); JITBot (Khanan et al., 2020) — just-in-time, commit-level defect prediction and CI integration.
- Recent few-shot / interpretable defect prediction (e.g., siamese-network approaches) and low-shot + class-imbalance surveys.

**Operational family — AIOps failure management.**
- *A Survey of AIOps for Failure Management in the Era of Large Language Models* (J.ACM, 2024) — pipeline taxonomy: anomaly detection, RCA, remediation.
- AIOpsLab — open platform for building and evaluating AIOps agents; noted gap in standardized reproducible remediation evaluation.
- Large-scale real-world AIOps benchmark datasets (Li, Zhao, Zhang, Sun, Chen, Wen, Ma, Pei, 2022) and microservice failure-diagnosis benchmarks.
- Node-failure and job-termination prediction in large-scale cloud platforms (Lin et al. 2018; Li et al. 2020; trace-driven job-termination studies).

**Cross-cutting evaluation, calibration, and reproducibility discipline.**
- Lyu, Sayagh, Jiang, Hassan et al. (ACM TOSEM 2021) — impact of data-splitting decisions on AIOps solution performance.
- Lyu, Rajbahadur, Lin, Chen, Jiang (ACM TOSEM 2021) — consistent interpretation of AIOps models.
- "Is Your Anomaly Detector Ready for Change? Adapting AIOps Solutions to the Real World" (2023) — non-stationarity / distribution change.
- Liem & Panichella (2020) — randomization and reproducibility in predictive software engineering.
- Clinical-ML reporting guidelines and general ML reproducibility recommendations — calibration reporting via reliability curves and Brier score; standardized reporting criteria (e.g., McDermott et al.'s reporting items including model calibration).
- Conformal prediction as a distribution-free calibration layer applicable across regression, classification, and anomaly detection.

**Public datasets, and their limits under the commensurability test (5.6).**

These are usable for *Structural* validation. None of them, alone or in combination, can support a *Semantic* cross-family claim — the reason is label semantics, not size or quality, and it is not repairable by calibration.

- *Change family:* ApacheJIT (Keshavarz & Nagappan, MSR 2022) — 106,674 Apache commits (28,239 bug-inducing / 78,435 clean), SZZ-labeled, with a purpose-built time-ordered train/test split; released on Zenodo. ReDef (2025) — revert-based, function-level, higher label precision, as a lower-noise secondary set.
  - **Limit:** SZZ labels the event *"a commit later textually linked to a fix."* That is a repository-archaeology event, not a runtime event. ApacheJIT remains valuable as a Change-family reference point and a baseline comparison target, and is retained for those purposes; it cannot be paired with telemetry-labeled operational data to make a Semantic claim.
- *Operational family:* Google Cluster Trace, Backblaze Disk Stats, and Alibaba GPU Cluster Trace — the three canonical public AIOps datasets, notably the same three used by the Lyu et al. AIOps studies above, enabling direct comparability with that line of work. Google Cluster Trace supports the standard job-failure-prediction task (predict final "fail" state from submission + early-execution features).
  - **Limit:** these traces contain no code changes. There is no Change-family event to condition on, so no configuration, authorization, or enrichment can make them contribute to a Cross-Family claim. This is a structural exclusion for cross-family purposes, not a resourcing gap — they remain fully valid for Operational-family work.
- *Cross-family linkage (no open dataset; industrially demonstrated):* Amazon Prime Video deployment-risk study (2026) links post-incident Correction-of-Error reports to root-cause commits (proprietary). Multiple 2024–2026 patents cover change-to-incident linkage mechanisms. Publicly, Google service-status incident collections (≈979 incidents / 191 services, with per-incident time-to-repair) plus corresponding open-source git histories provide raw material for construction.
  - **Limit even here:** a constructed corpus that joins fix-linkage change labels to telemetry incident labels inherits the same non-commensurability. Linkage solves *pairing*; it does not solve *shared label semantics*. A Semantic claim requires both families' labels to come from one observation process — which is why Appendix D.3 specifies deterministic replay rather than record linkage.

## Appendix D. Validation Roadmap and Future Work *(non-normative)*

This specification is accompanied by a reference implementation and is intended to be validated empirically in stages. The stages are defined here so the contribution's current scope is explicit and its trajectory is on record. Claims in the associated paper are bounded to the stage actually completed at time of writing.

The staging is shaped by Section 5.6. Structural validation is reachable with existing public data; Semantic validation is not reachable with any presently available public corpus, and the roadmap says so rather than blurring the two.

### D.1 Stage 0 — Contract proof (complete)
A reference implementation demonstrates that a Change-family Strategy and an Operational-family Strategy emit Signals through one contract, persist to one knowledge base, and are calibrated through one shared mechanism, with time-sliced evaluation and paired significance testing. This establishes that the *structural* unification and the calibration mechanism are mechanically real.

It uses synthetic data with known ground truth, so it validates the plumbing and the argument, not real-world predictive performance. Notably, the reference implementation's two baseline Strategies use **non-commensurable** Outcome Definitions, and it therefore self-reports **Cross-Family Conformance (Structural)** rather than Semantic — a deliberate demonstration that the distinction bites even on the specification's own example.

### D.2 Stage 1 — Structural validation on real data (near-term, low-risk)
Replace synthetic generators with public datasets: ApacheJIT (Change family) and a canonical operational trace (Operational family). This exercises the contract under conditions synthetic data cannot reproduce — severe real class imbalance, real label noise (SZZ), and authentic non-stationarity across time-ordered splits.

**Scope, stated precisely.** This stage validates that one contract, one knowledge base, and one calibration mechanism govern both families on real data, and that each family's Signals are calibrated *relative to its own Outcome Definition*. It does **not** validate cross-family comparability, and no result from it may be reported as doing so: ApacheJIT's SZZ labels and telemetry-derived operational labels are non-commensurable under 5.6.2, so per 5.6.4 no Semantic claim is available from this pairing at any corpus size. Results are reported per-family, with the commensurability test result stated alongside (Section 8, obligation 5).

Success criterion: both families achieve calibrated Signals under the identical contract, improvements confirmed by paired significance tests, and the implementation correctly self-reports Structural — not Semantic — conformance. Using the same operational datasets as the established AIOps evaluation literature (Appendix C) keeps results comparable to that prior work.

### D.3 Stage 2 — Semantic validation via deterministic replay (research contribution)
The strongest form of the thesis upgrades the claim from "both families satisfy the same contract" to "both families predict the same event and can be reasoned about jointly." Section 5.6 makes the requirement for this exact: both families' labels must be produced by one observation process.

**Why record linkage is insufficient.** The intuitive approach — link commits to incidents in an existing system — solves pairing but not label semantics. A corpus joining fix-linkage change labels to telemetry incident labels remains non-commensurable and cannot support a Semantic claim. This holds regardless of linkage quality, and it holds for the proprietary industrial datasets that demonstrate the capability.

**Deterministic replay.** The route that satisfies 5.6 is to replay a public project's commit history through a self-operated, instrumented environment, deriving *both* families' labels from the same telemetry, in the same observation window, against the same predeclared thresholds. The Change family then asks whether a threshold was crossed after this change was deployed; the Operational family asks whether a threshold was crossed following this observed state. The predicted event is identical; only the conditioning differs. This is the structural justification for replay, and it is independent of — and stronger than — the practical argument that no paired public corpus exists. It stands even if a large paired corpus later becomes available, unless that corpus also derives both families' labels from one process.

**Method commitments.** Because the corpus is self-constructed, the credibility risk is that the corpus was shaped to fit the result. Three commitments address this, and each is verifiable by a third party rather than asserted:

- *Admission before acquisition.* The standard a corpus must meet is specified and frozen before any rows are collected, so it cannot be relaxed to fit whatever data proves obtainable.
- *Predeclaration with cryptographic ordering.* The analysis plan — thresholds, observation window, positive-event definition, censoring rule, split boundaries, adequacy floor, and ablation plan — is committed before collection. Ordering is proven by content-hashing the declaration and requiring its commit to be a **git ancestor** of every corpus-data commit (an executed check, not a recorded claim), with at least one external anchor independent of the project's own repository and clock. Commit timestamps are forgeable; ancestry is not.
- *Cost-ordered candidate screening.* Candidate projects are screened cheapest-disqualifier-first: commit supply, then licence and publication terms, then historical build rate, then metadata availability.

**Principal risk, stated honestly.** Corpus scale is the binding feasibility constraint, not specification completeness. Adequate positive-event counts imply commit volumes in the thousands to tens of thousands, each requiring a build and a soak period in an instrumented environment. Sequential single-lane execution is likely infeasible on independent resources; the achievable corpus size under realistic parallelism and soak duration should be estimated before further specification work, since it may force a different strategy.

### D.4 Sequencing rationale
Stage 1 and Stage 2 are not the same claim at different scales — they are different claims. Stage 1 is low-risk and establishes Structural conformance on real data; it is achievable now and does not depend on Stage 2. Stage 2 is the only presently identified route to a Semantic claim, is higher-risk, and is gated on corpus construction and its feasibility.

The specification and its first paper rest on Stages 0–1 and claim Structural conformance only. Stage 2 is declared future work so the Semantic claim has a defined, referenceable path rather than being asserted prematurely — and so that the gap between the two is visible rather than papered over.

## Appendix E. Implementation Notes: Language and Accelerator Neutrality *(non-normative)*

The Strategy contract (Section 5) treats a Strategy's internals as a black box: the framework observes only its declared inputs, its Signal output, and its declared dependencies (5.5). A direct consequence is that Strategies are language- and accelerator-neutral — a ten-line rule-based Strategy and a GPU-accelerated deep-model Strategy satisfy the identical interface and are interchangeable behind it.

This neutrality is itself a testable property of the abstraction. A reference implementation is expected to be written in a language with a mature integration and data ecosystem (the framework core, adapters, knowledge base, and baseline Strategies are I/O- and orchestration-bound, not compute-bound, and benefit from ecosystem breadth over raw execution speed). However, a compute-intensive Strategy — for example, one performing GPU-accelerated inference over code-diff embeddings or a deep anomaly model — MAY be implemented in a high-performance systems language and accelerator stack (e.g., Mojo / MAX) while exposing a surface conforming to the RiskStrategy or AnomalyStrategy contract.

Demonstrating that such a Strategy drops in behind the same interface as a trivial baseline Strategy, with no change to the framework core, adapters, or KB, would serve as an empirical validation of the Strategy abstraction boundary. This is noted as a deliberate future validation exercise, not a requirement, and not a property the core framework depends upon.

## Appendix F. Open Issues *(non-normative)*

1. Whether to define a normative canonical serialization (e.g., a JSON encoding) in a companion document.
2. Whether to publish a conformance test suite, and whether passing it is required for a conformance claim. *(Strongly indicated: an unadopted, untestable spec is the primary risk to this work's credibility.)*
3. Whether to define a minimal cross-system federation profile for exchanging Signals between independent Implementations.
4. Whether a future revision should define an optional *Joint-Reasoning Conformance* class requiring demonstrated joint reasoning over Change and Operational Signals (e.g., correlating a deploy's RiskSignal with a subsequent AnomalySignal), upgrading the unification claim from "same contract" to "same reasoning substrate". This is gated on the Stage 2 dataset construction described in Appendix D.3 and is deliberately left out of the current normative conformance classes until that validation exists.
