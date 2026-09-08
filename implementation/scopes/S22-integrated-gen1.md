# S22 — integrated-gen1

## Objective
Assemble the executable product and enforce milestone claims without altering module science.

## Identity
ID: `S22`. Status: `NOT_STARTED`. No scientific implementation is authorized by document existence alone.

## Dependencies
- S18 produces `ValidationRunner`: Consume gate results.
- S20 produces `RunWorkspace`: Drive run workflow.
- S21 produces `ResultsWorkspace`: Render accepted results.
- S17 produces `ApplicationAPI`: Wire local application service.
- S00 produces `FoundationChecks`: Explicit final packaging metadata handoff; no scientific dependency selection.

## Normative IDs
`CAP-001`, `CAP-002`, `CAP-003`, `CAP-004`, `CAP-005`, `CAP-006`, `CAP-007`, `CAP-008`, `CAP-009`, `CAP-010`, `NUM-010`, `MR-008`, `MR-010`

C1 paths: `docs/science/C1.0/GEN1_CONTRACT.md`, `PHYSICS_SPEC.md`, `NUMERICAL_METHOD_SPEC.md`, `VALIDATION_SPEC.md`. IDs above select the relevant clauses.
- `docs/architecture/A1.0/DOMAIN_MODEL.md` — ownership and value-object contracts
- `docs/architecture/A1.0/MODULE_BOUNDARIES.md` — ownership and value-object contracts
- `docs/architecture/A1.0/APPLICATION_AND_API_CONTRACT.md` — public resource and error contracts
- `docs/science/C1.0/NUMERICAL_KERNEL_NORMATIVE_ANNEX.md` — C1.0-R2 normative clause companion
- `docs/science/C1.0/STAGE_EVENT_RESTORATION_ANNEX.md` — C1.0-R2 normative clause companion
- `docs/science/C1.0/EXPERIMENTAL_DATA_CONTRACT.md` — C1.0-R2 normative clause companion
- `docs/science/C1.0/BOUNDARY_CONTRACT.md` — C1.0-R2 normative clause companion
- `docs/science/C1.0/TIME_EVENT_PERIODICITY_CONTRACT.md` — C1.0-R2 normative clause companion
- `docs/science/C1.0/EXECUTABLE_VALIDATION_CATALOGUE.md` — C1.0-R2 normative clause companion
- `docs/science/C1.0/REFERENCE_EXECUTION_CONTRACT.md` — C1.0-R2 normative clause companion
- `docs/science/C1.0/BCR-S06-MATERIAL-RESOLUTION.md` — normative clause companion

## Required interfaces
### IntegratedProduct
- Purpose: Assemble the executable product and enforce milestone claims without altering module science.
- Inputs: selected implementations and their resource certificates; ApplicationAPI; UI entry points; ValidationRunner reports
- Outputs/signatures: local start command; release readiness manifest; end-to-end project/run/results workflow
- Units: no new scientific units or meanings; all values preserve producer metadata
- Owner: S22
- Mutability: Frozen value objects; caller inputs borrowed read-only; methods return new values. Stateful services own their private state and expose snapshots only.
- Failure semantics: READINESS_GATE_FAILED, REQUIRED_ENGINE_DATA_NOT_YET_ACQUIRED, SCIENTIFIC_CHANGE_REQUIRED

Common software value rules: `implementation/PUBLIC_INTERFACE_CONTRACT.md`. Internal algorithms remain subordinate to C1; this scope does not supply missing science.

## Required behavior
- Wire existing modules only; defects in other modules return to their owner scope.
- Require passed milestone and heavy gates before numerical-verification claim; leave experimental claims pending if data absent.
- System journey uses a clearly labelled synthetic verification fixture or supplied characterized engine; never fake a real-engine result.
- Report unmet gate IDs and artifact links rather than readiness partial-success.
- Consume MR-008 represented regional state and physical observables without homogeneous projection as a substitute. Implement affected birth/exit/donor/source-event routes only after their explicit contract and verification; retain required W/I/geometry/recovery identities and actual ledger transactions.
- Retain MR-010 resolution-specific coverage and historical failures; do not aggregate four fine confirmations into whole-battery or whole-engine acceptance.

## Allowed paths
- `src/dino2next/composition/`
- `tests/system/s22/`
- `frontend/tests/s22/`
- `release/`
- `pyproject.toml`

Paths ending in `/` are exclusive subtrees except for the exact file handoffs enumerated in SCOPE_DEPENDENCY_GRAPH. Other entries are exact files. Fixture/reference/expected paths are owned as one bundle. Rerunning another owner’s fixture grants no write access. Shared tooling handoffs are enumerated in SCOPE_DEPENDENCY_GRAPH.

## Forbidden changes
- Any C1 equation, correlation, method selection, fixture input, threshold, scientific fallback or output definition without approved BCR.
- Any module/fixture owned by another scope except the documented S00 to S19 tooling handoff.
- Clipping, silent normalization/parameter fitting, candidate as oracle, fabricated scientific output.

## Tests
- `tests/system/s22/test_product_replay.py`
- `frontend/tests/s22/product.spec.ts`

These are files to create by scope completion, not tests claimed to exist today. Foundation tests already exist. Scientific fixtures are data, not pytest directories: their owning acceptance test imports them and fails if they or a qualified reference are missing. Frontend unit/E2E commands use Vitest/Playwright produced by S19, never pytest.

Owned numerical/experimental fixtures: none; consume/rerun only as listed in SCOPE_VALIDATION_MATRIX.

## Acceptance
Run from repository root with the activated foundation environment. S00 setup: `python -m venv .venv`, activate it, `python -m pip install -r requirements/foundation.txt`, `python -m pip install --no-build-isolation --no-deps -e .`, `npm --prefix frontend ci`.
```sh
python scripts/run_foundation.py
python -m pytest tests/system/s22/test_product_replay.py -q
npm --prefix frontend run test:e2e -- tests/s22/product.spec.ts
```

Install scope-specific dependencies with pinned locks during the owning scope; acceptance cannot skip missing tests. Foundation commands execute now. Feature commands must execute at this scope’s completion; zero tests, unavailable adapters and unresolved contract gaps are not PASS.

## Produced artifacts
- `src/dino2next/composition/`
- `release/`
- `pyproject.toml`
- `artifacts/S22/acceptance.json`

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
