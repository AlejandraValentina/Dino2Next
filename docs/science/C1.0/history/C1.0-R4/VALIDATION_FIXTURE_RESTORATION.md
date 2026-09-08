> **Normative — C1.0-R3** · Status: `SCIENTIFIC_IMPLEMENTATION_BASELINE_FROZEN`
> Revision: explicit H-01/H-02/H-03 adjudication. See the R2 BCRs; R1 history is preserved byte-exact.

# Restored validation definitions

The active C1 table keeps its current types and thresholds. This annex restores compatible input definitions from C03; it does not resurrect superseded methods, change CFL 0.2 of the current kernel, or assign old meanings to reassigned VAL IDs. Historical inputs below are retained as provenance; the R2 EXECUTABLE_VALIDATION_CATALOGUE and JSON explicitly consolidate current inputs and the unchanged active acceptance table. Historical CFL .3/.15 below is not a production requirement: R2 uses .2/.1/.05.

## VF-001 — VAL-001 restored input/reference definition
Source: C03VAL VAL-001.

 — identidades V0, UNIT_TEST / NUMERICAL_VERIFICATION

PHY-001/002/006. B=.052 m,S=.05 m,l=.101 m,Vclear=1.2e−5 m³,Vcc,TDC=3e−4 m³; θ=jπ/180, j=0…360. Oráculos PMS/PMI exactos y diferenciación analítica. EOS: NASA cinco especies en T={350,400,600,999.999999,1000,1000.000001,1600,2200} K, p={5e4,1e5,1e6,5e6} Pa y cinco puros + premixφ=.6,.7,.8 + productos correspondientes; puros son stress matemático. Observar V,h−u−RT,cp−cv−R,ΣY,elementos,T roundtrip. Identidades: tolerancia γ128κ; roundtripT≤1e−8 K con raíz bracket cerrada y residual de energía≤cv·1e−8 K. Comparación propiedades contra Cantera3.2 con la representación derivada TI-001 (identidad RAW separada): |δcp|/cp,|δh|/max(|h|,cpT),|δu|/max(|u|,cvT)≤10^−8, los presupuestos se conservan sin trasladar evidencia C02/RAW como verificación de la representación derivada. A1000 exigir convención documentada, derivadas unilaterales; no derivada central entre ramas. Fail significa identidad/inversión/dataset incorrectos, no modelo químico validado. Artefactos tablas y condicionamiento.


## VF-002 — VAL-002 restored input/reference definition
Source: C03VAL VAL-002.

 — volumen móvil cerrado V1, NUMERICAL_VERIFICATION

PHY-003. Gas gamma1.4,R287, m=1e−3kg, V(t)=1e−3[1+.2sin(2πt)]m³; T0=600K,U0=mR T0/(γ−1); sin flujo/calor. t∈[0,1]s; pasos100,200,400,800. Uexact=U0(V0/V)^(γ−1), pexact=(γ−1)Uexact/V. Métrica **máximo sobre toda trayectoria**, no sólo último ciclo; escalaU0/p0. Error relativo máximo≤10^−4 en800 y orden≥1.8 en últimos dos pares, además balanceU+∫p dV. El presupuesto 10^−4 limita error de integración del trabajo reversible a escala energética del caso; no se hereda el orden3 aparente del error final C02. Referencia exacta; artefactos trayectoria y cuadratura de trabajo refinada. Fail integración/trabajo.


## VF-003 — VAL-003 restored input/reference definition
Source: C03VAL VAL-003.

 — calor cerrado V1, NUMERICAL_VERIFICATION

m=.001kg,cv=1000J/kgK,H=hA=2W/K,Tw=600K,T0={400,800}K,V=.001m³; sin flujo. tfin=2s, dt={.02,.01,.005,.0025}s. Texact=Tw+(T0−Tw)exp(−Ht/(mcv)). Métrica max|T−Texact|/|T0−Tw|≤10^−5 último nivel y orden≥1.8; Q=mcv(T−T0) con signo correcto y ledger10^−10. Referencia exacta. El límite se deriva de resolver tiempo térmico τ=.5s con dt/τ=.005 y error global RK2 O((dt/τ)²); no valida h de Annand.


