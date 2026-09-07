> **Normative — C1.0** · Status: `SCIENTIFIC_IMPLEMENTATION_BASELINE_FROZEN`
>
> This contract defines implementation requirements. Unexecuted verification gates remain mandatory and may not be relaxed without a Baseline Change Request (BCR).

# GEN1 operational contract

The exact supported engine and outputs are those in PRODUCT_AND_CAPABILITY_CONTRACT. Required physics: PHY-001…010. Required numerics: NUM-001…010. Required verification: every mandatory VAL in VALIDATION_SPEC. Unsupported cases must fail preflight, never silently approximate.

Required inputs include measured bore/stroke/rod/clearance and crankcase volume; port timing and physical T3 geometry; complete intake/transfer/exhaust area and perimeter distributions; raw bidirectional Cd characterization metadata and certified lambda map; NASA/transport dataset hash; ambient/premix state; ignition/Wiebe parameters; two-zone chi/kappa; wall temperatures/Hcc/Cq; roughness and local K; operating point and initial state. FMEP is optional only in the sense that its absence disables every brake output.

`SCIENTIFIC_IMPLEMENTATION_BASELINE_FROZEN` means Codex can implement without choosing science. `NUMERICALLY_VERIFIED_GEN1` additionally requires all nonexperimental mandatory gates to pass on production code. `SCIENTIFICALLY_COMPLETE_GEN1` additionally requires subsystem and engine scientific validation. `PREDICTIVELY_VALIDATED_GEN1` additionally requires held-out VAL-026 without recalibration.

Contract precedence: GEN1_CONTRACT; PRODUCT_AND_CAPABILITY_CONTRACT; PHYSICS_SPEC; NUMERICAL_METHOD_SPEC; VALIDATION_SPEC; SCIENTIFIC_DECISIONS; BASELINE_DECISION_REGISTER; research/history; legacy. A contradiction must be fixed by BCR rather than hidden by precedence.
