"""Independent linear standing/reflected waves; NUMERICAL_FIXTURE_ONLY."""
import math
import numpy as np

C=math.sqrt(1.4)

def point_states(x,time=0.,kind='rigid',epsilon=1e-5):
    x=np.asarray(x)
    if kind=='rigid':
        v=epsilon*np.cos(np.pi*x)*math.cos(np.pi*C*time)
        u=epsilon/C*np.sin(np.pi*x)*math.sin(np.pi*C*time)
    elif kind=='free':
        a=epsilon*np.exp(-((x-C*time-.25)/.05)**2);b=epsilon*np.exp(-((2-x-C*time-.25)/.05)**2)
        v=a-b;u=(a+b)/C
    else:raise ValueError(kind)
    rho=1+v/(C*C);p=1+v
    return dict(rho=rho,u=u,p=p,conserved=np.stack([rho,rho*u,p/.4+rho*u*u/2],axis=-1))

def gaussian_integral(left,right,center,epsilon):
    return epsilon*.05*math.sqrt(math.pi)/2*(math.erf((right-center)/.05)-math.erf((left-center)/.05))

def cell_averages(edges,time=0.,kind='rigid',epsilon=1e-5,order=32):
    edges=np.asarray(edges);dx=np.diff(edges);mid=(edges[:-1]+edges[1:])/2
    if kind=='rigid':
        v=epsilon*np.cos(np.pi*mid)*np.sinc(dx/2)*math.cos(np.pi*C*time)
        u=epsilon/C*np.sin(np.pi*mid)*np.sinc(dx/2)*math.sin(np.pi*C*time)
    elif kind=='free':
        a=np.array([gaussian_integral(l,r,.25+C*time,epsilon) for l,r in zip(edges[:-1],edges[1:])])/dx
        b=np.array([gaussian_integral(l,r,1.75-C*time,epsilon) for l,r in zip(edges[:-1],edges[1:])])/dx
        v=a-b;u=(a+b)/C
    else:raise ValueError(kind)
    z,w=np.polynomial.legendre.leggauss(order)
    q=np.array([np.tensordot(w,point_states(m+d*z/2,time,kind,epsilon)['conserved'],axes=(0,0))/2 for m,d in zip(mid,dx)])
    return dict(rho=1+v/(C*C),u=u,p=1+v,conserved=q)

def fourier_coefficient(edges,pressure_perturbation):
    edges=np.asarray(edges);weights=(np.exp(-2j*np.pi*edges[1:])-np.exp(-2j*np.pi*edges[:-1]))/(-2j*np.pi)
    return complex(np.dot(pressure_perturbation,weights))

def exact_fourier(time,epsilon=1e-5,order=32):
    """Full incident-minus-reflected waveform integral; no peak surrogate."""
    z,w=np.polynomial.legendre.leggauss(order);result=0j
    # Fixed fine panels resolve both Gaussian centers, even outside the domain.
    for l,r in zip(np.linspace(0,1,65)[:-1],np.linspace(0,1,65)[1:]):
        x=(l+r)/2+(r-l)*z/2
        pp=epsilon*(np.exp(-((x-C*time-.25)/.05)**2)-np.exp(-((2-x-C*time-.25)/.05)**2))
        result+=(r-l)/2*np.dot(w,pp*np.exp(-2j*np.pi*x))
    return complex(result)
