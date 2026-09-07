# Thermochemistry interfaces 1.0

`ThermoDataset.from_files(derived_path, raw_path, transport_path, generator_path,
expected_sha256=..., expected_raw_sha256=..., expected_transport_sha256=...,
expected_generator_sha256=...)` requires explicit hashes and verifies each file's
original bytes against both caller expectations and the frozen R3 identity.
There is no implicit file lookup or built-in replacement dataset. Distinct RAW,
derived and generator identities remain visible through `to_mapping()`.

Construct `ThermoModel(dataset, config_snapshot)` to bind accepted S01 provenance:
the immutable snapshot must reference all four resource hashes. Resource IDs are
application-owned and do not substitute for content identity. A standalone model
may omit the snapshot when its caller injects the verified dataset directly.

The API accepts finite SI scalars and five mass fractions in this order:
`C8H18,isooctane, O2, N2, CO2, H2O`. Fractions are preserved, with no normalization
or replacement of a dependent constituent. A gamma-five arithmetic summation
bound distinguishes representation roundoff from a composition mismatch; negative
fractions always fail. Temperature and pressure comparisons use the strict
contracted intervals, without additional domain tolerances.

- `evaluate(T, p, Y)` returns frozen `ThermoState`.
- `species_properties(T)` returns frozen `SpeciesProperties`, containing read-only
  tuples `names, cp, cv, h, e, s, R`. Entropy is species standard entropy, not the
  mixture entropy including pressure/mixing contributions.
- `invert_energy(rho, e, Y, initial_guess=None)` retains supplied density and the
  original energy target in its diagnostic.
- `invert_enthalpy(p, h, Y, initial_guess=None)` retains supplied pressure and the
  original enthalpy target. Optional guesses are ignored for both inverses, so
  they cannot select a branch or change the result.

Inversion bisects on the contracted interval split at the continuous NASA join.
The final temperature bracket is at most 1e-8 K wide and the evaluated-minus-target
residual must satisfy cv*1e-8 K (energy) or cp*1e-8 K (enthalpy). At an exactly zero
binary64 residual, neighboring representable pressure-bound candidates may be
tested to retain strict pressure admissibility. Such a candidate can cross the
continuous join when a rounded target lies on its other side. The returned
interval encloses both the root bracket (or computed zero) and the accepted
temperature, and must still meet the same width/residual criteria. Pressure is computed from
the unchanged density, R and returned T; it is never clipped to a boundary.
Recovered energy is a property and must not overwrite a conserved inventory.

`ThermoState.to_mapping()` is a detached JSON object conforming to
`thermo.schema.json`. Temperatures are K, pressure Pa, density kg/m3, cp/cv/R and
species entropy J/(kg K), h/e and diagnostic target/residual J/kg, sound speed m/s;
gamma and mass fractions are dimensionless. The runtime representation is
formation-inclusive TI-001, not RAW energy or an experimental accuracy claim.

Failures use `ValueContractError` with `component="thermo"`, stable `code`, JSON
Pointer `path`, message and immutable metadata. Codes are `EOS_OUT_OF_DOMAIN`,
`COMPOSITION_INVALID`, `DATASET_HASH_MISMATCH`, and `EOS_INVERSION_FAILED`.
Frozen result objects detach mutable tuple-field inputs even when constructed
directly. Serialization returns a new mutable copy, never a view of model state.
