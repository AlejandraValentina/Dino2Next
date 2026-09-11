from dataclasses import FrozenInstanceError
import numpy as np
import pytest

from dino2next.numerics import NumericalProfile, minmod, mc
from dino2next.units import ValueContractError
from .conftest import mesh, primitive


def test_profile_is_frozen_and_cannot_select_alternative_recipe():
    profile=NumericalProfile()
    with pytest.raises(FrozenInstanceError):profile.acoustic_cfl=.3
    with pytest.raises(ValueContractError) as exc:NumericalProfile(compression_threshold=.34)
    assert exc.value.code=="SCIENTIFIC_CHANGE_REQUIRED"


def test_local_characteristic_roundtrip_and_dependent_slopes(kernel):
    V=primitive([1,2],[-20,30],[1e5,2e5],2)
    a=np.array([350.,360.])
    delta=np.zeros((2,12)); delta[:,:3]=[[.1,2,30],[-.2,-1,40]]
    delta[:,3]=.02;delta[:,5]=-.02;delta[:,8]=.03;delta[:,11]=-.03
    amplitudes=kernel._project(delta,V,a)
    restored=kernel._unproject(amplitudes,V,a)
    np.testing.assert_allclose(restored,delta,rtol=1e-14,atol=1e-14)
    assert np.all(np.sum(restored[:,3:8],axis=1)==0)
    assert np.all(np.sum(restored[:,8:],axis=1)==0)


def test_minmod_and_mc_sign_and_amplitude():
    a=np.array([1.,-2.,1.,0.]);b=np.array([3.,-3.,-1.,2.])
    np.testing.assert_array_equal(minmod(a,b),[1,-2,0,0])
    np.testing.assert_array_equal(mc(a,b),[2,-2.5,0,0])


def test_uniform_state_reconstruction_and_immutable_arrays(kernel):
    V=primitive(1.,20.,1e5,8)
    U=kernel.primitive_to_conservative(V)
    state=kernel.state(mesh(8),U)
    faces=kernel.reconstruct(state)
    np.testing.assert_allclose(faces.left,np.repeat(U[:1],9,axis=0))
    np.testing.assert_allclose(faces.right,np.repeat(U[:1],9,axis=0))
    assert not np.any(faces.near)
    assert np.all(faces.contraction==1)
    for array in (state.Q,faces.left,faces.near):
        with pytest.raises(ValueError):array.setflags(write=True)
    U[0,0]=50
    assert state.Q[0,0]==1


def test_radius_two_sensor_and_flattening_match_explicit_stencil(kernel):
    n=15
    pressure=np.where(np.arange(n)<7,4e5,1e5)
    velocity=np.where(np.arange(n)<7,100.,0.)
    V=primitive(1.,velocity,pressure,n)
    faces=kernel.reconstruct(kernel.state(mesh(n),kernel.primitive_to_conservative(V)))
    strong=[]; chi=[]
    for i in range(n):
        J=abs(pressure[(i+1)%n]-pressure[(i-1)%n])
        W=abs(pressure[(i+2)%n]-pressure[(i-2)%n])
        value=W>0 and J/min(pressure[(i-1)%n],pressure[(i+1)%n])>.33 and velocity[(i-1)%n]>velocity[(i+1)%n]
        strong.append(value)
        chi.append(max(0,min(1,10*(J/W-.75))) if value else 0)
    expected=[any(strong[(i+j)%n] for j in range(-2,3)) for i in range(n)]
    flatten=[1-max(chi[(i+j)%n] for j in (-1,0,1)) for i in range(n)]
    np.testing.assert_array_equal(faces.near,expected)
    np.testing.assert_array_equal(faces.flattening,flatten)


def test_explicit_physical_ghosts_and_faces_admissible(kernel):
    V=primitive(1.,0.,1e5,6)
    V[:,3]=np.linspace(0,1,6);V[:,5]=1-V[:,3]
    U=kernel.primitive_to_conservative(V)
    state=kernel.state(mesh(6),U)
    with pytest.raises(ValueContractError):kernel.reconstruct(state,boundary="physical")
    faces=kernel.reconstruct(state,boundary="physical",ghosts=(np.repeat(U[:1],4,axis=0),np.repeat(U[-1:],4,axis=0)))
    assert kernel.admissible(faces.left) and kernel.admissible(faces.right)
    assert np.min(faces.left[:,3:])>=0


def test_joint_contraction_preserves_inputs_and_both_simplexes(kernel):
    rng=np.random.default_rng(8124)
    V=primitive(1.,0.,1e5,32)
    V[:,3:8]=rng.dirichlet(np.full(5,.2),size=32)
    V[:,8:]=rng.dirichlet(np.full(4,.2),size=32)
    U=kernel.primitive_to_conservative(V)
    state=kernel.state(mesh(32),U);before=state.Q.copy()
    faces=kernel.reconstruct(state)
    assert np.any(faces.contraction<1)
    assert kernel.admissible(faces.left) and kernel.admissible(faces.right)
    np.testing.assert_array_equal(state.Q,before)
def test_acoustic_acceptance_rejects_unqualified_l2_even_when_l1_is_second_order():
    """Regression for VAL-009's omitted density/velocity L2 order gate."""
    import importlib.util
    from pathlib import Path
    root=Path(__file__).resolve().parents[3]
    spec=importlib.util.spec_from_file_location('s06_metric_guard',root/'validation/fixtures/VAL-006/assessment.py')
    metrics=importlib.util.module_from_spec(spec);spec.loader.exec_module(metrics)
    rows=[{'max_L1':[4.**(-i),4.**(-i)],'max_L2':[2.**(-1.75*i),2.**(-1.75*i)]} for i in range(4)]
    import pytest
    with pytest.raises(AssertionError,match='L2'):
        metrics.require_smooth_orders(metrics.smooth_orders(rows),1.8)
    for row in rows:
        row['max_L2']=row['max_L1']
    metrics.require_smooth_orders(metrics.smooth_orders(rows),1.8)

