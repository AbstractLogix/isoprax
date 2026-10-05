# IsoPrax Scope and Architecture Audit

**Review date**: 2026-10-05
**Scope**: Current tracked files and the visible Feature 044 working-tree additions.
**Code movement**: None. This document gives recommendations only.

## Public mission

IsoPrax is an open research and reference framework for studying measurement validity, calibration, outcome semantics, and the conditions under which predictions or evidence can be compared. Its central thesis is that calibration for each predictor does not prove that the predictors refer to the same event or support the same operation.

The research question is: **What does each output measure, and which operations on those outputs are valid under the stated evidence?** This is narrower than general AI trust and does not make IsoPrax a deliberation or orchestration system.

## What the current repository establishes

| Area | Repository evidence | Claim boundary |
|---|---|---|
| Normative reference | The vendored v0.3 POC, Stage 0 specifications, and shared Change/Operational types define the reference contract. | The current base example supports Structural conformance only. It does not establish Semantic or Full Conformance. |
| Outcome meaning | `isoprax/commensurability.py` compares structured event, observation-process, window, and threshold fields. Event or observation-process differences are irreducible under the current rule. | This is a bounded OutcomeDefinition check. It does not judge every evidence type or all conditions needed for every operation. |
| Calibration and evaluation | `isoprax/evaluation.py` and `isoprax/per_family_evaluation.py` provide calibration and per-family evaluation measures. | Calibration is relative to the declared target. An aggregate measure does not establish target equivalence. |
| Synthetic counterexample | `isoprax/evidence.py` and `examples/demo_cross_family.py` show that locally low ECE can coexist with a pooled ranking that changes family-local selection. | This is synthetic evidence. The seven-day and ninety-day windows must stay explicit; the fixture must not be read as proof about real systems. |
| Admission and lineage | `isoprax/admission.py`, `isoprax/corpus_assembly.py`, `isoprax/predeclaration.py`, `isoprax/replay_capture.py`, and Stage 1/2 reducers check declared prerequisites such as linkage, time boundaries, provenance, and usable labels. | These gates support evidence quality and replay feasibility. They do not upgrade a result to Semantic conformance or efficacy by themselves. |
| Public data | Dataset-specific verifiers and manifests cover AI4I, ApacheJIT, C-MAPSS, MetroPT-3, and the current Feature 044 GADFPD/RCAEval additions. | These are different source and outcome lanes. Their public availability does not make their labels commensurable. Feature 044 files are uncommitted in the inspected working tree; their checks were not rerun for this audit. |
| Shared predictor | `isoprax/jepa.py`, `isoprax/eb_jepa.py`, and `isoprax/efficacy.py` provide a bounded shared-predictor reference and gated evaluation path. | One model identity does not prove one outcome meaning. Existing synthetic or device checks do not prove predictive efficacy. |
| Provenance and reporting | `isoprax/normative.py`, `isoprax/evidence_reporting.py`, and the identity/anchor modules make citations and evidence scope inspectable. | Preserve the declared provenance boundary. Do not turn an unavailable or partial input into a pass. |

The current branch has uncommitted Feature 044 work. This audit read its GADFPD and RCAEval code, manifests, and feature artifacts. It did not rerun its tests or public-data verifiers. The report does not claim that those checks passed in this turn.

## Module recommendations