## VF-006 — VAL-006 restored input/reference definition
Source: C03VAL VAL-006.

 — Sod V2, NUMERICAL_VERIFICATION

Euler gamma1.4,R1,x∈[0,1], discontinuidad .5; (ρ,v,p)L=(1,0,1), R=(.125,0,.1); t=.2, bordes extrapolados fuera de alcance de ondas; N=50,100,200,400; CFL=.3 y .15. Referencia exacta Clawpack C02 preservada, integrar celda cortando todas las ondas con Gauss16/32; discrepancia cuadratura<10^−10. Normas L1 por variable y residual. A400, L1ρ≤2Δx(ρmax−ρmin); se exige reducción L1 con cada refinamiento, pendiente log2≥.5 en últimos pares. Presupuesto de resolución de dos celdas equivalentes de salto integrado, no porcentaje histórico de potencia. Admisibilidadρ,p>0 y conservation10^−10. Falla solver/refinamiento, no física de motor.


## VF-007 — VAL-007 restored input/reference definition
Source: C03VAL VAL-007.

 — contacto gamma constante V2

Euler gamma1.4,R1,L=(1,1,1),R=(2,1,1),x0=.5,t=.1; N100,200,400,CFL.3, extrapolación; repetir v=0. Referencia exacta contacto x=.5+vt, promedio de celda. |p−1|∞,|v−v0|∞≤10^−10; L1ρ≤2Δx|ρR−ρL| y reducción por refinamiento. Para v=0, masa/energía inicial recuperada a tolerancia roundoff. NUMERICAL_VERIFICATION; artefactos perfiles/ledger.


## VF-009 — VAL-009 restored input/reference definition
Source: C03VAL VAL-009.

 — pulso acústico V2

Euler gamma1.4,R1,ρ0=p0=1,ε=1e−5,x∈[0,1] periódico; ρ=1+εcos2πx,p=1+γεcos2πx,v=sqrtγ εcos2πx. t=.25,N50,100,200,400,CFL.3/.15. Oráculo lineal: trasladar x→x−sqrtγ t; controlar error O(ε²) repitiendoε/2. Observable coeficiente Fourier de presión: amplitud y fase, no sólo L1. A400, errorfase≤π/N, pérdida relativa amplitud≤2(2π/N)²+10ε; orden≥1.8 antes del piso lineal/no lineal. Artefactos coeficientes complejos y soluciones.


## VF-011 — VAL-011 restored input/reference definition
Source: C03VAL VAL-011.

 — área variable V2

A=1+.4(x−.5)²m², x[0,1], gamma1.4,R1. Reposoρ=p=1,v=0,paredes,t=.2,N50/100/200/400; max|v|,|p−1|≤10^−10. Nozzle suave: p0=T0=1,Mthroat=.3; A/A*=M^−1[2/(γ+1)(1+(γ−1)M²/2)]^((γ+1)/(2(γ−1))); raíz subsónica. T=1/(1+.2M²),p=T^3.5,ρ=p/T,v=M sqrt(γT); t=.3,ghosts exactos en cada centro, N50/100/200/400,CFL.3. Referencia estacionaria, promedios ∫AQ por Gauss16/32 (delta<1e−10); L1ρ/ρref≤2e−6 a400 y orden≥1.8. C03 verificó orden con diagnóstico de centros; el fixture contractual exige además promedio de celda, no atribuirlo al ensayo ejecutado. Conservation con fuente geométrica. Transición cónica continua: vértices en caras y mismo control de refinamiento; no salto discontinuo en GEN1.


## VF-027 — VAL-027 restored input/reference definition
Source: C03VAL VAL-027.

 — refinamiento y tiempo aislado

