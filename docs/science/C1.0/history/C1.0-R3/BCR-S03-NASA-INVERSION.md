> **Normative — C1.0-R3** · Status: `SCIENTIFIC_IMPLEMENTATION_BASELINE_FROZEN`

# BCR-S03-NASA-INVERSION

Decision: select B, the derived continuous representation below, under the user's
2026-09-07 authorization limited to S03 continuity and inverse semantics. Adoption
requires independent scientific review and green checks on the PR HEAD. This BCR
does not authorize any other scientific change. Prior C1.0-R2 bytes and manifest
are preserved under `history/C1.0-R2/`; RAW data remain byte-identical.

## Problem and bounded alternatives

The R2 five-species NASA7 energy is not injective at 1000 K. The H2O RAW
counterexample uses T=999.999999 K, p=100000 Pa; the same rho,e,Y also admits
T=1000.0000137967431 K on the valid upper branch. Both pressures are admissible;
the separation is about 1.4796743e-5 K versus VAL-001's unchanged 1e-8 K budget.
The portable `research/bcr_s03_nasa_inversion/` evidence records source identity,
coefficients, both branch intervals, residuals and commands. This is a contract
diagnostic, not a failed production run or completed VAL-001 acceptance.

Only two alternatives were considered:

| Alternative | Conservative solver consequence | Decision |
|---|---|---|
| A: RAW piecewise inversion | Enumerate each admissible interval root, return all roots with intervals, reject no-root energies; a single-temperature API needs additional branch information or an explicit selection policy. RAW upward jumps also leave unattainable energies. Roundtrip can only guarantee membership in the root set, not recovery of the unidentified original T. | Not selected: would propagate branch state/ambiguity into conservative inventories and boundary/source consumers. Selecting the first converged root cannot resolve it. |
| B: continuous derived h,s | Keep cp curves and lower reference; uniquely derive upper integration constants. Positive cv proves a globally unique energy inverse, and positive cp proves a unique enthalpy inverse. | Selected: resolves the representation defect without fitting engine data or changing conservative state. |

## TI-001 — representation and derivation (PHY-002)

Runtime identity is `DINO2NEXT_NASA5_CONTINUOUS`, version `1.0.0`, stored in
`datasets/thermo_runtime_continuous_v1.json`. Its generator is versioned separately
in `research/bcr_s03_nasa_inversion/`; the active C1 manifest binds its output hash.
The source identities are the unchanged `thermo_species.json` and
`thermo_transport.yaml`. The original extract can contain additional species;
runtime selects only isooctane,O2,N2,CO2,H2O in that order. No additional species
are activated.

Use one-based NASA7 coefficients a1..a7, Rk=Ru/Mk and Tm=1000 K:

    cp/Rk = a1 + a2*T + a3*T^2 + a4*T^3 + a5*T^4
    h/Rk = a1*T + a2*T^2/2 + a3*T^3/3 + a4*T^4/4 + a5*T^5/5 + a6
    s_standard/Rk = a1*ln(T) + a2*T + a3*T^2/2 + a4*T^3/3 + a5*T^4/4 + a7
    delta_a6 = (h_low_RAW(Tm) - h_high_RAW(Tm))/Rk
    delta_a7 = (s_low_RAW(Tm) - s_high_RAW(Tm))/Rk

Apply these constants only on the high branch. delta_a6 has unit K; delta_a7 is
dimensionless; the applied h and s offsets are respectively J/kg and J/(kg K).
The derived file records every shift and unit. Low coefficients, including a6/a7,
remain unchanged; all a1..a5 and molar masses remain unchanged. This preserves the
lower formation reference and cp in both intervals. The shifts are derived at
the join, never calibrated. Standard-pressure and ideal-mixture entropy terms
remain unchanged. `e=h-R*T` remains authoritative.

The file stores the source coefficients and additive high shifts as decimal
strings; it is not mislabeled as a byte-equivalent RAW dataset. The generator uses
80-digit Decimal arithmetic (including ln for entropy) and deterministic UTF-8
serialization. That finite representation approximates the exact derived formula;
its tiny serialization error is numerical error, not physical uncertainty.
Runtime binary64 evaluation must satisfy VAL-001 against an independent evaluation
of this same representation; it may not silently substitute the RAW high constants.

The canonical high-branch definition is equivalently anchored at the join:
`h_D(T)=h_RAW_low(Tm)+integral(Tm,T,cp_RAW_high(t) dt)` and
`s_D(T)=s_RAW_low(Tm)+integral(Tm,T,cp_RAW_high(t)/t dt)`.
These are analytic polynomial integrals (plus ln(T/Tm) for entropy), not numerical
quadrature. This anchored form defines exact continuity without claiming that
rounded stored integration constants are exact real numbers. Stable algebraic
evaluation of polynomial differences/log ratios is permitted. The 80-digit
materialized shifts record the same derived representation; their finite rounding
error is measured separately. No input energy is moved to the anchor.

