# S03 — thermochemistry

## Objective
Implement immutable NASA/EOS dataset evaluation and inversion with explicit domain errors.

## Identity
ID: `S03`. Status: `NOT_STARTED`. No scientific implementation is authorized by document existence alone.

## Dependencies
- S01 produces `ConfigSnapshot`: Bind SI inputs and immutable dataset hash.

## Normative IDs
`CAP-002`, `CAP-006`, `PHY-002`, `NUM-001`, `VAL-001`

C1 paths: `docs/science/C1.0/GEN1_CONTRACT.md`, `PHYSICS_SPEC.md`, `NUMERICAL_METHOD_SPEC.md`, `VALIDATION_SPEC.md`. IDs above select the relevant clauses.
- `docs/architecture/A1.0/DOMAIN_MODEL.md` — ownership and value-object contracts
- `docs/architecture/A1.0/MODULE_BOUNDARIES.md` — ownership and value-object contracts
- `docs/architecture/A1.0/APPLICATION_AND_API_CONTRACT.md` — public resource and error contracts

## Required interfaces
### ThermoModel
- Purpose: Implement immutable NASA/EOS dataset evaluation and inversion with explicit domain errors.
- Inputs: ThermoDataset(species names/order, molar masses, NASA7 ranges/coefficients, reference metadata, sha256); T,p,Y or rho,e,Y
- Outputs/signatures: evaluate(T,p,Y) -> ThermoState(rho,R,cp,cv,h,e,gamma,a); invert_energy(rho,e,Y) -> ThermoState; species_properties(T) -> read-only arrays
- Units: K, Pa, kg/m3, kg/kmol, J/kg, J/(kg K), m/s; Y dimensionless
- Owner: S03
- Mutability: Frozen value objects; caller inputs borrowed read-only; methods return new values. Stateful services own their private state and expose snapshots only.
- Failure semantics: EOS_OUT_OF_DOMAIN, COMPOSITION_INVALID, DATASET_HASH_MISMATCH, EOS_INVERSION_FAILED

Common software value rules: `implementation/PUBLIC_INTERFACE_CONTRACT.md`. Internal algorithms remain subordinate to C1; this scope does not supply missing science.

## Required behavior
- Use five chemical species in normative order, distinct from provenance tags.
- Low/high NASA branch at 1000 K follows C1 exactly; no extrapolation or hidden formation-energy offset.
- Check simplex and supplied dataset identity; no undocumented built-in fuel dataset.
- Return diagnostic inversion residual and preserve input; use fixture oracle independent of candidate evaluator.

## Allowed paths
- `src/dino2next/thermo/`
- `schemas/thermo/`
- `tests/unit/s03/`
- `tests/contract/s03/`
- `validation/fixtures/VAL-001/`
- `validation/references/VAL-001/`
- `validation/expected/VAL-001/`
- `tests/numerical/VAL-001/`

Paths ending in `/` are exclusive subtrees. Other entries are exact files. Fixture/reference/expected paths are owned as one bundle. Rerunning another owner’s fixture grants no write access. Shared tooling handoffs are enumerated in SCOPE_DEPENDENCY_GRAPH.

## Forbidden changes
- Any C1 equation, correlation, method selection, fixture input, threshold, scientific fallback or output definition without approved BCR.
- Any module/fixture owned by another scope except the documented S00 to S19 tooling handoff.
- Clipping, silent normalization/parameter fitting, candidate as oracle, fabricated scientific output.

## Tests
- `tests/unit/s03/test_nasa_branches.py`
- `tests/unit/s03/test_eos_inversion.py`
- `tests/contract/s03/test_dataset_identity.py`
- `tests/numerical/VAL-001/test_acceptance.py`

These are files to create by scope completion, not tests claimed to exist today. Foundation tests already exist. Scientific fixtures are data, not pytest directories: their owning acceptance test imports them and fails if they or a qualified reference are missing. Frontend unit/E2E commands use Vitest/Playwright produced by S19, never pytest.

Owned numerical/experimental fixtures: VAL-001

## Acceptance
Run from repository root with the activated foundation environment. S00 setup: `python -m venv .venv`, activate it, `python -m pip install -r requirements/foundation.txt`, `python -m pip install --no-build-isolation --no-deps -e .`, `npm --prefix frontend ci`.
```sh
python scripts/run_foundation.py
python -m pytest tests/unit/s03/test_nasa_branches.py tests/unit/s03/test_eos_inversion.py tests/contract/s03/test_dataset_identity.py tests/numerical/VAL-001/test_acceptance.py -q
```

Install scope-specific dependencies with pinned locks during the owning scope; acceptance cannot skip missing tests. Foundation commands execute now. Feature commands must execute at this scope’s completion; zero tests, unavailable adapters and unresolved contract gaps are not PASS.

## Produced artifacts
- `src/dino2next/thermo/`
- `schemas/thermo/`
- `validation/fixtures/VAL-001/`
- `validation/references/VAL-001/`
- `validation/expected/VAL-001/`
- `artifacts/S03/acceptance.json`

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
Open audit findings: `H-03`. Stop the affected scientific path until reviewed normative consolidation resolves these. See `implementation/readiness_issues.json` and `docs/CODEX_READINESS_AUDIT.md`. This is not an invitation for Codex to choose a formula.

Rollback: keep failure artifacts, revert only this scope’s unaccepted changes or abandon its unmerged branch. Never reset unrelated work or rewrite a shared fixture.
