"""RESEARCH_ONLY_NON_PRODUCTION. Independent polynomial NASA half-Riemann boundary.
Pressure unknown for inflow; reference C05 uses velocity unknown and Cantera quadrature.
No Cd inversion. Equal physical area boundary; T3/W2 loss is inside PDE.
"""
import sys,numpy as np
from pathlib import Path
from scipy.optimize import brentq
from numpy.polynomial.legendre import leggauss
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'c09_dyn2t/research/c09'))
from nasa_fv import RK,CO
Z,W=leggauss(12)
class Gas:
 def __init__(self,Y):
  self.Y=np.asarray(Y);self.R=float(self.Y@RK);self.co=np.array([self.Y@(RK[:,None]*CO[:,8:15]),self.Y@(RK[:,None]*CO[:,1:8])])
 def hcs(self,T):
  T=np.asarray(T);a=self.co[(T>=1000).astype(int)];cp=a[...,0]+T*(a[...,1]+T*(a[...,2]+T*(a[...,3]+T*a[...,4])));h=T*(a[...,0]+T*(a[...,1]/2+T*(a[...,2]/3+T*(a[...,3]/4+T*a[...,4]/5))))+a[...,5];s=a[...,0]*np.log(T)+T*(a[...,1]+T*(a[...,2]/2+T*(a[...,3]/3+T*a[...,4]/4)))+a[...,6];return h,cp,s
 def sound(self,T):
  cp=self.hcs(T)[1];return np.sqrt(cp/(cp-self.R)*self.R*T)
 def isot(self,p,pi,Ti):
  h,cp,si=self.hcs(Ti);target=si+self.R*np.log(p/pi);T=Ti*(p/pi)**(self.R/cp)
  for _ in range(12):
   h,cp,s=self.hcs(T);step=(s-target)*T/cp;T-=step
   if abs(step)<1e-10:return float(T)
  raise ValueError('ISENTROPE_ITERATION_FAILED')
 def wave(self,v,p):
  r,u,pi=v;Ti=pi/(r*self.R);hi,ci,si=self.hcs(Ti)
  if p==pi:return np.array(v,float),[u+self.sound(Ti)]*2
  if p>pi:
   dp=p-pi
   def cvbar(z):
    T=Ti+dp*z
    if (Ti<1000)!=(T<1000):return (self.hcs(T)[0]-hi)/(dp*z)-self.R
    a=self.co[int(T>=1000)];ans=a[0]-self.R
    for k in range(1,5):ans+=a[k]*sum(T**j*Ti**(k-j) for j in range(k+1))/(k+1)
    return ans
   z=brentq(lambda z:z*(cvbar(z)+.5*(p+pi)*self.R/p)-.5*(p+pi)*self.R*Ti/(p*pi),0,Ti/pi,xtol=1e-17,rtol=1e-13)
   T=Ti+dp*z;rb=p/(self.R*T);j=np.sqrt(p/(self.R*(Ti/pi-z)));du=dp/j;speed=u+j/r;return np.array([rb,u+du,p]),[speed,speed]
  T=self.isot(p,pi,Ti);cuts=[Ti,T] if not T<1000<Ti else [Ti,1000,T];integ=0
  for aa,bb in zip(cuts[:-1],cuts[1:]):
   ts=(aa+bb)/2+(bb-aa)*Z/2;cp=self.hcs(ts)[1];integ+=(bb-aa)/2*np.dot(W,cp/self.sound(ts))
  rb=p/(self.R*T);ub=u+integ;return np.array([rb,ub,p]),[u+self.sound(Ti),ub+self.sound(T)]

def solve(pr,Tr,Yr,Ui,Yi,area):
 er,ei=Gas(Yr),Gas(Yi);ub,speeds=ei.wave(Ui,pr)
 if ub[1]<=0:
  gas=ei
  if max(speeds)<=0:v=np.array(Ui);kind='OUTGOING_ALL'
  elif min(speeds)>=0:v=ub;kind='OUTFLOW_PRESSURE'
  else:
   p=brentq(lambda p:ei.wave(Ui,p)[0][1]+ei.sound(ei.wave(Ui,p)[0][2]/(ei.wave(Ui,p)[0][0]*ei.R)),min(pr,Ui[2]),max(pr,Ui[2]));v=ei.wave(Ui,p)[0];kind='OUTFLOW_SONIC'
 else:
  gas=er;hr=er.hcs(Tr)[0];Ts=brentq(lambda T:2*(hr-er.hcs(T)[0])-er.sound(T)**2,200,Tr);ss=er.hcs(Ts)[2];sr=er.hcs(Tr)[2];ps=pr*np.exp((ss-sr)/er.R)
  def state(v):
   if v==0:return np.array([pr/(er.R*Tr),0.,pr])
   if v==er.sound(Ts):return np.array([ps/(er.R*Ts),v,ps])
   T=brentq(lambda T:er.hcs(T)[0]-hr+v*v/2,Ts,Tr,xtol=1e-11)
   p=pr*np.exp((er.hcs(T)[2]-sr)/er.R)
   return np.array([p/(er.R*T),v,p])
  vs=np.array([ps/(er.R*Ts),er.sound(Ts),ps])
  if ei.wave(Ui,ps)[0][1]>=vs[1]:v=vs;kind='INFLOW_SONIC'
  else:
   speed=brentq(lambda speed:speed-ei.wave(Ui,state(speed)[2])[0][1],0,vs[1],xtol=1e-12,rtol=1e-13);v=state(speed);kind='INFLOW_SUBSONIC'
 r,u,p=v;T=p/(r*gas.R);h0=float(gas.hcs(T)[0]+u*u/2);mass=area*r*u;f=np.r_[mass,area*(r*u*u+p),mass*h0,mass*gas.Y]
 if not(300-1e-8<=T<=2200+1e-8 and r>0 and p>0):raise ValueError('BOUNDARY_OUT_OF_DOMAIN')
 return f,dict(face=v.tolist(),T=T,h0=h0,donor='R' if mass>0 else 'D' if mass<0 else 'NONE',kind=kind)

def wall(Ui,Yi,area):
 ei=Gas(Yi);p=Ui[2]
 if Ui[1]==0:return np.r_[0.,area*p,0.,np.zeros(5)]
 lo,hi=p/2,p*2
 for _ in range(12):
  if ei.wave(Ui,lo)[0][1]*ei.wave(Ui,hi)[0][1]<=0:break
  lo/=2;hi*=2
 pw=brentq(lambda pp:ei.wave(Ui,pp)[0][1],lo,hi,xtol=1e-7);return np.r_[0.,area*pw,0.,np.zeros(5)]
