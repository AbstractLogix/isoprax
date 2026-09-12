# Convergence

The Stage 2 pilot now has an executable independent-anchor path. A caller can
create a Sigstore DSSE attestation and pass its bundle plus expected signer
identity to the pilot. The verifier runs Sigstore's production verifier in
offline mode, which checks the bundle's signature and Rekor inclusion proof,
then checks the in-toto binding to the exact predeclaration hash and commit.

The checked-in whoami pilot intentionally remains `inconclusive` because no
attestation bundle is published with it. No feasibility evidence is fabricated
to close that external/human gate.
