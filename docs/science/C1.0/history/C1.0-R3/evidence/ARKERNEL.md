# Numerical reference and kernel qualification

**C10-NUM-NP-02 = CLOSED. C03-BLK-001 = CLOSED.** Selected authority: BCR-AR-002. Global baseline is not frozen; BLK-004/002/003 require independent closure. All executable artifacts are RESEARCH_ONLY_NON_PRODUCTION. Prior C10 and all failed research attempts are preserved.

## NP reference: mathematical formulation

The physical problem is unchanged: NASA air, p0=600000 Pa, T0=800 K, At=1.8e-4 m², Ap=2e-4 m², Ln=Lw=.02 m, λ=.04, pexit=420000 Pa. Expansion area is At+(Ap−At)(3z²−2z³), z=x/Ln. W2 acts only in [.02,.04]. The outlet perturbation is 2000 sin²(πt/.0004) Pa for 0≤t≤.0004 s. End time .0008 s. Perturbed minus unperturbed trajectories are compared without phase alignment.

Let V=(ρ,u,p), U=(ρ,ρu,ρE), E=e(T)+u²/2. Frozen NASA air gives R constant, cp(T), cv=cp−R, and a²=cp p/(cv ρ). Define H=∂U/∂V and B by Vt+B Vx=S:

B=[[u,ρ,0],[0,u,1/ρ],[0,ρa²,u]].

For g=A'/A and f=−λw u|u|/2, the primitive source is S=(−ρug,f,−ρa²ug−(R/cv)ρuf). The last term converts kinetic energy into internal energy; the conservative total-energy source remains exactly zero.

The upstream region in this specific NP is supersonic with fixed inlet and no incident forcing. It is the stationary isentrope evaluated at the moving shock position. This reduction must cease if the shock loses the qualified supersonic upstream/subsonic downstream configuration. It is not a generic reservoir boundary algorithm.

The shock x_s(t), speed s, and downstream trace V+ satisfy F(U+)−sU+=F(U−)−sU−. Jump solution is computed in the shock frame from mass, momentum and h(T)+(u−s)²/2. Lab-frame h0 is **not** imposed equal across a moving shock. Compression and sonic inequalities reject the identity/expansion roots.

Let K=H+(B+−sI). Differentiating the jump relation gives:

V+_x=K⁻¹ H−(B−−sI) dV−/dx,

V+_s=K⁻¹(U+−U−).

The downstream outgoing acoustic compatibility supplies the acceleration:

s_dot = l−·[S+−(B+−sI)Vx+−V+_x s] / (l−·V+_s),

with l−=(0,−ρa,1). x_s_dot=s. This evolves a physical shock trajectory, not a branch chosen by pressure threshold.

The two smooth downstream domains are [xs,.02] and [.02,.04]. In the first, x=xs+(.02−xs)ξ and mesh velocity=s(1−ξ); in the second the mesh is fixed. Chebyshev collocation differentiates smooth fields; the window source discontinuity is a domain boundary. At that boundary, two outgoing positive-speed characteristic time derivatives come from the left region and the negative acoustic derivative from the right. At the exit, p_dot is prescribed by the exact forcing, while contact and positive acoustic derivatives retain their PDE compatibility. DOP853 integrates this system independently of candidate SSPRK2.

A downstream conservation audit compares quadrature inventory changes with the integrated ALE shock flux A(F−sU), physical exit flux and momentum sources. Spectral spatial conservation is checked by refinement, not falsely claimed as an algebraic FV identity. The shock jump is separately verified against Cantera and calorically perfect analytic relations.

## Independence and sources

This reference uses an explicit shock, smooth-domain spectral differentiation, differential characteristic boundary compatibility and an adaptive eighth-order integrator. The candidate uses diffuse shocks, FV reconstruction, HLLC and SSPRK2. Shared physical NASA coefficients and initial steady solution are intentional. Shock jumps are additionally checked against the independently implemented Cantera wave oracle. The reference does not call the candidate flux, reconstruction, time integrator or outlet Riemann routine.

