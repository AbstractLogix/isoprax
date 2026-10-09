# Version 2 Policy Challenge: Reporting Corrigendum

**Date:** 2026-10-08

The frozen version 2 preregistration's final status sentence says that version 2 is “unscored.” This sentence is stale: the candidate-policy run was executed and its machine-readable result is preserved in `docs/experiments/operation-policy-challenge-v2-results.json` with SHA-256 `211cec206853b67f0debe1b8eb33280627dd3ad862c730664e5af492813ab975`.

The preregistration file is left unchanged because its SHA-256, `9b09e19909825a60002bc5fea9a48b4e231b148f7693142c01966f4f7fa33f36`, is part of the frozen result provenance. This corrigendum changes no cases, labels, code, metrics, or historical result.

Version 2 was scored after its input and policy artifacts were committed. It remains internally authored and has no outside review. Its four forecast cases FP02, FP03, FP05, and FP06 contain calibration revisions that do not match the score sources. Preserve their recorded outcomes, but do not use the forecast-family comparison to infer policy value. See the [independent review packet](operation-specific-policy-independent-review-packet-2026-10-08.md) and its separate, unscored version 3 proposal.
