> **Normative — C1.0-R1** · Status: `SCIENTIFIC_IMPLEMENTATION_BASELINE_FROZEN`
> Revision: `NORMATIVE_COMPLETENESS_REVISION`; scientific decisions changed: NO. This restoration does not assert all specification gaps are closed.

# C1.0-R1 consolidation record

Classification: DOCUMENTARY_NORMATIVE_RESTORATION. Revision C1.0-R1. SCIENTIFIC_DECISION_CHANGED = NO. Predecessor commit 0503c869253f9cb4c6d966170d2792418f45e3cb. Predecessor manifest SHA-256 `6e6c67290d6a2f51768a68db99cd87bc65ec008302cb480c2f5f8f21f3a2e55b`.

Only restored selected clauses are normative. Raw evidence files preserve historical versions, including alternatives/pending statements, and have no implementation authority. Research .py files are inspected evidence only, never production dependencies. No new scientific experiment ran.

| H | IDs | Omission | Restoration | Selection source | Equation/value changed | Revalidation impact |
|---|---|---|---|---|---|---|
| H-01 | NUM-003/004/007/008 | Kernel formulas/stencil omitted | NK-001…004 restored; boundary remains missing | AR002, ARKERNEL, C10EIGEN, C03NUM | NO | Existing mandatory production gates remain; no waiver or claimed new execution |
| H-02 | NUM-002/005/006/009 | Stage/event/scale omissions | ST-001…003 restored; full recipe not adjudicated | C03NUM, C03PHY; ARTIME/ARPERIOD explicitly preparatory | NO | Existing mandatory production gates remain; no waiver or claimed new execution |
| H-03 | VAL-001…028 | Sparse/missing fiches | Compatible inputs and VF-022 restored; field-level omissions retained | C03VAL, ARCOUPLED, C02EX, C03GEN | NO | Existing mandatory production gates remain; no waiver or claimed new execution |
| H-04 | PHY-003/009/010 | Zone/tracer/output formulas omitted | PH-001/002 restored | C03PHY SELECTED | NO | Existing mandatory production gates remain; no waiver or claimed new execution |
| H-05 | PHY-005 | Certificate/interpolation/runtime omitted | LC-001…005 restored | C09THEORY/MAP/RUNTIME/DATA SELECTED | NO | Existing mandatory production gates remain; no waiver or claimed new execution |
| H-06 | PHY-007/008 | Correlations/data identity omitted | PH-003/004 restored; exact selected dataset included | C03PHY SELECTED and its named export | NO | Existing mandatory production gates remain; no waiver or claimed new execution |

## Readiness result
H-04/H-05/H-06 CLOSED by selected-source restoration. H-01/H-02/H-03 retain MISSING_PREIMPLEMENTATION_SCIENTIFIC_DECISION; see implementation/readiness_issues.json for exact remaining questions and source alternatives. C1.0-R1 is a documented partial completeness revision, not a claim that missing decisions were made.

## Exact normative byte inventory
The active manifest hashes every new byte, all source evidence, datasets and predecessor bytes. All ten original normative Markdown files changed the revision header; physics, numerics, validation and GEN1 additionally receive explicit annex integration; physics fixes the demonstrably absent metric cross-reference; validation restores the historically mandated VAL-022 row. New normative companions are listed in normative_files. History/C1.0 is byte-exact and non-normative for current implementation. This record and SOURCE_ADJUDICATION_INDEX.json provide H→clause→source tracing.

