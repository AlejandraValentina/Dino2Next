"""Canonical JSON identity and verification of original resource bytes."""

from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path
import re
from types import MappingProxyType

from dino2next.units import ValueContractError


def fail(code, path, message, **metadata):
    raise ValueContractError(code, path, message, component="provenance", metadata=metadata)


def pointer(path, key):
    return path + "/" + str(key).replace("~", "~0").replace("/", "~1")


def json_value(value, path="", active=None):
    """Copy validated JSON data; tuples/read-only mappings are snapshot equivalents."""
    active = set() if active is None else active
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float:
        if not isfinite(value):
            fail("NONFINITE_VALUE", path, "JSON numbers must be finite")
        return value
    if isinstance(value, (Mapping, list, tuple)):
        if id(value) in active:
            fail("INVALID_VALUE", path, "Cyclic data is not JSON")
        active.add(id(value))
        try:
            if isinstance(value, Mapping):
                result = {}
                for key, item in value.items():
                    if type(key) is not str:
                        fail("INVALID_VALUE", path, "JSON object keys must be strings")
                    result[key] = json_value(item, pointer(path, key), active)
                return result
            return [json_value(item, pointer(path, i), active) for i, item in enumerate(value)]
        finally:
            active.remove(id(value))
    fail("INVALID_VALUE", path, "Expected JSON-compatible value")


def immutable(value):
    """Deeply freeze an already validated, detached JSON tree."""
    if isinstance(value, Mapping):
        return MappingProxyType({key: immutable(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(immutable(item) for item in value)
    return value


def canonical_bytes(mapping: Mapping) -> bytes:
    if not isinstance(mapping, Mapping):
        fail("INVALID_VALUE", "", "Canonical root must be an object")
    data = json_value(mapping)
    try:
        return json.dumps(data, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (UnicodeError, ValueError) as exc:
        fail("INVALID_VALUE", "", f"Cannot encode canonical JSON: {exc}")


def content_hash(data: bytes) -> str:
    if type(data) is not bytes:
        fail("INVALID_VALUE", "", "Hash input must be original bytes")
    return sha256(data).hexdigest()


@dataclass(frozen=True, slots=True)
class ResourceRef:
    id: str
    sha256: str
    media_type: str

    def __post_init__(self):
        for name in ("id", "media_type"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                fail("INVALID_VALUE", "/" + name, "Expected nonempty string")
        if not isinstance(self.sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", self.sha256):
            fail("RESOURCE_HASH_MISMATCH", "/sha256", "Expected lowercase SHA-256 hex")

    def verify_bytes(self, data: bytes) -> None:
        actual = content_hash(data)
        if actual != self.sha256:
            fail("RESOURCE_HASH_MISMATCH", "/sha256", "Original resource bytes differ",
                 resource_id=self.id, expected=self.sha256, actual=actual)

    def verify_file(self, path: str | Path) -> None:
        # Read errors propagate; unavailable resources are never verified successfully.
        self.verify_bytes(Path(path).read_bytes())

    def to_mapping(self) -> dict:
        return {"id": self.id, "sha256": self.sha256, "media_type": self.media_type}
