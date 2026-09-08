"""Independent scalar diagnostic only. No Dino2Next imports or acceptance gates."""
import json,platform,time
from pathlib import Path
from hashlib import sha256
import numpy as np
OUT=Path(__file__).resolve().parents[2]/'artifacts/S06-BCR/scalar009'
OUT.mkdir(parents=True,exist_ok=True)
SPEED=np.sqrt(1.4);END=.25

def mc(q):
 dm=q-np.roll(q,1);dp=np.roll(q,-1)-q;dc=.5*(dm+dp)
 return np.where(dm*dp>0,np.sign(dc)*np.minimum(abs(dc),2*np.minimum(abs(dm),abs(dp))),0.)

def published_slope(q):
 # Sekora-Colella0903.4200v2 section2.1, HTML equations39-57 (PDF35-51).
 # Undivided second differences absorb h^2; no PPM reconstruction is used.
 dm=q-np.roll(q,1);dp=np.roll(q,-1)-q;dc=.5*(dm+dp)
 dmm=np.roll(dm,1);dpp=np.roll(dp,-1)
 extreme=np.minimum(dm*dp,dmm*dpp)<0
 d2c=dp-dm;d2m=dm-dmm;d2p=dpp-dp;s=np.sign(d2c)
 bound=np.minimum(abs(d2c),np.minimum(np.maximum(s*d2m,0),np.maximum(s*d2p,0)))
 side=np.where(s*dc<0,abs(dm),abs(dp))
 lim=np.minimum(1.25*1.5*bound,2*side)
 return np.where(extreme,np.sign(dc)*np.minimum(abs(dc),lim),mc(q))

def run(n,cfl,method):
 h=1/n;edges=np.linspace(0,1,n+1);x=(edges[1:]+edges[:-1])/2
 exact=lambda t:np.sinc(h)*np.cos(2*np.pi*(x-SPEED*t))
 q=exact(0);initial=q.copy();samples=[q.copy()];times=np.linspace(0,END,101);steps=[];t=0.
 slope=mc if method=='MC' else published_slope
 def rhs(z):
  f=SPEED*(z+.5*slope(z));return -(f-np.roll(f,1))/h
 for target in times[1:]:
  while t<target:
   dt=min(cfl*h/SPEED,float(target-t));z=q+dt*rhs(q);q=.5*(q+z+dt*rhs(z));t=float(target) if dt==target-t else t+dt;steps.append(dt)
  samples.append(q.copy())
 values=np.array(samples);ref=np.array([exact(t) for t in times]);err=abs(values-ref)
 l1=np.mean(err,axis=1);l2=np.sqrt(np.mean(err**2,axis=1));linf=np.max(err,axis=1)
 weights=(np.exp(-2j*np.pi*edges[1:])-np.exp(-2j*np.pi*edges[:-1]))/(-2j*np.pi)
 mode=values@weights;cref=.5*np.exp(-2j*np.pi*SPEED*times);amp=abs(abs(mode/cref)-1);phase=abs(np.angle(mode/cref))
 near=[];nearest=[];energyfrac=[]
 for j,t in enumerate(times):
  # Two extrema; fixed physical radius1/16 independent of observed candidate error.
  distance=np.minimum(abs((x-SPEED*t+.5)%1-.5),abs((x-SPEED*t)%1-.5))
  near.append(float(max(err[j,distance<=1/16])))
  nearest.append(float(max(err[j,np.argsort(distance)[:4]])))
  energyfrac.append(float(np.sum(err[j,distance<=1/16]**2)/np.sum(err[j]**2)) if np.any(err[j]) else 0.)
 raw=OUT/f'VAL009-scalar-{method}-N{n}-CFL{cfl}.npz';np.savez_compressed(raw,times=times,values=values,reference=ref,steps=steps)
 return dict(method=method,N=n,CFL=cfl,steps=len(steps),max_L1=float(max(l1)),max_L2=float(max(l2)),max_Linf=float(max(linf)),final_L1=float(l1[-1]),final_L2=float(l2[-1]),max_Fourier_amplitude_relative=float(max(amp)),max_Fourier_phase_radians=float(max(phase)),max_extrema_neighborhood_error=max(near),max_nearest_extrema_error=max(nearest),final_extrema_L2_energy_fraction=energyfrac[-1],mass_drift=float(max(abs(values.mean(axis=1)-initial.mean()))),raw_file=raw.name,raw_sha256=sha256(raw.read_bytes()).hexdigest())

if __name__=='__main__':
 start=time.monotonic();rows=[run(n,c,m) for m in ['MC','SC_SLOPE_ONLY'] for n in [100,200,400,800] for c in [.2,.1,.05]]
 orders={}
 for m in ['MC','SC_SLOPE_ONLY']:
  seq=[r for r in rows if r['method']==m and r['CFL']==.05]
  orders[m]={norm:np.log2(np.array([r[norm] for r in seq[:-1]])/np.array([r[norm] for r in seq[1:]])).tolist() for norm in ['max_L1','max_L2','max_Linf','max_nearest_extrema_error']}
 report=dict(classification='INDEPENDENT_SCALAR_NUMERICAL_DIAGNOSTIC_NOT_KERNEL_ACCEPTANCE',equation='w_t+sqrt(1.4)w_x=0, periodic x0..1; exact cosine cell averages; w=(rho-1)/epsilon',integrator='SSPRK2, same upwind scalar flux; only slope differs',method_B_limit='Published slope Eqs39-57 only, NOT complete paper MUSCL algorithm (no fourth-order slope stage or Hancock tracing).',extrema_window='Fixed radius1/16 around each exact moving extremum; four nearest cells also recorded. Diagnostic only, no acceptance threshold.',times='101 equally spaced,0..0.25; exact endpoint alignment',source='https://arxiv.org/html/0903.4200v2#S2.SS1',environment=dict(python=platform.python_version(),numpy=np.__version__),script_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),rows=rows,orders=orders,elapsed_seconds=time.monotonic()-start)
 (OUT/'VAL009-independent-scalar.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'orders':orders,'elapsed_seconds':report['elapsed_seconds']},indent=2))
