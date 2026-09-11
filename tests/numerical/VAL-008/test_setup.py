"""Analytical guard setup controls; no NASA candidate acceptance claim."""
from pathlib import Path
import importlib.util
import pytest
import numpy as np
from collections import deque
import runpy

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize('kind,ns,guards',[('contact',[100,200,400],[134,263,522]),('shock',[80,160,320,640],[45,86,167,330])])
def test_prescribed_guard_counts_preserve_original_window(kind,ns,guards):
    spec=importlib.util.spec_from_file_location('setup008',ROOT/'validation/fixtures/VAL-008/execution.py')
    obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj)
    fixture=obj.verify_fixture()
    end=.001 if kind=='contact' else .0002
    for n,expected in zip(ns,guards):
        mesh,m=obj.guarded_mesh(n,fixture['guard_speeds'][kind],end)
        assert m==expected and len(mesh.dx)==n+2*m
        assert mesh.cell_bounds[m]==0 and mesh.cell_bounds[m+n]==1
        assert sum(mesh.dx[m:m+n])==pytest.approx(1,abs=2e-15)


@pytest.mark.parametrize('limited',[False,True])
def test_identity_mapper_tail_contains_selected_second_euler_state(limited):
    helpers=runpy.run_path(str(ROOT/'tests/contract/s06/test_step_transaction.py'))
    from dino2next.numerics import NumericalKernel,FaceFluxes,StageRHS
    k=NumericalKernel(helpers['GammaFixture'](),source_kind='NUMERICAL_FIXTURE_ONLY')
    initial=helpers['initial'](k); tail=deque(maxlen=3)
    def mapper(q,t):tail.append(q);return q
    def rhs(q,t):
        n=len(q.Q); high=np.zeros((n+1,12)); low=np.zeros_like(high)
        if t>0:
            rate=1e5 if limited else .01
            high[1,[0,5,11]]=rate
            high[1,2]=rate*q.Q[0,2]/q.Q[0,0]
        return StageRHS(FaceFluxes(high,low,np.zeros(n+1,bool),True),np.zeros_like(q.Q))
    result=k.propose_step(initial,rhs,0.,.001,trial_state_mapper=mapper,initial_Z=initial.Q)
    plain=k.propose_step(initial,rhs,0.,.001)
    assert result.accepted and plain.accepted and len(tail)==3
    np.testing.assert_array_equal(result.state.Q,plain.state.Q)
    np.testing.assert_array_equal(tail[1],result.state.Q)
    np.testing.assert_array_equal(tail[2],result.state.Q)
    np.testing.assert_array_equal((initial.Q+tail[0])/2,result.state.Q)
    theta=[r[3] for r in result.diagnostics if r[0]=='stage'][1]
    assert (0<theta<1) if limited else theta==1
