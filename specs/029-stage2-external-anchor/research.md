# Research and Decisions

## Decision: use Sigstore's verifier rather than trusting a recorded URL

The official Python client exposes `Bundle.from_json`, a production verifier,
and DSSE verification. Its DSSE path validates the signing certificate,
signature, and transparency-log consistency/inclusion before application code
interprets the payload. The repository therefore treats the bundle as input
evidence and requires the signed in-toto payload to bind the artifact identity
and commit.

## Decision: no checked-in generated bundle

The historical pilot has no independently recorded bundle. Generating one
requires an OIDC identity and a live Rekor submission, which are external
release evidence rather than local test fixtures. Tests use malformed/missing
inputs and pure statement validation; no test claims a real-world anchor.
