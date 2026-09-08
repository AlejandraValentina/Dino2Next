import numpy as np
import pytest
from area_solver import AreaHybrid,AreaState,G,H
from dino2next.gasdynamics import PolynomialSegment
from run_controls import model,physical

def solver(area=(1.,0.,1.)):
    grid=np.linspace(0,1,25)
    return AreaHybrid(model(),grid,G.VolumeMap(PolynomialSegment(0.,1.,area,(1.,))))


def test_thin_bulk_uses_authoritative_volume_for_actual_nasa_recovery(monkeypatch):
    grid=np.array([.9,.9000000001,.9000000002])
    s=AreaHybrid(model(),grid,G.VolumeMap(PolynomialSegment(0.,1.,(1.,0.,2.),(1.,))))
    data=[(600.,1e5,0.,(0.,0.,1.,0.,0.),(0.,0.,1.,0.))]*2
    state=s.initialize(grid,data,('L','L'));before=state.inventory.tobytes()
    assert not np.any(s.patch_cells(state))
    calls=[];original=s.kernel.state
    def capture(mesh,Q):
        result=original(mesh,Q);calls.append((mesh,result,s.kernel.recover(Q/np.asarray(mesh.area_averages)[:,None])))
        return result
    monkeypatch.setattr(s.kernel,'state',capture)
    s.rhs_options(state)
    assert len(calls)==1
    mesh,local,primitive=calls[0]
    np.testing.assert_allclose(primitive.V[:,2],s.recover(state)[:,2],rtol=2e-14,atol=0.)
    np.testing.assert_allclose(primitive.V[:,0],state.inventory[:,0]/np.diff(state.W),rtol=5e-16,atol=0.)
    assert state.inventory.tobytes()==before
    assert tuple(mesh.area_averages)==tuple(np.diff(state.W)/np.diff(state.edges))

def test_quadratic_rest_stationary_thermal_contact_and_bulk():
    s=solver();state=s.initialize(s.grid,physical(s.grid),('left',)*12+('right',)*12)
    v,h,l,p,b,source=s.rhs_options(state)
    assert np.any(b) and np.any(p)
    assert max(abs(v))<1e-9
    assert np.max(abs(h[:-1]-h[1:]+source))<1e-3
    out,ledger=s.step(state,1e-6)
    assert max(abs(s.recover(out)[:,2]-1e5))<1e-5
    residual=out.inventory.sum(axis=0)-state.inventory.sum(axis=0)-(ledger.faces[0]-ledger.faces[-1])-ledger.sources.sum(axis=0)
    assert np.max(abs(residual))<1e-8
    assert max(abs(np.diff(out.W)-np.diff(state.W)-1e-6*.5*(np.diff(s.stage_records[-1]['volume_speed0'])+np.diff(s.stage_records[-1]['volume_speed1']))))<1e-15

def test_constant_area_matches_frozen_hybrid_explicitly():
    s=solver((1.,));old=H.HybridSolver(s.model,s.grid);states=physical(s.grid,u=30.)
    a=s.initialize(s.grid,states,('left',)*12+('right',)*12)
    b=old.initialize(old.grid,states,a.labels)
    new,ledger=s.step(a,1e-6);prior,oldledger=old.step(b,1e-6)
    assert new.edges.tobytes()==prior.edges.tobytes()
    assert new.inventory.tobytes()==prior.inventory.tobytes()
    assert ledger.faces.tobytes()==oldledger.tobytes()
    assert not np.any(ledger.sources)

def test_second_fe_volume_guard_cannot_hide_invalid_stage():
    s=solver();state=s.initialize(s.grid,physical(s.grid),('left',)*12+('right',)*12)
    s._guard_source=np.zeros_like(state.inventory)
    speed=np.zeros(25);speed[1]=-1e6
    flux=np.zeros((25,12))
    with pytest.raises(H.TrialRejected,match='LOW_ORDER_STAGE_INADMISSIBLE'):
        s._guard(state,state,1.,speed,flux,flux,True)
    assert not any(r['selected'] for r in s.guard_records)

def test_exact_area_overlap_remap_conserves_every_inventory():
    s=solver();edges=s.grid.copy();edges[12]+=.003
    state=s.initialize(edges,physical(edges),('left',)*12+('right',)*12)
    result=s.reorganize(state)
    np.testing.assert_allclose(result.inventory.sum(axis=0),state.inventory.sum(axis=0),rtol=3e-16,atol=1e-9)
    assert all(x in result.labels for x in ('left','right'))
    assert np.min(np.diff(result.W))>0

