"""Krawczyk existence/uniqueness and enclosure of each NASA Riemann root.

The residual integral is enclosed independently with certified Gauss nodes,
outward arithmetic and the global order16 Taylor remainder, not mp.quad error.
"""
import mpmath as mp
import numpy as np
from floating_bounds import Thermo,gaussian,up
iv=mp.iv

def coefficients(th,t):
    assert t.b<1000 or t.a>=1000
    return [q.v for q in (th.low if t.b<1000 else th.high)]
def cp(th,t):return sum(a*t**j for j,a in enumerate(coefficients(th,t)[:5]))
def h(th,t):
    a=coefficients(th,t);return sum(a[j]*t**(j+1)/(j+1) for j in range(5))+a[5]
def s(th,t):
    a=coefficients(th,t);return a[0]*iv.ln(t)+sum(a[j]*t**j/j for j in range(1,5))+a[6]
def sound(th,t):return iv.sqrt(th.r.v*t*cp(th,t)/(cp(th,t)-th.r.v))

def certify(solution,precise,bounds):
    names=(('N2','CO2'),('N2','CO2'),('premix','products'))[solution.case.pair]
    l=Thermo(names[0],solution.left);r=Thermo(names[1],solution.right)
    mu=[iv.mpf(precise[k]) for k in ('T_left','T_right','pressure')]
    tl,tr,p=mu;t0=iv.mpf(700);p0=iv.mpf(100000);pl=iv.mpf(solution.pl)
    # Exact-node Gauss32 in64 equal temperature panels. Bound applies to the
    # entire integral; every summation below uses outward interval arithmetic.
    count=64;width=(t0-tl)/count;u0=iv.mpf(0)
    for i in range(count):
        mid=tl+(iv.mpf(i)+iv.mpf('.5'))*width
        for z,w in gaussian(32):
            t=mid+width*z.v/2;u0+=width*w.v/2*cp(l,t)/sound(l,t)
    remainder=count*2*iv.mpf(bounds['f16_taylor_coefficient'])*width**17/(2**16*17)
    rem=iv.mpf(remainder.b);u0+=iv.mpf([-rem,rem])
    vi=r.r.v*t0/p0
    ur=iv.sqrt((p-p0)*(vi-r.r.v*tr/p))
    f=[s(l,tl)-s(l,t0)-l.r.v*iv.ln(p/pl),h(r,tr)-h(r,t0)-(p-p0)*(r.r.v*tr/p+vi)/2,u0-ur]
    radius=iv.mpf('1e-32');box=[x+iv.mpf([-radius,radius]) for x in mu]
    a,b,c=box;v=vi-r.r.v*b/c;speed=iv.sqrt((c-p0)*v)
    jac=[
        [cp(l,a)/a,iv.mpf(0),-l.r.v/c],
        [iv.mpf(0),cp(r,b)-(c-p0)*r.r.v/(2*c),-(vi+r.r.v*b*p0/c**2)/2],
        [-cp(l,a)/sound(l,a),(c-p0)*r.r.v/(2*c*speed),-(v+(c-p0)*r.r.v*b/c**2)/(2*speed)],
    ]
    # mpmath's internal endpoint values convert exactly to its scalar context.
    def mid(x):return (mp.mpf(x._mpi_[0])+mp.mpf(x._mpi_[1]))/2
    cm=mp.inverse(mp.matrix([[mid(x) for x in row] for row in jac]))
    cmat=[[iv.mpf(str(cm[i,j])) for j in range(3)] for i in range(3)]
    det=(cmat[0][0]*(cmat[1][1]*cmat[2][2]-cmat[1][2]*cmat[2][1])-
         cmat[0][1]*(cmat[1][0]*cmat[2][2]-cmat[1][2]*cmat[2][0])+
         cmat[0][2]*(cmat[1][0]*cmat[2][1]-cmat[1][1]*cmat[2][0]))
    assert det.a>0 or det.b<0
    defect=[[iv.mpf(int(i==j))-sum(cmat[i][k]*jac[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    norm=max(np.nextafter(sum(up(x) for x in row),np.inf) for row in defect);assert norm<1
    kraw=[]
    for i in range(3):
        v=mu[i]-sum(cmat[i][j]*f[j] for j in range(3))+sum(defect[i][j]*iv.mpf([-radius,radius]) for j in range(3))
        assert v.a>box[i].a and v.b<box[i].b,'REFERENCE_ROOT_NOT_ENCLOSED'
        kraw.append(v)
    # Use the whole certified box for all downstream derived state quantities.
    tl,tr,p=box;du=iv.mpf(up(cp(l,tl)/sound(l,tl)))*radius
    velocity=u0+iv.mpf([-du,du])
    shock=iv.sqrt((p-p0)/(vi-r.r.v*tr/p))/(p0/(r.r.v*t0))
    speeds=[-sound(l,t0),velocity-sound(l,tl),velocity,shock]
    actual=[solution.tstar_l,solution.tstar_r,solution.pstar]
    differences={k:up(iv.mpf(x)-y) for k,x,y in zip(('T_left','T_right','pressure'),actual,box)}
    differences['velocity']=up(iv.mpf(solution.ustar)-velocity)
    speed_differences=[up(iv.mpf(x)-y) for x,y in zip(solution.speeds,speeds)]
    def text(x):return [str(mp.mpf(x._mpi_[0])),str(mp.mpf(x._mpi_[1]))]
    precise=dict(precise);precise['float_differences']=differences;precise['wave_speed_differences']=speed_differences
    precise['status']='INTERVAL_ROOT_CERTIFIED'
    precise['root_certificate']=dict(method='Krawczyk strict inclusion with analytic interval Jacobian',radius='1e-32',
        box=[text(x) for x in box],krawczyk=[text(x) for x in kraw],defect_infinity_norm_upper=norm,
        interval_residual=[text(x) for x in f],velocity_enclosure=text(velocity),
        integral_panels=count,integral_rule='Gauss32 independently bracketed nodes and weights',integral_remainder_bound=up(remainder),status='PASS')
    return precise
