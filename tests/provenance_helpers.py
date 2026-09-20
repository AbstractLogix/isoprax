"""Test helpers that exercise the production external-anchor verifier path."""

import json
from pathlib import Path
from typing import Any, Mapping

import pytest

from isoprax.external_anchor import (
    IN_TOTO_PAYLOAD_TYPE,
    stage2_statement_payload,
    verify_sigstore_attestation,
)
from isoprax.identity import content_hash


def verified_anchor(payload: Mapping[str, Any]):
    """Return a verifier-issued result using a deterministic fake Sigstore boundary."""
    import sigstore.models
    import sigstore.verify
    import sigstore.verify.policy

    payload = dict(payload)
    artifact_hash = content_hash(payload)
    statement = stage2_statement_payload(
        artifact_hash, payload["predeclaration_commit"]
    )

    class FakeBundle:
        @classmethod
        def from_json(cls, raw):
            return cls()

        def to_json(self):
            return json.dumps(
                {"verificationMaterial": {"tlogEntries": [{"logIndex": "17"}]}}
            )

    class FakeVerifier:
        @classmethod
        def production(cls, *, offline):
            assert offline is True
            return cls()

        def verify_dsse(self, bundle, policy):
            assert isinstance(bundle, FakeBundle)
            assert policy._identity == "identity"
            return IN_TOTO_PAYLOAD_TYPE, json.dumps(statement).encode()

    class FakeIdentity:
        def __init__(self, *, identity, issuer):
            self._identity = identity
            self.issuer = issuer

    patch = pytest.MonkeyPatch()
    patch.setattr(sigstore.models, "Bundle", FakeBundle)
    patch.setattr(sigstore.verify, "Verifier", FakeVerifier)
    patch.setattr(sigstore.verify.policy, "Identity", FakeIdentity)
    try:
        return verify_sigstore_attestation(
            Path(__file__).parent / "fixtures/sigstore-python-4.5.0-pypi.sigstore.json",
            artifact_hash=artifact_hash,
            predeclaration_commit=payload["predeclaration_commit"],
            signer_identity="identity",
            issuer="issuer",
        )
    finally:
        patch.undo()
