# External scientific review packet — 2026-10-09

## Review status

This packet is prepared for an external reviewer. No independent scientific review has yet occurred. Passing an integrity command shows that pinned files and registered calculations reproduce; it is not peer review or independent validation.

## Materials

- Main paper: `Calibration Is Not Enough_ Outcome Commensurability as a Precondition for Cross-Family Failure Prediction.md`
- Scope decision: `paper-scope-decision-2026-10-09.md`
- Companion outline: `model-role-companion-outline-2026-10-09.md`
- Claim registry: `paper-claims-evidence.json`
- Raw recomputation: `paper-recomputed-results.json`
- Raw-source digests: `../experiments/bouleusis-2026-10-08-raw/manifest.json`
- Counterexamples: `paper-counterexamples-2026-10-09.md`
- Adversarial review: `adversarial-peer-review-2026-10-09.md`
- Threats to validity: `threats-to-validity-2026-10-09.md`
- Publication rights: `publication-rights-audit-2026-10-09.md`
- Integrity protocol: `../../scripts/paper_integrity.py`
- Adversarial internal review: `adversarial-peer-review-2026-10-09.md`
- Cross-repository assurance summary: `cross-repository-assurance-evidence-2026-10-09.md`
- Publication readiness and current venue requirements: `publication-readiness-2026-10-09.md`
- Selected Bouleusis data authorization and license: `../experiments/bouleusis-2026-10-08-raw/README.md`

## Requested independent assessment

1. **Novelty:** Is the contribution an appropriate research contribution beyond established work on calibration, forecast pooling, measurement/construct validity, and typed contracts? Is the operation-specific contract the right novelty boundary?
2. **Constructs:** Are event, observation process, window, threshold, population, prediction time, and operation defined well enough to support the paper's argument?
3. **Case validity:** Do the synthetic cases test the stated hypotheses without making the candidate rule's own metadata the de facto oracle?
4. **Reference outcomes:** Are expected permissions, refusals, task outcomes, and label sources justified independently of candidate implementation behavior?
5. **Fair baselines:** Are naive aggregation, one global commensurability label, and metadata-only checks defined fairly? Are operation-specific conditions compared with equivalent metadata and costs?
6. **Statistics:** Are the sample units, bootstrap units, estimands, mixture weights, uncertainty summaries, and proper scores correct? Does exact replay get described without suggesting new-task replication?
7. **Counterexamples:** Can the checker falsely permit under incomplete but equal declarations? Can it unnecessarily refuse semantically equivalent declarations? Is the planned bridge evidence credible?
8. **Related work:** Is the targeted literature audit missing work on measurement equivalence, transportability, forecasting combination, prediction-task definition, or benchmark construct validity?
9. **Claims:** Does any conclusion exceed the repository result, synthetic fixture, or cited publication?
10. **Artifact access:** Can a reviewer reproduce the main paper without the private Bouleusis repository? Is authenticated access needed to assess the separate Bouleusis assurance record?

## Threats to validity

- The operation-rule challenge is finite, authored to probe the candidate conditions, and not independently adjudicated.
- The retrieval sweep's repeated seeds perturb order on one bug. The multi-bug study has 12 fixed cases and its cases share construction choices.
- Model-role runs replay the same fixed cases exactly. They are not independent task replications.
- Model-role labels are synthetic. Tev1's family calibration does not estimate natural question-family calibration.
- Equal-weight pooling applies only to the declared synthetic mixture and fixed weights.
- Model identities do not establish independent errors. Zero observed joint errors do not establish zero population joint-error risk.
- The conformance code checks structured declarations, not whether source measurement pipelines match their declarations.
- The four selected Bouleusis research-data files have an owner authorization and a separate CC BY 4.0 release record. This is not a source-code license and does not cover third-party materials.
- The Bouleusis assurance source is private. The selected raw research records and main-paper computations are packaged in IsoPrax, but an external reader cannot verify the full assurance record without authenticated access.
- Automated hash and calculation checks cannot validate constructs or novelty.

## Replication commands

Run these commands from a clean checkout with the locked Python environment:

```sh
uv sync --locked
uv run python scripts/paper_integrity.py --check-only
uv run pytest --no-cov tests/test_paper_integrity.py
uv run ruff check scripts/paper_integrity.py tests/test_paper_integrity.py
uv run ruff format --check scripts/paper_integrity.py tests/test_paper_integrity.py
git diff --check
```

The first integrity command recomputes public raw-record analyses, validates model and preregistration identities, checks the paper and claim registry, and compares regenerated tables. The run is local and makes no model calls or network requests.

## Reviewer checklist

- [ ] Confirm the proposed contribution is narrow enough relative to construct validity, measurement invariance, estimand alignment, and forecast combination.
- [ ] Evaluate the utility-comparison counterexample and whether the contract separates direct probability pooling from decisions under common utility.
- [ ] Check whether observation-process declarations are complete enough and whether the implementation can falsely permit or unnecessarily refuse cases.
- [ ] Assess whether the internally authored target and policy labels are valid independently of the candidate rule.
- [ ] Treat repeated trials of one bug, exact model replays, and bootstrap intervals on authored clusters as fixed-case evidence, not independent task replication.
- [ ] Confirm the different-target aggregate names its mixture estimand and is not described as a common event.
- [ ] Confirm the four calibration-revision forecast cases remain excluded from positive validity claims.
- [ ] Confirm that model-role and cross-repository assurance evidence do not support JIT/AIOps forecast performance or semantic equivalence.
- [ ] Identify what independently authored result would falsify the proposed operation-specific value claim.
- [ ] Record whether any review comments are independent human scientific review; automated tools do not qualify.

## Submission readiness

**Not ready as an empirically validated JIT/AIOps study.** The manuscript can be reviewed as a contract proposal with a synthetic demonstration. Before submission, the authors need independent novelty and construct review, blinded independently authored conformance cases, a semantic-bridge positive control, a persistent data identifier, and a decision on authenticated access to the separate Bouleusis assurance records. Do not claim external validation, field effectiveness, or a Semadmit operational rule.

The full replication package is not ready for permanent public deposit while the companion model-role outputs lack an asserted reuse license. The exact scope and other venue requirements are in `publication-readiness-2026-10-09.md`.
