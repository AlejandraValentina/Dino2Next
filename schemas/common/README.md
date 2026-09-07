# Common software envelope 1.0

S01 introduces the software version `1.0` (distinct from the scientific C1.0-R2
baseline). `freeze_config` requires `schema_version` and an object `payload`;
`resource_refs` defaults to an empty ordered array. Unknown envelope, quantity
and resource metadata fields fail. Arbitrary scientific payload keys remain the
responsibility of later scope schemas. This schema does not certify scientific
validity or replace downstream preflight.

The full `{value, unit, dimension}` object shape is reserved for presentation
quantities; extra keys in that shape fail. Python callers can also use `Quantity`.
They become `{value: SI float, unit: SI unit, dimension: dimension}` objects,
preserving dimension as required by A1. Plain JSON numbers are assumed already SI,
with dimension binding and completeness enforced by the later scientific schema
owner; S01 does not invent dimensions for arbitrary numbers. Incomplete quantity
shapes are ordinary payload objects and must be checked by the scientific owner.
Temperature means absolute temperature, not temperature difference. Dimension
names are length, area, volume, pressure, angle, temperature, speed and power;
speed means angular speed. No physical domain limits are imposed here.

Snapshots deeply copy and freeze mappings/arrays. `to_mapping()` returns a new
mutable JSON envelope with `schema_version`, SI `payload` and ordered
`resource_refs`. The snapshot SHA-256 hashes canonical bytes of that envelope,
excluding the hash itself. A direct constructor expects an SI payload and checks
the supplied hash and rejects presentation units. UTF-8 canonical JSON uses sorted keys, compact separators,
unescaped Unicode and `allow_nan=False`; it preserves array order and JSON
numeric representations (1 and 1.0 have different bytes). No Unicode or signed
zero normalization occurs. Non-string keys and cyclic objects fail.

Resource identity (`id`) remains separate from content identity (`sha256`).
Freezing binds declared references; it does not claim that external files were
read or qualified. Consumers call `ResourceRef.verify_bytes` or `verify_file`
before using a resource. Verification hashes original bytes, including whitespace
and line endings; file read errors propagate and cannot return verification PASS.

Errors are `ValueContractError` with `code`, JSON Pointer `path`, `component`,
`message` and `metadata`. Codes required by S01 are unchanged. `INVALID_VALUE`
additionally identifies malformed software structure/type, missing required
fields, cyclic data or invalid UTF-8. Unknown units share
`UNIT_DIMENSION_MISMATCH`. Nonfinite conversion results (including overflow) use
`NONFINITE_VALUE`; malformed and mismatched hashes use `RESOURCE_HASH_MISMATCH`.
The JSON schema describes structural metadata; finite-number, unit/dimension
pairing and canonical-byte constraints are additionally enforced by Python.
