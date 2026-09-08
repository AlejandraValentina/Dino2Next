"""All selected stages and physical exterior errors, reconstructed without RHS."""
from pathlib import Path
import hashlib,json,math,time
import numpy as np
from fast_hybrid import FastHybridSolver
from prototype import State
from run_controls import make_model

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]


def sums(rows):return np.array([math.fsum(x) for x in np.asarray(rows).T])


def audit():
    summary=json.loads((HERE/'fast-contacts-summary.json').read_text())
    assert summary['completed']==summary['required']==9
    results=[];start=time.perf_counter()
    for item in summary['cases']:
        path=HERE/item['raw_file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==item['raw_sha256']
        r=json.loads(path.read_text())
        for name,digest in r['source_sha256'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
        grid=np.linspace(-.5,1.5,25);edges=np.array(r['initial_edges']);q=np.array(r['initial_inventory']);x=r['physical_initial']['interface']
        labels=tuple('L' if v<x else 'R' for v in (edges[:-1]+edges[1:])/2)
        state=State(edges,q,labels);initial=state;solver=FastHybridSolver(make_model(),grid)
        maxp=maxu=outsidep=maxspeed=gcl=0.;count=0
        outer=np.zeros(12);outer_abs=np.zeros(12);window=np.zeros(12);window_abs=np.zeros(12)
        def observe(stage):
            nonlocal maxp,maxu,outsidep,maxspeed,count
            w=solver.recover(stage);i=solver.interfaces(stage)[0];outside=np.ones(len(w),bool);outside[i-1:i+1]=False
            maxp=max(maxp,float(np.max(abs(w[:,2]-1e5))));maxu=max(maxu,float(np.max(abs(w[:,1]-r['velocity']))))
            outsidep=max(outsidep,float(np.max(abs(w[outside,2]-1e5))))
            maxspeed=max(maxspeed,float(np.max(abs(w[:,1])+w[:,3])));count+=1
            assert maxspeed<=1293
        def cut_inventory(stage,absolute=False):
            fraction=np.maximum(0.,np.minimum(1.,stage.edges[1:])-np.maximum(0.,stage.edges[:-1]))/np.diff(stage.edges)
            values=abs(stage.inventory) if absolute else stage.inventory
            return sums(values*fraction[:,None])
        observe(state)
        for i,(stage_record,sample) in enumerate(zip(r['stages'],r['history'],strict=True)):
            prepared=solver.reorganize(state);dt=stage_record['dt'];f0=np.array(stage_record['flux0']);f1=np.array(stage_record['flux1']);v0=np.array(stage_record['speed0']);v1=np.array(stage_record['speed1'])
            first=State(prepared.edges+dt*v0,prepared.inventory+dt*(f0[:-1]-f0[1:]),prepared.labels)
            second=State(first.edges+dt*v1,first.inventory+dt*(f1[:-1]-f1[1:]),prepared.labels)
            state=State(.5*prepared.edges+.5*second.edges,.5*prepared.inventory+.5*second.inventory,prepared.labels)
            assert state.edges.tobytes()==np.array(sample['edges']).tobytes()
            assert state.inventory.tobytes()==np.array(sample['inventory']).tobytes()
            for stage in (prepared,first,second,state):observe(stage)
            gcl=max(gcl,float(np.max(abs(np.diff(state.edges)-np.diff(prepared.edges)-.5*dt*(np.diff(v0)+np.diff(v1))))))
            for geometry,flux,stage in ((prepared.edges,f0,prepared),(first.edges,f1,first)):
                interface=solver.interfaces(stage)[0]
                assert np.array_equal(flux[interface,[0,*range(3,12)]],np.zeros(10))
                a=np.flatnonzero(geometry==0.);b=np.flatnonzero(geometry==1.);assert len(a)==len(b)==1
                fa,fb=flux[int(a[0])],flux[int(b[0])]
                window+=.5*dt*(fa-fb);window_abs+=.5*dt*(abs(fa)+abs(fb))
                outer+=.5*dt*(flux[0]-flux[-1]);outer_abs+=.5*dt*(abs(flux[0])+abs(flux[-1]))
        winres=cut_inventory(state)-cut_inventory(initial)-window
        winscale=cut_inventory(initial,True)+window_abs+np.array(r['Qref'])/2;winscale[3:]=winscale[0]
        outres=sums(state.inventory)-sums(initial.inventory)-outer
        outscale=sums(abs(initial.inventory))+outer_abs+np.array(r['Qref']);outscale[3:]=outscale[0]
        assert max(np.max(abs(winres)/winscale),np.max(abs(outres)/outscale))<1e-10
        result={'pair':r['pair'],'velocity':r['velocity'],'bitwise_every_accepted_state_replay':True,
                'selected_physical_states_checked':count,'all_stage_max_pressure_error_Pa':maxp,
                'all_stage_exterior_pressure_error_Pa':outsidep,'all_stage_max_velocity_error':maxu,
                'all_stage_max_characteristic_speed':maxspeed,'GCL_max_m':gcl,
                'material_face_mass_species_origin_flux_exact_zero':True,
                'outer_ST003':(abs(outres)/outscale).tolist(),'window_ST003':(abs(winres)/winscale).tolist(),
                'raw_sha256':item['raw_sha256']}
        results.append(result);print(r['pair'],r['velocity'],count,maxp,outsidep,flush=True)
    output={'classification':'AUTHOR_NO_EVOLUTION_ALL_SELECTED_STATE_AND_LEDGER_AUDIT_NOT_FULL_VAL008_ACCEPTANCE',
            'cases':results,'completed':9,'elapsed_seconds':time.perf_counter()-start,
            'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'raw_summary_sha256':hashlib.sha256((HERE/'fast-contacts-summary.json').read_bytes()).hexdigest()}
    (HERE/'fast-contacts-audit.json').write_text(json.dumps(output,indent=2)+'\n')


if __name__=='__main__':audit()
