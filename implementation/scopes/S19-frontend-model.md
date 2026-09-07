# S19 — frontend-model

## Objective
Build the traditional engine tree, short wizard and backend-consumed model editors.

## Identity
ID: `S19`. Status: `NOT_STARTED`. No scientific implementation is authorized by document existence alone.

## Dependencies
- S17 produces `ApplicationAPI`: Consume generated client, schemas and immutable revision endpoints.
- S00 produces `FoundationChecks`: Explicit tooling handoff for frontend package/lock/tsconfig after S00 completion.

## Normative IDs
`CAP-001`, `CAP-004`, `CAP-010`, `PHY-001`, `PHY-005`

C1 paths: `docs/science/C1.0/GEN1_CONTRACT.md`, `PHYSICS_SPEC.md`, `NUMERICAL_METHOD_SPEC.md`, `VALIDATION_SPEC.md`. IDs above select the relevant clauses.
- `docs/architecture/A1.0/DOMAIN_MODEL.md` — ownership and value-object contracts
- `docs/architecture/A1.0/MODULE_BOUNDARIES.md` — ownership and value-object contracts
- `docs/architecture/A1.0/APPLICATION_AND_API_CONTRACT.md` — public resource and error contracts
- `docs/ux/UX1.0/ENGINEERING_WORKFLOW.md`
- `docs/ux/UX1.0/NAVIGATION_MODEL.md`
- `docs/ux/UX1.0/INPUT_FORM_PATTERNS.md`
- `docs/ux/UX1.0/BASIC_VS_ADVANCED_POLICY.md`
- `docs/ux/UX1.0/ENGINEERING_USER_JOURNEYS.md`
- `docs/ux/UX1.0/UI_TRACEABILITY_MATRIX.md`
- `docs/science/C1.0/PHYSICS_RESTORATION_ANNEX.md` — C1.0-R1 selected-source restoration
- `docs/science/C1.0/LOSS_CHARACTERIZATION_NORMATIVE_ANNEX.md` — C1.0-R1 selected-source restoration

## Required interfaces
### ModelWorkspace
- Purpose: Build the traditional engine tree, short wizard and backend-consumed model editors.
- Inputs: generated ApplicationAPI client; project revision; field descriptors with schema JSON Pointer, units, required/domain/availability metadata
- Outputs/signatures: ModelWorkspace route /projects/:id/model/:section; draft/save/preflight intents; ModelRouteEntry; FieldBinding registry
- Units: display units from backend schema; stored SI through API; no authoritative derived displacement/power
- Owner: S19
- Mutability: Frozen value objects; caller inputs borrowed read-only; methods return new values. Stateful services own their private state and expose snapshots only.
- Failure semantics: FIELD_UNSUPPORTED, UNSAVED_CHANGES, API_VALIDATION_ERROR, REVISION_CONFLICT

Common software value rules: `implementation/PUBLIC_INTERFACE_CONTRACT.md`. Internal algorithms remain subordinate to C1; this scope does not supply missing science.

## Required behavior
- Implement J01–J04: short creation, geometry/ports, exhaust and operating-point editing with free navigation after creation.
- Every scientific editable field binds to S17 schema pointer and eventual solver input/provenance; absent backend consumer means disabled NOT_YET_SUPPORTED.
- No physical calculator in frontend; displayed derived displacement comes from backend.
- Advanced station/uncertainty metadata is reachable without hiding required errors; keyboard tree and focus restoration are tested.
- Own shell route outlet that consumes named route entries; S20/S21 own their entries and do not rewrite shell.
- Add React/Vite/Vitest/Playwright tooling with committed exact npm lock; scripts test:unit (vitest run), test:e2e (playwright test), build and typecheck. Network/download setup is explicit; tests use API fixtures labelled CONTRACT_TEST_ONLY and never persist them as engine evidence.

## Allowed paths
- `frontend/src/model/`
- `frontend/src/navigation/`
- `frontend/src/shell/`
- `frontend/src/route_entries/model.ts`
- `frontend/tests/s19/`
- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/tsconfig.json`
- `frontend/vite.config.ts`
- `frontend/playwright.config.ts`
- `frontend/vitest.config.ts`
- `frontend/index.html`

Paths ending in `/` are exclusive subtrees. Other entries are exact files. Fixture/reference/expected paths are owned as one bundle. Rerunning another owner’s fixture grants no write access. Shared tooling handoffs are enumerated in SCOPE_DEPENDENCY_GRAPH.

## Forbidden changes
- Any C1 equation, correlation, method selection, fixture input, threshold, scientific fallback or output definition without approved BCR.
- Any module/fixture owned by another scope except the documented S00 to S19 tooling handoff.
- Clipping, silent normalization/parameter fitting, candidate as oracle, fabricated scientific output.

## Tests
- `frontend/tests/s19/model.test.tsx`
- `frontend/tests/s19/journeys.spec.ts`

These are files to create by scope completion, not tests claimed to exist today. Foundation tests already exist. Scientific fixtures are data, not pytest directories: their owning acceptance test imports them and fails if they or a qualified reference are missing. Frontend unit/E2E commands use Vitest/Playwright produced by S19, never pytest.

Owned numerical/experimental fixtures: none; consume/rerun only as listed in SCOPE_VALIDATION_MATRIX.

## Acceptance
Run from repository root with the activated foundation environment. S00 setup: `python -m venv .venv`, activate it, `python -m pip install -r requirements/foundation.txt`, `python -m pip install --no-build-isolation --no-deps -e .`, `npm --prefix frontend ci`.
```sh
python scripts/run_foundation.py
npm --prefix frontend run test:unit -- tests/s19
npm --prefix frontend run test:e2e -- tests/s19/journeys.spec.ts
npm --prefix frontend run build
```

Install scope-specific dependencies with pinned locks during the owning scope; acceptance cannot skip missing tests. Foundation commands execute now. Feature commands must execute at this scope’s completion; zero tests, unavailable adapters and unresolved contract gaps are not PASS.

## Produced artifacts
- `frontend/src/model/`
- `frontend/src/navigation/`
- `frontend/src/shell/`
- `frontend/src/route_entries/model.ts`
- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/tsconfig.json`
- `frontend/vite.config.ts`
- `frontend/playwright.config.ts`
- `frontend/vitest.config.ts`
- `frontend/index.html`
- `artifacts/S19/acceptance.json`

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
