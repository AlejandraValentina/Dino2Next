"""Independent smooth subsonic nozzle; exact area-weighted Gauss averages."""
import numpy as np

def area(x):return 1+.4*(np.asarray(x)-.5)**2

def area_mach(m):return ((5+m*m)/6)**3/m

def point_states(x,time=0.,smooth=True):
    x=np.asarray(x,dtype=float)
    if smooth:
        target=area(x)*area_mach(.3);lo=np.full_like(x,1e-12);hi=np.ones_like(x)
        for _ in range(64):
            mid=(lo+hi)/2;greater=area_mach(mid)>target
            lo=np.where(greater,mid,lo);hi=np.where(greater,hi,mid)
        m=(lo+hi)/2;t=1/(1+.2*m*m);p=t**3.5;rho=p/t;u=m*np.sqrt(1.4*t)
    else:rho=np.ones_like(x);u=np.zeros_like(x);p=np.ones_like(x)
    return dict(rho=rho,u=u,p=p,conserved=np.stack([rho,rho*u,p/.4+rho*u*u/2],axis=-1))

def cell_averages(edges,time=0.,smooth=True,order=32):
    edges=np.asarray(edges);z,w=np.polynomial.legendre.leggauss(order);rows=[];q=[]
    for l,r in zip(edges[:-1],edges[1:]):
        x=(l+r)/2+(r-l)*z/2;s=point_states(x,time,smooth);a=area(x)
        rows.append([np.dot(w,s[k])/2 for k in ['rho','u','p']])
        q.append(np.tensordot(w,a[:,None]*s['conserved'],axes=(0,0))/2)
    v=np.asarray(rows)
    return dict(rho=v[:,0],u=v[:,1],p=v[:,2],conserved=np.asarray(q))
