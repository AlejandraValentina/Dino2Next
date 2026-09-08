"""Algebra/NASA consistency only; no selected transport recipe or waves oracle."""
from pathlib import Path
from hashlib import sha256
from fractions import Fraction as F
import json,time
import numpy as np
from geometry import VolumeMap,algebra_rhs,manufactured_ssprk2
from dino2next.gasdynamics import PolynomialSegment
from dino2next.thermo import (ThermoModel,ThermoDataset,DERIVED_SHA256,RAW_SHA256,
                             TRANSPORT_SHA256,GENERATOR_SHA256)
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
data=ROOT/'docs/science/C1.0/datasets'
m=ThermoModel(ThermoDataset.from_files(data/'thermo_runtime_continuous_v1.json',
    data/'thermo_species.json',data/'thermo_transport.yaml',
    ROOT/'research/bcr_s03_nasa_inversion/generate.py',expected_sha256=DERIVED_SHA256,
    expected_raw_sha256=RAW_SHA256,expected_transport_sha256=TRANSPORT_SHA256,
    expected_generator_sha256=GENERATOR_SHA256))
g=VolumeMap(PolynomialSegment(0.,3.,(1.,0.,9.),(1.,)))
records=[];start=time.perf_counter()
for T,Y in [(600.,(0.,0.,1.,0.,0.)),(1800.,(0.,0.,0.,1.,0.))]:
    s=m.evaluate(T,1e5,Y)
    U=np.array([s.rho,0.,s.rho*s.e,*(s.rho*np.array(Y)),0.,0.,s.rho,0.])
    W=np.array([g.cumulative(.5),g.cumulative(1.5)]);Q=U*np.diff(W)[0]
    maxp=maxT=maxidentity=maxgeom=0.
    for _ in range(10):
        W,Q,stages=manufactured_ssprk2(g,W,Q,U,1e5,[.1,.2],.01)
        for stageW,stageQ in (*stages,(W,Q)):
            volume=float(np.diff(stageW)[0]);rho=float(stageQ[0]/volume)
            velocity=float(stageQ[1]/stageQ[0])
            recovered=m.invert_energy(rho,float(stageQ[2]/stageQ[0]-.5*velocity**2),Y)
            maxp=max(maxp,abs(recovered.p-1e5));maxT=max(maxT,abs(recovered.T-T))
            maxidentity=max(maxidentity,float(np.max(abs(stageQ-U*volume)/np.maximum(abs(U*volume),1.))))
            for w in stageW:
                _,_,res=g.inverse(float(w));maxgeom=max(maxgeom,abs(float(res)))
    records.append(dict(T=T,Y=Y,initial_specific_internal_energy=s.e,
        max_pressure_error_Pa=maxp,max_temperature_error_K=maxT,
        max_inventory_identity_normalized_diagnostic=maxidentity,
        max_exact_inverse_volume_roundoff=maxgeom,final_W=W.tolist(),final_Q=Q.tolist()))

# Stationary two-region thermal/composition contact in variable area. Geometry
# source cancels each region's own pressure-face flux; no moving-u oracle used.
stationary=[]
for a,b,T,Y in [(.5,1.,600.,(0.,0.,1.,0.,0.)),(1.,1.5,1800.,(0.,0.,0.,1.,0.))]:
    s=m.evaluate(T,1e5,Y);U=np.array([s.rho,0.,s.rho*s.e,*(s.rho*np.array(Y)),0.,0.,s.rho,0.])
    dW,dQ,flux,source=algebra_rhs(g,np.array([g.cumulative(a),g.cumulative(b)]),U,s.p,[0.,0.])
    stationary.append(dict(bounds=[a,b],volume=g.segment.integral(a,b),inventory_rhs=dQ.tolist(),
        geometry_rhs=dW.tolist(),face_flux=flux.tolist(),pressure_area_source=source.tolist()))

report=dict(classification='RESEARCH_GEOMETRY_ALGEBRA_AND_NASA_AUDIT_NOT_TRANSPORT_ACCEPTANCE',
    stationary_thermal_contact=stationary,manufactured_static_fluid_moving_mesh=records,
    exact_position_FE_counterexample_volume_defect=str(F(1,5000)),
    exact_unequal_speed_SSPRK_final_volume_defect=str(-((F(1,5)**3-F(1,10)**3)*F(1,10)**3)/6),
    elapsed_seconds=time.perf_counter()-start,
    source_sha256={str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in
        [HERE/'geometry.py',Path(__file__),ROOT/'src/dino2next/gasdynamics/__init__.py',
         ROOT/'src/dino2next/thermo/__init__.py',data/'thermo_runtime_continuous_v1.json']})
(HERE/'control-results.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
