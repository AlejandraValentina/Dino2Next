"""Independent translated acoustic averages and exact Fourier operator."""
import math
import numpy as np

C=math.sqrt(1.4)

def point_states(x,time=0.,epsilon=1e-5):
    v=epsilon*np.cos(2*np.pi*(np.asarray(x)-C*time));rho=1+v;u=C*v;p=1+1.4*v
    return dict(rho=rho,u=u,p=p,conserved=np.stack([rho,rho*u,p/.4+rho*u*u/2],axis=-1))

def cell_averages(edges,time=0.,epsilon=1e-5,order=32):
    edges=np.asarray(edges);dx=np.diff(edges);mid=(edges[:-1]+edges[1:])/2;k=2*np.pi
    co=np.cos(k*(mid-C*time))*np.sinc(dx)
    co2=(1+np.cos(2*k*(mid-C*time))*np.sinc(2*dx))/2
    co3=(3*co+np.cos(3*k*(mid-C*time))*np.sinc(3*dx))/4
    rho=1+epsilon*co;u=C*epsilon*co;p=1+1.4*epsilon*co
    momentum=C*(epsilon*co+epsilon**2*co2)
    energy=p/.4+C*C/2*(epsilon**2*co2+epsilon**3*co3)
    return dict(rho=rho,u=u,p=p,conserved=np.stack([rho,momentum,energy],axis=-1))

def fourier_coefficient(edges,pressure_perturbation):
    """Exact integral of supplied piecewise-constant cell field times exp(-2pi ix)."""
    edges=np.asarray(edges);weights=(np.exp(-2j*np.pi*edges[1:])-np.exp(-2j*np.pi*edges[:-1]))/(-2j*np.pi)
    return complex(np.dot(pressure_perturbation,weights))

def exact_fourier(time=0.,epsilon=1e-5):
    return 1.4*epsilon/2*np.exp(-2j*np.pi*C*time)
