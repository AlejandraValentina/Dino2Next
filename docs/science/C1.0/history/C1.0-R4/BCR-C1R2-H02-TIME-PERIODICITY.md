> **Normative — C1.0-R2** · Status: `SCIENTIFIC_IMPLEMENTATION_BASELINE_FROZEN`

# BCR-C1R2-H02-TIME-PERIODICITY

Status: APPROVED — user-authorized preimplementation adjudication, 2026-09-07.

Atomic question: Exact prescribed extent in SSPRK2 plus complete scales.

Alternatives: Naive quadrature of Wiebe rate (terminal extent not exact); operator splitting (not selected); affine time-dependent source coordinate.

Selection and rationale: Select TS-001…007 affine Z, shared nonreaction RHS, endpoint reaction map, inventory/temperature/opposing-force rays, exact events, fixed physical scales. Preserve existing constants and thresholds. This closes an implementation interpretation gap using a bounded, testable recipe; it does not claim completed numerical validation.

Published evidence / adaptation: Published SSP framework; affine substitution derived here, Dino2Next-specific bound composition and scale choice. Primary references are linked in BC-008, TS-007 and REF-001. Research/preimplementation_r2 contains executed lightweight checks; no production code is introduced.

Affected scopes: S04/S10/S12/S13/S14/S15/S16/S18. Affected verification: VAL005/018/021/023/024/027/028 and coupled gates. Numerical execution remains MANDATORY_VERIFICATION_DURING_IMPLEMENTATION. Acceptance values remain those of C1/R1. A failed future verification cannot be called PASS by changing the fixture, domain or parameter without a new BCR.

Validation impact: none of these checks is independent engine validation. The existing experimental acquisition, loss-characterization and held-out partition contracts remain in force. No new sensor or physics model is selected.

Reversibility: EXPENSIVE; changing this recipe affects implementation interfaces, tests and reference qualification and requires explicit revalidation. Predecessor bytes and hash manifest are archived, not overwritten.
