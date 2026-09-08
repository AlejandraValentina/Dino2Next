"""Bounded author demonstration; no reference trajectories enter the solver."""
from pathlib import Path
import importlib.util
import hashlib
import json
import time
import numpy as np
from prototype import LocalSolver

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
from dino2next.thermo import ThermoModel,ThermoDataset,DERIVED_SHA256,RAW_SHA256,TRANSPORT_SHA256,GENERATOR_SHA256

def make_model():
    p=ROOT/'docs/science/C1.0/datasets'
    return ThermoModel(ThermoDataset.from_files(p/'thermo_runtime_continuous_v1.json',p/'thermo_species.json',p/'thermo_transport.yaml',ROOT/'research/bcr_s03_nasa_inversion/generate.py',expected_sha256=DERIVED_SHA256,expected_raw_sha256=RAW_SHA256,expected_transport_sha256=TRANSPORT_SHA256,expected_generator_sha256=GENERATOR_SHA256))


def run():
    model = make_model()
    raw = json.loads((ROOT/'docs/science/C1.0/datasets/thermo_species.json').read_text())
    mw = np.array([s['MW_kg_kmol'] for s in raw['species'][:5]])
    def mix(moles):
        x = mw*np.array(moles); return tuple(map(float,x/x.sum()))
    pairs = [((0,0,1,0,0),(0,0,0,1,0),600.,600.),
             ((0,0,1,0,0),(0,0,0,1,0),600.,1800.),
             (mix([1,12.5/.7,47/.7,0,0]),mix([0,12.5/.7-12.5,47/.7,8,9]),400.,1800.)]
    reports = []
    for pair, (yl, yr, tl, tr) in enumerate(pairs):
        for velocity in (0.,100.,-100.):
            grid = np.linspace(-.5,1.5,25)
            solver = LocalSolver(model, grid)
            # Deliberately tiny geometric cut next to a base face; removed by
            # same-region agglomeration, not removal of the material interface.
            interface = .5+1e-10
            edges = np.sort(np.r_[grid,interface])
            centers = .5*(edges[:-1]+edges[1:])
            physical = [(tl if x<interface else tr,1e5,velocity,yl if x<interface else yr,
                         (1,0,0,0) if x<interface else (0,0,1,0)) for x in centers]
            state = solver.initialize(edges,physical,tuple('left' if x<interface else 'right' for x in centers))
            initial = state
            initial_sum = np.sum(initial.inventory,axis=0)
            initial_abs = np.sum(abs(initial.inventory),axis=0)
            initial_w = solver.recover(initial)
            # Physical, nonzero inventory scales; formation energy is retained
            # in I and its ledger. a_ref derives from initial accepted EOS.
            ambient = model.evaluate(350.,1e5,mix([0,1,3.76,0,0]))
            mass_ref = ambient.rho*(grid[-1]-grid[0])
            reference_scale = np.array([mass_ref,mass_ref*ambient.a,mass_ref*ambient.cv*350.]+[mass_ref]*9)
            t = 0.; signed = np.zeros(12); throughput = np.zeros(12)
            maxp=maxu=0.; steps=0; crossings=[]; last_cell=int(np.searchsorted(grid,interface))
            start = time.perf_counter(); min_width=1.; exterior_p=0.
            while t<.001:
                state, flux, dt, failures = solver.advance(state,.001-t)
                assert not failures, failures
                signed += flux[0]-flux[-1]
                # Stage-resolved absolute exterior throughput, not abs of net.
                rec=solver.stage_records[-1]
                for f in (np.array(rec['flux0']),np.array(rec['flux1'])):
                    throughput += .5*dt*(abs(f[0])+abs(f[-1]))
                t += dt; steps += 1
                w=solver.recover(state); maxp=max(maxp,float(np.max(abs(w[:,2]-1e5))))
                maxu=max(maxu,float(np.max(abs(w[:,1]-velocity))))
                ids=solver.interfaces(state); pos=float(state.edges[ids[0]])
                outside=np.ones(len(w),bool);outside[max(0,ids[0]-1):ids[0]+1]=False
                exterior_p=max(exterior_p,float(np.max(abs(w[outside,2]-1e5))))
                cell=int(np.searchsorted(grid,pos));
                if cell!=last_cell:crossings.append((steps,t,pos,last_cell,cell));last_cell=cell
                min_width=min(min_width,float(np.min(np.diff(state.edges))))
            residual=np.sum(state.inventory,axis=0)-initial_sum-signed
            scale=initial_abs+throughput+reference_scale
            # All constituent residuals use total-mass inventory/throughput.
            scale[3:]=scale[0]
            assert np.max(abs(residual)/scale)<1e-10
            name=f'contact-{pair}-{velocity:g}'
            evidence={'initial_edges':initial.edges.tolist(),'initial_inventory':initial.inventory.tolist(),
                      'final_edges':state.edges.tolist(),'final_inventory':state.inventory.tolist(),
                      'final_labels':state.labels,'stages':solver.stage_records,'remaps':solver.remap_records}
            path=HERE/(name+'.json');path.write_text(json.dumps(evidence)+'\n')
            reports.append({'case':name,'pair':pair,'velocity':velocity,'steps':steps,
                            'elapsed_seconds':time.perf_counter()-start,'max_pressure_error_Pa':maxp,
                            'exterior_pressure_error_Pa':exterior_p,'max_velocity_error':maxu,
                            'min_evolved_width':min_width,'crossings':crossings,'remaps':len(solver.remap_records),
                            'residual':residual.tolist(),'absolute_throughput':throughput.tolist(),
                            'ambient_reference':{'T':350.,'p':1e5,'rho':ambient.rho,'cv':ambient.cv,'a':ambient.a,'air_mole_ratio':'O2:N2=1:3.76'},'reference_scale':reference_scale.tolist(),'normalizer':scale.tolist(),
                            'ST003_normalized':(abs(residual)/scale).tolist(),
                            'max_GCL_m':max(r['max_GCL_absolute_m'] for r in solver.stage_records),
                            'raw_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
            print(name,steps,maxp,exterior_p,'seconds',reports[-1]['elapsed_seconds'],flush=True)
            write(reports)
    return reports


def write(reports):
    paths=[HERE/'prototype.py',Path(__file__),HERE.parent/'material/prototype.py',HERE.parent/'material/run_controls.py',
           ROOT/'src/dino2next/thermo/__init__.py',ROOT/'docs/science/C1.0/datasets/thermo_runtime_continuous_v1.json',
           ROOT/'docs/science/C1.0/datasets/thermo_species.json']
    result={'classification':'LOCAL_ALE_AUTHOR_CONTACT_DEMONSTRATION_NOT_VAL008_ACCEPTANCE','cases':reports,
            'completed_contacts':len(reports),'required_contacts':9,
            'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    (HERE/'control-results.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':run()
