"""Forward absolute floating-error propagation under an explicit arithmetic model.

Each operation carries an outward exact-value interval and an absolute error
interval. This replaces a guessed operation-count/cancellation multiplier.
Basic operations round with relative error<=2^-52; log/exp/sqrt and small integer
powers use a conservative4*2^-52 model (at least2ulp). No comparison of two
precisions supplies these bounds. Gauss nodes/weights are independently enclosed.
"""
import json,math
from functools import lru_cache
import mpmath as mp
import numpy as np
import reference as ref
iv=mp.iv
iv.dps=80
EPS=iv.mpf(2)**-52

def up(x):return np.nextafter(float(abs(x).b),np.inf)
def mag(x):return iv.mpf([0,max(abs(x.a),abs(x.b))])
def maximum(x):return iv.mpf(x.b)
def minimum(x):return iv.mpf(x.a)

class Ball:
    def __init__(self,v,e=0):self.v=v if hasattr(v,'_mpi_') else iv.mpf(v);self.e=maximum(abs(iv.mpf(e)))
    @staticmethod
    def cast(x):return x if isinstance(x,Ball) else Ball(x)
    def __add__(self,x):
        x=self.cast(x);v=self.v+x.v;e=self.e+x.e
        return Ball(v,e+EPS*(mag(v)+e))
    __radd__=__add__
    def __neg__(self):return Ball(-self.v,self.e)
    def __sub__(self,x):return self+-self.cast(x)
    def __rsub__(self,x):return self.cast(x)+-self
    def __mul__(self,x):
        x=self.cast(x);v=self.v*x.v;e=mag(self.v)*x.e+mag(x.v)*self.e+self.e*x.e
        return Ball(v,e+EPS*(mag(v)+e))
    __rmul__=__mul__
    def __truediv__(self,x):
        x=self.cast(x);den=minimum(abs(x.v))-x.e
        assert den.a>0,'arithmetic denominator not separated from zero'
        v=self.v/x.v;e=(self.e+mag(v)*x.e)/den
        return Ball(v,e+EPS*(mag(v)+e))
    def __rtruediv__(self,x):return self.cast(x)/self
    def __pow__(self,n):
        if n==0:return Ball(1)
        assert isinstance(n,int) and n>0
        lo=minimum(self.v)-self.e;hi=maximum(self.v)+self.e
        assert lo.a>0
        e=n*hi**(n-1)*self.e;v=self.v**n
        return Ball(v,e+4*EPS*(mag(v)+e))
    def sqrt(self):
        lo=minimum(self.v)-self.e;assert lo.a>0
        v=iv.sqrt(self.v);e=self.e/(iv.sqrt(lo)+iv.sqrt(minimum(self.v)))
        return Ball(v,e+4*EPS*(mag(v)+e))
    def log(self):
        lo=minimum(self.v)-self.e;assert lo.a>0
        v=iv.ln(self.v);e=self.e/lo
        return Ball(v,e+4*EPS*(mag(v)+e))
    def exp(self):
        v=iv.exp(self.v);e=iv.exp(maximum(self.v)+self.e)*self.e
        return Ball(v,e+4*EPS*(mag(v)+e))

def binary_coefficient(exact,binary):return Ball(exact,abs(iv.mpf(float(binary))-exact))

