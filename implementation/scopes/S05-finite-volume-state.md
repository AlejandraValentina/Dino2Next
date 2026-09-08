# S05 — finite-volume-state

## Objective
Implement area-weighted cell storage, geometry integration and conservative inventory reporting.

## Identity
ID: `S05`. Status: `NOT_STARTED`. No scientific implementation is authorized by document existence alone.

## Dependencies
- S02 produces `GeometryModel`: Consume physical face/average geometry.
- S03 produces `ThermoModel`: Recover NASA states.

## Normative IDs
`CAP-003`, `PHY-004`, `NUM-001`, `NUM-004`, `VAL-011`, `MR-008`

C1 paths: `docs/science/C1.0/GEN1_CONTRACT.md`, `PHYSICS_SPEC.md`, `NUMERICAL_METHOD_SPEC.md`, `VALIDATION_SPEC.md`. IDs above select the relevant clauses.
- `docs/architecture/A1.0/DOMAIN_MODEL.md` — ownership and value-object contracts
- `docs/architecture/A1.0/MODULE_BOUNDARIES.md` — ownership and value-object contracts
- `docs/architecture/A1.0/APPLICATION_AND_API_CONTRACT.md` — public resource and error contracts
- `docs/science/C1.0/NUMERICAL_KERNEL_NORMATIVE_ANNEX.md` — C1.0-R2 normative clause companion
- `docs/science/C1.0/STAGE_EVENT_RESTORATION_ANNEX.md` — C1.0-R2 normative clause companion
- `docs/science/C1.0/PHYSICS_RESTORATION_ANNEX.md` — C1.0-R2 normative clause companion
- `docs/science/C1.0/VALIDATION_FIXTURE_RESTORATION.md` — C1.0-R2 normative clause companion
- `docs/science/C1.0/BOUNDARY_CONTRACT.md` — C1.0-R2 normative clause companion
- `docs/science/C1.0/TIME_EVENT_PERIODICITY_CONTRACT.md` — C1.0-R2 normative clause companion
- `docs/science/C1.0/EXECUTABLE_VALIDATION_CATALOGUE.md` — C1.0-R2 normative clause companion
- `docs/science/C1.0/REFERENCE_EXECUTION_CONTRACT.md` — C1.0-R2 normative clause companion
- `docs/science/C1.0/BCR-S06-MATERIAL-RESOLUTION.md` — normative clause companion

## Required interfaces
### DuctState
- Purpose: Implement area-weighted cell storage, geometry integration and conservative inventory reporting.
- Inputs: Mesh1D(cell bounds, area averages, face areas, perimeter); Q[cell, component] with chemical/tracer ordering; ThermoModel
- Outputs/signatures: primitive(duct) -> read-only state arrays; integrated_inventory(duct) -> extensive totals; geometry_source(duct) -> momentum rate array
- Units: Q=A*U averages; kg/m, kg/s, J/m for respective components; SI mesh
- Owner: S05
- Mutability: Frozen value objects; caller inputs borrowed read-only; methods return new values. Stateful services own their private state and expose snapshots only.
- Failure semantics: MESH_NONCONFORMING, GEOMETRY_INVALID, EOS_OUT_OF_DOMAIN
### RegionalDuctState
- Purpose: Additive MR-008 state extension delivered and accepted with S06 under its exact S05 handoff; historical homogeneous S05 acceptance is unchanged.
- Inputs: Geometry/base mesh identity; authoritative cumulative-volume faces W; extensive inventory I12 per interval; physical material identities; ThermoModel/recovery identity.
- Outputs/signatures: regional_states; conservative_projection; pressure_volume_average; integrated_inventory; immutable regional restart with inverse certificates.
- Units: W in m3; I12 in kg, kg m/s, J and constituent kg; derived x in m; pressure in Pa.
- Owner: S05
- Mutability: One authoritative immutable W/I representation; read-only derived coordinates, observables and snapshots; no homogeneous EOS cache of a mixed projection.
- Failure semantics: GEOMETRY_INVALID, NONPOSITIVE_VOLUME, EOS_OUT_OF_DOMAIN, EOS_INVERSION_FAILED, UNSUPPORTED_REGIONAL_EVENT

Common software value rules: `implementation/PUBLIC_INTERFACE_CONTRACT.md`. Internal algorithms remain subordinate to C1; this scope does not supply missing science.

## Required behavior
- Distinguish cell average from integrated inventory using dx.
- Use exact piecewise geometry integration and AF+pΔA semantics.
- Do not compute numerical face fluxes in this scope.
- Keep closed-port storage persistent; do not derive storage from Cd or opening.
- MR-008 additive regional extension is produced by S06 under exact file handoff; preserve accepted homogeneous behavior and existing S05 regression tests. No numerical flux implementation belongs in S05.

## Allowed paths
- `src/dino2next/gasdynamics/`
- `tests/unit/s05/`
- `tests/contract/s05/`

Paths ending in `/` are exclusive subtrees except for the exact file handoffs enumerated in SCOPE_DEPENDENCY_GRAPH. Other entries are exact files. Fixture/reference/expected paths are owned as one bundle. Rerunning another owner’s fixture grants no write access. Shared tooling handoffs are enumerated in SCOPE_DEPENDENCY_GRAPH.

## Forbidden changes
- Any C1 equation, correlation, method selection, fixture input, threshold, scientific fallback or output definition without approved BCR.
- Any module/fixture owned by another scope except the documented S00 to S19 tooling handoff.
- Clipping, silent normalization/parameter fitting, candidate as oracle, fabricated scientific output.

## Tests
- `tests/unit/s05/test_cell_inventory.py`
- `tests/contract/s05/test_geometry_balance.py`

These are files to create by scope completion, not tests claimed to exist today. Foundation tests already exist. Scientific fixtures are data, not pytest directories: their owning acceptance test imports them and fails if they or a qualified reference are missing. Frontend unit/E2E commands use Vitest/Playwright produced by S19, never pytest.

Owned numerical/experimental fixtures: none; consume/rerun only as listed in SCOPE_VALIDATION_MATRIX.

## Acceptance
Run from repository root with the activated foundation environment. S00 setup: `python -m venv .venv`, activate it, `python -m pip install -r requirements/foundation.txt`, `python -m pip install --no-build-isolation --no-deps -e .`, `npm --prefix frontend ci`.
```sh
python scripts/run_foundation.py
python -m pytest tests/unit/s05/test_cell_inventory.py tests/contract/s05/test_geometry_balance.py -q
```

Install scope-specific dependencies with pinned locks during the owning scope; acceptance cannot skip missing tests. Foundation commands execute now. Feature commands must execute at this scope’s completion; zero tests, unavailable adapters and unresolved contract gaps are not PASS.

## Produced artifacts
- `src/dino2next/gasdynamics/`
- `artifacts/S05/acceptance.json`

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
