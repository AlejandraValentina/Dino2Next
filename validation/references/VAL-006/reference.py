"""Independent constant-gamma Sod reference; NUMERICAL_FIXTURE_ONLY."""
import math
from functools import lru_cache
import numpy as np

GAMMA=1.4

@lru_cache(maxsize=None)
def quadrature(order):return np.polynomial.legendre.leggauss(order)

def integrate(function,left,right,order=32):
    z,w=quadrature(order)
    return (right-left)/2*np.tensordot(w,function((left+right)/2+(right-left)/2*z),axes=(0,0))

def pack(rho,u,p):
    rho,u,p=np.broadcast_arrays(rho,u,p)
    return {'rho':rho,'u':u,'p':p,'conserved':np.stack([rho,rho*u,p/(GAMMA-1)+rho*u*u/2],axis=-1)}

def averages(edges,point,breaks=(),order=32,area=None):
    edges=np.asarray(edges,dtype=float); rows=[]; qs=[]
    for left,right in zip(edges[:-1],edges[1:]):
        cuts=[left,*sorted(b for b in breaks if left<b<right),right]
        primitive=np.zeros(3);q=np.zeros(3)
        for a,b in zip(cuts[:-1],cuts[1:]):
            primitive+=integrate(lambda x:np.stack([point(x)[k] for k in ['rho','u','p']],axis=-1),a,b,order)
            q+=integrate(lambda x:point(x)['conserved']*(area(x)[:,None] if area else 1),a,b,order)
        rows.append(primitive/(right-left));qs.append(q/(right-left))
    values=np.array(rows)
    return dict(rho=values[:,0],u=values[:,1],p=values[:,2],conserved=np.array(qs))

def pressure_root():
    def wave(p,rho,pk):
        c=math.sqrt(GAMMA*pk/rho)
        return (p-pk)*math.sqrt(2/((GAMMA+1)*rho)/(p+(GAMMA-1)/(GAMMA+1)*pk)) if p>pk else 2*c/(GAMMA-1)*((p/pk)**((GAMMA-1)/(2*GAMMA))-1)
    lo,hi=.1,1.
    for _ in range(100):
        p=(lo+hi)/2
        if wave(p,1.,1.)+wave(p,.125,.1)>0:hi=p
        else:lo=p
    p=(lo+hi)/2
    return p,(wave(p,.125,.1)-wave(p,1.,1.))/2

PSTAR,USTAR=pressure_root()
CL=math.sqrt(1.4)
CSTAR=CL*PSTAR**((GAMMA-1)/(2*GAMMA))
SHOCK=math.sqrt(GAMMA*.1/.125)*math.sqrt((GAMMA+1)/(2*GAMMA)*PSTAR/.1+(GAMMA-1)/(2*GAMMA))

def point_states(x,time=0.):
    x=np.asarray(x,dtype=float)
    if time==0:return pack(np.where(x<.5,1.,.125),np.zeros_like(x),np.where(x<.5,1.,.1))
    v=(x-.5)/time;rho=np.empty_like(v);u=np.empty_like(v);p=np.empty_like(v)
    masks=[v<=-CL,(v>-CL)&(v<USTAR-CSTAR),(v>=USTAR-CSTAR)&(v<=USTAR),(v>USTAR)&(v<SHOCK),v>=SHOCK]
    rho[masks[0]]=1;u[masks[0]]=0;p[masks[0]]=1
    f=masks[1];c=2/(GAMMA+1)*(CL-(GAMMA-1)*v[f]/2)
    rho[f]=(c/CL)**(2/(GAMMA-1));u[f]=2/(GAMMA+1)*(CL+v[f]);p[f]=(c/CL)**(2*GAMMA/(GAMMA-1))
    rho[masks[2]]=PSTAR**(1/GAMMA);u[masks[2]]=USTAR;p[masks[2]]=PSTAR
    ratio=PSTAR/.1;beta=(GAMMA-1)/(GAMMA+1)
    rho[masks[3]]=.125*(ratio+beta)/(beta*ratio+1);u[masks[3]]=USTAR;p[masks[3]]=PSTAR
    rho[masks[4]]=.125;u[masks[4]]=0;p[masks[4]]=.1
    return pack(rho,u,p)

def cell_averages(edges,time=0.,order=32):
    return averages(edges,lambda x:point_states(x,time),[.5+v*time for v in [-CL,USTAR-CSTAR,USTAR,SHOCK]],order)
