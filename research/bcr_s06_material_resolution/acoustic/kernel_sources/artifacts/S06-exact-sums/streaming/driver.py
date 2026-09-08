"""Experimental storage-only canonical driver. No long run on import."""
from pathlib import Path
from hashlib import sha256
import gzip,importlib.util,inspect,json,sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CANONICAL=ROOT/'validation/fixtures/VAL-006/canonical_execution.py'

def digest(path):
    h=sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
    return h.hexdigest()

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

class Sink:
    def __init__(self,path):
        self.path=Path(path);self.file=self.path.open('wb')
        self.gz=gzip.GzipFile(filename='',mode='wb',fileobj=self.file,compresslevel=1,mtime=0)
        self.count=0;self.closed=False;self.plain=sha256()
    def append(self,row):
        encoded=(json.dumps(row,separators=(',',':'),allow_nan=False)+'\n').encode()
        self.gz.write(encoded);self.plain.update(encoded);self.count+=1
    def close(self):
        if not self.closed:self.gz.close();self.file.close();self.closed=True
    def manifest(self):
        self.close()
        return dict(format='gzip JSONL',file=self.path.name,count=self.count,
                    sha256=digest(self.path),uncompressed_sha256=self.plain.hexdigest(),
                    bytes=self.path.stat().st_size)

def events(directory,manifest):
    path=Path(directory)/manifest['file']
    assert digest(path)==manifest['sha256']
    plain=sha256();count=0
    with gzip.open(path,'rb') as f:
        for line in f:
            plain.update(line);count+=1;yield json.loads(line)
    assert count==manifest['count'] and plain.hexdigest()==manifest['uncompressed_sha256']

def execute(fixture_id,n,case,cfl,*,output_root):
    out=Path(output_root);out.mkdir(parents=True,exist_ok=True)
    stem=f"{case['name']}-N{n}-CFL{cfl}"
    sinks={kind:Sink(out/(stem+'-'+kind+'.jsonl.gz')) for kind in ('steps','rejections','limiters')}
    pinned={p:digest(p) for p in (Path(__file__),CANONICAL,
        ROOT/'src/dino2next/numerics/__init__.py',
        ROOT/f'validation/references/{fixture_id}/reference.py',
        ROOT/f'validation/fixtures/{fixture_id}/input.json',CANONICAL.with_name('gamma_adapter.py'))}
    d=load('stream_canonical',CANONICAL)
    original=inspect.getsource(d.execute)
    # Storage substitutions only. The arithmetic statements, 101-target loop,
    # retry logic and compensated ledger terms remain the original source.
    replacements={
        "failure = ROOT/'artifacts'/fixture_id/":"failure = Path(output_root)/",
        'rhs = CanonicalRHS(k, fixture_id, case, reference)':
            "rhs = CanonicalRHS(k, fixture_id, case, reference)\n    rhs.limiter_records = STREAM_SINKS['limiters']",
        'samples, times, steps, rejected, metrics = [state.Q.copy()], [0.], [], [], []':
            "samples, times, steps, rejected, metrics = [state.Q.copy()], [0.], STREAM_SINKS['steps'], STREAM_SINKS['rejections'], []",
        'time=time, attempts=rejected)':"time=time, attempts=rejected.manifest())",
        'metrics=metrics, steps=steps, rejections=rejected, limiter_records=rhs.limiter_records,':
            'metrics=metrics, steps=steps.manifest(), rejections=rejected.manifest(), limiter_records=rhs.limiter_records.manifest(),',
        "source_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),":
            "source_sha256=STREAM_SOURCE_HASH, canonical_source_sha256=sha256(Path(__file__).read_bytes()).hexdigest(), storage='STREAMED_TRACES_EXPERIMENTAL',",
    }
    try:
        for a,b in replacements.items():
            assert original.count(a)==1,a
            original=original.replace(a,b)
        d.__dict__.update(STREAM_SINKS=sinks,STREAM_SOURCE_HASH=digest(Path(__file__)))
        exec(compile(original,str(HERE/'storage_adapted_execute.py'),'exec'),d.__dict__)
        # Preserve reproducible generated source and exact input source binding.
        (out/(stem+'-storage-adapted.py')).write_text(original)
        result=d.execute(fixture_id,n,case,cfl,output_root=out)
        assert all(digest(p)==value for p,value in pinned.items()),'EXECUTION_SOURCE_CHANGED'
        return result
    except BaseException as exc:
        manifests={k:v.manifest() for k,v in sinks.items()}
        (out/(stem+'-interrupted.json')).write_text(json.dumps(dict(
            result='INTERRUPTED_INCOMPLETE' if isinstance(exc,KeyboardInterrupt) else 'EXECUTION_FAILED',
            reason=repr(exc),traces=manifests,source_sha256=digest(Path(__file__)),
            canonical_source_sha256=digest(CANONICAL)),indent=2)+'\n')
        raise
    finally:
        for sink in sinks.values():sink.close()

def assess_n1600(record,directory,observation_path):
    """Original operators + independently qualified MR observation, all samples."""
    import numpy as np
    assert record['N']==1600 and record['case']['kind']=='free'
    assert record['case']['epsilon'] in (1e-5,5e-6)
    observation_path=Path(observation_path)
    observation=load('qualified_mr_observation',observation_path)
    assessment=load('stream_assessment',ROOT/'validation/fixtures/VAL-006/assessment.py')
    d=load('assessment_canonical',CANONICAL)
    k,_,ref=d.setup('VAL-010',1600,record['case'])
    raw=Path(directory)/f"{record['case']['name']}-N1600-CFL{record['CFL']}.npz"
    assert digest(raw)==record['raw_sha256']
    data=np.load(raw);times=data['times'];Q=data['Q'];bounds=data['cell_bounds']
    assert times.shape==(101,) and Q.shape==(101,1600,12)
    assert np.array_equal(times,np.linspace(0,record['case']['time'],101))
    rows=[]
    for j,t in enumerate(times):
        certified=observation.observation_reference(1600,j,record['case']['epsilon'])
        primitive=k.recover(Q[j]).V
        rows.append(assessment.assess_reflection_sample(ref,bounds,primitive,certified,1600,float(t),j))
    for field in ('steps','rejections','limiter_records'):
        # Fully read/hash-check even an empty stream; never silently omit guards.
        for _ in events(directory,record[field]):pass
    return dict(classification='EXPERIMENTAL_N1600_OBSERVATION_NOT_R4_ACCEPTANCE',samples=rows,
        all_observation_gates_satisfied=all(row['passed'] for row in rows),
        ledger_max=max(abs(v) for row in record['metrics'] for v in row['ledger']),
        observation_sha256=digest(observation_path),
        qualification_sha256=digest(observation_path.with_name('free_observation_qualification.json')),
        assessment_sha256=digest(ROOT/'validation/fixtures/VAL-006/assessment.py'))
