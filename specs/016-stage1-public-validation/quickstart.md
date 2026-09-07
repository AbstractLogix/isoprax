# Quickstart

Download the two declared source files into a local directory, then run:

```bash
uv run python scripts/run_stage1_public_validation.py \
  --apachejit /path/to/apachejit_total.csv \
  --google-trace /path/to/google-cluster-data-1.csv.gz \
  --output docs/stage1/stage1-public-validation.json
```

The command is offline after the files are supplied. It emits separate
Change/Operational evidence and never emits a pooled metric or a Semantic/Full
Conformance claim.
