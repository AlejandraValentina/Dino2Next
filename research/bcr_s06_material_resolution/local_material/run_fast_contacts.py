"""All nine physical contacts in the small hybrid prototype, not fixture gates."""
from pathlib import Path
import hashlib,json,time
import numpy as np
from fast_hybrid import FastHybridSolver
from prototype import State
from run_controls import make_model

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]


def main():
    model=make_model();raw=json.loads((ROOT/'docs/science/C1.0/datasets/thermo_species.json').read_text())
    mw=np.array([x['MW_kg_kmol'] for x in raw['species'][:5]])
    def mix(moles):
        x=mw*np.array(moles);return tuple(map(float,x/x.sum()))
    pairs=[((0.,0.,1.,0.,0.),(0.,0.,0.,1.,0.),600.,600.),
           ((0.,0.,1.,0.,0.),(0.,0.,0.,1.,0.),600.,1800.),
           (mix([1,12.5/.7,47/.7,0,0]),mix([0,12.5/.7-12.5,47/.7,8,9]),400.,1800.)]
    summary=[]
    for pair,(yl,yr,tl,tr) in enumerate(pairs):
        for velocity in (0.,100.,-100.):
            grid=np.linspace(-.5,1.5,25);solver=FastHybridSolver(model,grid)
            x=.5+1e-10;edges=np.sort(np.r_[grid,x]);centers=(edges[:-1]+edges[1:])/2
            rows=[(tl if v<x else tr,1e5,velocity,yl if v<x else yr,
                   (1.,0.,0.,0.) if v<x else (0.,0.,1.,0.)) for v in centers]
            state=solver.initialize(edges,rows,tuple('L' if v<x else 'R' for v in centers));initial=state
            ambient=model.evaluate(350.,1e5,mix([0,1,3.76,0,0]));massref=2*ambient.rho
            qref=massref*np.array([1.,ambient.a,ambient.cv*350.]+[1.]*9)
            signed=np.zeros(12);throughput=np.zeros(12);t=0.;history=[];start=time.perf_counter()
            maxp=maxu=exteriorp=maxspeed=0.;physical_checks=0;crossings=[];lastcell=int(np.searchsorted(grid,x))
            while t<.001:
                # Deterministic geometry-only preparation for audit. Advance
                # repeats that exact remap from the same immutable state.
                prepared=solver.reorganize(state)
                state,flux,dt,failures=solver.advance(state,.001-t)
                assert not failures,failures
                r=solver.stage_records[-1];f0=np.array(r['flux0']);f1=np.array(r['flux1']);v0=np.array(r['speed0']);v1=np.array(r['speed1'])
                first=State(prepared.edges+dt*v0,prepared.inventory+dt*(f0[:-1]-f0[1:]),prepared.labels)
                second=State(first.edges+dt*v1,first.inventory+dt*(f1[:-1]-f1[1:]),prepared.labels)
                for stage in (prepared,first,second,state):
                    w=solver.recover(stage);maxspeed=max(maxspeed,float(np.max(abs(w[:,1])+w[:,3])));physical_checks+=1
                assert maxspeed<=1293
                signed+=flux[0]-flux[-1]
                throughput+=.5*dt*(abs(f0[0])+abs(f0[-1])+abs(f1[0])+abs(f1[-1]))
                t+=dt;w=solver.recover(state);i=solver.interfaces(state)[0]
                p_error=float(np.max(abs(w[:,2]-1e5)));u_error=float(np.max(abs(w[:,1]-velocity)))
                outside=np.ones(len(w),bool);outside[i-1:i+1]=False
                outside_error=float(np.max(abs(w[outside,2]-1e5)))
                maxp=max(maxp,p_error);maxu=max(maxu,u_error);exteriorp=max(exteriorp,outside_error)
                cell=int(np.searchsorted(grid,state.edges[i]))
                if cell!=lastcell:crossings.append((len(history)+1,t,float(state.edges[i]),lastcell,cell));lastcell=cell
                history.append({'time':t,'edges':state.edges.tolist(),'inventory':state.inventory.tolist(),'labels':state.labels,
                    'max_pressure_error_Pa':p_error,'exterior_pressure_error_Pa':outside_error,'max_velocity_error':u_error})
            residual=np.sum(state.inventory,axis=0)-np.sum(initial.inventory,axis=0)-signed
            scale=np.sum(abs(initial.inventory),axis=0)+throughput+qref;scale[3:]=scale[0]
            assert max(abs(residual)/scale)<1e-10
            name=f'fast-contact-{pair}-{velocity:g}'
            report={'classification':'ALL_COMPOSITION_SMALL_HYBRID_CONTACT_CONTROL_NOT_FULL_VAL008_ACCEPTANCE',
                'pair':pair,'velocity':velocity,'physical_initial':{'Tleft':tl,'Tright':tr,'p':1e5,'Yleft':yl,'Yright':yr,'interface':x},
                'domain_note':'Same 24-cell prototype domain [-.5,1.5]; not the SV008 guarded original fixture geometry.',
                'elapsed_seconds':time.perf_counter()-start,'steps':len(history),'physical_stage_checks':physical_checks,
                'max_characteristic_speed':maxspeed,'max_pressure_error_Pa':maxp,'max_velocity_error':maxu,
                'exterior_pressure_error_Pa':exteriorp,'crossings':crossings,'history':history,
                'initial_edges':initial.edges.tolist(),'initial_inventory':initial.inventory.tolist(),
                'ST003_residual':residual.tolist(),'ST003_normalizer':scale.tolist(),'ST003_normalized':(abs(residual)/scale).tolist(),
                'absolute_throughput':throughput.tolist(),'Qref':qref.tolist(),
                'ambient':{'T':350.,'p':1e5,'air_mole_ratio':'O2:N2=1:3.76','rho':ambient.rho,'cv':ambient.cv,'a':ambient.a},
                'stages':solver.stage_records,'hybrid':solver.hybrid_records,'guard_candidates':solver.guard_records,
                'transactions':solver.transaction_records,'remaps':solver.remap_records,
                'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
                     [Path(__file__),HERE/'fast_hybrid.py',HERE/'fast_overlap.py',HERE/'hybrid.py',HERE/'prototype.py',
                      HERE.parent/'material/prototype.py',HERE/'kernel_source.py',ROOT/'src/dino2next/thermo/__init__.py',
                      ROOT/'docs/science/C1.0/datasets/thermo_runtime_continuous_v1.json',ROOT/'docs/science/C1.0/datasets/thermo_species.json']}}
            path=HERE/(name+'.json');path.write_text(json.dumps(report)+'\n')
            summary.append({k:report[k] for k in ('pair','velocity','elapsed_seconds','steps','physical_stage_checks','max_characteristic_speed','max_pressure_error_Pa','exterior_pressure_error_Pa','max_velocity_error','ST003_normalized','crossings')})
            summary[-1].update(raw_file=path.name,raw_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            (HERE/'fast-contacts-summary.json').write_text(json.dumps({'classification':'PROTOTYPE_CONTACT_COVERAGE_NOT_FULL_VAL008_ACCEPTANCE','completed':len(summary),'required':9,'cases':summary},indent=2)+'\n')
            print(name,len(history),maxp,exteriorp,summary[-1]['elapsed_seconds'],flush=True)


if __name__=='__main__':main()
