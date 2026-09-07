import importlib.util
import json
import shutil
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('integrity', ROOT / 'scripts/check_contracts.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

@pytest.fixture
def corpus(tmp_path):
    shutil.copytree(ROOT / module.PREFIX, tmp_path / module.PREFIX)
    return tmp_path

def edit_manifest(root, change):
    p = root / module.MANIFEST
    data = json.loads(p.read_text())
    change(data)
    p.write_text(json.dumps(data))

def test_valid_manifest_passes(corpus):
    assert module.check(corpus)['result'] == 'PASS'

def test_modified_bytes_fail(corpus):
    p = corpus / next(iter(sorted(module.REQUIRED)))
    p.write_bytes(p.read_bytes() + b'\r\n')
    with pytest.raises(module.IntegrityError, match='HASH_MISMATCH'):
        module.check(corpus)

def test_missing_file_fails(corpus):
    (corpus / next(iter(module.REQUIRED))).unlink()
    with pytest.raises(module.IntegrityError, match='MISSING'):
        module.check(corpus)

def test_incorrect_hash_fails(corpus):
    edit_manifest(corpus, lambda m: m['files'].update({next(iter(module.REQUIRED)): '0' * 64}))
    with pytest.raises(module.IntegrityError, match='HASH_MISMATCH'):
        module.check(corpus)

def test_removed_required_entry_fails(corpus):
    edit_manifest(corpus, lambda m: m['files'].pop(next(iter(module.REQUIRED))))
    with pytest.raises(module.IntegrityError, match='UNLISTED'):
        module.check(corpus)

@pytest.mark.parametrize('key,value', [('version','C2.0'), ('status','READY')])
def test_wrong_authority_fails(corpus,key,value):
    edit_manifest(corpus,lambda m:m.update({key:value}))
    with pytest.raises(module.IntegrityError, match='VERSION_OR_STATUS'):
        module.check(corpus)

def test_unmanifested_normative_file_fails(corpus):
    (corpus / module.PREFIX / 'EXTRA.md').write_text('unreviewed')
    with pytest.raises(module.IntegrityError, match='UNLISTED'):
        module.check(corpus)

def test_path_escape_fails(corpus):
    edit_manifest(corpus,lambda m:m['files'].update({'../outside':'0'*64}))
    with pytest.raises(module.IntegrityError, match='UNSAFE'):
        module.check(corpus)

def test_duplicate_manifest_key_fails(corpus):
    p=corpus/module.MANIFEST
    p.write_text(p.read_text().replace('"version":', '"version":"C1.0", "version":',1))
    with pytest.raises(module.IntegrityError, match='DUPLICATE'):
        module.check(corpus)


def test_predecessor_bytes_preserved(corpus):
 assert module.check(corpus)['version']=='C1.0-R1'
 p=corpus/module.PREFIX/'history/C1.0/PHYSICS_SPEC.md';p.write_bytes(p.read_bytes()+b'changed')
 with pytest.raises(module.IntegrityError,match='HASH_MISMATCH'):module.check(corpus)
