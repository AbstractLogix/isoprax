# Evidence Commensurability: Research Specification

**Status**: Research hypothesis. This document does not define a new normative runtime rule.

## Research question

When may a system compare, rank, pool, average, jointly calibrate, or combine two evidence streams without changing what they mean?

The starting claim is narrow: a numeric score or probability does not by itself identify a shared target. The broader proposal—that one evidence-commensurability framework can assess all evidence types—is unproven.

## Scope

Study predictions, observed outcomes, and evidence streams that may come from:

- probabilistic predictors and their calibration records;
- deterministic tests and static-analysis results;
- formal verification results;
- telemetry and direct human observations;
- model-generated critiques, retrieved documents, or world-model predictions.

These items can differ in type and role. A test pass, a proof, a forecast, and an analyzer warning must not become interchangeable because each can be assigned a number.

IsoPrax studies measurement meaning and operation validity. It does not define how a deliberative runtime updates its beliefs or chooses an action.

## Provisional evidence dimensions

Use these as questions to record, not as a fixed or exhaustive taxonomy:

| Dimension | Questions |
|---|---|
| Target | What event, claim, construct, or property does the evidence concern? |
| Evidence form | Is it deterministic, probabilistic, learned, formal, human, or descriptive? |
| Measurement path | Was it observed directly, inferred, labeled, or derived from another record? |
| Time | What prediction time, observation window, horizon, censoring rule, and model version apply? |
| Population | Which system, subgroup, operating regime, and sampling process does it represent? |
| Provenance | What source, instrument, workflow, code, and transformation produced it? |
| Dependence | Does it share data, labels, code, model state, or upstream observations with other evidence? |
| Calibration | If probabilistic, for which target, population, and period was calibration evaluated? |
| Role | Is it predictive or retrospective, primary or secondary, structural or semantic? |
| Operation | Which exact comparison or combination is proposed, and for what estimand or decision? |

Do not collapse these dimensions into one global status or confidence value. An assessment may differ by operation.

## Candidate assessment record

For a research prototype or report, record:

1. the evidence items and their stable identities;
2. the target or estimand and its outcome definition;
3. the requested operation;
4. source, population, observation process, time window, threshold, censoring, and model version where relevant;
5. shared upstream observations and dependence assumptions;
6. the evidence that supports each assumption;
7. one operation-scoped result: allowed, conditional, disallowed, or unknown;
8. rationale, unresolved facts, and a limit on the conclusion.

These result words are provisional. Research must establish their definitions, reproducibility, and use before the project adopts them as public API terms.

## Research questions

1. When do two outcome definitions denote the same estimand?
2. Which operation needs identical outcomes, and which can use a declared transformation or mixture target?
3. Do event, observation process, time window, threshold, and censoring capture the important differences?
4. When does family-local calibration add information beyond global calibration?
5. How should population shift and calibration drift change an assessment?
6. How can shared source data, repeated observations, and derived evidence be identified?
7. Which combinations require conditional independence, and which can use an explicit dependence model?
8. Can deterministic, probabilistic, formal, and learned evidence support a common operation without becoming one scalar?
9. Is an operation-scoped categorical result more useful than a graded result?
10. What is the minimum metadata for each operation, rather than for all evidence in general?
11. Which questions are measurement findings and which are runtime policy choices?

## Study design

1. Define one target and operation per benchmark case.
2. Construct small counterexamples with known outcome definitions, source lineage, and dependence.
3. Add valid controls where targets are aligned or a mixture estimand is declared in advance.
4. Compare the proposed operation assessment with simple metadata-only rules and naive aggregation.
5. Measure false permission, unnecessary refusal, calibration by target, ranking change, decision loss, and review agreement where applicable.
6. Repeat the analysis across a changed population, observation window, and model version.
7. Report negative results and keep each conclusion within the tested operation and population.

Do not use one benchmark result to assert that all evidence types share a commensurability rule.

## Claim status

### Established in this repository

- The current `OutcomeDefinition` records an event, observation process, window, and thresholds.
- The current check rejects an event or observation-process mismatch. Window and threshold differences remain non-poolable until the stated bridge is actually applied.
- Calibration and outcome-definition compatibility are separate checks in the research argument.
- Current synthetic evidence is not real-world efficacy or Semantic/Full Conformance evidence.

See [the v0.3 reference](../isoprax-v0.3-poc.md), [the current scope audit](project-scope-and-architecture.md), and [the existing calibration/commensurability paper](Calibration%20Is%20Not%20Enough_%20Outcome%20Commensurability%20as%20a%20Precondition%20for%20Cross-Family%20Failure%20Prediction.md).

### Supported by adjacent literature

- Forecast calibration is assessed relative to forecasts and observed outcomes. Proper scoring rules evaluate declared probabilistic targets; they do not prove that different targets are the same. See [Gneiting, Balabdaoui, and Raftery (2007)](https://doi.org/10.1111/j.1467-9868.2007.00587.x) and [Gneiting and Raftery (2007)](https://doi.org/10.1198/016214506000001437).
- Multicalibration studies calibration across identifiable subpopulations. It supports subgroup diagnostics but does not establish equivalence between different outcome definitions. See [Hébert-Johnson et al. (2018)](https://proceedings.mlr.press/v80/hebert-johnson18a.html).
- Measurement comparability for latent variables offers a useful analogy for checking whether measures support group comparisons. Its assumptions do not transfer automatically to arbitrary machine evidence. See [Van Bork et al. (2024)](https://doi.org/10.1080/10705511.2024.2339396).
- Dempster-Shafer combination has explicit independence conditions; dependent evidence may require reframing. This does not define a universal rule for all evidence. See [Shafer (2016)](https://doi.org/10.1016/j.ijar.2016.05.003).
- Calibration under dataset shift is a separate evaluation concern. See [Ovadia et al. (2019)](https://proceedings.neurips.cc/paper_files/paper/2019/hash/8558cb408c1d76621371888657d2eb1d-Abstract.html).

### New hypotheses

- Operation-scoped assessments may be more precise than one global commensurability label.
- Evidence provenance and dependence may be as important as evidence family.
- A shared model identity may create unjustified confidence in output comparability.
- A useful framework may need a mix of explicit categorical refusals and conditional approvals, rather than one graded scale.

These claims need the benchmark and experiment described in this research map. None is an established IsoPrax result.
