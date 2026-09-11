# S06 — numerical-kernel

## Objective
Implement the already selected interior recipe and integrator through explicit replace-free interfaces.

## Identity
ID: `S06`. Status: `NOT_STARTED`. No scientific implementation is authorized by document existence alone.

## Dependencies
- S05 produces `DuctState`: Read conservative mesh/state arrays.
- S03 produces `ThermoModel`: Use consistent thermodynamic derivatives and state recovery.

## Normative IDs
`CAP-003`, `NUM-001`, `NUM-002`, `NUM-003`, `NUM-004`, `NUM-005`, `NUM-006`, `NUM-010`, `VAL-006`, `VAL-007`, `VAL-008`, `VAL-009`, `VAL-010`, `VAL-011`, `VAL-027`, `SV-008`, `SV-009`, `SV-010`, `SV-027`, `MR-008`, `MR-010`

C1 paths: `docs/science/C1.0/GEN1_CONTRACT.md`, `PHYSICS_SPEC.md`, `NUMERICAL_METHOD_SPEC.md`, `VALIDATION_SPEC.md`. IDs above select the relevant clauses.
- `docs/architecture/A1.0/DOMAIN_MODEL.md` — ownership and value-object contracts
- `docs/architecture/A1.0/MODULE_BOUNDARIES.md` — ownership and value-object contracts
- `docs/architecture/A1.0/APPLICATION_AND_API_CONTRACT.md` — public resource and error contracts
- `docs/science/C1.0/NUMERICAL_KERNEL_NORMATIVE_ANNEX.md` — C1.0-R2 normative clause companion
- `docs/science/C1.0/STAGE_EVENT_RESTORATION_ANNEX.md` — C1.0-R2 normative clause companion
- `docs/science/C1.0/VALIDATION_FIXTURE_RESTORATION.md` — C1.0-R2 normative clause companion
- `docs/science/C1.0/BOUNDARY_CONTRACT.md` — C1.0-R2 normative clause companion
- `docs/science/C1.0/TIME_EVENT_PERIODICITY_CONTRACT.md` — C1.0-R2 normative clause companion
- `docs/science/C1.0/EXECUTABLE_VALIDATION_CATALOGUE.md` — C1.0-R2 normative clause companion
- `docs/science/C1.0/REFERENCE_EXECUTION_CONTRACT.md` — C1.0-R2 normative clause companion
- `docs/science/C1.0/BCR-S06-VERIFICATION-CONTRACT.md` — normative clause companion
- `docs/science/C1.0/BCR-S06-MATERIAL-RESOLUTION.md` — normative clause companion
- `docs/science/C1.0/BCR-S06-VERIFICATION-STAGING.md` — normative clause companion

## Required interfaces
### NumericalKernel
- Purpose: Implement the already selected interior recipe and integrator through explicit replace-free interfaces.
- Inputs: DuctState; stage RHS callback; time and dt; boundary flux values; immutable NumericalProfile referencing C1; trial_state_mapper(Z,time) supplied by composition layer for TS-001 (identity when no reaction); callback read-only; MR-008 RegionalDuctState for explicitly represented material input, never fixture identity dispatch
- Outputs/signatures: reconstruct(state) -> FaceStates; interior_flux(faces) -> FaceFluxes; propose_step(state,rhs,time,dt) -> StepAttempt(state or rejection, limiter diagnostics); regional_step -> transactional W/I state plus shared face/source ledgers and stage/guard/remap diagnostics
- Units: seconds; face flux per area before area weighting; extensive ledger integrals after stage quadrature
- Owner: S06
- Mutability: Frozen value objects; caller inputs borrowed read-only; methods return new values. Stateful services own their private state and expose snapshots only.
- Failure semantics: ROE_SECANT_NONHYPERBOLIC, EOS_OUT_OF_DOMAIN, STAGE_INADMISSIBLE, SCIENTIFIC_CHANGE_REQUIRED, UNSUPPORTED_REGIONAL_EVENT, RIEMANN_INADMISSIBLE, GEOMETRY_VOLUME_INVERSION

Common software value rules: `implementation/PUBLIC_INTERFACE_CONTRACT.md`. Internal algorithms remain subordinate to C1; this scope does not supply missing science.

