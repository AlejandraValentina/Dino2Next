# Coupled validation closure

Status: **RUNNING — C03-BLK-004 NOT CLOSED**. BCR-AR-002 is the selected kernel; BCR-AR-001 is withdrawn historical evidence. This is not a frozen contract or an experimental-validation claim.

## Scope and unchanged accuracy requirement

VAL-013/014/016/020 use T3 persistent physical storage, W2 passive loss and characterized λ. There is no online ambiguous Cd inversion. The candidate is exactly BCR-AR-002: characteristic MC, compression-local acoustic minmod/flattening, HLLC Davis outside and interpolated flux B inside the selected compression stencil, joint conservative stage/final-combination guard, SSPRK2, AF+pΔA.

The input-defined total normalized L∞ requirement is1e−3 for each primary observable. Reference and temporal allocations are each10% of that requirement. Pressure scale120000Pa, temperature700K; mass scaleρ*Vleft(0), energy scale m*cv_air(700)*700, mass-flow scaleρ*a_air(700)*2e−4. Formation energy remains in every balance; only its arbitrary reference contribution is excluded from the normalization. Chemical fractions have scale1. Phase budget4microseconds uses the same isolated extremum or interior zero crossing, never shifted traces. Full waveform applies when an extremum is flat/nonunique. Conservation requirement1e−10 of its physical inventory/throughput scale. Exact machine-readable source: `research/autonomous_resolution/inputs/coupled_accuracy_contract.json`.

For pressure the reference allowance is12Pa; for local mass flow it is6.239136106e−6kg/s. These values predate the reference refinements and have not been increased. The engineering reference estimator uses twice the last intergrid difference divided by2^observed_order−1, with an observed order greater than.5 and separately assessed time/root/roundoff contributions. This is an engineering estimate, not a rigorous PDE interval bound. Pointwise Richardson acceleration was tested and rejected because it did not improve the complete waveform.

## Reference independence argument

Three reference families are preserved: (1) conservative WENO5-JS/HLLE/RK4, (2) LGL-DGSEM degree3/local-LF/RK4, (3) WENO5-JS/frozen-NASA Roe secant/RK4. They use independently derived quadrature/Illinois half-Riemann evaluation, checked against Cantera. Candidate coupling uses independent polynomial evaluation and its own bracketing implementation. The source physics, station locations and EOS dataset are necessarily shared; branch/root implementation, reconstruction, flux and integrator are not copied from the candidate. The Roe secant is shared verified mathematics, not the candidate's interpolated flux B.

The accelerated AIR references store only rho,momentum,total energy because composition is exactly constant for014/020; species inventories are AIR times mass. This is an exact reduction, not projection/renormalization of an evolving mixture. VAL016 retains evolving composition and its separate independent reference. Native/Python equivalence is verified on complete trajectories, not inferred from compilation. No `.running` or truncated output is accepted.

Reference-only Roe is restricted to the verified subsonic acoustic sector and fails explicitly at a sonic crossing; no unverified entropy fix is inserted. It is not promoted as a production flux. OpenMP only parallelizes independent face evaluations; its1024-cell trajectory is bitwise identical to the serial result.

## Fixed SI fixtures

All pipes: L=0.2 m, A=2e-4 m², persistent physical volume. W2 support [0.15,0.2] m, w=20 m⁻¹; λ=0.04 forward and0.06 reverse. No geometry or loss parameter is fitted to candidate output. Initial pipe pressure/composition use a cosine blend between the stated end inventories, T=700 K and u=0. NASA5 properties and formation energy are unchanged.

- VAL-013: finite left reservoir V=2e-4 m³,p=130000 Pa,T=700 K, dry model air; right infinite reservoir120000 Pa,700 K, same air. End0.0005 s, fully open.
- VAL-014: moving cylinder B=S=0.04 m,l=0.08 m,Vclear=8e-6 m³,6000 rpm, initial θ=π/2. Initially120000 Pa,700 K, air. Right infinite120000 Pa/700 K. End0.002 s, fully open. The crank-slider fixes V and Vdot; work is integrated with the same stage pressure used by energy.
- VAL-016: left V(t)=2e-4[1−0.08 sin²(πt/0.002)] m³, initially120000 Pa,700 K,premixφ=0.7. Right infinite120000 Pa,700 K,complete lean productsφ=0.7. End0.002 s. The original2ms interval is retained; the coverage audit found that inertia keeps its resolved mass flow forward. The additive VAL016-R1 uses the identical periodic geometry/forcing through4ms and the same1microsecond output spacing to observe reversal.
- VAL-020: same crank-slider as VAL-014; finite cylinder and finite crankcase Vcc=1.5e-4−Apiston s m³. Initial120000 Pa,700 K,air. End0.005 s. The cylinder-facing window opensθ120°…240° with area fraction sin²[π(θ−120°)/120°]; otherwise zero. Opposite connection remains open. Window closure does not remove pipe inventory. Opening/closing instants are integration events.

