# Quickstart: RFC 8785 Identities

```python
from isoprax.identity import canonical_json, content_hash

canonical_json({"b": 2, "a": 1})  # '{"a":1,"b":2}'
content_hash({"b": 2, "a": 1})
```

The same JCS implementation can be used by another language to recompute the
hash. Values that are not valid JCS inputs must be rejected before identity
creation.
