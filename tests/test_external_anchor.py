import json
from pathlib import Path

import pytest

from isoprax.external_anchor import (
    DEFAULT_SUBJECT_NAME,
    IN_TOTO_STATEMENT_TYPE,
    PREDICATE_TYPE,
    _rekor_reference,
    _validate_statement,
    verify_sigstore_attestation,
)

HASH = "a" * 64
COMMIT = "b" * 40


def _statement():
    return {
        "_type": IN_TOTO_STATEMENT_TYPE,
        "subject": [{"name": DEFAULT_SUBJECT_NAME, "digest": {"sha256": HASH}}],
        "predicateType": PREDICATE_TYPE,
        "predicate": {"artifact_hash": HASH, "predeclaration_commit": COMMIT},
    }


def _install_fake_sigstore(monkeypatch, payload):
    import sigstore.models
    import sigstore.verify
    import sigstore.verify.policy

    class FakeBundle:
        log_entry = type(
            "LogEntry", (), {"_inner": type("Entry", (), {"log_index": 17})()}
        )()

        @classmethod
        def from_json(cls, raw):
            assert raw == b"bundle"
            return cls()

    class FakeVerifier:
        @classmethod
        def production(cls, *, offline):
            assert offline is True
            return cls()

        def verify_dsse(self, bundle, policy):
            assert isinstance(bundle, FakeBundle)
            assert policy._identity == "identity"
            return payload

    class FakeIdentity:
        def __init__(self, *, identity, issuer):
            self._identity = identity
            self.issuer = issuer

    monkeypatch.setattr(sigstore.models, "Bundle", FakeBundle)
    monkeypatch.setattr(sigstore.verify, "Verifier", FakeVerifier)
    monkeypatch.setattr(sigstore.verify.policy, "Identity", FakeIdentity)


def test_valid_in_toto_statement_binds_hash_and_commit():
    _validate_statement(
        _statement(),
        artifact_hash=HASH,
        predeclaration_commit=COMMIT,
        subject_name=DEFAULT_SUBJECT_NAME,
    )


@pytest.mark.parametrize(
    "change, message",
    [
        ({"subject": [{"name": DEFAULT_SUBJECT_NAME, "digest": {}}]}, "hash"),
        (
            {"predicate": {"artifact_hash": HASH, "predeclaration_commit": "x"}},
            "commit",
        ),
    ],
)
def test_in_toto_statement_rejects_changed_identity(change, message):
    statement = _statement()
    statement.update(change)
    with pytest.raises(ValueError, match=message):
        _validate_statement(
            statement,
            artifact_hash=HASH,
            predeclaration_commit=COMMIT,
            subject_name=DEFAULT_SUBJECT_NAME,
        )


@pytest.mark.parametrize(
    "change, message",
    [
        ({"_type": "wrong"}, "Statement"),
        ({"predicateType": "wrong"}, "predicate type"),
        ({"subject": {}}, "subject list"),
        ({"subject": [{"name": "wrong", "digest": {}}]}, "does not name"),
        ({"predicate": None}, "predicate is required"),
        ({"predicate": {"artifact_hash": "wrong"}}, "predicate does not match"),
    ],
)
def test_in_toto_statement_rejects_malformed_structure(change, message):
    statement = _statement()
    statement.update(change)
    with pytest.raises(ValueError, match=message):
        _validate_statement(
            statement,
            artifact_hash=HASH,
            predeclaration_commit=COMMIT,
            subject_name=DEFAULT_SUBJECT_NAME,
        )


def test_missing_bundle_is_unverified_and_never_an_anchor(tmp_path):
    result = verify_sigstore_attestation(
        tmp_path / "missing.json",
        artifact_hash=HASH,
        predeclaration_commit=COMMIT,
        signer_identity="https://github.com/example/workflow",
    )

    assert result.verified is False
    assert result.status == "unverified"
    assert "missing" in result.reason
    assert result.anchor_reference == ""


def test_unconfigured_bundle_is_unverified_and_serializable():
    result = verify_sigstore_attestation(
        None,
        artifact_hash=HASH,
        predeclaration_commit=COMMIT,
        signer_identity=None,
    )

    assert result.to_dict()["status"] == "unverified"
    assert result.verified is False


@pytest.mark.parametrize(
    "artifact_hash, signer_identity, message",
    [
        ("A" * 64, "identity", "lowercase"),
        (HASH, "", "identity"),
    ],
)
def test_bundle_configuration_errors_are_unverified(
    tmp_path, artifact_hash, signer_identity, message
):
    bundle = tmp_path / "bundle.json"
    bundle.write_text("{}", encoding="utf-8")

    result = verify_sigstore_attestation(
        bundle,
        artifact_hash=artifact_hash,
        predeclaration_commit=COMMIT,
        signer_identity=signer_identity,
    )

    assert result.verified is False
    assert message in result.reason


def test_invalid_bundle_is_unverified_without_network_or_clock_evidence(tmp_path):
    bundle = tmp_path / "bundle.json"
    bundle.write_text(json.dumps({"mediaType": "invalid"}), encoding="utf-8")

    result = verify_sigstore_attestation(
        bundle,
        artifact_hash=HASH,
        predeclaration_commit=COMMIT,
        signer_identity="https://github.com/example/workflow",
    )

    assert result.verified is False
    assert "verification failed" in result.reason


def test_valid_bundle_verification_binds_statement_and_rekor(monkeypatch, tmp_path):
    _install_fake_sigstore(
        monkeypatch,
        ("application/vnd.in-toto+json", json.dumps(_statement()).encode()),
    )
    bundle = tmp_path / "bundle.json"
    bundle.write_bytes(b"bundle")

    result = verify_sigstore_attestation(
        bundle,
        artifact_hash=HASH,
        predeclaration_commit=COMMIT,
        signer_identity="identity",
        issuer="issuer",
    )

    assert result.verified is True
    assert result.anchor_reference == "rekor://17"
    assert result.rekor_log_index == "17"
    assert result.statement == _statement()


def test_rekor_reference_has_bundle_fallback():
    reference, index = _rekor_reference(object(), Path("bundle.json"))

    assert reference == "sigstore-bundle:bundle.json"
    assert index is None


@pytest.mark.parametrize(
    "payload, message",
    [
        (("wrong/type", b"{}"), "unexpected DSSE payload type"),
        (("application/vnd.in-toto+json", b"[]"), "JSON object"),
    ],
)
def test_signed_payload_shape_errors_remain_unverified(
    monkeypatch, tmp_path, payload, message
):
    _install_fake_sigstore(monkeypatch, payload)
    bundle = tmp_path / "bundle.json"
    bundle.write_bytes(b"bundle")

    result = verify_sigstore_attestation(
        bundle,
        artifact_hash=HASH,
        predeclaration_commit=COMMIT,
        signer_identity="identity",
    )

    assert result.verified is False
    assert message in result.reason
