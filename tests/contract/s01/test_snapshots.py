from copy import deepcopy
from dataclasses import FrozenInstanceError
import json
from pathlib import Path

import pytest

from dino2next.config import ConfigSnapshot, freeze_config
from dino2next.provenance import ResourceRef, canonical_bytes, content_hash
from dino2next.units import Quantity, ValueContractError


def test_recursive_detachment_conversion_and_hash():
    source = {"schema_version": "1.0", "payload": {"rows": [
        {"bore": {"value": 50, "unit": "mm", "dimension": "length"}},
        Quantity(25, "degC", "temperature"), {"flag": True}]}}
    before = deepcopy(source)
    frozen = freeze_config(source)
    assert source == before
    assert frozen.payload["rows"][0]["bore"] == {"value": .05, "unit": "m", "dimension": "length"}
    assert frozen.payload["rows"][1] == {"value": 298.15, "unit": "K", "dimension": "temperature"}
    source["payload"]["rows"][0]["bore"]["value"] = 100
    assert frozen.payload["rows"][0]["bore"]["value"] == .05
    with pytest.raises(TypeError):
        frozen.payload["rows"][0]["bore"] = 1
    with pytest.raises(FrozenInstanceError):
        frozen.version = "2"
    exported = frozen.to_mapping()
    exported["payload"]["rows"].append(1)
    assert len(frozen.payload["rows"]) == 3
    assert frozen.sha256 == content_hash(canonical_bytes(frozen.to_mapping()))
    assert freeze_config(frozen.to_mapping()) == frozen


@pytest.mark.parametrize("mapping,code,path", [
    ({"schema_version": "2", "payload": {}}, "SCHEMA_VERSION_UNSUPPORTED", "/schema_version"),
    ({"schema_version": "1.0", "payload": {}, "typo": 1}, "UNKNOWN_FIELD", "/typo"),
    ({"schema_version": "1.0"}, "INVALID_VALUE", "/payload"),
    ({"schema_version": "1.0", "payload": []}, "INVALID_VALUE", "/payload"),
    ({"schema_version": "1.0", "payload": {"a/b": [float("nan")]}}, "NONFINITE_VALUE", "/payload/a~1b/0"),
    ({"schema_version": "1.0", "payload": {"q": {"value": 1, "unit": "mm", "dimension": "area"}}}, "UNIT_DIMENSION_MISMATCH", "/payload/q/dimension"),
    ({"schema_version": "1.0", "payload": {"q": {"value": 1, "unit": "mm", "dimension": "length", "extra": 1}}}, "UNKNOWN_FIELD", "/payload/q/extra"),
])
def test_failure_contract(mapping, code, path):
    with pytest.raises(ValueContractError) as exc:
        freeze_config(mapping)
    assert exc.value.code == code
    assert exc.value.path == path
    assert exc.value.component
    assert exc.value.message
    assert dict(exc.value.metadata) == {}


def test_resource_binding_does_not_claim_content_verification():
    ref = ResourceRef("dataset", "0" * 64, "application/json")
    source = {"schema_version": "1.0", "payload": {}, "resource_refs": [ref.to_mapping()]}
    frozen = freeze_config(source)
    source["resource_refs"][0]["id"] = "changed"
    assert frozen.resource_refs == (ref,)
    with pytest.raises(ValueContractError) as exc:
        ref.verify_bytes(b"unverified")
    assert exc.value.code == "RESOURCE_HASH_MISMATCH"
    assert exc.value.metadata["actual"] == content_hash(b"unverified")


@pytest.mark.parametrize("change", ["payload", "id", "sha256", "media_type", "array_order"])
def test_snapshot_identity_binds_every_content_field(change):
    original = {"schema_version": "1.0", "payload": {"items": [1, 2]},
                "resource_refs": [{"id": "a", "sha256": "0" * 64, "media_type": "text/plain"}]}
    modified = deepcopy(original)
    if change == "payload":
        modified["payload"]["new"] = 3
    elif change == "array_order":
        modified["payload"]["items"].reverse()
    else:
        modified["resource_refs"][0][change] = "1" * 64 if change == "sha256" else "other"
    assert freeze_config(original).sha256 != freeze_config(modified).sha256
    reordered = dict(reversed(list(original.items())))
    assert freeze_config(original).sha256 == freeze_config(reordered).sha256


def test_resource_metadata_unknown_fields_and_invalid_hash_paths():
    source = {"schema_version": "1.0", "payload": {}, "resource_refs": [
        {"id": "a", "sha256": "0" * 64, "media_type": "text/plain", "typo": True}]}
    with pytest.raises(ValueContractError) as exc:
        freeze_config(source)
    assert (exc.value.code, exc.value.path) == ("UNKNOWN_FIELD", "/resource_refs/0/typo")
    del source["resource_refs"][0]["typo"]
    source["resource_refs"][0]["sha256"] = "invalid"
    with pytest.raises(ValueContractError) as exc:
        freeze_config(source)
    assert (exc.value.code, exc.value.path) == ("RESOURCE_HASH_MISMATCH", "/resource_refs/0/sha256")


def test_direct_constructor_detaches_and_verifies():
    snapshot = freeze_config({"schema_version": "1.0", "payload": {"a": [1]}})
    payload = {"a": [1]}
    direct = ConfigSnapshot("1.0", payload, [], snapshot.sha256)
    payload["a"].append(2)
    assert direct == snapshot
    with pytest.raises(ValueContractError) as exc:
        ConfigSnapshot("1.0", {}, [], "0" * 64)
    assert exc.value.code == "RESOURCE_HASH_MISMATCH"


def test_direct_constructor_rejects_non_si_even_with_matching_hash():
    payload = {"bore": {"value": 50, "unit": "mm", "dimension": "length"}}
    digest = content_hash(canonical_bytes({"schema_version": "1.0", "payload": payload,
                                          "resource_refs": []}))
    with pytest.raises(ValueContractError) as exc:
        ConfigSnapshot("1.0", payload, [], digest)
    assert exc.value.code == "UNIT_DIMENSION_MISMATCH"


def test_cycles_fail_and_repeated_aliases_are_allowed():
    payload = {}
    payload["cycle"] = payload
    with pytest.raises(ValueContractError) as exc:
        freeze_config({"schema_version": "1.0", "payload": payload})
    assert exc.value.code == "INVALID_VALUE"
    item = [1]
    frozen = freeze_config({"schema_version": "1.0", "payload": {"a": item, "b": item}})
    assert frozen.payload["a"] == frozen.payload["b"] == (1,)


def test_common_schema_leaves_scientific_payload_to_owner():
    schema = json.loads(Path("schemas/common/config.schema.json").read_text())
    assert schema["additionalProperties"] is False
    assert schema["properties"]["schema_version"]["const"] == "1.0"
    frozen = freeze_config({"schema_version": "1.0", "payload": {"future_science": {"x": 4}}})
    assert frozen.payload["future_science"]["x"] == 4
