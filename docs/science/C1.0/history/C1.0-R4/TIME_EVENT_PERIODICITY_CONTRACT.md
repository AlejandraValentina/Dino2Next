> **Normative — C1.0-R2** · Status: `SCIENTIFIC_IMPLEMENTATION_BASELINE_FROZEN`

# Time, source, event and periodicity contract

## TS-001 — NUM-002, exact prescribed reaction in unsplit SSPRK2
The prescribed closed-cylinder extent is xi(t)=eta xi_max xb(theta(t)), in kmol, captured at SOC; xi_max=min(nfuel,nO2/12.5). All combustion must lie within closed ports. There is no kinetic ODE or LHV source. Let b contain stoichiometric mass coefficients nu_k M_k only in the burning inventory's chemical coordinates and zero in total energy, momentum, total mass and origin tracers. Set Z=Q−b xi(t). Outside burning intervals b=0. This affine, time-dependent coordinate transformation is SELECTED; the standard SSPRK2 tableau is unchanged:

1. Qn=Zn+b xi(tn); K0=L_nonreaction(tn,Qn).
2. Z1=Zn+dt K0; Q1=Z1+b xi(tn+dt). Check Q1.
3. K1=L_nonreaction(tn+dt,Q1); Z2=Z1+dt K1; Q2=Z2+b xi(tn+dt). Check Q2 (an algebraic RK trial, not a state at tn+2dt).
4. Znew=(Zn+Z2)/2; Qnew=Znew+b xi(tn+dt). Check Qnew.

All other state coordinates follow the same unsplit RHS at the same two times. Total energy changes only by its physical work/heat/flux terms; recomputing T from formation-inclusive energy accounts for combustion. Chemical ledger adds b[xi(tn+dt)−xi(tn)] exactly once, not twice, plus dt/2 of both nonreaction stage fluxes. Elemental sum b is zero within molecular-weight roundoff; record that error, never normalize chemical masses to repair it. The final convex combination is in Z, not old-time physical Q. The high/low flux guard must evaluate these exact physical Q1/Q2/Qnew tests; its admissible low-order trial is not a license to use an outdated xi. A trial may fail even though the SSP tableau is stable; reject globally.

This avoids a quadrature-dependent terminal burn fraction without hidden splitting. It is a DINO2NEXT_SPECIFIC_ADAPTATION of a prescribed-source change of variables. The published SSP guarantee alone does not prove positivity for this transformed, coupled RHS. Trial EOS/simplex checks and future combined-source verification remain compulsory. No combustion-stage reconstruction is applied in open ducts.

## TS-002 — NUM-005, combined RHS table
All entries use the current common physical stage Q(t); evaluate closure parameters at that same time. Cells store mean AU; multiply intensive sources by physical A. Extensive 0D inventories use physical volume.

| Contribution | Conserved target | Energy effect | Admissibility / ledger |
|---|---|---|---|
| Flux divergence | all AU components | total-enthalpy face flux | one shared flux; true upwind composition |
| AF+pDeltaA geometry | momentum only p_i DeltaA/dx | zero for fixed passage | pressure/support impulse ledger |
| W2 | −lambda w A rho u abs(u)/2 momentum | zero total energy | lambda≥0; kinetic→internal; entropy production≥0 |
| Churchill wall shear | −fD A rho u abs(u)/(2 Dh) momentum | zero total energy | no force at u=0; positive fD |
| Measured local K | −K wK A rho u abs(u)/2 momentum | zero total energy | only disjoint measured loss regions; no W2 duplication |
| Heat | energy h Pw(Tw−T) in pipe, h Area(Tw−T) in volume | signed external heat | thermal rays; wall heat ledger |
| Zone exchange | paired masses, species, tags, enthalpy | net internal transfer zero | donor mixture, same exchange in both zones |
| Combustion | affine b xi in TS-001 | no total-energy source | captured reactant extent, elemental ledger |
| Moving volume | 0D energy −p Vdot; zone H derivatives PHY-003 | pressure work once | positive exact V(t); moving-work ledger |
| 0D/T3 coupling | paired mass, total enthalpy, species, origin | paired transfer | BC-007, no stale boundary stage |

Two-zone pressure-equilibrium derivatives are exactly PHY-003/PHYSICS_RESTORATION_ANNEX. Do not advance both its enthalpy equation and an additional independent −pVdot energy source. Reconstruct U=sum H−pV to audit the balance. At SOC the selected conservative merge gives one homogeneous burning inventory. Physical extents, map interpolation and algebraic EOS are evaluated before closure RHS, then boundaries, then shared flux/source assembly; this dependency order does not split time integration.

## TS-003 — NUM-006, bounds
Compute each bound at Qn before a trial and again at Q1. A trial dt larger than any second-stage bound rejects the entire trial; do not change dt in mid-stage. Bounds on affine transport are conservative predictors, not substitutes for physical Q2/Qnew checks. Definitions with zero denominator are +infinity unless their numerator is already inadmissible. Use the minimum over every inventory/cell/zone/face.

