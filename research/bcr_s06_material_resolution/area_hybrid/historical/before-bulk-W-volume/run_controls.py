"""Bounded area-hybrid rest and constant-area checks; no full VAL campaign."""
from pathlib import Path
from hashlib import sha256
import json,time
import numpy as np
from dino2next.thermo import ThermoModel,ThermoDataset,DERIVED_SHA256,RAW_SHA256,TRANSPORT_SHA256,GENERATOR_SHA256
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def model():
    p=ROOT/'docs/science/C1.0/datasets'
    return ThermoModel(ThermoDataset.from_files(p/'thermo_runtime_continuous_v1.json',p/'thermo_species.json',p/'thermo_transport.yaml',ROOT/'research/bcr_s03_nasa_inversion/generate.py',expected_sha256=DERIVED_SHA256,expected_raw_sha256=RAW_SHA256,expected_transport_sha256=TRANSPORT_SHA256,expected_generator_sha256=GENERATOR_SHA256))
def physical(edges,u=0.):
    return [(600. if x<.5 else 1800.,1e5,u,(0.,0.,1.,0.,0.) if x<.5 else (0.,0.,0.,1.,0.),(0.,0.,1.,0.)) for x in (edges[:-1]+edges[1:])/2]

def run():
    from area_solver import AreaHybrid,G,H
    from dino2next.gasdynamics import PolynomialSegment
    grid=np.linspace(0,1,25);s=AreaHybrid(model(),grid,G.VolumeMap(PolynomialSegment(0.,1.,(1.,0.,1.),(1.,))))
    state=s.initialize(grid,physical(grid),('left',)*12+('right',)*12);initial=state
    start=time.perf_counter();faces=np.zeros((25,12));sources=np.zeros((24,12));maxp=maxu=0.
    for _ in range(10):
        state,ledger=s.step(state,1e-6);faces+=ledger.faces;sources+=ledger.sources
        w=s.recover(state);maxp=max(maxp,float(abs(w[:,2]-1e5).max()));maxu=max(maxu,float(abs(w[:,1]).max()))
    np.savez_compressed(HERE/'rest-control.npz',initial_W=initial.W,initial_inventory=initial.inventory,final_W=state.W,final_inventory=state.inventory,faces=faces,sources=sources)
    report=dict(classification='AREA_HYBRID_RESEARCH_REST_CONTROL_NOT_VAL_ACCEPTANCE',steps=10,dt=1e-6,
        max_pressure_error_Pa=maxp,max_velocity=maxu,elapsed_seconds=time.perf_counter()-start,
        ledger_residual=(state.inventory.sum(axis=0)-initial.inventory.sum(axis=0)-(faces[0]-faces[-1])-sources.sum(axis=0)).tolist(),
        stage_records=s.stage_records,hybrid_records=s.hybrid_records,guard_records=s.guard_records,
        source_sha256={str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in [HERE/'area_solver.py',Path(__file__),HERE.parent/'local_material/hybrid.py',HERE.parent/'regional_geometry/geometry.py']})
    (HERE/'control-results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if not k.endswith('_records')},indent=2))
if __name__=='__main__':run()
