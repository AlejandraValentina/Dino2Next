from dataclasses import FrozenInstanceError,replace
from fractions import Fraction
from pathlib import Path
from hashlib import sha256
from math import nextafter,inf,fsum
import json
import numpy as np
import pytest
from dino2next.gasdynamics import (CumulativeVolumeGeometry,RegionalDuctState,
                                  PolynomialSegment,Mesh1D,DuctState,COMPONENTS)
from dino2next.thermo import ThermoModel,ThermoDataset
from dino2next.units import ValueContractError

@pytest.fixture(scope='module')
def thermo():
    root=Path(__file__).resolve().parents[3];base=root/'docs/science/C1.0/datasets'
    paths=[base/'thermo_runtime_continuous_v1.json',base/'thermo_species.json',base/'thermo_transport.yaml',root/'research/bcr_s03_nasa_inversion/generate.py']
    h=lambda p:sha256(p.read_bytes()).hexdigest()
    return ThermoModel(ThermoDataset.from_files(*paths,expected_sha256=h(paths[0]),expected_raw_sha256=h(paths[1]),expected_transport_sha256=h(paths[2]),expected_generator_sha256=h(paths[3])))

def setup(thermo,edges=(0.,.5,1.),area=(1.,0.,2.),labels=None):
    geometry=CumulativeVolumeGeometry(PolynomialSegment(0.,1.,area,(1.,)))
    mesh=Mesh1D(tuple(edges),tuple(geometry.segment.integral(a,b)/(b-a) for a,b in zip(edges,edges[1:])),
                tuple(geometry.segment.value(x) for x in edges),(1.,)*(len(edges)-1))
    labels=labels or ('N2',)*(len(edges)-1)
    data=[(600.,1e5,0.,(0.,0.,1.,0.,0.),(0.,0.,1.,0.))]*(len(edges)-1)
    return RegionalDuctState.from_physical(geometry,mesh,edges,data,labels,thermo)

def test_canonical_right_endpoint_and_next_float_outside(thermo):
    s=setup(thermo);g=s.geometry;w=g.cumulative(1.)
    c=g.inverse(w)
    assert c.x==1. and c.bracket is None and c.kind=='CANONICAL_RIGHT_ENDPOINT'
    assert c.residual_exact==Fraction(5,3)-Fraction(w)
    with pytest.raises(ValueContractError) as error:g.inverse(nextafter(w,inf))
    assert error.value.code=='GEOMETRY_VOLUME_INVERSION'
    with pytest.raises(ValueContractError):g.inverse(-1e-300)

def test_inverse_exact_bracket_and_residual(thermo):
    g=setup(thermo).geometry
    for x in (.01,.1,.9,.999):
        w=g.cumulative(x);c=g.inverse(w);lo,hi=c.bracket
        assert g.exact(lo)<=Fraction(w)<=g.exact(hi)
        assert lo==hi or nextafter(lo,inf)==hi
        assert c.residual_exact==g.exact(c.x)-Fraction(w)

def test_area02_thin_region_self_projection_exact_inventory(thermo):
    s=setup(thermo)
    edges=(0.,.9,.9000000001,1.)
    physical=[(600.,1e5,0.,(0.,0.,1.,0.,0.),(0.,0.,1.,0.))]*3
    state=RegionalDuctState.from_physical(s.geometry,s.base_mesh,edges,physical,('L','M','R'),thermo)
    projected=state.projection(state.edges)
    assert np.array(projected.inventory).tobytes()==np.array(state.inventory).tobytes()
    assert projected.W==state.W
    assert projected.geometry_residuals==tuple(c.residual_exact for c in state.inverse_certificates)

def test_area03_bulk_consistent_volume_and_region_pressure(thermo):
    s=setup(thermo,edges=(.9,.9000000001,.9000000002))
    dx=np.diff(s.edges);avg=np.array(s.volumes)/dx;Q=np.array(s.inventory)/dx[:,None]
    mesh=Mesh1D(s.edges,tuple(map(float,avg)),s.base_mesh.face_areas,s.base_mesh.perimeter)
    bulk=DuctState(mesh,tuple(tuple(map(float,row)) for row in Q),thermo)
    np.testing.assert_allclose(bulk.primitive().p,s.regional_states.p,rtol=2e-14,atol=0.)
    np.testing.assert_allclose(bulk.primitive().rho,s.regional_states.rho,rtol=5e-16,atol=0.)
    assert s.regional_states.p==pytest.approx((1e5,1e5),abs=1e-5)

def test_immutable_detached_state_and_restart(thermo):
    original=setup(thermo);rows=[list(row) for row in original.inventory];W=list(original.W);labels=list(original.labels)
    state=RegionalDuctState(original.geometry,original.base_mesh,W,rows,labels,thermo)
    rows[0][0]=0.;W[0]=-1.;labels[0]='changed'
    assert state.state_identity==original.state_identity
    with pytest.raises(FrozenInstanceError):state.labels=()
    with pytest.raises(TypeError):state.inventory[0][0]=0.
    payload=json.loads(json.dumps(state.to_restart()))
    restored=RegionalDuctState.from_restart(payload,thermo)
    assert restored.state_identity==state.state_identity
    assert restored.inventory==state.inventory and restored.W==state.W
    payload['inventory'][0][1]+=1.
    with pytest.raises(ValueContractError) as error:RegionalDuctState.from_restart(payload,thermo)
    assert error.value.code=='REGIONAL_RESTART_IDENTITY'

@pytest.mark.parametrize('field,value',[('labels',('renamed','N2')),('source_kind','UNKNOWN'),('component_order',tuple(reversed(COMPONENTS)))])
def test_identity_and_classification_bound(thermo,field,value):
    s=setup(thermo)
    if field=='labels':assert replace(s,labels=value).state_identity!=s.state_identity
    else:
        with pytest.raises(ValueContractError):replace(s,**{field:value})

