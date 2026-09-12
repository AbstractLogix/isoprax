# Tasks

- [x] Add offline Sigstore/Rekor DSSE verification.
- [x] Bind the in-toto statement to the predeclaration hash and commit.
- [x] Thread verification into the Stage 2 whoami pilot.
- [x] Add the Rekor-backed attestation creation command.
- [x] Preserve fail-closed output for the historical unanchored pilot.
- [x] Run focused and full quality verification.

## Phase 2: Convergence

- [x] T007 Replace the CLI attestation subprocess with the shared canonical
  StatementBuilder and Sigstore Python signing API per acceptance scenario 3.
- [x] T008 Add a real third-party production Sigstore/Rekor bundle fixture and
  an offline verifier regression while rejecting non-Isoprax predicates per
  acceptance scenario 2.
- [x] T009 Remove the Sigstore minor-version private-field dependency from
  Rekor reference extraction per plan item 2: verifier stability.
- [x] T010 Run the tagged OIDC workflow, commit its real Isoprax bundle fixture,
  and add the offline producer/consumer round-trip regression.
