> **Normative — C1.0-R2** · Status: `SCIENTIFIC_IMPLEMENTATION_BASELINE_FROZEN`
>
> This contract defines implementation requirements. Unexecuted verification gates remain mandatory and may not be relaxed without a Baseline Change Request (BCR).

# Validation and verification specification

Tests are typed as UNIT, REGRESSION, NUMERICAL_VERIFICATION, SCIENTIFIC_VALIDATION or EXPERIMENTAL_VALIDATION. Only the last two support physical claims. Candidate output is never its own oracle. Raw artifacts, input hashes, environment and software versions are mandatory.

| ID | Type | Fixture / reference | Metric and frozen acceptance |
|---|---|---|---|
| VAL-001 | UNIT | NASA tables and independent tabulated values | scaled cp,h,u,gamma ≤1e-8; EOS inversion ≤1e-8 K |
| VAL-002 | NUMERICAL_VERIFICATION | closed moving ideal-gas volume, analytic isentrope, 100–800 cells/steps | finest relative error ≤1e-4; observed order ≥1.8 |
| VAL-003 | NUMERICAL_VERIFICATION | closed heat ODE, m=.001 kg, cv=1000, H=2, Tw=600 K, T0=400/800 K | relative error ≤1e-5; order ≥1.8 |
| VAL-004 | NUMERICAL_VERIFICATION | ideal nozzle/orifice subcritical and choked references | mass, h0 and choking branch within documented oracle uncertainty and 0.1% total scale |
| VAL-005 | NUMERICAL_VERIFICATION | closed UV Wiebe/reaction extent | species/energy ≤1e-10 normalized; exact terminal extent |
| VAL-006 | NUMERICAL_VERIFICATION | Sod exact cell averages, N=50…400 | L1 rho at N400 ≤0.004375; decreasing, order ≥0.5 |
| VAL-007 | NUMERICAL_VERIFICATION | stationary gamma contact | p,u ≤1e-10 scaled; L1 rho ≤2 dx jump |
| VAL-008 | NUMERICAL_VERIFICATION | NASA species/thermal contacts and mixed shocks | operational contact L1≤5e-4, Linf≤5e-3; thermal L1≤2e-3,Linf≤2e-2; positivity/conservation |
| VAL-009 | NUMERICAL_VERIFICATION | periodic acoustic Fourier mode | amplitude ≤2(2π/N)^2+10eps; phase ≤π/N; order ≥1.8 |
| VAL-010 | NUMERICAL_VERIFICATION | rigid/free reflection, N=800 | wall L1≤0.01; free-end amplitude≤1%, phase≤π/N |
| VAL-011 | NUMERICAL_VERIFICATION | variable-area rest and smooth Mthroat=.3 | rest ≤1e-10; L1 rho≤2e-6 at 400; order≥1.8 |
| VAL-013 | NUMERICAL_VERIFICATION | fixed reservoir–T3/W2–duct | all primary waveform errors + reference ≤0.1% physical scale; reference ≤0.01%; phase≤4 us; ledger≤1e-10 |
| VAL-014 | NUMERICAL_VERIFICATION | moving cylinder–T3/W2–duct | same budgets; p·dV, transferred mass/energy and phase mandatory |
| VAL-016 | NUMERICAL_VERIFICATION | original waveform plus additive R1 through 4 ms | same budgets; resolved forward→zero→reverse; donor h0/species and accumulated transfers |
| VAL-018 | NUMERICAL_VERIFICATION | source-only and combined heat/shear/K/W2 | analytic/reference error≤0.1%; total-energy ledger≤1e-10; passive entropy |
| VAL-020 | NUMERICAL_VERIFICATION | moving crankcase–transfer–cylinder with opening/closing | same 0.1/0.01% and phase budgets; retained passage inventory |
| VAL-021 | NUMERICAL_VERIFICATION | complete coupon from cold/warm/high/low composition | NUM-009 thresholds, period 2–8 detection, max-cycle and multiple-attractor semantics |
| VAL-022 | EXPERIMENTAL_VALIDATION | Motored cylinder/crankcase campaign, VF-022 and EXR-001/002 | Preregistered 95%/Holm and metrological capability; REQUIRES_EXPERIMENTAL_DATA |
| VAL-023 | NUMERICAL_VERIFICATION | reaction source limits | no depleted reactant; exact coordinate/species/energy ledgers |
| VAL-024 | NUMERICAL_VERIFICATION | distributed/local loss | sign/passivity/analytic laminar limit and map station semantics |
| VAL-025 | EXPERIMENTAL_VALIDATION | complete reference engine calibration/validation split | GUM uncertainty, preregistered observables; calibration allowed only on calibration partition |
| VAL-026 | EXPERIMENTAL_VALIDATION | held-out rpm/load/phi/exhaust points | no recalibration; preregistered 95% acceptance and multiplicity control |
| VAL-027 | NUMERICAL_VERIFICATION | smooth MOL entropy wave, independent DOP853 | dt=.002…2.5e-4, finest L1≤1e-10, order 1.8–2.2 |
| VAL-028 | NUMERICAL_VERIFICATION | exact two-zone mixing/birth/merge/re-entry | relative error≤1e-6, order≥1.8, ledger≤1e-10 |

Coupled scales: p=120 kPa, T=700 K, mass=rho_air(120 kPa,700 K)Vleft(0), energy=mass·cv_air·700 K, mass flow=rho_air·a_air·2e-4 m², fractions=1. Reference error allocation is 10% of the 0.1% total budget. Phase uses the frozen isolated-extremum/zero-crossing operator without shifting or filtering.

VAL-020 heavy reference execution remains mandatory before `NUMERICALLY_VERIFIED_GEN1`; the recovered 8192 run is complete but does not meet its reference allocation. Failure blocks the numerical-verification claim and requires a BCR before changing method, fixture or threshold. It does not reopen this implementation contract by itself.

## C1.0-R2 documentary restoration
Detailed clauses: VALIDATION_FIXTURE_RESTORATION.md and EXPERIMENTAL_DATA_CONTRACT.md. These are normative companions for their explicit clause IDs; R2 adjudications are enumerated in NORMATIVE_CONSOLIDATION_RECORD.md. No silent precedence override is permitted.

## R2 executable companions

BOUNDARY_CONTRACT.md, TIME_EVENT_PERIODICITY_CONTRACT.md and EXECUTABLE_VALIDATION_CATALOGUE.md / EXECUTABLE_VALIDATION_FIXTURES.json complete the implementation contract. REFERENCE_EXECUTION_CONTRACT.md fixes the independent reference recipes. Heavy verification remains MANDATORY_VERIFICATION_DURING_IMPLEMENTATION, not an implementation prerequisite waived by readiness.
