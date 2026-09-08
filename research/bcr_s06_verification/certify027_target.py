"""Contract exact-real contact target: analytic initial enclosure and all-Q lift.
No candidate states corrected. Exact Fraction Machin/Taylor enclosures include
trigonometric initial uncertainty and binary sample timestamp discrepancies.
Requires BCR's explicit exact-real contact-target clarification and invariant
subspace proof; does not certify the ODE starting at rounded off-manifold Q0.
"""
from pathlib import Path
from fractions import Fraction as F
from hashlib import sha256
import numpy as np,json,math,time
OUT=Path(__file__).resolve().parents[2]/'artifacts/S06-BCR/val027';start=time.monotonic()
def exact(x):return F(*x.as_integer_ratio())
def atan_bounds(x,n=24):
 s=sum((-1)**k*x**(2*k+1)/F(2*k+1) for k in range(n));tail=x**(2*n+1)/F(2*n+1)
 return (s,s+tail) if n%2==0 else (s-tail,s)
a,b=atan_bounds(F(1,5));c,d=atan_bounds(F(1,239))
pi_lo=16*a-4*d;pi_hi=16*b-4*c
scale=10**40
pi_lo=F(math.floor(pi_lo*scale),scale);pi_hi=F(math.ceil(pi_hi*scale),scale);pi_mid=(pi_lo+pi_hi)/2
assert 3<pi_lo<pi_hi<4

def cos_bounds(j):
 x=pi_mid*F(j,20);radius=(pi_hi-pi_lo)*F(j,40)
 s=sum((-1)**k*x**(2*k)/F(math.factorial(2*k)) for k in range(31))
 # Taylor through degree61; odd coefficients are zero; derivative magnitude<=1.
 tail=abs(x)**62/F(math.factorial(62))
 return s-tail-radius,s+tail+radius
cosines=[cos_bounds(j) for j in range(41)]
analytic=[]
for j in range(40):
 a,b=cosines[j];c,d=cosines[j+1];lo,hi=a-d,b-c
 products=[lo/(5*pi_lo),lo/(5*pi_hi),hi/(5*pi_lo),hi/(5*pi_hi)]
 analytic.append((1+min(products),1+max(products)))
cert=json.loads((OUT/'exact-residual-refined-certificate.json').read_text());defect=F(cert['weighted_defect_upper_rational'])
inputs=['longdouble-RK4-subdivisions-64.npz','full-kernel-reference.npz','full-kernel-dt-0.000125.npz','scalar-dt-0.00025.npz','exact-residual-refined-certificate.json']
hashes={p:sha256((OUT/p).read_bytes()).hexdigest() for p in inputs}
for name,digest in cert['input_sha256'].items():assert hashes[name]==digest, name
original_path=OUT/'original-full-dt-0.00025.npz'
hashes[str(original_path.relative_to(OUT.parents[2]))]=sha256(original_path.read_bytes()).hexdigest()
scalar=np.load(OUT/inputs[0]);ref=np.load(OUT/inputs[1]);trajectory=scalar['rho'];Q=ref['Q'];times=ref['times']
assert trajectory.shape==(801,40) and Q.shape==(801,40,12) and times.shape==(801,)
assert np.array_equal(scalar['times'],times)
initial=max(max(abs(exact(q)-lo),abs(exact(q)-hi)) for q,(lo,hi) in zip(trajectory[0],analytic))
# exp4.8<122 and exp7.2<1340 using exact Taylor majorants.
def exp_upper(x):
 term=F(1);s=term
 for n in range(1,61):term*=x/n;s+=term
 return s+term*x/61/(1-x/62)
assert exp_upper(F(24,5))<122
assert exp_upper(72*max(F(1,10),max(map(exact,times))))<1340
initial_bound=122*initial
# All exact-real q0 lie inside these intervals; conservative ||F(q0)||∞<1.
# Since every density in[.98,1.02], each MC slope magnitude<=.08 and flux
# neighbor difference<=.12: |F|<=1.44; use2, rigorously, then exp72t<=1340.
assert all(F(98,100)<lo<hi<F(102,100) for lo,hi in analytic)
time_offset=max(abs(exact(t)-F(i,8000)) for i,t in enumerate(times))
time_bound=2680*time_offset
scalar_bound=defect+initial_bound+time_bound
coeff=[F(1),F(3,10),F(9,200),F(0),F(0),F(1),F(0),F(0),F(0),F(0),F(1),F(0)]
constant=[F(0),F(0),F(5,2)]+[F(0)]*9
maxdiff=[F(0)]*12;maxL1=[F(0)]*12;initial_offmanifold=[F(0)]*12
for i in range(801):
 for k in range(12):
  differences=[abs(exact(Q[i,j,k])-(constant[k]+coeff[k]*exact(trajectory[i,j]))) for j in range(40)]
  maxdiff[k]=max(maxdiff[k],max(differences));maxL1[k]=max(maxL1[k],sum(differences)/40)
