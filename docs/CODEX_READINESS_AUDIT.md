# Operational readiness audit

Status: DINO2NEXT_FOUNDATION_HARDENING_REQUIRED.

The foundation audit covers C1, A1, UX1, all S00–S22, dependency/validation ownership, manifest, scripts, Python/frontend scaffolds and CI. C1 bytes and its SCIENTIFIC_IMPLEMENTATION_BASELINE_FROZEN declaration are preserved. A frozen label cannot supply omitted clauses.

## Repaired foundation defects

- Manifest checker recalculates SHA-256 of all ten mandatory normative files, validates version/status, rejects missing/unlisted files, malformed paths/hashes and duplicate entries. Negative tests alter bytes, remove files and corrupt hashes.
- PR_FAST compiles Python, checks integrity and scope consistency, runs actual pytest tests and TypeScript/Node scaffold tests. Locked frontend installation replaces the previous echo check.
- S00 has actual setup and acceptance commands. S01–S22 enumerate public boundaries, exact tests, artifacts and consumed dependencies. Future tests are not represented as already implemented.
- Validation matrix covers VAL-001…028. Twenty-four are referenced as mandatory by the current C1 corpus; all have a single owner. VAL-012/015/017/019 are not specified as mandatory there and are explicitly unassigned, rather than invented.
- S11 owns the coupled fixtures after port characterization and volumes exist. S18 aggregates them read-only. Frontend shell/tooling handoffs are explicit.

## Remaining defects preventing global readiness

| ID | Contract | Concrete defect |
|---|---|---|
| H-01 | NUM-003/004/007/008 | AR-002 flux/reconstruction and boundary equations referenced without complete normative recipes |
| H-02 | NUM-002/005/006/009 | Source/stage combination, timestep rays and periodic scale/event definitions incomplete |
| H-03 | VAL contracts | VAL-022 required by CAP-007 but missing its fiche; other fixtures lack complete SI inputs/reference/normalization |
| H-04 | PHY-003/009/010 | Two-zone evolution and metric denominator/failure definitions absent from their claimed normative destination |
| H-05 | PHY-005 | Exact certified loss-map interpolation/conditioning/runtime coordinate policy missing |
| H-06 | PHY-007/008 | Exact selected thermal/transport/friction realization not fully specified |

Evidence and corrective action are in implementation/readiness_issues.json. Restore already adjudicated material through a reviewed normative consolidation and corresponding manifest update. This audit neither chooses new science nor reopens research. Missing real engine data and pending heavy execution are distinct from these missing specification clauses.

## Gate interpretation

S00 = COMPLETE_FOUNDATION when PR_FAST is green. NEXT_CODEX_SCOPE = S01; not started here. Structural checks pass with explicit open issues; the separate `check_scopes.py --readiness` must fail. No DINO2NEXT_CODEX_READY claim is made. Full readiness requires closing H-01…H-06 and demonstrating all scopes can execute without choosing science.

Local/remote command evidence is reported at the final PR HEAD. CI green certifies foundation checks only. Numerical verification, scientific validation and predictive validation remain pending separately; no heavy reference was executed by this audit.
