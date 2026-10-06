# Convergence: Commensurability Experiments and Evidence

**Assessment date**: 2026-10-05

**Result**: The implementation meets the requirements in `spec.md`. No remaining in-scope implementation tasks were found.

## Requirement assessment

| Requirement | Evidence | Result |
|---|---|---|
| Correct the Feature 044 audit boundary and public ownership language. | The audit assesses tracked Feature 044 ancestry and names the later excluded working-tree paths. Semadmit and Bouleusis boundaries state implementation responsibilities without business-state assumptions. | Met |
| Execute Benchmark A and a same-target control. | The runner reports local calibration, a uniquely named 50:50 mixture estimand, its weights, allowed operations, and unsupported interpretations. | Met |
| Test one JEPA identity across family, horizon, and same-target cases. | The two mismatched cases remain unpooled. Target results include calibration, Brier, AUC where meaningful, counts, event rates, bootstrap intervals, and ranking behavior. Only the named same-target mixture is pooled. | Met |
| Compare four gate rules. | The fixed synthetic challenge set reports false permissions, unnecessary refusals, interpretation errors, rank changes, and selected-record changes under its stated top-20% rule. The report limits the conclusion to this authored set. | Met |
| Keep the Haskell oracle bounded and publish evidence classes. | The oracle source did not change. The evidence report separates repository results, literature, new synthetic findings, and remaining hypotheses, and answers all five requested questions. | Met |

## Verification

- Final runner output was reproduced byte for byte twice. Both outputs had SHA-256 `02d3642044768c47957221a1e615dc221baf248b97eb4a61c8d75fa8eca80fcd`.
- Focused research, JEPA, and Haskell-oracle tests: 42 passed, 1 skipped. The oracle differential test also passed when run with the built binary.
- Haskell oracle: offline build passed; six QuickCheck properties passed with 2,000 cases each; compile-fail check passed.
- Full Python suite: 594 passed, 4 skipped. The local run measured 94.33% repository coverage, below the 95% threshold, because this environment lacks the optional GPU extra and skips EB-JEPA module tests. CI installs that extra. Hosted checks must confirm the CI result before merge.
- New experiment modules measured 99% and 100% branch-aware coverage; changed-line coverage measured 99%. Repository-wide Ruff lint and format checks passed. Pre-commit's contract-test hook reported the local aggregate coverage shortfall; its other hooks passed. `git diff --check` and all relative links in research and Feature 046 Markdown passed.
- The baseline ancestry check passed. The separate Feature 044 qualification working tree and the Haskell oracle source remain unchanged.

## Remaining release checks

No product or research implementation gap remains in this feature. Required hosted CI, PR review, and merge remain release steps. The synthetic findings do not settle independent field performance; the report lists those hypotheses and the next research cases.
