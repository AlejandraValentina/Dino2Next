> **Normative — C1.0-R2** · Status: `SCIENTIFIC_IMPLEMENTATION_BASELINE_FROZEN`
>
> This contract defines implementation requirements. Unexecuted verification gates remain mandatory and may not be relaxed without a Baseline Change Request (BCR).

# Numerical method specification

## State and space (NUM-001)
Store cell averages $Q_i=\Delta x^{-1}\int A U dx$ in float64 on uniform cells per physical segment; integrate tabulated area exactly by segment. Store all five chemical masses and all four tracer masses conservatively although reconstruction uses independent fractions. Global diagnostics use compensated sums.

## Reconstruction and flux (NUM-003/004)
Recover NASA primitive state. Project primitive differences using the verified thermodynamic eigensystem: local mixture $R,c_p,c_v$ and the full-NASA Roe secant for mixed states; no constant-gamma substitution. Use local-cell characteristic MUSCL. SV-009 preserves MC for material/species/provenance fields and regular acoustic stencils; its published extremum-preserving slope applies only to acoustic extrema outside near-compression. On a radius-two strong-compression stencil, use minmod only for acoustic fields and the frozen flattening thresholds (0.33 pressure ratio trigger, 0.75 compression weight, factor 10 sensor scaling). Reconstruct four species fractions and three tracer fractions; derive the last member. A single cell factor reduces all slopes to the largest admissible value. No component clipping.

Use HLLC with Davis speeds elsewhere. At shock-intersecting interior faces use the AR-002 Zaide/Roe interpolated shock flux B with the verified full-NASA secant. A nonpositive secant sound-speed square is `ROE_SECANT_NONHYPERBOLIC`. Physical boundaries use the half-Riemann boundary solver, never flux B. The conservative high/low flux guard limits shared face fluxes jointly and also verifies the final SSPRK2 convex combination.

## Geometry and sources (NUM-004/005)
Use $A_fF$ and cell momentum source $p_i(A_{i+1/2}-A_{i-1/2})/\Delta x$. All selected physical sources form one method-of-lines RHS. W2, shear and local loss act in momentum with zero total-energy source; wall heat acts only in energy; chemistry advances the exact reaction coordinate and stoichiometric masses without an LHV source. Coupled interfaces use one mass/total-enthalpy/species/tracer flux with opposite ledger signs.

## Time integration and events (NUM-002/005)
SSPRK2 unsplit with the exact prescribed-source coordinate Z=Q−b xi(t), as specified step by step in TS-001. All shared fluxes and nonreaction sources use the two common stage states. Final combination is in Z, then mapped to physical Q at the endpoint. No LHV source and no Lie/Strang splitting. TS-002…005 give the complete RHS, first-exit bounds, transactional retries and event table; constants remain acoustic0.2, safety0.5 and sixteen retries with halving.

## Periodicity (NUM-009)
At the identical post-event crank angle compare all 0D masses/energies/species/tracers/zones/reaction coordinates and every distributed conserved cell state. Scales are $S_q=\max(|q|,q_{ambient/reference},q_{floor})$ by physical block; floors are 256 epsilon times its nonzero reference scale. Use the maximum componentwise normalized defect, plus separate subsystem maxima. Period-1 requires state defect ≤1e-6 and successive-cycle changes in indicated work, delivery, trapping, short-circuit, retained composition and peak pressure ≤1e-4 of declared physical scales for three consecutive cycles. Test lags 2…8; if a higher lag passes while lag 1 fails, return `MULTIPERIODIC_UNSUPPORTED`. Stop after 1000 cycles with `MAX_CYCLES_REACHED`, never convergence. Cold/warm final states must meet the same defect; otherwise `MULTIPLE_ATTRACTORS_DETECTED`.

## Verification and failures (NUM-006/010)
Mesh refinement by 2 over at least three levels and time refinement by 2 at fixed fine mesh are mandatory. Smooth order must be 1.8–2.2; discontinuities use exact/reference L1 and dedicated limits. Diagnostics expose every retry, limiter activation, minimum state, source bound, event, root failure and local/global conservation residual. Required named failures include EOS/domain, map/out-of-domain, nonidentifiable loss, no boundary root, nonhyperbolic Roe state, inadmissible stage, retry exhaustion, multiperiodicity and multiple attractors.

## Physical boundaries (NUM-007/008)

BOUNDARY_CONTRACT.md BC-001…008 specifies the equal-area, reservoir half-Riemann evaluator, wave sampling, domain300…2200K, bounded roots, partial aperture/wall flux and every failure. No Cd restriction is inserted at this boundary. Physical T3 geometry and W2 are unchanged.

## C1.0-R2 contract integration

NUMERICAL_KERNEL_NORMATIVE_ANNEX.md fixes AR-002, with the sole R4 acoustic-extremum amendment SV-009. TIME_EVENT_PERIODICITY_CONTRACT.md is the complete time/source/event/scale recipe; BOUNDARY_CONTRACT.md is the complete physical-boundary recipe. R2 BCRs record new decisions, not historical restoration. Mandatory numerical execution remains pending.