def test_mixed_observable_is_regional_pressure_not_homogeneous_eos(thermo):
    s=setup(thermo,area=(1.,))
    data=[(600.,1e5,20.,(0.,0.,1.,0.,0.),(0.,0.,1.,0.)),(1800.,1e5,20.,(0.,0.,0.,1.,0.),(0.,0.,1.,0.))]
    state=RegionalDuctState.from_physical(s.geometry,s.base_mesh,(0.,.5,1.),data,('N2','CO2'),thermo)
    p=state.projection((0.,1.))
    assert p.pressure_volume_average[0]==pytest.approx(1e5,abs=1e-5)
    assert p.bulk_velocity[0]==pytest.approx(20.)
    row=p.inventory[0];mixed=thermo.invert_energy(row[0],row[2]/row[0]-.5*(row[1]/row[0])**2,p.chemical_mass_fractions[0])
    assert abs(mixed.p-p.pressure_volume_average[0])>100.
    assert p.inventory[0]==tuple(fsum(row[k] for row in state.inventory) for k in range(12))

def test_negative_formation_energy_is_admissible(thermo):
    s=setup(thermo);data=[(600.,1e5,0.,(0.,0.,0.,0.,1.),(0.,0.,1.,0.))]*2
    state=RegionalDuctState.from_physical(s.geometry,s.base_mesh,s.edges,data,('CO2','CO2'),thermo)
    assert state.integrated_inventory().total_energy<0.

def test_invalid_inventories_and_no_q_only_restart(thermo):
    s=setup(thermo);rows=[list(r) for r in s.inventory];rows[0][3]=-1.
    with pytest.raises(ValueContractError):replace(s,inventory=rows)
    with pytest.raises(ValueContractError):replace(s,W=(s.W[0],s.W[0],s.W[-1]))
    with pytest.raises(ValueContractError):RegionalDuctState.from_restart({'Q':s.projection().Q},thermo)

def test_unsupported_geometry_join_rejected(thermo):
    with pytest.raises(ValueContractError):CumulativeVolumeGeometry((PolynomialSegment(0.,.5,(1.,),(1.,)),PolynomialSegment(.5,1.,(1.,),(1.,))))

def test_ts004_derived_fractions_records_preserve_inventory(thermo):
    s=setup(thermo);rows=[list(r) for r in s.inventory];rows[0][5]*=1+8e-15;rows[0][10]*=1+8e-15
    state=replace(s,inventory=rows)
    assert state.inventory==tuple(map(tuple,rows))
    assert {r[1] for r in state.regional_states.roundoff_records}=={'/chemical','/tracers'}

@pytest.mark.parametrize('field,value',[('labels',None),('labels','AB'),('component_order',None),('inventory',None)])
def test_malformed_public_state_is_typed_failure(thermo,field,value):
    with pytest.raises(ValueContractError):replace(setup(thermo),**{field:value})

def test_projection_direct_construction_detaches_and_rejects_mutable_records(thermo):
    p=setup(thermo).projection();rows=[list(r) for r in p.inventory]
    q=replace(p,inventory=rows);rows[0][0]=0.
    assert q.inventory==p.inventory
    with pytest.raises(ValueContractError):replace(p,roundoff_records=((0,'/chemical',[]),))
    with pytest.raises(ValueContractError):replace(p,geometry_residuals=([1],)*len(p.W))

def test_state_identity_binds_geometry_and_recovery(thermo):
    s=setup(thermo);other=setup(thermo,area=(1.,))
    assert s.geometry.identity!=other.geometry.identity and s.state_identity!=other.state_identity
    p=s.to_restart();p['recovery_identity']='changed'
    with pytest.raises(ValueContractError):RegionalDuctState.from_restart(p,thermo)

def test_self_projection_preserves_signed_zero_bytes(thermo):
    s=setup(thermo);rows=[list(r) for r in s.inventory];rows[0][1]=-0.;rows[0][3]=-0.
    s=replace(s,inventory=rows)
    assert np.array(s.projection(s.edges).inventory).tobytes()==np.array(s.inventory).tobytes()

def test_explicit_fixture_classification_cannot_masquerade_as_gen1(thermo):
    # Protocol/identity test only; this delegate is not a scientific reference.
    class Delegate:
        source_kind='NUMERICAL_FIXTURE_ONLY'
        identity='SOFTWARE_PROTOCOL_TEST_NASA_DELEGATE'
        reference_sha256='a'*64
        def invert_energy(self,*args):return thermo.invert_energy(*args)
    s=setup(thermo)
    fixture=replace(s,thermo=Delegate(),source_kind='NUMERICAL_FIXTURE_ONLY')
    assert fixture.regional_states.states[0].source_kind=='NUMERICAL_FIXTURE_ONLY'
    assert fixture.state_identity!=s.state_identity
    with pytest.raises(ValueContractError):replace(fixture,source_kind='GEN1_RUNTIME')
    fixture.thermo.reference_sha256='invalid'
    with pytest.raises(ValueContractError):replace(fixture)

def test_recovery_must_retain_original_density(thermo):
    class BadRecovery:
        source_kind='NUMERICAL_FIXTURE_ONLY';identity='BAD_SOFTWARE_PROTOCOL_TEST';reference_sha256='b'*64
        def invert_energy(self,rho,e,Y):return thermo.invert_energy(rho*1.01,e,Y)
    with pytest.raises(ValueContractError):replace(setup(thermo),thermo=BadRecovery(),source_kind='NUMERICAL_FIXTURE_ONLY')
