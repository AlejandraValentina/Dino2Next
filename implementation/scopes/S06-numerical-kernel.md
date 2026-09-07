# S06 — numerical-kernel

## Objective
Implement the already selected interior recipe and integrator through explicit replace-free interfaces.

## Identity
ID: `S06`. Status: `NOT_STARTED`. No scientific implementation is authorized by document existence alone.

## Dependencies
- S05 produces `DuctState`: Read conservative mesh/state arrays.
- S03 produces `ThermoModel`: Use consistent thermodynamic derivatives and state recovery.

## Normative IDs
`CAP-003`, `NUM-001`, `NUM-002`, `NUM-003`, `NUM-004`, `NUM-005`, `NUM-006`, `NUM-010`, `VAL-006`, `VAL-007`, `VAL-008`, `VAL-009`, `VAL-010`, `VAL-011`, `VAL-027`

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

## Required interfaces
### NumericalKernel
- Purpose: Implement the already selected interior recipe and integrator through explicit replace-free interfaces.
- Inputs: DuctState; stage RHS callback; time and dt; boundary flux values; immutable NumericalProfile referencing C1; trial_state_mapper(Z,time) supplied by composition layer for TS-001 (identity when no reaction); callback read-only
- Outputs/signatures: reconstruct(state) -> FaceStates; interior_flux(faces) -> FaceFluxes; propose_step(state,rhs,time,dt) -> StepAttempt(state or rejection, limiter diagnostics)
- Units: seconds; face flux per area before area weighting; extensive ledger integrals after stage quadrature
- Owner: S06
- Mutability: Frozen value objects; caller inputs borrowed read-only; methods return new values. Stateful services own their private state and expose snapshots only.
- Failure semantics: ROE_SECANT_NONHYPERBOLIC, EOS_OUT_OF_DOMAIN, STAGE_INADMISSIBLE, SCIENTIFIC_CHANGE_REQUIRED

Common software value rules: `implementation/PUBLIC_INTERFACE_CONTRACT.md`. Internal algorithms remain subordinate to C1; this scope does not supply missing science.

## Required behavior
- Implement NK-001…004 exactly; the joint guard receives the TS-001 physical trial-state mapping from the caller, never assumes an unreacted final combination.
- Do not infer the sensor formula from three constants or copy research code as authority.
- Preserve HLLC Davis, SSPRK2 and conservative final-combination check; expose every limiter activation.
- No global coupled timestep policy here; S16 composes all source bounds.

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

Paths ending in `/` are exclusive subtrees. Other entries are exact files. Fixture/reference/expected paths are owned as one bundle. Rerunning another owner’s fixture grants no write access. Shared tooling handoffs are enumerated in SCOPE_DEPENDENCY_GRAPH.

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
- `tests/numerical/VAL-009/test_acceptance.py`
- `tests/numerical/VAL-010/test_acceptance.py`
- `tests/numerical/VAL-011/test_acceptance.py`
- `tests/numerical/VAL-027/test_acceptance.py`

These are files to create by scope completion, not tests claimed to exist today. Foundation tests already exist. Scientific fixtures are data, not pytest directories: their owning acceptance test imports them and fails if they or a qualified reference are missing. Frontend unit/E2E commands use Vitest/Playwright produced by S19, never pytest.

Owned numerical/experimental fixtures: VAL-006, VAL-007, VAL-008, VAL-009, VAL-010, VAL-011, VAL-027

## Acceptance
Run from repository root with the activated foundation environment. S00 setup: `python -m venv .venv`, activate it, `python -m pip install -r requirements/foundation.txt`, `python -m pip install --no-build-isolation --no-deps -e .`, `npm --prefix frontend ci`.
```sh
python scripts/run_foundation.py
python -m pytest tests/unit/s06/test_reconstruction.py tests/unit/s06/test_flux.py tests/contract/s06/test_step_transaction.py tests/numerical/VAL-006/test_acceptance.py tests/numerical/VAL-007/test_acceptance.py tests/numerical/VAL-008/test_acceptance.py tests/numerical/VAL-009/test_acceptance.py tests/numerical/VAL-010/test_acceptance.py tests/numerical/VAL-011/test_acceptance.py tests/numerical/VAL-027/test_acceptance.py -q
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

The acceptance artifact records commands, exits, nonzero collected-test counts, C1 hash, commit, environment and any pending heavy gates. It is an output under ignored `artifacts/`, not a fabricated precompleted report.

## Definition of done
- All listed public interfaces, behavior and test files exist; dependency scopes have accepted artifacts.
- Every acceptance command succeeds with nonempty test collection; no skipped required fixture accepted as PASS.
- Owner fixture numerical execution follows its gate class; deferred HEAVY_VERIFICATION remains explicitly unverified.
- Independent reviewer checks contract IDs, signatures, units, failure cases, path ownership and raw artifact hashes.

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
