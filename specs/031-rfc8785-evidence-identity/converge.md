# Convergence

`canonical_json` now returns the UTF-8-decoded output of `rfc8785.dumps`, and
all shared `content_hash` consumers inherit the JCS representation. Unsafe
JSON values fail closed instead of being converted with Python's `str()`.
Existing project artifacts retain their hash because their payloads are
already JCS-representable.