class Thermo:
    def __init__(self,name,th):
        raw=json.loads(ref.RAW_PATH.read_text(),parse_float=iv.mpf)
        rows=raw['species'][:5];mw=[iv.mpf(r['MW_kg_kmol']) for r in rows]
        if name in ('N2','CO2'):n=[iv.mpf(int(j==(2 if name=='N2' else 3))) for j in range(5)]
        else:
            phi=iv.mpf('.7');n=[1,iv.mpf('12.5')/phi,47/phi,0,0] if name=='premix' else [0,iv.mpf('12.5')/phi-iv.mpf('12.5'),47/phi,8,9]
        den=sum(a*b for a,b in zip(n,mw));y=[a*b/den for a,b in zip(n,mw)]
        ru=raw['Ru_J_kmol_K'];r=sum(a*ru/m for a,m in zip(y,mw))
        low=[sum(y[k]*ru/mw[k]*rows[k]['coeffs'][8+j] for k in range(5)) for j in range(7)]
        high=[sum(y[k]*ru/mw[k]*rows[k]['coeffs'][1+j] for k in range(5)) for j in range(7)]
        def h(a):return sum(a[j]*iv.mpf(1000)**(j+1)/(j+1) for j in range(5))+a[5]
        def s(a):return a[0]*iv.ln(1000)+sum(a[j]*iv.mpf(1000)**j/j for j in range(1,5))+a[6]
        high[5]+=h(low)-h(high);high[6]+=s(low)-s(high)
        self.low=[binary_coefficient(a,b) for a,b in zip(low,th.low)]
        self.high=[binary_coefficient(a,b) for a,b in zip(high,th.high)]
        self.r=binary_coefficient(r,th.r);self.y=[binary_coefficient(a,b) for a,b in zip(y,th.y)]
    def coeff(self,t):return self.low if t.v.b<1000 else self.high
    def cp(self,t):return sum(t**j*a for j,a in enumerate(self.coeff(t)[:5]))
    def h(self,t):
        a=self.coeff(t);return sum(t**(j+1)*a[j]/(j+1) for j in range(5))+a[5]
    def s(self,t):
        a=self.coeff(t);return t.log()*a[0]+sum(t**j*a[j]/j for j in range(1,5))+a[6]
    def sound(self,t):return (self.r*t*self.cp(t)/(self.cp(t)-self.r)).sqrt()
    def row(self,t,p,u):
        rho=p/(self.r*t);e=self.h(t)-self.r*t
        return [rho,u,p,t]+[rho*y for y in self.y]+[rho,rho*u,rho*(e+u*u*.5)]+[rho*y for y in self.y]+[Ball(0),Ball(0),rho,Ball(0)]

@lru_cache(None)
def gaussian(order):
    mp.mp.dps=80;z,w=mp.gauss_quadrature(order,'legendre');zf,wf=ref.gauss(order)
    def leg(x):
        a,b=iv.mpf(1),x
        for n in range(2,order+1):a,b=b,((2*n-1)*x*b-(n-1)*a)/n
        return b,order*(x*b-a)/(x*x-1)
    out=[];previous_hi=None
    for j in range(order):
        # Sign bracket verifies each root enclosure; non-overlap follows sorted
        # narrow brackets, while degree/order accounts for all roots.
        lo=mp.mpf(z[j])-mp.mpf('1e-60');hi=mp.mpf(z[j])+mp.mpf('1e-60')
        assert previous_hi is None or lo>previous_hi
        previous_hi=hi
        pl=leg(iv.mpf(str(lo)))[0];ph=leg(iv.mpf(str(hi)))[0]
        assert (pl.b<0 and ph.a>0) or (pl.a>0 and ph.b<0)
        zi=iv.mpf([str(lo),str(hi)]);deriv=leg(zi)[1];wi=2/((1-zi*zi)*deriv*deriv)
        out.append((binary_coefficient(zi,zf[j]),binary_coefficient(wi,wf[j])))
    return out

def fan_velocity_error(solution,thermo):
    t=Ball(iv.mpf([solution.tstar_l-1e-7,solution.tl]));half=(solution.tl-t)/4
    total=Ball(0)
    for side in (1,3):
        for z,w in gaussian(32):
            q=t+half*(side+z);total=total+w*thermo.cp(q)/thermo.sound(q)
    result=half*total
    return up(result.e)

