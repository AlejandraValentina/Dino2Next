"""Independent scalar MC temporal/reference controls; does not import production."""
from pathlib import Path
from hashlib import sha256
import json,time,platform
import numpy as np
from scipy.integrate import solve_ivp
import argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output-dir',type=Path,required=True)
OUT=parser.parse_args().output_dir.resolve();OUT.mkdir(parents=True,exist_ok=True)
N=40;c=.3;dx=1/N
edges=np.arange(N+1,dtype=float)/N
initial=1+.01*(np.cos(2*np.pi*edges[:-1])-np.cos(2*np.pi*edges[1:]))/(2*np.pi*dx)
T=np.arange(801)*.000125

def rhs(t,q):
 left=q-np.roll(q,1);right=np.roll(q,-1)-q
 same=(left>0)&(right>0);negative=(left<0)&(right<0)
 slope=np.zeros_like(q);center=(left+right)/2
 slope[same]=np.minimum(np.minimum(2*left[same],2*right[same]),center[same])
 slope[negative]=np.maximum(np.maximum(2*left[negative],2*right[negative]),center[negative])
 flux=q+slope/2
 return -12*(flux-np.roll(flux,1))

def branch(q):
 left=q-np.roll(q,1);right=np.roll(q,-1)-q
 candidates=np.stack(((left+right)/2,2*left,2*right))
 indices=np.argmin(abs(candidates),axis=0)+1
 return np.where(left*right>0,indices,0)

report={'classification':'INDEPENDENT_SCALAR_REFERENCE_DIAGNOSTICS_NOT_FULL_KERNEL_ACCEPTANCE','method':'independent MC contact SSPRK2; DOP853 and fixed-step long-double RK4 controls','levels':[],'longdouble_controls':[],'reference_uncertainty':'Empirical differences/estimators, not absolute certified bounds','environment':{'python':platform.python_version(),'numpy':np.__version__,'longdouble_epsilon':str(np.finfo(np.longdouble).eps)}}
start=time.monotonic()
refs=[]
for rtol,atol in [(2.3e-14,1e-16),(1e-13,1e-15)]:
 sol=solve_ivp(rhs,(0,.1),initial,method='DOP853',rtol=rtol,atol=atol,max_step=.0001,t_eval=T)
 assert sol.success
 refs.append(sol.y.T)
report['DOP_cross_Linf']=float(np.max(abs(refs[0]-refs[1])))
report['DOP_cross_max_time_L1']=float(np.max(np.mean(abs(refs[0]-refs[1]),axis=1)))
np.savez_compressed(OUT/'scalar-DOP-reference.npz',times=T,rho=refs[0],cross=refs[1])
for dt in [.002,.001,.0005,.00025,.000125]:
 q=initial.copy();path=[q.copy()];steps=round(.1/dt)
 for j in range(steps):
  one=q+dt*rhs(j*dt,q);two=one+dt*rhs((j+1)*dt,one);q=(q+two)/2;path.append(q.copy())
 path=np.array(path);ref=refs[0][::800//steps];errors=np.mean(abs(path-ref),axis=1)
 report['levels'].append({'dt':dt,'steps':steps,'max_L1':float(errors.max()),'final_L1':float(errors[-1]),'max_time':float(np.argmax(errors)*dt)})
 np.savez_compressed(OUT/f'scalar-dt-{dt}.npz',times=np.arange(steps+1)*dt,rho=path)
print('Scalar original+extra SSPRK2 completed',flush=True)
previous=None
for subdivisions in [8,16,32,64]:
 # Every original/new candidate sample remains an exact endpoint. This
 # refinement controls the REFERENCE only, never modifies candidate dt.
 h=np.longdouble('0.000125')/subdivisions
 q=initial.astype(np.longdouble);path=[q.copy()];switches=0
 for sample in range(800):
  for j in range(subdivisions):
   old=branch(q)
   k1=rhs(0,q);k2=rhs(0,q+h*k1/2);k3=rhs(0,q+h*k2/2);k4=rhs(0,q+h*k3)
   q=q+h*(k1+2*k2+2*k3+k4)/6
   switches+=int(np.any(old!=branch(q)))
  path.append(q.copy())
 path=np.array(path,dtype=np.longdouble)
 diff=path-refs[0].astype(np.longdouble)
 item={'step':str(h),'steps':800*subdivisions,'subdivisions_per_sample':subdivisions,'branch_change_steps':switches,
       'vs_DOP_Linf':float(np.max(abs(diff))),'vs_DOP_max_time_L1':float(np.max(np.mean(abs(diff),axis=1)))}
 if previous is not None:
  difference=path-previous
  item['successive_difference_Linf']=float(np.max(abs(difference)))
  item['successive_difference_max_time_L1']=float(np.max(np.mean(abs(difference),axis=1)))
 report['longdouble_controls'].append(item)
 np.savez_compressed(OUT/f'longdouble-RK4-subdivisions-{subdivisions}.npz',times=T,rho=path)
 previous=path
 report['elapsed_seconds']=time.monotonic()-start
 (OUT/'scalar-result.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
 print(json.dumps(item),flush=True)
errors=np.array([x['max_L1'] for x in report['levels']]);report['SSPRK2_orders']=np.log2(errors[:-1]/errors[1:]).tolist()
diff=[x.get('successive_difference_max_time_L1') for x in report['longdouble_controls'][1:]]
report['observed_RK4_difference_orders']=np.log2(np.array(diff[:-1])/diff[1:]).tolist()
report['script_sha256']=sha256(Path(__file__).read_bytes()).hexdigest();report['elapsed_seconds']=time.monotonic()-start
(OUT/'scalar-result.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(report,indent=2),flush=True)
