# Research Inputs: Retrieval and Interpretation Dependence

## Primary source

Kinderman et al., [UNREAL: Unifying Retrieval and Long-Context with a Single Model, arXiv:2610.08463v1](https://arxiv.org/abs/2610.08463v1), submitted 6 October 2026.

The paper uses internal states from a frozen language model to select chunks, then uses the same model to generate an answer. It reports retrieval and answer-quality measures on the stated question-answering and long-context benchmarks. Its abstract and evaluation sections do not report the conditional selection/interpreter error measures proposed by this feature.

The paper is a preprint. This feature treats its reported results as evidence for the tested retrieval settings only.

## Repository context

Feature 046 reports synthetic outcome-commensurability experiments with one shared JEPA backend. That work found that model identity did not make different outcomes poolable in its fixtures. It also compared simple and operation-specific rules on an authored synthetic challenge set.

This is useful motivation for testing selector lineage. It is not a retrieval experiment and does not establish correlated selection and interpretation errors.

## Research gap

No result in the cited paper or current Feature 046 report measures whether retrieval and interpretation errors are dependent, whether selector identity adds value beyond source provenance, or whether a larger operation-specific policy beats held-out metadata rules for evidence selection.
