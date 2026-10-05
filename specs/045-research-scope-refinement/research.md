# Research Notes: IsoPrax Research-Scope Refinement

## Decisions

### Treat calibration as target-relative

**Decision**: Describe calibration as a property of forecasts together with the outcomes that materialize. Do not use calibration alone as proof that two forecasts refer to the same event.

**Rationale**: Gneiting, Balabdaoui, and Raftery distinguish calibration from sharpness and describe calibration relative to forecasts and observed outcomes. Proper scoring rules evaluate probabilistic forecasts for their declared targets. Applying these tools to a common numerical scale does not establish that two different targets are the same estimand.

**Alternative considered**: Treat a probability in `[0, 1]` as directly comparable across all models. Rejected because it skips the event and observation process that give the probability its meaning.

### Keep outcome and evidence commensurability distinct

**Decision**: Preserve the current structured `OutcomeDefinition` gate. Frame evidence commensurability as a research hypothesis that may contain several different problems rather than as a proven generalization.

**Rationale**: The repository gate compares event, observation process, window, and thresholds. The related calibration and outcome specs already state a bounded target. Other evidence types do not all describe probabilistic outcomes.

**Alternative considered**: Replace the existing model with a general evidence taxonomy now. Rejected because the user asks for a proposal and because the available evidence does not validate such a runtime abstraction.

### Assess a named operation, target, and context

**Decision**: Record operation-level permissions and uncertainty instead of one universal commensurability score.

**Rationale**: A pair can be comparable for one question but not safely pooled, averaged, or treated as independent. The allowed operation also depends on the estimand, population, temporal context, and evidence lineage.

**Alternative considered**: Adopt a universal ordinal status. Deferred until benchmark studies show that such a status is reliable and useful.

### Model dependence explicitly

**Decision**: Treat shared upstream observations and conditional dependence as first-class provenance questions for evidence combination. Do not equate different model identities with independent evidence.

**Rationale**: Shafer's analysis of Dempster's rule states that the rule is appropriate only when the belief functions are based on independent items of evidence, and recommends reframing dependent cases. This is a result about a specific combination rule, not a universal prescription for all evidence.

## Primary Literature and Scope

- [Gneiting, Balabdaoui, and Raftery, “Probabilistic forecasts, calibration and sharpness” (2007)](https://doi.org/10.1111/j.1467-9868.2007.00587.x): forecast verification distinguishes calibration and sharpness and uses proper scoring rules. It does not claim that forecasts for different events are comparable.
- [Gneiting and Raftery, “Strictly Proper Scoring Rules, Prediction, and Estimation” (2007)](https://doi.org/10.1198/016214506000001437): proper scoring rules assess probabilistic forecasts relative to their outcome distributions. It supports careful per-target evaluation, not a universal confidence scale.
- [Hébert-Johnson et al., “Multicalibration: Calibration for the (Computationally-Identifiable) Masses” (2018)](https://proceedings.mlr.press/v80/hebert-johnson18a.html): studies calibration across computationally identifiable subpopulations for fairness. It motivates subgroup diagnostics; subgroup calibration does not make different outcome definitions equivalent.
- [Van Bork et al., “A Causal Framework for the Comparability of Latent Variables” (2024)](https://doi.org/10.1080/10705511.2024.2339396): offers adjacent measurement-comparability research for latent variables. Its assumptions and methods do not transfer automatically to heterogeneous machine evidence.
- [Shafer, “The problem of dependent evidence” (2016)](https://doi.org/10.1016/j.ijar.2016.05.003): examines dependence in Dempster-Shafer belief-function combination and recommends reframing dependent evidence. It is a focused precedent, not a universal evidence calculus.
- [Ovadia et al., “Can You Trust Your Model's Uncertainty? Evaluating Predictive Uncertainty Under Dataset Shift” (NeurIPS 2019)](https://proceedings.neurips.cc/paper_files/paper/2019/hash/8558cb408c1d76621371888657d2eb1d-Abstract.html): benchmarks uncertainty and calibration under dataset shift. It motivates explicit population and shift context; it does not test cross-family outcome semantics.

## What the Literature Does Not Establish

The cited work does not establish that one general-purpose `CommensurabilityResult` can judge every evidence modality, nor that a finite evidence-family taxonomy is complete. It also does not establish that operation-specific assessment improves real deliberative decisions. These remain open hypotheses for public tests.
