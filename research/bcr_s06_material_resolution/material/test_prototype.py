"""Software/algebra controls, not numerical acceptance of VAL-008."""
import numpy as np
import pytest
from prototype import RegionSolver,State,TrialRejected
from run_controls import model


@pytest.fixture
def solver():return RegionSolver(model())

def initial(solver,edges=(-1.,0.,1.),u=100.,pressures=(100000.,100000.)):
    return solver.initialize(edges,[(600.,pressures[0],u,(0.,0.,1.,0.,0.),(0.,0.,1.,0.)),
        (1800.,pressures[1],u,(0.,0.,0.,1.,0.),(0.,0.,1.,0.))],('parcel-a','parcel-b'))

def test_immutable_state_and_rejected_trial(solver):
    s=initial(solver);before=s.inventory.tobytes(),s.edges.tobytes()
    with pytest.raises(ValueError):s.inventory[0,0]=0
    with pytest.raises(TrialRejected):solver.attempt(s,1.,max_retries=0)
    assert before==(s.inventory.tobytes(),s.edges.tobytes())
    out,ledger,dt,failures=solver.attempt(s,4*solver.suggested_dt(s))
    assert len(failures)==2 and dt>0
    np.testing.assert_allclose(out.inventory.sum(axis=0)-s.inventory.sum(axis=0),
                               ledger[0]-ledger[-1],rtol=0,atol=3e-9)

def test_split_retains_inventory_and_separate_thermo(solver):
    s=initial(solver);out=solver.split(s,0,-.37)
    np.testing.assert_allclose(out.inventory.sum(axis=0),s.inventory.sum(axis=0),rtol=2e-16,atol=0)
    assert out.labels==('parcel-a','parcel-a','parcel-b')
    np.testing.assert_allclose(solver.recover(out)[:,4],[600.,600.,1800.],rtol=0,atol=1e-8)

def test_geometric_projection_and_face_crossing(solver):
    s=initial(solver);out,f=solver.step(s,.0001)
    totals,p,pieces=solver.sample(out,[-.2,.005,.2])
    assert out.edges[1]>.005
    assert {region for cell,region,_,_ in pieces if cell==0}=={0}
    assert {region for cell,region,_,_ in pieces if cell==1}=={0,1}
    np.testing.assert_allclose(p,1e5,rtol=0,atol=1e-5)
    assert np.any(totals[:,3:8]>0)
    assert sum(width for _,_,width,_ in pieces)==pytest.approx(.4)

def test_pressure_force_and_work_not_suppressed(solver):
    s=initial(solver,u=0.,pressures=(150000.,100000.));v,f=solver.rhs(s)
    assert v[1]>0 and 1e5<f[1,1]<1.5e5
    assert f[1,2]==f[1,1]*v[1]
    assert np.array_equal(f[:,[0,3,4,5,6,7,8,9,10,11]],np.zeros((3,10)))
    out,ledger=solver.step(s,1e-5)
    assert solver.recover(out)[:,1].max()>0
    np.testing.assert_allclose(out.inventory.sum(axis=0)-s.inventory.sum(axis=0),ledger[0]-ledger[-1],atol=3e-9)

def test_tiny_region_restricts_step_without_deletion(solver):
    s=initial(solver,edges=(-1.,0.,1e-9))
    assert solver.suggested_dt(s)<1e-12
    with pytest.raises(TrialRejected):solver.attempt(s,1e-6,max_retries=0)
    assert len(s.labels)==2 and s.inventory[1,0]>0

def test_smooth_composition_is_physical_parcels(solver):
    edges=np.linspace(0,1,6)
    values=[(800.,1e5,0.,(0.,0.,float(y),float(1-y),0.),(1.,0.,0.,0.)) for y in np.linspace(.1,.9,5)]
    s=solver.initialize(edges,values,('smooth',)*5)
    out,ledger=solver.step(s,1e-6)
    np.testing.assert_allclose(out.inventory[:,3:],s.inventory[:,3:],rtol=0,atol=0)
    assert np.ptp(s.inventory[:,5]/s.inventory[:,0])>0

def test_invalid_negative_and_geometry_fail_without_repair(solver):
    s=initial(solver);bad=s.inventory.copy();bad[0,3]=-1e-30
    with pytest.raises(TrialRejected):State(s.edges,bad,s.labels)
    with pytest.raises(TrialRejected):State([0,0,1],s.inventory,s.labels)
    with pytest.raises(TrialRejected):solver.split(s,0,0.)


def test_second_fe_geometry_cannot_hide_in_valid_combination(solver,monkeypatch):
    s=solver.initialize([0.,1.],[(600.,1e5,0.,(0.,0.,1.,0.,0.),(0.,0.,1.,0.))],('parcel',))
    calls=[0]
    def rhs(_):
        calls[0]+=1
        return np.array([0.,0. if calls[0]==1 else -1.5]),np.zeros((2,12))
    monkeypatch.setattr(solver,'rhs',rhs)
    before=s.inventory.tobytes(),s.edges.tobytes()
    with pytest.raises(TrialRejected,match='NONPOSITIVE_REGION'):solver.step(s,1.)
    assert before==(s.inventory.tobytes(),s.edges.tobytes())
    assert solver.records[-1]['stage']=='FE2_STATE'
    assert solver.records[-1]['status']=='REJECTED'


def test_second_fe_eos_cannot_hide_in_valid_combination(solver,monkeypatch):
    from dino2next.units import ValueContractError
    y=(0.,0.,1.,0.,0.)
    s=solver.initialize([0.,1.],[(600.,1e5,0.,y,(0.,0.,1.,0.))],('parcel',))
    target=2*solver.model.evaluate(1800.,1e5,y).e-solver.model.evaluate(600.,1e5,y).e
    assert target>solver.model.evaluate(2200.,1e5,y).e
    addition=s.inventory[0,0]*target-s.inventory[0,2];calls=[0]
    def rhs(_):
        calls[0]+=1;flux=np.zeros((2,12))
        if calls[0]==2:flux[0,2]=addition
        return np.zeros(2),flux
    monkeypatch.setattr(solver,'rhs',rhs)
    with pytest.raises(ValueContractError):solver.step(s,1.)
    assert solver.records[-1]['stage']=='FE2_STATE'
    assert solver.records[-1]['status']=='REJECTED'


def test_retry_records_distinguish_rejected_and_accepted_trials(solver):
    s=initial(solver)
    solver.attempt(s,4*solver.suggested_dt(s))
    ends=[row for row in solver.records if row['event']=='TRIAL_END']
    assert [row['status'] for row in ends]==['REJECTED','REJECTED','ACCEPTED']
    ids=[row['transaction_id'] for row in ends]
    assert len(set(ids))==3
    for row in solver.records:
        if row['transaction_id'] is not None:
            assert row['status']==ends[ids.index(row['transaction_id'])]['status']
