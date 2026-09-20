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

The provenance must be supplied as a digest-backed `EvidenceProvenance` artifact
whose corpus and split identities match the profile; a caller-controlled evidence
class alone cannot produce a claim. Claimable profiles also preserve the 800-row,
50-positive, and 50-negative per-family evidence floor.

## Local verification snapshot

On 2026-09-20 in the Isoprax WSL workspace, the optional runtime reported PyTorch
2.14.0+cu130, CUDA available, and an NVIDIA GeForce RTX 5070 with `sm_120` support.
The CUDA smoke test completed successfully. The latest recorded full repository
suite, Ruff, formatting, and pre-commit gates are listed in the changelog. These are
implementation/runtime checks only. No Isoprax efficacy claim was made because no
independent labeled train/calibration/test corpus with verified provenance was
supplied.
