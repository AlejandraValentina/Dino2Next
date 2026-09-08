"""Exact-rational Bernstein enclosure for scalar MC ODE, no floating roots.
The certificate concerns the exact mathematical contact MC ODE and exact stored
initial values. It does not qualify an altered RHS or experimentally validate it.
"""
from pathlib import Path
from fractions import Fraction as F
from hashlib import sha256
import numpy as np,json,time,math
OUT=Path(__file__).resolve().parents[2]/'artifacts/S06-BCR/val027'
start=time.monotonic()
# Reproduce only fine RK4 segments near switches, exactly as original controls.
D=np.longdouble
input_names=['longdouble-RK4-subdivisions-64.npz','full-kernel-reference.npz']
input_hashes={name:sha256((OUT/name).read_bytes()).hexdigest() for name in input_names}
trajectory_data=np.load(OUT/input_names[0])
trajectory=trajectory_data['rho'].astype(D)
assert trajectory.shape==(801,40) and np.isfinite(trajectory).all()
assert trajectory_data['times'].shape==(801,) and np.array_equal(trajectory_data['times'],np.arange(801)*.000125)
ns={'trajectory':trajectory}
def floating_rhs(q):
 l=q-np.roll(q,1);r=np.roll(q,-1)-q;s=np.zeros_like(q)
 pos=(l>0)&(r>0);neg=(l<0)&(r<0)
 s[pos]=np.minimum(np.minimum(2*l[pos],2*r[pos]),(l[pos]+r[pos])/2)
 s[neg]=np.maximum(np.maximum(2*l[neg],2*r[neg]),(l[neg]+r[neg])/2)
 flux=q+s/2
 return -12*(flux-np.roll(flux,1))
segments=[]
micro_h=D('0.000125')/64
for sample in range(800):
 q=trajectory[sample].copy();previous=q.copy();stride=1 if sample in (0,205,557) else 16
 for j in range(64):
  k1=floating_rhs(q);k2=floating_rhs(q+micro_h*k1/2);k3=floating_rhs(q+micro_h*k2/2);k4=floating_rhs(q+micro_h*k3)
  q=q+micro_h*(k1+2*k2+2*k3+k4)/6
  if (j+1)%stride==0:
   segments.append((F(sample*64+j+1-stride,512000),F(stride,512000),previous.copy(),q.copy()));previous=q.copy()
 assert np.array_equal(q,trajectory[sample+1]),sample
def exact(x):return F(*x.as_integer_ratio())
def rhs(q):
 l=[q[i]-q[(i-1)%40] for i in range(40)];r=[q[(i+1)%40]-q[i] for i in range(40)]
 slope=[min(2*a,2*b,(a+b)/2) if a>0 and b>0 else max(2*a,2*b,(a+b)/2) if a<0 and b<0 else F(0) for a,b in zip(l,r)]
 flux=[q[i]+slope[i]/2 for i in range(40)]
 return [-12*(flux[i]-flux[(i-1)%40]) for i in range(40)]
def splitpoly(p):
 a=[(p[i]+p[i+1])/2 for i in range(3)];b=[(a[i]+a[i+1])/2 for i in range(2)];c=(b[0]+b[1])/2
 return [p[0],a[0],b[0],c],[c,b[1],a[2],p[3]]
def split(rows):
 pairs=[splitpoly(p) for p in rows]
 return [p[0] for p in pairs],[p[1] for p in pairs]
def possible(q):
 result=[]
 for i in range(40):
  l=[q[i][k]-q[(i-1)%40][k] for k in range(4)];r=[q[(i+1)%40][k]-q[i][k] for k in range(4)]
  choices=[[F(0)]*4,[(a+b)/2 for a,b in zip(l,r)],[2*a for a in l],[2*a for a in r]]
  if (max(l)<=0 and min(r)>=0) or (min(l)>=0 and max(r)<=0):result.append([choices[0]]);continue
  positive=min(l)>0 and min(r)>0;negative=max(l)<0 and max(r)<0
  selected=None
  if positive or negative:
   for j in range(1,4):
    if all(all((choices[z][k]-choices[j][k] if positive else choices[j][k]-choices[z][k])>=0 for k in range(4)) for z in range(1,4)):
     selected=choices[j];break
  result.append([selected] if selected is not None else choices[1:] if positive or negative else choices)
 return result