NASA7 formula source: [Cantera 3.2 species thermodynamic models](https://cantera.org/3.2/reference/thermo/species-thermo.html#the-nasa-7-coefficient-polynomial-parameterization).
The continuity adaptation is an explicit Dino2Next decision, not a claim that
the published RAW table is continuous or that Cantera automatically applies it.

## TI-002 — global invertibility and error separation

Check each selected species cv/Rk quartic over the complete closed intervals
[300,1000] and [1000,2200] with certified polynomial bounds, not sampled positivity
alone. Strictly positive species cv implies positive mixture cv for every simplex
composition; cp=cv+R is positive. Continuous h and e therefore are strictly
increasing globally. cp may have its original finite jump: derivatives at the join
are unilateral, never a central derivative across branches. The low branch is used
below 1000 K and the high branch at/above it. Entropy continuity uses the same join.

Three quantities must never be conflated:

1. Algorithm error against the selected derived representation: VAL-001 budgets
   remain 1e-8 K and energy residual <=cv*1e-8 K, with unchanged property budgets.
2. Derived-minus-RAW difference: exactly zero below the join, the recorded h/s
   shifts on the high branch; cp,R,cv and gamma are unchanged. Report these changes
   separately, including their effect on e and inverse comparisons. They are not
   solver error and must not be hidden inside an enlarged tolerance.
3. Physical data uncertainty: this BCR does not estimate it or claim improved
   experimental accuracy.

## TI-003 — ThermoModel inverse contract

`invert_energy(rho,e,Y) -> ThermoState` recovers the unique T of the derived
representation at fixed Y and positive rho, then p=rho*R(Y)*T. All original T and
p domains remain in force. `invert_enthalpy(p,h,Y) -> ThermoState` analogously
recovers the unique T at fixed Y and supplied valid pressure, for boundary/zone
consumers. Species properties expose standard entropy as well as cp,h,e and R.
The original arguments are immutable inputs, never overwritten with reconstructed
energy/enthalpy. Diagnostics retain the target and the signed evaluated-minus-target
residual. Consumers must not replace a conserved energy inventory with a rounded
primitive reconstruction.

Bracket on the contracted temperature domain, split explicitly at the join when
evaluating branch properties. No root outside the domain is usable. An out-of-range
energy or enthalpy is `EOS_OUT_OF_DOMAIN`; a bracketed solve that cannot meet both
the temperature and residual criteria is `EOS_INVERSION_FAILED`. Invalid simplex
or dataset identity retains `COMPOSITION_INVALID` or `DATASET_HASH_MISMATCH`.
No extrapolation, clipping, reference offset of the input state, seed-dependent
branch selection or ambiguous-root success is allowed. A deterministic bracketed
algorithm must produce the same result regardless of any optional initial guess.
The enthalpy residual criterion is cp*1e-8 K; this explicitly supplies the analogous
criterion for the enthalpy inverse and does not loosen energy inversion.

## TI-004 — VAL-001 and independent reference

All existing Cartesian tuples and thresholds remain required. Add 300 K and
join-near/crossing checks to the representation evidence, never remove a RAW
counterexample or a required production test. The RAW counterexample remains a
regression demonstrating why the old original-temperature guarantee was invalid.
The runtime roundtrip now refers to the continuous derived dataset and retains
1e-8 K. Conservation means retaining the supplied extensive state; an inverse is a
property recovery, not a state correction.

Independent references must implement TI-001 without importing candidate thermo,
the generator's property evaluator, or using candidate results as expected values.
Use independent high-precision arithmetic and Cantera 3.2 with explicit derived
integration constants/offsets and branch convention. Bind RAW, derived, generator,
reference code, environment and output hashes. At exactly 1000 K explicitly use
the selected high cp branch rather than relying on a library's equality convention.
Tests cover all five species, air, COMMON-001 premix/products, both endpoints,
one-sided derivatives, cp/cv positivity, h-e=RT, h/e inversion, deterministic
guesses and energy crossings in both directions. Small BCR checks establish the
representation; S03 production acceptance must run separately after integration.

## TI-005 — consumers and mandatory revalidation

All references to NASA5 thermodynamics in current clauses use TI-001. Transport
collision parameters and mixture rules remain RAW-selected; a transport adapter
must install derived thermodynamics when constructing a phase and record both
identities. No RAW energy state can be relabeled as a derived state or replayed
under the new identity. A conversion/replay across representations would require
an explicit separately reviewed procedure; none is supplied here.

| Consumer | Required impact / rerun when implemented |
|---|---|
| S03 EOS/enthalpy | VAL-001: entire property, identity, inversion and endpoint catalogue |
| S04/S05 inventories | Formation-inclusive e recovery, h0 mixing; VAL-002 and constituent-state checks |
| S06 reconstruction/flux | NASA derivatives/secants and admissibility; VAL-006/007/008/009/010/011/027 |
| S07/S08/S09 boundaries/passages/loss characterization | BC entropy/isentrope/Hugoniot and h inversion must use one derived identity; VAL-004 plus all characterization references |
| S10/S11 coupled engine | Moving work, shared total enthalpy, storage; VAL-013/014/016/020 remain mandatory heavy gates |
| S12 zones | Birth h inverse, common pressure, exact merge; VAL-028 |
| S13 reaction | Same stoichiometry and formation-inclusive energy, no LHV source; VAL-005/023 |
| S14 sources/rays | Temperature rays must use derived e/h at bounds; transport cp consistent; VAL-003/018/024 |
| S15/S16 outputs/periodicity | Recomputed reference cv/scales and provenance; VAL-021 remains mandatory heavy gate |
| S18/experimental | VAL-022/025/026 require newly identified candidate outputs; old RAW evidence is not transferred as PASS |

No consumer is implemented by this BCR; no heavy verification or engine run is
performed. This decision changes only representation continuity, identity and
inverse/reference semantics. Five species, formation reference, domains, chemistry,
flow methods, ports, thermal/loss closures and numerical acceptance thresholds
otherwise remain unchanged. Numerical, experimental and predictive claims remain
pending their assigned gates.
