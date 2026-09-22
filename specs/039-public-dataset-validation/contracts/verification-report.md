# Verification Report Contract

The CLI returns a JSON object with this stable top-level shape:

```json
{
  "dataset_id": "apachejit",
  "verified": true,
  "artifact": {
    "path": "/data/apachejit_total.csv",
    "sha256": "..."
  },
  "observed": {},
  "diagnostics": {},
  "errors": [],
  "warnings": []
}
```

Required behavior:

- Exit status `0` only when `verified` is true.
- Exit status nonzero when any required invariant fails or a required input is
  missing.
- `--json` emits one machine-readable object to stdout; human-readable mode
  summarizes the same result without changing semantics.
- No subcommand downloads files, follows URLs, mutates input, or drops rows.
- MetroPT-3 reports interval coverage and anchor completeness; it must not
  emit inferred negative labels for uncovered observations.
- Reports may include additional diagnostic keys, but must retain the top-level
  fields above.

Commands:

```text
verify_public_dataset.py apachejit PATH [--json]
verify_public_dataset.py cmapss --dataset FD001|FD002|FD003|FD004 \
  --train PATH --test PATH --rul PATH [--json]
verify_public_dataset.py metropt3 PATH --intervals PATH [--json]
```
