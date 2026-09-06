# Public Evidence Contract

`normalize_public_evidence(snapshots)` is offline and deterministic. It returns
ordered records only for public immutable source evidence. Unsafe provenance,
credentials, mutable revisions, invalid timestamps, duplicates, or CI linked
to another revision raise `ValueError`. Missing CI is explicit unavailable.
