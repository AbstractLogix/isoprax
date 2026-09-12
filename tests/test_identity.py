import pytest
import rfc8785

from isoprax.identity import bytes_hash, canonical_json, content_hash


def test_identity_serialization_is_rfc8785_and_hashes_are_stable():
    assert canonical_json({"b": 2, "a": 1}) == '{"a":1,"b":2}'
    assert content_hash({"b": 2, "a": 1}) == content_hash({"a": 1, "b": 2})
    assert content_hash({"b": 2, "a": 1}) == (
        "43258cff783fe7036d8a43033f830adfc60ec037382473548ac742b888292777"
    )
    assert canonical_json({"text": "é", "number": 1.0}) == ('{"number":1,"text":"é"}')


def test_identity_serialization_handles_json_sequences_consistently():
    assert canonical_json({"value": (1, 2)}) == '{"value":[1,2]}'
    assert bytes_hash(b"isoprax") == bytes_hash(b"isoprax")


def test_identity_rejects_values_without_an_rfc8785_representation():
    with pytest.raises(rfc8785.CanonicalizationError):
        canonical_json({"value": b"isoprax"})

    with pytest.raises(rfc8785.FloatDomainError):
        canonical_json({"value": float("nan")})

    with pytest.raises(rfc8785.IntegerDomainError):
        canonical_json({"value": 2**53})
