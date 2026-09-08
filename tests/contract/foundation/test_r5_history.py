"""Persistent shared-history integrity regressions; no fabricated baseline."""
from pathlib import Path
import importlib.util,json,hashlib,shutil
import pytest
ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('r5_integrity_gate',ROOT/'scripts/check_contracts.py')
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj):p.write_text(json.dumps(obj,indent=2)+'\n')
@pytest.fixture(scope='module')
def corpus(tmp_path_factory):
    # One mutable disposable corpus per test module; mutations are restored.
    root=tmp_path_factory.mktemp('r5-integrity')
    shutil.copytree(ROOT/gate.PREFIX,root/gate.PREFIX)
    return root
@pytest.fixture
def restore(corpus):
    saved={}
    def remember(path):saved.setdefault(path,path.read_bytes())
    yield remember
    for path,data in saved.items():path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
def refresh(corpus,restore):
    p=corpus/gate.MANIFEST;restore(p);m=json.loads(p.read_text())
    m['files']={f.relative_to(corpus).as_posix():sha(f) for f in (corpus/gate.PREFIX).rglob('*') if f.is_file() and f!=p}
    write(p,m)
def test_r5_shared_layout_is_real(corpus):
    m=json.loads((corpus/gate.MANIFEST).read_text())
    assert m['version']=='C1.0-R5' and m['predecessor_history_layout']=='shared-root-v1'
    assert m['predecessor_manifest_path']==gate.PREFIX+'/history/C1.0-R4/C1_BASELINE_MANIFEST_SHA256.json'
    assert not (corpus/gate.PREFIX/'history/C1.0-R4/history').exists()
    assert gate.check(corpus)['result']=='PASS'
@pytest.mark.parametrize('mode',['tamper','missing'])
def test_predecessor_manifest_identity_remains_bound(corpus,restore,mode):
    m=json.loads((corpus/gate.MANIFEST).read_text());p=corpus/m['predecessor_manifest_path'];restore(p)
    if mode=='tamper':p.write_bytes(p.read_bytes()+b' ')
    else:p.unlink()
    refresh(corpus,restore)
    with pytest.raises(gate.IntegrityError,match='PREDECESSOR_MANIFEST_(MISMATCH|MISSING)'):gate.check(corpus)
@pytest.mark.parametrize('rel',['history/C1.0/PHYSICS_SPEC.md','history/C1.0-R3/PHYSICS_SPEC.md','history/C1.0-R4/PHYSICS_SPEC.md'])
@pytest.mark.parametrize('mode',['tamper','missing'])
def test_original_hash_survives_current_manifest_rehash(corpus,restore,rel,mode):
    p=corpus/gate.PREFIX/rel;restore(p)
    if mode=='tamper':p.write_bytes(p.read_bytes()+b'changed')
    else:p.unlink()
    refresh(corpus,restore)
    with pytest.raises(gate.IntegrityError,match='PREDECESSOR_BYTES_(MISMATCH|MISSING)'):gate.check(corpus)
@pytest.mark.parametrize('bad',['../outside','docs/science/C1.0/../outside','/tmp/outside','docs/science/C1.0/history/../../outside','docs/science/C1.0/history\\outside','docs/science/C1.0/history/C:/outside'])
def test_rehashed_predecessor_cannot_supply_unsafe_path(corpus,restore,bad):
    mp=corpus/gate.MANIFEST;m=json.loads(mp.read_text());p=corpus/m['predecessor_manifest_path']
    restore(p);old=json.loads(p.read_text());old['files'][bad]='0'*64;write(p,old)
    restore(mp);m['predecessor_manifest_sha256']=sha(p);write(mp,m);refresh(corpus,restore)
    with pytest.raises(gate.IntegrityError,match='UNSAFE_PREDECESSOR_PATH'):gate.check(corpus)
@pytest.mark.parametrize('layout,error',[('guess','LAYOUT_UNKNOWN'),(None,'PREDECESSOR_BYTES_MISSING')])
def test_no_unknown_layout_or_implicit_fallback(corpus,restore,layout,error):
    p=corpus/gate.MANIFEST;restore(p);m=json.loads(p.read_text())
    if layout is None:m.pop('predecessor_history_layout')
    else:m['predecessor_history_layout']=layout
    write(p,m)
    with pytest.raises(gate.IntegrityError,match=error):gate.check(corpus)
