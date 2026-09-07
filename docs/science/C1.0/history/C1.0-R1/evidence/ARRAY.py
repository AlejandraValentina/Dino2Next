"""RESEARCH_ONLY_NON_PRODUCTION. Exact conservative forward-Euler ray bounds.
No state repair. Polynomial roots locate the first loss of a thermal inequality.
"""
import numpy as np

def first_exit(c):
 c=np.asarray(c,dtype=float);scale=max(abs(c))
 if scale==0:return np.inf
 c=c/scale
 if c[0]<0:raise ValueError('INITIAL_THERMAL_INADMISSIBLE')
 if c[0]==0 and (c[1]<0 or (c[1]==0 and c[2]<0)):return 0.
 roots=np.polynomial.polynomial.polyroots(np.trim_zeros(c,'b'))
 rr=sorted(float(z.real) for z in roots if abs(z.imag)<=64*np.finfo(float).eps*max(1,abs(z.real)) and z.real>0)
 for r in rr:
  # A tangency does not leave the closed admissible set.
  derivative=c[1]+2*c[2]*r
  if derivative<0:return r
 return np.inf

def bound(M,P,E,Mk,dM,dP,dE,dMk,ek_lower,ek_upper):
 """Q=(M,P,E,Mk) all share one volume/area factor; e_k includes formation.
 2 M (E-sum Mk e_k(T)) - P^2 has the sign of T-T_bound for cv>0.
 """
 out={}
 for name,ek,sgn in [('lower',ek_lower,1.),('upper',ek_upper,-1.)]:
  I=E-np.dot(Mk,ek);dI=dE-np.dot(dMk,ek)
  coeff=sgn*np.array([2*M*I-P*P,2*(M*dI+dM*I-P*dP),2*dM*dI-dP*dP])
  out[name]=first_exit(coeff)
 out['mass']=M/-dM if dM<0 else np.inf
 return out
