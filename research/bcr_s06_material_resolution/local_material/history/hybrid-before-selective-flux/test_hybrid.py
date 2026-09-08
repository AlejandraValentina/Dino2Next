import numpy as np
import pytest
from hybrid import HybridSolver
from prototype import TrialRejected
from run_controls import make_model


@pytest.mark.parametrize('material',[False,True])
def test_bulk_fluxes_bitwise_equal_pinned_kernel_without_Qbar_proxy(material):
    grid=np.linspace(0,1,49);solver=HybridSolver(make_model(),grid)
    centers=(grid[:-1]+grid[1:])/2
    rows=[(600.,float(1e5+100*np.sin(2*np.pi*x)),30.,
           (0.,0.,0.,1.,0.) if material and x>.5 else (0.,0.,1.,0.,0.),(0.,0.,1.,0.)) for x in centers]
    state=solver.initialize(grid,rows,tuple('R' if material and x>.5 else 'L' for x in centers))
    speeds,high,low,patch,bulk=solver.rhs_options(state)
    full=solver.bulk_call(state,0,len(rows),(high[0],high[-1]))
    assert np.any(bulk)
    assert high[bulk].tobytes()==full.high[bulk].tobytes()
    assert low[bulk].tobytes()==full.low[bulk].tobytes()
    if not material:
        assert not patch.any()
        assert high.tobytes()==full.high.tobytes()
        assert low.tobytes()==full.low.tobytes()
    else:
        assert patch[23] and patch[24]
    ordinary=np.ones(len(grid),bool);ordinary[solver.interfaces(state)]=False
    assert np.all(speeds[ordinary]==0)


def one_state():
    solver=HybridSolver(make_model(),[0.,.5,1.])
    state=solver.initialize([0.,1.],[(600.,300000.,0.,(0.,0.,1.,0.,0.),(0.,0.,1.,0.))],('one',))
    return solver,state


def test_common_guard_conserves_and_validates_second_FE():
    solver,state=one_state();low=np.zeros((2,12));high=low.copy();high[0]=-1.5*state.inventory[0]
    trial,flux,theta,reductions=solver._guard(state,state,1.,np.zeros(2),high,low,True)
    assert 0<=theta<1
    solver.recover(trial)
    assert np.allclose(trial.inventory-state.inventory,flux[:-1]-flux[1:],rtol=0,atol=1e-10)
    assert np.array_equal(flux,low+theta*(high-low))


def test_inadmissible_low_order_rejects_instead_of_clipping():
    solver,state=one_state();flux=np.zeros((2,12));flux[0]=-2*state.inventory[0]
    original=state.inventory.tobytes()
    with pytest.raises(TrialRejected,match='LOW_ORDER_STAGE_INADMISSIBLE_RETRY_DT'):
        solver._guard(state,state,1.,np.zeros(2),flux,flux,True)
    assert state.inventory.tobytes()==original
