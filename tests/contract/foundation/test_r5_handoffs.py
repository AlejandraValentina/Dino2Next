"""Persistent R5 scope-boundary tests against repository scripts."""
from pathlib import Path
import importlib.util,json,sys,copy
import pytest
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('r5_scope_gate',ROOT/'scripts/check_scopes.py')
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
PATHS=['src/dino2next/gasdynamics/'+name for name in ('__init__.py','regional.py','README.md')]
ALIASES=['./src/dino2next/gasdynamics/other.py','src\\dino2next\\gasdynamics\\other.py',
         'src//dino2next/gasdynamics/other.py','src/dino2next/../gasdynamics/other.py',
         'C:/src/dino2next/gasdynamics/other.py','/src/dino2next/gasdynamics/other.py',
         'src/dino2next/gasdynamics//','src/dino2next/gasdynamics/./other.py','']
@pytest.fixture
def scopes():return json.loads((ROOT/'implementation/scope_registry.json').read_text())['scopes']
def by(scopes,id):return next(s for s in scopes if s['id']==id)
def test_r5_has_exact_reviewed_handoff(scopes):
    s=by(scopes,'S06')
    assert s['material_path_handoff']=={'owner':'S05','normative_id':'MR-008','paths':PATHS}
    assert set(PATHS)<=set(s['allowed_paths']) and 'MR-008' in s['normative_ids']
    gate.check_ownership(scopes)
def test_removing_handoff_does_not_grant_access(scopes):
    by(scopes,'S06').pop('material_path_handoff')
    with pytest.raises(AssertionError,match='ownership overlap'):gate.check_ownership(scopes)
@pytest.mark.parametrize('path',['src/dino2next/gasdynamics/','src/dino2next/gasdynamics/sibling.py',
    'src/dino2next/gasdynamics/regional/','tests/unit/s05/new.py','tests/contract/s05/new.py'])
def test_sibling_directory_and_owner_tests_are_not_shared(scopes,path):
    by(scopes,'S06')['allowed_paths'].append(path)
    with pytest.raises(AssertionError,match='ownership overlap'):gate.check_ownership(scopes)
@pytest.mark.parametrize('other',['S04','S07','S22'])
def test_other_consumer_rejected(scopes,other):
    by(scopes,other)['allowed_paths'].append(PATHS[1])
    with pytest.raises(AssertionError,match='ownership overlap'):gate.check_ownership(scopes)
@pytest.mark.parametrize('field,value',[('owner','S04'),('normative_id','MR-010'),('paths',PATHS+['src/dino2next/gasdynamics/sibling.py'])])
def test_altered_handoff_rejected(scopes,field,value):
    by(scopes,'S06')['material_path_handoff'][field]=value
    with pytest.raises(AssertionError,match='invalid material handoff'):gate.check_ownership(scopes)
@pytest.mark.parametrize('alias',ALIASES)
def test_aliases_fail_closed(scopes,alias):
    by(scopes,'S06')['allowed_paths'].append(alias)
    with pytest.raises(AssertionError,match='unsafe ownership path'):gate.check_ownership(scopes)
def test_missing_normative_id_rejected(scopes):
    by(scopes,'S06')['normative_ids'].remove('MR-008')
    with pytest.raises(AssertionError,match='missing MR-008'):gate.check_ownership(scopes)
def test_missing_declared_file_rejected(scopes):
    by(scopes,'S06')['allowed_paths'].remove(PATHS[1])
    with pytest.raises(AssertionError,match='paths missing'):gate.check_ownership(scopes)
def test_graph_exposes_exact_handoff():
    graph=gate.documents(ROOT)['implementation/SCOPE_DEPENDENCY_GRAPH.md']
    assert '## MR-008 bounded S05 to S06 handoff' in graph
    assert 'additive public exposure' in graph and 'S05 test path' in graph
    for path in PATHS:assert '`'+path+'`' in graph
def test_full_gate_rejects_alias_before_integrity_without_copying_history(scopes,tmp_path):
    dest=tmp_path/'implementation';dest.mkdir()
    (dest/'validation_registry.json').write_bytes((ROOT/'implementation/validation_registry.json').read_bytes())
    for alias in ALIASES:
        records=copy.deepcopy(scopes);by(records,'S06')['allowed_paths'].append(alias)
        (dest/'scope_registry.json').write_text(json.dumps({'scopes':records}))
        with pytest.raises(AssertionError,match='unsafe ownership path'):gate.check(tmp_path,readiness=True)
