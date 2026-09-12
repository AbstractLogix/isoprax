# Quickstart: Stage 2 External Anchor

Create a bundle in an environment with Sigstore OIDC credentials:

```bash
uv run python scripts/create_stage2_anchor_attestation.py \
  docs/stage2/whoami-pilot-predeclaration-v2.json \
  --bundle /tmp/whoami-predeclaration.sigstore.json
```

Verify it while reducing the pilot (replace the identity with the identity in
the signing certificate):

```bash
uv run python scripts/run_stage2_whoami_pilot.py \
  --attestation-bundle /tmp/whoami-predeclaration.sigstore.json \
  --attestation-identity 'https://github.com/ORG/REPO/.github/workflows/WORKFLOW.yml@refs/heads/main' \
  --attestation-issuer 'https://token.actions.githubusercontent.com'
```

Without a valid bundle, the command remains `inconclusive` and emits no
feasibility report.
