> **Normative — C1.0-R3** · Status: `SCIENTIFIC_IMPLEMENTATION_BASELINE_FROZEN`
>
> This contract defines implementation requirements. Unexecuted verification gates remain mandatory and may not be relaxed without a Baseline Change Request (BCR).

# Baseline traceability

| Capability | Physics | Numerics | Validation | Outputs | Legacy dependency |
|---|---|---|---|---|---|
| CAP-001 | PHY-001 | NUM-001,008 | VAL-001,002 | geometry/timing | none |
| CAP-002 | PHY-002,003,005 | NUM-001,002,007 | VAL-002,003,013,014,028 | 0D p,T,m,U,Y | none |
| CAP-003 | PHY-004,007,008 | NUM-001–008 | VAL-006–011,013,018,027 | waves/Mach/flows | none |
| CAP-004 | PHY-005 | NUM-003–008 | VAL-004,013,014,016 | port traces/flux | none |
| CAP-005 | PHY-003,009 | NUM-001,002,007–009 | VAL-016,020,028 | delivery/trapping/residual/SC | none |
| CAP-006 | PHY-002,006 | NUM-002,005,006 | VAL-005,023,025 | heat release/Y | none |
| CAP-007 | PHY-007 | NUM-002,005,006 | VAL-003,018,022 | wall heat/T | none |
| CAP-008 | PHY-008,010 | NUM-002,005,010 | VAL-018,024,027 | indicated/pumping/brake | none |
| CAP-009 | PHY-001–010 | NUM-009,010 | VAL-021,025,027 | status/sweep | none |
| CAP-010 | PHY-001–010 | NUM-010 | all mandatory VAL | manifest/diagnostics | none |

Every mandatory capability has a defined implementation and validation chain. Pending execution is identified in VERIFICATION_EXECUTION_MATRIX rather than represented as a missing link.

## R3 representation traceability

PHY-002 / PH-004 → BCR-S03-NASA-INVERSION TI-001…005 → derived dataset and research/bcr_s03_nasa_inversion generator/checks → S03 ThermoModel → VAL-001. Consumer reruns are enumerated in TI-005. RAW inputs and archived R2 remain hash-addressed; small BCR checks are not production acceptance.
