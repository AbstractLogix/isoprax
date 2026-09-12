"""Create a Rekor-backed in-toto attestation for a Stage 2 predeclaration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sigstore.dsse import Statement
from sigstore.models import ClientTrustConfig
from sigstore.oidc import IdentityToken, Issuer, detect_credential
from sigstore.sign import SigningContext

from isoprax.external_anchor import (
    build_stage2_statement,
)
from isoprax.identity import content_hash


def _predeclaration_hash(predeclaration: dict[str, object]) -> str:
    payload = {
        key: value for key, value in predeclaration.items() if key != "artifact_hash"
    }
    return content_hash(payload)


def _statement(predeclaration: dict[str, object]) -> Statement:
    artifact_hash = str(predeclaration.get("artifact_hash", "")).strip()
    if not artifact_hash or _predeclaration_hash(predeclaration) != artifact_hash:
        raise ValueError("predeclaration artifact hash does not match its content")
    commit = str(predeclaration.get("predeclaration_commit", "")).strip()
    if not commit:
        raise ValueError("predeclaration_commit is required")
    return build_stage2_statement(artifact_hash, commit)


def _identity_token(
    trust_config: ClientTrustConfig,
    *,
    client_id: str,
    oidc_issuer: str | None,
    oauth_force_oob: bool,
) -> IdentityToken:
    raw_token = detect_credential(client_id)
    if raw_token:
        return IdentityToken(raw_token, client_id)
    issuer_url = oidc_issuer or trust_config.signing_config.get_oidc_url()
    return Issuer(issuer_url).identity_token(
        client_id=client_id,
        force_oob=oauth_force_oob,
    )


def _create_bundle(
    statement: Statement,
    bundle_path: Path,
    *,
    oidc_client_id: str,
    oidc_issuer: str | None,
    oauth_force_oob: bool,
) -> None:
    trust_config = ClientTrustConfig.production()
    identity = _identity_token(
        trust_config,
        client_id=oidc_client_id,
        oidc_issuer=oidc_issuer,
        oauth_force_oob=oauth_force_oob,
    )
    signing_context = SigningContext.from_trust_config(trust_config)
    with signing_context.signer(identity) as signer:
        bundle = signer.sign_dsse(statement)
    bundle_path.write_text(bundle.to_json() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("predeclaration", type=Path)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--oidc-client-id", default="sigstore")
    parser.add_argument("--oidc-issuer")
    parser.add_argument("--oauth-force-oob", action="store_true")
    args = parser.parse_args()

    predeclaration = json.loads(args.predeclaration.read_text(encoding="utf-8"))
    if not isinstance(predeclaration, dict):
        raise ValueError("predeclaration must be a JSON object")
    statement = _statement(predeclaration)
    args.bundle.parent.mkdir(parents=True, exist_ok=True)
    _create_bundle(
        statement,
        args.bundle,
        oidc_client_id=args.oidc_client_id,
        oidc_issuer=args.oidc_issuer,
        oauth_force_oob=args.oauth_force_oob,
    )
    print(json.dumps({"bundle": str(args.bundle), "status": "created"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
