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
