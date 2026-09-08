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
