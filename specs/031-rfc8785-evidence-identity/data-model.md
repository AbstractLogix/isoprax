# Data Model

An evidence identity is:

```text
SHA-256(UTF-8(RFC8785(value)))
```

The canonical JSON API returns text for existing callers; byte hashing remains
available for already serialized artifacts. JCS safe integers are limited to
the exact JSON number domain supported by the RFC 8785 implementation.
