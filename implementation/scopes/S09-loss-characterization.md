# S09 — loss-characterization

## Objective
Produce offline characterized lambda certificates and guarded runtime loss evaluation.

## Identity
ID: `S09`. Status: `NOT_STARTED`. No scientific implementation is authorized by document existence alone.

## Dependencies
- S01 produces `ConfigSnapshot`: Bind raw and derived resource identity.
- S03 produces `ThermoModel`: Use the certified EOS.
- S08 produces `PortPassage`: Evaluate the fixed characterization passage.

## Normative IDs
`CAP-004`, `PHY-005`, `NUM-005`, `NUM-007`, `VAL-004`, `VAL-013`, `VAL-016`

C1 paths: `docs/science/C1.0/GEN1_CONTRACT.md`, `PHYSICS_SPEC.md`, `NUMERICAL_METHOD_SPEC.md`, `VALIDATION_SPEC.md`. IDs above select the relevant clauses.
- `docs/architecture/A1.0/DOMAIN_MODEL.md` — ownership and value-object contracts
- `docs/architecture/A1.0/MODULE_BOUNDARIES.md` — ownership and value-object contracts
- `docs/architecture/A1.0/APPLICATION_AND_API_CONTRACT.md` — public resource and error contracts
- `docs/science/C1.0/NUMERICAL_KERNEL_NORMATIVE_ANNEX.md` — C1.0-R2 normative clause companion
- `docs/science/C1.0/STAGE_EVENT_RESTORATION_ANNEX.md` — C1.0-R2 normative clause companion
- `docs/science/C1.0/PHYSICS_RESTORATION_ANNEX.md` — C1.0-R2 normative clause companion
- `docs/science/C1.0/LOSS_CHARACTERIZATION_NORMATIVE_ANNEX.md` — C1.0-R2 normative clause companion
- `docs/science/C1.0/VALIDATION_FIXTURE_RESTORATION.md` — C1.0-R2 normative clause companion
- `docs/science/C1.0/BOUNDARY_CONTRACT.md` — C1.0-R2 normative clause companion
- `docs/science/C1.0/TIME_EVENT_PERIODICITY_CONTRACT.md` — C1.0-R2 normative clause companion
- `docs/science/C1.0/EXECUTABLE_VALIDATION_CATALOGUE.md` — C1.0-R2 normative clause companion
- `docs/science/C1.0/REFERENCE_EXECUTION_CONTRACT.md` — C1.0-R2 normative clause companion

## Required interfaces
### CharacterizedLoss
- Purpose: Produce offline characterized lambda certificates and guarded runtime loss evaluation.
- Inputs: RawCdDataset(stations, pressure types, reference area, direction, opening, observations,covariance); fixed geometry/EOS hashes; auxiliary p_window_in where required
- Outputs/signatures: characterize(dataset) -> LossMapCertificate; evaluate(certificate,state,opening,direction) -> lambda, uncertainty, momentum source and entropy diagnostic
- Units: Cd/lambda dimensionless; pressure Pa; w 1/m; source in Q momentum units; raw data immutable
- Owner: S09
- Mutability: Frozen value objects; caller inputs borrowed read-only; methods return new values. Stateful services own their private state and expose snapshots only.
- Failure semantics: LOSS_PARAMETER_NONIDENTIFIABLE, LOSS_PARAMETER_ILL_CONDITIONED, AUXILIARY_MEASUREMENT_REQUIRED, LOSS_DATA_OUT_OF_DOMAIN

Common software value rules: `implementation/PUBLIC_INTERFACE_CONTRACT.md`. Internal algorithms remain subordinate to C1; this scope does not supply missing science.

## Required behavior
- Raw Cd remains unchanged and linked to every fitted point.
- Report lack of identifying observations rather than choose a root in a plateau.
- No negative lambda, clipping, unqualified interpolation or extrapolation.
- Use LC-001…005 interpolation, certificate, covariance and conditioning guards; no online ambiguous Cd inversion.

## Allowed paths
- `src/dino2next/ports/characterization/`
- `schemas/port_loss/`
- `tests/unit/s09/`
- `tests/contract/s09/`

Paths ending in `/` are exclusive subtrees. Other entries are exact files. Fixture/reference/expected paths are owned as one bundle. Rerunning another owner’s fixture grants no write access. Shared tooling handoffs are enumerated in SCOPE_DEPENDENCY_GRAPH.

## Forbidden changes
- Any C1 equation, correlation, method selection, fixture input, threshold, scientific fallback or output definition without approved BCR.
- Any module/fixture owned by another scope except the documented S00 to S19 tooling handoff.
- Clipping, silent normalization/parameter fitting, candidate as oracle, fabricated scientific output.

## Tests
- `tests/unit/s09/test_identification_status.py`
- `tests/contract/s09/test_raw_cd_provenance.py`
- `tests/contract/s09/test_map_domain.py`

These are files to create by scope completion, not tests claimed to exist today. Foundation tests already exist. Scientific fixtures are data, not pytest directories: their owning acceptance test imports them and fails if they or a qualified reference are missing. Frontend unit/E2E commands use Vitest/Playwright produced by S19, never pytest.

Owned numerical/experimental fixtures: none; consume/rerun only as listed in SCOPE_VALIDATION_MATRIX.

## Acceptance
Run from repository root with the activated foundation environment. S00 setup: `python -m venv .venv`, activate it, `python -m pip install -r requirements/foundation.txt`, `python -m pip install --no-build-isolation --no-deps -e .`, `npm --prefix frontend ci`.
```sh
python scripts/run_foundation.py
python -m pytest tests/unit/s09/test_identification_status.py tests/contract/s09/test_raw_cd_provenance.py tests/contract/s09/test_map_domain.py -q
```

Install scope-specific dependencies with pinned locks during the owning scope; acceptance cannot skip missing tests. Foundation commands execute now. Feature commands must execute at this scope’s completion; zero tests, unavailable adapters and unresolved contract gaps are not PASS.

## Produced artifacts
- `src/dino2next/ports/characterization/`
- `schemas/port_loss/`
- `artifacts/S09/acceptance.json`

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