| Major module group | Disposition | Reason and next action |
|---|---|---|
| `events.py`, `signals.py`, `strategies.py`, `kb.py`, `commensurability.py` | **KEEP** | These implement the public, deterministic reference vocabulary and the current outcome-definition gate. Keep the normative v0.3 boundary. |
| `evaluation.py`, `per_family_evaluation.py`, `evidence.py` | **REFINE** | Keep the calibration and synthetic pooling examples. State the target and operation beside each aggregate. In particular, describe the 7-day/90-day fixture as two window-defined targets; qualify the “same-event” shorthand in the code description before using it to justify a broader claim. |
| `admission.py`, `corpus_assembly.py`, `public_corpus.py`, `predeclaration.py`, `replay_capture.py`, `replay_selection.py`, `replay_constraints.py`, Stage 1/2 evaluation and reporting | **KEEP** | These form reproducible research infrastructure for lineage, data leakage, admission, and replay. Keep their reports bounded to their stated evidence class. |
| Dataset verifiers in `ai4i2020.py`, `apachejit.py`, `nasa_cmaps.py`, `metropt3.py`, `gadfpd.py`, and `rcaeval.py` | **REFINE** | Keep as public, dataset-specific examples. Do not let their source-specific labels become a single benchmark by default. Revisit packaging only if the adapter set makes the normative package hard to use. No move is justified now. |
| `jepa.py`, `eb_jepa.py`, `efficacy.py` and Feature 036/037 | **KEEP** | Preserve the shared-model research slice. Present each target, horizon, calibration, and provenance separately. Use it to test the model-identity hypothesis, not as product orchestration. |
| `hermetic_runner.py`, public validation scripts, and evidence workbench | **KEEP** | These are bounded public research and reproduction tools. Keep external effects explicit and avoid claims that synthetic runner evidence is a real deployment result. |
| Existing specifications, dataset manifests, notebooks, research paper, and Stage 1/2 records | **KEEP** | These preserve research history and evidence boundaries. Link them from a research map instead of rewriting their original purpose. |
| Operation-level evidence assessment vocabulary | **EXTRACT CONCEPTUALLY** | Publish a neutral research contract for operation, target, assumptions, provenance, and rationale. Do not extract or copy private implementation code. |
| Any current module | **DEPRECATE** | None identified. No evidence shows that a major module is redundant or unmaintained. |
| Any current module | **MOVE TO PRIVATE PROJECT** | None identified. The reviewed code is public research or reference tooling. The private product roles are boundaries for future work, not a reason to move current code. |

## What IsoPrax should stop trying to be

IsoPrax should not own belief updates, hypothesis ranking, planning, experiment choice, tool selection, action, runtime trust policy, or product-specific orchestration. It should not turn every evidence source into a probability, or promise one confidence value across tests, proofs, model outputs, warnings, and observations.

It should also avoid presenting a public dataset as a shared end-to-end benchmark when it lacks the required same-system lineage or shared observation process. Do not grow acquisition or enforcement code merely because a private product may need it.

## Responsibility boundaries

- **IsoPrax** publishes measurement questions, outcome definitions, conformance rules, reproducible examples, benchmark methods, and the limits of each claim.
- **Semadmit** may operationalize mature, validated concepts in its private trust/admission/verification product. It owns product authentication, policy, enforcement, deployment, and production handling. IsoPrax publishes the neutral rule and test evidence, not Semadmit's implementation.
- **Bouleusis** may consume a bounded validity assessment when it reasons over evidence. It owns epistemic state, hypothesis management, search, planning, experiment selection, belief revision, and orchestration. IsoPrax does not choose conclusions or actions.
- **World-model/JEPA components** remain pluggable predictive methods. IsoPrax keeps only a public reference slice when it answers a stand-alone measurement or comparability question.

See the [Semadmit boundary](isoprax-semadmit-boundary.md) and [Bouleusis boundary](isoprax-bouleusis-boundary.md).

## Strongest current contribution

The strongest contribution is the combination of an explicit OutcomeDefinition, a fail-closed pooling boundary, calibration kept separate from target meaning, and reproducible evidence controls. The public-data and replay lanes make those rules inspectable. They are support for the research claim, not proof that all evidence types can be compared.

## Next research direction

Extend the current outcome-level question into an operation-level question: **For a named target and context, which operations on a specific pair or set of evidence are supported?** Test this first with synthetic counterexamples, then with public, well-provenanced data. Keep the broader “evidence commensurability” thesis open until it survives those tests.

## Next falsifiable experiment

Use one shared JEPA-style predictor identity to emit forecasts for two explicitly different outcome families and horizons. Check family-local calibration, pooled diagnostics, output ranking, and decisions. Add a same-target control. If model identity alone predicts which comparisons remain valid, or if operation checks never change interpretation or decisions on realistic cases, weaken or reject the proposed operation-specific contribution. See [the experiment protocol](shared-model-commensurability-experiment.md).
