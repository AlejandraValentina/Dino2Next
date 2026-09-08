import numpy as np
import pytest
from prototype import LocalSolver, TrialRejected
from run_controls import make_model


def physical(x, contact=.5, pressure_jump=False):
    return (600., 150000. if pressure_jump and x < .25 else 1e5, 100.,
            (0.,0.,1.,0.,0.) if x < contact else (0.,0.,0.,1.,0.), (0.,0.,1.,0.))


def test_local_agglomeration_removes_geometric_tiny_piece_and_keeps_contact():
    grid=np.linspace(0,1,13);s=LocalSolver(make_model(),grid)
    x=.5+1e-12;edges=np.sort(np.r_[grid,x]);mid=(edges[:-1]+edges[1:])/2
    a=s.initialize(edges,[physical(v,x) for v in mid],tuple('L' if v<x else 'R' for v in mid))
    before=a.inventory.tobytes();b=s.reorganize(a)
    assert np.min(np.diff(b.edges))>.3*s.dx
    assert b.edges[s.interfaces(b)[0]]==x
    assert a.inventory.tobytes()==before
    assert np.max(abs(np.sum(b.inventory,axis=0)-np.sum(a.inventory,axis=0)))<1e-9
    assert np.max(abs(s.recover(b)[:,2]-1e5))<1e-5


def test_true_thin_material_slab_not_deleted_or_mixed():
    grid=np.linspace(0,1,13);s=LocalSolver(make_model(),grid)
    edges=np.sort(np.r_[grid,.500001,.500002]);mid=(edges[:-1]+edges[1:])/2
    labels=tuple('thin' if .500001<v<.500002 else 'background' for v in mid)
    a=s.initialize(edges,[physical(.1) for v in mid],labels);b=s.reorganize(a)
    assert len(s.interfaces(b))==2
    assert min(np.diff(b.edges))<2e-6
    assert s.suggested_dt(b)<1e-9


def test_only_material_faces_move_and_every_internal_flux_is_paired():
    grid=np.linspace(0,1,13);s=LocalSolver(make_model(),grid);mid=(grid[:-1]+grid[1:])/2
    a=s.initialize(grid,[physical(v) for v in mid],tuple('L' if v<.5 else 'R' for v in mid))
    speed,flux=s.rhs(a);ordinary=np.ones(len(grid),bool);ordinary[s.interfaces(a)]=False
    assert (speed[ordinary]==0).all()
    assert abs(speed[s.interfaces(a)[0]]-100)<1e-8
    assert np.array_equal(flux[1:-1]+(-flux[1:-1]),np.zeros_like(flux[1:-1]))
    for i in s.interfaces(a):assert np.array_equal(flux[i,[0,*range(3,12)]],np.zeros(10))


def test_stage_topology_GCL_and_failed_trial_immutability():
    grid=np.linspace(0,1,13);s=LocalSolver(make_model(),grid);mid=(grid[:-1]+grid[1:])/2
    a=s.initialize(grid,[physical(v) for v in mid],tuple('L' if v<.5 else 'R' for v in mid))
    frozen=a.inventory.tobytes(),a.edges.tobytes();b,ledger=s.step(a,s.suggested_dt(a))
    assert b.labels==a.labels
    assert s.stage_records[-1]['max_GCL_absolute_m']<1e-15
    residual=np.sum(b.inventory-a.inventory,axis=0)-ledger[0]+ledger[-1]
    assert np.max(abs(residual))<1e-9
    with pytest.raises(TrialRejected):s.step(a,1.)
    assert frozen==(a.inventory.tobytes(),a.edges.tobytes())


def test_smooth_composition_does_not_create_material_faces():
    grid=np.linspace(0,1,13);s=LocalSolver(make_model(),grid)
    rows=[(700.,1e5,10.,(0.,0.,float(x),float(1-x),0.),(0.,0.,1.,0.)) for x in (grid[:-1]+grid[1:])/2]
    a=s.initialize(grid,rows,('smooth',)*12)
    assert s.interfaces(a)==[]
    assert s.reorganize(a) is a
    speed,_=s.rhs(a);assert not np.any(speed)
