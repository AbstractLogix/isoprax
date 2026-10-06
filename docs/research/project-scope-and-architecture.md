# IsoPrax Scope and Architecture Audit

**Review date**: 2026-10-05
**Scope**: Files tracked at base commit `38cfc27` on `main`.
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
| Public data | Dataset-specific verifiers and manifests cover AI4I, ApacheJIT, C-MAPSS, and MetroPT-3. | These are different source and outcome lanes. Their public availability does not make their labels commensurable. |
| Shared predictor | `isoprax/jepa.py`, `isoprax/eb_jepa.py`, and `isoprax/efficacy.py` provide a bounded shared-predictor reference and gated evaluation path. | One model identity does not prove one outcome meaning. Existing synthetic or device checks do not prove predictive efficacy. |
| Provenance and reporting | `isoprax/normative.py`, `isoprax/evidence_reporting.py`, and the identity/anchor modules make citations and evidence scope inspectable. | Preserve the declared provenance boundary. Do not turn an unavailable or partial input into a pass. |

## Baseline and Feature 044 scope

The stated baseline, `38cfc27`, descends from the earlier Feature 044 merge `ab37efe` (`codex/044-ci-semantics-oracle`). Its tracked semantic types, conformance tests, and `haskell/semantic-oracle/` files are part of this audit. The Haskell oracle is classified below as a bounded independent check of public semantics.

The separate, uncommitted `codex/044-public-dataset-lane-qualification` work was not present in the `38cfc27` tree. Its new paths are `examples/gadfpd/`, `examples/rcaeval/`, `isoprax/gadfpd.py`, `isoprax/rcaeval.py`, `scripts/fetch_rcaeval_index.py`, `specs/044-public-dataset-lane-qualification/`, `tests/test_fetch_rcaeval_index.py`, and `tests/test_public_dataset_lane_qualification.py`. The working-tree edits to `examples/public-datasets/decision-ledger.json` and `scripts/verify_public_dataset.py` are also excluded; the baseline versions of those two tracked files remain in scope. This is a commit-state boundary, not a blanket exclusion of Feature 044.

## Module recommendations

| Major module group | Disposition | Reason and next action |
|---|---|---|
| `events.py`, `signals.py`, `strategies.py`, `kb.py`, `commensurability.py` | **KEEP** | These implement the public, deterministic reference vocabulary and the current outcome-definition gate. Keep the normative v0.3 boundary. |
| `evaluation.py`, `per_family_evaluation.py`, `evidence.py` | **REFINE** | Keep the calibration and synthetic pooling examples. State the target and operation beside each aggregate. In particular, describe the 7-day/90-day fixture as two window-defined targets; qualify the “same-event” shorthand in the code description before using it to justify a broader claim. |
| `admission.py`, `corpus_assembly.py`, `public_corpus.py`, `predeclaration.py`, `replay_capture.py`, `replay_selection.py`, `replay_constraints.py`, Stage 1/2 evaluation and reporting | **KEEP** | These form reproducible research infrastructure for lineage, data leakage, admission, and replay. Keep their reports bounded to their stated evidence class. |
| Dataset verifiers in `ai4i2020.py`, `apachejit.py`, `nasa_cmaps.py`, and `metropt3.py` | **REFINE** | Keep as public, dataset-specific examples. Do not let their source-specific labels become a single benchmark by default. Revisit packaging only if the adapter set makes the normative package hard to use. No move is justified now. |
| `jepa.py`, `eb_jepa.py`, `efficacy.py` and Feature 036/037 | **KEEP** | Preserve the shared-model research slice. Present each target, horizon, calibration, and provenance separately. Use it to test the model-identity hypothesis, not for runtime orchestration. |
| `haskell/semantic-oracle/`, `tests/test_haskell_semantic_oracle.py`, and Feature 044 CI integration | **KEEP** | Retain the small Haskell implementation as an independent differential check of public IsoPrax semantics. Do not expand it into runtime admission, trust, or verification enforcement. |
| `hermetic_runner.py`, public validation scripts, and evidence workbench | **KEEP** | These are bounded public research and reproduction tools. Keep external effects explicit and avoid claims that synthetic runner evidence is a real deployment result. |
| Existing specifications, dataset manifests, notebooks, research paper, and Stage 1/2 records | **KEEP** | These preserve research history and evidence boundaries. Link them from a research map instead of rewriting their original purpose. |
| Operation-level evidence assessment vocabulary | **EXTRACT CONCEPTUALLY** | Publish a neutral research contract for operation, target, assumptions, provenance, and rationale. Do not copy implementation code from another project. |
| Any current module | **DEPRECATE** | None identified. No evidence shows that a major module is redundant or unmaintained. |
| Any current module | **MOVE TO ANOTHER PROJECT** | None identified. The reviewed code serves the public research or reference scope. Project responsibility boundaries do not require a code move. |

## What IsoPrax should stop trying to be

IsoPrax should not own belief updates, hypothesis ranking, planning, experiment choice, tool selection, action, runtime admission policy, or deliberation orchestration. It should not turn every evidence source into a probability, or promise one confidence value across tests, proofs, model outputs, warnings, and observations.

It should also avoid presenting a public dataset as a shared end-to-end benchmark when it lacks the required same-system lineage or shared observation process. Keep acquisition and enforcement outside IsoPrax unless a public research requirement justifies them.

## Responsibility boundaries

- **IsoPrax** publishes measurement questions, outcome definitions, conformance rules, reproducible examples, benchmark methods, and the limits of each claim.
- **Semadmit** owns runtime admission and verification enforcement. It may operationalize mature IsoPrax concepts in its runtime policies and checks. IsoPrax publishes the neutral rule and evidence; it does not specify Semadmit's implementation.
- **Bouleusis** owns deliberation and epistemic-state behavior, including hypothesis management, search, planning, experiment selection, belief revision, and orchestration. It may consume a bounded validity assessment; IsoPrax does not choose conclusions or actions.
- **World-model/JEPA components** remain pluggable predictive methods. IsoPrax keeps only a public reference slice when it answers a stand-alone measurement or comparability question.

See the [Semadmit boundary](isoprax-semadmit-boundary.md) and [Bouleusis boundary](isoprax-bouleusis-boundary.md).

## Strongest current contribution

The strongest contribution is the combination of an explicit OutcomeDefinition, a fail-closed pooling boundary, calibration kept separate from target meaning, and reproducible evidence controls. The public-data and replay lanes make those rules inspectable. They are support for the research claim, not proof that all evidence types can be compared.

## Next research direction

Extend the current outcome-level question into an operation-level question: **For a named target and context, which operations on a specific pair or set of evidence are supported?** Test this first with synthetic counterexamples, then with public, well-provenanced data. Keep the broader “evidence commensurability” thesis open until it survives those tests.

## Next falsifiable experiment

The synthetic shared-model and operation-gate experiments now run. See the [experimental evidence report](experimental-evidence.md) for their results, evidence limits, and next questions.
