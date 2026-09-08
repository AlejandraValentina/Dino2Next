# Prototype result and integration limits

Status: bounded research demonstration, not selected BCR recipe and not VAL-008 acceptance. The authorized implementation scope remains blocked until adjudication and full verification. Source hashes are in control-results.json; raw contact inventories, geometry and sample times are in nine contact-*.npz files. No reference position is consumed by prototype.py. The driver's expected_position_diagnostic is comparison only.

## Software guard correction and current evidence

The complete earlier source/results/logs/NPZ snapshot is preserved in historical/before-second-fe-guard, source 52482dda581dd4cef38fbb38c3ae04670cc1a72e2ceee72885288d792ab2c32c. Independent review found that the second forward-Euler state was not explicitly validated before its convex combination. The corrected source be0a1d24dde91ff7cc54c6e7111a320195f113d019cbb068b98800337a68ca32 now constructs and validates that state with NASA before combining it. Diagnostic entries carry transaction ID, stage and ACCEPTED/REJECTED status; nontrial recoveries are explicitly OBSERVATIONAL. Failed trials retain their own diagnostics and no inventory/ledger is committed.

Actual controlled-RHS reproducer: FE2 width −0.5 was previously hidden by final width +0.25; historical code accepted, corrected code rejects NONPOSITIVE_REGION. guard-reproducer.json binds both sources. A second test exercises inadmissible FE2 energy with an otherwise admissible final temperature. These are explicit software guard tests, not claimed physical wave solutions.

Current verification: 10 tests PASS in 0.79 s. All nine contact controls and both pressure/interaction controls reran successfully in 35.94 s. Every array in all ten retained contact/shock NPZ files is bitwise equal to its historical counterpart; added guards did not change these accepted trajectories. Current contact errors and diagnostic ledger maxima remain those below. Per-contact transaction diagnostics are now stored and hashed; pressure-jump and shock diagnostics are also retained. The 19.57 s and seven-test measurements below describe the earlier demonstrated version and remain historical measurements, not the cost of the corrected source.

Actual run: nine contacts, three contractual compositions/temperature pairs and u=0,+100,-100 m/s, 24 moving intervals, end time 0.001 s. Largest pressure perturbation across all intervals and steps: 3.6435085348784924e-7 Pa. Largest velocity perturbation: 6.971185989651457e-10 m/s. This bounds exterior perturbations as well; it is not a separately masked full catalogue norm. Moving material interfaces travel 0.1 m and cross fixed observation faces of spacing 1/12 m. No conservation correction is performed.

The separate 150/100 kPa pressure-jump control produces velocity 44.5869 m/s. A second control starts a pressure jump strictly left of the composition interface; by 0.0008 s it produces a 23193.0 Pa pressure change in the CO2 parcels and interface velocity 95.1060 m/s. These show that the solver does not force pressure uniformity or freeze physical waves. They are smoke controls without a qualified shock oracle, convergence sequence or full contractual shock coverage.

Total measured driver evolution cost: 19.57 s in the existing WSL Python3.12 environment. Contact cases used 30–49 steps and about 0.06–3.25 s each. NASA calls use a bounded exact-argument successful-call cache; no alternative caloric EOS is used. The prototype is small enough for this demonstration, but these costs do not establish the full 2T simulator's budget.

Seven local software/algebra tests passed in 0.49 s. They check immutable input/rejected attempts, retry after oversized step, conservative split, geometric crossing/projection, pressure work and unconstrained waves, tiny-region step restriction, smooth physical compositions, and invalid state rejection. These do not replace independently qualified numerical acceptance.

## Equations and state correspondence

For interval r of width V_r (unit area), I_r=V_r U_r. Face location satisfies dx_f/dt=s_f. Reynolds transport gives dI_r/dt=G_left−G_right with G=F−sU. Here all faces are Lagrangian and use the HLLC-Davis contact speed s=u*. The material-face flux is G=(0,p*,p*u*,0,...). One identical flux array supplies both signs, so internal transfers cancel. No mass, chemical or provenance transfer crosses that moving material face in the chemically frozen inviscid operator. A label identifies a parcel region, not a species or additional thermodynamic phase.

The first-order Riemann inputs are recovered from each region's own inventory and geometry by the accepted ThermoModel. Derived chemical fractions use the TS-004 division with recorded sum; stored masses and energy remain unchanged. Pressure and temperature are not obtained by applying NASA to the observation cell's aggregate inventory.

SSPRK2 advances the tuple (all positions, all I_r) with a fixed region indexing during both stages: Y1=Yn+dt L(Yn), Yn+1=.5Yn+.5(Y1+dt L(Y1)). Geometry and pressure-work use the same stage. Width is the difference of its two evolved faces, giving the same discrete geometric conservation relation as the positions. Crossing a fixed observation face creates a different overlap list only when sampling; it does not change integration topology. No averaging of unrelated region lists is used. Explicit splitting is permitted only between complete steps. Disappearance, coalescence and relabeling are not implemented.

The global raw conservation residual is sum I_final−sum I_initial−integrated exterior flux. The diagnostic normalizer currently printed is max(sum|I_initial|,1), per component, with maximum 1.77636e-15. Mass/species/provenance residuals are zero in this run. **This is not the full ST-003 normalizer:** no ledger PASS is declared. Raw signed external ledgers are retained for the parent's independent ST-003 audit. Exterior endpoints move with adjacent fluid and exert that state's pressure; this is a local moving-domain control, not the accepted GEN1 physical-boundary implementation.

## Limits that must remain visible

- This moves every parcel face and uses first-order spatial states. It is not a localized replacement for the existing Eulerian MUSCL kernel and changes smooth-state transport too. Existing S06 numerical evidence cannot be reused automatically.
- Tiny regions are retained and constrain time step. Attempts can reject/halve the whole step without changing input. There is no published/qualified same-material agglomeration implementation yet; arbitrarily small regions may make this route impractical.
- Splitting assigns first=alpha I and second=I−first, with NASA recovery checked afterward. Distinct thermal regions are never merged to enforce pressure. This is not a full topology-change algorithm.
- Smooth composition is initialized from physical samples into parcels. When only a stored homogeneous Q is available, the prototype has no method to infer previously lost subcell history. It requires physical initial intervals or an independently justified initialization model.
- The correspondence to GEN1 is only inviscid, chemically frozen transport. Diffusion, mixing, chemistry, ports, varying area, multi-zone interactions and cycle events are outside this prototype. No immiscibility law has been added.
- A possible future coupling would use s=u* only at material boundaries and s=0 on ordinary Eulerian faces with general F−sU; crossing, conservative same-material reorganization and stage topology then require a separate derivation and review. That coupling is not implemented or approved here.
- S05 aggregate Q can remain a conservative projection, but its current single NASA primitive cache and geometry pressure source cannot silently become physical regional observables. State/storage and S07 consumer impacts require architecture adjudication.

No assertion is made that this is the only possible conservative treatment, that alpha alone can never support another closure, or that this isolated-contact demonstration covers GEN1.
