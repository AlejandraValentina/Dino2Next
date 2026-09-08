"""Independent linear acoustic compatibility diagnosis; no kernel imports.

Unknowns are w+/epsilon and w-/epsilon. Dimensionless time tau=c*t reduces
transport speeds to+1,-1 exactly; physical times and amplitudes are reported.
This is not candidate acceptance and does not replace any failed kernel case.
"""
from pathlib import Path
import json,math,hashlib,platform,time
import numpy as np
from scipy.special import erf,erfc

ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
C=math.sqrt(1.4);EPS=1e-5;SIGMA=.05
def gaussian_average(edges,center):
    return SIGMA*math.sqrt(math.pi)/2*np.diff(erf((edges-center)/SIGMA))/np.diff(edges)

def slope(ext,n):
    center=ext[...,4:4+n];dm=center-ext[...,3:3+n];dp=ext[...,5:5+n]-center
    mm=ext[...,3:3+n]-ext[...,2:2+n];pp=ext[...,6:6+n]-ext[...,5:5+n]
    dc=(dm+dp)/2;mc=np.sign(dc)*np.minimum(abs(dc),2*np.minimum(abs(dm),abs(dp)))
    mc=np.where(dm*dp>0,mc,0.)
    active=np.minimum(dm*dp,mm*pp)<0;qc=dp-dm;s=np.sign(qc)
    curvature=np.minimum(abs(qc),np.minimum(np.maximum(s*(dm-mm),0),np.maximum(s*(pp-dp),0)))
    side=np.where(s*dc<0,abs(dm),abs(dp));bound=np.minimum(15/8*curvature,2*side)
    return np.where(active,np.sign(dc)*np.minimum(abs(dc),bound),mc)

def bounded_rhs(q,dx):
    n=q.shape[1];left=np.stack((np.zeros(4),q[1,:4][::-1]));right=-q[::-1,-4:][:,::-1]
    s=slope(np.concatenate((left,q,right),axis=1),n)
    flux=np.empty((2,n+1));flux[0,0]=0;flux[0,1:]=q[0]+s[0]/2
    flux[1,:-1]=-q[1]+s[1]/2
    flux[1,-1]=flux[0,-1]  # w-(1)=-w+(1); negative-speed flux=-w-.
    return -np.diff(flux,axis=1)/dx

def extended_rhs(q,dx):
    n=len(q);ext=np.r_[np.zeros(4),q,np.full(4,q[-1])]
    flux=np.r_[0,q+slope(ext,n)/2]
    return -np.diff(flux)/dx

