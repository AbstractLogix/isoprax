"""Verify independent Sigstore/Rekor anchors for evidence artifacts.

This module verifies a local Sigstore DSSE bundle with the production trust
roots in offline mode.  Sigstore's verifier checks the signing certificate,
the DSSE signature, and the Rekor inclusion proof/checkpoint.  The in-toto
statement checks below then bind that signed payload to the exact artifact and
predeclaration commit consumed by the Stage 2 reducer.

The absence of a bundle, signer identity, or valid statement is represented as
an unverified result.  Callers must keep their result inconclusive in that
case; this module never treats a repository URL or a self-asserted timestamp
as an independent anchor.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

IN_TOTO_PAYLOAD_TYPE = "application/vnd.in-toto+json"
IN_TOTO_STATEMENT_TYPE = "https://in-toto.io/Statement/v1"
PREDICATE_TYPE = "https://isoprax.dev/predicates/stage2-predeclaration/v1"
DEFAULT_SUBJECT_NAME = "isoprax-stage2-predeclaration"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class ExternalAnchorVerification:
    """Machine-readable result of one independent-anchor verification."""

    status: str
    anchor_type: str
    anchor_reference: str
    bundle_path: str | None
    signer_identity: str | None
    issuer: str | None
    reason: str
    rekor_log_index: str | None = None
    statement: Mapping[str, Any] | None = None

    @property
    def verified(self) -> bool:
        return self.status == "verified"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "anchor_type": self.anchor_type,
            "anchor_reference": self.anchor_reference,
            "bundle_path": self.bundle_path,
            "signer_identity": self.signer_identity,
            "issuer": self.issuer,
            "reason": self.reason,
            "rekor_log_index": self.rekor_log_index,
        }


def _unverified(
    *,
    bundle_path: Path | None,
    signer_identity: str | None,
    issuer: str | None,
    reason: str,
) -> ExternalAnchorVerification:
    return ExternalAnchorVerification(
        status="unverified",
        anchor_type="sigstore_rekor_dsse",
        anchor_reference="",
        bundle_path=None if bundle_path is None else str(bundle_path),
        signer_identity=signer_identity,
        issuer=issuer,
        reason=reason,
    )


def _validate_statement(
    statement: Mapping[str, Any],
    *,
    artifact_hash: str,
    predeclaration_commit: str,
    subject_name: str,
) -> None:
    if statement.get("_type") != IN_TOTO_STATEMENT_TYPE:
        raise ValueError("attestation is not an in-toto Statement/v1")
    if statement.get("predicateType") != PREDICATE_TYPE:
        raise ValueError("attestation predicate type is not the Stage 2 type")
    subjects = statement.get("subject")
    if not isinstance(subjects, list):
        raise ValueError("attestation subject list is required")
    matching_subject = next(
        (
            subject
            for subject in subjects
            if isinstance(subject, Mapping) and subject.get("name") == subject_name
        ),
        None,
    )
    if matching_subject is None:
        raise ValueError("attestation does not name the expected predeclaration")
    digest = matching_subject.get("digest")
    if not isinstance(digest, Mapping) or digest.get("sha256") != artifact_hash:
        raise ValueError("attestation subject does not match the predeclaration hash")
    predicate = statement.get("predicate")
    if not isinstance(predicate, Mapping):
        raise ValueError("attestation predicate is required")
    if predicate.get("artifact_hash") != artifact_hash:
        raise ValueError("attestation predicate does not match the predeclaration hash")
    if predicate.get("predeclaration_commit") != predeclaration_commit:
        raise ValueError(
            "attestation predicate does not match the predeclaration commit"
        )


def _rekor_reference(bundle: Any, bundle_path: Path) -> tuple[str, str | None]:
    """Return a stable Rekor reference without depending on it for validity."""

    try:
        entry = bundle.log_entry._inner
        log_index = str(entry.log_index)
        return f"rekor://{log_index}", log_index
    except (AttributeError, TypeError):
        return f"sigstore-bundle:{bundle_path.name}", None


def verify_sigstore_attestation(
    bundle_path: str | Path | None,
    *,
    artifact_hash: str,
    predeclaration_commit: str,
    signer_identity: str | None,
    issuer: str | None = None,
    subject_name: str = DEFAULT_SUBJECT_NAME,
) -> ExternalAnchorVerification:
    """Verify a Sigstore DSSE/in-toto attestation for one predeclaration.

    Verification runs offline after loading the bundle, so no current local
    clock or network response is used as evidence.  The Sigstore verifier
    still validates the bundle's Rekor inclusion proof and signed checkpoint.
    """

    path = None if bundle_path is None else Path(bundle_path)
    if path is None:
        return _unverified(
            bundle_path=None,
            signer_identity=signer_identity,
            issuer=issuer,
            reason="Sigstore attestation bundle is not configured",
        )
    if not path.is_file():
        return _unverified(
            bundle_path=path,
            signer_identity=signer_identity,
            issuer=issuer,
            reason=f"Sigstore attestation bundle is missing: {path}",
        )
    if not _SHA256.fullmatch(artifact_hash):
        return _unverified(
            bundle_path=path,
            signer_identity=signer_identity,
            issuer=issuer,
            reason="predeclaration artifact hash is not a lowercase SHA-256 digest",
        )
    if not signer_identity or not signer_identity.strip():
        return _unverified(
            bundle_path=path,
            signer_identity=signer_identity,
            issuer=issuer,
            reason="Sigstore signer identity is required for verification",
        )

    try:
        from sigstore.models import Bundle
        from sigstore.verify import Verifier
        from sigstore.verify.policy import Identity

        bundle = Bundle.from_json(path.read_bytes())
        payload_type, payload = Verifier.production(offline=True).verify_dsse(
            bundle,
            Identity(identity=signer_identity, issuer=issuer),
        )
        if payload_type != IN_TOTO_PAYLOAD_TYPE:
            raise ValueError(f"unexpected DSSE payload type: {payload_type}")
        statement = json.loads(payload)
        if not isinstance(statement, Mapping):
            raise ValueError("attestation payload must be a JSON object")
        _validate_statement(
            statement,
            artifact_hash=artifact_hash,
            predeclaration_commit=predeclaration_commit,
            subject_name=subject_name,
        )
        reference, log_index = _rekor_reference(bundle, path)
    except Exception as error:  # external verification boundary
        return _unverified(
            bundle_path=path,
            signer_identity=signer_identity,
            issuer=issuer,
            reason=f"Sigstore/Rekor verification failed: {error}",
        )

    return ExternalAnchorVerification(
        status="verified",
        anchor_type="sigstore_rekor_dsse",
        anchor_reference=reference,
        bundle_path=str(path),
        signer_identity=signer_identity,
        issuer=issuer,
        reason="Sigstore DSSE signature, in-toto binding, and Rekor inclusion verified",
        rekor_log_index=log_index,
        statement=statement,
    )