## Required behavior
- Implement NK-001…004 exactly; the joint guard receives the TS-001 physical trial-state mapping from the caller, never assumes an unreacted final combination.
- Do not infer the sensor formula from three constants or copy research code as authority.
- Preserve HLLC Davis, SSPRK2 and conservative final-combination check; expose every limiter activation.
- No global coupled timestep policy here; S16 composes all source bounds.
- Apply R4 SV-008/009/027 and SV-010 as explicitly superseded by R5 MR-010/free; preserve historical R3/R4 failures. Implement MR-008 only within its adjudicated interior applicability and exact S05 file handoff; every changed arithmetic route requires affected verification.
- Regional state uses authoritative W and I12, explicit physical initialization, W-weighted pressure, selected patch/remap and regional Riemann flux. Preserve NASA and inventories; no pressure/energy repair or oracle routing.
- Validate both Euler endpoints and final physical mapped state; compose the same-dt Y0/Y1 volume predictors and preserve rejected diagnostics. Unsupported birth/exit/collision/source-event operations reject transactionally until their explicit consumer contract exists.
- MR-010 STUDY comparisons retain failures; FINAL_PRECISION requires all declared bounds for both epsilon and all101 samples. Coarse convergence and rigid coverage remain mandatory.
- R6 staging: `VAL-008` has `GATE_A` 32/189 (`S06_IMPLEMENTATION_ACCEPTED_FOR_DOWNSTREAM`, `validation/fixtures/VAL-008/gate_a_matrix.json`) and `GATE_B` 189/189 (`NUMERICAL_VERIFICATION_COMPLETE`). Same `input.json`, thresholds, `101` samples, `qualification.json`, `ST003` ledger `1e-10`. `GATE_A` allows `S07→S16` consumption; `GATE_B` is required for `NUMERICALLY_VERIFIED_GEN1`. `GATE_B` reuses `GATE_A` artifacts and runs in parallel via `S18`.

## Allowed paths
- `src/dino2next/numerics/`
- `tests/unit/s06/`
- `tests/contract/s06/`
- `validation/fixtures/VAL-006/`
- `validation/references/VAL-006/`
- `validation/expected/VAL-006/`
- `tests/numerical/VAL-006/`
- `validation/fixtures/VAL-007/`
- `validation/references/VAL-007/`
- `validation/expected/VAL-007/`
- `tests/numerical/VAL-007/`
- `validation/fixtures/VAL-008/`
- `validation/references/VAL-008/`
- `validation/expected/VAL-008/`
- `tests/numerical/VAL-008/`
- `validation/fixtures/VAL-009/`
- `validation/references/VAL-009/`
- `validation/expected/VAL-009/`
- `tests/numerical/VAL-009/`
- `validation/fixtures/VAL-010/`
- `validation/references/VAL-010/`
- `validation/expected/VAL-010/`
- `tests/numerical/VAL-010/`
- `validation/fixtures/VAL-011/`
- `validation/references/VAL-011/`
- `validation/expected/VAL-011/`
- `tests/numerical/VAL-011/`
- `validation/fixtures/VAL-027/`
- `validation/references/VAL-027/`
- `validation/expected/VAL-027/`
- `tests/numerical/VAL-027/`
- `src/dino2next/gasdynamics/__init__.py`
- `src/dino2next/gasdynamics/regional.py`
- `src/dino2next/gasdynamics/README.md`

Paths ending in `/` are exclusive subtrees except for the exact file handoffs enumerated in SCOPE_DEPENDENCY_GRAPH. Other entries are exact files. Fixture/reference/expected paths are owned as one bundle. Rerunning another owner’s fixture grants no write access. Shared tooling handoffs are enumerated in SCOPE_DEPENDENCY_GRAPH.

## Forbidden changes
- Any C1 equation, correlation, method selection, fixture input, threshold, scientific fallback or output definition without approved BCR.
- Any module/fixture owned by another scope except the documented S00 to S19 tooling handoff.
- Clipping, silent normalization/parameter fitting, candidate as oracle, fabricated scientific output.

## Tests
- `tests/unit/s06/test_reconstruction.py`
- `tests/unit/s06/test_flux.py`
- `tests/contract/s06/test_step_transaction.py`
- `tests/numerical/VAL-006/test_acceptance.py`
- `tests/numerical/VAL-007/test_acceptance.py`
- `tests/numerical/VAL-008/test_acceptance.py`
- `tests/numerical/VAL-008/test_gate_a_acceptance.py`
- `tests/numerical/VAL-009/test_acceptance.py`
- `tests/numerical/VAL-010/test_acceptance.py`
- `tests/numerical/VAL-011/test_acceptance.py`
- `tests/numerical/VAL-027/test_acceptance.py`
- `tests/unit/s06/test_regional_state.py`
- `tests/unit/s06/test_regional_kernel.py`
- `tests/contract/s06/test_regional_transaction.py`

These are files to create by scope completion, not tests claimed to exist today. Foundation tests already exist. Scientific fixtures are data, not pytest directories: their owning acceptance test imports them and fails if they or a qualified reference are missing. Frontend unit/E2E commands use Vitest/Playwright produced by S19, never pytest.

