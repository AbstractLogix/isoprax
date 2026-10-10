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

From a clean public checkout with full Git history and no private credentials:

```sh
git clone https://github.com/AbstractLogix/isoprax.git
cd isoprax
git fetch origin refs/pull/56/head:refs/heads/review/flagship-56
git switch review/flagship-56
git rev-parse HEAD
uv sync --locked --group dev --extra gpu
uv run python scripts/flagship_paper_integrity.py
uv run python scripts/flagship_paper_integrity.py --check-only
uv run pytest --no-cov -q tests/test_flagship_paper_integrity.py tests/test_research_experiments.py
uv run pytest tests -q --cov-report=xml
```

Record the `git rev-parse HEAD` output as the validation commit for your review. The selected experiment sections existed at historical research commit `5d46abf27e2b15740090be0b6e389f44322a396f`; the standalone runner first appeared at `780edda34a0b0f396001ea43bd4085502a88c892`. Artifact SHA-256 values identify the checked-out file bytes. The validation commit is not embedded in the self-hashed registry. The first runner command regenerates the numeric summary and both tables. The check-only command verifies generated files and pinned inputs. The runner makes no network or model calls. The full test command requires Git history for existing repository ancestry checks.

## Independent-review invitation drafts — not sent

**Measurement-methodology researcher.** We invite an independent review of [PR #56](https://github.com/AbstractLogix/isoprax/pull/56) and this packet. Please compare its contribution with Freiesleben and Zezulka (2026), Qin (2026, arXiv v1), and ODCS plus a policy rule. Identify valid semantic or utility bridges that the proposed rule could refuse. The experiments are synthetic; please separate mechanical reproduction from scientific validity.

**Empirical software-engineering researcher.** We invite an independent review of [PR #56](https://github.com/AbstractLogix/isoprax/pull/56) and this packet. Please assess whether Benchmark A and the 23 internally authored cases support the claimed software contribution beyond ODCS plus a policy rule. Identify missing independent cases, observation-process checks, and field evidence needed before any JIT/AIOps application claim. Please flag unsupported wording or a mismatch between the manuscript and code.

## Requested independent review

1. Does the proposed contribution add value beyond existing measurement and estimand practice? Which claim, if any, needs narrowing or removal?
2. Which explicit semantic, horizon, observation, or utility bridges would make a comparison valid even when raw outcome fields differ? Does the proposal handle or clearly defer them?
3. Do the internally authored synthetic cases support the stated descriptive contribution? Which independently authored positive and negative cases are needed next?
4. Do the paper, code, and generated tables agree on what the public structural checker implements and what the synthetic operation rule tests?
5. Does any sentence imply field performance, real JIT/AIOps equivalence, Semadmit enforcement, or general value beyond the repository results?
6. What capability does IsoPrax implement that cannot already be obtained, with comparable effort and reliability, by combining established validity methodology with a general-purpose data contract and policy engine? Please compare the [focused related-work check](literature-citation-audit-2026-10-10.md) with the code. If the answer is none, say so and identify the smallest useful contribution claim.

Please separate manuscript-level criticism from recommendations for future field validation. Do not treat the model-role or retrieval studies as evidence for the flagship claims. Companion model-output rights remain unresolved; this packet requires no model output, model weight, or Bouleusis raw retrieval record.

## Readiness

The manuscript and reproduction package are ready for author review. It is not an empirically validated field study. External review remains pending. The three main unresolved objections and minimum evidence needed are in the adversarial review.

## Author-review checklist

- [ ] Confirm that the paper claims a structural pooling check and a separate synthetic operation-rule challenge, with no field efficacy claim.
- [ ] Review the exact manuscript tables, 24 flagship claim records, and limits in the adversarial review.
- [ ] Decide whether the focused related-work comparison supports any incremental contribution claim; do not treat the untested ODCS comparator as an established advantage.
- [ ] Record the PR head and CI run used for validation outside the self-hashed registry. If the branch history is rewritten or merged by squash, reassess the runner introduction commit and rerun the provenance test on the release ref.
- [ ] Request independent methods and empirical software-engineering reviews; record objections and author responses before a submission decision.
- [ ] Keep companion model outputs and their unresolved rights assessment outside the flagship evidence and any flagship data release.