* dt_acoustic=0.2 min dx/(abs(u)+a), including all T3 cells. Zero-area wall faces do not eliminate their cells.
* dt_donor=0.5 M/sum(mdot_out). Sum ALL outgoing interfaces and zone exchanges before crediting any incoming material. No outgoing rate from an empty donor is allowed.
* dt_species and dt_origin=0.5 Mk/sum(outgoing rate of k), including internal exchanges. Also include 0.5 q/(−Lq) for each nonnegative coordinate with negative net nonreaction derivative. A zero coordinate with negative derivative is an inadmissible RHS. No per-interface budget reuse. Exact prescribed reaction is handled separately below.
* dt_temperature=0.5 times first positive EXIT along the current nonreaction affine FE ray, for both Tmin=300 and Tmax=2200. For M,P,E,Mk, set I=E−sum Mk e_k(Tb), dI=dE−sum dMk e_k(Tb); c=(2MI−P²,2(M dI+dM I−P dP),2 dM dI−dP²). Find the first exit of c0+c1 t+c2 t²≥0 at Tmin and its negative at Tmax, intersected with positive mass. Stable quadratic roots use q=−(c1+copysign(sqrt(D),c1))/2, roots q/c2,c0/q; linear/constant degeneracies handled exactly. Tangency without exit gives no limit. Domain EOS is checked additionally using exact endpoint reaction. For 0D set P=0; for a zone use enthalpy margin H−sum Mk hk(Tb), a linear ray. Positive pressure/volume remain separate constraints.
* dt_loss=0.5 abs(P)/sum(abs(opposing momentum source)) for W2, wall shear and local K only. Do not include acoustic/pressure acceleration in this sign-preservation budget: physical flow reversal is allowed. At P=0 all passive drag sources must be zero.
* dt_geometry=0.5 V/abs(Vdot) for each moving volume, AND stop at the next positive root of V(t)=0 if one exists. Actual analytic V at both stages must remain positive. A configured crank-slider with nonpositive minimum volume is rejected before running.
* dt_zone=0.5 kappa/omega, plus the donor and species budgets above. New zero-mass zones receive only the admitted inflow limit; never seed mass. If a step would exhaust an outgoing donor it is rejected; exact zero topology events use the defined limits/merge, not epsilon deletion.
* dt_reaction=next burn-end time minus t while burning. Monotone prescribed xi cannot exceed eta xi_max; require 0≤xi≤xi_max at both stage times. Because the burn is closed and homogeneous, exact stoichiometry cannot deplete a reactant beyond its SOC inventory; no explicit kinetic CFL or artificial remaining-reactant half-step is needed. Reject an input that overlaps burn with an open port. Thermal failure due to reaction is caught in Q1/Q2/Qnew and triggers retry; a physically out-of-domain complete burn must ultimately fail, never be truncated.
* dt_window=next known extremum/breakpoint of the opening spline minus t; on each smooth segment also impose 0.5 Aface/abs(dAopen/dt). Scale by physical Aface, not Aopen, so the bound is finite at opening. This controls coefficient variation without creating storage. Lambda interpolation boundaries use the characterized map domain guards; no coefficient extrapolation.
* dt_event=next strictly future event time minus t, calculated from unwrapped crank angle and omega=2pi RPM/60. Fixed RPM per point. Output sample instants are also exact step endpoints.

Global dt=min(all above, requested maximum dt). All 0.5 and 0.2 constants are retained from C1. A positive representable step below the next event must exist; otherwise TIME_RESOLUTION_EXHAUSTED. These sufficient predictors can be conservative. Their efficiency and nonlinear adequacy are MANDATORY_VERIFICATION_DURING_IMPLEMENTATION, not claimed by this adjudication.

## TS-004 — transactional recovery / ledgers
Use one complete snapshot of physical inventories, Z/extent state, geometry/event cursor, zone/cohort state and accumulated diagnostics. On inadmissible stage, root failure or stage-bound violation restore it, halve dt and retry. At most 16 retries AFTER the initial attempt. If still failing: ADMISSIBILITY_RETRY_EXHAUSTED with all dt bounds, failing component, stage, state, map/root diagnostics and retry count. Event counters and physical ledgers commit only after a successful step; failed-attempt diagnostics are retained separately. Map/data invalidity is a configuration failure, not a retryable scientific choice.

Simplex fractions are derived from stored nonnegative constituent masses; a discrepancy ≤256 eps in their floating-point SUM permits only division of the derived fractions by that sum with a roundoff record. Never change stored masses/energy, erase a negative species, or normalize a physically inadmissible composition. Conservation scale is ST-003. Per-interface signed copies must cancel to roundoff separately from global residuals.

