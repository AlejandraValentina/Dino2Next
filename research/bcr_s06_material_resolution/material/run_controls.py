"""Bounded research controls, explicitly not the complete VAL-008 adapter."""
from pathlib import Path
from hashlib import sha256
from time import perf_counter
import json
import numpy as np
from prototype import RegionSolver
from dino2next.thermo import (ThermoModel,ThermoDataset,DERIVED_SHA256,
                             RAW_SHA256,TRANSPORT_SHA256,GENERATOR_SHA256)

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]

def model():
    p=ROOT/'docs/science/C1.0/datasets'
    return ThermoModel(ThermoDataset.from_files(p/'thermo_runtime_continuous_v1.json',
        p/'thermo_species.json',p/'thermo_transport.yaml',
        ROOT/'research/bcr_s03_nasa_inversion/generate.py',
        expected_sha256=DERIVED_SHA256,expected_raw_sha256=RAW_SHA256,
        expected_transport_sha256=TRANSPORT_SHA256,expected_generator_sha256=GENERATOR_SHA256))

def run():
    m=model();raw=json.loads((ROOT/'docs/science/C1.0/datasets/thermo_species.json').read_text())
    mw=np.array([s['MW_kg_kmol'] for s in raw['species'][:5]])
    def mixture(n):
        z=np.array(n)*mw;return tuple(map(float,z/np.sum(z)))
    n2=(0.,0.,1.,0.,0.);co2=(0.,0.,0.,1.,0.)
    premix=mixture([1,12.5/.7,47/.7,0,0]);products=mixture([0,12.5/.7-12.5,47/.7,8,9])
    pairs=[(n2,co2,600.,600.),(n2,co2,600.,1800.),(premix,products,400.,1800.)]
    records=[]
    for pair,(yl,yr,tl,tr) in enumerate(pairs):
        for u in (0.,100.,-100.):
            solver=RegionSolver(m);edges=np.linspace(-.5,1.5,25)
            physical=[(tl if x<.5 else tr,1e5,u,yl if x<.5 else yr,(0,0,1,0)) for x in (edges[:-1]+edges[1:])/2]
            state=solver.initialize(edges,physical,tuple('L' if x<.5 else 'R' for x in (edges[:-1]+edges[1:])/2))
            initial=state;start=perf_counter();t=0.;steps=0;ledger=np.zeros(12);maxp=maxu=0.
            history_q=[state.inventory];history_x=[state.edges];history_t=[0.]
            while t<.001:
                dt=min(solver.suggested_dt(state),.001-t)
                state,flux=solver.step(state,dt);ledger+=flux[0]-flux[-1];t+=dt;steps+=1
                history_q.append(state.inventory);history_x.append(state.edges);history_t.append(t)
                w=solver.recover(state);maxp=max(maxp,float(np.max(abs(w[:,2]-1e5))));maxu=max(maxu,float(np.max(abs(w[:,1]-u))))
            total=state.inventory.sum(axis=0)-initial.inventory.sum(axis=0)-ledger
            scale=np.maximum(np.sum(abs(initial.inventory),axis=0),1.)
            sampled,p,pieces=solver.sample(state,np.linspace(0,1,13))
            rawfile=HERE/f'contact-{pair}-{u:g}.npz'
            np.savez_compressed(rawfile,times=history_t,inventory=history_q,edges=history_x,ledger=ledger)
            diagfile=HERE/f'contact-{pair}-{u:g}-diagnostics.json'
            diagfile.write_text(json.dumps(solver.records,indent=2)+'\n')
            records.append(dict(kind='CONTACT',pair=pair,u=u,steps=steps,elapsed=perf_counter()-start,
                max_pressure_error_Pa=maxp,max_velocity_error=maxu,ledger_normalized=(abs(total)/scale).tolist(),
                sampled_pressure_error_Pa=float(np.max(abs(p-1e5))),pieces=len(pieces),
                material_interface_position=float(state.edges[12]),expected_position_diagnostic=.5+u*t,
                initial_sha256=sha256(initial.inventory.tobytes()).hexdigest(),cache=solver._invert.cache_info()._asdict(),
                raw_sha256=sha256(rawfile.read_bytes()).hexdigest(),
                diagnostics_sha256=sha256(diagfile.read_bytes()).hexdigest()))
    # Nonuniform physical data: no constant-pressure condition is passed to solver.
    solver=RegionSolver(m);edges=np.linspace(-.5,1.5,25)
    physical=[(600.,150000. if x<.5 else 100000.,0.,n2 if x<.5 else co2,(0,0,1,0)) for x in (edges[:-1]+edges[1:])/2]
    state=solver.initialize(edges,physical,tuple(range(24)));initial=state;t=0.;steps=0;ledger=np.zeros(12);start=perf_counter()
    while t<.0002:
        dt=min(solver.suggested_dt(state),.0002-t);state,flux=solver.step(state,dt);ledger+=flux[0]-flux[-1];t+=dt;steps+=1
    w=solver.recover(state)
    (HERE/'pressure-jump-diagnostics.json').write_text(json.dumps(solver.records,indent=2)+'\n')
    records.append(dict(kind='PRESSURE_JUMP_INTERACTION_SMOKE_ONLY',steps=steps,elapsed=perf_counter()-start,
        pressure_min=float(w[:,2].min()),pressure_max=float(w[:,2].max()),max_velocity=float(abs(w[:,1]).max()),
        ledger_normalized=(abs(state.inventory.sum(axis=0)-initial.inventory.sum(axis=0)-ledger)/np.maximum(np.sum(abs(initial.inventory),axis=0),1.)).tolist()))
    # The pressure jump starts strictly to the left of the material interface.
    # Its shock reaches/interacts with that interface through ordinary evolution.
    solver=RegionSolver(m)
    physical=[(600.,200000. if x<1/6 else 100000.,0.,n2 if x<.5 else co2,(0,0,1,0)) for x in (edges[:-1]+edges[1:])/2]
    state=solver.initialize(edges,physical,tuple('N2' if x<.5 else 'CO2' for x in (edges[:-1]+edges[1:])/2))
    initial=state;t=0.;steps=0;ledger=np.zeros(12);start=perf_counter()
    while t<.0008:
        dt=min(solver.suggested_dt(state),.0008-t);state,flux=solver.step(state,dt);ledger+=flux[0]-flux[-1];t+=dt;steps+=1
    w=solver.recover(state)
    (HERE/'shock-interaction-diagnostics.json').write_text(json.dumps(solver.records,indent=2)+'\n')
    np.savez_compressed(HERE/'shock-interaction.npz',initial_inventory=initial.inventory,initial_edges=initial.edges,final_inventory=state.inventory,final_edges=state.edges,ledger=ledger)
    records.append(dict(kind='SEPARATE_SHOCK_MATERIAL_INTERACTION_SMOKE_ONLY',steps=steps,elapsed=perf_counter()-start,
        final_time=t,transmitted_CO2_pressure_change_Pa=float(np.max(abs(w[12:,2]-1e5))),
        material_velocity=float(solver.rhs(state)[0][12]),
        ledger_normalized=(abs(state.inventory.sum(axis=0)-initial.inventory.sum(axis=0)-ledger)/np.maximum(np.sum(abs(initial.inventory),axis=0),1.)).tolist()))
    out={'classification':'RESEARCH_PROTOTYPE_CONTROLS_NOT_VAL008_ACCEPTANCE','records':records,
         'source_sha256':{p.name:sha256(p.read_bytes()).hexdigest() for p in [HERE/'prototype.py',Path(__file__)]}}
    (HERE/'control-results.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':run()
