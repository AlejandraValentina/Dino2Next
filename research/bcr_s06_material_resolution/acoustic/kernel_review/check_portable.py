"""Read-only compact evidence check. Does not execute a solver or audit absent steps."""
from pathlib import Path
from math import fsum
import gzip,hashlib,json,math,re
import numpy as np

HERE=Path(__file__).resolve().parent;ACOUSTIC=HERE.parent;ROOT=HERE.parents[3]
DATA=ACOUSTIC/'kernel_data';SOURCES=ACOUSTIC/'kernel_sources'
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
load=lambda p:json.loads(p.read_text())
manifest=load(DATA/'manifest.json')
for member in manifest['members']:
 path=(DATA/member['path']).resolve();assert path.is_relative_to(DATA.resolve())
 assert path.stat().st_size==member['size'] and digest(path)==member['sha256'],member['path']
pins=load(HERE/'execution-source-pins.json')
for path,h in pins.items():assert digest(SOURCES/path)==h,path
cert=load(ACOUSTIC/'free_observation_qualification.json');assert cert['status']=='REFERENCE_QUALIFIED' and not cert['candidate_imports']
for path,h in cert['source_hashes'].items():assert digest(ROOT/path)==h,path
mesh=next(x for x in cert['meshes'] if x['N']==1600)
assert mesh['incident_eligible_samples']==list(range(84)) and mesh['reflected_eligible_samples']==list(range(67,101))
reports=[];signals={};primitives={}
for cfl in (.05,.1):
 for eps,label in ((1e-5,'1e-5'),(5e-6,'5e-6')):
  name=f'N1600-CFL{cfl}-eps{label}';folder=DATA/name;case='free-full' if eps==1e-5 else 'free-half';stem=f'{case}-N1600-CFL{cfl}'
  p=folder/(stem+'.json');a=folder/(stem+'-observation-assessment.json');rawp=folder/(stem+'.npz');cost=folder/'cost.txt'
  r=load(p);assessment=load(a);old=load(HERE/(name+'-review.json'))
  assert r['case']['epsilon']==eps and r['CFL']==cfl and r['N']==1600
  assert r['result']=='EXECUTED_METRICS_PENDING_ASSESSMENT' and re.search(r'Exit status:\s*0\s*(?:\n|$)',cost.read_text())
  for path,h in r['hashes'].items():assert pins[path]==h,path
  assert r['source_sha256']==pins['artifacts/S06-exact-sums/streaming/driver.py'] and r['canonical_source_sha256']==pins['validation/fixtures/VAL-006/canonical_execution.py']
  assert digest(p)==old['execution_record_sha256'] and digest(a)==old['assessment_sha256'] and digest(cost)==old['cost_sha256'] and digest(rawp)==r['raw_sha256']==old['raw_sha256']
  assert assessment['observation_sha256']==digest(ACOUSTIC/'observation.py') and assessment['qualification_sha256']==digest(ACOUSTIC/'free_observation_qualification.json') and assessment['assessment_sha256']==pins['validation/fixtures/VAL-006/assessment.py']
  for key in ('rejections','limiter_records'):
   record=r[key];path=folder/record['file'];assert digest(path)==record['sha256'] and record['count']==0
   with gzip.open(path,'rb') as f:contents=f.read()
   assert not contents and hashlib.sha256(contents).hexdigest()==record['uncompressed_sha256']
  assert old['trace_manifests']=={k:r[k] for k in ('steps','rejections','limiter_records')}
  raw=np.load(rawp);Q=raw['Q'];t=raw['times'];edges=raw['cell_bounds'];dx=np.diff(edges)
  assert Q.shape==(101,1600,12) and np.isfinite(Q).all() and np.array_equal(t,np.linspace(0,r['case']['time'],101))
  rho=Q[:,:,0];u=Q[:,:,1]/rho;pfield=.3999999999999999*(Q[:,:,2]-.5*Q[:,:,1]*u)
  assert np.all(rho>0) and np.all(pfield>0) and np.all(Q[:,:,3:]>=0)
  primitive=np.stack((rho,u,pfield),axis=-1);err=abs(primitive-raw['reference_rho_u_p'])
  for key,norm in {'L1':np.sum(dx[None,:,None]*err,axis=1),'L2':np.sqrt(np.sum(dx[None,:,None]*err**2,axis=1)),'Linf':err.max(axis=1)}.items():
   assert np.max(abs(norm-np.array([m[key] for m in r['metrics']])))<3e-15,key
  weights=np.diff(np.exp(-2j*np.pi*edges))/(-2j*np.pi)
  coeff=np.stack(((pfield-1+math.sqrt(1.4)*u)/2,(pfield-1-math.sqrt(1.4)*u)/2,pfield-1),axis=1)@weights
  scaling=eps/1e-5;A0=cert['normalization']['stored_A0']*scaling;A0error=cert['normalization']['stored_A0_error_upper']*scaling
  maxima=np.zeros(3)
  for j in range(101):
   refs={c['name']:c for c in mesh['samples'][j]['components']}
   cr=[complex(*refs[k]['stored_coefficient'])*scaling for k in ('incident','reflected')]
   ce=[refs[k]['stored_coefficient_error_upper']*scaling for k in ('incident','reflected')]
   for k,key in enumerate(('incident','reflected','pressure')):
    z=coeff[j,k];ref=cr[k] if k<2 else sum(cr)
    uncertainty=ce[k] if k<2 else math.nextafter(sum(ce)+2*(math.ulp(ref.real)+math.ulp(ref.imag)),math.inf)
    absolute=(abs(z-ref)+uncertainty)/(A0-A0error);assert absolute<=.01
    maxima[0]=max(maxima[0],absolute)
    if k<2 and refs[key]['phase_and_relative_amplitude_eligible']:
     relative=(abs(abs(z)-abs(ref))+uncertainty)/(abs(ref)-uncertainty)
     assert abs(z)>0
     phase=abs(np.angle(z*np.conj(ref)))+math.asin(uncertainty/abs(ref))
     assert relative<=.01 and phase<=math.pi/1600
     maxima[1]=max(maxima[1],relative);maxima[2]=max(maxima[2],phase)
    saved=assessment['samples'][j]['components'][key];assert saved['passed'] and abs(z-complex(*saved['C']))<3e-16
  inventory=np.array([[fsum(col) for col in (qi*dx[:,None]).T] for qi in Q]);assert np.max(abs(inventory-np.array([m['inventory'] for m in r['metrics']])))<3e-14
  residual=inventory-inventory[0]-np.array([m['boundary'] for m in r['metrics']])-np.array([m['source'] for m in r['metrics']])
  reference=np.full(12,inventory[0,0]);reference[1]*=math.sqrt(1.4);reference[2]=fsum(Q[0,:,2]*dx-.5*Q[0,:,1]*u[0]*dx)
  ledger_upper=float(np.max(abs(residual)/(abs(inventory[0])+reference)));assert ledger_upper<1e-10
  assert ledger_upper==old['strict_ledger_upper_from_lower_denominator']
  signals[cfl,eps]=coeff/A0;primitives[cfl,eps]=primitive
  reports.append({'case':name,'result':'COMPACT_RAW_OBSERVATIONS_AND_LEDGER_CORROBORATED','max_absolute_relative_phase':maxima.tolist(),'ledger_strict_upper':ledger_upper,'raw_sha256':digest(rawp),'prior_full_review_sha256':digest(HERE/(name+'-review.json')),'steps_manifest_count_not_reaudited':r['steps']['count']})
comparisons=[]
for eps in (1e-5,5e-6):comparisons.append({'epsilon':eps,'CFL_sensitivity_not_order':abs(signals[.1,eps]-signals[.05,eps]).max(axis=0).tolist()})
for cfl in (.05,.1):
 d=(primitives[cfl,1e-5]-[1,0,1])/1e-5-(primitives[cfl,5e-6]-[1,0,1])/5e-6
 comparisons.append({'CFL':cfl,'epsilon_normalized_difference_no_subtraction':abs(d).mean(axis=1).max(axis=0).tolist()})
print(json.dumps({'result':'FOUR_COMPACT_CHECKS_PASS_NOT_FULL_TRACE_OR_BATTERY_ACCEPTANCE','cases':reports,'comparisons':comparisons,'limits':['Read-only: no solver, no file writes, no prior review overwritten.','Absent large step streams are NOT reaudited. Their manifests are bound to the previous independent full-stream review; only included empty rejection/limiter streams checked here.','Boundary/source cumulative ledgers are trusted as hash-bound execution records; raw inventories and stricter denominator recomputed, not original full-throughput ST003 rederived.','No whole VAL010/S06/GEN1 acceptance, no extrapolated engine cost.']},indent=2))
