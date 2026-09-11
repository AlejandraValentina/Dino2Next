"""Independent, full-NASA exact Riemann reference for the frozen VAL-008 cases.

No production imports. Conserved components are rho,rhou,rhoE,5rhoY,4rhoZ.
Primitive averages are direct averages, never EOS(conserved averages).
"""
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import json
import numpy as np
from scipy.integrate import quad_vec
from scipy.optimize import brentq

ROOT = Path(__file__).resolve().parents[3]
RAW_PATH = ROOT / 'docs/science/C1.0/datasets/thermo_species.json'
RAW = json.loads(RAW_PATH.read_text())
RU = RAW['Ru_J_kmol_K']
MW = np.array([r['MW_kg_kmol'] for r in RAW['species'][:5]])
LOW = np.array([r['coeffs'][8:] for r in RAW['species'][:5]])
HIGH = np.array([r['coeffs'][1:8] for r in RAW['species'][:5]])

def hs(a, t):
    return (sum(a[...,j]*t**(j+1)/(j+1) for j in range(5))+a[...,5],
            a[...,0]*np.log(t)+sum(a[...,j]*t**j/j for j in range(1,5))+a[...,6])

_hl,_sl=hs(LOW,1000.);_hh,_sh=hs(HIGH,1000.)
HIGH[:,5]+=_hl-_hh;HIGH[:,6]+=_sl-_sh

def composition(name):
    if name in ('N2','CO2'):
        v=np.zeros(5);v[2 if name=='N2' else 3]=1.;return v
    phi=.7
    n=np.array([1,12.5/phi,47/phi,0,0]) if name=='premix' else np.array([0,12.5/phi-12.5,47/phi,8,9])
    return n*MW/np.dot(n,MW)

class Thermo:
    def __init__(self,y):
        self.y=np.array(y);self.r=float(np.sum(self.y*RU/MW))
        self.low=np.sum((self.y*RU/MW)[:,None]*LOW,axis=0)
        self.high=np.sum((self.y*RU/MW)[:,None]*HIGH,axis=0)
    def coeff(self,t):return self.low if t<1000 else self.high
    def cp(self,t):
        t=np.asarray(t);a=np.where((t<1000)[...,None],self.low,self.high)
        return sum(a[...,j]*t**j for j in range(5))
    def h(self,t):
        t=np.asarray(t);a=np.where((t<1000)[...,None],self.low,self.high)
        return sum(a[...,j]*t**(j+1)/(j+1) for j in range(5))+a[...,5]
    def s0(self,t):
        t=np.asarray(t);a=np.where((t<1000)[...,None],self.low,self.high)
        return a[...,0]*np.log(t)+sum(a[...,j]*t**j/j for j in range(1,5))+a[...,6]
    def sound(self,t):return np.sqrt(self.r*t*self.cp(t)/(self.cp(t)-self.r))
    def fan_integral(self,a,b):
        cuts=[a]+([1000.] if min(a,b)<1000<max(a,b) else [])+[b]
        if b<a:cuts=sorted(cuts,reverse=True)
        return sum(quad_vec(lambda t:float(self.cp(t)/self.sound(t)),x,y,
                        quadrature='gk15',epsabs=1e-10,epsrel=1e-12)[0] for x,y in zip(cuts[:-1],cuts[1:]))

@dataclass(frozen=True)
class Case:
    pair: int
    velocity: float=0.
    pressure_ratio: float|None=None
    @property
    def name(self):return f'pair{self.pair}-'+(f'u{self.velocity:g}' if self.pressure_ratio is None else f'ratio{self.pressure_ratio:g}')
    @property
    def final_time(self):return .001 if self.pressure_ratio is None else .0002

def cases():
    return [Case(i,u) for i in range(3) for u in (0.,100.,-100.)]+[Case(i,0.,r) for i in range(3) for r in (2.,5.,10.)]