The established method structure is supported by [Hussaini et al., Chebyshev shock fitting, NASA](https://ntrs.nasa.gov/citations/19850039711), [Wang & Zhong, ICCFD7-2305](https://www.iccfd.org/iccfd7/assets/pdf/papers/ICCFD7-2305_paper.pdf) and Salas, *A Shock-Fitting Primer*. The NASA-specific derivatives and W2 extension above are campaign derivations. None of those references is claimed to validate a two-stroke engine.

## Executed evidence and budget

Raw arrays, commands and logs: `research/autonomous_resolution/`. `moving_RH_verification.json` checks 12 NASA moving jumps; largest pressure discrepancy versus the independent wave implementation is approximately1.4e-8 Pa. `gamma_moving_RH.json` checks nine analytic moving jumps, maximum pressure difference approximately5.9e-10 Pa. Full uniform translating-shock ALE checks and reference refinement are recorded separately.

Initial NP shock position: .008028165091955567 m. The incremental pressure differences N16→24, N24→32, N32→48 and N48→64 are tracked, along with tighter integration tolerances. Preliminary N32→48 L∞=.084 Pa, N48→64=.028 Pa; these are differences, not rigorous absolute error bounds. The completed `SHOCK_FITTING_REFERENCE_ERROR_BUDGET.json` assigns a conservative engineering pressure allowance of1 Pa, covering these sources; this is not a rigorous interval-PDE bound. Deterministic barycentric weights and tightened DOP853 reruns are canonical.

The C10 research precision budget is preserved: total pointwise40 Pa for a2000 Pa forcing, with candidate spatial25 Pa, reference10 Pa and time5 Pa. It is an engineering numerical target, not identification σp=100 Pa or an experimental uncertainty. Other C10 waveform/phase/integral/TV requirements remain active. No tolerance is enlarged to admit a failed method.

## Selected kernel and executed comparison

BCR-AR-002 gives the complete algorithm: local-cell NASA characteristic MUSCL-MC, compression-local acoustic minmod and flattening, HLLC Davis outside that stencil and interpolated flux B inside it, joint conservative high/low flux admissibility including the actual SSPRK2 final combination. SSPRK2 unsplit and AF+pΔA remain. There is no changed physical λ, geometry, station, forcing, EOS or acceptance threshold.

| Cells | NP incremental pressure L∞ Pa | L1 Pa | L2 Pa | Total variation Pa |
|---:|---:|---:|---:|---:|
|640|10.0791084|1.550399|2.824555|3621.939|
|1280|6.1128320|.782182|1.394437|3618.726|
|2560|2.9312069|.412305|.685630|3626.186|

Final two spatial refinements decrease. TV satisfies the unchanged1.05-reference gate; peak and phase meet40Pa/4microseconds. The complete metrics are `outputs/interpolated_b_np_metrics.json`. Full five-species Python NP160 independently matches the compiled frozen-air trajectory within1.72e−8Pa, with no flux guard activation.

Final temporal sequence at640, CFL.25… .0078125: nominal-versus-finest1.42481914Pa; last difference.027636864Pa, observed local order1.70884, engineering residual.0243607Pa. Total1.44917985Pa≤5Pa. The earlier nonmonotone differences remain visible; this is not a universal second-order claim for a switching shock waveform. `outputs/interpolated_time_final_metrics.json` is authoritative.

Gamma Sod400 cell-average L1rho=.00235809≤.004375; area4001.3103e−8≤2e−6; rest preservation and contacts meet their separate gates. Smooth acoustic controls retain second-order behavior. Free-end amplitude.008170493≤.01 and Fourier phase5.60647e−5≤π/800. Fourier phase is not a pulse-peak location metric.

NASA contact400 normalized L1/L∞: operational.000118712/.00199967≤.0005/.005; pure thermal.00114618/.0139478≤.002/.02; isothermal.000045308/.00021553. Stationary pressure drift1.46e−11Pa. Mixed NASA shock ratios2/5/10 at80…640cells have decreasing conserved-state L1 error against independent Cantera wave/cell-average references, positive accepted states and ledger closure. The common flux guard is required; unguarded interpolated B and a donor-species-only correction were rejected.

## Failure diagnosis and adjudication history

Primitive MC, uniform characteristic MC, local acoustic minmod alone, localized HLLE, SSPRK3 substitution, characteristic WENO5 and tested artificial viscosity did not jointly satisfy all NP waveform/TV/refinement gates. First-order HLLC is a convergent diagnostic, not production. Global acoustic minmod passed an earlier NP comparison but failed the unchanged free-end amplitude gate; BCR-AR-001 is withdrawn. The selected change addresses the inconsistency of a cell containing a fraction of a moving shock through flux interpolation, not by changing its physical loss.

[Zaide/Roe original slides7–9](https://www.cespr.fsu.edu/people/myh/CFD-Conference/Session-7/Zaide_CFDfutures.pdf) supply flux B's interpolation structure. They do not establish its NASA multispecies extension; that derivation and independent checks follow.

### Derivación propia de la matriz secante multispecie

Con densidades parciales r_k y T_L,T_R, definir barras aritméticas y secantes e_k^d=[e_k(T_R)−e_k(T_L)]/(T_R−T_L). Para temperaturas coincidentes usar cv_k. Sean β=(Σ r̄_k R_k)/(Σ r̄_k e_k^d), ζ_k=T̄R_k−β[e_k(T_L)+e_k(T_R)]/2. La identidad de productos da exactamente:

Δp=βΔ(ρe)+Σζ_kΔr_k.

Las medias Roe de u,H,Y,τ usan pesos√ρ. Con dU=(dρ,dm,dE,dr_k,drτ_j), la presión linealizada es dp=β(dE−ū dm+ū²dρ/2)+Σζ_kdr_k. El producto ĀdU es:

- masa: dm;
- momentum: −ū²dρ+2ūdm+dp;
- energía: −ūH̄dρ+H̄dm+ū(dE+dp);
- especie k: ūdr_k+Ȳ_k(dm−ūdρ);
- tracer j: ūdrτ_j+τ̄_j(dm−ūdρ).

La velocidad acústica secante cumple ā²=Σζ_kȲ_k+β(H̄−ū²/2). Se rechaza ā²≤0, no se reemplaza por un valor positivo artificial. Los vectores acústicos son (1,ū±ā,H̄±ūā,Ȳ,τ̄); el residuo material tras retirar las amplitudes acústicas tiene autovalorū. Esta construcción conserva explícitamente el significado químico y la energía de formación. No es sustituir NASA por gamma constante.

`verify_roe_multispecies.py`:600 estados mezclados, identidad de diferencia de flujo≤2.20e−14 bajo escalas registradas, eigenpair≤9.32e−10, ā² mínimo143020m²/s². Los casos de composición congelada tienen además90 verificaciones de una celda intermedia de shock estacionario contra RH Cantera; error escalado≤7.74e−14, reproducción C++≤7.65e−14. Estas identidades no prueban estabilidad ni positividad de la evolución; los ensayos dinámicos siguen siendo obligatorios.

## Conservative admissibility and explicit limitations

A common pipe-wide flux weight acts on all conserved components, following the conservative principle of [Hu, Adams and Shu2013](https://arxiv.org/pdf/1203.1540). Their constant-gamma positivity proof is not asserted for the NASA upper-temperature set. The returned flux is re-evaluated against both forward-Euler state and actual final SSPRK2 combination. An inadmissible low-order state requests global rollback; no clipping or inventory insertion is allowed. Exact algorithm and failure codes are in BCR-AR-002.

The upper-temperature constraint is not convex: conservative mixing converts velocity variance into internal energy. The retained2200.000010373K example falsifies stage-only checking. Endpoint300/2200K and301/2199K contacts can exhaust recovery even though their exact solution is within EOS. This is an explicit NUMERICAL_ADMISSIBILITY_NOT_RESOLVED result, not PASS, invalid physical input or a reduced domain. Operational400/1800K contacts atphi.6/.8 pass in both directions. The later global retry contract must retain this numerical failure envelope.

## Reproducibility and invalidations

Complete finite output length and end time are checked before promotion from `.running`. A truncated compiled NP control was preserved as invalid and rerun; no incomplete CSV is used. The contact fixture adapter's initial ghost/substr-match errors were corrected, invalidated and rerun. Research corrections never alter historical observations. Exact attempts, rejected results and next discriminating experiments are in AUTONOMOUS_RESOLUTION_LOG.md and structured research outputs.

### Commercial/context evidence boundary

[EngMod2T](https://vannik.co.za/EngMod2T%20-%20OutputsDegree.htm) publicly documents port pressure, Mach, directional-wave and composition traces. [GT-POWER](https://www.gtisoft.com/gt-power/) documents engine performance outputs; [WAVE](https://www.realis-simulation.com/products/wave/) documents1D engine/acoustic/thermal capabilities. These are `PUBLICLY_DOCUMENTED` capabilities; their relevant proprietary internal algorithms remain `PROPRIETARY_INTERNAL_UNKNOWN`. None selects a numerical flux for Dyn2T. Blair R-161 and Benson volumeI were identified through publisher/institutional records; inaccessible full-book equations are not cited as inspected evidence. Exact access scope is recorded in `sources/context_and_new_methods.json`.
