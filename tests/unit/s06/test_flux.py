from pathlib import Path
import numpy as np
import pytest

from dino2next.numerics import NumericalKernel
from dino2next.thermo import ThermoDataset, ThermoModel, DERIVED_SHA256, RAW_SHA256, TRANSPORT_SHA256, GENERATOR_SHA256
from dino2next.units import ValueContractError
from .conftest import mesh, primitive


def test_consistent_hllc_flux_and_stationary_contact(kernel):
    L=kernel.primitive_to_conservative(primitive(1,0,1e5))
    R=kernel.primitive_to_conservative(primitive(2,0,1e5))
    flux=kernel.hllc(L,R)
    expected=np.zeros((1,12));expected[:,1]=1e5
    np.testing.assert_allclose(flux,expected,rtol=1e-14,atol=1e-10)
    np.testing.assert_array_equal(kernel.hllc(L,L),kernel.physical_flux(L))


@pytest.mark.parametrize("u",[1500.,-1500.])
def test_hllc_supersonic_selects_correct_donor(kernel,u):
    L=kernel.primitive_to_conservative(primitive(1,u,1e5))
    R=kernel.primitive_to_conservative(primitive(2,u,2e5))
    np.testing.assert_array_equal(kernel.hllc(L,R),kernel.physical_flux(L if u>0 else R))


def test_secant_flux_difference_and_absolute_acoustic_eigenvectors(kernel):
    L=kernel.primitive_to_conservative(primitive(1,20,1e5))
    R=kernel.primitive_to_conservative(primitive(2,50,1.5e5))
    np.testing.assert_allclose(kernel.secant_action(L,R,R-L),kernel.physical_flux(R)-kernel.physical_flux(L),rtol=1e-12,atol=1e-7)
    base=kernel.recover(L);a=base.a[0];H=(L[0,2]+1e5)
    acoustic=np.array([[1,20+a,H+20*a,0,0,1,0,0,0,0,0,1]])
    np.testing.assert_allclose(kernel.secant_action(L,L,acoustic,absolute=True),abs(20+a)*acoustic,rtol=1e-12,atol=1e-7)


def test_selected_flux_b_and_physical_boundary_fluxes(kernel):
    n=12;V=primitive(1,np.where(np.arange(n)<6,100,0),np.where(np.arange(n)<6,4e5,1e5),n)
    U=kernel.primitive_to_conservative(V)
    state=kernel.state(mesh(n),U)
    faces=kernel.reconstruct(state,boundary="physical",ghosts=(np.repeat(U[:1],4,axis=0),np.repeat(U[-1:],4,axis=0)))
    physical=(kernel.physical_flux(U[:1])[0],kernel.physical_flux(U[-1:])[0])
    fluxes=kernel.interior_flux(faces,boundary_flux=physical)
    assert np.any(fluxes.flux_b[1:-1])
    assert not fluxes.flux_b[0] and not fluxes.flux_b[-1]
    np.testing.assert_array_equal(fluxes.high[[0,-1]],physical)
    np.testing.assert_array_equal(fluxes.low[[0,-1]],physical)


def test_flux_b_selection_never_evaluates_unused_hllc_star_states(kernel,monkeypatch):
    n=20
    V=primitive(1,np.where(np.arange(n)<10,100,0),np.where(np.arange(n)<10,4e5,1e5),n)
    U=kernel.primitive_to_conservative(V)
    faces=kernel.reconstruct(kernel.state(mesh(n),U),boundary="physical",
                             ghosts=(np.repeat(U[:1],4,axis=0),np.repeat(U[-1:],4,axis=0)))
    expected=np.zeros(n+1,bool)
    expected[1:-1]=~(faces.near[:-1]|faces.near[1:])
    calls=[]
    actual_hllc=kernel.hllc
    def only_unselected(left,right):
        calls.append(len(left))
        np.testing.assert_array_equal(left,faces.left[expected])
        np.testing.assert_array_equal(right,faces.right[expected])
        return actual_hllc(left,right)
    monkeypatch.setattr(kernel,"hllc",only_unselected)
    fluxes=kernel.interior_flux(faces,boundary_flux=(np.zeros(12),np.zeros(12)))
    assert np.any(fluxes.flux_b) and sum(calls)==np.count_nonzero(expected)


def nasa_kernel():
    root=Path(__file__).resolve().parents[3];data=root/"docs/science/C1.0/datasets"
    thermo=ThermoModel(ThermoDataset.from_files(data/"thermo_runtime_continuous_v1.json",data/"thermo_species.json",
        data/"thermo_transport.yaml",root/"research/bcr_s03_nasa_inversion/generate.py",
        expected_sha256=DERIVED_SHA256,expected_raw_sha256=RAW_SHA256,
        expected_transport_sha256=TRANSPORT_SHA256,expected_generator_sha256=GENERATOR_SHA256))
    return NumericalKernel(thermo)


def test_full_nasa_mixed_species_secant_retains_formation():
    kernel=nasa_kernel()
    thermo=kernel.thermo
    states=[]
    for T,p,u,Y in ((700,1e5,30,(0,.23,.77,0,0)),(1600,2e5,-10,(0,.1,.7,.1,.1))):
        props=thermo.evaluate(T,p,Y)
        V=np.array([[props.rho,u,p,*Y,0,0,1,0]])
        states.append(kernel.primitive_to_conservative(V))
    L,R=states
    delta_flux=kernel.physical_flux(R)-kernel.physical_flux(L)
    action=kernel.secant_action(L,R,R-L)
    np.testing.assert_allclose(action,delta_flux,rtol=1e-10,atol=2e-5)
    assert R[0,2]<0


def test_unchanged_nasa_endpoint_faces_reuse_original_conserved_state():
    from dino2next.gasdynamics import DuctState
    kernel=nasa_kernel()
    for p in (5e4,1e5):
        props=kernel.thermo.evaluate(300,p,(0,0,1,0,0))
        U=np.array([[props.rho,0,props.rho*props.e,0,0,props.rho,0,0,0,0,0,props.rho]]*4)
        duct=DuctState(mesh(4),tuple(tuple(map(float,row)) for row in U),kernel.thermo)
        faces=kernel.reconstruct(duct)
        np.testing.assert_array_equal(faces.left,np.repeat(U[:1],5,axis=0))
        np.testing.assert_array_equal(faces.right,np.repeat(U[:1],5,axis=0))
