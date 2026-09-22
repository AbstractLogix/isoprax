# Quickstart: AI4I 2020 Structural Fixture

The repository does not download or vendor the external dataset. Obtain the UCI
artifact manually, then verify the local extracted CSV:

```bash
curl -fL -o /tmp/ai4i2020.zip \
  'https://cdn.uci-ics-mlr-prod.aws.uci.edu/601/ai4i%2B2020%2Bpredictive%2Bmaintenance%2Bdataset.zip'
sha256sum /tmp/ai4i2020.zip
unzip -q /tmp/ai4i2020.zip -d /tmp/ai4i2020
uv run python scripts/verify_ai4i2020.py /tmp/ai4i2020/ai4i2020.csv
```

The pinned ZIP checksum is
`f601f14294bcf190f9d720676b7f0aea46a26cde9ab8ebc7b4f8174d9d26b252`. The pinned
CSV checksum is recorded in `examples/ai4i2020/manifest.json`.

Expected structural output includes 10,000 rows, 14 columns, 339 composite
failures, mode counts TWF=46, HDF=115, PWF=95, OSF=98, RNF=19, 24 multi-mode
rows, 9 failures without a mode flag, and 18 mode flags on rows labelled as
non-failures. The verifier must preserve these discrepancies.

## Verified snapshot

On 2026-09-22, the UCI artifact verified with exit status 0 and CSV SHA-256
`dc6630cd9b1f0f853922fad78a1b6436570d3f1ec863f1dd5c4340ac56bc8a8e`. The report
contained `verified: true`, `row_count: 10000`, `machine_failure_count: 339`,
`composite_mismatch_count: 27`, `multi_mode_row_count: 24`,
`failure_without_mode_count: 9`, and `mode_without_failure_count: 18`.

Run focused tests without network access:

```bash
uv run pytest tests/test_ai4i2020.py -q
uv run ruff check isoprax/ai4i2020.py scripts/verify_ai4i2020.py tests/test_ai4i2020.py
```

This fixture proves only source/schema/label and commensurability mechanics. It
does not establish replay lineage, time-safe prediction, calibration, production
efficacy, or Semantic/Full Conformance.
