# Data Model: Stage 2 Corpus Evaluation Gate

## CorpusEvaluationProfile

Immutable profile containing:

- predeclaration and feasibility-report identities;
- corpus row and revision membership;
- structured Change and Operational definitions;
- split policy and score-time boundary;
- minimum complete/positive/negative/sample thresholds;
- allowed evidence scope and published artifacts.

## CorpusEvaluationReport

Canonical report containing:

- selected, terminal, complete, censored, blocked, withheld, and excluded
  counts;
- split leakage and temporal-order results;
- per-family calibration, discrimination, score-variance, and sample evidence;
- commensurability and pooling decisions;
- gate statuses, report identity, and withheld-claim boundary.

Raw telemetry and private payloads are not part of the public report.
