"""Unsplit mapped-stage guard and immutable transaction interface tests."""

from dataclasses import replace
from pathlib import Path
import runpy

import numpy as np
import pytest

from dino2next.numerics import NumericalKernel, FaceFluxes, StageRHS, StepAttempt, KernelState, PrimitiveBatch
from dino2next.units import ValueContractError

helpers=runpy.run_path(str(Path(__file__).resolve().parents[2]/"unit/s06/conftest.py"))
GammaFixture,mesh,primitive=(helpers[k] for k in ("GammaFixture","mesh","primitive"))


@pytest.fixture
def kernel():
    return NumericalKernel(GammaFixture(),source_kind="NUMERICAL_FIXTURE_ONLY")


def initial(kernel,n=4):
    return kernel.state(mesh(n),kernel.primitive_to_conservative(primitive(1,0,1e5,n)))


def zero_rhs(state,time):
    n=len(state.Q);zero=np.zeros((n+1,12))
    return StageRHS(FaceFluxes(zero,zero,np.zeros(n+1,bool),True),np.zeros_like(state.Q))


def test_step_snapshot_and_callback_are_read_only(kernel):
    state=initial(kernel)
    original=state.Q.copy()
    seen=[]
    def rhs(q,t):
        with pytest.raises(ValueError):q.Q[0,0]=9
        with pytest.raises(ValueError):q.Q.setflags(write=True)
        seen.append(t)
        return zero_rhs(q,t)
    attempt=kernel.propose_step(state,rhs,0.,.001)
    assert attempt.accepted and seen==[0.,.001]
    np.testing.assert_array_equal(attempt.state.Q,original)
    np.testing.assert_array_equal(state.Q,original)
    assert np.all(attempt.face_integrals==0) and np.all(attempt.source_integrals==0)
    with pytest.raises(ValueError):attempt.face_integrals.setflags(write=True)


def test_affine_prescribed_mapping_uses_endpoint_once_and_final_Z_combination(kernel):
    state=initial(kernel)
    b=np.zeros_like(state.Q);b[:,4]=.4;b[:,5]=-.4
    times=[]
    def mapper(Z,t):
        with pytest.raises(ValueError):Z.setflags(write=True)
        times.append(t)
        return Z+t*b
    result=kernel.propose_step(state,zero_rhs,0.,.2,trial_state_mapper=mapper,initial_Z=state.Q)
    assert result.accepted
    np.testing.assert_allclose(result.state.Q,state.Q+.2*b,rtol=0,atol=1e-15)
    np.testing.assert_array_equal(result.state.Q[:,2],state.Q[:,2])
    assert times[0]==0 and times.count(.2)>=4
    assert np.all(result.source_integrals==0)  # Reaction mapping is not an energy source.
    with pytest.raises(ValueContractError):
        kernel.propose_step(state,zero_rhs,0.,.2,trial_state_mapper=mapper)


def test_low_order_failure_rejects_whole_attempt_without_publishing_ledgers(kernel):
    state=initial(kernel);before=state.Q.copy()
    def rhs(q,t):
        result=zero_rhs(q,t)
        sources=np.zeros_like(q.Q);sources[:,2]=-1e12
        return StageRHS(result.fluxes,sources)
    attempt=kernel.propose_step(state,rhs,0.,.001)
    assert not attempt.accepted
    assert attempt.rejection=="LOW_ORDER_STAGE_INADMISSIBLE_RETRY_DT"
    assert attempt.face_integrals is None and attempt.source_integrals is None
    np.testing.assert_array_equal(state.Q,before)


def test_single_shared_guard_theta_preserves_all_conserved_columns(kernel):
    state=initial(kernel)
    count=0
    def rhs(q,t):
        nonlocal count
        count+=1
        n=len(q.Q);H=np.zeros((n+1,12));L=np.zeros_like(H)
        if count==1:
            # One interface would drain the left cell's full mass/chemistry/tags.
            H[1,[0,5,11]]=1e5
            H[1,2]=1e5*q.Q[0,2]/q.Q[0,0]
        return StageRHS(FaceFluxes(H,L,np.zeros(n+1,bool),True),np.zeros_like(q.Q))
    attempt=kernel.propose_step(state,rhs,0.,.001)
    assert attempt.accepted
    stage=[x for x in attempt.diagnostics if x[0]=="stage"]
    assert 0<stage[0][3]<1
    before=np.sum(state.Q*np.asarray(state.mesh.dx)[:,None],axis=0)
    after=np.sum(attempt.state.Q*np.asarray(state.mesh.dx)[:,None],axis=0)
    np.testing.assert_allclose(after,before,rtol=2e-14,atol=1e-10)
    np.testing.assert_array_equal(attempt.state.Q[:,0],attempt.state.Q[:,5])
    np.testing.assert_array_equal(attempt.state.Q[:,0],attempt.state.Q[:,11])


