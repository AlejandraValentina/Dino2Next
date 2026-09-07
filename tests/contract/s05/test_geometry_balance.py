from dataclasses import FrozenInstanceError,replace
from math import fsum
from pathlib import Path
from hashlib import sha256

import pytest

from dino2next.geometry import GeometryModel,CrankGeometry,PassageSamples
from dino2next.gasdynamics import Mesh1D,PolynomialSegment,DuctState
from dino2next.thermo import ThermoDataset,ThermoModel
from dino2next.units import ValueContractError


def thermo():
    root=Path(__file__).resolve().parents[3]
    base=root/'docs/science/C1.0/datasets'
    paths=[base/'thermo_runtime_continuous_v1.json',base/'thermo_species.json',
           base/'thermo_transport.yaml',root/'research/bcr_s03_nasa_inversion/generate.py']
    hashes=[sha256(p.read_bytes()).hexdigest() for p in paths]
    return ThermoModel(ThermoDataset.from_files(*paths,expected_sha256=hashes[0],
        expected_raw_sha256=hashes[1],expected_transport_sha256=hashes[2],expected_generator_sha256=hashes[3]))


def test_nonlinear_declared_area_integrates_exactly_across_aligned_knots():
    # First A=1+x², second A=1.25+0.5xi+0.25xi² (same global law).
    shapes=(PolynomialSegment(0,.5,(1,0,.25),(4,)),
            PolynomialSegment(.5,1,(1.25,.5,.25),(4,)))
    mesh=Mesh1D.from_segments((0,.25,.5,.75,1),shapes)
    for left,right,average in zip(mesh.cell_bounds,mesh.cell_bounds[1:],mesh.area_averages):
        independent=(right-left)+(right**3-left**3)/3
        assert average*(right-left)==pytest.approx(independent,rel=2e-15)
    assert fsum(mesh.cell_volumes)==pytest.approx(4/3,rel=2e-15)
    assert mesh.face_areas==pytest.approx(tuple(1+x*x for x in mesh.cell_bounds),rel=2e-15)
    assert mesh.perimeter==(4,4,4,4)
    assert shapes[0].integral(.1,.4)==pytest.approx(.3+(.4**3-.1**3)/3,rel=2e-15)
    spanning=shapes[0].integral(.25,.5)+shapes[1].integral(.5,.75)
    assert spanning==pytest.approx(.5+(.75**3-.25**3)/3,rel=2e-15)
    with pytest.raises(ValueContractError):Mesh1D.from_segments((0,1/3,2/3,1),shapes)


def test_cubic_and_high_degree_are_explicit_inputs():
    shape=PolynomialSegment(0,2,(1,2,0,3,0,1),(4,1))
    assert shape.integral(0,2)==pytest.approx(2*(1+1+3/4+1/6),rel=2e-15)
    assert shape.integral(0,2,perimeter=True)==9
    assert shape.value(2)==7
    with pytest.raises(ValueContractError):shape.value(2.0001)
    with pytest.raises(FrozenInstanceError):shape.left=1


def test_positive_geometry_certificate_detects_interior_failure():
    with pytest.raises(ValueContractError):PolynomialSegment(0,1,(1,-8,8),(4,))
    # Positive despite negative coarse Bernstein bound; subdivision certifies it.
    shape=PolynomialSegment(0,1,(.3,-1,1),(4,))
    assert shape.value(.5)>0


def test_rest_momentum_flux_geometry_balance_without_a_face_solver():
    model=thermo()
    shape=PolynomialSegment(0,1,(1.1,-.4,.4),(4,))
    mesh=Mesh1D.from_segments(tuple(i/16 for i in range(17)),(shape,))
    state=model.evaluate(700,120000,(0,0,1,0,0))
    q=tuple(tuple(a*v for v in (state.rho,0,state.rho*state.e,0,0,state.rho,0,0,0,0,state.rho,0))
            for a in mesh.area_averages)
    duct=DuctState(mesh,q,model)
    pressures=duct.primitive().p
    source=duct.geometry_source()
    for i,(p,s,dx) in enumerate(zip(pressures,source,mesh.dx)):
        flux_difference=(mesh.face_areas[i+1]*p-mesh.face_areas[i]*p)/dx
        scale=(abs(mesh.face_areas[i+1]*p)+abs(mesh.face_areas[i]*p))/dx
        assert abs(flux_difference-s)<=128*2.220446049250313e-16*scale
    assert duct.Q==q
    assert fsum(s*dx for s,dx in zip(source,mesh.dx))==pytest.approx(0,abs=1e-8)


def test_geometry_model_binding_and_count_are_not_collapsed():
    samples=PassageSamples('transfer',(0,1),(1,2),(4,5),3,'PER_PASSAGE')
    geometry=GeometryModel(CrankGeometry(.05,.04,.08,8e-6,150e-6),(samples,),(), 'a'*64)
    shape=PolynomialSegment(0,1,(1,1),(4,1))
    mesh=Mesh1D.from_geometry(geometry,'transfer',(0,.5,1),segments=(shape,))
    assert fsum(mesh.cell_volumes)==1.5
    assert mesh.replication_count==3 and mesh.config_hash=='a'*64
    assert samples.areas==(1,2)
    with pytest.raises(ValueContractError):Mesh1D.from_geometry(geometry,'transfer',(0,1),segments=())
    with pytest.raises(ValueContractError):Mesh1D.from_geometry(geometry,'absent',(0,1),segments=(shape,))
    aggregate=replace(samples,area_basis='AGGREGATE')
    with pytest.raises(ValueContractError):Mesh1D.from_geometry(replace(geometry,passages=(aggregate,)),'transfer',(0,1),segments=(shape,))
    with pytest.raises(ValueContractError):Mesh1D.from_geometry(geometry,'transfer',(0,1),segments=(PolynomialSegment(0,1,(1,2),(4,1)),))


@pytest.mark.parametrize('changes',[
    {'cell_bounds':(0,0,1)},{'cell_bounds':(0,.1,1)},
    {'area_averages':(0,1)},{'face_areas':(1,1)}, {'perimeter':(4,-1)},
    {'segment_boundaries':(.25,)},{'component_id':''},{'replication_count':True},
    {'area_averages':(float('inf'),1)}, {'cell_bounds':(0,True,1)},
])
def test_bad_mesh_is_not_repaired(changes):
    values=dict(cell_bounds=(0,.5,1),area_averages=(1,1),face_areas=(1,1,1),perimeter=(4,4))
    values.update(changes)
    with pytest.raises(ValueContractError) as error:Mesh1D(**values)
    assert error.value.code in ('MESH_NONCONFORMING','GEOMETRY_INVALID')


def test_segment_grid_and_shape_identity():
    mesh=Mesh1D((0,.1,.2,.6,1),(1,1,1,1),(1,1,1,1,1),(4,4,4,4),(.2,))
    assert len(mesh.dx)==4
    shape=PolynomialSegment(0,1,(1,),(4,))
    bound=Mesh1D.from_segments((0,.5,1),(shape,))
    with pytest.raises(ValueContractError):replace(bound,area_averages=(1,2))
    with pytest.raises(ValueContractError):Mesh1D.from_segments((0,1),(PolynomialSegment(0,.5,(1,),(4,)),))
