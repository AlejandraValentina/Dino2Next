> **Normative — C1.0-R4** · Status: `SCIENTIFIC_IMPLEMENTATION_BASELINE_FROZEN`
>
> This contract defines implementation requirements. Unexecuted verification gates remain mandatory and may not be relaxed without a Baseline Change Request (BCR).

# GEN1 operational contract

The exact supported engine and outputs are those in PRODUCT_AND_CAPABILITY_CONTRACT. Required physics: PHY-001…010. Required numerics: NUM-001…010. Required verification: every mandatory VAL in VALIDATION_SPEC. Unsupported cases must fail preflight, never silently approximate.

Required inputs include measured bore/stroke/rod/clearance and crankcase volume; port timing and physical T3 geometry; complete intake/transfer/exhaust area and perimeter distributions; raw bidirectional Cd characterization metadata and certified lambda map; NASA/transport dataset hash; ambient/premix state; ignition/Wiebe parameters; two-zone chi/kappa; wall temperatures/Hcc/Cq; roughness and local K; operating point and initial state. FMEP is optional only in the sense that its absence disables every brake output.

`SCIENTIFIC_IMPLEMENTATION_BASELINE_FROZEN` means Codex can implement without choosing science. `NUMERICALLY_VERIFIED_GEN1` additionally requires all nonexperimental mandatory gates to pass on production code. `SCIENTIFICALLY_COMPLETE_GEN1` additionally requires subsystem and engine scientific validation. `PREDICTIVELY_VALIDATED_GEN1` additionally requires held-out VAL-026 without recalibration.

Contract precedence: GEN1_CONTRACT; PRODUCT_AND_CAPABILITY_CONTRACT; PHYSICS_SPEC; NUMERICAL_METHOD_SPEC; VALIDATION_SPEC; SCIENTIFIC_DECISIONS; BASELINE_DECISION_REGISTER; research/history; legacy. A contradiction must be fixed by BCR rather than hidden by precedence.

## Revision authority
Active revision C1.0-R4: SCIENTIFIC_DECISION_CHANGED=YES, exclusively BCR-S06-VERIFICATION-CONTRACT SV-008/009/010/027; accepted TI-001..005 remains unchanged. C1.0-R2 and earlier bytes remain preserved. Companion annexes elaborate their parent PHY/NUM/VAL clauses at the same authority level; they do not silently override conflicts. NORMATIVE_CONSOLIDATION_RECORD.md scopes each restoration. The predecessor manifest and bytes are preserved in history/C1.0. The historical implementation-frozen status is preserved, but global operational readiness is not established while named specification gaps remain.

## R2 executable companions

BOUNDARY_CONTRACT.md, TIME_EVENT_PERIODICITY_CONTRACT.md and EXECUTABLE_VALIDATION_CATALOGUE.md / EXECUTABLE_VALIDATION_FIXTURES.json complete the implementation contract. REFERENCE_EXECUTION_CONTRACT.md fixes the independent reference recipes. Heavy verification remains MANDATORY_VERIFICATION_DURING_IMPLEMENTATION, not an implementation prerequisite waived by readiness.

## R3 scoped adjudication

Runtime NASA5 means DINO2NEXT_NASA5_CONTINUOUS 1.0.0 under TI-001…005. RAW NASA and transport exports remain immutable source data. The separate BCR is the sole scientific change authorized by R3; other methods, domains, species and thresholds remain frozen. Archived headers retain their historical revision; the active R3 manifest explicitly carries unchanged clauses forward.

## R4 scoped verification adjudication

BCR-S06-VERIFICATION-CONTRACT defines computational guard zones, acoustic-only smooth-extrema slopes, a directional reflection observation operator, and an extra fixed temporal refinement with reference qualification. Only these four decisions change. R3 and earlier bytes/manifests remain preserved. All unaffected clauses, including headers naming their historical revision, are carried forward by the R4 manifest. The exception ends with these adjudications; implementation still cannot choose science or infer numerical acceptance from structural readiness.