for k in range(12):
 initial_offmanifold[k]=max(abs(exact(Q[0,j,k])-(constant[k]+coeff[k]*exact(Q[0,j,0]))) for j in range(40))
field_bounds=[maxdiff[k]+abs(coeff[k])*scalar_bound for k in range(12)]
densityL1=maxL1[0]+scalar_bound
rows=[]
for filename,stride,label in [('scalar-dt-0.00025.npz',2,'independent scalar original'),('full-kernel-dt-0.000125.npz',1,'actual full kernel additional'),(str(original_path),2,'actual full kernel original preserved77caaba')]:
 data=np.load(OUT/filename);rho=data['rho'] if 'rho' in data.files else data['Q'][:,:,0]
 assert rho.shape==(len(times[::stride]),40) and data['times'].shape==times[::stride].shape
 assert np.array_equal(data['times'],times[::stride]) and np.isfinite(rho).all()
 error=max(sum(abs(exact(a)-exact(b)) for a,b in zip(row,truth))/40 for row,truth in zip(rho,trajectory[::stride]))
 rows.append({'candidate':label,'lower_rational':str(max(F(0),error-scalar_bound)),'upper_rational':str(error+scalar_bound),'lower_display':float(max(F(0),error-scalar_bound)),'upper_display':float(error+scalar_bound)})
result={'classification':'EXACT_RATIONAL_CONTACT_TARGET_CERTIFICATE_REQUIRES_BCR_TARGET_CLARIFICATION',
 'target':'Exact-real frozen cell-average sinusoidal initial density, u=3/10,p=1,gamma=7/5, periodic selected semidiscrete MC/HLLC contact invariant subspace; NOT ODE initialized at stored off-manifold full Q0.',
 'source_hashes':hashes,'shapes':{'rho':list(trajectory.shape),'Q':list(Q.shape),'times':list(times.shape)},
 'pi_interval':[str(pi_lo),str(pi_hi)],'analytic_initial_enclosure_method':'Machin identity and24-term alternating atan bounds,31-term cos Taylor with exact Lagrange remainder; Fraction throughout',
 'initial_density_discrepancy_bound_rational':str(initial),'initial_density_propagated_bound_rational':str(initial_bound),
 'timestamp_offset_bound_rational':str(time_offset),'timestamp_propagated_bound_rational':str(time_bound),
 'scalar_total_error_bound_rational':str(scalar_bound),'scalar_total_error_bound_display':float(scalar_bound),
 'full_reference_field_max_discrepancy_rational':list(map(str,maxdiff)),
 'full_reference_field_absolute_error_bound_rational':list(map(str,field_bounds)),
 'full_reference_field_absolute_error_bound_display':list(map(float,field_bounds)),
 'full_reference_all_fields_below_1e_minus_11_exact':max(field_bounds)<=F(1,10**11),
 'full_reference_density_max_L1_error_bound_rational':str(densityL1),'full_reference_density_max_L1_error_bound_display':float(densityL1),
 'stored_full_initial_off_contact_manifold_rational':list(map(str,initial_offmanifold)),
 'candidate_density_intervals':rows,
 'limits':['Requires independent proof that exact-real selected RHS preserves this contact subspace; no claim for arbitrary rounded-Q0 ODE.','Any changed post-SV009 RHS requires qualification and regeneration.','No original execution, candidate state, physical input or threshold was changed.'],
 'elapsed_seconds':time.monotonic()-start,'script_sha256':sha256(Path(__file__).read_bytes()).hexdigest()}
(OUT/'contact-target-certificate.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if not k.endswith('_rational') and k not in ['pi_interval']},indent=2))
