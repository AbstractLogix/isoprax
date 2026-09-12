# Research and Decisions

## Decision: use Sigstore's verifier rather than trusting a recorded URL

The official Python client exposes `Bundle.from_json`, a production verifier,
and DSSE verification. Its DSSE path validates the signing certificate,
signature, and transparency-log consistency/inclusion before application code
interprets the payload. The repository therefore treats the bundle as input
evidence and requires the signed in-toto payload to bind the artifact identity
and commit.

## Decision: keep the production fixture separate from Stage 2 evidence

The historical pilot has no independently recorded Isoprax bundle. Generating
that bundle requires an OIDC identity and a live Rekor submission, which remain
external release evidence. CI therefore checks in one real production
Sigstore/Rekor DSSE bundle from a public PyPI attestation to pin the third-party
bundle shape and offline verifier behavior, while the Stage 2 verifier rejects
it because its predicate is not the Isoprax predicate. No test claims that the
historical pilot is anchored.