def certificate(solution,scales,derivative_bounds=None,precise=None,velocity_truncation=0.):
    names=(('N2','CO2'),('N2','CO2'),('premix','products'))[solution.case.pair]
    l=Thermo(names[0],solution.left);r=Thermo(names[1],solution.right)
    rows=[l.row(Ball(solution.tl),Ball(solution.pl),Ball(solution.u)),r.row(Ball(solution.tr),Ball(solution.pr),Ball(solution.u))]
    point=np.maximum(*[np.array([up(q.e) for q in row]) for row in rows])
    velocity_error=0.;coordinate_error=0.
    if solution.case.pressure_ratio is not None:
        velocity_error=fan_velocity_error(solution,l)+velocity_truncation
        for lo,hi in zip(np.linspace(solution.tstar_l-1e-7,solution.tl,33)[:-1],np.linspace(solution.tstar_l-1e-7,solution.tl,33)[1:]):
            t=Ball(iv.mpf([lo,hi]));u=Ball(iv.mpf(['-1e-7',solution.ustar+1e-7]),velocity_error)
            p=solution.pl*((l.s(t)-l.s(Ball(solution.tl)))/l.r).exp()
            row=l.row(t,p,u);rows.append(row)
            point=np.maximum(point,[up(q.e) for q in row])
        dif=precise['float_differences']
        for th,temp,key in ((l,solution.tstar_l,'T_left'),(r,solution.tstar_r,'T_right')):
            row=th.row(Ball(temp,dif[key]),Ball(solution.pstar,dif['pressure']),Ball(solution.ustar,dif['velocity']))
            rows.append(row)
            point=np.maximum(point,[up(q.e) for q in row])
        # Coordinate calculation xnode=(a+b)/2+(b-a)*z/2 and xi=(xnode-.5)/t.
        # Original window only; minimum positive frozen sample is t_final/100.
        x=Ball(iv.mpf([0,1]));width=Ball(iv.mpf([0,1/80]));z=Ball(iv.mpf([-1,1]),max(up(z.e) for z,w in gaussian(32)))
        node=(x+x)/2+width*z/2;xi=(node-.5)/Ball(iv.mpf([solution.case.final_time/100,solution.case.final_time]))
        # Actual np.linspace panel endpoints add <=16eps absolute position
        # error: two operations for step, two for indexed endpoint, midpoint/
        # width/node operations and original wave-endpoint arithmetic. All
        # positions lie in[0,1]. Charge this explicitly after division by the
        # smallest positive frozen sampling time, rather than hiding it in a
        # discontinuity-location budget. Fan endpoint subtraction is exact by
        # Sterbenz (the complete fan lies between .3 and .6m in these cases).
        coordinate_error=up(xi.e)+16*np.finfo(float).eps/(solution.case.final_time/100)
        sound_error=up(l.sound(Ball(iv.mpf([solution.tstar_l-1e-7,solution.tl]))).e)
        point+=np.array(derivative_bounds['first_xi_derivative'])*(velocity_error+sound_error+coordinate_error+2e-10)
    # Dot products need at most32 dependent rounding steps, then P panel
    # additions and <=8 steps for half/constant pieces/final division. There
    # are at most4 constant wave pieces.32+P+8 <=32*(P+4), the conservative
    # actual-count envelope used below; it is not a guessed fixed gamma.
    terms=(int(np.ceil((solution.tail-solution.head)/4))+4)*32 if solution.case.pressure_ratio is not None else 8
    gamma=terms*np.finfo(float).eps/(1-terms*np.finfo(float).eps)
    maxvalues=np.max([np.array([up(q.v) for q in row]) for row in rows],axis=0)
    # Convex averages preserve pointwise errors. Discontinuity location errors
    # use maximum state jump divided by finest cell width; time*speed rounding
    # and independently checked star velocity errors are included explicitly.
    speed_error=max(precise.get('wave_speed_differences',[precise['float_differences']['velocity']])) if precise else 0.
    edge_error=16*np.finfo(float).eps+(solution.case.final_time*speed_error if precise else 0.)
    finest=640 if precise else 400
    weight_error=sum(up(w.e) for z,w in gaussian(32))/2 if precise else 0.
    # One material jump for contacts, two (contact and shock) for shock cases.
    # Each absolute jump <=2M even when formation energy changes sign.
    jump_factor=4 if precise else 2
    # Accumulation/weight errors act on the already perturbed node values too.
    # Keep the small increment without subtracting nearly equal numbers.
    increment=gamma+weight_error+gamma*weight_error
    average=(1+increment)*point+increment*maxvalues+jump_factor*finest*edge_error*maxvalues
    average=np.nextafter(average*(1+64*np.finfo(float).eps),np.inf)
    return dict(absolute_bounds=average.tolist(),normalized_bounds=(average/scales).tolist(),velocity_arithmetic_bound=velocity_error,
        coordinate_arithmetic_bound=coordinate_error,weighted_sum_terms=terms,discontinuity_jump_factor=jump_factor,
        model='Forward interval propagation per arithmetic operation, IEEE basic error<=eps and elementary/smallintegerpower error<=4eps; exact binary coefficient errors and certified Gaussian nodes/weights included.')