Espacial: reglas por caso anteriores. Temporal interior: N40 fijo, Euler gamma1.4,R1,ρ=1+.01sin2πx,v=.3,p=1,periódico,t=.1. MUSCL-MC/HLLC seleccionado; se conserva también el ensayo minmod para continuidad de evidencia. Las dos variantes se ejecutan separadamente. dt=.002,.001,.0005,.00025. Referencia semidiscreta DOP853 rtol2.3e−14,atol1e−16,maxstep=.0001, contrastada con rtol1e−13/atol1e−15; discrepancia1.4322e−14 L∞ para minmod. MC se contrastó en time_mc.json. Escala1, L1error≤1e−10 último dt y orden1.8–2.2 en dos primeros pares (verificar además que error de referencia sea menor al10% del umbral). No usar esta referencia semidiscreta como verdad física espacial. Para fuente lineal, matrices y y0 en source_selection.json, t1, pasos20/40/80/160, oráculo expm; exigir orden≥1.8 para método seleccionado. Fuente no lineal conjunta sigue BLK-002, no sustituida por expm.


## VF-028 — VAL-028 restored input/reference definition
Source: C03VAL VAL-028.

 — balance de dos zonas (nuevo requisito)

V0/V1 NUMERICAL_VERIFICATION, PHY-003. Exact limit: cp1000,R287,mA=.0003,mB=.0007kg,TA400,TB900K,τ=.01s,Vconst=ΣmRT/1e5, p=1e5Pa,sin flujos externos/calor; tfin=.02s, pasos40/80/160/320. Oráculo mA=mA0exp(−t/τ), HA=HA0exp(−t/τ),mB=mtot−mA,HB=Htot−HA; pconst por gas igual y energía total constante. Error max escalado por mtot/Htot≤1e−6 a320, orden≥1.8; balances10^−10. Ensayo algebraico NASA: semilla2302,1000 estados exactos del script con escala e inputs preservados; identidades deVdot yUdot≤1e−11. Es verificación de cierre, no calificación empíricaχ/κ. Nacimiento/merge/reingreso de zonas están cubiertos por el gate BLK-002, no por este límite.


## VF-022 — VAL-022 motored data contract
MANDATORY_WITH_COMPLETE_FICHE; EXPERIMENTAL_VALIDATION. Sources: C03VAL grouped VAL-017…024 explicitly maps VAL-022 to pc/pcc motored; C02EX EX-02 motored campaign, EX-03/04 operators and acceptance, C03GEN BCR-EX-C03.

Objective: compare motored cylinder/crankcase pressure and work, without combustion. Hardware, geometry, dry gas, thermal state, initial/measured ambient states and operating setpoints are mandatory measured SI inputs from EXR-001/002. Acquire nine normalized speeds and 25/50/75/100% measured throttle at the two measured stabilized thermal states, three independent sessions and initially 200 consecutive cycles, with the preregistered acquisition extension rule. Phase uses independent TDC; initial 0.1 degree acquisition and 0.05 degree integration-bias check. Numerical mesh/time refinement and uncertainty are required before comparison; actual mesh is a convergence-study artifact, not an invented experimental datum.

Reference: independent raw ensemble pressure at cylinder and crankcase; filtering/encoder/geometry covariance per EXR-001. Observables p_c(theta), p_cc(theta), Wc, Wcc. Metric/acceptance: EX-04 residual and 95% covariance-compatible interval, rank-aware vector statistic/distribution, Holm alpha .05 and metrological contrast capacity factor3. No calibration on validation partition, no model-uncertainty inflation. Missing measured data: REQUIRES_EXPERIMENTAL_DATA, not failure of physics. Failed qualified comparison blocks corresponding scientific-validation claim. Required artifacts: raw cycles, SI setpoints/geometry, calibration certificates, covariance, measurement operators, partition hash, simulation/refinement provenance and per-observable decision.

## VF-COUPLED — restored fixture and observation clauses
Source: ARCOUPLED fixed SI fixtures, scope/budgets and phase audit, retained by C1 VERIFICATION_EXECUTION_MATRIX as mandatory execution. Reference execution is still pending, not a missing measurement.



All pipes: L=0.2 m, A=2e-4 m², persistent physical volume. W2 support [0.15,0.2] m, w=20 m⁻¹; λ=0.04 forward and0.06 reverse. No geometry or loss parameter is fitted to candidate output. Initial pipe pressure/composition use a cosine blend between the stated end inventories, T=700 K and u=0. NASA5 properties and formation energy follow TI-001 continuous runtime identity in R3; the lower formation reference is unchanged.

