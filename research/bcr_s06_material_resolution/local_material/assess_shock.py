"""Postprocess immutable directed runs: exact stage replay, no RHS evolution."""
from pathlib import Path
import argparse,hashlib,json,math,time
import numpy as np
from prototype import State
from fast_hybrid import FastHybridSolver
from run_controls import make_model
from shock_control import prepare

HERE=Path(__file__).resolve().parent


def compensated(rows):return np.array([math.fsum(column) for column in np.asarray(rows).T])


def assess(path,reference_root):
    start=time.perf_counter();record=json.loads(path.read_text());n=record['N']
    for name,digest in record['candidate_source_hashes'].items():
        source=HERE/name
        if name=='shock_control.py' and hashlib.sha256(source.read_bytes()).hexdigest()!=digest:
            source=HERE/'history/shock-N80/shock_control.py'
        assert hashlib.sha256(source.read_bytes()).hexdigest()==digest,name
    ref,binding=prepare(reference_root,n)
    assert binding['qualification_sha256']==record['qualification_sha256']
    solution=ref.solve(ref.Case(**record['parameters']))
    edges=np.array(record['initial_edges']);grid=edges.copy();I=np.array(record['initial_inventory'])
    labels=tuple('L' if x<.5 else 'R' for x in (edges[:-1]+edges[1:])/2)
    state=State(edges,I,labels);initial=state;solver=FastHybridSolver(make_model(),grid)
    window=np.linspace(0,1,n+1);scale=np.array(record['normalization'][:3]);unc=np.array(record['reference_uncertainty'][:3])
    max_speed=0.;max_record=None;stage_checks=0
    def check(state,phase,step):
        nonlocal max_speed,max_record,stage_checks
        w=solver.recover(state);values=abs(w[:,1])+w[:,3];maximum=float(np.max(values));stage_checks+=1
        assert maximum<=record['guard_speed'],(phase,step,maximum)
        if maximum>max_speed:max_speed=maximum;max_record={'phase':phase,'step':step,'interval':int(np.argmax(values))}
        return w
    def weights(state):
        return np.maximum(0.,np.minimum(window[1:,None],state.edges[None,1:])-np.maximum(window[:-1,None],state.edges[None,:-1]))/np.diff(window)[:,None]
    def window_inventory(state):
        overlap=np.maximum(0.,np.minimum(1.,state.edges[1:])-np.maximum(0.,state.edges[:-1]))
        return compensated(state.inventory*(overlap/np.diff(state.edges))[:,None])
    rows=[]
    def measure(state,t,j):
        w=solver.recover(state);candidate=weights(state)@w[:,:3]
        oracle=solution.cell_averages(window,t,order=32);exact=np.column_stack([oracle[x] for x in ('rho','u','p')])
        error=(candidate-exact)/scale
        rows.append({'sample':j,'time':t,'L1':np.mean(abs(error),axis=0).tolist(),
                     'L2':np.sqrt(np.mean(error**2,axis=0)).tolist(),'Linf':np.max(abs(error),axis=0).tolist(),
                     'L1_upper':(np.mean(abs(error),axis=0)+unc).tolist(),
                     'candidate':candidate.tolist(),'reference':exact.tolist()})
    check(state,'INITIAL',0);measure(state,0.,0)
    window0=window_inventory(initial);window_signed=np.zeros(12);window_abs=np.zeros(12)
    outer_signed=np.zeros(12);outer_abs=np.zeros(12);index=0;t=0.
    for j,sample in enumerate(record['history'],1):
        target=sample['t']
        while t<target:
            state=solver.reorganize(state);r=record['stages'][index];dt=r['dt']
            assert tuple(r['fixed_labels'])==state.labels
            f0=np.array(r['flux0']);f1=np.array(r['flux1']);v0=np.array(r['speed0']);v1=np.array(r['speed1'])
            check(state,'Y0',index)
            first=State(state.edges+dt*v0,state.inventory+dt*(f0[:-1]-f0[1:]),state.labels);check(first,'Y1',index)
            second=State(first.edges+dt*v1,first.inventory+dt*(f1[:-1]-f1[1:]),state.labels);check(second,'Y2',index)
            final=State(.5*state.edges+.5*second.edges,.5*state.inventory+.5*second.inventory,state.labels);check(final,'FINAL',index)
            for geometry,f in ((state.edges,f0),(first.edges,f1)):
                a=np.flatnonzero(geometry==0.);b=np.flatnonzero(geometry==1.)
                assert len(a)==len(b)==1,'Window cut is not an integration face in this control'
                fa,fb=f[int(a[0])],f[int(b[0])]
                window_signed+=.5*dt*(fa-fb);window_abs+=.5*dt*(abs(fa)+abs(fb))
                outer_signed+=.5*dt*(f[0]-f[-1]);outer_abs+=.5*dt*(abs(f[0])+abs(f[-1]))
            state=final;t=float(target) if dt==target-t else t+dt;index+=1
        assert state.edges.tobytes()==np.array(sample['edges']).tobytes()
        assert state.inventory.tobytes()==np.array(sample['inventory']).tobytes()
        measure(state,t,j)
        if j%25==0:print('N',n,'sample',j,'stage-checks',stage_checks,flush=True)
    assert index==record['steps'] and len(rows)==101
    ambient=record['ambient'];mass=ambient['rho']
    qref=mass*np.array([1.,ambient['a'],ambient['cv']*350.]+[1.]*9)
    winres=window_inventory(state)-window0-window_signed
    initial_overlap=np.maximum(0.,np.minimum(1.,initial.edges[1:])-np.maximum(0.,initial.edges[:-1]))
    winscale=compensated(abs(initial.inventory)*(initial_overlap/np.diff(initial.edges))[:,None])+window_abs+qref;winscale[3:]=winscale[0]
    outerres=compensated(state.inventory)-compensated(initial.inventory)-outer_signed
    outerscale=compensated(abs(initial.inventory))+outer_abs+qref*(grid[-1]-grid[0]);outerscale[3:]=outerscale[0]
    assert max(np.max(abs(winres)/winscale),np.max(abs(outerres)/outerscale))<1e-10
    output={'classification':'ALL101_PHYSICAL_METRICS_AND_EXACT_SELECTED_STAGE_AUDIT_NOT_FULL_VAL008_ACCEPTANCE',
            'N':n,'raw_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'sample_count':101,
            'bitwise_all_sample_replay':True,'stage_physical_checks':stage_checks,'causal_max_speed':max_speed,'causal_max_where':max_record,
            'outer_ST003':(abs(outerres)/outerscale).tolist(),'window_ST003':(abs(winres)/winscale).tolist(),
            'window_fluxes_observed_at_actual_integration_faces':True,'rows':rows,
            'time_max_L1_upper':np.max([r['L1_upper'] for r in rows],axis=0).tolist(),
            'time_max_L2':np.max([r['L2'] for r in rows],axis=0).tolist(),
            'time_max_Linf':np.max([r['Linf'] for r in rows],axis=0).tolist(),
            'elapsed_seconds':time.perf_counter()-start,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'qualification_sha256':binding['qualification_sha256']}
    (HERE/f'shock-N{n}-assessment.json').write_text(json.dumps(output)+'\n')
    print(json.dumps({k:output[k] for k in ('N','stage_physical_checks','causal_max_speed','time_max_L1_upper','elapsed_seconds')}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--reference-root',type=Path,required=True);a=p.parse_args();assess(a.raw,a.reference_root)
