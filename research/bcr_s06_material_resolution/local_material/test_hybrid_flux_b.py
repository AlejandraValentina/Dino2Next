import numpy as np
from hybrid import HybridSolver
from prototype import LocalSolver
from run_controls import make_model


def test_bulk_selected_flux_b_is_retained_without_regional_HLLC(monkeypatch):
    grid=np.linspace(0,1,49);solver=HybridSolver(make_model(),grid)
    rows=[(700.,150000. if x<.5 else 100000.,100. if x<.5 else 0.,
           (0.,0.,1.,0.,0.),(0.,0.,1.,0.)) for x in (grid[:-1]+grid[1:])/2]
    state=solver.initialize(grid,rows,('smooth_material',)*48)
    def forbidden(*args):raise AssertionError('Unused regional HLLC before kernel selection')
    monkeypatch.setattr(LocalSolver,'rhs',forbidden)
    _,high,low,patch,bulk=solver.rhs_options(state)
    full=solver.bulk_call(state,0,48,(high[0],high[-1]))
    assert np.any(full.flux_b)
    assert high.tobytes()==full.high.tobytes()
    assert low.tobytes()==full.low.tobytes()
