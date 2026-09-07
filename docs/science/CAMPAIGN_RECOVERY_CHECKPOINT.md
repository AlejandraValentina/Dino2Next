# Campaign recovery checkpoint

Recovered 2026-09-07 from the C0.10 dossier and the autonomous campaign checkpoint. Classification is based on complete files, completion markers, finite-row checks and recorded hashes; a log line alone is not evidence.

| Evidence | Classification | Consequence |
|---|---|---|
| C01–C09 physical adjudications | COMPLETE_VALID_EVIDENCE | Fuel/NASA species, two-zone scavenging, thermal/loss closures, topology, T3/W2 and offline lambda characterization survive. |
| Explicit-shock NP oracle; NASA Rankine–Hugoniot/ALE checks | COMPLETE_VALID_EVIDENCE | Independent NP reference and its error budget survive. |
| BCR-AR-002 interpolated shock flux qualification | COMPLETE_VALID_EVIDENCE | C10-NUM-NP-02 and C03-BLK-001 are closed. |
| BCR-AR-001 global acoustic minmod | COMPLETE_REJECTED_EVIDENCE | Withdrawn after the free-end amplitude gate failed. |
| Primitive MC, characteristic MC and localized HLLC→HLLE attempts | COMPLETE_REJECTED_EVIDENCE | Useful diagnosis; none is the selected complete recipe. |
| VAL-013 coupled qualification | COMPLETE_VALID_EVIDENCE | Passed fixed reference, time, phase and ledger budgets. |
| VAL-014 DG reference through 2048 and candidate time sequence | COMPLETE_VALID_EVIDENCE | Reference estimates 4.38 Pa and 2.68e-6 kg/s meet allocated budgets; final expensive replay is verification evidence, not a science choice. |
| Original VAL-016 | PARTIAL_NOT_ADMISSIBLE | Waveform gates pass but 2 ms duration does not demonstrate reversal. VAL-016-R1 is the required additive reversal fixture. |
| VAL-016-R1 completed candidate/reference files | COMPLETE_VALID_EVIDENCE | Physical reversal appears near 2.61865 ms; final qualification remains an implementation verification gate. |
| VAL-020 Roe 8192 | COMPLETE_VALID_EVIDENCE, NOT YET QUALIFIED | Complete 2001-row run; pressure error estimate 14.83 Pa exceeds 12 Pa allocation and mass-flow sequence is not asymptotic. It cannot be called PASS. |
| Roe 16384 and interrupted sessions | RUNNING_WHEN_INTERRUPTED | Excluded from PASS evidence. |
| Truncated native VAL-020 CSV | INVALIDATED | Archived and excluded; atomic replay is the valid candidate artifact. |
| Full RHS and periodicity preparations | PARTIAL_NOT_ADMISSIBLE | Derivations are reusable; no executed PASS is claimed. |

## Last valid scientific state

The selected numerical kernel is the AR-002 recipe: local-cell NASA primitive characteristic MUSCL; MC normally; acoustic minmod on a radius-two strong-compression stencil; the specified flattening; HLLC-Davis away from shock-intersecting faces; the verified full-NASA Roe-secant interpolated shock flux at those faces; SSPRK2 unsplit; AF+pΔA; a conservative joint high/low admissibility guard including the final SSPRK2 combination. Physical boundaries retain the selected half-Riemann solution. Clipping is forbidden.

No physical decision remains open. Remaining work is execution of already specified numerical verification: complete coupled reference qualification, full-source timestep/recovery qualification and periodic sensitivity. It is classified `MANDATORY_BEFORE_NUMERICALLY_VERIFIED_GEN1`, not a prerequisite for organizing and implementing the frozen scientific contract.

The historical evidence remains in the preserved campaign archive. Legacy disposition is `SALVAGE`; `MANDATORY_LEGACY_CODE_DEPENDENCY=NONE`.
