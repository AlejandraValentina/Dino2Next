from dataclasses import FrozenInstanceError,replace
from types import SimpleNamespace
from hashlib import sha256
from math import fsum
import pytest

from dino2next.gasdynamics import (Mesh1D,DuctState,IntegratedInventory,PrimitiveArrays,
                                  COMPONENTS,PolynomialSegment)
from dino2next.units import ValueContractError


def state_rows(mesh,thermo,T=700,p=120000,u=20,Y=(0,0,1,0,0),tau=(0,0,1,0)):
    state=thermo.evaluate(T,p,Y)
    return [[a*v for v in (state.rho,state.rho*u,state.rho*(state.e+u*u/2),
                           *(state.rho*y for y in Y),*(state.rho*t for t in tau))]
            for a in mesh.area_averages]


def test_cell_averages_are_not_integrated_inventories(thermo):
    mesh=Mesh1D((0,.1,.3),(.002,.003),(.001,.003,.003),(.2,.2),(.1,))
    q=state_rows(mesh,thermo)
    duct=DuctState(mesh,q,thermo)
    expected=[fsum(row[j]*dx for row,dx in zip(q,mesh.dx)) for j in range(12)]
    inv=duct.integrated_inventory()
    assert (inv.mass,inv.momentum,inv.total_energy,*inv.species_mass,*inv.tracer_mass)==tuple(expected)
    assert inv.mass!=fsum(row[0] for row in q)
    q[0][0]=0
    assert duct.Q[0][0]>0
    assert duct.component_order==COMPONENTS
    with pytest.raises(FrozenInstanceError):duct.Q=()
    with pytest.raises(TypeError):duct.Q[0][0]=0
    with pytest.raises(FrozenInstanceError):inv.mass=0


@pytest.mark.parametrize('u',[-300,0,300])
@pytest.mark.parametrize('Y',[(1,0,0,0,0),(0,0,0,0,1),(0,.23,.77,0,0)])
def test_formation_energy_and_kinetic_recovery(thermo,u,Y):
    mesh=Mesh1D((0,.25,.5),(1,1),(1,1,1),(4,4))
    q=state_rows(mesh,thermo,T=600,p=200000,u=u,Y=Y,tau=(.1,.2,.3,.4))
    duct=DuctState(mesh,q,thermo)
    primitive=duct.primitive()
    for state in primitive.states:
        assert abs(state.T-600)<=1e-8
        assert state.Y==pytest.approx(Y,rel=0,abs=2e-16)
    assert primitive.u==pytest.approx((u,u),rel=1e-14,abs=0)
    assert primitive.tracers[0]==pytest.approx((.1,.2,.3,.4),rel=1e-14)
    if Y[4]==1:assert duct.integrated_inventory().total_energy<0
    assert duct.Q==tuple(map(tuple,q))


def test_exact_duplicate_rows_reuse_eos_result_without_changing_recovery(thermo,monkeypatch):
    mesh=Mesh1D((0,.25,.5,.75,1.),(1,1,1,1),(1,1,1,1,1),(4,4,4,4))
    rows=state_rows(mesh,thermo,T=600,p=200000,u=75,Y=(0,.23,.77,0,0),tau=(.1,.2,.3,.4))
    expected=thermo.invert_energy(rows[0][0],rows[0][2]/rows[0][0]-.5*(rows[0][1]/rows[0][0])**2,
                                  (0,.23,.77,0,0))
    calls=[];original=type(thermo).invert_energy
    def invert(model,rho,e,Y,**kwargs):
        calls.append((rho,e,Y));return original(model,rho,e,Y,**kwargs)
    monkeypatch.setattr(type(thermo),'invert_energy',invert)
    duct=DuctState(mesh,rows,thermo)
    assert len(calls)==1
    for state in duct.primitive().states:
        assert (state.T,state.p,state.rho,state.e)==pytest.approx((expected.T,expected.p,expected.rho,expected.e),rel=0,abs=5e-10)
        assert state.Y==pytest.approx(expected.Y,rel=0,abs=5e-16)


def test_only_derived_fraction_roundoff_is_corrected(thermo):
    mesh=Mesh1D((0,1),(1,),(1,1),(4,))
    q=state_rows(mesh,thermo)
    q[0][5]*=1+8e-15
    q[0][10]*=1+8e-15
    original=tuple(q[0])
    duct=DuctState(mesh,q,thermo)
    output=duct.primitive()
    assert duct.Q==(original,)
    assert {record[1] for record in output.roundoff_records}=={'/chemical','/tracers'}
    assert output.Y[0]==(0,0,1,0,0)
    assert output.tracers[0]==(0,0,1,0)
    assert duct.integrated_inventory().species_mass[2]==original[5]


