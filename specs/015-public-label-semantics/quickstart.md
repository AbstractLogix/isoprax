# Quickstart

Run the focused contract tests without network access:

```bash
uv run pytest tests/test_public_label_evidence.py -q --no-cov
```

The fixtures demonstrate direct, bridgeable, irreducible, unavailable, and
inconclusive evidence. A successful report still does not authorize pooled
scores or Semantic/Full Conformance.
