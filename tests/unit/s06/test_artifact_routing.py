"""Software-only actual artifact routing; no time integration or science PASS."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]

def test_actual_adapter_checkpoint_and_final_files_survive_second_case(tmp_path):
    """Exercise actual I/O with initial states only; this is no numerical gate."""
    import importlib.util
    import types
    from hashlib import sha256
    import numpy as np
    path=ROOT/'validation/fixtures/VAL-008/execution.py'
    spec=importlib.util.spec_from_file_location('s06_routing_io',path)
    driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
    class InitialSampleOnly:
        def __getattr__(self,name):return getattr(np,name)
        def linspace(self,start,stop,num):
            assert num==101
            return np.array([start])
    driver.np=InitialSampleOnly()
    driver.subprocess=types.SimpleNamespace(check_output=lambda *a,**k:'SOFTWARE_ROUTING_TEST_NO_TIME_INTEGRATION')
    fixture=driver.verify_fixture();first=None
    for index in (0,7):
        case=fixture['cases'][index];n=fixture['meshes'][case['kind']][0];cfl=.2
        record=driver.execute(case,n,cfl,output_root=tmp_path)
        stem=f"{case['name']}-N{n}-CFL{cfl}"
        final=tmp_path/(stem+'.npz');partial=tmp_path/(stem+'-partial.npz')
        for raw in (partial,final):
            assert raw.exists()
            metadata=json.loads(raw.with_suffix('.json').read_text())
            assert metadata['case']==case and metadata['N']==n and metadata['CFL']==cfl
            assert metadata['raw_sha256']==sha256(raw.read_bytes()).hexdigest()
        assert len(record['metrics'])==1 and record['steps']==[]
        assert record['result']=='EXECUTED_PENDING_ASSESSMENT'
        assert json.loads(partial.with_suffix('.json').read_text())['result']=='INCOMPLETE_NOT_ACCEPTANCE'
        if first is None:first=(final,sha256(final.read_bytes()).hexdigest())
        else:assert sha256(first[0].read_bytes()).hexdigest()==first[1]
    assert len(list(tmp_path.iterdir()))==8
    assert not (tmp_path/'window.npz').exists()
