# S13 — combustion

## Objective
Advance the selected closed-cylinder prescribed reaction and exact stoichiometric ledger.

## Identity
ID: `S13`. Status: `NOT_STARTED`. No scientific implementation is authorized by document existence alone.

## Dependencies
- S03 produces `ThermoModel`: Use formation-inclusive species properties.
- S10 produces `EngineVolumes`: Read cylinder inventory.
- S12 produces `ScavengingModel`: Require conservative merged state at SOC.

## Normative IDs
`CAP-006`, `PHY-002`, `PHY-006`, `NUM-002`, `NUM-005`, `VAL-005`, `VAL-023`

C1 paths: `docs/science/C1.0/GEN1_CONTRACT.md`, `PHYSICS_SPEC.md`, `NUMERICAL_METHOD_SPEC.md`, `VALIDATION_SPEC.md`. IDs above select the relevant clauses.
- `docs/architecture/A1.0/DOMAIN_MODEL.md` — ownership and value-object contracts
- `docs/architecture/A1.0/MODULE_BOUNDARIES.md` — ownership and value-object contracts
- `docs/architecture/A1.0/APPLICATION_AND_API_CONTRACT.md` — public resource and error contracts
- `docs/science/C1.0/NUMERICAL_KERNEL_NORMATIVE_ANNEX.md` — C1.0-R1 selected-source restoration
- `docs/science/C1.0/STAGE_EVENT_RESTORATION_ANNEX.md` — C1.0-R1 selected-source restoration
- `docs/science/C1.0/PHYSICS_RESTORATION_ANNEX.md` — C1.0-R1 selected-source restoration
- `docs/science/C1.0/VALIDATION_FIXTURE_RESTORATION.md` — C1.0-R1 selected-source restoration

## Required interfaces
### CombustionModel
- Purpose: Advance the selected closed-cylinder prescribed reaction and exact stoichiometric ledger.
- Inputs: merged cylinder inventory; SOC/end event; supplied Wiebe parameters; stage angle; reactant-limited initial extent
- Outputs/signatures: initialize_soc(...) -> BurnState; reaction_increment(t0,t1) -> species increment and progress; admissibility_bound(...) -> bound diagnostic
- Units: extent kmol; kg chemical changes; rad/seconds; total-energy source zero
- Owner: S13
- Mutability: Frozen value objects; caller inputs borrowed read-only; methods return new values. Stateful services own their private state and expose snapshots only.
- Failure semantics: COMBUSTION_PORT_OPEN, REACTANT_DEPLETION, SOC_OUT_OF_DOMAIN, SCIENTIFIC_CHANGE_REQUIRED

Common software value rules: `implementation/PUBLIC_INTERFACE_CONTRACT.md`. Internal algorithms remain subordinate to C1; this scope does not supply missing science.

## Required behavior
- Use the exact selected reaction-coordinate integration, not an extra LHV energy source.
- Reject open-port or unmerged-cylinder SOC; preserve unburned reactants.
- End-burn handling is event aligned and does not overshoot terminal extent.
- H-02 must define how the exact coordinate composes with SSPRK2; no hidden splitting.

## Allowed paths
- `src/dino2next/combustion/`
- `schemas/combustion/`
- `tests/unit/s13/`
- `tests/contract/s13/`
- `validation/fixtures/VAL-005/`
- `validation/references/VAL-005/`
- `validation/expected/VAL-005/`
- `tests/numerical/VAL-005/`
- `validation/fixtures/VAL-023/`
- `validation/references/VAL-023/`
- `validation/expected/VAL-023/`
- `tests/numerical/VAL-023/`

Paths ending in `/` are exclusive subtrees. Other entries are exact files. Fixture/reference/expected paths are owned as one bundle. Rerunning another owner’s fixture grants no write access. Shared tooling handoffs are enumerated in SCOPE_DEPENDENCY_GRAPH.

## Forbidden changes
- Any C1 equation, correlation, method selection, fixture input, threshold, scientific fallback or output definition without approved BCR.
- Any module/fixture owned by another scope except the documented S00 to S19 tooling handoff.
- Clipping, silent normalization/parameter fitting, candidate as oracle, fabricated scientific output.

## Tests
- `tests/unit/s13/test_reaction_balance.py`
- `tests/contract/s13/test_soc_events.py`
- `tests/numerical/VAL-005/test_acceptance.py`
- `tests/numerical/VAL-023/test_acceptance.py`

These are files to create by scope completion, not tests claimed to exist today. Foundation tests already exist. Scientific fixtures are data, not pytest directories: their owning acceptance test imports them and fails if they or a qualified reference are missing. Frontend unit/E2E commands use Vitest/Playwright produced by S19, never pytest.

Owned numerical/experimental fixtures: VAL-005, VAL-023

## Acceptance
Run from repository root with the activated foundation environment. S00 setup: `python -m venv .venv`, activate it, `python -m pip install -r requirements/foundation.txt`, `python -m pip install --no-build-isolation --no-deps -e .`, `npm --prefix frontend ci`.
```sh
python scripts/run_foundation.py
python -m pytest tests/unit/s13/test_reaction_balance.py tests/contract/s13/test_soc_events.py tests/numerical/VAL-005/test_acceptance.py tests/numerical/VAL-023/test_acceptance.py -q
```

Install scope-specific dependencies with pinned locks during the owning scope; acceptance cannot skip missing tests. Foundation commands execute now. Feature commands must execute at this scope’s completion; zero tests, unavailable adapters and unresolved contract gaps are not PASS.

## Produced artifacts
- `src/dino2next/combustion/`
- `schemas/combustion/`
- `validation/fixtures/VAL-005/`
- `validation/references/VAL-005/`
- `validation/expected/VAL-005/`
- `validation/fixtures/VAL-023/`
- `validation/references/VAL-023/`
- `validation/expected/VAL-023/`
- `artifacts/S13/acceptance.json`

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
Open preimplementation decisions: `H-02`, `H-03`. Stop the affected scientific path until reviewed normative consolidation resolves these. See `implementation/readiness_issues.json` and `docs/CODEX_READINESS_AUDIT.md`. This is not an invitation for Codex to choose a formula.

Rollback: keep failure artifacts, revert only this scope’s unaccepted changes or abandon its unmerged branch. Never reset unrelated work or rewrite a shared fixture.
