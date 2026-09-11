# Implementation Plan: Unified Commensurability Policy

Thread `Attestation` and `retained_observations` through
`require_commensurable` and `cross_family_report`. Use the canonical
`CommensurabilityResult.pooling_allowed` decision for pooled metric emission,
while retaining the direct/attested/bridgeable level in the report.
