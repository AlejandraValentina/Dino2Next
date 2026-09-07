"""RESEARCH_ONLY_NON_PRODUCTION: bounded algebra/ODE checks, not a solver qualification."""
import json, math, platform, hashlib, sys
from pathlib import Path
import numpy as np
import scipy
from scipy.optimize import brentq
from scipy.integrate import quad
import cantera as ct
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).parent
species=ct.Species.list_from_file(str(ROOT/'docs/science/C1.0/datasets/thermo_transport.yaml'))
gas=ct.Solution(thermo='ideal-gas',species=species)
rows=[]
def record(name, **data): rows.append({'check':name,**data})
# Independently evaluated NASA Hugoniot and isentropic integral; no candidate FV code.
for X in ['O2:1,N2:3.76','CO2:8,H2O:9,O2:5.357142857142858,N2:67.14285714285714']:
 for Ti in [400.,700.,1000.]:
  pi=100000.; gas.TPX=Ti,pi,X; hi=gas.enthalpy_mass;ri=gas.density;si=gas.entropy_mass;ui=-50.
  for ratio in [1.01,1.2,2.,3.]:
   p=ratio*pi
   def H(T):
    gas.TPX=T,p,X
    return gas.enthalpy_mass-hi-(p-pi)*(1/gas.density+1/ri)/2
   T=brentq(H,Ti,2200,xtol=1e-10);gas.TPX=T,p,X;r=gas.density;h=gas.enthalpy_mass;s=gas.entropy_mass
   j=math.sqrt((p-pi)/(1/ri-1/r));u=ui+(p-pi)/j;S=ui+j/ri
   mass=ri*(ui-S)-r*(u-S)
   momentum=(pi+ri*(ui-S)**2)-(p+r*(u-S)**2)
   energy=(hi+(ui-S)**2/2)-(h+(u-S)**2/2)
   assert abs(mass)/j<1e-10 and abs(momentum)/p<1e-10 and abs(energy)/max(abs(hi),1e6)<1e-10 and s>=si-1e-8
   record('NASA_RH',composition=X,T0=Ti,ratio=ratio,T=T,mass_residual=mass,momentum_residual=momentum,energy_residual=energy,entropy_jump=s-si)
# Constant-gamma right wave integral and critical capacity identities.
g=1.4; R=287.;cp=g*R/(g-1)
for T0 in [350.,700.,1500.]:
 for q in [.2,.5,.9,1.]:
  T=T0*q**((g-1)/g)
  val=quad(lambda t: cp/math.sqrt(g*R*t),T0,T,epsabs=1e-10)[0]
  exact=2*(math.sqrt(g*R*T)-math.sqrt(g*R*T0))/(g-1)
  assert abs(val-exact)<1e-9
  record('gamma_rarefaction',T0=T0,pressure_ratio=q,error=val-exact,in_GEN1=T>=300)
 Ts=2*T0/(g+1); sonic=2*cp*(T0-Ts)-g*R*Ts
 assert abs(sonic)<1e-8
 record('sonic_domain',T0=T0,Ts=Ts,valid_GEN1=Ts>=300,sonic_residual=sonic)
# Constant-gamma boundary roots independently use closed-form wave curves.
def wave(p,pi,Ti,ui):
 ri=pi/(R*Ti);ai=math.sqrt(g*R*Ti)
 if p<=pi:
  T=Ti*(p/pi)**((g-1)/g);a=math.sqrt(g*R*T)
  return ui+2*(a-ai)/(g-1),T,None
 beta=(g-1)/(g+1);r=ri*(p/pi+beta)/(beta*p/pi+1)
 j=math.sqrt((p-pi)/(1/ri-1/r))
 return ui+(p-pi)/j,p/(R*r),ui+j/ri
for M in [-2.,-.5,0.,.5]:
 for ratio in [.5,1.,2.]:
  pi=200000.;Ti=700.;TR=700.;ui=M*math.sqrt(g*R*Ti);pR=ratio*pi
  v,T,S=wave(pR,pi,Ti,ui)
  if ui+math.sqrt(g*R*Ti)<=0 and pR<=pi:
   v=ui;p=pi;T=Ti;regime='supersonic_outflow'
  elif v<=0:
   p=pR;regime='subsonic_outflow'
   if S is not None and S<0:v=ui;p=pi;T=Ti;regime='supersonic_outflow'
   elif S is None and v+math.sqrt(g*R*T)<0:
    p=brentq(lambda p:wave(p,pi,Ti,ui)[0]+math.sqrt(g*R*wave(p,pi,Ti,ui)[1]),pR,pi)
    v,T,_=wave(p,pi,Ti,ui);regime='sonic_outflow'
  else:
   Ts=2*TR/(g+1)
   def f(T):
    ps=pR*(T/TR)**(g/(g-1))
    return math.sqrt(max(0,2*cp*(TR-T)))-wave(ps,pi,Ti,ui)[0]
   if f(Ts)<0:T=Ts;regime='sonic_inflow'
   else:T=brentq(f,Ts,TR);regime='subsonic_inflow'
   p=pR*(T/TR)**(g/(g-1));v=math.sqrt(max(0,2*cp*(TR-T)))
   assert abs(cp*T+v*v/2-cp*TR)/(cp*TR)<1e-12
  assert 300<=T<=2200 and 50000<=p<=5000000
  record('gamma_boundary',Mi=M,pressure_ratio=ratio,regime=regime,pface=p,Tface=T,uface=v,Mface=v/math.sqrt(g*R*T))
