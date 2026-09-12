# Data Model

`ExternalAnchorVerification` contains:

- `status`: `verified` or `unverified`;
- Sigstore/Rekor anchor type and reference;
- bundle path, signer identity, and OIDC issuer;
- a bounded failure reason; and
- the Rekor log index when available.

The signed in-toto Statement must use the Isoprax predicate type and contain a
subject named `isoprax-stage2-predeclaration` with the predeclaration's
lowercase SHA-256 digest. Its predicate repeats that digest and the
predeclaration introducing commit.
