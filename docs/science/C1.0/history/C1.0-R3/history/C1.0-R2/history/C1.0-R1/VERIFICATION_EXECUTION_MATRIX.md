> **Normative — C1.0-R1** · Status: `SCIENTIFIC_IMPLEMENTATION_BASELINE_FROZEN`
>
> This contract defines implementation requirements. Unexecuted verification gates remain mandatory and may not be relaxed without a Baseline Change Request (BCR).

# Verification execution matrix

The exact fixtures and thresholds live in VALIDATION_SPEC; this matrix schedules them without altering them.

| Gate | VAL | Independent reference | Compute class | Execution | Failure blocks |
|---|---|---|---|---|---|
| Thermo/geometry/unit | 001–005 | tables/analytic ODE and identities | FAST_PR_GATE | every affected PR | merge |
| Canonical gas dynamics | 006–011 | exact Riemann/Fourier/analytic area cases | PR_SCIENTIFIC_AFFECTED | numerical-kernel PRs | merge |
| Fixed coupling | 013 | WENO5-HLLE-RK4 + independent half-Riemann | MILESTONE_GATE | port milestone | milestone acceptance |
| Moving coupling | 014 | DGSEM-LF-RK4 + independent boundary | HEAVY_VERIFICATION_GATE | cylinder-port milestone | NUMERICALLY_VERIFIED_GEN1 |
| Reversal | 016 + R1 | independent WENO5-HLLE-RK4 | HEAVY_VERIFICATION_GATE | port/coupling milestone | NUMERICALLY_VERIFIED_GEN1 |
| Combined sources | 018,023,024,028 | analytic/source ODE and independent high-accuracy integration | MILESTONE_GATE | source milestones | milestone acceptance |
| Full moving network | 020 | frozen-air Roe-WENO5-RK4 and independent boundary, refine until reference allocation passes | HEAVY_VERIFICATION_GATE | integrated GEN1 | NUMERICALLY_VERIFIED_GEN1 |
| Periodicity | 021 | frozen state/output sensitivity campaign | MILESTONE_GATE | convergence milestone | integrated GEN1 |
| Smooth temporal order | 027 | DOP853 | PR_SCIENTIFIC_AFFECTED | time-integrator PR | merge |
| Engine validation | 025 | preregistered measured dataset | EXPERIMENTAL_VALIDATION | after numerical verification | SCIENTIFICALLY_COMPLETE_GEN1 |
| Held-out prediction | 026 | sealed measured partition | EXPERIMENTAL_VALIDATION | final validation | PREDICTIVELY_VALIDATED_GEN1 |
