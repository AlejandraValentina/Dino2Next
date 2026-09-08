"""Render scope/ownership documents from reviewed software-only registries."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def documents(root=ROOT):
    scopes=json.loads((root/'implementation/scope_registry.json').read_text())['scopes']
    vals=json.loads((root/'implementation/validation_registry.json').read_text())['validations']
    docs={}
    for s in scopes:
        old=list((root/'implementation/scopes').glob(s['id']+'-*.md'))
        path=old[0].relative_to(root).as_posix() if len(old)==1 else f'implementation/scopes/{s["id"]}-{s["title"]}.md'
        b=[f'# {s["id"]} — {s["title"]}', '', '## Objective', s['objective'], '', '## Identity', f'ID: `{s["id"]}`. Status: `{s["status"]}`. No scientific implementation is authorized by document existence alone.', '', '## Dependencies']
        b += [f'- {d["scope"]} produces `{d["interface"]}`: {d["reason"]}.' for d in s['dependencies']] or ['None; foundation root.']
        b += ['', '## Normative IDs', ', '.join(f'`{x}`' for x in s['normative_ids']), '', 'C1 paths: `docs/science/C1.0/GEN1_CONTRACT.md`, `PHYSICS_SPEC.md`, `NUMERICAL_METHOD_SPEC.md`, `VALIDATION_SPEC.md`. IDs above select the relevant clauses.']
        b += [f'- `{p}` — '+ ('public resource and error contracts' if 'APPLICATION' in p else 'ownership and value-object contracts') for p in s['architecture']]
        b += [f'- `{p}`' for p in s['ux']]
        b += [(f'- `{p}` — normative clause companion' if 'BCR-' in p else f'- `{p}` — C1.0-R2 normative clause companion') for p in s.get('normative_annexes', [])]
        b += ['', '## Required interfaces']
        for i in s['interfaces']:
            b += [f'### {i["name"]}',f'- Purpose: {i["purpose"]}',f'- Inputs: {i["inputs"]}',f'- Outputs/signatures: {i["outputs"]}',f'- Units: {i["units"]}',f'- Owner: {i["owner"]}',f'- Mutability: {i["mutability"]}',f'- Failure semantics: {i["failures"]}']
        b += ['', 'Common software value rules: `implementation/PUBLIC_INTERFACE_CONTRACT.md`. Internal algorithms remain subordinate to C1; this scope does not supply missing science.', '', '## Required behavior']+[f'- {x}' for x in s['behavior']]
        b += ['', '## Allowed paths']+[f'- `{x}`' for x in s['allowed_paths']]
        b += ['', 'Paths ending in `/` are exclusive subtrees except for the exact file handoffs enumerated in SCOPE_DEPENDENCY_GRAPH. Other entries are exact files. Fixture/reference/expected paths are owned as one bundle. Rerunning another owner’s fixture grants no write access. Shared tooling handoffs are enumerated in SCOPE_DEPENDENCY_GRAPH.', '', '## Forbidden changes']+[f'- {x}' for x in s['forbidden_changes']]
        b += ['', '## Tests']+[f'- `{x}`' for x in s['tests']]
        b += ['', 'These are files to create by scope completion, not tests claimed to exist today. Foundation tests already exist. Scientific fixtures are data, not pytest directories: their owning acceptance test imports them and fails if they or a qualified reference are missing. Frontend unit/E2E commands use Vitest/Playwright produced by S19, never pytest.']
        b += ['','Owned numerical/experimental fixtures: '+(', '.join(s['vals']) if s['vals'] else 'none; consume/rerun only as listed in SCOPE_VALIDATION_MATRIX.'), '', '## Acceptance', 'Run from repository root with the activated foundation environment. S00 setup: `python -m venv .venv`, activate it, `python -m pip install -r requirements/foundation.txt`, `python -m pip install --no-build-isolation --no-deps -e .`, `npm --prefix frontend ci`.']
        b += ['```sh', *s['acceptance'], '```']
        b += ['', 'Install scope-specific dependencies with pinned locks during the owning scope; acceptance cannot skip missing tests. Foundation commands execute now. Feature commands must execute at this scope’s completion; zero tests, unavailable adapters and unresolved contract gaps are not PASS.', '', '## Produced artifacts']+[f'- `{x}`' for x in s['artifacts']]
        b += ['', 'The acceptance artifact records commands, exits, nonzero collected-test counts, C1 hash, commit, environment and any pending heavy gates. It is an output under ignored `artifacts/`, not a fabricated precompleted report.', '', '## Definition of done']+[f'- {x}' for x in s['dod']]
        b += ['', '## Reviewer checklist', '- Read the normative IDs before reviewing the builder explanation.', '- Check every public signature, unit, mutation boundary and error case against Required interfaces.', '- Verify each dependency supplies the consumed object; no duplicate fixture owner or unauthorized file.', '- Confirm actual test collection, reference independence and pending-heavy status; no hidden relaxation.', '- For UI, verify schema pointer → domain → application → solver input → provenance from the field binding table.', '', '## Failure semantics']+[f'- `{k}`: {v}' for k,v in s['failure_semantics'].items()]
        b += ['', '## Specification preconditions', ('Open preimplementation decisions: '+', '.join(f'`{x}`' for x in s['issues'])+'. Stop the affected scientific path until reviewed normative consolidation resolves these. See `implementation/readiness_issues.json` and `docs/CODEX_READINESS_AUDIT.md`. This is not an invitation for Codex to choose a formula.' if s['issues'] else 'No direct specification gap recorded for this scope. Dependency acceptance is still required.'), '', 'Rollback: keep failure artifacts, revert only this scope’s unaccepted changes or abandon its unmerged branch. Never reset unrelated work or rewrite a shared fixture.','']
        docs[path]='\n'.join(b)
    b=['# Scope dependency graph','','Registry source: `implementation/scope_registry.json`. Every edge below names an actual consumed public interface. Order is topological; numbering is not a substitute for dependency acceptance.','','| Producer | Consumer | Interface | Reason |','|---|---|---|---|']
    for s in scopes:
        for d in s['dependencies']:b.append(f'| {d["scope"]} | {s["id"]} | `{d["interface"]}` | {d["reason"]} |')
    b += ['', '## Explicit tooling handoffs', '- S00 owns `frontend/package.json`, `frontend/package-lock.json`, `frontend/tsconfig.json` at foundation. S19 may extend them solely for React/Vitest/Playwright after S00 is complete; later UI scopes cannot edit them independently.', '- S00 owns `pyproject.toml` at foundation. S22 owns final packaging composition after dependencies complete. Packaging changes do not authorize changing scientific dependencies or algorithms.', '- Other cross-scope edits return to the owner scope; no blanket shared directories.', '', 'S18 is an aggregator, not a prerequisite for earlier scientific test execution. Each fixture owner supplies a standalone pytest acceptance adapter; S18 later consumes it. This removes the previous validation-runner dependency cycle.', '']
    if any('material_path_handoff' in s for s in scopes):
        b += ['## MR-008 bounded S05 to S06 handoff',
              '- S05 retains ownership of `src/dino2next/gasdynamics/`. S06 may edit only `src/dino2next/gasdynamics/__init__.py` (additive public exposure), `src/dino2next/gasdynamics/regional.py` (regional extension), and `src/dino2next/gasdynamics/README.md` (documentation), under its explicit MR-008 material_path_handoff declaration.',
              '- This grants no shared directory, sibling file, S05 test path, other-scope access, or replacement of accepted homogeneous behavior. New tests remain in S06-owned test paths.', '']
    docs['implementation/SCOPE_DEPENDENCY_GRAPH.md']='\n'.join(b)
    b=['# Scope validation matrix','','All 28 identifiers are classified. A number alone does not create a mandatory validation: 012,015,017,019 have no requirement in current C1 and remain explicit nonmandatory entries. VAL-022 is mandatory by CAP-007 and restored as the C03 motored experimental data contract VF-022; S18 owns it. All 24 mandatory fiches have concrete field values in the R2 coverage catalogue; execution status remains separate.','','Reference owner is accountable for a separate implementation/data source, not permission to use candidate output as its oracle. Fixture, reference and expected bundle has exactly one owner. Rerun scopes have read-only access.','','| VAL | Required | Owner | Rerun scopes | Gate class | Reference owner | Fixture owner | CI/milestone | Failure consequence |','|---|---|---|---|---|---|---|---|---|']
    for v in vals:
        b.append('| '+' | '.join([v['id'],'yes' if v['mandatory'] else 'no',v['owner_scope'] or 'not required',', '.join(v['rerun_scopes']) or 'none',v['gate_class'],v['reference_owner'] or 'none',v['fixture_owner'] or 'none',('owner milestone / '+v['execution_status']) if v['mandatory'] else v['contract_status'],v['failure_consequence']])+' |')
    b += ['', 'Canonical machine records: `implementation/validation_registry.json`. No scientific test is run by PR_FAST merely because its directory exists. Later gate adapters are explicit; unavailable adapters fail with GATE_UNAVAILABLE. Expensive gates retain MANDATORY_VERIFICATION_DURING_IMPLEMENTATION status.','']
    docs['implementation/SCOPE_VALIDATION_MATRIX.md']='\n'.join(b)
    return docs

if __name__=='__main__':
    for path,text in documents().items():
        p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8')
