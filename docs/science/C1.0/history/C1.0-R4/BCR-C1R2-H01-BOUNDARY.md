> **Normative — C1.0-R2** · Status: `SCIENTIFIC_IMPLEMENTATION_BASELINE_FROZEN`

# BCR-C1R2-H01-BOUNDARY

Status: APPROVED — user-authorized preimplementation adjudication, 2026-09-07.

Atomic question: NUM-007/008 reservoir branch and domain.

Alternatives: Unbounded research roots down to200K; instantaneous restricted-Cd branch; bounded equal-area reservoir wave matching.

Selection and rationale: Select BC-001…008. Domain-bounded shock/rarefaction compatibility and x/t=0 sampling, outgoing donor and partial wall flux. Reject external supersonic-jet input; T3 interior supersonic outflow/acceleration remain supported. This closes an implementation interpretation gap using a bounded, testable recipe; it does not claim completed numerical validation.

Published evidence / adaptation: Clawpack Euler wave curves and Cantera3.2 NASA7; published structure, Dino2Next reservoir/domain adaptation. Primary references are linked in BC-008, TS-007 and REF-001. Research/preimplementation_r2 contains executed lightweight checks; no production code is introduced.

Affected scopes: S06/S07/S08/S11/S16/S18. Affected verification: VAL004 and coupled013/014/016/020. Numerical execution remains MANDATORY_VERIFICATION_DURING_IMPLEMENTATION. Acceptance values remain those of C1/R1. A failed future verification cannot be called PASS by changing the fixture, domain or parameter without a new BCR.

Validation impact: none of these checks is independent engine validation. The existing experimental acquisition, loss-characterization and held-out partition contracts remain in force. No new sensor or physics model is selected.

Reversibility: EXPENSIVE; changing this recipe affects implementation interfaces, tests and reference qualification and requires explicit revalidation. Predecessor bytes and hash manifest are archived, not overwritten.
