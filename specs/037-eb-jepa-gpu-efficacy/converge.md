# Convergence

The implementation matches the feature contract: the optional PyTorch backend
supports explicit CPU/CUDA execution, shared learned state, EMA targets,
anti-collapse diagnostics, runtime device identity, and fail-closed host
architecture validation. Anti-collapse regularizers act on trainable predictor
outputs. The evaluator keeps Change and Operational results separate, converts
malformed evidence into machine-readable `not_claimable` reasons, and returns
`efficacy_supported` only for complete, disjoint, externally verified real-labeled
digest-backed evidence with a validated training report and canonical run
configuration. Claimable profiles preserve the protected 800/50/50 per-family
evidence floor.

All feature tasks are checked. Local validation includes the passing full-suite,
Ruff, formatting, and pre-commit gates recorded in the changelog, plus a passing
RTX 5070 (`sm_120`) CUDA smoke test with PyTorch 2.14.0+cu130. These are
implementation/runtime gates; real labeled held-out evidence is still absent, so
the current efficacy status remains `not_claimable` and no predictive efficacy
claim is made.
