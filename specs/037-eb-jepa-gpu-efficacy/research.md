# Research: EB-JEPA GPU Backend and Efficacy Gate

## Decision 1: Adapt the EB-JEPA shape, not the external repository

- **Decision**: Implement a small Isoprax-specific backend with separate change and
  state encoders, an action-conditioned predictor, an EMA target state encoder, and
  variance/covariance anti-collapse diagnostics. Do not copy the external repository
  or change Isoprax’s event contract.
- **Rationale**: The official EB-JEPA project presents representation learning,
  prediction, and planning examples, including action-conditioned video with an
  encoder, action encoder, predictor, regularizer, prediction loss, and inverse
  dynamics/time-similarity losses. Isoprax has normalized tabular/event windows, so a
  smaller adapter preserves the project’s minimal reference scope.
- **Source**: [official EB-JEPA repository](https://github.com/facebookresearch/eb_jepa)
  and [EB-JEPA paper](https://arxiv.org/abs/2602.03604).

## Decision 2: Make PyTorch optional and device selection explicit

- **Decision**: Put PyTorch behind an optional dependency and a lazy import. A
  requested CUDA device fails closed when `torch.cuda.is_available()` is false or
  initialization fails; CPU is only used when explicitly selected.
- **Rationale**: The base project must remain runnable without an accelerator. PyTorch
  documents `torch.cuda.is_available()` as the runtime availability check, and its
  deterministic-algorithm setting only guarantees deterministic algorithms where
  available, on the same software and hardware.
- **Source**: [PyTorch local installation](https://docs.pytorch.org/get-started/locally/),
  [`torch.cuda.is_available`](https://docs.pytorch.org/docs/main/generated/torch.cuda.is_available.html),
  and [`torch.use_deterministic_algorithms`](https://docs.pytorch.org/docs/main/generated/torch.use_deterministic_algorithms.html).

For NVIDIA Blackwell (`sm_120`) hosts, the selected wheel must include matching
architecture kernels. PyTorch 2.7 introduced Blackwell support in CUDA 12.8 wheels;
the backend checks the installed wheel’s architecture list before training and fails
closed when it is missing.

- **Source**: [PyTorch 2.7 release notes](https://pytorch.org/blog/pytorch-2-7/).

## Decision 3: Efficacy is a separate, fail-closed evidence decision

- **Decision**: Return `not_claimable` or `efficacy_supported` from a report that
  requires disjoint train/calibration/test row IDs, a named baseline, two observed
  classes per family, finite non-constant probabilities, predeclared thresholds, and
  a completed training run. Compare Change and Operational families separately.
- **Rationale**: A GPU run demonstrates implementation and runtime evidence, not
  predictive efficacy. Existing Isoprax calibration and per-family evaluation
  boundaries already distinguish evidence from claims and prohibit unsupported
  cross-family pooling.
- **Rejected**: Treating lower training loss, CUDA availability, calibration alone,
  or a synthetic smoke test as an efficacy claim.

## Decision 4: Do not install PyTorch as part of the base verification

- **Decision**: Add documented optional installation/verification commands, but keep
  the normal test path independent of PyTorch. Run the CUDA smoke test only when the
  environment already has a usable optional runtime or when explicitly installed by
  the operator.
- **Rationale**: CUDA wheel selection is platform/runtime-specific and can be large;
  silently changing the base environment would weaken reproducibility and obscure the
  distinction between a repository implementation and a host-specific GPU result.
