# S14 — thermal-losses

## Objective
Implement selected thermal and mechanical gas-path source closures with separate ledgers.

## Identity
ID: `S14`. Status: `NOT_STARTED`. No scientific implementation is authorized by document existence alone.

## Dependencies
- S03 produces `ThermoModel`: Use pinned transport/EOS properties.
- S11 produces `EngineTopology`: Locate physical walls and loss regions.
- S09 produces `CharacterizedLoss`: Exclude W2 characterization regions from local K.
- S12 produces `ScavengingModel`: Combined source verification includes zone exchange.
- S13 produces `CombustionModel`: Combined source verification includes prescribed chemistry.

## Normative IDs
`CAP-007`, `CAP-008`, `PHY-007`, `PHY-008`, `NUM-005`, `VAL-003`, `VAL-018`, `VAL-022`, `VAL-024`

C1 paths: `docs/science/C1.0/GEN1_CONTRACT.md`, `PHYSICS_SPEC.md`, `NUMERICAL_METHOD_SPEC.md`, `VALIDATION_SPEC.md`. IDs above select the relevant clauses.
- `docs/architecture/A1.0/DOMAIN_MODEL.md` — ownership and value-object contracts
- `docs/architecture/A1.0/MODULE_BOUNDARIES.md` — ownership and value-object contracts
- `docs/architecture/A1.0/APPLICATION_AND_API_CONTRACT.md` — public resource and error contracts

## Required interfaces
### PhysicalSources
- Purpose: Implement selected thermal and mechanical gas-path source closures with separate ledgers.
- Inputs: ThermoState; physical geometry/perimeter; prescribed wall data; Hcc,Cq,roughness and measured K map; disjoint loss regions
- Outputs/signatures: evaluate(...) -> SourceRates(momentum,heat,species=0), entropy/force diagnostics and timestep-bound inputs
- Units: N/m for A-weighted momentum source; W/m duct heat; W 0D heat; Pa FMEP separate
- Owner: S14
- Mutability: Frozen value objects; caller inputs borrowed read-only; methods return new values. Stateful services own their private state and expose snapshots only.
- Failure semantics: THERMAL_MODEL_OUT_OF_DOMAIN, LOSS_REGION_OVERLAP, REQUIRED_MAP_MISSING, SCIENTIFIC_CHANGE_REQUIRED

Common software value rules: `implementation/PUBLIC_INTERFACE_CONTRACT.md`. Internal algorithms remain subordinate to C1; this scope does not supply missing science.

## Required behavior
- Reject W2/K duplicate representation of the same measured region.
- Adiabatic shear has zero total-energy source; heat remains separately signed.
- No zero/default substitution for missing Hcc/Cq required characterization.
- H-06 must supply the exact named correlation realization and H-03 the absent VAL-022 fiche.

## Allowed paths
- `src/dino2next/heat_transfer/`
- `src/dino2next/losses/`
- `schemas/thermal_loss/`
- `tests/unit/s14/`
- `tests/contract/s14/`
- `validation/fixtures/VAL-003/`
- `validation/references/VAL-003/`
- `validation/expected/VAL-003/`
- `tests/numerical/VAL-003/`
- `validation/fixtures/VAL-018/`
- `validation/references/VAL-018/`
- `validation/expected/VAL-018/`
- `tests/numerical/VAL-018/`
- `validation/fixtures/VAL-022/`
- `validation/references/VAL-022/`
- `validation/expected/VAL-022/`
- `tests/numerical/VAL-022/`
- `validation/fixtures/VAL-024/`
- `validation/references/VAL-024/`
- `validation/expected/VAL-024/`
- `tests/numerical/VAL-024/`

Paths ending in `/` are exclusive subtrees. Other entries are exact files. Fixture/reference/expected paths are owned as one bundle. Rerunning another owner’s fixture grants no write access. Shared tooling handoffs are enumerated in SCOPE_DEPENDENCY_GRAPH.

## Forbidden changes
- Any C1 equation, correlation, method selection, fixture input, threshold, scientific fallback or output definition without approved BCR.
- Any module/fixture owned by another scope except the documented S00 to S19 tooling handoff.
- Clipping, silent normalization/parameter fitting, candidate as oracle, fabricated scientific output.

## Tests
- `tests/unit/s14/test_source_ledgers.py`
- `tests/contract/s14/test_loss_region_ownership.py`
- `tests/numerical/VAL-003/test_acceptance.py`
- `tests/numerical/VAL-018/test_acceptance.py`
- `tests/numerical/VAL-022/test_acceptance.py`
- `tests/numerical/VAL-024/test_acceptance.py`

These are files to create by scope completion, not tests claimed to exist today. Foundation tests already exist. Scientific fixtures are data, not pytest directories: their owning acceptance test imports them and fails if they or a qualified reference are missing. Frontend unit/E2E commands use Vitest/Playwright produced by S19, never pytest.

Owned numerical/experimental fixtures: VAL-003, VAL-018, VAL-022, VAL-024

## Acceptance
Run from repository root with the activated foundation environment. S00 setup: `python -m venv .venv`, activate it, `python -m pip install -r requirements/foundation.txt`, `python -m pip install --no-build-isolation --no-deps -e .`, `npm --prefix frontend ci`.
```sh
python scripts/run_foundation.py
python -m pytest tests/unit/s14/test_source_ledgers.py tests/contract/s14/test_loss_region_ownership.py tests/numerical/VAL-003/test_acceptance.py tests/numerical/VAL-018/test_acceptance.py tests/numerical/VAL-022/test_acceptance.py tests/numerical/VAL-024/test_acceptance.py -q
```

Install scope-specific dependencies with pinned locks during the owning scope; acceptance cannot skip missing tests. Foundation commands execute now. Feature commands must execute at this scope’s completion; zero tests, unavailable adapters and unresolved contract gaps are not PASS.

## Produced artifacts
- `src/dino2next/heat_transfer/`
- `src/dino2next/losses/`
- `schemas/thermal_loss/`
- `validation/fixtures/VAL-003/`
- `validation/references/VAL-003/`
- `validation/expected/VAL-003/`
- `validation/fixtures/VAL-018/`
- `validation/references/VAL-018/`
- `validation/expected/VAL-018/`
- `validation/fixtures/VAL-022/`
- `validation/references/VAL-022/`
- `validation/expected/VAL-022/`
- `validation/fixtures/VAL-024/`
- `validation/references/VAL-024/`
- `validation/expected/VAL-024/`
- `artifacts/S14/acceptance.json`

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
Open audit findings: `H-03`, `H-06`. Stop the affected scientific path until reviewed normative consolidation resolves these. See `implementation/readiness_issues.json` and `docs/CODEX_READINESS_AUDIT.md`. This is not an invitation for Codex to choose a formula.

Rollback: keep failure artifacts, revert only this scope’s unaccepted changes or abandon its unmerged branch. Never reset unrelated work or rewrite a shared fixture.
