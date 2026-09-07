# S00 — bootstrap-tooling

## Objective
Install and verify the documentation/toolchain foundation without a solver.

## Identity
ID: `S00`. Status: `COMPLETE_FOUNDATION`. No scientific implementation is authorized by document existence alone.

## Dependencies
None; foundation root.

## Normative IDs
`CAP-010`, `NUM-010`

C1 paths: `docs/science/C1.0/GEN1_CONTRACT.md`, `PHYSICS_SPEC.md`, `NUMERICAL_METHOD_SPEC.md`, `VALIDATION_SPEC.md`. IDs above select the relevant clauses.
- `docs/architecture/A1.0/DOMAIN_MODEL.md` — ownership and value-object contracts
- `docs/architecture/A1.0/MODULE_BOUNDARIES.md` — ownership and value-object contracts
- `docs/architecture/A1.0/APPLICATION_AND_API_CONTRACT.md` — public resource and error contracts

## Required interfaces
### FoundationChecks
- Purpose: Install and verify the documentation/toolchain foundation without a solver.
- Inputs: repository root; optional scope ID and gate class
- Outputs/signatures: JSON PASS/FAIL report and process exit status
- Units: no physical values
- Owner: S00
- Mutability: Frozen value objects; caller inputs borrowed read-only; methods return new values. Stateful services own their private state and expose snapshots only.
- Failure semantics: INTEGRITY_ERROR, SCOPE_CONSISTENCY_ERROR, GATE_UNAVAILABLE

Common software value rules: `implementation/PUBLIC_INTERFACE_CONTRACT.md`. Internal algorithms remain subordinate to C1; this scope does not supply missing science.

## Required behavior
- Verify C1 SHA-256 bytes and mandatory file coverage.
- Run real pytest and TypeScript compiler, reject missing test paths.
- Validate scope structure, ownership, dependency edges and generated documents.
- Do not mark scientific gates as passed when a runner or fixture is absent.

## Allowed paths
- `scripts/`
- `tests/contract/foundation/`
- `pyproject.toml`
- `.github/`
- `frontend/scaffold/`
- `frontend/tsconfig.json`
- `frontend/package.json`
- `frontend/package-lock.json`
- `requirements/foundation.txt`

Paths ending in `/` are exclusive subtrees. Other entries are exact files. Fixture/reference/expected paths are owned as one bundle. Rerunning another owner’s fixture grants no write access. Shared tooling handoffs are enumerated in SCOPE_DEPENDENCY_GRAPH.

## Forbidden changes
- Any C1 equation, correlation, method selection, fixture input, threshold, scientific fallback or output definition without approved BCR.
- Any module/fixture owned by another scope except the documented S00 to S19 tooling handoff.
- Clipping, silent normalization/parameter fitting, candidate as oracle, fabricated scientific output.

## Tests
- `tests/contract/foundation/test_manifest_integrity.py`
- `tests/contract/foundation/test_scope_lint.py`
- `tests/contract/foundation/test_gates.py`
- `tests/contract/foundation/test_foundation.py`

These are files to create by scope completion, not tests claimed to exist today. Foundation tests already exist. Scientific fixtures are data, not pytest directories: their owning acceptance test imports them and fails if they or a qualified reference are missing. Frontend unit/E2E commands use Vitest/Playwright produced by S19, never pytest.

Owned numerical/experimental fixtures: none; consume/rerun only as listed in SCOPE_VALIDATION_MATRIX.

## Acceptance
Run from repository root with the activated foundation environment. S00 setup: `python -m venv .venv`, activate it, `python -m pip install -r requirements/foundation.txt`, `python -m pip install --no-build-isolation --no-deps -e .`, `npm --prefix frontend ci`.
```sh
python scripts/run_foundation.py
python -m pytest tests/contract/foundation -q
```

Install scope-specific dependencies with pinned locks during the owning scope; acceptance cannot skip missing tests. Foundation commands execute now. Feature commands must execute at this scope’s completion; zero tests, unavailable adapters and unresolved contract gaps are not PASS.

## Produced artifacts
- `scripts/`
- `pyproject.toml`
- `.github/`
- `frontend/scaffold/`
- `frontend/tsconfig.json`
- `frontend/package.json`
- `frontend/package-lock.json`
- `requirements/foundation.txt`
- `artifacts/S00/acceptance.json`

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
