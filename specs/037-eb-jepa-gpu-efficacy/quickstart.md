# Quickstart: EB-JEPA GPU Backend and Efficacy Gate

The base project remains usable without PyTorch:

```bash
uv run pytest -q
uv run ruff check .
```

To install the repository-pinned optional runtime, use the `gpu` extra and verify
the runtime explicitly:

```bash
uv sync --extra gpu
uv run python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

If the lockfile does not yet contain a wheel for a particular host, use the
host-specific command from [PyTorch Start Locally](https://docs.pytorch.org/get-started/locally/)
instead, then rerun the verification command. That host-specific install is an
environment override; update the project extra and lockfile before treating it as
the repository's reproducible runtime.

The repository’s focused optional tests use a CPU device when CUDA is unavailable.
Use `device="cuda"` only when the verification command reports CUDA available. A
successful fit is a runtime/implementation result; it is not an efficacy claim.

An efficacy run must provide disjoint train/calibration/test identifiers, a named
baseline, family-specific labels and probabilities, a validated completed
`EBJEPATrainingReport`, canonical run configuration, and a frozen evaluation profile.
Inspect `EfficacyReport.status` and `reasons`; `not_claimable` is the expected result
for synthetic, unverified, undersized, one-class, leaked, or otherwise incomplete
evidence. The profile defaults to `evidence_class="synthetic"`; set
`evidence_class="real_labeled"` only for a separately identified, access-controlled
corpus with independent labels and externally verified provenance.

## Local verification snapshot

On 2026-09-20 in the Isoprax WSL workspace, the optional runtime reported PyTorch
2.14.0+cu130, CUDA available, and an NVIDIA GeForce RTX 5070 with `sm_120` support.
The CUDA smoke test completed successfully. The full repository suite completed with
392 passed, 1 skipped, and 95.38% total coverage; Ruff, formatting, and pre-commit
also passed. These are implementation/runtime checks only. No Isoprax efficacy claim
was made because no independent labeled train/calibration/test corpus was supplied.
