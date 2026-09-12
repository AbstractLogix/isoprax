# Sigstore bundle fixture

`sigstore-python-4.5.0-pypi.sigstore.json` is a checked-in, production
Sigstore/Rekor DSSE bundle derived from the public PyPI Integrity API provenance
for the `sigstore==4.5.0` wheel. Its signed statement is intentionally a PyPI
publish attestation, not an Isoprax Stage 2 attestation.

The fixture is used only to exercise `sigstore`'s real offline bundle parser,
certificate/signature policy, and Rekor inclusion verification in CI. The
Stage 2 verifier must reject it because its predicate is not the Isoprax
predicate.

`whoami-pilot-predeclaration-v3.sigstore.json` is the companion real Isoprax
Stage 2 bundle. It was produced by the tagged GitHub Actions workflow
`stage2-anchor-v3` with the repository workflow identity and is verified
offline in the producer/consumer round-trip test.
