# Convergence

The Stage 2 pilot now has an executable independent-anchor path. A caller can
create a Sigstore DSSE attestation and pass its bundle plus expected signer
identity to the pilot. The verifier runs Sigstore's production verifier in
offline mode, which checks the bundle's signature and Rekor inclusion proof,
then checks the in-toto binding to the exact predeclaration hash and commit.

The producer now builds the canonical in-toto Statement with Sigstore's Python
API and signs that same definition; it does not pass a nested Statement to the
CLI predicate input. A real third-party PyPI Sigstore/Rekor bundle is verified
offline in CI to pin bundle shape and identity handling, then rejected by the
Stage 2 predicate binding. The tagged `stage2-anchor-v3` workflow also produced
the real Isoprax bundle, which is committed and verified offline against the
same builder definition, workflow identity, and Rekor inclusion proof.

The checked-in v2 whoami pilot intentionally remains `inconclusive` because it
has no independently matching attestation bundle. The v3 fixture proves the
producer/consumer path for the new predeclaration only; no feasibility claim
is fabricated for v2.

The report now includes a deterministic outcome-yield estimate. The recorded
pilot is `no_positive_events`, so its implied corpus size is not finite; both
outcome classes must be observed before corpus planning can proceed.
