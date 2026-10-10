# External reviewer packet — 2026-10-10

## Status

This packet is ready for an independent researcher. No independent scientific review has been completed. Automated tests and hashes show that the published calculations reproduce. They do not establish novelty, construct validity, or scientific correctness.

## Materials

- Manuscript: [Calibration Is Not Enough](Calibration%20Is%20Not%20Enough_%20Outcome%20Commensurability%20as%20a%20Precondition%20for%20Cross-Family%20Failure%20Prediction.md)
- Scope and dependency decision: [flagship scope](flagship-scope-decision-2026-10-10.md) and [dependency report](flagship-dependency-separation-2026-10-10.md)
- Evidence matrix: [36-claim registry](paper-claims-evidence.json), with 24 flagship claims and 12 companion-only claims
- Numeric recomputation: [recomputed result summary](paper-recomputed-results.json) and [generated tables](paper-recomputed-tables.md)
- Integrity runner: `scripts/flagship_paper_integrity.py`
- Citation audit: [targeted literature review](literature-citation-audit-2026-10-10.md)
- Adversarial review: [severity-ranked objections](flagship-adversarial-review-2026-10-10.md)

The paper uses no model output, model weights, or Bouleusis retrieval archive. Its exact required files are listed in the dependency report.

## Minimal reproduction

From a clean public checkout, with no private credentials:

```sh
uv sync --locked --group dev --extra gpu
uv run python scripts/flagship_paper_integrity.py
uv run python scripts/flagship_paper_integrity.py --check-only
uv run pytest --no-cov -q tests/test_flagship_paper_integrity.py tests/test_research_experiments.py
```

The first command regenerates the numeric summary and both tables. The check-only command verifies the generated files and pinned inputs. The runner makes no network or model calls. Run the full repository CI commands in the replication note if broader code review is required.

## Requested independent review

1. Does the software contract add a concrete contribution beyond construct validity, measurement invariance, and estimand definition?
2. Does the paper limit its refusal correctly to unsupported direct pooling while leaving room for explicit mixtures and decision comparisons under validated utility?
3. Are the outcome, observation-process, threshold, and window declarations sufficient to make the synthetic counterexample clear?
4. Are the 23 internally authored challenge cases useful as a descriptive demonstration, given that their expected labels were not independently adjudicated?
5. Does any sentence imply field performance, real JIT/AIOps equivalence, Semadmit enforcement, or general value beyond the repository results?

Please separate manuscript-level criticism from recommendations for future field validation. Do not treat the model-role or retrieval studies as evidence for the flagship claims.

## Readiness

The manuscript and reproduction package are ready for author review. It is not an empirically validated field study. External review remains pending. The three main unresolved objections and minimum evidence needed are in the adversarial review.