These fixtures isolate coupling. They do not replace two-zone scavenging, combustion, thermal or complete-engine validation. Orientation of VAL-020 is cylinder→pipe→crankcase, and negative flow represents transfer toward the cylinder.


## Executed reference checks and current limitation

- Independent boundary600states: zero failures; per-unit-area discrepancies versus Cantera≤2.06e−11kg/(m²s),1.92e−8Pa,7.53e−6W/m². Actual fixture transfers multiply these values by2e−4m².
- Native FV/Cantera complete-trajectory equivalence:014128 pressure≤2.80e−9Pa;020128≤6.80e−7Pa against the same quadratic-ghost formulation. An earlier comparison to the different constant-ghost formulation is explicitly not an equivalence test.
- DG SBP/derivative identities and exact NASA smooth entropy transport verified. Closed moving volume matches independent Cantera isentrope within4.95e−10Pa and3.07e−12K. Native/Python DG01432 trajectory pressure≤1.94e−9Pa.
- HLLE reference CF.8 introduces unacceptable local-flow temporal error in020; increasing CFL is not accepted solely for speed. Constant ghost extrapolation does not remove it.
- WENO/Roe0201024→2048→4096 has pressure differences11.5713/7.21630Pa and mass-flow6.32251e−6/3.98118e−6kg/s. Current estimated reference errors23.9152Pa and1.35391e−5kg/s exceed allocation.8192 refinement is running.
- DG014256→512→1024 pressure estimate8.11853Pa is within allocation, but mass-flow1.16869e−5kg/s is not.2048 refinement is running. Different observables are assessed separately; one passing observable cannot qualify the entire oracle.
- Candidate1024 vs current references has pressure differences26.97Pa(014),27.79Pa(020), mass-flow1.1166e−5/1.0366e−5kg/s. These are promising comparisons, not final PASS because the reference budget remains unclosed.

## Invalidations and reproducibility

All pre-fix VAL014 runs with an accidentally moving infinite right reservoir are invalidated and retained under `invalidated/val014_moving_infinite_reservoir/`. The correct right reservoir is fixed120000Pa/700K. No λ or physical geometry was recalibrated. The initial reference root100-iteration cap was insufficient for a1e−17 residual bracket; safeguarded256iterations resolved it without relaxing tolerance. Sources, failed logs, corrected sources and reruns are retained.

Structured results and exact commands live under `research/autonomous_resolution/outputs`, `logs`, `inputs` and the named executable/source files. All code is RESEARCH_ONLY_NON_PRODUCTION. Remaining work is reference qualification, final candidate mesh/time/phase/ledger comparison and explicit adjudication; no full-RHS or periodicity result is claimed here.

## Coverage and observation audit

VAL013 now passes the combined budgets (`outputs/simple_coupled_qualification.json`). Its true reference time-halving sequence isCFL.1/.05/.025; the earlier.2/.1 runs had identical output-capped timesteps and were not a time-order experiment.

VAL016-R1 is additive and never replaces the original2ms results. It retains V(t), physical geometry, λ, stations, composition and all original samples, and extends the same periodic forcing to4ms. The128-cell candidate crosses to reverse near2.618ms with min flow−.00466549kg/s. Full independent mesh/time qualification is running. Early return in this particular fixture is predominantly previously expelled premix; it is not claimed to be a strong chemical-donor contrast by itself. The separately preserved90 independent boundary comparisons cover six donor-composition pairs, four unequal, and both flow directions: max mass/species discrepancies4.45e−13/3.27e−13kg/s and enthalpy-flux7.26e−7W. The1620-point compiled-versus-polynomial check has zero failures. These tests, together with the selected kernel's species-contact tests, supply the separate donor/composition part of the chain.

Phase is not artificially aligned. A five-point quartic locates the same isolated extremum, with decimation and finite-precision inverse-curvature conditioning checks. When interpolation error is not qualified, retain a full neighboring-sample interval for an isolated unimodal peak; never choose a favorable time within it. Add separate spatial-reference phase uncertainty to the worst-case candidate/reference interval distance and require≤4microseconds. All waveform norms continue to use unchanged raw time samples. Exact peak controls are preserved in `outputs/phase_operator_verification.json`; unresolved phase requires more evidence, not a broader threshold.
