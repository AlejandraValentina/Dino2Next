"""Reference-only certified Simpson remainder + outward interval arithmetic."""
from pathlib import Path
import json,time,hashlib
import mpmath as mp
mp.mp.dps=100;mp.iv.dps=80
iv=mp.iv;OUT=Path(__file__).resolve().parents[2]/'artifacts/S06-BCR'
eps=iv.mpf(1)/100000;sig=iv.mpf(1)/20;k=2*iv.pi
B4=76*eps/sig**4
def endpoints(x):return mp.mpf(x.a),mp.mpf(x.b)
def upper(x):return x.b
def midpoint(x):
 a,b=endpoints(x);return (a+b)/2
def bounds(x):return [str(v) for v in endpoints(x)]
def weight(l,r):
 return iv.mpc((iv.sin(k*r)-iv.sin(k*l))/k,(iv.cos(k*r)-iv.cos(k*l))/k)
def widen(z,e):
 e=upper(e);padding=iv.mpf([-mp.mpf(e),mp.mpf(e)])
 return iv.mpc(z.real+padding,z.imag+padding)
def exact_continuous(mu):
 sigm=mp.mpf('.05');kk=2*mp.pi;zz=kk*sigm/2
 return mp.mpf('1e-5')*sigm*mp.sqrt(mp.pi)/2*mp.exp(-1j*kk*mu-zz*zz)*(mp.erf((1-mu)/sigm+1j*zz)-mp.erf(-mu/sigm+1j*zz))
def contains(z,truth):
 return endpoints(z.real)[0]<=truth.real<=endpoints(z.real)[1] and endpoints(z.imag)[0]<=truth.imag<=endpoints(z.imag)[1]

start=time.monotonic()
# Fixed independent normalization quadrature; the derivative remainder is the certificate.
m=1600;step=iv.mpf(1)/m;a0quad=iv.mpc(0)
for i in range(m+1):
 x=iv.mpf(i)/m;g=eps*iv.exp(-((x-iv.mpf(1)/4)/sig)**2)
 z=iv.mpc(iv.cos(k*x),-iv.sin(k*x))
 a0quad+=(1 if i in (0,m) else 4 if i%2 else 2)*g*z
