import json
import numpy as np
import pytest
from fast_hybrid import FastHybridSolver
from hybrid import HybridSolver
from prototype import LocalSolver
from run_controls import make_model


@pytest.mark.parametrize('wave',[False,True])
def test_fast_overlap_composition_preserves_hybrid_states_fluxes_transactions(wave):
    grid=np.linspace(0,1,25);x=.5+1e-10;edges=np.sort(np.r_[grid,x]);mid=(edges[:-1]+edges[1:])/2
    rows=[(600. if v<x else 1800.,150000. if wave and v<.25 else 100000.,100.,
           (0.,0.,1.,0.,0.) if v<x else (0.,0.,0.,1.,0.),(0.,0.,1.,0.)) for v in mid]
    results=[]
    for cls in (HybridSolver,FastHybridSolver):
        solver=cls(make_model(),grid);state=solver.initialize(edges,rows,tuple('L' if v<x else 'R' for v in mid));arrays=[]
        for step in range(3):
            state,flux,dt,failures=solver.advance(state,1e-5)
            arrays.extend((state.edges.tobytes(),state.inventory.tobytes(),flux.tobytes(),np.float64(dt).tobytes()))
        results.append((arrays,solver.stage_records,solver.hybrid_records,solver.guard_records,solver.transaction_records,solver.remap_records))
    assert results[0]==results[1]
    assert FastHybridSolver.step is LocalSolver.step
    assert FastHybridSolver._step is HybridSolver._step
