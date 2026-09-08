"""Outward interval Taylor bounds, independent of quadrature error estimates.

Taylor coefficients are derivative/k!, allowing high-order Gaussian error bounds
without numerical differentiation. mpmath.iv performs the interval arithmetic.
"""
import math
import mpmath as mp
mp.iv.dps=60
iv=mp.iv

class Jet:
    def __init__(self,c,n=None):
        if isinstance(c,list):self.c=c
        else:self.c=[iv.mpf(c)]+[iv.mpf(0)]*n
    @property
    def n(self):return len(self.c)-1
    def cast(self,x):return x if isinstance(x,Jet) else Jet(x,self.n)
    def __add__(self,x):
        x=self.cast(x);return Jet([a+b for a,b in zip(self.c,x.c)])
    __radd__=__add__
    def __neg__(self):return Jet([-x for x in self.c])
    def __sub__(self,x):return self+-self.cast(x)
    def __rsub__(self,x):return self.cast(x)+-self
    def __mul__(self,x):
        x=self.cast(x);return Jet([sum(self.c[j]*x.c[k-j] for j in range(k+1)) for k in range(self.n+1)])
    __rmul__=__mul__
    def inv(self):
        c=[1/self.c[0]]
        for k in range(1,self.n+1):c.append(-sum(self.c[j]*c[k-j] for j in range(1,k+1))/self.c[0])
        return Jet(c)
    def __truediv__(self,x):return self*self.cast(x).inv()
    def __rtruediv__(self,x):return self.cast(x)*self.inv()
    def __pow__(self,p):
        if isinstance(p,int) and p>=0:
            out=Jet(1,self.n)
            for _ in range(p):out=out*self
            return out
        if p==.5:
            c=[iv.sqrt(self.c[0])]
            for k in range(1,self.n+1):c.append((self.c[k]-sum(c[j]*c[k-j] for j in range(1,k)))/(2*c[0]))
            return Jet(c)
        raise ValueError(p)
    def derivative(self):return Jet([(k+1)*self.c[k+1] for k in range(self.n)])
    def exp(self):
        c=[iv.exp(self.c[0])]
        for k in range(1,self.n+1):c.append(sum(j*self.c[j]*c[k-j] for j in range(1,k+1))/k)
        return Jet(c)
    def log(self):
        d=self.derivative()/Jet(self.c[:-1]);return Jet([iv.ln(self.c[0])]+[d.c[k-1]/k for k in range(1,self.n+1)])

def upper(x):
    import numpy as np
    return np.nextafter(float(max(abs(x.a),abs(x.b))),np.inf)

def temperature(lo,hi,n):return Jet([iv.mpf([str(lo),str(hi)]),iv.mpf(1)]+[iv.mpf(0)]*(n-1))

def hull(a,b):return iv.mpf([min(a.a,b.a),max(a.b,b.b)])

def thermo(th,t,exact=None):
    a=[hull(iv.mpf(float(x)),exact.low[j].v) if exact else iv.mpf(float(x)) for j,x in enumerate(th.low)]
    r=hull(iv.mpf(float(th.r)),exact.r.v) if exact else iv.mpf(float(th.r))
    cp=sum(t**j*a[j] for j in range(5));sound=(t*r*cp/(cp-r))**.5
    h=sum(t**(j+1)*a[j]/(j+1) for j in range(5))+a[5]
    s=t.log()*a[0]+sum(t**j*a[j]/j for j in range(1,5))+a[6]
    return cp,sound,h,s

def bounds(solution):
    """Global fan derivatives and 16th Taylor coefficient of cp/a.

    Fixed32 temperature subintervals reduce dependency overestimation. This bounds
    complete intervals, not a sampled derivative maximum.
    """
    import numpy as np
    from floating_bounds import Thermo as ExactThermo, Ball
    exact=ExactThermo('premix' if solution.case.pair==2 else 'N2',solution.left)
    r=hull(iv.mpf(float(solution.left.r)),exact.r.v)
    s_initial=hull(iv.mpf(float(solution.left.s0(solution.tl))),exact.s(Ball(solution.tl)).v)
    ys=[hull(iv.mpf(float(y)),exact.y[j].v) for j,y in enumerate(solution.left.y)]
    fourth=np.zeros(21);first=np.zeros(21);f16=0.;xi_min=float('inf')
    cuts=np.linspace(solution.tstar_l-1e-7,solution.tl+1e-7,33)
    for lo,hi in zip(cuts[:-1],cuts[1:]):
        t=temperature(lo,hi,16);cp,a,h,s=thermo(solution.left,t,exact)
        f=cp/a;f16=max(f16,upper(f.c[16]))
        t=temperature(lo,hi,5);cp,a,h,s=thermo(solution.left,t,exact);f=cp/a
        u=Jet([iv.mpf(['-0.0000001',str(solution.ustar+1e-7)])]+[-f.c[k-1]/k for k in range(1,6)])
        xi=u-a;d=xi.derivative();xi_min=min(xi_min,np.nextafter(float(-d.c[0].b),-np.inf))
        p=solution.pl*((s-s_initial)/r).exp()
        rho=p/(t*r);energy=rho*(h-t*r+u*u/2)
        quantities=[rho,u,p,t]+[rho*y for y in ys]+[rho,rho*u,energy]+[rho*y for y in ys]+[Jet(0,5),Jet(0,5),rho,Jet(0,5)]
        for j,q in enumerate(quantities):
            # D_xi = (1/xi_T) D_T; coefficients truncated consistently.
            for k in range(4):
                q=q.derivative()/Jet(d.c[:len(q.c)-1])
                if k==0:first[j]=max(first[j],upper(q.c[0]))
            fourth[j]=max(fourth[j],upper(q.c[0]))
    assert xi_min>0
    return dict(fourth_xi_derivative=fourth.tolist(),first_xi_derivative=first.tolist(),f16_taylor_coefficient=f16,minus_dxi_dT_lower=xi_min,
                interval_dps=mp.iv.dps,temperature_boxes=32)

def gaussian_remainder(coefficient,order,length):
    """Positive Gauss rule reproducing the even degree order; remainder twice.

    coefficient bounds |f^(order)|/order!. Integral plus quadrature of |x-mid|^order
    are each length^(order+1)/(2^order*(order+1)), since |x-mid|^order is an
    exactly reproduced polynomial for even order. All calls use order4 or16
    with Gauss16/32 (exact through31/63); degree order-1 alone would not suffice.
    """
    return 2*coefficient*length**(order+1)/(2**order*(order+1))
