from isoprax.identity import bytes_hash, canonical_json, content_hash


def test_identity_serialization_is_sorted_and_hashes_are_stable():
    assert canonical_json({"b": 2, "a": 1}) == '{"a":1,"b":2}'
    assert content_hash({"b": 2, "a": 1}) == content_hash({"a": 1, "b": 2})


def test_identity_serialization_handles_non_json_values_consistently():
    assert canonical_json({"value": (1, 2)}) == '{"value":[1,2]}'
    assert bytes_hash(b"isoprax") == bytes_hash(b"isoprax")