def _row(th,t,p,u):
    t,p,u=np.broadcast_arrays(t,p,u)
    rho=p/(th.r*t);e=th.h(t)-th.r*t
    return np.concatenate((np.stack((rho,u,p,t),axis=-1),rho[...,None]*th.y,
        np.stack((rho,rho*u,rho*(e+.5*u*u)),axis=-1),rho[...,None]*th.y,
        np.stack((np.zeros_like(rho),np.zeros_like(rho),rho,np.zeros_like(rho)),axis=-1)),axis=-1)

def _unpack(a):
    return dict(rho=a[...,0],u=a[...,1],p=a[...,2],T=a[...,3],rhoY=a[...,4:9],conserved=a[...,9:21])

@lru_cache(None)
def gauss(order):return np.polynomial.legendre.leggauss(order)

class RiemannSolution:
    def __init__(self,case):
        self.case=case
        names=(('N2','CO2'),('N2','CO2'),('premix','products'))[case.pair]
        self.left=Thermo(composition(names[0]));self.right=Thermo(composition(names[1]))
        self.tl,self.tr=((600.,600.),(600.,1800.),(400.,1800.))[case.pair]
        self.pl=self.pr=1e5;self.u=case.velocity
        if case.pressure_ratio is not None:self.tl=self.tr=700.;self.pl*=case.pressure_ratio;self.u=0.
        self.initial_left=_row(self.left,self.tl,self.pl,self.u)
        self.initial_right=_row(self.right,self.tr,self.pr,self.u)
        if case.pressure_ratio is None:
            self.pstar=self.pl;self.ustar=self.u;self.speeds=np.array([self.u]);return
        def match(p):
            t,ul=self.left_wave(p);s,ur,j=self.right_wave(p);return ul-ur
        self.pstar=brentq(match,self.pr,self.pl,xtol=1e-7,rtol=1e-14)
        self.tstar_l,self.ustar=self.left_wave(self.pstar)
        self.tstar_r,ur,j=self.right_wave(self.pstar)
        self.shock_speed=j/(self.pr/(self.right.r*self.tr))
        self.head=-float(self.left.sound(self.tl));self.tail=self.ustar-float(self.left.sound(self.tstar_l))
        self.speeds=np.array([self.head,self.tail,self.ustar,self.shock_speed])
        self.star_left=_row(self.left,self.tstar_l,self.pstar,self.ustar)
        self.star_right=_row(self.right,self.tstar_r,self.pstar,self.ustar)
        assert 300<=self.tstar_l<=self.tl and self.tr<self.tstar_r<=2200
        assert self.head<self.tail<self.ustar<self.shock_speed
        assert self.ustar+self.right.sound(self.tstar_r)>self.shock_speed>self.right.sound(self.tr)
        assert self.right.s0(self.tstar_r)-self.right.s0(self.tr)-self.right.r*np.log(self.pstar/self.pr)>=-1e-9
        assert abs(self.ustar-ur)<1e-8
    def left_wave(self,p):
        t=brentq(lambda t:self.left.s0(t)-self.left.s0(self.tl)-self.left.r*np.log(p/self.pl),300.,self.tl,xtol=1e-11)
        return t,-self.left.fan_integral(self.tl,t)
    def right_wave(self,p):
        if p==self.pr:return self.tr,0.,0.
        th=self.right;vi=th.r*self.tr/self.pr
        t=brentq(lambda t:th.h(t)-th.h(self.tr)-.5*(p-self.pr)*(th.r*t/p+vi),self.tr,2200.,xtol=1e-11)
        j=np.sqrt((p-self.pr)/(vi-th.r*t/p))
        return t,(p-self.pr)/j,j
    def fan_state(self,t):
        u=-self.left.fan_integral(self.tl,t)
        p=self.pl*np.exp((self.left.s0(t)-self.left.s0(self.tl))/self.left.r)
        return _row(self.left,t,p,u)
    def fan_rows(self,xi):
        """Vector safeguarded Newton; fixed Gaussian integration on the left fan.

        The frozen left fan lies wholly below1000K. No NASA interval is crossed.
        """
        xi=np.asarray(xi);lo=np.full(xi.shape,self.tstar_l);hi=np.full(xi.shape,self.tl)
        t=lo+(hi-lo)*(self.tail-xi)/(self.tail-self.head)
        z,w=gauss(32)
        for iteration in range(48):
            half=(self.tl-t)/4
            q=t[...,None,None]+half[...,None,None]*(np.array([1.,3.])[None,:,None]+z)
            u=half*np.sum(w*self.left.cp(q)/self.left.sound(q),axis=(-2,-1))
            a=self.left.sound(t);res=u-a-xi
            if np.max(np.abs(res),initial=0.)<2e-10:break
            cp=self.left.cp(t);cv=cp-self.left.r
            dcp=sum(j*self.left.low[j]*t**(j-1) for j in range(1,5))
            da=.5*a*(1/t+dcp/cp-dcp/cv)
            deriv=-cp/a-da
            lo=np.where(res>0,t,lo);hi=np.where(res<=0,t,hi)
            new=t-res/deriv
            t=np.where(np.abs(res)<2e-10,t,np.where((new>lo)&(new<hi),new,(lo+hi)/2))
        else:raise RuntimeError('REFERENCE_FAN_ROOT_FAILURE')
        p=self.pl*np.exp((self.left.s0(t)-self.left.s0(self.tl))/self.left.r)
        return _row(self.left,t,p,u)
    def _point(self,xi):
        if self.case.pressure_ratio is None:return self.initial_left if xi<self.u else self.initial_right
        if xi<=self.head:return self.initial_left
        if xi<self.tail:
            t=brentq(lambda t:-self.left.fan_integral(self.tl,t)-self.left.sound(t)-xi,self.tstar_l,self.tl,xtol=1e-10)
            return self.fan_state(t)
        if xi<self.ustar:return self.star_left
        if xi<self.shock_speed:return self.star_right
        return self.initial_right
    def point_states(self,x,time):
        x=np.asarray(x,dtype=float);flat=x.ravel()
        rows=np.array([self.initial_left if a<.5 else self.initial_right for a in flat]) if time==0 else np.array([self._point((a-.5)/time) for a in flat])
        return _unpack(rows.reshape(x.shape+(21,)))
    def cell_averages(self,edges,time,order=32):
        edges=np.asarray(edges,dtype=float)
        if np.any(np.diff(edges)<=0) or time<0:raise ValueError('invalid averaging domain')
        z,w=gauss(order);out=[];breaks=.5+time*self.speeds if time else np.array([.5])
        for lo,hi in zip(edges[:-1],edges[1:]):
            cuts=np.r_[lo,breaks[(breaks>lo)&(breaks<hi)],hi];total=np.zeros(21)
            for a,b in zip(cuts[:-1],cuts[1:]):
                mid=(a+b)/2
                if time and self.case.pressure_ratio is not None and self.head<(mid-.5)/time<self.tail:
                    # Additional smooth splits bound the Gaussian Taylor remainder
                    # uniformly, including early samples with a fan inside one cell.
                    panels=max(1,int(np.ceil((b-a)/time/4.)))
                    ends=np.linspace(a,b,panels+1);half=np.diff(ends)/2
                    pts=(ends[:-1]+half)[:,None]+half[:,None]*z
                    rows=self.fan_rows((pts.ravel()-.5)/time).reshape(panels,order,21)
                    total+=np.sum(half[:,None]*np.einsum('j,ijk->ik',w,rows),axis=0)
                else:
                    row=(self.initial_left if mid<.5 else self.initial_right) if time==0 else self._point((mid-.5)/time)
                    total+=(b-a)*row
            out.append(total/(hi-lo))
        return _unpack(np.array(out))

@lru_cache(None)
def solve(case):return RiemannSolution(case)

def cell_averages(edges,time,case,order=32):return solve(case).cell_averages(edges,time,order)

def point_states(x,time,case):return solve(case).point_states(x,time)
