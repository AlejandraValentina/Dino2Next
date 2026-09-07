# S05 physical cell storage

`Mesh1D(cell_bounds, area_averages, face_areas, perimeter, ...)` receives SI
geometry for one physical passage. Cell widths are m, area averages and face
areas m², perimeter averages m. Each declared physical mesh segment is uniform;
changes in cell width must occur at explicit segment boundary faces. This scope
implements storage and source algebra, not qualification of a numerical flux at
a changed mesh spacing.

Preintegrated geometry is accepted explicitly. For declared analytic geometry,
`PolynomialSegment(left, right, area_coefficients, perimeter_coefficients)` uses
ascending powers of xi=(x-left)/(right-left). `Mesh1D.from_segments` integrates
these input polynomials analytically, with rational arithmetic over the supplied
binary64 coefficients, then rounds final integrals. It supports nonlinear shapes,
including the quadratic VAL-011 geometry; it does not fit or interpolate sparse
measurements. Positive area/perimeter is certified over the full segment by exact
Bernstein subdivision. Uncertified geometry fails explicitly after the finite
subdivision budget. Segment joins are continuous and must occur at mesh faces;
abrupt jumps require a separately specified physical interface.

`Mesh1D.from_geometry(GeometryModel, component_id, cell_bounds, *, segments=...)`
binds accepted S02 measured per-passage data and its ConfigSnapshot hash. The
explicit shape must agree with those measurements. Sample-only or aggregate-only
input is rejected; no interpolation or independent passage geometry is inferred.
`replication_count` is retained as provenance and is never multiplied into stored
area, perimeter, Q or integrated inventories. Topology owners instantiate the
independent physical passages. Closing a communicating window does not change
these mesh or inventory values; opening and Cd are not storage inputs.

`DuctState(mesh, Q, thermo)` stores immutable rows in this order:

1. A*rho average: kg/m.
2. A*rho*u average: kg/s.
3. A*rho*E average: J/m, including internal formation energy and kinetic energy.
4. Five A*rho*Y averages: kg/m, isooctane/O2/N2/CO2/H2O.
5. Four A*rho*tau averages: kg/m, F0/F1/R/X.

`primitive()` returns read-only column tuples and immutable thermodynamic
snapshots. It divides by mean area, recovers u and internal energy, then calls
the injected energy-recovery protocol. Original Q is never replaced by recovered
energy. TS-004 permits only a derived-fraction rescale for sum discrepancy ≤256eps,
with an explicit `(cell, simplex, original_sum)` record; negative constituents
and larger discrepancies fail. Each result retains target energy and signed
recovery residual, source kind and implementation identity.
Recovery values and implementation identity are captured at construction in a
private immutable cache. Later changes to a caller's fixture service cannot alter
an existing accepted duct's primitives or provenance.

The sole GEN1 runtime recovery is the accepted S03 ThermoModel. A separate
`source_kind="NUMERICAL_FIXTURE_ONLY"` protocol seam requires an explicitly
classified adapter, implementation identity and reference SHA256. It permits
later owners to execute contracted mathematical limit fixtures without forging
a NASA ThermoState or introducing another runtime model. S05 supplies no
constant-gamma implementation. Fixture snapshots cannot acquire GEN1 labels.

`integrated_inventory()` uses compensated sum(Q_i*dx_i) and returns kg, kg*m/s,
J and constituent kg. `geometry_source()` returns only the cell momentum source
p_i*(A_right-A_left)/dx_i. No face flux, time advance or physical wall source is
implemented here. Module-level functions expose the same three operations.

Tests verify frozen inputs, admissibility, exact analytic integration, inventory
refinement invariance and constant-pressure geometric balance. They do not claim
VAL-011 nozzle-flow qualification, which belongs to S06, or experimental/predictive
validation. Failures are typed MESH_NONCONFORMING, GEOMETRY_INVALID or
EOS_OUT_OF_DOMAIN; invalid data never produce repaired accepted states.