def test_guard_explicitly_checks_mapped_final_combination(kernel):
    state=initial(kernel,2)
    calls=[]
    # Software fault injection models a nonconvex admissibility set. Production
    # EOS remains unchanged; this verifies final combinations are not skipped.
    real_admissible=kernel.admissible
    energy0=state.Q[0,2]
    def admissible(U):
        calls.append(U.copy())
        ratio=U[0,2]/energy0
        return real_admissible(U) and not (1.04<ratio<1.06)
    kernel.admissible=admissible
    def rhs(q,t):
        base=zero_rhs(q,t);sources=np.zeros_like(q.Q)
        if t>0:sources[:,2]=.1*energy0
        return StageRHS(base.fluxes,sources)
    result=kernel.propose_step(state,rhs,0.,1.)
    assert not result.accepted
    # Q2=1.1U passes, physical final=1.05U is the rejected state.
    assert any(np.isclose(q[0,2]/energy0,1.05) for q in calls)
    assert result.rejection=="LOW_ORDER_STAGE_INADMISSIBLE_RETRY_DT"


def test_step_attempt_exclusivity_and_boundary_pair_contract(kernel):
    state=initial(kernel)
    with pytest.raises(ValueContractError):StepAttempt(None,None,())
    with pytest.raises(ValueContractError):StepAttempt(state,"failure",())
    with pytest.raises(ValueContractError):StepAttempt(None,"failure",(),np.zeros((1,12)))
    H=np.zeros((5,12));L=H.copy();H[0,0]=1
    with pytest.raises(ValueContractError):FaceFluxes(H,L,np.zeros(5,bool),True)
    with pytest.raises(ValueContractError):
        kernel.propose_step(KernelState(state.mesh,state.Q,"NUMERICAL_FIXTURE_ONLY","different"),zero_rhs,0.,.01)


def test_reconstruction_limiter_records_reach_step_attempt(kernel):
    state=initial(kernel,8)
    def rhs(q,t):
        faces=kernel.reconstruct(q)
        flux=kernel.interior_flux(faces)
        return StageRHS(flux,np.zeros_like(q.Q))
    attempt=kernel.propose_step(state,rhs,0.,1e-5)
    assert attempt.accepted
    assert sum(d[:3]==("rhs",1,"reconstruction_contraction") for d in attempt.diagnostics)==1
    assert sum(d[:3]==("rhs",2,"flux_b_faces") for d in attempt.diagnostics)==1


def test_nonhyperbolic_secant_diagnostic_survives_rejection():
    class InvalidSecantFixture(GammaFixture):
        def species_properties_batch(self,T):
            values=super().species_properties_batch(T)
            values["cv"]=-values["cv"]  # Explicit fault injection, not a valid reference model.
            return values
    kernel=NumericalKernel(InvalidSecantFixture(),source_kind="NUMERICAL_FIXTURE_ONLY")
    state=initial(kernel)
    def rhs(q,t):
        kernel.secant_action(q.Q,q.Q,np.zeros_like(q.Q))
        return zero_rhs(q,t)
    attempt=kernel.propose_step(state,rhs,0.,.001)
    assert attempt.rejection=="ROE_SECANT_NONHYPERBOLIC"
    metadata=[d for d in attempt.diagnostics if d[0]=="failure_metadata"][0][1]
    assert any(key=="denominator" and all(x<0 for x in values) for key,values in metadata)


def test_oversized_scalar_has_typed_failure(kernel):
    state=initial(kernel)
    for time,dt in ((10**1000,.01),(0.,10**1000)):
        with pytest.raises(ValueContractError) as exc:
            kernel.propose_step(state,zero_rhs,time,dt)
        assert exc.value.code=="STAGE_INADMISSIBLE"


def test_primitive_diagnostic_sequences_are_deeply_immutable(kernel):
    batch=kernel.recover(initial(kernel).Q)
    nested=[[0,"diagnostic",["immutable",1.]]]
    result=replace(batch,roundoff_records=nested)
    nested[0][2][1]=42.
    assert result.roundoff_records==((0,"diagnostic",("immutable",1.)),)
