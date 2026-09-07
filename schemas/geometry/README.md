# Geometry values (common envelope schema_version 1.0)

`GeometryModel.from_snapshot` consumes an accepted S01 `ConfigSnapshot` and binds
its SHA-256 as `config_hash`. The geometry payload has required `crank` and optional
`passages` and `events` arrays. Unknown or missing geometry fields fail.

Crank requires bore, stroke, rod (length/m) and clearance_volume,
crankcase_tdc_volume (volume/m3). Each numeric dimension is an S01 SI quantity
object `{value, unit, dimension}`. Typed constructors receive SI scalars, with
dimensions fixed by the named fields. Count is the sole dimensionless integer.

Passages require component_id, positions (length/m quantity array), areas
(area/m2 array), perimeters (length/m array), count and area_basis.
`PER_PASSAGE` means measured values for one identical physical passage;
`AGGREGATE` means an explicitly already-counted measurement.
`aggregate_areas` multiplies only PER_PASSAGE values, returning new values without
altering originals or count provenance. It is a reporting quantity, not a merged
flow domain. No aggregate value may be treated as one independent transfer's
physical geometry. Positions are strictly increasing, area/perimeter positive.
Samples describe persistent storage, never window communicating aperture; closing
a window never zeros these samples. No length, perimeter, effective Cd area,
window curve or interpolation model is inferred. Later owners consume the
measured data and their normative laws.

Events require theta (angle/rad quantity), kind and component_id. Configured theta
is one-cycle phase in [0,2pi); unwrapped start/end can span positive or negative
cycles. Enumeration uses `(start,end]`, so adjacent intervals share no event.
Occurrence identity binds configured phase, kind, component and integer cycle;
it does not depend on call interval or caller ordering. A returned list can be
changed without changing the model; occurrence values are frozen.

TS-005 kinds and priority: OPENING, CLOSING, OPENING_KNOT, OPENING_EXTREMUM (1);
TRANSFER_OPENING, EXHAUST_CLOSURE, SOC_MERGE (2); SOC, BURN_END (3);
CYCLE_BOUNDARY (4, required phase zero). Same-priority ties use stable event IDs.
Configure the communicating-area event separately from any required relabel or
merge event: enumeration performs no state transitions. Coincident SOC/burn end
for one component is rejected. Burn validity involving open transfers requires
the later owner with the complete burn/opening definition. Near angular
coincidences are retained and diagnosed as ROUNDING_COINCIDENCE at 32 machine
eps max(1,abs(theta)); they are not fuzzy-merged.

Errors use S01 ValueContractError with geometry component and stable scope codes:
GEOMETRY_INVALID, AREA_DOMAIN_ERROR, VOLUME_NONPOSITIVE. VAL-002 is owned by S04;
these S02 mathematical regression checks do not qualify that numerical fixture.