def test_manufactured_static_gas_moving_mesh_gcl_through_full_guards(monkeypatch):
    s=solver();data=[(600.,1e5,0.,(0.,0.,1.,0.,0.),(0.,0.,1.,0.))]*24
    state=s.initialize(s.grid,data,('uniform',)*24)
    U=state.inventory[0]/(state.W[1]-state.W[0])
    def manufactured(stage):
        area=np.array([s.geometry.segment.value(float(x)) for x in stage.edges])
        speed=.1*np.sin(np.pi*stage.edges);speed[[0,-1]]=0.
        F=np.zeros(12);F[1]=1e5
        flux=area[:,None]*(F-speed[:,None]*U)
        source=np.zeros_like(stage.inventory);source[:,1]=1e5*np.diff(area)
        return area*speed,flux,flux,np.ones(24,bool),np.zeros(25,bool),source
    monkeypatch.setattr(s,'rhs_options',manufactured)
    final,ledger=s.step(state,.001)
    np.testing.assert_allclose(final.inventory,U*np.diff(final.W)[:,None],rtol=1e-14,atol=1e-9)
    assert max(abs(s.recover(final)[:,2]-1e5))<1e-5
    assert s.stage_records[-1]['max_GCL_volume']<1e-15

def test_y2_eos_guard_checks_before_admissible_convex_combination():
    s=solver();state=s.initialize(s.grid,physical(s.grid),('left',)*12+('right',)*12)
    y=(0.,0.,1.,0.,0.)
    energy=2*s.model.evaluate(1800.,1e5,y).e-s.model.evaluate(600.,1e5,y).e
    flux=np.zeros((25,12));flux[0,2]=state.inventory[0,0]*energy-state.inventory[0,2]
    s._guard_source=np.zeros_like(state.inventory)
    with pytest.raises(H.TrialRejected,match='LOW_ORDER_STAGE_INADMISSIBLE'):
        s._guard(state,state,1.,np.zeros(25),flux,flux,True)
    assert not any(row['selected'] for row in s.guard_records)

def test_projection_uses_area_overlap_and_physical_pressure():
    s=solver();state=s.initialize(s.grid,physical(s.grid),('left',)*12+('right',)*12)
    q,p,pieces=s.sample(state,[0.,.55,1.])
    np.testing.assert_allclose(q.sum(axis=0),state.inventory.sum(axis=0),rtol=2e-15,atol=1e-9)
    assert max(abs(p-1e5))<1e-5
    assert sum(v for _,_,v,_ in pieces)==pytest.approx(4/3)

def test_canonical_rounded_endpoint_is_recorded_without_clipping():
    from fractions import Fraction
    s=solver((1.,0.,2.));state=s.initialize(s.grid,physical(s.grid),('left',)*12+('right',)*12)
    assert state.edges[-1]==1. and state.W[-1]==float(Fraction(5,3))
    exact=Fraction(5,3)-Fraction(float(Fraction(5,3)))
    assert exact<0
    assert state.endpoint_records[-1]==(24,'CANONICAL_RIGHT_ENDPOINT',str(exact))
    assert state.inverse_residuals[-1]==float(exact)
    original=state.inventory.tobytes()
    invalid=state.W.copy();invalid[-1]=np.nextafter(invalid[-1],np.inf)
    with pytest.raises(H.TrialRejected,match='GEOMETRY_VOLUME_INVERSION'):
        s.make_state(invalid,state.inventory,state.labels)
    assert state.inventory.tobytes()==original
    interior=state.W.copy();interior[-1]=np.nextafter(interior[-1],-np.inf)
    inner=s.make_state(interior,state.inventory,state.labels)
    assert inner.edges[-1]<=1. and not inner.endpoint_records
    assert inner.W[-1]==interior[-1]  # Ordinary inverse may round x to endpoint.

def test_thin_region_self_projection_preserves_authoritative_inventory_bits():
    grid=np.array([0.,.9,.9000000001,1.])
    s=AreaHybrid(model(),grid,G.VolumeMap(PolynomialSegment(0.,1.,(1.,0.,2.),(1.,))))
    data=[(600.,1e5,0.,(0.,0.,1.,0.,0.),(0.,0.,1.,0.))]*3
    state=s.initialize(grid,data,('L','M','R'))
    q,p,pieces=s.sample(state,state.edges)
    assert q.tobytes()==state.inventory.tobytes()
    assert np.array([v for _,_,v,_ in pieces]).tobytes()==np.diff(state.W).tobytes()
    assert max(abs(p-1e5))<1e-5
    remapped=s.reorganize(state)
    np.testing.assert_array_equal(remapped.inventory.sum(axis=0),state.inventory.sum(axis=0))
    assert remapped.labels==state.labels
