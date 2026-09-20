# Convergence

The implementation matches the feature contract: the optional PyTorch backend
supports explicit CPU/CUDA execution, shared learned state, EMA targets,
anti-collapse diagnostics, runtime device identity, and fail-closed host
architecture validation. Anti-collapse regularizers act on trainable predictor
outputs. The evaluator keeps Change and Operational results separate, converts
malformed evidence into machine-readable `not_claimable` reasons, and returns
`efficacy_supported` only for complete, disjoint, externally verified real-labeled
evidence with a validated training report and canonical run configuration.

All feature tasks are checked. Local validation includes 392 passing tests, one
expected skip, 95.38% total coverage, and a passing RTX 5070 (`sm_120`) CUDA
smoke test with PyTorch 2.14.0+cu130. These are implementation/runtime gates;
real labeled held-out evidence is still absent, so the current efficacy status
remains `not_claimable` and no predictive efficacy claim is made.
