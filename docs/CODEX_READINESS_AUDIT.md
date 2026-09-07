# Operational readiness — C1.0-R2

Target terminal status: DINO2NEXT_CODEX_READY_FINAL, conditional on strict foundation and standalone readiness PASS on this PR HEAD. No expected-failure readiness job remains.

| Issue | Status | Executable closure |
|---|---|---|
| H-01 | CLOSED | BC-001…008: reservoir wave compatibility, roots/domain, donor, wall/open area, failure codes |
| H-02 | CLOSED | TS-001…007: prescribed-source SSPRK2, combined RHS/bounds, events, complete scales and detector |
| H-03 | CLOSED | 24 actual 19-field current VAL fiches, REF-001, unchanged thresholds and experimental contracts |
| H-04 | CLOSED | PH-001/002; unchanged R1 physical restoration |
| H-05 | CLOSED | LC-001…005; unchanged loss characterization |
| H-06 | CLOSED | PH-003/004; unchanged thermal/loss realization |

S00 = COMPLETE_FOUNDATION; NEXT_CODEX_SCOPE = S01, NOT_STARTED. 23 scopes audited; 24 mandatory VAL have one owner each. VAL-012/015/017/019 remain explicitly nonmandatory; VAL-022 remains S18's motored experiment. Scope DAG edges retain consumed-interface explanations. Frontend S19–21 consumes S17 descriptors/API and UX1.0, never physics or invented results.

Required checks: `python scripts/run_foundation.py`; `python scripts/check_scopes.py --readiness`. Manifest checks every declared byte plus mandatory roster, version/status, data tables and archived R1 bytes. Scope checks verify concrete fiche values, placeholders and catalogue drift in addition to fields, IDs, ownership, DAG and generated documents. Negative tests mutate bytes, remove files/fields, alter hashes, reopen issues and erase thresholds.

C1 original and R1 are preserved with manifests. R2 changes only the three approved BCRs and operational checking. Lightweight research checks are recorded under research/preimplementation_r2; no coupled reference, high-resolution run, engine campaign or production solver was run/created. Heavy gates remain MANDATORY_VERIFICATION_DURING_IMPLEMENTATION. The known unresolved coupled reference error allocation still forbids NUMERICALLY_VERIFIED_GEN1. Readiness does not grant that claim, scientific validity or predictive validation.

PR #1 stays open on work/foundation-c1-a1-ux1. No merge and no S01 execution. Final reported HEAD and GitHub Actions run are the evidence of remote CI status; this document never predicts that status from local tests alone.
