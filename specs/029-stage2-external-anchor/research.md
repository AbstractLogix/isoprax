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

The producer/consumer round trip is covered by a second, real Isoprax bundle.
The tagged `stage2-anchor-v3` GitHub Actions workflow signed the fixed
predeclaration with the repository workflow OIDC identity; the resulting
bundle is committed as a fixture and verified offline. The historical v2
pilot remains unanchored because it has no matching bundle.
