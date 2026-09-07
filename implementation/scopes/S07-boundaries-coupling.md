# S07 — boundaries-coupling

## Objective
Produce oriented half-Riemann boundary traces and a shared interface ledger.

## Identity
ID: `S07`. Status: `NOT_STARTED`. No scientific implementation is authorized by document existence alone.

## Dependencies
- S03 produces `ThermoModel`: Evaluate donor thermodynamics.
- S04 produces `VolumeInventory`: Return paired increments to the volume.
- S06 produces `NumericalKernel`: Consume reconstructed traces.

## Normative IDs
`CAP-002`, `CAP-004`, `PHY-004`, `PHY-005`, `NUM-007`, `NUM-008`, `VAL-004`

C1 paths: `docs/science/C1.0/GEN1_CONTRACT.md`, `PHYSICS_SPEC.md`, `NUMERICAL_METHOD_SPEC.md`, `VALIDATION_SPEC.md`. IDs above select the relevant clauses.
- `docs/architecture/A1.0/DOMAIN_MODEL.md` — ownership and value-object contracts
- `docs/architecture/A1.0/MODULE_BOUNDARIES.md` — ownership and value-object contracts
- `docs/architecture/A1.0/APPLICATION_AND_API_CONTRACT.md` — public resource and error contracts

## Required interfaces
### BoundaryCoupler
- Purpose: Produce oriented half-Riemann boundary traces and a shared interface ledger.
- Inputs: reservoir state, duct face state, outward normal, physical face area, opening fraction, time; ThermoModel
- Outputs/signatures: solve(...) -> BoundaryTrace(donor, p,T,u,M, flux, diagnostics); pair_flux(trace,left_id,right_id) -> TransferLedger pair
- Units: SI; outward normal +/-1; kg/s, N, W and species/tracer kg/s
- Owner: S07
- Mutability: Frozen value objects; caller inputs borrowed read-only; methods return new values. Stateful services own their private state and expose snapshots only.
- Failure semantics: BOUNDARY_NO_PHYSICAL_ROOT, EOS_OUT_OF_DOMAIN, CHARACTERISTIC_DOMAIN_ERROR

Common software value rules: `implementation/PUBLIC_INTERFACE_CONTRACT.md`. Internal algorithms remain subordinate to C1; this scope does not supply missing science.

## Required behavior
- Use the approved full boundary equations after H-01 supplies the missing half-Riemann recipe.
- Use actual donor composition and enthalpy on reversal; no mixture averaging to suppress a contact.
- Closed face has zero mass/energy/species exchange and physical pressure force.
- One flux record is shared by both endpoints; never evaluate different times for each end.

## Allowed paths
- `src/dino2next/boundaries/`
- `src/dino2next/coupling/`
- `tests/unit/s07/`
- `tests/contract/s07/`
- `validation/fixtures/VAL-004/`
- `validation/references/VAL-004/`
- `validation/expected/VAL-004/`
- `tests/numerical/VAL-004/`

Paths ending in `/` are exclusive subtrees. Other entries are exact files. Fixture/reference/expected paths are owned as one bundle. Rerunning another owner’s fixture grants no write access. Shared tooling handoffs are enumerated in SCOPE_DEPENDENCY_GRAPH.

## Forbidden changes
- Any C1 equation, correlation, method selection, fixture input, threshold, scientific fallback or output definition without approved BCR.
- Any module/fixture owned by another scope except the documented S00 to S19 tooling handoff.
- Clipping, silent normalization/parameter fitting, candidate as oracle, fabricated scientific output.

## Tests
- `tests/unit/s07/test_boundary_donor.py`
- `tests/contract/s07/test_oriented_flux.py`
- `tests/numerical/VAL-004/test_acceptance.py`

These are files to create by scope completion, not tests claimed to exist today. Foundation tests already exist. Scientific fixtures are data, not pytest directories: their owning acceptance test imports them and fails if they or a qualified reference are missing. Frontend unit/E2E commands use Vitest/Playwright produced by S19, never pytest.

Owned numerical/experimental fixtures: VAL-004

## Acceptance
Run from repository root with the activated foundation environment. S00 setup: `python -m venv .venv`, activate it, `python -m pip install -r requirements/foundation.txt`, `python -m pip install --no-build-isolation --no-deps -e .`, `npm --prefix frontend ci`.
```sh
python scripts/run_foundation.py
python -m pytest tests/unit/s07/test_boundary_donor.py tests/contract/s07/test_oriented_flux.py tests/numerical/VAL-004/test_acceptance.py -q
```

Install scope-specific dependencies with pinned locks during the owning scope; acceptance cannot skip missing tests. Foundation commands execute now. Feature commands must execute at this scope’s completion; zero tests, unavailable adapters and unresolved contract gaps are not PASS.

## Produced artifacts
- `src/dino2next/boundaries/`
- `src/dino2next/coupling/`
- `validation/fixtures/VAL-004/`
- `validation/references/VAL-004/`
- `validation/expected/VAL-004/`
- `artifacts/S07/acceptance.json`

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
Open audit findings: `H-01`, `H-03`. Stop the affected scientific path until reviewed normative consolidation resolves these. See `implementation/readiness_issues.json` and `docs/CODEX_READINESS_AUDIT.md`. This is not an invitation for Codex to choose a formula.

Rollback: keep failure artifacts, revert only this scope’s unaccepted changes or abandon its unmerged branch. Never reset unrelated work or rewrite a shared fixture.