def run(n,cfl):
    start=time.monotonic();dx=1/n;edges=np.linspace(0,1,n+1);xe=np.linspace(-1,3,4*n+1)
    q=np.stack((gaussian_average(edges,.25),-gaussian_average(edges,1.75)))
    f=gaussian_average(xe,.25);samples=[q.copy()];extended=[np.stack((f[n:2*n],-f[2*n:3*n][::-1]))]
    taus=np.linspace(0,1,101);tau=0.;steps=[]
    for target in taus[1:]:
        while tau<target:
            dt=min(cfl*dx,float(target-tau))
            z=q+dt*bounded_rhs(q,dx);q=.5*(q+z+dt*bounded_rhs(z,dx))
            z=f+dt*extended_rhs(f,dx);f=.5*(f+z+dt*extended_rhs(z,dx))
            steps.append(dt);tau=float(target) if dt==target-tau else tau+dt
        samples.append(q.copy());extended.append(np.stack((f[n:2*n],-f[2*n:3*n][::-1])))
    values=np.array(samples);folded=np.array(extended)
    exact=np.array([np.stack((gaussian_average(edges,.25+t),-gaussian_average(edges,1.75-t))) for t in taus])
    # Qualified reference observation and masks are read as immutable DATA only.
    cert=json.loads((OUT/'free_observation_qualification.json').read_text())
    assert cert['status']=='REFERENCE_QUALIFIED'
    for path,digest in cert['source_hashes'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest
    mesh=next(m for m in cert['meshes'] if m['N']==n);a0=cert['normalization']['stored_A0']
    weights=np.diff(np.exp(-2j*np.pi*edges))/(-2j*np.pi)
    trace=[];failed=[]
    for j,tau in enumerate(taus):
        row=dict(sample=j,tau=float(tau),time=float(tau/C),components={})
        refs={v['name']:v for v in mesh['samples'][j]['components']}
        for k,name in enumerate(('incident','reflected','pressure')):
            signal=values[j,k] if k<2 else values[j].sum(axis=0)
            cref=complex(*refs[name]['stored_coefficient']) if k<2 else sum(complex(*refs[x]['stored_coefficient']) for x in ('incident','reflected'))
            coeff=EPS*(signal@weights);delta=abs(coeff-cref)
            eligible=refs[name]['phase_and_relative_amplitude_eligible'] if k<2 else False
            relative=abs(abs(coeff)-abs(cref))/abs(cref) if abs(cref)>0 else None
            phase=abs(np.angle(coeff*np.conj(cref))) if abs(cref)>0 and abs(coeff)>0 else None
            referr=refs[name]['stored_coefficient_error_upper'] if k<2 else sum(refs[x]['stored_coefficient_error_upper'] for x in ('incident','reflected'))
            a0err=cert['normalization']['stored_A0_error_upper']
            absolute_upper=(delta+referr)/(a0-a0err)
            relative_upper=(abs(abs(coeff)-abs(cref))+referr)/(abs(cref)-referr) if eligible else None
            phase_upper=phase+math.asin(min(1.,referr/abs(cref))) if eligible and phase is not None else None
            passed=absolute_upper<=.01 and (not eligible or (relative_upper<=.01 and phase_upper is not None and phase_upper<=np.pi/n))
            row['components'][name]=dict(C_over_A0=[coeff.real/a0,coeff.imag/a0],Cref_over_A0=[cref.real/a0,cref.imag/a0],
                abs_Cref_over_A0=abs(cref)/a0,absolute_error_over_A0=delta/a0,relative_amplitude_error=relative,
                phase_error_radians=None if phase is None else float(phase),phase_defined=phase is not None,
                phase_eligible=eligible,phase_status='ASSESSED' if eligible else 'NOT_ASSESSED_BELOW_DECLARED_ABSOLUTE_RESOLUTION' if k<2 else 'ABSOLUTE_COMPLEX_GATE_ONLY',
                absolute_error_upper_over_A0=absolute_upper,relative_amplitude_upper=relative_upper,phase_upper=phase_upper,diagnostic_threshold_pass=bool(passed))
        if not all(x['diagnostic_threshold_pass'] for x in row['components'].values()):failed.append(j)
        trace.append(row)
    maxima={}
    for name in ('incident','reflected','pressure'):
        maxima[name]={}
        for metric in ('absolute_error_over_A0','relative_amplitude_error','phase_error_radians','absolute_error_upper_over_A0','relative_amplitude_upper','phase_upper'):
            rows=[r for r in trace if r['components'][name][metric] is not None and (metric in ('absolute_error_over_A0','absolute_error_upper_over_A0') or r['components'][name]['phase_eligible'])]
            if rows:
                r=max(rows,key=lambda r:r['components'][name][metric]);maxima[name][metric]=dict(sample=r['sample'],time=r['time'],**r['components'][name])
    profile=[]
    for j in (25,50,60,67,74,75,83,100):
        profile.append(dict(sample=j,incident_L1_over_initial_mass=float(np.sum(abs(values[j,0]-exact[j,0]))*dx/(SIGMA*np.sqrt(np.pi))),
            incident_peak_ratio=float(max(values[j,0])/max(exact[j,0]))))
    raw=OUT/f'linear-N{n}-CFL{cfl}.npz';np.savez_compressed(raw,times=taus/C,values=values,folded_extended=folded,reference=exact,edges=edges,steps=steps)
    report=dict(classification='INDEPENDENT_LINEAR_ACOUSTIC_DIAGNOSTIC_NOT_KERNEL_ACCEPTANCE',N=n,CFL=cfl,steps=len(steps),elapsed_seconds=time.monotonic()-start,
        failed_samples=failed,maxima=maxima,samples=trace,profile=profile,
        bounded_vs_folded_max_point=float(np.max(abs(values-folded))),
        bounded_vs_folded_max_C_over_A0=float(EPS*np.max(abs((values-folded)@weights))/a0),
        initial_left_gaussian_tail_mass_over_A0=float(EPS*SIGMA*np.sqrt(np.pi)/2*erfc(5)/a0),
        raw_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        certified_observation_sha256=hashlib.sha256((OUT/'free_observation_qualification.json').read_bytes()).hexdigest(),
        epsilon_coverage=[1e-5,5e-6],amplitude_scaling='Positive homogeneous slope and linear SSPRK2/BC: evolve dimensionless w/epsilon once; coefficients, reference enclosure and A0 all scale by epsilon. This does not establish nonlinear-kernel half-amplitude equivalence.',normalization='w/epsilon evolved; coefficients restored to originalepsilon1e-5. Linear homogeneity is exact; no candidate nonlinear remainder subtracted.',
        mask_policy='Original qualified masks preserved. All errors retained; diagnostic thresholds do not certify the scalar approximation as an oracle.',
        environment=dict(python=platform.python_version(),numpy=np.__version__))
    (OUT/f'linear-N{n}-CFL{cfl}.json').write_text(json.dumps(report,indent=2)+'\n')
    print(n,cfl,'failed',failed,'boundary_difference',report['bounded_vs_folded_max_C_over_A0'],'seconds',report['elapsed_seconds'],flush=True)
    return report

if __name__=='__main__':
    reports=[run(1600,.05)]
    (OUT/'reduction-summary.json').write_text(json.dumps([{k:r[k] for k in ('N','CFL','failed_samples','maxima','bounded_vs_folded_max_C_over_A0','profile','code_sha256','raw_sha256')} for r in reports],indent=2)+'\n')
