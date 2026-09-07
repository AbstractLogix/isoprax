# Public Validation Contract

`build_stage1_public_validation_report(apachejit_path, google_trace_path)`
MUST:

- verify source file identity and parse only the declared schemas;
- use one system per family;
- construct and admit chronological train, calibration-fit,
  calibration-gate, and test rows;
- fit calibration only on calibration-fit rows;
- preserve uncalibrated/inconclusive evidence;
- return deterministic aggregate metadata and no pooled metric.

It MUST NOT perform network I/O, include raw source rows in the report, or
upgrade the result to Semantic/Full Conformance.
