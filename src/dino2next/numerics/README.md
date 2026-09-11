# Selected numerical kernel

NumericalKernel implements C1.0-R3 NK-001..004 and the TS-001 stage composition.
The immutable NumericalProfile accepts only the frozen constants. No global
timestep selection, retry orchestration, boundary Riemann closure or reaction
law is chosen here. VAL-008 remains scientifically blocked independently of
the unit tests of this implementation.

KernelState stores accepted S05 Mesh1D, twelve mean-AU columns, explicit source
kind and thermodynamic identity. NumericalKernel.state(mesh,Q) recovers and
validates before returning it. KernelState.from_duct consumes an accepted
DuctState; every public kernel state entry checks identity and recovers the
physical state. Arrays exported by value objects use immutable byte buffers,
so callers cannot re-enable writes. The row order is rho,rho*u,rho*E, five
chemical partial densities and four origin partial densities, multiplied by
the physical cell-average area. No stored species, origin or energy is repaired.
TS-004 derived-fraction summation corrections have explicit roundoff records.

reconstruct(state,boundary="periodic"|"physical",ghosts=...) returns FaceStates.
Its left/right arrays are conservative per-area states at n+1 faces. The
primitive working columns are rho,u,p,Y[5],origin[4]. Physical boundaries require
four explicit ghost cells per side in per-area conservative units: radius-two
strong-compression detection followed by a radius-two near union reaches four
cells beyond the boundary. Periodic wrapping is used only when selected by
the caller. No physical boundary state is inferred.

Reconstruction uses the cell-average characteristic basis, MC except minmod
on the two acoustic fields near strong compression, N2 and X dependent slopes,
one common 54-bisection contraction per cell, and the frozen flattening factor
applied once after contraction. Every returned face is rechecked.
An unchanged primitive face reuses its original conservative cell state
exactly, avoiding a second floating-point EOS conversion of a zero slope.

interior_flux(faces,boundary_flux=(left,right)) returns FaceFluxes. Flux arrays
are per-area values before physical face weighting. Away from the selected
compression stencil, the high flux is HLLC with Davis speeds and checked star
states. Flux B uses the four cell-average states and the full NK-003
thermochemical secant/absolute action. Low flux is first-order local LF with
max(abs(u)+a). At physical faces both arrays contain the same caller-supplied
flux, and flux B is prohibited there. Reconstruction contractions, flattening
and flux-B face indices are retained in diagnostics.

The NASA backend delegates evaluation and energy recovery to the accepted
ThermoModel and obtains its species e/cv/R from that model, including formation
energy. It does not embed a second NASA or constant-gamma EOS. An explicitly
classified NUMERICAL_FIXTURE_ONLY adapter may provide batch methods for the
canonical mathematical verification cases. Such an adapter must carry identity,
source_kind and an actual reference_sha256 and supply:

- evaluate_batch(rho,p,Y) and recover_batch(rho,e,Y): dictionary arrays
  T,p,e,cp,cv,R,a, each shape (n,).
- species_properties_batch(T): dictionary e,cv,R, each shape (n,5).

The fixture methods receive read-only arrays. They must reject their stated
mathematical domain with ValueContractError and may not claim NASA provenance.
The runtime constructor rejects these adapters unless explicitly classified.

propose_step(state,rhs,time,dt,trial_state_mapper=...,initial_Z=...) performs one
SSPRK2 attempt. rhs receives an immutable KernelState and returns StageRHS:
FaceFluxes plus mean-AU source rates and optional diagnostic tuples. All sources
remain unchanged while one theta blends all faces and all twelve components.
The guard checks the high FE update and, in stage two, the physical mapped
final combination. A failed high update requires admissible low updates, then
the density/constituent linear cap and 54 EOS-tested bisections are applied.
The final shared flux is recomputed and checked; at most eight prescribed
roundoff reductions are attempted.

The mapper receives immutable Z and the physical stage time. With prescribed
reaction, the caller supplies initial_Z explicitly and its affine physical
mapping; the initial mapped state must equal the accepted Q. The callback is
used on Q1, algebraic Q2 and final (Z0+Z2)/2 at the endpoint time. Reaction
coordinates are never advanced or inferred by the kernel. Sources have no
extra LHV term.

StepAttempt contains either an accepted immutable state and committed
area-weighted face / cell-integrated source ledgers, or a rejection with
diagnostics and no published state/ledger. A rejection leaves every original
array untouched and does not automatically halve dt or retry. Face integrals
are dt/2 times the two accepted stage fluxes times face area; source integrals
are dt/2 times both source rates times dx. Reactions remain the caller's
separate exact composition ledger.

ROE_SECANT_NONHYPERBOLIC preserves offending states/acoustic diagnostics;
EOS_OUT_OF_DOMAIN and STAGE_INADMISSIBLE never return plausible replacement
states. Low-order and roundoff guard rejections retain their specific reason
codes. Scientific profile changes require SCIENTIFIC_CHANGE_REQUIRED.
