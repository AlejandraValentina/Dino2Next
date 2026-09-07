> **Normative — C1.0-R1** · Status: `SCIENTIFIC_IMPLEMENTATION_BASELINE_FROZEN`
>
> This contract defines implementation requirements. Unexecuted verification gates remain mandatory and may not be relaxed without a Baseline Change Request (BCR).

# Numerical method specification

## State and space (NUM-001)
Store cell averages $Q_i=\Delta x^{-1}\int A U dx$ in float64 on uniform cells per physical segment; integrate tabulated area exactly by segment. Store all five chemical masses and all four tracer masses conservatively although reconstruction uses independent fractions. Global diagnostics use compensated sums.

## Reconstruction and flux (NUM-003/004)
Recover NASA primitive state. Project primitive differences using the verified thermodynamic eigensystem: local mixture $R,c_p,c_v$ and the full-NASA Roe secant for mixed states; no constant-gamma substitution. Use local-cell characteristic MUSCL. MC limits regular fields. On a radius-two strong-compression stencil, use minmod only for acoustic fields and the frozen flattening thresholds (0.33 pressure ratio trigger, 0.75 compression weight, factor 10 sensor scaling). Reconstruct four species fractions and three tracer fractions; derive the last member. A single cell factor reduces all slopes to the largest admissible value. No component clipping.

Use HLLC with Davis speeds elsewhere. At shock-intersecting interior faces use the AR-002 Zaide/Roe interpolated shock flux B with the verified full-NASA secant. A nonpositive secant sound-speed square is `ROE_SECANT_NONHYPERBOLIC`. Physical boundaries use the half-Riemann boundary solver, never flux B. The conservative high/low flux guard limits shared face fluxes jointly and also verifies the final SSPRK2 convex combination.

## Geometry and sources (NUM-004/005)
Use $A_fF$ and cell momentum source $p_i(A_{i+1/2}-A_{i-1/2})/\Delta x$. All selected physical sources form one method-of-lines RHS. W2, shear and local loss act in momentum with zero total-energy source; wall heat acts only in energy; chemistry advances the exact reaction coordinate and stoichiometric masses without an LHV source. Coupled interfaces use one mass/total-enthalpy/species/tracer flux with opposite ledger signs.

## Time integration and events (NUM-002/005)
SSPRK2 unsplit: $Q^{(1)}=Q^n+\Delta tL(t_n,Q^n)$; $Q^{n+1}=\frac12[Q^n+Q^{(1)}+\Delta tL(t_n+\Delta t,Q^{(1)})]$. Check every Euler stage and final combination. Align steps exactly to port opening/closing, transfer/exhaust relabel/merge, SOC, burn end and cycle boundary; coincident events execute in the order topology → conservative relabel/merge → combustion coordinate. An event is applied once using unwrapped angle.

The pre-step bound is the minimum of: acoustic $0.2\min\Delta x/(|u|+a)$; exact positive-inventory donor/species ray with factor 0.5; exact formation-aware quadratic lower/upper-temperature ray with factor 0.5; W2/shear/local-loss momentum sign-preservation ray with factor 0.5; moving-volume fractional change 0.5; zone exchange $0.5\kappa/\omega$; remaining reaction-coordinate/reactant bound; next-event time. Bounds are recomputed at each stage. A nonfinite/nonpositive/EOS-domain/simplex/reachable-chemistry violation rejects the whole transaction, restores the last accepted state, halves dt and retries. Maximum 16 retries; then `ADMISSIBILITY_RETRY_EXHAUSTED`. No state repair. Roundoff-only simplex normalization is permitted only when the discrepancy is ≤256 machine epsilon times inventory, with a recorded ledger; otherwise reject.

## Periodicity (NUM-009)
At the identical post-event crank angle compare all 0D masses/energies/species/tracers/zones/reaction coordinates and every distributed conserved cell state. Scales are $S_q=\max(|q|,q_{ambient/reference},q_{floor})$ by physical block; floors are 256 epsilon times its nonzero reference scale. Use the maximum componentwise normalized defect, plus separate subsystem maxima. Period-1 requires state defect ≤1e-6 and successive-cycle changes in indicated work, delivery, trapping, short-circuit, retained composition and peak pressure ≤1e-4 of declared physical scales for three consecutive cycles. Test lags 2…8; if a higher lag passes while lag 1 fails, return `MULTIPERIODIC_UNSUPPORTED`. Stop after 1000 cycles with `MAX_CYCLES_REACHED`, never convergence. Cold/warm final states must meet the same defect; otherwise `MULTIPLE_ATTRACTORS_DETECTED`.

## Verification and failures (NUM-006/010)
Mesh refinement by 2 over at least three levels and time refinement by 2 at fixed fine mesh are mandatory. Smooth order must be 1.8–2.2; discontinuities use exact/reference L1 and dedicated limits. Diagnostics expose every retry, limiter activation, minimum state, source bound, event, root failure and local/global conservation residual. Required named failures include EOS/domain, map/out-of-domain, nonidentifiable loss, no boundary root, nonhyperbolic Roe state, inadmissible stage, retry exhaustion, multiperiodicity and multiple attractors.

## C1.0-R1 documentary restoration
Detailed clauses: NUMERICAL_KERNEL_NORMATIVE_ANNEX.md and STAGE_EVENT_RESTORATION_ANNEX.md. These are normative companions for their explicit clause IDs; missing decisions are enumerated in NORMATIVE_CONSOLIDATION_RECORD.md. No silent precedence override is permitted.
