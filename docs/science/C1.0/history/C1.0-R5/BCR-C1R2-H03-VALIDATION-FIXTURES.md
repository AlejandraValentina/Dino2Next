> **Normative — C1.0-R2** · Status: `SCIENTIFIC_IMPLEMENTATION_BASELINE_FROZEN`

# BCR-C1R2-H03-VALIDATION-FIXTURES

Status: APPROVED — user-authorized preimplementation adjudication, 2026-09-07.

Atomic question: Close current VAL field-level input/reference/observable omissions.

Alternatives: Historical ID reuse or adapter-defined inputs; explicit current-GEN1 catalogue.

Selection and rationale: Select EXECUTABLE_VALIDATION_FIXTURES.json and its identical catalogue plus REF-001. Separate Fourier operator from pulse diagnostics; exact ODE/source/zone and detector coupons. Reference A WENO5-JS/RK4 and B exact-Godunov/DOP853 independently qualify; no heavy execution in this task. This closes an implementation interpretation gap using a bounded, testable recipe; it does not claim completed numerical validation.

Published evidence / adaptation: Analytic balances, acoustic image solutions, published WENO and exact Euler reference methods. Fixtures, sampling and normalization are Dino2Next adaptations. Primary references are linked in BC-008, TS-007 and REF-001. Research/preimplementation_r2 contains executed lightweight checks; no production code is introduced.

Affected scopes: S03/S04/S06/S07/S11/S12/S13/S14/S16/S18. Affected verification: All24 mandatoryVAL; 022/025/026 remain measured-data contracts. Numerical execution remains MANDATORY_VERIFICATION_DURING_IMPLEMENTATION. Acceptance values remain those of C1/R1. A failed future verification cannot be called PASS by changing the fixture, domain or parameter without a new BCR.

Validation impact: none of these checks is independent engine validation. The existing experimental acquisition, loss-characterization and held-out partition contracts remain in force. No new sensor or physics model is selected.

Reversibility: EXPENSIVE; changing this recipe affects implementation interfaces, tests and reference qualification and requires explicit revalidation. Predecessor bytes and hash manifest are archived, not overwritten.
