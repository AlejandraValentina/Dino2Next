"""Successful exact-model memoization is a software optimization only."""
from dataclasses import FrozenInstanceError
from struct import pack
import numpy as np
import pytest
from dino2next.thermo import ThermoModel
from dino2next.units import ValueContractError
from .test_flux import nasa_kernel
from .conftest import primitive

Y=(0.,0.,1.,0.,0.)

def counter(monkeypatch):
    calls=[];original=ThermoModel.evaluate
    def evaluate(self,T,p,y):
        calls.append((id(self),pack('!7d',T,p,*y)))
        return original(self,T,p,y)
    monkeypatch.setattr(ThermoModel,'evaluate',evaluate)
    return calls


def test_exact_cache_hits_and_immutable_results(monkeypatch):
    k=nasa_kernel();calls=counter(monkeypatch)
    a=k._cached_thermo_call(False,700.,1e5,Y);b=k._cached_thermo_call(False,700.,1e5,Y)
    assert a is b and len(calls)==1 and len(k._thermo_cache)==1
    with pytest.raises(FrozenInstanceError):a.T=701.
    detached=a.to_mapping();detached['Y'][0]=1
    assert b.Y==Y


def test_cache_signed_zeros_and_neighbors_are_distinct(monkeypatch):
    k=nasa_kernel();calls=counter(monkeypatch)
    for y,T in ((Y,700.),((-0.,0.,1.,0.,0.),700.),(Y,float(np.nextafter(700.,np.inf)))):
        k._cached_thermo_call(False,T,1e5,y)
    assert len(calls)==3 and len(set(key for _,key in calls))==3


def test_cache_lru_eviction_is_bounded(monkeypatch):
    k=nasa_kernel();monkeypatch.setattr(k,'_THERMO_CACHE_LIMIT',2);calls=counter(monkeypatch)
    for T in (500.,600.,500.,700.,600.):
        k._cached_thermo_call(False,T,1e5,Y)
        assert len(k._thermo_cache)<=2
    assert len(calls)==4


def test_failures_are_reexecuted_and_never_cached(monkeypatch):
    k=nasa_kernel();calls=counter(monkeypatch);failures=[]
    for _ in range(2):
        with pytest.raises(ValueContractError) as exc:k._cached_thermo_call(False,299.,1e5,Y)
        failures.append((exc.value.code,exc.value.path,str(exc.value)))
    assert failures[0]==failures[1] and len(calls)==2 and len(k._thermo_cache)==0


def test_cache_is_per_kernel_and_bound_to_model_object(monkeypatch):
    k=nasa_kernel();other=nasa_kernel();calls=counter(monkeypatch)
    k._cached_thermo_call(False,700.,1e5,Y);other._cached_thermo_call(False,700.,1e5,Y)
    assert len(calls)==2
    k.thermo=other.thermo
    k._cached_thermo_call(False,700.,1e5,Y)
    assert len(calls)==3 and k._thermo_cache_model is other.thermo and len(k._thermo_cache)==1


def test_recovery_and_evaluation_have_separate_keys():
    k=nasa_kernel();a=k._cached_thermo_call(False,700.,1e5,Y)
    b=k._cached_thermo_call(True,a.rho,a.e,Y)
    assert b.diagnostic is not None and a.diagnostic is None
    assert {key[:1] for key in k._thermo_cache}=={b'E',b'I'}


def test_fixture_branch_does_not_allocate_or_call_nasa_cache(kernel,monkeypatch):
    def forbidden(*args,**kwargs):raise AssertionError('Fixture touched NASA cache')
    monkeypatch.setattr(kernel,'_cached_thermo_call',forbidden)
    assert not hasattr(kernel,'_thermo_cache')
    u=kernel.primitive_to_conservative(primitive(1.,0.,1e5,2))
    assert np.isfinite(kernel.recover(u).V).all()


def test_failed_inversions_are_not_cached(monkeypatch):
    k=nasa_kernel();original=ThermoModel.invert_energy;calls=[];failures=[]
    def invert(self,rho,e,y):
        calls.append((rho,e,y));return original(self,rho,e,y)
    monkeypatch.setattr(ThermoModel,'invert_energy',invert)
    for _ in range(2):
        with pytest.raises(ValueContractError) as exc:k._cached_thermo_call(True,1.,-1e30,Y)
        failures.append((exc.value.code,exc.value.path,str(exc.value)))
    assert len(calls)==2 and failures[0]==failures[1] and len(k._thermo_cache)==0


def test_concurrent_identical_calls_share_only_success(monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    k=nasa_kernel();calls=counter(monkeypatch)
    with ThreadPoolExecutor(max_workers=4) as executor:
        results=list(executor.map(lambda _:k._cached_thermo_call(False,700.,1e5,Y),range(16)))
    assert len(calls)==1 and all(result is results[0] for result in results)
