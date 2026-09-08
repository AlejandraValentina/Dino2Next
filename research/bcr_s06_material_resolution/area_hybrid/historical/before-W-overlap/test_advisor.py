from types import SimpleNamespace
import numpy as np
import pytest
from advisor import bounds,AdvisedAreaHybrid
from area_solver import G,H
from dino2next.gasdynamics import PolynomialSegment
from run_controls import model,physical

def test_volume_advisor_not_old_dx_in_steep_positive_area():
    state=SimpleNamespace(W=np.array([0.,1.]),edges=np.array([0.,1.]))
    primitive=np.array([[1.,0.,1.,1.,1.]])
    report=bounds(state,primitive,[1.,10.],[0.,0.])
    assert report['inherited_acoustic']==[.2]
    assert report['volumetric_acoustic']==[.2*.1]
    assert report['limit']==.2*.1 and report['shrinking_volume']==[None]

def test_shrinking_bound_keeps_half_current_volume_at_same_FE_rate():
    state=SimpleNamespace(W=np.array([0.,1.]),edges=np.array([0.,1.]))
    primitive=np.array([[1.,100.,1.,1.,1.]])
    # Material faces move at fluid speed in a strongly decreasing area.
    report=bounds(state,primitive,[10.,1.],[1000.,100.])
    assert report['limit']==.5/900
    assert 1+report['limit']*report['volume_rate'][0]==.5

def test_constant_area_volumetric_and_inherited_bounds_agree():
    state=SimpleNamespace(W=np.array([0.,2.,4.]),edges=np.array([0.,1.,2.]))
    w=np.array([[1.,3.,1.,5.,1.],[1.,-2.,1.,4.,1.]])
    r=bounds(state,w,[2.,2.,2.],[0.,2.,0.])
    np.testing.assert_array_equal(r['inherited_acoustic'],r['volumetric_acoustic'])

def make_solver(coefficients):
    grid=np.linspace(0,1,13)
    solver=AdvisedAreaHybrid(model(),grid,G.VolumeMap(PolynomialSegment(0.,1.,coefficients,(1.,))))
    state=solver.initialize(grid,physical(grid,u=30.),('left',)*6+('right',)*6)
    return solver,state

@pytest.mark.parametrize('coefficients',[(1.,0.,20.),(4.,-3.,1.),(.1,10.)])
def test_positive_polynomials_and_moving_material_stage_bounds(coefficients):
    solver,state=make_solver(coefficients);dt=solver.suggested_dt(state)
    before=state.W.tobytes(),state.inventory.tobytes()
    with pytest.raises(H.TrialRejected,match='VOLUMETRIC_STAGE_BOUND_Y0'):
        solver.step(state,np.nextafter(dt,np.inf))
    assert before==(state.W.tobytes(),state.inventory.tobytes())
    final,ledger,used,failures=solver.attempt(state,dt)
    records=[r for r in solver.advisor_records if r['transaction_id']==solver.transaction_records[-1]['transaction_id']]
    assert [r['stage'] for r in records]==['Y0','Y1']
    assert all(r['admissible_dt'] and r['requested_dt']==used for r in records)
    assert np.min(np.diff(final.W))>0
    assert np.all(np.isfinite(solver.recover(final)))

def test_reject_second_stage_bound_without_changing_step_midstage(monkeypatch):
    solver,state=make_solver((1.,0.,1.));actual=solver.evaluate_bounds
    dt=actual(state)['limit']*.5;calls=[0]
    def lowered(stage):
        result=actual(stage);calls[0]+=1
        if calls[0]==2:result['limit']=dt*.5
        return result
    monkeypatch.setattr(solver,'evaluate_bounds',lowered)
    before=state.W.tobytes(),state.inventory.tobytes()
    with pytest.raises(H.TrialRejected,match='VOLUMETRIC_STAGE_BOUND_Y1'):solver.step(state,dt)
    assert before==(state.W.tobytes(),state.inventory.tobytes())
    assert [r['requested_dt'] for r in solver.advisor_records]==[dt,dt]
    assert solver.transaction_records[-1]['status']=='REJECTED'