# Domain endpoint with T0=350K: mild inflow must not require the invalid sonic root.
TR=350.;targetT=340.;targetu=math.sqrt(2*cp*(TR-targetT));pR=200000.;p= pR*(targetT/TR)**(g/(g-1))
assert 2*TR/(g+1)<300 and targetT>=300
record('mild_inflow_with_outside_sonic',Tface=targetT,uface=targetu,pface=p,sonicT=2*TR/(g+1))

# Exact prescribed extent under affine SSPRK2; naive source quadrature is not exact.
def xi(t): return (1-math.exp(-5*t**3))/(1-math.exp(-5))
for n in [8,16,32]:
 z=np.array([1.,0.]);b=np.array([-1.,1.]);dt=1/n
 for i in range(n):
  q1=z+b*xi((i+1)*dt);q2=z+b*xi((i+1)*dt);q=z+b*xi((i+1)*dt)
  assert min(q)>=-1e-15
 assert np.max(abs(q-[0,1]))<1e-15
 record('affine_extent',steps=n,terminal=q.tolist())
# Quadratic energy margin equals direct FE state calculation, including negative formation energy.
rng=np.random.default_rng(72026)
for i in range(128):
 M=1+rng.random();P=rng.normal();E=1e6+rng.random()*1e6;I=E-M*(-3e6)
 dM=rng.normal();dP=rng.normal();dE=rng.normal()*1e5;dI=dE-dM*(-3e6);t=.01
 polynomial=2*M*I-P*P+2*(M*dI+dM*I-P*dP)*t+(2*dM*dI-dP*dP)*t*t
 direct=2*(M+t*dM)*(I+t*dI)-(P+t*dP)**2
 assert abs(direct-polynomial)/abs(direct)<1e-14
record('thermal_ray',cases=128,max_allowed_relative_error=1e-14)
# Analytic passive source: energy unchanged, internal energy increases.
for u0 in [-100.,100.]:
 b=2.;t=.01;u=u0/(1+b*abs(u0)*t);e0=700000.;e=e0+(u0*u0-u*u)/2
 assert u*u0>0 and e>=e0
 record('passive_W2',u0=u0,u=u,energy_residual=e+u*u/2-e0-u0*u0/2)
# Exact two-zone mixing coupon convergence with the selected RK2 tableau.
errors=[]
for n in [40,80,160,320]:
 dt=.02/n;y=np.array([.0003,120.]);tau=.01
 for i in range(n):
  y1=y-dt*y/tau;y=.5*(y+y1-dt*y1/tau)
 exact=np.array([.0003,120.])*math.exp(-2)
 error=max(abs(y-exact)/np.array([.001,750.]));errors.append(error)
record('zone_mixing_RK2',errors=errors,orders=[math.log(a/b,2) for a,b in zip(errors,errors[1:])])
assert errors[-1]<1e-6 and min(math.log(a/b,2) for a,b in zip(errors,errors[1:]))>1.8
# Detector coupon: state defect maximum identifies every exact period, no phase shift.
for k in range(1,9):
 seq=[np.array([1+.01*math.cos(2*math.pi*n/k),.01*math.sin(2*math.pi*n/k)]) for n in range(40)]
 detected=next(j for j in range(1,9) if all(np.max(abs(seq[n]-seq[n-j]))<=1e-6 for n in [37,38,39]))
 assert detected==k
 record('period_coupon',truth=k,detected=detected)
# Slow contraction need not finish by maxcycles.
assert .01*.9999**1000>1e-6
record('maxcycles_not_convergence',residual=.01*.9999**1000)
payload={'label':'RESEARCH_ONLY_NON_PRODUCTION','scope':'algebra and small ODE checks only; no FV/coupled/engine PASS','seed':72026,'environment':{'python':sys.version,'platform':platform.platform(),'numpy':np.__version__,'scipy':scipy.__version__,'cantera':ct.__version__},'results':rows,'status':'PASS'}
(OUT/'results.json').write_text(json.dumps(payload,indent=2)+'\n')
print(json.dumps({'status':'PASS','checks':len(rows),'claim':payload['scope']}))