a0quad*=step/3
Bc=B4+4*k*(20*eps/sig**3)+6*k*k*(6*eps/sig**2)+4*k**3*(2*eps/sig)+k**4*eps
a0error=Bc*step**4/180;a0enclosure=widen(a0quad,a0error);A0=abs(a0enclosure)
assert contains(a0enclosure,exact_continuous(mp.mpf('.25')))
assert endpoints(A0)[0]>0
norm={'subintervals':m,'complex_fourier_real_bounds':bounds(a0enclosure.real),'complex_fourier_imag_bounds':bounds(a0enclosure.imag),'A0_bounds':bounds(A0),'Simpson_remainder_upper':str(mp.mpf(upper(a0error))),'derivative_bound_upper':str(mp.mpf(upper(Bc)))}
meshes=[]
for n in [200,400,800]:
 h=iv.mpf(1)/(8*n);quaderror=B4*h**4/180
 # Gaussian center/sample coordinates are exact mesh vertices for all contracted N.
 # Evenness lets every cell integral be reused through I[-d-1]=I[d].
 table=[]
 for d in range(7*n//4+1):
  q=iv.mpf(0)
  for node in range(9):
   x=(iv.mpf(8*d+node)/(8*n))/sig
   q+=(1 if node in (0,8) else 4 if node%2 else 2)*eps*iv.exp(-x*x)
  table.append(q*h/3)
 weights=[weight(iv.mpf(i)/n,iv.mpf(i+1)/n)*n for i in range(n)]
 centers=set(n//4+j*n//100 for j in range(101))|set(7*n//4-j*n//100 for j in range(101))
 cache={}
 for center in sorted(centers):
  z=iv.mpc(0)
  for i,w in enumerate(weights):
   d=i-center;z+=table[d if d>=0 else -d-1]*w
  # Verify arithmetic width is negligible against analytic quadrature remainder,
  # rather than assuming interval precision itself certifies truncation error.
  width=max(endpoints(z.real)[1]-endpoints(z.real)[0],endpoints(z.imag)[1]-endpoints(z.imag)[0])
  assert width<mp.mpf(upper(quaderror))*mp.mpf('1e-40')
  cache[center]=(z,widen(z,quaderror))
 delta_cert=2*upper(quaderror)  # Covers rectangle radius and measured interval arithmetic width.
 allocation=min(iv.mpf('.001'),iv.mpf('.1')*iv.sin(iv.pi/n))*iv.mpf('.01')*A0.a
 assert mp.mpf(upper(delta_cert))<mp.mpf(allocation.a)
 plus=[];minus=[];rows=[]
 for j in range(101):
  row={'sample':j,'ct_exact':f'{j}/100','components':[]}
  for name,center,sgn in [('incident',n//4+j*n//100,1),('reflected',7*n//4-j*n//100,-1)]:
   z,enclosure=cache[center];z*=sgn;enclosure*=sgn
   magnitude=abs(enclosure);threshold=A0*iv.mpf('.01')
   if mp.mpf(magnitude.a)>=mp.mpf(threshold.b):eligible=True
   elif mp.mpf(magnitude.b)<mp.mpf(threshold.a):eligible=False
   else:raise AssertionError('Mask classification interval intersects threshold')
   if eligible:(plus if name=='incident' else minus).append(j)
   if j in [66,67,75,83,84]:
    # Independent 100-digit erf cell average spot evaluation is tested against
    # the analytic remainder enclosure; agreement is not used as the bound.
    mu=mp.mpf(center)/n;truth=mp.mpc(0);sigma=mp.mpf('.05');kk=2*mp.pi
    for i in range(n):
     l=mp.mpf(i)/n;r=mp.mpf(i+1)/n
     avg=mp.mpf('1e-5')*sigma*mp.sqrt(mp.pi)/2*(mp.erf((r-mu)/sigma)-mp.erf((l-mu)/sigma))*n
     truth+=avg*(mp.exp(-1j*kk*r)-mp.exp(-1j*kk*l))/(-1j*kk)
    assert contains(enclosure,sgn*truth)
   row['components'].append({'name':name,'real_bounds':bounds(enclosure.real),'imag_bounds':bounds(enclosure.imag),'abs_over_A0_bounds':bounds(magnitude/A0),'phase_and_relative_amplitude_eligible':eligible})
  rows.append(row)
 assert plus==list(range(84)) and minus==list(range(67,101))
 meshes.append({'N':n,'Simpson_subintervals_per_cell':8,'gaussian_fourth_derivative_bound':bounds(B4),'quadrature_complex_error_bound':bounds(quaderror),'certified_midpoint_complex_error_upper':str(mp.mpf(upper(delta_cert))),'allocated_reference_error_lower':str(mp.mpf(allocation.a)),'incident_eligible_samples':plus,'reflected_eligible_samples':minus,'samples':rows})
report={'reviewer':'/root/bcr_science_review','role':'Independent review of parent Simpson certification proposal; author of earlier reflection-operator proposal','classification':'REFERENCE_ONLY_CERTIFICATION_NOT_CANDIDATE_ACCEPTANCE','result':'PASS','method':'Composite Simpson8subintervals/cell, analytic fourth-derivative remainder, outward mp.iv80-digit arithmetic; no two-precision difference used as certificate','derivative_proof':'g_fourth/epsilon=(16z^4-48z²+12)exp(-z²)/sigma^4; z²exp(-z²)<=1,z4exp(-z²)<=1 give76/sigma4. Summed cell Simpson errors weighted by |FourierWeight|/dx<=1 yield76eps/sigma4*(dx/8)^4/180.','normalization':norm,'meshes':meshes,'half_amplitude':'Every integral, derivative bound, arithmetic enclosure and A0 scales linearly by1/2; eligibility ratios and relative qualification margins identical. No second candidate/reference execution implied.','normalization_error_in_mask':'Classification uses entireA0 interval and component magnitude interval; every101sample is strictly on one side of .01*A0.','candidate_representation_note':'Reference coefficients are C_h of exactGaussian cell averages; this certifies their reference computation. Candidate errors, phase/amplitude results and kernel gates have not been run.','mpmath_version':mp.__version__,'elapsed_seconds':time.monotonic()-start,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(OUT/'reference-010-certified.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'result':report['result'],'A0':norm,'meshes':[{k:v for k,v in x.items() if k not in ['samples','incident_eligible_samples','reflected_eligible_samples']} for x in meshes],'elapsed_seconds':report['elapsed_seconds']},indent=2))