## TS-005 — events
Use unwrapped angle events with exact analytic angle→time conversion. Coincident means the same configured angle, not fuzzy merging of physically distinct inputs; rounding coincidence within 32 eps max(1,abs(theta)) is diagnosed. At every endpoint apply the following rows in order, once per (cycle,event ID). Evaluate the pre-event RHS on the left limit for the just-finished step; begin the next RHS on the right limit. Continuous opening has the same value on both sides; source coordinate endpoints also agree.

| Order | Event | Transition | Ledger |
|---|---|---|---|
| 1 | opening/closing, piecewise opening knots/extrema | update communicating area segment; retain all passage state | no inventory jump |
| 2 | transfer opening | selected whole-network cohort F1→F0 | origin relabel ledger only |
| 2 | exhaust closure / SOC merge when required | merge zones conserving chemical masses, tags, U; solve common T | paired internal transfer, no heat |
| 3 | SOC | relabel cylinder tags to R; capture xi_max and b; set xi=0, Z=Q | origin ledger; no chemical/energy jump |
| 3 | burn end | finish xi=eta xi_max exactly, then store Q and disable b | stoichiometric ledger, no second burn |
| 4 | cycle boundary | after all preceding events, sample period state; reset output accumulators only | physical inventories retained |

If geometry has exhaust closure and SOC at the same angle, merge once before SOC. End-burn and next SOC cannot coincide for the same burn; reject ambiguous event definitions. Transfer opening during burn is invalid. Continuous birth during incoming flow follows the zero-zone limit, not a discrete reinitialization.

## TS-006 — NUM-009 state/scales
Store an identical post-event theta=0 snapshot per cycle. No time/phase shifting. Compare every cell, not averages. Fixed scales are computed once per operating point from measured ambient p_a,T_a, dry-air rho_a,a_a, and cv_air(350 K); let e*=cv_air(350 K)*350 K. Reference pressure p*=p_a. Never use signed formation energy as the sole scale.

| State block | Nonzero reference scale q* |
|---|---|
| 0D total mass, each species, each origin | rho_a Vmax of that physical volume |
| 0D U; zone H | rho_a Vmax e*; zones use parent cylinder Vmax |
| zone mass/species/origin | parent cylinder rho_a Vmax, also for an empty zone |
| reaction xi (kmol) | rho_a Vc,max/Mfuel (kg/kmol) |
| 1D mean rho A and every partial chemical/origin rho A | Abar rho_a per cell |
| 1D mean rho u A | Abar rho_a a_a |
| 1D mean rho E A | Abar rho_a e* |
| any stored pressure / temperature diagnostic | p_a / 350 K |

For each coordinate pair qn,qn−k use S=max(abs(qn),abs(qn−k),q*,256 eps q*). Defect Dk=max(abs(qn−qn−k)/S); retain maxima per subsystem. Canonical zone A/B slots are used, absent slots contain exact zeros; no historic cohort IDs. Include every persistent dynamic state; omit elapsed absolute time, event counters, integrated output counters and caches. Reaction is normally inactive at the comparison angle but is still represented consistently.

Output changes are absolute differences divided by FIXED scales: work Wc,Wcc,Wnet use p_a Vd; delivery ratio, trapping, short circuit and retained chemical/origin fractions use 1; delivered/retained masses additionally use rho_a Vd; peak cylinder pressure p_a; reported temperature extrema 350 K. Undefined trapping/short circuit (zero delivery) prevents a successful engine period claim, rather than comparing NaNs as zeros.

Period-1 requires D1≤1e−6 AND every required output change≤1e−4 for three consecutive comparisons. Test lags k=2…8 with the same thresholds for three consecutive comparisons at each lag. If D1/output1 fail and one higher lag passes, report the smallest passing k as MULTIPERIODIC_UNSUPPORTED. At 1000 completed cycles without qualification report MAX_CYCLES_REACHED. No averaging can turn it into period 1.

Cold and warm runs that independently qualify period 1 must have cross-state defect≤1e−6 and cross-output difference≤1e−4 with the same scales. Otherwise MULTIPLE_ATTRACTORS_DETECTED and neither is selected silently. A single initialized run can be PERIOD1_CONVERGED but lacks WARM_COLD_CONSISTENCY_VERIFIED; an accepted sweep point requires both. A failed cold or warm run retains its actual failure. A warm seed is provenance-tagged and reprojected only by conservative geometry-compatible mapping; a changed geometry requires a cold initialization, not silent interpolation.

## TS-007 — sources and future gates
[SSP time-discretization primary record](https://drum.lib.umd.edu/items/78e24b83-01d8-4e55-935e-dc8bacaf910c): ESTABLISHED_PUBLISHED_METHOD for the SSP framework; it does not supply Dino2Next reaction or periodicity rules. TS-001, bounds composition and scale selection are DINO2NEXT_SPECIFIC_ADAPTATION, derived here. VAL-005/023/027/028 verify algebra and order; VAL-018/024 the passive sources; VAL-013/014/016/020 the coupled method; VAL-021 the detector plus mandatory full-kernel state→output sensitivity. Frozen tolerances are engineering requirements, not an already demonstrated universal bound on residual output error.
