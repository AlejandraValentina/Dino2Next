"""Research-only cumulative-volume coordinates for one accepted area segment."""
from dataclasses import dataclass
from fractions import Fraction as F
from math import isfinite
import numpy as np
from dino2next.gasdynamics import PolynomialSegment


@dataclass(frozen=True)
class VolumeMap:
    segment: PolynomialSegment

    def exact(self,x):
        """Exact rational integral of accepted binary64 polynomial input."""
        s=self.segment;x=F(x)
        if not F(s.left)<=x<=F(s.right):raise ValueError('GEOMETRY_OUTSIDE_DOMAIN')
        h=F(s.right)-F(s.left);xi=(x-F(s.left))/h
        return h*sum(F(a)*xi**(i+1)/(i+1) for i,a in enumerate(s.area_coefficients))

    def cumulative(self,x):
        return self.segment.integral(self.segment.left,float(x))

    def inverse(self,volume):
        if not isfinite(volume):raise ValueError('NONFINITE_VOLUME')
        target=F(float(volume));lo=self.segment.left;hi=self.segment.right
        if not 0<=target<=self.exact(hi):raise ValueError('VOLUME_OUTSIDE_DOMAIN')
        if target==0:return lo,(lo,lo),F(0)
        if target==self.exact(hi):return hi,(hi,hi),F(0)
        while True:
            mid=lo+(hi-lo)/2
            if mid==lo or mid==hi:break
            if self.exact(mid)<target:lo=mid
            else:hi=mid
        assert self.exact(lo)<=target<=self.exact(hi)
        x=min((lo,hi),key=lambda v:abs(self.exact(v)-target))
        return x,(lo,hi),self.exact(x)-target


def algebra_rhs(geometry,W,U,pressure,speeds):
    """Exact selected first-order pressure source and full ALE flux algebra.

    Face U/physical F are uniform in this manufactured control. Not a Riemann
    solver; no contact or wave recipe is selected by this helper.
    """
    x=np.array([geometry.inverse(float(v))[0] for v in W])
    area=np.array([geometry.segment.value(float(v)) for v in x])
    velocity=U[1]/U[0]
    Fflux=velocity*U.copy();Fflux[1]+=pressure;Fflux[2]+=pressure*velocity
    flux=area[:,None]*(Fflux[None,:]-np.asarray(speeds)[:,None]*U[None,:])
    source=np.zeros(12);source[1]=pressure*(area[1]-area[0])
    return area*np.asarray(speeds),flux[0]-flux[1]+source,flux,source


def manufactured_ssprk2(geometry,W,Q,U,pressure,speeds,dt):
    dW0,dQ0,_,_=algebra_rhs(geometry,W,U,pressure,speeds)
    W1=W+dt*dW0;Q1=Q+dt*dQ0
    if W1[1]<=W1[0]:raise ValueError('FE1_VOLUME')
    dW1,dQ1,_,_=algebra_rhs(geometry,W1,U,pressure,speeds)
    W2=W1+dt*dW1;Q2=Q1+dt*dQ1
    if W2[1]<=W2[0]:raise ValueError('FE2_VOLUME')
    Wnew=.5*W+.5*W2;Qnew=.5*Q+.5*Q2
    return Wnew,Qnew,((W1,Q1),(W2,Q2))
