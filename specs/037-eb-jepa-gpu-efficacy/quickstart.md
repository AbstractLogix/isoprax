# Quickstart: EB-JEPA GPU Backend and Efficacy Gate

The base project remains usable without PyTorch:

```bash
uv run pytest -q
uv run ruff check .
```

To install the optional runtime, use the PyTorch command appropriate for the host
from [PyTorch Start Locally](https://docs.pytorch.org/get-started/locally/), then
verify the runtime explicitly:

```bash
uv pip install torch --index-url https://download.pytorch.org/whl/cu128
uv run python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

The repository’s focused optional tests use a CPU device when CUDA is unavailable.
Use `device="cuda"` only when the verification command reports CUDA available. A
successful fit is a runtime/implementation result; it is not an efficacy claim.

An efficacy run must provide disjoint train/calibration/test identifiers, a named
baseline, family-specific labels and probabilities, and a frozen evaluation profile.
Inspect `EfficacyReport.status` and `reasons`; `not_claimable` is the expected result
for synthetic, undersized, one-class, leaked, or otherwise incomplete evidence.
The profile defaults to `evidence_class="synthetic"`; set `evidence_class="real_labeled"`
only for a separately identified, access-controlled corpus with independent labels.

## Local verification snapshot

On 2026-09-20 in the Isoprax WSL workspace, the optional runtime reported PyTorch
2.14.0+cu130, CUDA available, and an NVIDIA GeForce RTX 5070 with `sm_120` support.
The CUDA smoke test completed successfully. The full repository suite completed with
392 passed, 1 skipped, and 95.38% total coverage; Ruff, formatting, and pre-commit
also passed. These are implementation/runtime checks only. No Isoprax efficacy claim
was made because no independent labeled train/calibration/test corpus was supplied.
