import json
from pathlib import Path
import shutil
import sys
import pytest
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from check_scopes import check

@pytest.fixture
def corpus(tmp_path):
 shutil.copytree(ROOT/'implementation',tmp_path/'implementation');return tmp_path

def test_valid(): assert check()['scope_count']==23

def test_readiness_cannot_hide_gaps():
 with pytest.raises(AssertionError,match='OPEN_SPECIFICATION_GAPS'): check(readiness=True)

@pytest.mark.parametrize('mutation',['objective','cycle','interface','owner','document'])
def test_regressions_rejected(corpus,mutation):
 p=corpus/'implementation/scope_registry.json';d=json.loads(p.read_text())
 if mutation=='objective':d['scopes'][1]['objective']=''
 if mutation=='cycle':d['scopes'][0]['dependencies']=[{'scope':'S01','interface':'ConfigSnapshot','reason':'test'}]
 if mutation=='interface':d['scopes'][1]['dependencies'][0]['interface']='Missing'
 if mutation=='owner':d['scopes'][1]['allowed_paths'].append('scripts/')
 p.write_text(json.dumps(d))
 if mutation=='document':next((corpus/'implementation/scopes').glob('S01-*')).write_text('# incomplete template')
 with pytest.raises(AssertionError):check(corpus)
