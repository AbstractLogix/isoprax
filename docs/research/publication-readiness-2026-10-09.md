# Publication readiness — 2026-10-09

## Required status

- `PAPER CLAIMS MECHANICALLY VERIFIED / NOT VERIFIED`: **PAPER CLAIMS MECHANICALLY VERIFIED**. The integrity runner passed for 36 registered claims and 17 numeric manuscript lines. Deliberately changed manuscript numbers, source bytes, and recorded artifact digests were rejected. A clean checkout at commit `a63e819` passed locked-environment installation, `--check-only`, all 16 focused integrity tests, and repository lint/format checks.
- `PUBLIC REPLICATION PACKAGE READY / NOT READY`: **NOT READY** for permanent public deposit. The four selected Bouleusis data records have an exact owner authorization and CC BY 4.0 license. The six-role model output files have no asserted reuse license and are outside that authorization. See the [rights audit](publication-rights-audit-2026-10-09.md).
- `INDEPENDENT SCIENTIFIC REVIEW COMPLETED / NOT COMPLETED`: **NOT COMPLETED**. The [adversarial review](adversarial-peer-review-2026-10-09.md) is internal. No independent external referee has reviewed the claims or case labels.
- `SUBMISSION CANDIDATE READY / BLOCKED`: **BLOCKED**. The candidate still needs a rights decision for model outputs, a persistent archive identifier, independent scientific review, author approval and title-page metadata, and final journal declarations.

Mechanical reproduction of the listed repository results is distinct from permission to deposit every artifact, independent validation, and readiness to submit.

## Proposed venue

**Provisional target: Empirical Software Engineering (Springer Nature).** The topic has a software-engineering measurement and reproducibility focus. Fit is uncertain because the flagship result is a synthetic contract demonstration rather than a field evaluation. The journal says the editor must assess full-manuscript suitability; send a scope inquiry before submission if the authors keep this venue.

Requirements checked against the [official submission guidelines](https://link.springer.com/journal/10664/submission-guidelines) on 2026-10-09:

- The abstract must have 150–250 words. The current abstract is within this range.
- Provide 4–6 keywords. The current paper has six.
- Include a title page with author names, affiliation, and a corresponding-author email.
- Use Word or LaTeX source. The current Markdown file is the auditable source, not a ready upload format.
- The journal uses single-blind review.
- Include the required Statements and Declarations, including funding, competing interests, data and materials, code, and author contributions. Mark inapplicable sections as required.
- Original research needs a Data Availability Statement. The journal strongly encourages public data deposit, encourages open licenses, and asks authors to ensure they have rights to deposit the data. A persistent data identifier is recommended for data citation.
- Generative AI use beyond copy editing must be disclosed in Methods or a suitable alternative. Human authors must verify and approve the final work. A draft disclosure is in the experimental protocol; author approval is still required.
- References use author-year citations and should include DOI links where available.

No separate artifact-evaluation badge or mandatory artifact-review gate was found on the public guideline page checked. Confirm any current editorial or special-issue requirements before submission.

## Readiness checklist

| Item | Status | Evidence or remaining work |
|---|---|---|
| Main manuscript scope stays on outcome meaning and operation support | Ready for review | Model-role work is companion research and is not used to claim real-world JIT/AIOps prediction performance. |
| Calibration and construct-validity novelty claims are bounded | Ready for review | The manuscript treats the premise as established background and claims only the proposed declaration contract and synthetic demonstration. |
| Mixture and decision comparisons are distinguished from direct pooling | Ready for review | The manuscript includes a named mixture counterexample and a separate common-utility decision example. |
| Four disputed forecast cases remain unresolved | Ready for review | `FP02`, `FP03`, `FP05`, and `FP06` remain excluded from positive policy-validity claims. |
| Quantitative tables and integrity lock | Mechanically verified | Tables were regenerated from pinned inputs. Three integrity-CLI mutation checks rejected a changed manuscript number, changed raw source bytes, and changed recorded digest. |
| Clean-checkout reproduction without private source repositories | Passed at `a63e819` | `uv sync --locked`, `uv run python scripts/paper_integrity.py --check-only`, focused integrity tests (16 passed), Ruff check, and Ruff format check passed. The integrity command makes no network or model calls. |
| Selected Bouleusis data permission | Ready within exact scope | Four listed files only; CC BY 4.0; original private source code excluded. |
| Six-role model output release basis | Blocked | Tev1 fine-tune terms and output reuse rights are not established by this audit. Do not extend the Bouleusis license to these files. |
| Third-party and secret screening | Partial | Deterministic pattern scan passes or fails with the integrity run; it cannot establish all privacy, copyright, or license rights. |
| Independent scientific review | Not complete | Internal adversarial review is not external peer review. Obtain independent review of novelty, constructs, and evaluator labels. |
| Persistent data identifier | Not complete | Deposit the approved release after rights scope is resolved, then record the DOI/identifier in the manuscript. |
| Submission file and declarations | Not complete | Create Word or LaTeX upload files, complete title page and declarations, and obtain author approval. |

## Three strongest unresolved criticisms

1. **No independent case or outcome adjudication.** Minimum evidence: a blinded set authored by an independent team, independently adjudicated target/process labels, positive semantic-bridge cases, negative deceptive-metadata cases, and frozen baseline decisions before running the rule.
2. **No field evidence for real JIT/AIOps target pairs.** Minimum evidence: a real dataset pair with independently reviewed event definitions, data collection and censoring processes, windows, populations, prediction times, and label adjudication; then evaluate a preregistered bridge on held-out data.
3. **Novelty and value beyond existing validity frameworks remain open.** Minimum evidence: independent related-work review plus a prospective comparison against construct-validity/measurement-invariance practice and the three simple policy baselines, reporting both false permission and unnecessary refusal on independently authored cases.

The reproducible synthetic counterexample supports the narrow claim that calibration summaries alone do not establish a common event. It does not resolve these three criticisms.
