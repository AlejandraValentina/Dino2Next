"""Bounded reference-only qualification. Never imports the candidate.

Analytic quadrature bounds are separate from high-precision sensitivity checks.
No kernel, experimental or predictive acceptance is inferred.
"""
from pathlib import Path
import hashlib,json,platform,time,sys
import numpy as np
import scipy
import mpmath as mp
import reference as ref
from interval_bounds import bounds,gaussian_remainder
from floating_bounds import certificate as floating_certificate
from root_certificate import certify as certify_root

HERE=Path(__file__).resolve().parent
OUT=ref.ROOT/'artifacts/S06-R4/reference008'
mp.mp.dps=80

class MP:
    """Separate decimal-token implementation of the anchored TI-001 definition."""
    def __init__(self,name):
        raw=json.loads(ref.RAW_PATH.read_text(),parse_float=mp.mpf,parse_int=mp.mpf)
        species=raw['species'][:5];mw=[x['MW_kg_kmol'] for x in species]
        if name in ('N2','CO2'):n=[mp.mpf(int(j==(2 if name=='N2' else 3))) for j in range(5)]
        else:
            phi=mp.mpf('.7');n=([1,mp.mpf('12.5')/phi,47/phi,0,0] if name=='premix' else [0,mp.mpf('12.5')/phi-mp.mpf('12.5'),47/phi,8,9])
        total=sum(a*b for a,b in zip(n,mw));self.y=[a*b/total for a,b in zip(n,mw)]
        # Pure species n=1 produces exactly the intended mass fraction too.
        ru=raw['Ru_J_kmol_K'];self.r=sum(y*ru/m for y,m in zip(self.y,mw))
        self.low=[sum(self.y[k]*ru/mw[k]*species[k]['coeffs'][8+j] for k in range(5)) for j in range(7)]
        self.high=[sum(self.y[k]*ru/mw[k]*species[k]['coeffs'][1+j] for k in range(5)) for j in range(7)]
        for j,fn in ((5,self._h),(6,self._s)):
            self.high[j]+=fn(self.low,mp.mpf(1000))-fn(self.high,mp.mpf(1000))
    def coeff(self,t):return self.low if t<1000 else self.high
    def _h(self,a,t):return sum(a[j]*t**(j+1)/(j+1) for j in range(5))+a[5]
    def _s(self,a,t):return a[0]*mp.log(t)+sum(a[j]*t**j/j for j in range(1,5))+a[6]
    def h(self,t):return self._h(self.coeff(t),t)
    def s(self,t):return self._s(self.coeff(t),t)
    def cp(self,t):return sum(self.coeff(t)[j]*t**j for j in range(5))
    def a(self,t):return mp.sqrt(self.r*t*self.cp(t)/(self.cp(t)-self.r))
    def integral(self,lo,hi):return mp.quad(lambda t:self.cp(t)/self.a(t),[lo,hi])

def precise(solution):
    names=(('N2','CO2'),('N2','CO2'),('premix','products'))[solution.case.pair]
    l,r=map(MP,names);p0=mp.mpf(100000);pl=p0*mp.mpf(str(solution.case.pressure_ratio));t0=mp.mpf(700)
    def equations(tl,tr,p):
        ul=l.integral(tl,t0);ur=mp.sqrt((p-p0)*(r.r*t0/p0-r.r*tr/p))
        return (l.s(tl)-l.s(t0)-l.r*mp.log(p/pl),r.h(tr)-r.h(t0)-(p-p0)*(r.r*tr/p+r.r*t0/p0)/2,ul-ur)
    tl,tr,p=mp.findroot(equations,(solution.tstar_l,solution.tstar_r,solution.pstar),tol=mp.mpf('1e-65'),maxsteps=15)
    residual=equations(tl,tr,p);u=l.integral(tl,t0)
    assert max(abs(x) for x in residual)<mp.mpf('1e-60')
    assert 300<tl<700<tr<2200 and p0<p<pl
    shock=mp.sqrt((p-p0)/(r.r*t0/p0-r.r*tr/p))/(p0/(r.r*t0))
    speeds=[-l.a(t0),u-l.a(tl),u,shock]
    return dict(T_left=str(tl),T_right=str(tr),pressure=str(p),velocity=str(u),wave_speed_differences=[abs(float(a)-b) for a,b in zip(speeds,solution.speeds)],
        residuals=[str(x) for x in residual],float_differences=dict(T_left=abs(float(tl)-solution.tstar_l),T_right=abs(float(tr)-solution.tstar_r),pressure=abs(float(p)-solution.pstar),velocity=abs(float(u)-solution.ustar)))

