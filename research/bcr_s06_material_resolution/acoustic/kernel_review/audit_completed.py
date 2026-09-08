"""Audit completed original confirmations only; never launch a solver."""
from pathlib import Path
from math import fsum
import argparse,gzip,hashlib,json,math,re,subprocess
import numpy as np
HERE=Path(__file__).resolve().parent;MR=HERE.parents[3];REF=HERE.parent
parser=argparse.ArgumentParser();parser.add_argument('--execution-root',type=Path,required=True);args=parser.parse_args();PERF=args.execution_root
load=lambda p:json.loads(p.read_text())
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
pins=load(HERE/'execution-source-pins.json')
for path,h in pins.items():assert digest(PERF/path)==h,path
cert=load(REF/'free_observation_qualification.json');assert cert['status']=='REFERENCE_QUALIFIED' and not cert['candidate_imports']
for path,h in cert['source_hashes'].items():assert digest(MR/path)==h,path
mesh=next(m for m in cert['meshes'] if m['N']==1600)
assert mesh['incident_eligible_samples']==list(range(84)) and mesh['reflected_eligible_samples']==list(range(67,101))
def events(folder,manifest):
 p=folder/manifest['file'];assert digest(p)==manifest['sha256'];plain=hashlib.sha256();count=0
 with gzip.open(p,'rb') as f:
  for line in f:plain.update(line);count+=1;yield json.loads(line)
 assert count==manifest['count'] and plain.hexdigest()==manifest['uncompressed_sha256']
reports=[];pending=[];arrays={};signals={}
for cfl in [.05,.1]:
 for eps,label in [(1e-5,'1e-5'),(5e-6,'5e-6')]:
  folder=PERF/f'artifacts/S06-MR-kernel/N1600-CFL{cfl}-eps{label}';case='free-full' if eps==1e-5 else 'free-half';stem=f'{case}-N1600-CFL{cfl}';p=folder/(stem+'.json');a=folder/(stem+'-observation-assessment.json');cost=folder/'cost.txt'
  if not all(x.exists() and x.stat().st_size for x in [p,a,cost]) or not re.search(r'Exit status:\s*0\s*(?:\n|$)',cost.read_text()):
   pending.append(folder.name);continue
  rec=load(p);assessment=load(a);assert rec['result']=='EXECUTED_METRICS_PENDING_ASSESSMENT';assert rec['N']==1600 and rec['CFL']==cfl and rec['case']['epsilon']==eps
  for name,h in rec['hashes'].items():assert pins.get(name,digest(PERF/name))==h,name
  assert rec['source_sha256']==pins['artifacts/S06-exact-sums/streaming/driver.py'] and rec['canonical_source_sha256']==pins['validation/fixtures/VAL-006/canonical_execution.py']
  assert assessment['observation_sha256']==digest(REF/'observation.py') and assessment['qualification_sha256']==digest(REF/'free_observation_qualification.json') and assessment['assessment_sha256']==pins['validation/fixtures/VAL-006/assessment.py']
  rawp=folder/(stem+'.npz');assert digest(rawp)==rec['raw_sha256'];raw=np.load(rawp);q=raw['Q'];t=raw['times'];edges=raw['cell_bounds'];dx=np.diff(edges)
  assert q.shape==(101,1600,12) and np.array_equal(t,np.linspace(0,rec['case']['time'],101)) and np.isfinite(q).all();assert len(rec['metrics'])==len(assessment['samples'])==101
  rho=q[:,:,0];u=q[:,:,1]/rho;pfield=(1.4-1)*(q[:,:,2]-.5*q[:,:,1]*u);assert np.all(rho>0) and np.all(pfield>0) and np.all(q[:,:,3:]>=0)
  prim=np.stack((rho,u,pfield),axis=-1);error=abs(prim-raw['reference_rho_u_p']);norms={'L1':np.sum(dx[None,:,None]*error,axis=1),'L2':np.sqrt(np.sum(dx[None,:,None]*error**2,axis=1)),'Linf':error.max(axis=1)}
  for name,val in norms.items():assert np.max(abs(val-np.array([x[name] for x in rec['metrics']])))<3e-15,name
  weights=np.diff(np.exp(-2j*np.pi*edges))/(-2j*np.pi);wav=np.stack(((pfield-1+math.sqrt(1.4)*u)/2,(pfield-1-math.sqrt(1.4)*u)/2,pfield-1),axis=1);coeff=wav@weights
  scale=eps/1e-5;a0=cert['normalization']['stored_A0']*scale;a0e=cert['normalization']['stored_A0_error_upper']*scale;trace=[];failed=[]
  for j in range(101):
   refs={r['name']:r for r in mesh['samples'][j]['components']};cref=[complex(*refs[n]['stored_coefficient'])*scale for n in ['incident','reflected']];unc=[refs[n]['stored_coefficient_error_upper']*scale for n in ['incident','reflected']];components={}
   for k,n in enumerate(['incident','reflected','pressure']):
    v=coeff[j,k];ref=cref[k] if k<2 else sum(cref);e=unc[k] if k<2 else math.nextafter(sum(unc)+2*(math.ulp(ref.real)+math.ulp(ref.imag)),math.inf);absolute=(abs(v-ref)+e)/(a0-a0e);eligible=k<2 and refs[n]['phase_and_relative_amplitude_eligible'];row={'C':[v.real,v.imag],'Cref':[ref.real,ref.imag],'absolute_upper':float(absolute),'eligible':eligible,'passed':absolute<=.01}
    if eligible:
     rel=(abs(abs(v)-abs(ref))+e)/(abs(ref)-e);phase=abs(np.angle(v*np.conj(ref)))+math.asin(e/abs(ref)) if abs(v)>0 else None;row.update(relative_upper=float(rel),phase_upper=None if phase is None else float(phase));row['passed']=row['passed'] and rel<=.01 and phase is not None and phase<=math.pi/1600
    saved=assessment['samples'][j]['components'][n];assert abs(v-complex(*saved['C']))<3e-16 and bool(row['passed'])==saved['passed'];row['passed']=bool(row['passed']);components[n]=row
   if not all(r['passed'] for r in components.values()):failed.append(j)
   trace.append({'sample':j,'time':float(t[j]),'components':components})
  assert not assessment['all_observation_gates_satisfied']==bool(failed)
  previous_path=HERE/(folder.name+'-review.json')
  previous=load(previous_path) if previous_path.exists() else None
  reuse=previous is not None and previous['execution_record_sha256']==digest(p) and previous['raw_sha256']==digest(rawp) and previous['assessment_sha256']==digest(a) and previous['cost_sha256']==digest(cost) and previous['trace_manifests']=={k:rec[k] for k in ['steps','rejections','limiter_records']}
  if reuse:
   for k in ['steps','rejections','limiter_records']:assert digest(folder/rec[k]['file'])==rec[k]['sha256']
   steps=[None]*previous['steps'];rejects=[None]*previous['retries'];limiter_count=previous['limiter_trace_count']
  else:
   steps=[(s['time'],s['dt']) for s in events(folder,rec['steps'])];rejects=[None for _ in events(folder,rec['rejections'])];limiter_count=sum(1 for _ in events(folder,rec['limiter_records']))
   times=np.array([s[0] for s in steps]);dt=np.array([s[1] for s in steps]);assert np.all(dt>0) and np.max(abs(np.diff(np.r_[0.,times])-dt))<1e-15 and times[-1]==t[-1];assert all(np.any(times==ti) for ti in t[1:])
  inv=np.array([[fsum(col) for col in (qi*dx[:,None]).T] for qi in q]);assert np.max(abs(inv-np.array([r['inventory'] for r in rec['metrics']])))<3e-14
  boundary=np.array([r['boundary'] for r in rec['metrics']]);source=np.array([r['source'] for r in rec['metrics']]);residual=inv-inv[0]-boundary-source;reference=np.full(12,inv[0,0]);reference[1]*=math.sqrt(1.4);reference[2]=fsum(q[0,:,2]*dx-.5*q[0,:,1]*u[0]*dx);lower=abs(inv[0])+reference;strict=float(np.max(abs(residual)/lower));assert strict<1e-10
  observed=max(abs(v) for r in rec['metrics'] for v in r['ledger']);assert observed==assessment['ledger_max']
  arrays[cfl,eps]=prim;signals[cfl,eps]=coeff/a0
  out={'case':case,'N':1600,'CFL':cfl,'epsilon':eps,'recorded_commit':rec['commit'],'source_sha256':rec['hashes'],'raw_sha256':rec['raw_sha256'],'execution_record_sha256':digest(p),'assessment_sha256':digest(a),'cost_sha256':digest(cost),'GNU_time_report':cost.read_text(),'execution_elapsed_seconds':rec['elapsed_seconds'],'steps':len(steps),'retries':len(rejects),'limiter_trace_count':limiter_count,'trace_manifests':{k:rec[k] for k in ['steps','rejections','limiter_records']},'failed_samples':failed,'strict_ledger_upper_from_lower_denominator':strict,'reported_original_ledger_max':observed,'all_samples':trace,'result':'OBSERVATION_AND_LEDGER_PASS_CORROBORATED' if not failed else 'VERIFICATION_FAILURE_CORROBORATED'}
  reports.append(out);(HERE/(folder.name+'-review.json')).write_text(json.dumps(out,indent=2)+'\n')
