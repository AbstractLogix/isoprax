# Research: Complete Stage 1 Public-Data Validation

## Selected sources

- ApacheJIT Zenodo record `10.5281/zenodo.5907002`, CC-BY-4.0. The record
  publishes `apachejit_total.csv` and identifies the `buggy` label as whether
  a commit introduced a bug. The adapter selects Apache Ignite to preserve the
  single-system admission boundary.
- Google Cluster Trace v1 documentation and CSV, CC-BY. The trace documents
  task observations with relative timestamps, ParentID, task identifiers, job
  type, normalized cores, and normalized memory. The adapter derives a
  predeclared later-resource-threshold outcome from repeated task observations.

## Decisions

- Raw source files are downloaded by the operator and never checked into Git.
- The report records SHA-256 hashes in addition to the published source
  checksum/identifier.
- Apache calibration results are not repaired after seeing the gate result. If
  temporal drift causes ECE to exceed 0.05, the report remains uncalibrated.
- The Google outcome is explicitly named as a resource-threshold event; it is
  not silently mapped to the existing job-failure definition.

## Remaining limitations

- The sources do not share an observation process, so Stage 1 cannot support a
  Semantic cross-family claim.
- The report is a bounded public-data structural validation, not a model
  comparison or production efficacy study.
