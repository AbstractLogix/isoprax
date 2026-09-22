# Quickstart: Evidence-Bounded Dataset Examples

This is the runnable index for all four repository examples. AI4I 2020 is a
synthetic structural/label-semantics fixture; ApacheJIT is repository-derived;
C-MAPSS is simulated run-to-failure/RUL data; and MetroPT-3 relies on external
failure anchors. Each keeps its own schema and outcome definition. Feature 038
contains the detailed AI4I source and acceptance record.

The verifiers are intentionally local-only. Obtain each artifact yourself and
pass its local path; the checked-in manifests record the expected source and
identity for the included examples. The repository does not download or vendor
public datasets.

## AI4I 2020

Obtain the UCI artifact as described in the
[Feature 038 quickstart](../038-ai4i-structural-fixture/quickstart.md), then
verify the local CSV:

```bash
uv run python scripts/verify_ai4i2020.py /path/to/ai4i2020.csv
```

The pinned snapshot has 10,000 rows, 14 columns, and 339 composite machine
failures. The five mode labels are outcomes/diagnostics, not prediction inputs
for the composite label.

## ApacheJIT

```bash
uv run python scripts/verify_public_dataset.py apachejit \
  /path/to/apachejit_total.csv --json
```

The canonical snapshot should report 106,674 rows, 18 columns, 15 projects,
28,239 buggy rows, 78,435 clean rows, and SHA-256
`5097cbbbab8c4611a709b3cf95ac5c9fe5f62e619bab081911a2a247ddbed4e0`.
The JSON report also includes each project's positive yield (buggy commits / all
commits), including projects with a zero yield.

## NASA C-MAPSS

```bash
uv run python scripts/verify_public_dataset.py cmapss \
  --dataset FD001 \
  --train /path/to/train_FD001.txt \
  --test /path/to/test_FD001.txt \
  --rul /path/to/RUL_FD001.txt --json
```

Repeat for FD002 through FD004. The verifier checks the observed artifact,
not copied README trajectory counts.

## MetroPT-3

```bash
uv run python scripts/verify_public_dataset.py metropt3 \
  /path/to/MetroPT3\(AirCompressor\).csv \
  --intervals examples/metropt3/failure_intervals.json --json
```

The interval file is an external-anchor declaration. It supplies positive
coverage windows only; all other observations remain unlabeled/censored.
The UCI record supplies date/time values without a timezone. The manifest keeps
those values timezone-unqualified; the verifier compares them as written and
rejects timezone-qualified CSV timestamps or anchors rather than assuming UTC.

## Evidence boundary

A passing verifier proves the supplied artifact matches the declared structural
and provenance checks. It does not prove production behavior, causal failure
prediction, semantic conformance, or cross-family pooling. Use the decision
ledger and existing commensurability/evidence APIs before making any claim.

## Verified snapshot results

The downloaded artifacts were checked locally on 2026-09-22. The data files
remain outside the repository.

| Dataset | Verified observations | Identity/anchor result |
|---|---:|---|
| AI4I 2020 | 10,000 rows; 14 columns; 339 composite failures | CSV SHA-256 `dc6630cd9b1f0f853922fad78a1b6436570d3f1ec863f1dd5c4340ac56bc8a8e`; 27 composite/mode discrepancies and 24 multi-mode rows preserved |
| ApacheJIT | 106,674 rows; 15 projects; 28,239 buggy and 78,435 clean | SHA-256 `5097cbbbab8c4611a709b3cf95ac5c9fe5f62e619bab081911a2a247ddbed4e0`; 53,487 file-order inversions and 1,314 year/epoch mismatches reported |
| C-MAPSS FD001–FD004 | Train rows 20,631 / 53,759 / 24,720 / 61,249; test rows 13,096 / 33,991 / 16,596 / 41,214 | All 12 file hashes passed; RUL counts align to 100 / 259 / 100 / 248 test units |
| MetroPT-3 | 1,516,948 rows; 17 columns; unique monotonic timestamps | SHA-256 `db30ccb4ea402e3c8bf2c99db06e288d4f2a772f6928f9dbe26a920d69793e24`; F1–F4 coverage 8,657 / 2,360 / 17,315 / 1,622 rows |

The C-MAPSS FD004 files contain 249 training units and 248 test units; the
copied readme reverses those counts. The verifier follows the pinned files and
RUL alignment. MetroPT-3 intervals are the UCI-published 2020 air-leak reports;
timestamps without an interval remain censored.
