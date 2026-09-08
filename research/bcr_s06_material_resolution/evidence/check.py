"""Portable checks of published historical projections, not acceptance reruns."""
from pathlib import Path
import json,hashlib,numpy as np
from scipy.special import erf
ROOT=Path(__file__).resolve().parent
p=json.loads((ROOT/'provenance.json').read_text());results={}
for name,record in p['files'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==record['sha256'],name
d=np.load(ROOT/'contact-window.npz');assert np.array_equal(d['C']-d['A'],d['representation_signed']+d['evolution_difference_signed']);assert np.all(d['A']==100000)
results['contact']=dict(max_pressure_error=float(np.max(abs(d['C']-d['A']))),samples=len(d['times']),classification='PRESERVED_INCOMPLETE_FAILURE_NOT_PASS')
a0=json.loads((ROOT/'acoustic-normalization.json').read_text())['normalization']['stored_A0'];maxima=json.loads((ROOT/'acoustic-maxima.json').read_text())
for n in (200,400,800):
 d=np.load(ROOT/f'acoustic-N{n}.npz');q=d['Q_rho_momentum_energy'];edges=d['cell_bounds'];assert q.shape==(101,n,3)
 rho=q[:,:,0];u=q[:,:,1]/rho;pressure=(1.4-1)*(q[:,:,2]-.5*q[:,:,1]**2/rho);weights=np.diff(np.exp(-2j*np.pi*edges))/(-2j*np.pi)
 values={'incident':(pressure-1+np.sqrt(1.4)*u)/2,'reflected':(pressure-1-np.sqrt(1.4)*u)/2,'pressure':pressure-1};max_dif=0.
 for row in maxima[str(n)]['rows']:
  j=row['sample'];name=row['component'];center=.25+j/100;inc=1e-5*.05*np.sqrt(np.pi)/2*np.diff(erf((edges-center)/.05))/np.diff(edges);center=1.75-j/100;out=-1e-5*.05*np.sqrt(np.pi)/2*np.diff(erf((edges-center)/.05))/np.diff(edges)
  refs={'incident':inc,'reflected':out,'pressure':inc+out};error=abs((values[name][j]-refs[name])@weights)/a0;max_dif=max(max_dif,abs(error-row['absolute_error_over_A0']))
 results[str(n)]=dict(samples=101,max_difference_from_recorded_absolute_metric=max_dif,classification='HISTORICAL_REQUIRED_FAILURE_REPRODUCED_NOT_NEW_PASS')
 # Bound is arithmetic comparison only, not a physical acceptance threshold.
 assert max_dif<1024*np.finfo(float).eps/a0
print(json.dumps(results,indent=2))