# exp(k/10) rational upper bound: Taylor0..40 plus geometric tail.
exp_upper=[]
for k in range(49):
 x=F(k,10);term=F(1);total=term
 for n in range(1,41):term*=x/n;total+=term
 tail=term*x/41/(1-x/42)
 exp_upper.append(total+tail)
count=0;ambiguous=0;depthmax=0

def enclose(q,d,t,h,depth=0):
 global count,ambiguous,depthmax
 choices=possible(q);unknown=any(len(c)>1 for c in choices)
 if unknown and depth<22:
  ql,qr=split(q);dl,dr=split(d)
  return enclose(ql,dl,t,h/2,depth+1)+enclose(qr,dr,t+h/2,h/2,depth+1)
 count+=1;ambiguous+=int(unknown);depthmax=max(depthmax,depth)
 bound=F(0)
 for i in range(40):
  for a in choices[i]:
   for b in choices[(i-1)%40]:
    bound=max(bound,max(abs(d[i][k]+12*(q[i][k]-q[(i-1)%40][k]+(a[k]-b[k])/2)) for k in range(4)))
 exponent=48*(F(1,10)-t);index=min(48,math.ceil(exponent*10))
 return h*bound*exp_upper[index]
rows=[];certificate=F(0)
for i,(t,h,q0,q1) in enumerate(segments):
 # Decimal mesh is exact; initial/endpoint stored binary values are exact.
 t=F(t);h=F(h);q0=list(map(exact,q0));q1=list(map(exact,q1));f0=rhs(q0);f1=rhs(q1)
 q=[[q0[j],q0[j]+h*f0[j]/3,q1[j]-h*f1[j]/3,q1[j]] for j in range(40)]
 d=[]
 for p in q:
  v=[3*(p[k+1]-p[k])/h for k in range(3)]
  d.append([v[0],(v[0]+2*v[1])/3,(2*v[1]+v[2])/3,v[2]])
 contribution=enclose(q,d,t,h);certificate+=contribution
 rows.append({'segment':i,'start':str(t),'step':str(h),'weighted_defect_upper':str(contribution)})
 if i%100==0:print(i,float(certificate),time.monotonic()-start,flush=True)
# Bound discrepancy at every stored reference endpoint, exact rational arithmetic.
full_data=np.load(OUT/'full-kernel-reference.npz')
full=full_data['Q']
assert full.shape==(801,40,12) and np.isfinite(full).all()
assert np.array_equal(full_data['times'],trajectory_data['times'])
assert input_hashes=={name:sha256((OUT/name).read_bytes()).hexdigest() for name in input_names}
traj=ns['trajectory'];delta=F(0)
for a,b in zip(full[:,:,0].flat,traj.flat):delta=max(delta,abs(exact(a)-exact(b)))
initial_delta=max(abs(exact(a)-exact(b)) for a,b in zip(full[0,:,0],traj[0]))
assert exp_upper[48]<122
initial_propagation=122*initial_delta
result={'classification':'EXACT_RATIONAL_SCALAR_MC_CONTINUOUS_DEFECT_ENCLOSURE',
 'certificate_domain':'Scalar exact-arithmetic periodic material-contact MC ODE with stored initial density; transfer to full reference assumes the frozen mathematical contact reduction. Requalify if RHS changes.',
 'input_sha256':input_hashes,'input_shapes':{'rho':[801,40],'Q':[801,40,12],'times':[801]},'scalar_initial_error':0,'full_reference_initial_difference_Linf_rational':str(initial_delta), 'initial_difference_propagated_upper_rational':str(initial_propagation),'global_logarithmic_norm_inf':48,'weighted_defect_upper_rational':str(certificate),'weighted_defect_upper_float_display':float(certificate),
 'full_reference_density_discrepancy_rational':str(delta),'full_reference_density_absolute_error_upper_rational':str(delta+certificate+initial_propagation),'full_reference_density_absolute_error_upper_float_display':float(delta+certificate+initial_propagation),
 'below_1e_minus_11_exact':delta+certificate+initial_propagation<=F(1,10**11),'pieces':count,'ambiguous_pieces_enclosed_with_all_branches':ambiguous,'maximum_subdivision_depth':depthmax,
 'no_floating_root_assumption':True,'arithmetic':'fractions.Fraction exact rational; exp upper by 40-term Taylor with geometric remainder; all MC branch ambiguity enclosed',
 'elapsed_seconds':time.monotonic()-start,'script_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),'rows':rows}
(OUT/'exact-residual-refined-certificate.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2),flush=True)