@pytest.mark.parametrize('column,value',[(0,0),(0,-1),(3,-1e-300),(8,-1e-300),(3,1),
                                         (8,1),(2,float('nan')),(1,float('inf')),(2,1e300)])
def test_inadmissible_cell_never_publishes_partial_state(thermo,column,value):
    mesh=Mesh1D((0,1),(1,),(1,1),(4,))
    q=state_rows(mesh,thermo)
    q[0][column]=value
    original=[row.copy() for row in q]
    with pytest.raises(ValueContractError) as error:DuctState(mesh,q,thermo)
    assert error.value.code=='EOS_OUT_OF_DOMAIN'
    assert q==original


def test_order_and_dimensions_are_checked(thermo):
    mesh=Mesh1D((0,1),(1,),(1,1),(4,))
    q=state_rows(mesh,thermo)
    with pytest.raises(ValueContractError):DuctState(mesh,q,thermo,tuple(reversed(COMPONENTS)))
    with pytest.raises(ValueContractError):DuctState(mesh,[q[0][:-1]],thermo)
    with pytest.raises(ValueContractError):DuctState(mesh,[],thermo)


def test_direct_public_values_freeze_nested_inputs(thermo):
    mesh=Mesh1D((0,1),(1,),(1,1),(4,))
    s=DuctState(mesh,state_rows(mesh,thermo),thermo).primitive().states[0]
    tags=[[0,0,1,0]]
    p=PrimitiveArrays([s],[0],tags,[[0,'/tracers',1]])
    tags[0][2]=0
    assert p.tracers==((0,0,1,0),)
    assert p.roundoff_records==((0,'/tracers',1),)
    with pytest.raises(ValueContractError):replace(p,tracers=[[0,0,-1,2]])
    with pytest.raises(ValueContractError):replace(p,roundoff_records=[[0,'unknown',1]])
    with pytest.raises(ValueContractError):IntegratedInventory(1,0,-1,[0,0,2,0,0],[0,0,1,0])
    inv=IntegratedInventory(1,0,-1,[0,0,1,0,0],[0,0,1,0])
    assert inv.species_mass==(0,0,1,0,0)


def test_explicit_fixture_recovery_protocol_is_not_gen1_runtime(thermo):
    class ForwardingFixture:
        source_kind='NUMERICAL_FIXTURE_ONLY'
        identity='SOFTWARE_PROTOCOL_FORWARDING_TEST'
        reference_sha256=sha256(b'forward accepted NASA output through a detached result protocol').hexdigest()
        def invert_energy(self,rho,e,Y):
            s=thermo.invert_energy(rho,e,Y)
            return SimpleNamespace(**{key:getattr(s,key) for key in ('T','p','rho','R','cp','cv','h','e','gamma','a','Y')})
    mesh=Mesh1D((0,1),(1,),(1,1),(4,))
    q=state_rows(mesh,thermo)
    adapter=ForwardingFixture()
    with pytest.raises(ValueContractError):DuctState(mesh,q,adapter)
    duct=DuctState(mesh,q,adapter,source_kind='NUMERICAL_FIXTURE_ONLY')
    result=duct.primitive().states[0]
    assert result.source_kind=='NUMERICAL_FIXTURE_ONLY'
    assert result.model_identity.startswith('SOFTWARE_PROTOCOL_FORWARDING_TEST')
    assert 'DINO2NEXT_NASA5' not in result.model_identity
    assert duct.Q==tuple(map(tuple,q))
    adapter.reference_sha256='unqualified'
    adapter.invert_energy=lambda *args:None
    assert duct.primitive().states[0]==result
    assert duct.recovery_identity==result.model_identity
    with pytest.raises(ValueContractError):DuctState(mesh,q,adapter,source_kind='NUMERICAL_FIXTURE_ONLY')


def test_refining_geometry_preserves_integrated_constant_state(thermo):
    shape=PolynomialSegment(0,1,(1.1,-.4,.4),(4,))
    results=[]
    for n in (4,8,16):
        mesh=Mesh1D.from_segments(tuple(i/n for i in range(n+1)),(shape,))
        duct=DuctState(mesh,state_rows(mesh,thermo),thermo)
        results.append(duct.integrated_inventory())
    for result in results[1:]:
        assert result.mass==pytest.approx(results[0].mass,rel=3e-15)
        assert result.total_energy==pytest.approx(results[0].total_energy,rel=3e-15)
