"""Explicit mathematical fixture adapter for isolated kernel unit tests."""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import numpy as np
import pytest

from dino2next.gasdynamics import Mesh1D
from dino2next.numerics import NumericalKernel
from dino2next.units import ValueContractError


@dataclass(frozen=True)
class GammaFixture:
    source_kind: str = "NUMERICAL_FIXTURE_ONLY"
    identity: str = "UNIT_TEST_ONLY_GAMMA_1.4_R287"
    reference_sha256: str = sha256(Path(__file__).read_bytes()).hexdigest()

    def evaluate_batch(self,rho,p,Y):
        T=p/(rho*287)
        return self._values(T,p)

    def recover_batch(self,rho,e,Y):
        T=e/(287/.4)
        return self._values(T,rho*287*T)

    def _values(self,T,p):
        if np.any(T<=0) or np.any(p<=0):
            raise ValueContractError("EOS_OUT_OF_DOMAIN","/T","Mathematical fixture domain")
        return dict(T=T,p=p,e=T*(287/.4),cp=np.full_like(T,287*1.4/.4),
                    cv=np.full_like(T,287/.4),R=np.full_like(T,287),a=np.sqrt(1.4*287*T))

    def species_properties_batch(self,T):
        return {"e":np.repeat((T*(287/.4))[:,None],5,axis=1),
                "cv":np.full((len(T),5),287/.4),"R":np.full((len(T),5),287.)}


@pytest.fixture
def kernel():
    return NumericalKernel(GammaFixture(),source_kind="NUMERICAL_FIXTURE_ONLY")


def mesh(n):
    return Mesh1D(tuple(map(float,np.linspace(0,1,n+1))),(1.,)*n,(1.,)*(n+1),(4.,)*n)


def primitive(rho,u,p,n=1):
    V=np.zeros((n,12))
    V[:,0]=rho; V[:,1]=u; V[:,2]=p
    V[:,5]=1; V[:,11]=1
    return V