comparison=[]
for eps in [1e-5,5e-6]:
 if (.05,eps) in signals and (.1,eps) in signals:comparison.append({'kind':'CFL_SENSITIVITY_NOT_TEMPORAL_ORDER','epsilon':eps,'max_coefficient_difference_over_A0':abs(signals[.1,eps]-signals[.05,eps]).max(axis=0).tolist()})
for cfl in [.05,.1]:
 if (cfl,1e-5) in arrays and (cfl,5e-6) in arrays:
  difference=(arrays[cfl,1e-5]-[1,0,1])/1e-5-(arrays[cfl,5e-6]-[1,0,1])/5e-6;comparison.append({'kind':'EPSILON_HALVING_NORMALIZED_DIFFERENCE_NOT_ERROR_SUBTRACTION','CFL':cfl,'max_time_mean_absolute_rho_u_p':abs(difference).mean(axis=1).max(axis=0).tolist(),'max_pointwise_rho_u_p':abs(difference).max(axis=(0,1)).tolist()})
summary={'reviewer':'/root/s01_reviewer','result':'INCOMPLETE' if pending else 'FOUR_CONFIRMATIONS_REVIEWED_NOT_FULL_R4_ACCEPTANCE','completed_count':len(reports),'pending':pending,'completed_results':[{k:r[k] for k in ['case','CFL','epsilon','result','failed_samples','recorded_commit','raw_sha256','steps','retries']} for r in reports],'comparisons':comparison,'limits':['No solver execution by auditor; only completed cost exit0, execution record, assessment, all101 raw and fully hash-checked streaming traces are eligible.','A proposed N1600 obligation is not the original R4 battery and does not retrospectively approve failed historical resolutions or S06.','Ledger bound uses original cumulative boundary/source terms and denominator abs(initial inventory)+Qref, omitting positive throughput. It is a stricter upper bound, not exact original ST003 normalization.','GNU time figures are per process with four concurrent kernel jobs; do not interpret as isolated wall-clock benchmarks.','Two CFL values show sensitivity only; both amplitudes actually executed; no normalized remainder subtracted for acceptance.']}
(HERE/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))

