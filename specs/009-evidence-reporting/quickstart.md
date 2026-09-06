# Quickstart: Validate Evidence Reporting

From the repository root:

```sh
uv run --python 3.10 pytest -q --no-cov tests/test_evidence_reporting.py
uv run ruff check isoprax/evidence_reporting.py tests/test_evidence_reporting.py
uv run --python 3.10 pytest -q
```

Expected focused checks demonstrate:

1. Equivalent source evidence produces identical public report identities.
2. Raw prediction values and replay payloads are absent from the canonical
   public representation.
3. Failed gates are `blocked`, missing evidence is `inconclusive`, and a
   complete passing evaluation is `admission_evidence` only.
4. Mismatched lineage, scope, claim type, or private/privileged provenance is
   rejected.
