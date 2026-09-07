"""Structural scope gate; scientific readiness is a separate, explicit gate."""
import argparse
import json
from pathlib import Path
from render_scopes import documents
from check_contracts import check as check_integrity
ROOT = Path(__file__).resolve().parents[1]


def check(root=ROOT, readiness=False):
    scopes = json.loads((root/'implementation/scope_registry.json').read_text())['scopes']
    vals = json.loads((root/'implementation/validation_registry.json').read_text())['validations']
    by = {s['id']: s for s in scopes}
    assert len(scopes) == len(by) == 23 and set(by) == {f'S{i:02}' for i in range(23)}, 'scope coverage'
    required = ['objective', 'normative_ids', 'allowed_paths', 'interfaces', 'behavior', 'tests', 'acceptance', 'artifacts', 'forbidden_changes', 'dod', 'failure_semantics']
    done, visiting = set(), set()
    def visit(k):
        assert k not in visiting, 'dependency cycle'
        if k in done: return
        visiting.add(k)
        for d in by[k]['dependencies']:
            assert d['scope'] in by and d['reason'].strip(), 'missing dependency'
            assert d['interface'] in [i['name'] for i in by[d['scope']]['interfaces']], 'missing consumed interface'
            visit(d['scope'])
        visiting.remove(k); done.add(k)
    for s in scopes:
        for field in required: assert s.get(field), f'{s["id"]}: missing {field}'
        assert set(s['failure_semantics']) == {'IMPLEMENTATION_DEFECT','VERIFICATION_FAILURE','SCIENTIFIC_CHANGE_REQUIRED','OUT_OF_SCOPE'}
        for i in s['interfaces']:
            for key in ['name','purpose','inputs','outputs','units','owner','mutability','failures']: assert i.get(key), f'incomplete interface {key}'
            assert i['owner'] == s['id']
        for p in s['allowed_paths']:
            assert not Path(p).is_absolute() and '..' not in Path(p).parts, 'unsafe ownership path'
        for p in s['tests']:
            assert any(p == a or (a.endswith('/') and p.startswith(a)) for a in s['allowed_paths']), f'unowned test {p}'
        visit(s['id'])
    handoffs = {('S00','S19',p) for p in ['frontend/package.json','frontend/package-lock.json','frontend/tsconfig.json']} | {('S00','S22','pyproject.toml')}
    for n,s in enumerate(scopes):
        for t in scopes[n+1:]:
            for a in s['allowed_paths']:
                for b in t['allowed_paths']:
                    if a == b or (a.endswith('/') and b.startswith(a)) or (b.endswith('/') and a.startswith(b)):
                        assert (s['id'],t['id'],a) in handoffs and a == b, f'ownership overlap {s["id"]}/{t["id"]}: {a}, {b}'
    assert len(vals) == 28 and {v['id'] for v in vals} == {f'VAL-{i:03}' for i in range(1,29)}, 'VAL coverage'
    for v in vals:
        if not v['mandatory']: continue
        owner = v['owner_scope']
        assert owner in by and v['fixture_owner'] == v['reference_owner'] == owner, 'ambiguous VAL ownership'
        assert [s['id'] for s in scopes if v['id'] in s['vals']] == [owner], 'duplicate/missing VAL owner'
        assert v['test'] in by[owner]['tests'], 'missing acceptance adapter'
        assert all(x in by for x in v['rerun_scopes'])
    for path, expected in documents(root).items():
        assert (root/path).read_text() == expected, f'generated document drift: {path}'
    check_integrity(root)
    index = json.loads((root/'docs/science/C1.0/NORMATIVE_ID_INDEX.json').read_text())
    for s in scopes:
        for identifier in s['normative_ids']:
            assert identifier in index, 'UNDEFINED_NORMATIVE_ID: ' + identifier
            item = index[identifier]
            assert item['definition_line'] in (root/item['path']).read_text().splitlines(), 'STALE_NORMATIVE_DEFINITION: ' + identifier
        for path in s.get('normative_annexes', []): assert (root/path).is_file(), 'missing normative annex'
    issues = json.loads((root/'implementation/readiness_issues.json').read_text())['issues']
    assert {i['id'] for i in issues} == {f'H-{n:02}' for n in range(1,7)}, 'ISSUE_COVERAGE_MISSING'
    opened = [i['id'] for i in issues if i['status'] != 'CLOSED']
    coverage = json.loads((root/'docs/science/C1.0/VALIDATION_CONTRACT_COVERAGE.json').read_text())['validations']
    cv = {v['id']:v for v in coverage}
    assert len(cv)==len(coverage) and set(cv)=={v['id'] for v in vals if v['mandatory']}, 'FIXTURE_COVERAGE_MISSING'
    if readiness:
        assert not opened, 'MISSING_PREIMPLEMENTATION_SCIENTIFIC_DECISION: ' + ', '.join(opened)
        for scope in scopes:
            for identifier in scope['normative_ids']:
                assert index[identifier].get('definition_status','COMPLETE') == 'COMPLETE', 'INCOMPLETE_NORMATIVE_DEFINITION: '+identifier
        for v in vals:
            if not v['mandatory']: continue
            c=cv[v['id']]
            assert c['contract_status']=='COMPLETE' and not c['missing'], 'INCOMPLETE_VALIDATION_CONTRACT: '+v['id']
            required={'objective','type','physics_numerics','initial_state','geometry','domain','mesh_sequence','dt_sequence','boundary_states','end_condition','sampling','independent_reference','reference_resolution','observable','normalization','metric','threshold','failure','artifacts'}
            assert set(c['required_fields'])==required and (root/c['normative_path']).is_file(), 'INCOMPLETE_FIXTURE_FIELDS: '+v['id']
        for s in scopes:
            assert not s['issues'], 'UNSATISFIED_SCOPE_PRECONDITION: '+s['id']
    return {'result':'PASS','scope_count':len(scopes),'mandatory_validations_owned':sum(v['mandatory'] for v in vals),'open_specification_gaps':len(opened),'scientific_readiness':'PASS' if readiness else 'NOT_ASSERTED'}

if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('--readiness',action='store_true'); p.add_argument('--report',type=Path); a=p.parse_args()
    try:
        result=check(readiness=a.readiness); code=0
    except (AssertionError, KeyError, ValueError, OSError) as e:
        result={'result':'FAIL','reason':str(e)};code=1
    if a.report:
        a.report.parent.mkdir(parents=True,exist_ok=True); a.report.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result));raise SystemExit(code)
