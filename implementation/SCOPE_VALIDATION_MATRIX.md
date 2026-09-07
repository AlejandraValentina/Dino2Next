# Scope validation matrix

All 28 identifiers are classified. A number alone does not create a mandatory validation: 012,015,017,019 have no requirement in current C1 and remain explicit nonmandatory entries. VAL-022 is mandatory by CAP-007 and restored as the C03 motored experimental data contract VF-022; S18 owns it. Other incomplete contracts remain explicit in the coverage audit.

Reference owner is accountable for a separate implementation/data source, not permission to use candidate output as its oracle. Fixture, reference and expected bundle has exactly one owner. Rerun scopes have read-only access.

| VAL | Required | Owner | Rerun scopes | Gate class | Reference owner | Fixture owner | CI/milestone | Failure consequence |
|---|---|---|---|---|---|---|---|---|
| VAL-001 | yes | S03 | S18, S22 | MILESTONE | S03 | S03 | owner milestone / NOT_IMPLEMENTED | Blocks NUMERICALLY_VERIFIED_GEN1; preserve failure and require BCR for method/fixture/threshold change |
| VAL-002 | yes | S04 | S02, S18, S22 | MILESTONE | S04 | S04 | owner milestone / NOT_IMPLEMENTED | Blocks NUMERICALLY_VERIFIED_GEN1; preserve failure and require BCR for method/fixture/threshold change |
| VAL-003 | yes | S14 | S18, S22 | MILESTONE | S14 | S14 | owner milestone / NOT_IMPLEMENTED | Blocks NUMERICALLY_VERIFIED_GEN1; preserve failure and require BCR for method/fixture/threshold change |
| VAL-004 | yes | S07 | S09, S18, S22 | PR_SCIENTIFIC_AFFECTED | S07 | S07 | owner milestone / NOT_IMPLEMENTED | Blocks NUMERICALLY_VERIFIED_GEN1; preserve failure and require BCR for method/fixture/threshold change |
| VAL-005 | yes | S13 | S18, S22 | PR_SCIENTIFIC_AFFECTED | S13 | S13 | owner milestone / NOT_IMPLEMENTED | Blocks NUMERICALLY_VERIFIED_GEN1; preserve failure and require BCR for method/fixture/threshold change |
| VAL-006 | yes | S06 | S18, S22 | PR_SCIENTIFIC_AFFECTED | S06 | S06 | owner milestone / NOT_IMPLEMENTED | Blocks NUMERICALLY_VERIFIED_GEN1; preserve failure and require BCR for method/fixture/threshold change |
| VAL-007 | yes | S06 | S18, S22 | PR_SCIENTIFIC_AFFECTED | S06 | S06 | owner milestone / NOT_IMPLEMENTED | Blocks NUMERICALLY_VERIFIED_GEN1; preserve failure and require BCR for method/fixture/threshold change |
| VAL-008 | yes | S06 | S18, S22 | PR_SCIENTIFIC_AFFECTED | S06 | S06 | owner milestone / NOT_IMPLEMENTED | Blocks NUMERICALLY_VERIFIED_GEN1; preserve failure and require BCR for method/fixture/threshold change |
| VAL-009 | yes | S06 | S18, S22 | PR_SCIENTIFIC_AFFECTED | S06 | S06 | owner milestone / NOT_IMPLEMENTED | Blocks NUMERICALLY_VERIFIED_GEN1; preserve failure and require BCR for method/fixture/threshold change |
| VAL-010 | yes | S06 | S18, S22 | PR_SCIENTIFIC_AFFECTED | S06 | S06 | owner milestone / NOT_IMPLEMENTED | Blocks NUMERICALLY_VERIFIED_GEN1; preserve failure and require BCR for method/fixture/threshold change |
| VAL-011 | yes | S06 | S05, S18, S22 | PR_SCIENTIFIC_AFFECTED | S06 | S06 | owner milestone / NOT_IMPLEMENTED | Blocks NUMERICALLY_VERIFIED_GEN1; preserve failure and require BCR for method/fixture/threshold change |
| VAL-012 | no | not required | none | NOT_REQUIRED | none | none | UNASSIGNED_NOT_MANDATORY | No GEN1 execution required; adding it requires normative adjudication |
| VAL-013 | yes | S11 | S08, S09, S18, S22 | HEAVY_VERIFICATION | S11 | S11 | owner milestone / NOT_IMPLEMENTED | Blocks NUMERICALLY_VERIFIED_GEN1; preserve failure and require BCR for method/fixture/threshold change |
| VAL-014 | yes | S11 | S08, S10, S18, S22 | HEAVY_VERIFICATION | S11 | S11 | owner milestone / NOT_IMPLEMENTED | Blocks NUMERICALLY_VERIFIED_GEN1; preserve failure and require BCR for method/fixture/threshold change |
| VAL-015 | no | not required | none | NOT_REQUIRED | none | none | UNASSIGNED_NOT_MANDATORY | No GEN1 execution required; adding it requires normative adjudication |
| VAL-016 | yes | S11 | S08, S09, S18, S22 | HEAVY_VERIFICATION | S11 | S11 | owner milestone / NOT_IMPLEMENTED | Blocks NUMERICALLY_VERIFIED_GEN1; preserve failure and require BCR for method/fixture/threshold change |
| VAL-017 | no | not required | none | NOT_REQUIRED | none | none | UNASSIGNED_NOT_MANDATORY | No GEN1 execution required; adding it requires normative adjudication |
| VAL-018 | yes | S14 | S18, S22 | PR_SCIENTIFIC_AFFECTED | S14 | S14 | owner milestone / NOT_IMPLEMENTED | Blocks NUMERICALLY_VERIFIED_GEN1; preserve failure and require BCR for method/fixture/threshold change |
| VAL-019 | no | not required | none | NOT_REQUIRED | none | none | UNASSIGNED_NOT_MANDATORY | No GEN1 execution required; adding it requires normative adjudication |
| VAL-020 | yes | S11 | S18, S22 | HEAVY_VERIFICATION | S11 | S11 | owner milestone / NOT_IMPLEMENTED | Blocks NUMERICALLY_VERIFIED_GEN1; preserve failure and require BCR for method/fixture/threshold change |
| VAL-021 | yes | S16 | S18, S22 | HEAVY_VERIFICATION | S16 | S16 | owner milestone / NOT_IMPLEMENTED | Blocks NUMERICALLY_VERIFIED_GEN1; preserve failure and require BCR for method/fixture/threshold change |
| VAL-022 | yes | S18 | S22 | EXPERIMENTAL_VALIDATION | S18 | S18 | owner milestone / REQUIRES_EXPERIMENTAL_DATA | Blocks experimental/predictive claim; never reuse calibration data as validation |
| VAL-023 | yes | S13 | S18, S22 | PR_SCIENTIFIC_AFFECTED | S13 | S13 | owner milestone / NOT_IMPLEMENTED | Blocks NUMERICALLY_VERIFIED_GEN1; preserve failure and require BCR for method/fixture/threshold change |
| VAL-024 | yes | S14 | S15, S18, S22 | PR_SCIENTIFIC_AFFECTED | S14 | S14 | owner milestone / NOT_IMPLEMENTED | Blocks NUMERICALLY_VERIFIED_GEN1; preserve failure and require BCR for method/fixture/threshold change |
| VAL-025 | yes | S18 | S22 | EXPERIMENTAL_VALIDATION | S18 | S18 | owner milestone / NOT_IMPLEMENTED | Blocks experimental/predictive claim; never reuse calibration data as validation |
| VAL-026 | yes | S18 | S22 | EXPERIMENTAL_VALIDATION | S18 | S18 | owner milestone / NOT_IMPLEMENTED | Blocks experimental/predictive claim; never reuse calibration data as validation |
| VAL-027 | yes | S06 | S18, S22 | PR_SCIENTIFIC_AFFECTED | S06 | S06 | owner milestone / NOT_IMPLEMENTED | Blocks NUMERICALLY_VERIFIED_GEN1; preserve failure and require BCR for method/fixture/threshold change |
| VAL-028 | yes | S12 | S18, S22 | PR_SCIENTIFIC_AFFECTED | S12 | S12 | owner milestone / NOT_IMPLEMENTED | Blocks NUMERICALLY_VERIFIED_GEN1; preserve failure and require BCR for method/fixture/threshold change |

Canonical machine records: `implementation/validation_registry.json`. No scientific test is run by PR_FAST merely because its directory exists. Later gate adapters are explicit; unavailable adapters fail with GATE_UNAVAILABLE. Expensive gates retain MANDATORY_VERIFICATION_DURING_IMPLEMENTATION status.
