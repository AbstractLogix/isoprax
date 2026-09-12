# Research and Decisions

## Decision: use Sigstore's verifier rather than trusting a recorded URL

The official Python client exposes `Bundle.from_json`, a production verifier,
and DSSE verification. Its DSSE path validates the signing certificate,
signature, and transparency-log consistency/inclusion before application code
interprets the payload. The repository therefore treats the bundle as input
evidence and requires the signed in-toto payload to bind the artifact identity
and commit.

## Decision: use layered real fixtures and keep the custom anchor external

The historical pilot has no independently recorded Isoprax bundle. Generating
that bundle requires an OIDC identity and a live Rekor submission, which remain
external release evidence. The committed public PyPI Sigstore/Rekor DSSE
bundle pins the third-party parsing, certificate, DSSE, inclusion-proof, and
checkpoint boundary; Stage 2 deliberately rejects it because its predicate is
not the Isoprax predicate.

The producer/consumer round trip requires a second, real Isoprax bundle. A
tagged GitHub Actions workflow now signs the fixed predeclaration with the
workflow OIDC identity and uploads the bundle for review and commit. Until
that workflow has run and its identity has been recorded, no test claims that
the historical pilot is independently anchored.