@pytest.mark.parametrize('differences,expected',[
    ((2.6,.6,-1.4,-3.4),-.4),  # displaced quadratic maximum; MC would erase slope
    ((-2.6,-.6,1.4,3.4),.4),  # displaced quadratic minimum
    ((0.,1.,-1.,0.),0.),       # zero centered derivative
    ((1.,0.,2.,3.),0.),       # detector equality retains ordinary MC
    ((1.,1.,2.,3.),1.5),       # monotone region retains MC
])
def test_sv009_acoustic_quadratics_and_detector_equality(kernel,monkeypatch,differences,expected):
    n=6;U=kernel.primitive_to_conservative(primitive(1.,0.,1e5,n))
    dmm,dm,dp,dpp=differences
    values=[]
    for value in (dm,dp,dmm,dpp):
        row=np.full((n,12),value);values.append(row)
    calls=iter(values);captured=[]
    monkeypatch.setattr(kernel,'_project',lambda *args:next(calls))
    def capture(amplitudes,*args):
        captured.append(amplitudes.copy());return np.zeros_like(amplitudes)
    monkeypatch.setattr(kernel,'_unproject',capture)
    faces=kernel.reconstruct(kernel.state(mesh(n),U))
    for family in (0,2):np.testing.assert_allclose(captured[0][:,family],expected,atol=1e-15)
    material=[1,*range(3,12)]
    np.testing.assert_array_equal(captured[0][:,material],mc(np.full((n,10),dm),np.full((n,10),dp)))
    if min(dm*dp,dmm*dpp)>=0:assert faces.acoustic_extrema==()


def test_sv009_four_differences_use_common_center_basis_and_physical_ghosts(kernel,monkeypatch):
    n=8;V=primitive(np.linspace(1.,1.2,n),np.linspace(-5,7,n),1e5+100*np.cos(np.arange(n)),n)
    U=kernel.primitive_to_conservative(V)
    left=np.repeat(U[:1],4,axis=0);right=np.repeat(U[-1:],4,axis=0)
    left[-2,1]-=.5;right[1,1]+=.3
    state=kernel.state(mesh(n),U);calls=[];actual=kernel._project
    def project(delta,center,a):
        calls.append((delta.copy(),center.copy(),a.copy()));return actual(delta,center,a)
    monkeypatch.setattr(kernel,'_project',project)
    faces=kernel.reconstruct(state,boundary='physical',ghosts=(left,right))
    assert len(calls)==4
    ext=kernel.recover(np.concatenate((left,U,right))).V
    expected=[ext[4:4+n]-ext[3:3+n],ext[5:5+n]-ext[4:4+n],ext[3:3+n]-ext[2:2+n],ext[6:6+n]-ext[5:5+n]]
    for (delta,center,a),wanted in zip(calls,expected):
        np.testing.assert_array_equal(delta,wanted)
        np.testing.assert_array_equal(center,calls[0][1]);np.testing.assert_array_equal(a,calls[0][2])
    assert kernel.admissible(faces.left) and kernel.admissible(faces.right)


def test_sv009_compression_uses_original_acoustic_minmod_and_material_mc(kernel,monkeypatch):
    n=20;x=np.arange(n);V=primitive(1+.01*np.cos(x),np.where(x<10,100.,0.),np.where(x<10,4e5,1e5),n)
    U=kernel.primitive_to_conservative(V);state=kernel.state(mesh(n),U)
    actual_project=kernel._project;actual_unproject=kernel._unproject;projected=[];limited=[]
    def project(*args):
        result=actual_project(*args);projected.append(result.copy());return result
    def unproject(a,*args):limited.append(a.copy());return actual_unproject(a,*args)
    monkeypatch.setattr(kernel,'_project',project);monkeypatch.setattr(kernel,'_unproject',unproject)
    faces=kernel.reconstruct(state)
    assert np.any(faces.near) and np.any(faces.flattening<1)
    for k in (0,2):np.testing.assert_array_equal(limited[0][faces.near,k],minmod(projected[0][faces.near,k],projected[1][faces.near,k]))
    material=[1,*range(3,12)]
    np.testing.assert_array_equal(limited[0][:,material],mc(projected[0][:,material],projected[1][:,material]))
    assert all(not faces.near[i] for i,k,old,new in faces.acoustic_extrema)
    assert np.any(kernel.interior_flux(faces).flux_b)


def test_sv009_diagnostics_are_immutable_and_propagate_to_flux(kernel):
    from dataclasses import replace
    n=12;V=primitive(1.,0.,1e5+100*np.cos(2*np.pi*(np.arange(n)+.2)/n),n)
    faces=kernel.reconstruct(kernel.state(mesh(n),kernel.primitive_to_conservative(V)))
    assert faces.acoustic_extrema and {row[1] for row in faces.acoustic_extrema}<={0,2}
    mutable=[list(row) for row in faces.acoustic_extrema]
    detached=replace(faces,acoustic_extrema=mutable);mutable[0][0]=-123
    assert detached.acoustic_extrema==faces.acoustic_extrema
    flux=kernel.interior_flux(faces)
    assert dict(flux.diagnostics)['acoustic_extrema']==faces.acoustic_extrema
    assert NumericalProfile().contract=='C1.0-R4 NK-001..004 TS-001 SV-009'
    with pytest.raises(ValueContractError):NumericalProfile(contract='C1.0-R3 NK-001..004 TS-001')
