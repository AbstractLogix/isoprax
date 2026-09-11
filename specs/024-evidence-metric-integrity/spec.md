# Feature Specification: Evidence Metric Integrity

**Feature Branch**: `024-evidence-metric-integrity`

## Summary

Align the pooling-harm evidence names and output with the metric actually
computed, and ensure the synthetic ranking fixture has distinct scores so its
selection result cannot be caused by identifier tie-breaking.

## Acceptance scenarios

1. Evidence fields and demo output consistently say macro precision.
2. The fixture produces unique scores within each family.
3. The fixture still shows low within-family and pooled ECE with positive
   top-k precision degradation.

## Claim boundary

This repairs synthetic evidence semantics only. It is not efficacy,
Semantic Conformance, or Full Conformance evidence.
