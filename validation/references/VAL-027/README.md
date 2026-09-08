# VAL-027 R4 reference qualification

`reference.py` executes DOP853 on the current complete selected RHS with the frozen tolerances and all 801 finest endpoints. Its cross-run discrepancy is recorded but never used as an absolute certificate.

The three standalone qualification commands accept `--output-dir` and were ported from the independently reviewed R4 BCR evidence:

- `scalar027.py`: independent scalar MC/DOP853 and four long-double RK4 refinements.
- `certify027_residual.py`: exact Fraction cubic-Hermite/Bernstein residual enclosure, including all branch ambiguity, and rational exponential majorant with logarithmic norm 48.
- `certify027_target.py`: exact analytic cell-average initial enclosure, timestamp allowance and exact lift to all 12 conservative components, compared with the newly generated full-RHS reference.

The accepted SV-027 target is the exact-real material contact invariant subspace. These tools do not certify an arbitrary rounded-Q0 full-state ODE or experimental validity. No candidate output constructs the reference. Original R3 failures remain under `artifacts/S06-R3-preserved/VAL-027`; current runs write `artifacts/VAL-027`.

The acceptance adapter executes and qualifies the reference before all five actual SSPRK2 sequences, uses the certified density-L1 uncertainty for the order-floor check, preserves every endpoint, and checks source identity throughout the run. A failed or interrupted command cannot produce PASS.
