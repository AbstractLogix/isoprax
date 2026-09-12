import importlib.util
import json
import sys
from contextlib import contextmanager
from pathlib import Path

from isoprax.identity import content_hash

_SCRIPT_PATH = Path(__file__).parents[1] / "scripts/create_stage2_anchor_attestation.py"
_SPEC = importlib.util.spec_from_file_location(
    "create_stage2_anchor_attestation", _SCRIPT_PATH
)
assert _SPEC and _SPEC.loader
_SCRIPT = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _SCRIPT
_SPEC.loader.exec_module(_SCRIPT)


def _predeclaration():
    predeclaration = {"predeclaration_commit": "b" * 40}
    predeclaration["artifact_hash"] = content_hash(predeclaration)
    return predeclaration


def test_statement_builder_is_used_without_nesting_a_statement():
    statement = _SCRIPT._statement(_predeclaration())
    payload = json.loads(statement._contents)

    assert payload["_type"] == "https://in-toto.io/Statement/v1"
    assert payload["subject"] == [
        {
            "name": "isoprax-stage2-predeclaration",
            "digest": {"sha256": _predeclaration()["artifact_hash"]},
        }
    ]
    assert payload["predicate"]["predeclaration_commit"] == "b" * 40
    assert isinstance(payload["predicate"], dict)
    assert "predicate" not in payload["predicate"]


def test_main_signs_the_statement_through_sigstore_python_api(monkeypatch, tmp_path):
    predeclaration_path = tmp_path / "predeclaration.json"
    predeclaration_path.write_text(
        json.dumps(_predeclaration()),
        encoding="utf-8",
    )
    bundle_path = tmp_path / "bundle.json"
    calls = {}

    class FakeTrustConfig:
        signing_config = type(
            "SigningConfig", (), {"get_oidc_url": lambda self: "unused"}
        )()

        @classmethod
        def production(cls):
            calls["trust_config"] = True
            return cls()

    class FakeBundle:
        def to_json(self):
            return '{"fixture":true}'

    class FakeSigner:
        def sign_dsse(self, statement):
            calls["statement"] = json.loads(statement._contents)
            return FakeBundle()

    class FakeSigningContext:
        @classmethod
        def from_trust_config(cls, trust_config):
            assert isinstance(trust_config, FakeTrustConfig)
            calls["context"] = True
            return cls()

        @contextmanager
        def signer(self, identity):
            assert identity == "identity-token"
            calls["signer"] = True
            yield FakeSigner()

    monkeypatch.setattr(_SCRIPT, "ClientTrustConfig", FakeTrustConfig)
    monkeypatch.setattr(_SCRIPT, "SigningContext", FakeSigningContext)
    monkeypatch.setattr(
        _SCRIPT, "_identity_token", lambda *args, **kwargs: "identity-token"
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "create_stage2_anchor_attestation.py",
            str(predeclaration_path),
            "--bundle",
            str(bundle_path),
        ],
    )

    assert _SCRIPT.main() == 0

    assert calls == {
        "trust_config": True,
        "context": True,
        "signer": True,
        "statement": calls["statement"],
    }
    assert json.loads(bundle_path.read_text(encoding="utf-8")) == {"fixture": True}
