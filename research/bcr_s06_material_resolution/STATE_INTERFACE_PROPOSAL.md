# Minimal state-interface extension under review

Author: /root. Status: PROPOSAL, not a frozen API or an accepted numerical recipe. This document addresses the inspected S05 implementation at accepted main15b070b6 and the bounded local prototype. Independent architecture review is required; no production files change here.

The existing `DuctState` stores twelve cell-average A*U columns and eagerly recovers a homogeneous NASA state in its constructor. `primitive()` returns that cache and `geometry_source()` consumes its pressure. Passing a regional projection through that constructor would therefore reproduce B instead of physical A. This is an observable/storage incompatibility, not a reason to alter NASA recovery.

## Proposed additive value object

Introduce a separately named regional state in the S05 gasdynamics module, retaining the existing homogeneous state for explicitly homogeneous data. Its authoritative immutable content is the accepted base-mesh/geometry identity, ordered integration edges in metres, twelve extensive inventories per interval, and material-boundary identities independent of chemical species and origin cohorts. Recovery identity and source classification obey the current NASA/fixture separation. A region may contain all five species and all four origin fractions.

The regional partition is an integration partition; its boundaries may cross the base mesh and need not satisfy `Mesh1D`'s uniform-segment restriction. Do not weaken that restriction for existing meshes. Base-cell ownership and overlap lists are derived. The sum of regional inventory intersections divided by base-cell width supplies a read-only A*U projection. There is only one editable inventory representation.

Public operations must distinguish three products:

* regional thermodynamic states, recovered from each interval's inventory divided by its exact physical volume;
* conservative base-cell projection and global compensated inventory;
* volume-averaged physical observables, integrating the represented regional pressure over overlaps. A homogeneous EOS of the projected average, if requested as a diagnostic, must be explicitly named and must not supply physical pressure to consumers.

Do not claim averaged pressure, temperature, composition and velocity together constitute one homogeneous EOS state. Results must retain enough region/aggregation metadata to identify the reported observable. This is an additive typed interface, not a silent change in `DuctState.primitive()` semantics.

The proposed physical pressure product is explicitly `pressure_volume_average`: sum of the integral A*p over regional overlaps divided by the cell's integral A. It equals the length average in the currently prescribed unit-area VAL008 window. It must not silently replace a length-weighted field in another fixture. A length average, if a consumer explicitly requires it, is separately named and integrates p*dx. Projected chemical/origin fractions and bulk velocity are mass-weighted ratios of the corresponding conserved inventories, not volume averages of regional fractions or speeds. Temperature has no implicit aggregate EOS meaning; expose regional temperatures, with any requested volume- or mass-weighted diagnostic named explicitly. No generic unqualified `primitive_average` is proposed.

For the present piecewise-constant regional prototype, an overlap receives I_region times V_overlap/V_region, with volumes computed from the physical area integral, followed by the explicitly reviewed conservative remainder allocation. This is distinct from a length-fraction transfer when area varies. If the selected near-contact reconstruction is higher order, its overlap integral must be specified and independently checked before replacing this first-order rule. A pressure observable must integrate the same represented thermodynamic field under its declared weighting. These proposed regional products do not change the existing homogeneous VAL011 reference/operator by implication.

Initial data must supply the physical region intervals or a complete regional restart. An input containing only Q remains explicitly homogeneous and cannot be promoted to a uniquely reconstructed contact history. Smooth composition uses the chosen smooth spatial representation; a species fraction or tracer ID is not a material-boundary detector.

## Geometry and sources

S05's `Mesh1D` retains cell-average areas and face areas, but these alone do not uniquely determine an area integral at a newly moved internal coordinate. A regional state therefore needs the already accepted physical polynomial geometry (or another separately qualified exact geometry provider), not interpolation invented from those averages. The bounded constant-area prototype requires no such interpolation. Preintegrated-only geometry cannot silently acquire a moving-interface area law.

For a static duct, regional volume is the accepted integral of A(x) between its evolving edges. A moving numerical face contributes A(x_f)*(F-sU); the geometric momentum source is the region integral of p*dA/dx under the selected reconstruction, evaluated at the same stage. A constant-pressure control must cancel geometric pressure flux and source while preserving the geometric conservation law. These are required derivation/prototype checks before adopting variable-area support; the unit-area prototype does not establish them.

The minimal S05 changes are this additive immutable state, access to the already specified geometry evaluator, explicit projection/observable methods and serialization identity hooks. S06 owns reconstruction, flux, remap, time stages, admissibility and diagnostics. No 0D storage, NASA dataset, port Cd, T3 or W2 law is changed.

## Transaction and consumers

Snapshots include regional geometry, order, identities and inventories. Complete-step remap and both SSPRK Euler endpoints must be admissible before accepting the final combination. A rejected attempt restores all authoritative state, with rejected diagnostics retained as explicitly rejected records. Regional arrays and cache snapshots remain read-only. No stage may average unrelated region indexing.

S07 consumes the actual material trace at the physical interface and one shared exchange ledger. S14 evaluates physical sources on the represented state; it must not double-count a projected and a regional source. S16 composes existing physical bounds with the adjudicated regional motion/volume bounds and physical crossing events. S17/S18 serialize and compare the regional state, geometry and recovery identities, not only projected Q. Frontend consumers receive backend observables and do not recover physics.

The BCR must explicitly grant only these S05 interface paths to S06 implementation, with corresponding S05 regression tests. Existing accepted S05 commits remain historical acceptance of the homogeneous interface. The regional extension and every numerical route it changes require new evidence. Until geometry, near-contact reconstruction, guards, exits and source coupling are adjudicated, this proposal is not sufficient to merge S06.
