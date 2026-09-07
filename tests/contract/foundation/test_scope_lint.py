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
 shutil.copytree(ROOT/'implementation',tmp_path/'implementation')
 shutil.copytree(ROOT/'docs/science/C1.0',tmp_path/'docs/science/C1.0')
 return tmp_path

def test_valid(): assert check()['scope_count']==23

def test_readiness_cannot_hide_gaps():
 with pytest.raises(AssertionError,match='MISSING_PREIMPLEMENTATION_SCIENTIFIC_DECISION'): check(readiness=True)

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


def test_cannot_remove_issue_register(corpus):
 p=corpus/'implementation/readiness_issues.json';p.write_text('{"issues": []}')
 with pytest.raises(AssertionError,match='ISSUE_COVERAGE_MISSING'):check(corpus,readiness=True)

def test_closed_flags_do_not_hide_missing_fixtures(corpus):
 p=corpus/'implementation/readiness_issues.json';d=json.loads(p.read_text())
 for i in d['issues']:i['status']='CLOSED'
 p.write_text(json.dumps(d))
 with pytest.raises(AssertionError,match='INCOMPLETE_(VALIDATION_CONTRACT|NORMATIVE_DEFINITION)'):check(corpus,readiness=True)

def test_unknown_normative_id_fails(corpus):
 p=corpus/'implementation/scope_registry.json';d=json.loads(p.read_text());d['scopes'][1]['normative_ids'].append('PHY-999');p.write_text(json.dumps(d))
 from render_scopes import documents
 for path,text in documents(corpus).items():(corpus/path).write_text(text)
 with pytest.raises(AssertionError,match='UNDEFINED_NORMATIVE_ID'):check(corpus)
