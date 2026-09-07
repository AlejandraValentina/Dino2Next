from dataclasses import FrozenInstanceError

import pytest

from dino2next.provenance import ResourceRef, canonical_bytes, content_hash
from dino2next.units import ValueContractError


def test_sha256_known_vectors():
    assert content_hash(b"") == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert content_hash(b"abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_canonical_exact_bytes_unicode_order_and_array_order():
    assert canonical_bytes({"z": [2, 1], "a": "ñ"}) == '{"a":"ñ","z":[2,1]}'.encode()
    assert canonical_bytes({"z": [2, 1], "a": "ñ"}) == canonical_bytes({"a": "ñ", "z": [2, 1]})
    assert canonical_bytes({"z": [1, 2]}) != canonical_bytes({"z": [2, 1]})


@pytest.mark.parametrize("value,code", [
    ({"x": float("nan")}, "NONFINITE_VALUE"), ({"x": float("inf")}, "NONFINITE_VALUE"),
    ({1: "x"}, "INVALID_VALUE"), ({"x": object()}, "INVALID_VALUE"),
    ({"x": "\ud800"}, "INVALID_VALUE"), ([], "INVALID_VALUE"),
])
def test_invalid_canonical_data(value, code):
    with pytest.raises(ValueContractError) as exc:
        canonical_bytes(value)
    assert exc.value.code == code


def test_original_file_bytes_determine_identity(tmp_path):
    original = b'{"a": 1}\r\n'
    file = tmp_path / "resource.json"
    file.write_bytes(original)
    ref = ResourceRef("logical-id", content_hash(original), "application/json")
    ref.verify_file(file)
    ref.verify_bytes(original)
    file.write_bytes(b'{"a":1}\n')
    with pytest.raises(ValueContractError) as exc:
        ref.verify_file(file)
    assert exc.value.code == "RESOURCE_HASH_MISMATCH"
    with pytest.raises(FileNotFoundError):
        ref.verify_file(tmp_path / "missing")
    with pytest.raises(FrozenInstanceError):
        ref.id = "changed"


@pytest.mark.parametrize("digest", ["", "x" * 64, "A" * 64, "0" * 63])
def test_malformed_hash(digest):
    with pytest.raises(ValueContractError) as exc:
        ResourceRef("id", digest, "text/plain")
    assert exc.value.code == "RESOURCE_HASH_MISMATCH"


def test_mutable_bytes_rejected():
    with pytest.raises(ValueContractError) as exc:
        content_hash(bytearray(b"abc"))
    assert exc.value.code == "INVALID_VALUE"
