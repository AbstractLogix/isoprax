# AI4I 2020 structural fixture

This directory records the provenance and expected structural summary for the
AI4I 2020 Predictive Maintenance dataset. The dataset is synthetic and the full
CSV is intentionally not checked in or fetched automatically.

AI4I is the first of several distinct dataset examples in the repository. See
the [shared example overview](../../specs/039-public-dataset-validation/spec.md)
for ApacheJIT, NASA C-MAPSS, MetroPT-3, and the common evidence boundaries.

The authoritative source is the [UCI Machine Learning Repository record](https://archive.ics.uci.edu/dataset/601/ai4i%2B2020%2Bpredictive%2Bmaint),
DOI `10.24432/C5HS5C`, licensed CC BY 4.0. The [Kaggle page](https://www.kaggle.com/datasets/stephanmatzka/predictive-maintenance-dataset-ai4i-2020)
is recorded as a mirror/discovery reference.

Download the source manually and run:

```bash
uv run python scripts/verify_ai4i2020.py /path/to/ai4i2020.csv
```

The verifier reports the source checksum, schema, counts, multi-mode rows, and
both directions of composite/mode disagreement. It never derives or repairs the
`Machine failure` label from `TWF`, `HDF`, `PWF`, `OSF`, or `RNF`.

The dataset is a structural/label-semantics fixture. It does not provide real
machine histories, maintenance events, replay lineage, a future forecast horizon,
or evidence for predictive efficacy. Its outcome definitions are deliberately
separate from Isoprax JIT defect and replay-telemetry definitions; the expected
commensurability result is irreducible/non-poolable.
