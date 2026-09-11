# Data Model: Shared Canonical Evidence Identities

Identity payloads are serialized by `canonical_json` and hashed by
`content_hash`. Already serialized artifact bytes use `bytes_hash`. All three
functions are deterministic and SHA-256 based.
