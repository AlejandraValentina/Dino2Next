"""Predefined directed shock-pair0-ratio2 N80; qualified existing NASA oracle.

Default is preparation only. --execute is used only after function/guard review.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,math,sys,time
import numpy as np
from fast_hybrid import FastHybridSolver as HybridSolver
from run_controls import make_model

HERE=Path(__file__).resolve().parent


def prepare(root,n=80):
    certpath=root/'validation/references/VAL-008/qualification.json'
    certificate=json.loads(certpath.read_text())
    assert certificate['status']=='REFERENCE_QUALIFIED' and certificate['candidate_imports'] is False
    for path,digest in certificate['source_hashes'].items():
        assert hashlib.sha256((root/path).read_bytes()).hexdigest()==digest,path
    parameters={'pair':0,'velocity':0.,'pressure_ratio':2.}
    record=next(r for r in certificate['cases'] if r['parameters']==parameters)
    assert record['status']=='PASS'
    path=root/'validation/references/VAL-008/reference.py'
    assert hashlib.sha256(path.read_bytes()).hexdigest()==certificate['reference_sha256']
    spec=importlib.util.spec_from_file_location('qualified_existing_NASA008',path)
    ref=importlib.util.module_from_spec(spec);sys.modules[spec.name]=ref;spec.loader.exec_module(ref)
    metadata={'classification':'DIRECTED_HYBRID_SHOCK_PREPARATION_NOT_EXECUTED','parameters':parameters,
              'N':n,'CFL':.2,'end_time':.0002,'guard_speed':2544,'reference_imports_candidate':False,
              'qualification_sha256':hashlib.sha256(certpath.read_bytes()).hexdigest(),
              'reference_source_sha256':certificate['reference_sha256'],
              'source_hashes':certificate['source_hashes'],'reference_uncertainty':record['total_normalized_reference_bound'],
              'normalization':record['normalization'],
              'candidate_source_hashes':{name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in ('shock_control.py','fast_hybrid.py','fast_overlap.py','hybrid.py','prototype.py','kernel_source.py','../material/prototype.py')}}
    return ref,metadata


def execute(ref,metadata):
    n=metadata['N'];end=.0002;m=math.ceil(n*2544*end)+4
    edges=np.arange(-m,n+m+1,dtype=float)/n
    solver=HybridSolver(make_model(),edges)
    # Original physical initial data, not a later oracle interface trajectory.
    centers=(edges[:-1]+edges[1:])/2
    rows=[(700.,200000. if x<.5 else 100000.,0.,
           (0.,0.,1.,0.,0.) if x<.5 else (0.,0.,0.,1.,0.),(0.,0.,1.,0.)) for x in centers]
    state=solver.initialize(edges,rows,tuple('L' if x<.5 else 'R' for x in centers));initial=state
    t=0.;history=[];ledger=np.zeros(12);throughput=np.zeros(12);start=time.perf_counter()
    for target in np.linspace(0,end,101)[1:]:
        while t<target:
            try:
                state,flux,dt,failures=solver.advance(state,float(target-t))
            except Exception as exc:
                failure=dict(metadata,classification='DIRECTED_SHOCK_EXECUTION_FAILED_NOT_PASS',time=t,error=repr(exc),history=history,latest_edges=state.edges.tolist(),latest_inventory=state.inventory.tolist(),stages=solver.stage_records,guard_candidates=solver.guard_records,transactions=solver.transaction_records)
                (HERE/'shock-failure.json').write_text(json.dumps(failure)+'\n')
                raise
            ledger+=flux[0]-flux[-1]
            for f in (np.array(solver.stage_records[-1]['flux0']),np.array(solver.stage_records[-1]['flux1'])):
                throughput+=.5*dt*(abs(f[0])+abs(f[-1]))
            t=float(target) if dt==target-t else t+dt
        history.append({'t':t,'edges':state.edges.tolist(),'inventory':state.inventory.tolist(),'labels':state.labels})
        (HERE/'shock-progress.json').write_text(json.dumps({'classification':'RUNNING_NOT_PASS','time':t,'accepted_samples':len(history),'steps':len(solver.stage_records),'latest':history[-1]})+'\n')
    solution=ref.solve(ref.Case(**metadata['parameters']))
    window=np.linspace(0,1,n+1);oracle=solution.cell_averages(window,end,order=32)
    primitive=solver.recover(state);candidate=np.zeros((n,3))
    for j,(left,right) in enumerate(zip(window[:-1],window[1:])):
        for i,(a,b) in enumerate(zip(state.edges[:-1],state.edges[1:])):
            overlap=max(0.,min(right,b)-max(left,a))
            candidate[j]+=overlap*primitive[i,:3]/(right-left)
    exact=np.column_stack([oracle[x] for x in ('rho','u','p')]);normalization=np.array(metadata['normalization'][:3])
    error=(candidate-exact)/normalization
    ambient=solver.model.evaluate(350.,1e5,(0.,.232,.768,0.,0.))
    massref=ambient.rho*(edges[-1]-edges[0])
    qref=massref*np.array([1.,ambient.a,ambient.cv*350.]+[1.]*9)
    residual=np.sum(state.inventory,axis=0)-np.sum(initial.inventory,axis=0)-ledger
    scale=np.sum(abs(initial.inventory),axis=0)+throughput+qref;scale[3:]=scale[0]
    assert np.max(abs(residual)/scale)<1e-10
    metadata.update(classification='DIRECTED_HYBRID_SHOCK_RESULT_NOT_FULL_VAL008_ACCEPTANCE',
        elapsed_seconds=time.perf_counter()-start,steps=len(solver.stage_records),sample_count=101,
        candidate_final=candidate.tolist(),reference_final=exact.tolist(),
        final_L1=np.mean(abs(error),axis=0).tolist(),final_L2=np.sqrt(np.mean(error**2,axis=0)).tolist(),
        final_Linf=np.max(abs(error),axis=0).tolist(),history=history,
        initial_edges=initial.edges.tolist(),initial_inventory=initial.inventory.tolist(),
        raw_inventory_residual=(np.sum(state.inventory,axis=0)-np.sum(initial.inventory,axis=0)-ledger).tolist(),
        absolute_throughput=throughput.tolist(),ST003_normalizer=scale.tolist(),ST003_normalized=(abs(residual)/scale).tolist(),
        Qref=qref.tolist(),ambient={'T':350.,'p':1e5,'Y':[0.,.232,.768,0.,0.],'rho':ambient.rho,'a':ambient.a,'cv':ambient.cv},stages=solver.stage_records,hybrid=solver.hybrid_records,
        guard_candidates=solver.guard_records,transactions=solver.transaction_records)
    return metadata


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--reference-root',type=Path,required=True);parser.add_argument('--execute',action='store_true');parser.add_argument('--mesh',type=int,choices=(80,160),default=80)
    args=parser.parse_args();ref,metadata=prepare(args.reference_root,args.mesh)
    if args.execute:metadata=execute(ref,metadata)
    output=f'shock-N{args.mesh}-result.json' if args.execute else f'shock-N{args.mesh}-preparation.json'
    (HERE/output).write_text(json.dumps(metadata)+'\n')
    print(metadata['classification'])