Owned numerical/experimental fixtures: VAL-006, VAL-007, VAL-008, VAL-009, VAL-010, VAL-011, VAL-027

## Acceptance
Run from repository root with the activated foundation environment. S00 setup: `python -m venv .venv`, activate it, `python -m pip install -r requirements/foundation.txt`, `python -m pip install --no-build-isolation --no-deps -e .`, `npm --prefix frontend ci`.
```sh
python scripts/run_foundation.py
python -m pytest tests/unit/s06/test_reconstruction.py tests/unit/s06/test_flux.py tests/contract/s06/test_step_transaction.py tests/numerical/VAL-006/test_acceptance.py tests/numerical/VAL-007/test_acceptance.py tests/numerical/VAL-008/test_acceptance.py tests/numerical/VAL-009/test_acceptance.py tests/numerical/VAL-010/test_acceptance.py tests/numerical/VAL-011/test_acceptance.py tests/numerical/VAL-027/test_acceptance.py -q
python -m pytest tests/unit/s06/test_regional_state.py tests/unit/s06/test_regional_kernel.py tests/contract/s06/test_regional_transaction.py tests/unit/s05/test_cell_inventory.py tests/contract/s05/test_geometry_balance.py -q
```

Install scope-specific dependencies with pinned locks during the owning scope; acceptance cannot skip missing tests. Foundation commands execute now. Feature commands must execute at this scope’s completion; zero tests, unavailable adapters and unresolved contract gaps are not PASS.

## Produced artifacts
- `src/dino2next/numerics/`
- `validation/fixtures/VAL-006/`
- `validation/references/VAL-006/`
- `validation/expected/VAL-006/`
- `validation/fixtures/VAL-007/`
- `validation/references/VAL-007/`
- `validation/expected/VAL-007/`
- `validation/fixtures/VAL-008/`
- `validation/references/VAL-008/`
- `validation/expected/VAL-008/`
- `validation/fixtures/VAL-009/`
- `validation/references/VAL-009/`
- `validation/expected/VAL-009/`
- `validation/fixtures/VAL-010/`
- `validation/references/VAL-010/`
- `validation/expected/VAL-010/`
- `validation/fixtures/VAL-011/`
- `validation/references/VAL-011/`
- `validation/expected/VAL-011/`
- `validation/fixtures/VAL-027/`
- `validation/references/VAL-027/`
- `validation/expected/VAL-027/`
- `artifacts/S06/acceptance.json`
- `src/dino2next/gasdynamics/regional.py`

The acceptance artifact records commands, exits, nonzero collected-test counts, C1 hash, commit, environment and any pending heavy gates. It is an output under ignored `artifacts/`, not a fabricated precompleted report.

## Definition of done
- All listed public interfaces, behavior and test files exist; dependency scopes have accepted artifacts.
- Every acceptance command succeeds with nonempty test collection; no skipped required fixture accepted as PASS.
- Owner fixture numerical execution follows its gate class; deferred HEAVY_VERIFICATION remains explicitly unverified.
- Independent reviewer checks contract IDs, signatures, units, failure cases, path ownership and raw artifact hashes.
- The regional extension and all affected original S06 gates are complete at the accepted tree; small prototype controls and N1600 confirmations alone are insufficient. Unsupported consumer events remain explicitly tracked, not silently accepted.

## Reviewer checklist
- Read the normative IDs before reviewing the builder explanation.
- Check every public signature, unit, mutation boundary and error case against Required interfaces.
- Verify each dependency supplies the consumed object; no duplicate fixture owner or unauthorized file.
- Confirm actual test collection, reference independence and pending-heavy status; no hidden relaxation.
- For UI, verify schema pointer → domain → application → solver input → provenance from the field binding table.

## Failure semantics
- `IMPLEMENTATION_DEFECT`: Code violates a specified interface/behavior; repair within owner scope, preserve failing test.
- `VERIFICATION_FAILURE`: Candidate/reference/gate disagrees with frozen acceptance; retain evidence and block the corresponding claim, never tune acceptance.
- `SCIENTIFIC_CHANGE_REQUIRED`: Missing or contradictory normative formula/fixture; file a BCR with affected IDs and stop affected implementation before choosing science.
- `OUT_OF_SCOPE`: Required change lies outside allowed ownership; return to owner or amend software-only scope with review; do not edit silently.

## Specification preconditions
No direct specification gap recorded for this scope. Dependency acceptance is still required.

Rollback: keep failure artifacts, revert only this scope’s unaccepted changes or abandon its unmerged branch. Never reset unrelated work or rewrite a shared fixture.