- VAL-013: finite left reservoir V=2e-4 m³,p=130000 Pa,T=700 K, dry model air; right infinite reservoir120000 Pa,700 K, same air. End0.0005 s, fully open.
- VAL-014: moving cylinder B=S=0.04 m,l=0.08 m,Vclear=8e-6 m³,6000 rpm, initial θ=π/2. Initially120000 Pa,700 K, air. Right infinite120000 Pa/700 K. End0.002 s, fully open. The crank-slider fixes V and Vdot; work is integrated with the same stage pressure used by energy.
- VAL-016: left V(t)=2e-4[1−0.08 sin²(πt/0.002)] m³, initially120000 Pa,700 K,premixφ=0.7. Right infinite120000 Pa,700 K,complete lean productsφ=0.7. End0.002 s. The original2ms interval is retained; the coverage audit found that inertia keeps its resolved mass flow forward. The additive VAL016-R1 uses the identical periodic geometry/forcing through4ms and the same1microsecond output spacing to observe reversal.
- VAL-020: same crank-slider as VAL-014; finite cylinder and finite crankcase Vcc=1.5e-4−Apiston s m³. Initial120000 Pa,700 K,air. End0.005 s. The cylinder-facing window opensθ120°…240° with area fraction sin²[π(θ−120°)/120°]; otherwise zero. Opposite connection remains open. Window closure does not remove pipe inventory. Opening/closing instants are integration events.

These fixtures isolate coupling. They do not replace two-zone scavenging, combustion, thermal or complete-engine validation. Orientation of VAL-020 is cylinder→pipe→crankcase, and negative flow represents transfer toward the cylinder.





VAL-013/014/016/020 use T3 persistent physical storage, W2 passive loss and characterized λ. There is no online ambiguous Cd inversion. The candidate is exactly BCR-AR-002: characteristic MC, compression-local acoustic minmod/flattening, HLLC Davis outside and interpolated flux B inside the selected compression stencil, joint conservative stage/final-combination guard, SSPRK2, AF+pΔA.

The input-defined total normalized L∞ requirement is1e−3 for each primary observable. Reference and temporal allocations are each10% of that requirement. Pressure scale120000Pa, temperature700K; mass scaleρ*Vleft(0), energy scale m*cv_air(700)*700, mass-flow scaleρ*a_air(700)*2e−4. Formation energy remains in every balance; only its arbitrary reference contribution is excluded from the normalization. Chemical fractions have scale1. Phase budget4microseconds uses the same isolated extremum or interior zero crossing, never shifted traces. Full waveform applies when an extremum is flat/nonunique. Conservation requirement1e−10 of its physical inventory/throughput scale. Exact machine-readable source: `research/autonomous_resolution/inputs/coupled_accuracy_contract.json`.

For pressure the reference allowance is12Pa; for local mass flow it is6.239136106e−6kg/s. These values predate the reference refinements and have not been increased. The engineering reference estimator uses twice the last intergrid difference divided by2^observed_order−1, with an observed order greater than.5 and separately assessed time/root/roundoff contributions. This is an engineering estimate, not a rigorous PDE interval bound. Pointwise Richardson acceleration was tested and rejected because it did not improve the complete waveform.



## R2 current fixtures

All current execution fields are in EXECUTABLE_VALIDATION_FIXTURES.json and its catalogue. Current VAL018/023/024 numerical meanings are explicitly selected; their older experimental meanings remain history only.

## R3 applicability

TI-004 defines the runtime/reference identity and additional continuity/inversion checks. All original fixture states, timing and thresholds are retained. Previously evaluated RAW references must be regenerated/requalified for TI-001 before a PASS claim.

## R4 explicit amendments to historical fixture descriptions

The earlier VF descriptions remain traceable historical sources. For current execution, SV-008 retains the physical window and adds causally derived computational guards; SV-009 updates only acoustic-extremum slopes with all VAL009 norms/thresholds intact; SV-010 replaces the undefined total-pressure relative operator with the fully specified directional operator; SV-027 adds dt=.000125 to the original four fixed steps and strengthens reference qualification. Exact current definitions are in the R4 executable catalogue/JSON and BCR-S06-VERIFICATION-CONTRACT. This is an explicit contract change, not a code-only correction.
