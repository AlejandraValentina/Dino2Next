"""Independent exact cut-cell contact; NUMERICAL_FIXTURE_ONLY."""
import numpy as np

def point_states(x,time=0.,speed=0.):
    x=np.asarray(x);rho=np.where(x<.5+speed*time,1.,2.);u=np.full_like(rho,speed);p=np.ones_like(rho)
    return dict(rho=rho,u=u,p=p,conserved=np.stack([rho,rho*u,2.5+rho*u*u/2],axis=-1))

def cell_averages(edges,time=0.,speed=0.,order=32):
    edges=np.asarray(edges);fraction=np.maximum(0.,np.minimum(edges[1:],.5+speed*time)-edges[:-1])/np.diff(edges)
    rho=2.-fraction;u=np.full_like(rho,speed);p=np.ones_like(rho)
    return dict(rho=rho,u=u,p=p,conserved=np.stack([rho,rho*u,2.5+rho*u*u/2],axis=-1))