def scales(solution):
    l=solution.initial_left;r=solution.initial_right
    rho=max(l[0],r[0]);a=max(solution.left.sound(solution.tl),solution.right.sound(solution.tr))
    energy=max(abs(l[11]),abs(r[11]),rho*a*a)
    return np.array([rho,a,1e5,2200]+[rho]*5+[rho,rho*a,energy]+[rho]*9)

def flux(row):
    u=row[1];p=row[2];q=row[9:];f=q*u;f=f.copy();f[1]+=p;f[2]+=p*u;return f

def checksum(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    OUT.mkdir(parents=True,exist_ok=True);start=time.monotonic();rows=[];unique={}
    cache=None
    if '--reuse-sampling' in sys.argv:
        path=OUT/'initial-diagnostic/qualification.json';cache=json.loads(path.read_text())
        assert cache['reference_sha256']==checksum(HERE/'reference.py')
        assert cache['dataset_raw_sha256']==checksum(ref.RAW_PATH)
        assert cache['fixture_sha256']==checksum(ref.ROOT/'docs/science/C1.0/EXECUTABLE_VALIDATION_FIXTURES.json')
        assert cache['environment']['numpy']==np.__version__ and cache['environment']['scipy']==scipy.__version__
    for case in ref.cases():
        s=ref.solve(case);scale=scales(s)
        if case.pressure_ratio is None:
            checks=[]
            for n in (100,200,400):
                edges=np.linspace(0,1,n+1)
                for t in np.linspace(0,case.final_time,101):
                    got=s.cell_averages(edges,t)
                    fraction=np.maximum(0,np.minimum(edges[1:],.5+case.velocity*t)-edges[:-1])*n
                    expected=fraction[:,None]*s.initial_left+(1-fraction[:,None])*s.initial_right
                    actual=np.concatenate((np.stack([got[k] for k in ('rho','u','p','T')],axis=-1),got['rhoY'],got['conserved']),axis=-1)
                    checks.append(float(np.max(abs(actual-expected)/scale)))
            arithmetic=floating_certificate(s,scale)
            bound=np.array(arithmetic['normalized_bounds'])
            assert max(checks)<max(bound)<5e-5
            rows.append(dict(parameters=case.__dict__,name=case.name,kind='exact_material_contact',comparisons=303,max_normalized_error=max(checks),
                total_normalized_reference_bound=bound.tolist(),normalization=scale.tolist(),floating_certificate=arithmetic,status='PASS'))
            continue
        key=(0 if case.pair==1 else case.pair,case.pressure_ratio)
        if key in unique:
            row=dict(unique[key]);row['parameters']=case.__dict__;row['name']=case.name;row['duplicate_original_case_of']=unique[key]['name'];rows.append(row);continue
        hp=precise(s);b=bounds(s);hp=certify_root(s,hp,b);max_t_dx=.0002*640
        assert .5+s.case.final_time*(s.head-hp['wave_speed_differences'][0])>.3
        assert .5+s.case.final_time*(s.tail+hp['wave_speed_differences'][1])<.6
        # Gauss16/32 reproduce degree4 (including |x-mid|^4), not merely degree3.
        # Account also for endpoint/node rounding in nominal4m/s subdivisions.
        panel_width=4+64*np.finfo(float).eps/(s.case.final_time/100)
        error=np.array(b['fourth_xi_derivative'])*panel_width**4*(s.tail-s.head)/960*max_t_dx
        velocity_integral_error=np.nextafter(2*gaussian_remainder(b['f16_taylor_coefficient'],16,(s.tl-s.tstar_l)/2)*(1+64*np.finfo(float).eps),np.inf)
        assert velocity_integral_error<1e-9
        arithmetic=floating_certificate(s,scale,b,hp,velocity_integral_error)
        error=np.nextafter(error*(1+64*np.finfo(float).eps),np.inf)
        normalized=np.nextafter(error/scale+arithmetic['normalized_bounds'],np.inf)
        assert max(normalized)<5e-5,'REFERENCE_NOT_QUALIFIED: analytic allocation exceeded'
        discrepancies=[];conservation=[];snapshot={}
        cached=next((row for row in cache['cases'] if row['parameters']==case.__dict__),None) if cache else None
        for n in (() if cached else (80,160,320,640)):
            edges=np.linspace(0,1,n+1)
            for j,t in enumerate(np.linspace(0,case.final_time,101)):
                a=s.cell_averages(edges,t,16);c=s.cell_averages(edges,t,32)
                def pack(q):return np.concatenate((np.stack([q[k] for k in ('rho','u','p','T')],axis=-1),q['rhoY'],q['conserved']),axis=-1)
                aa,cc=pack(a),pack(c);discrepancies.append(float(np.max(abs(aa-cc)/scale)))
                # Selfsimilar conservation yields an exact integral over[0,1]
                # with initial states at both boundaries throughout this fixture.
                expected=.5*(s.initial_left[9:]+s.initial_right[9:])+t*(flux(s.initial_left)-flux(s.initial_right))
                conservation.append(float(np.max(abs(c['conserved'].mean(axis=0)-expected)/scale[9:])))
                if n==640 and j in (0,1,50,100):snapshot[f't{j}']=cc
        raw=OUT/(case.name+'.npz')
        if cached:
            assert checksum(raw)==cached['raw_sha256']
            discrepancies=[cached['max_gauss16_32_normalized_difference']]
            conservation=[cached['max_selfsimilar_conservation_normalized_difference']]
        else:np.savez_compressed(raw,**snapshot)
        assert max(discrepancies)<max(normalized)
        assert max(conservation)<max(normalized)
        row=dict(parameters=case.__dict__,name=case.name,status='PASS',kind='independent_NASA_Riemann',precise80=hp,interval_derivative_bounds=b,
            sampling_comparisons=404,max_gauss16_32_normalized_difference=max(discrepancies),max_selfsimilar_conservation_normalized_difference=max(conservation),
            absolute_quadrature_bounds=error.tolist(),panel_width_bound=panel_width,normalization=scale.tolist(),floating_certificate=arithmetic,
            velocity_integral_error_bound=velocity_integral_error,total_normalized_reference_bound=normalized.tolist(),
            required_allocation_normalized=5e-5,wave_speeds=s.speeds.tolist(),raw_file=raw.name,raw_sha256=checksum(raw))
        rows.append(row);unique[key]=row
        print(case.name,'PASS',max(normalized),flush=True)
    report=dict(status='REFERENCE_QUALIFIED',classification='NUMERICAL_REFERENCE_ONLY_NOT_KERNEL_ACCEPTANCE',reference_sha256=checksum(HERE/'reference.py'),
        qualifier_sha256=checksum(Path(__file__)),interval_bounds_sha256=checksum(HERE/'interval_bounds.py'),
        dataset_raw_sha256=checksum(ref.RAW_PATH),dataset_runtime_sha256=checksum(ref.ROOT/'docs/science/C1.0/datasets/thermo_runtime_continuous_v1.json'),
        fixture_sha256=checksum(ref.ROOT/'docs/science/C1.0/EXECUTABLE_VALIDATION_FIXTURES.json'),
        arithmetic_model='IEEE754 basic error<=eps; sqrt/log/exp/smallintegerpowers<=4eps. Outward interval forward propagation per operation includes actual binary coefficient errors, certified Gauss nodes/weights, energy formation/cancellation and averaging/edge location. No guessed gamma4096 or normalized floor.',
        qualification='Outward interval derivative bounds + positive-Gauss Taylor remainder; independent80 roots and exact conservation identities. Gauss16/32 differences are diagnostics, not the certificate.',
        candidate_imports=False,sampling_cache_sha256=checksum(OUT/'initial-diagnostic/qualification.json') if cache else None,
        cases=rows,environment=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,mpmath=mp.__version__),elapsed_seconds=time.monotonic()-start)
    paths=[HERE/x for x in ('reference.py','qualify.py','interval_bounds.py','floating_bounds.py','root_certificate.py','cantera_check.py','prepare_cantera.py','test_reference.py','requirements.txt','requirements-cantera.txt')]
    paths +=[ref.RAW_PATH,ref.ROOT/'docs/science/C1.0/datasets/thermo_runtime_continuous_v1.json',ref.ROOT/'docs/science/C1.0/EXECUTABLE_VALIDATION_FIXTURES.json',ref.ROOT/'docs/science/C1.0/EXECUTABLE_VALIDATION_CATALOGUE.md']
    report['source_hashes']={str(p.relative_to(ref.ROOT)):checksum(p) for p in paths}
    cantera=json.loads((OUT/'cantera-check.json').read_text());assert cantera['status']=='PASS'
    assert cantera['raw_sha256']==checksum(ref.RAW_PATH)
    assert cantera['code_sha256']==checksum(HERE/'cantera_check.py') and cantera['input_sha256']==checksum(OUT/'cantera-inputs.json')
    report['cantera_check']=dict(status='PASS',samples=cantera['cases'],artifact_sha256=checksum(OUT/'cantera-check.json'))
    (HERE/'qualification.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'],report['elapsed_seconds'])

if __name__=='__main__':main()
