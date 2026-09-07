"""Versioned common envelope; scientific payload validation belongs to its owner."""

from collections.abc import Mapping
from dataclasses import dataclass

from dino2next.provenance import (
    ResourceRef, canonical_bytes, content_hash, immutable, json_value, pointer,
)
from dino2next.units import Quantity, SI_UNITS, ValueContractError, to_si

SCHEMA_VERSION = "1.0"


def fail(code, path, message):
    raise ValueContractError(code, path, message, component="config")


def fields(mapping, required, optional, path):
    if not isinstance(mapping, Mapping):
        fail("INVALID_VALUE", path, "Expected an object")
    for key in mapping:
        if key not in required | optional:
            fail("UNKNOWN_FIELD", pointer(path, key), "Unknown common metadata field")
    for key in sorted(required):
        if key not in mapping:
            fail("INVALID_VALUE", pointer(path, key), "Required field is missing")


def si_payload(value, path="/payload", active=None, *, require_si=False):
    active = set() if active is None else active
    if isinstance(value, Quantity):
        try:
            result = to_si(value)
            if require_si and value.unit != SI_UNITS[value.dimension]:
                fail("UNIT_DIMENSION_MISMATCH", "", "Direct snapshot requires SI quantities")
            return {"value": result, "unit": SI_UNITS[value.dimension], "dimension": value.dimension}
        except ValueContractError as exc:
            fail(exc.code, path + exc.path, exc.message)
    if isinstance(value, (Mapping, list, tuple)):
        if id(value) in active:
            fail("INVALID_VALUE", path, "Cyclic data is not JSON")
        active.add(id(value))
        try:
            if isinstance(value, Mapping):
                # The complete triple is a reserved presentation quantity shape.
                if {"value", "unit", "dimension"} <= value.keys():
                    fields(value, {"value", "unit", "dimension"}, set(), path)
                    try:
                        quantity = Quantity(**value)
                        result = to_si(quantity)
                        if require_si and quantity.unit != SI_UNITS[quantity.dimension]:
                            fail("UNIT_DIMENSION_MISMATCH", "/unit", "Direct snapshot requires SI quantities")
                        return {"value": result, "unit": SI_UNITS[quantity.dimension],
                                "dimension": quantity.dimension}
                    except ValueContractError as exc:
                        fail(exc.code, path + exc.path, exc.message)
                result = {}
                for key, item in value.items():
                    if type(key) is not str:
                        fail("INVALID_VALUE", path, "JSON object keys must be strings")
                    result[key] = si_payload(item, pointer(path, key), active, require_si=require_si)
                return result
            return [si_payload(item, pointer(path, i), active, require_si=require_si)
                    for i, item in enumerate(value)]
        finally:
            active.remove(id(value))
    return json_value(value, path)


@dataclass(frozen=True, slots=True)
class ConfigSnapshot:
    version: str
    payload: Mapping
    resource_refs: tuple[ResourceRef, ...]
    sha256: str

    def __post_init__(self):
        if self.version != SCHEMA_VERSION:
            fail("SCHEMA_VERSION_UNSUPPORTED", "/schema_version", "Unsupported common schema")
        if not isinstance(self.payload, Mapping):
            fail("INVALID_VALUE", "/payload", "Payload must be an object")
        payload = immutable(si_payload(self.payload, require_si=True))
        if not isinstance(self.resource_refs, (list, tuple)) or any(
            not isinstance(ref, ResourceRef) for ref in self.resource_refs
        ):
            fail("INVALID_VALUE", "/resource_refs", "Expected ResourceRef sequence")
        object.__setattr__(self, "payload", payload)
        object.__setattr__(self, "resource_refs", tuple(self.resource_refs))
        if self.sha256 != content_hash(canonical_bytes(self.to_mapping())):
            fail("RESOURCE_HASH_MISMATCH", "/sha256", "Snapshot content hash differs")

    @property
    def schema_version(self) -> str:
        return self.version

    def to_mapping(self) -> dict:
        """Detached SI envelope, excluding its own content hash."""
        return {"schema_version": self.version, "payload": json_value(self.payload),
                "resource_refs": [ref.to_mapping() for ref in self.resource_refs]}


def freeze_config(mapping: Mapping) -> ConfigSnapshot:
    fields(mapping, {"schema_version", "payload"}, {"resource_refs"}, "")
    if mapping["schema_version"] != SCHEMA_VERSION:
        fail("SCHEMA_VERSION_UNSUPPORTED", "/schema_version", "Unsupported common schema")
    if not isinstance(mapping["payload"], Mapping):
        fail("INVALID_VALUE", "/payload", "Payload must be an object")
    payload = si_payload(mapping["payload"])
    resources = mapping.get("resource_refs", [])
    if not isinstance(resources, (list, tuple)):
        fail("INVALID_VALUE", "/resource_refs", "Expected an array")
    refs = []
    for i, resource in enumerate(resources):
        if isinstance(resource, ResourceRef):
            refs.append(resource)
            continue
        path = pointer("/resource_refs", i)
        fields(resource, {"id", "sha256", "media_type"}, set(), path)
        try:
            refs.append(ResourceRef(**resource))
        except ValueContractError as exc:
            fail(exc.code, path + exc.path, exc.message)
    envelope = {"schema_version": SCHEMA_VERSION, "payload": payload,
                "resource_refs": [ref.to_mapping() for ref in refs]}
    digest = content_hash(canonical_bytes(envelope))
    return ConfigSnapshot(SCHEMA_VERSION, payload, tuple(refs), digest)
