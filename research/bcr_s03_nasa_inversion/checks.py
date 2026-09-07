"""Small research-only Decimal/Cantera checks, NOT production VAL-001 acceptance."""
from decimal import Decimal as D, getcontext
from pathlib import Path
import argparse
import json
import cantera as ct
from generate import ROOT, OUTPUT, SOURCE, derive, serialized, sha, integral, entropy

getcontext().prec=80
OUT=Path(__file__).parent/'results.json'

def run():
    assert ct.__version__=='3.2.0'
    data=derive(); assert OUTPUT.read_text()==serialized(data)
    species=data['species']; ru=D(data['Ru_J_kmol_K'])
    def pure(s,t,high=None,raw=False):
        high=t>=1000 if high is None else high
        a=list(map(D,s['raw_nasa7_high' if high else 'raw_nasa7_low']))
        r=ru/D(s['MW_kg_kmol']); cp=r*sum(a[i]*t**i for i in range(5))
        h=integral(a,t); ent=entropy(a,t)
        if high and not raw:
            low=list(map(D,s['raw_nasa7_low']))
            # Canonical anchored function, exact continuity in real arithmetic.
            h=integral(low,D(1000))+sum(a[i]*(t**(i+1)-D(1000)**(i+1))/D(i+1) for i in range(5))
            ent=entropy(low,D(1000))+a[0]*(t/D(1000)).ln()+sum(a[i]*(t**i-D(1000)**i)/D(i) for i in range(1,5))
        return cp,r*h,r*h-r*t,r,r*ent
    def mix(t,y,high=None,raw=False):
        values=[pure(s,t,high,raw) for s in species]
        return tuple(sum(y[i]*values[i][j] for i in range(5)) for j in range(5))
    def energy(t,y,index):
        total=D(0)
        for w,s in zip(y,species):
            if not w:continue
            low=list(map(D,s['raw_nasa7_low']));a=list(map(D,s['raw_nasa7_high'])) if t>=1000 else low
            h=integral(low,D(1000))+sum(a[i]*(t**(i+1)-D(1000)**(i+1))/D(i+1) for i in range(5)) if t>=1000 else integral(a,t)
            total+=w*ru/D(s['MW_kg_kmol'])*(h-(t if index==2 else 0))
        return total
    def mass(n):
        a=[D(str(v))*D(s['MW_kg_kmol']) for v,s in zip(n,species)]
        return tuple(v/sum(a) for v in a)
    comps=[(s['name'],tuple(D(i==j) for i in range(5))) for j,s in enumerate(species)]
    comps.append(('air',mass([0,1,'3.76',0,0])))
    for p in ['0.6','0.7','0.8']:
        phi=D(p)
        comps.extend([('premix_'+p,mass([1,D('12.5')/phi,D(47)/phi,0,0])),
                      ('products_'+p,mass([0,D('12.5')/phi-D('12.5'),D(47)/phi,8,9]))])
    gases={}
    for high in [False,True]:
        cs=[]
        for s in species:
            c=ct.Species(s['name'],{k:float(v) for k,v in s['composition'].items()})
            a=list(map(D,s['raw_nasa7_high' if high else 'raw_nasa7_low']))
            if high:a[5]+=D(s['high_delta_a6_K']);a[6]+=D(s['high_delta_a7_dimensionless'])
            # Duplicate explicit branch in both slots: Cantera equality convention cannot select wrong polynomial.
            c.thermo=ct.NasaPoly2(300,2200,float(s['pref_Pa']),[1000,*map(float,a),*map(float,a)])
            cs.append(c)
        gases[high]=ct.Solution(thermo='ideal-gas',species=cs)
    def inverse(target,y,index,seed):
        # Seed changes first trial only; all iterations preserve original target.
        lo,hi=D(300),D(2200); received=target
        # Endpoint values use the same forward arithmetic as fixture creation.
        assert mix(lo,y)[index]<=target<=mix(hi,y)[index]
        trial=D(seed)
        for _ in range(120):
            val=energy(trial,y,index)
            if val<target:lo=trial
            else:hi=trial
            trial=(lo+hi)/2
        assert target==received
        return trial,energy(trial,y,index)-received
    maxima={k:D(0) for k in ['h_minus_e_RT','continuity_h','continuity_s','cantera_cp','cantera_h','cantera_e','cantera_s','cantera_inverse_T','cantera_inverse_residual','inverse_T','inverse_residual','seed_difference','derivative_h','derivative_e','derivative_s','serialized80_h','serialized80_s']}
    def track(k,v):maxima[k]=max(maxima[k],abs(v))
    rows=[]
    temperatures=list(map(D,['300','700','999.999999','999.999999999999','1000','1000.000000000001','1000.000001','1500','2200']))
    for sp in species:
        a=list(map(D,sp['raw_nasa7_high']));r=ru/D(sp['MW_kg_kmol'])
        for t in [D(1000),D('1000.000001'),D(2200)]:
            canonical=pure(sp,t)
            track('serialized80_h',r*(integral(a,t)+D(sp['high_delta_a6_K']))-canonical[1])
            track('serialized80_s',r*(entropy(a,t)+D(sp['high_delta_a7_dimensionless']))-canonical[4])
    for name,y in comps:
        low=mix(D(1000),y,False);high=mix(D(1000),y,True)
        track('continuity_h',high[1]-low[1]);track('continuity_s',high[4]-low[4])
        row={'composition':name,'Y':[str(v) for v in y],'raw_to_derived_high_h_e_shift_J_kg':str(high[1]-mix(D(1000),y,True,True)[1]),
             'raw_to_derived_high_s_shift_J_kg_K':str(high[4]-mix(D(1000),y,True,True)[4]),'temperatures_K':[str(t) for t in temperatures]}
        for t in temperatures:
            cp,h,e,r,s=mix(t,y); assert cp-r>0
            track('h_minus_e_RT',h-e-r*t)
            g=gases[t>=1000];g.TPY=float(t),101325,[float(v) for v in y]
            # Compare weighted standard species entropies at reference pressure,
            # not mixture entropy (which also includes the ideal mixing term).
            standard_s=sum(float(w)*ct.gas_constant/g.molecular_weights[i]*g.standard_entropies_R[i] for i,w in enumerate(y))
            for key,actual,ref in [('cantera_cp',g.cp_mass,cp),('cantera_h',g.enthalpy_mass,h),('cantera_e',g.int_energy_mass,e),('cantera_s',standard_s,s)]:
                track(key,D(str(actual))-ref)
            for idx,value in [(1,h),(2,e)]:
                roots=[]
                for seed in [300,1000,2200]:
                    root,res=inverse(value,y,idx,seed);roots.append(root)
                    track('inverse_T',root-t);track('inverse_residual',res)
                track('seed_difference',max(roots)-min(roots))
                # Independent binary64 root solve with Cantera property calls;
                # target remains the original Decimal fixture energy/enthalpy.
                cl,ch=300.0,2200.0
                for _ in range(60):
                    cm=(cl+ch)/2;cg=gases[cm>=1000]
                    cg.TPY=cm,101325,[float(v) for v in y]
                    cv=cg.enthalpy_mass if idx==1 else cg.int_energy_mass
                    if cv<float(value):cl=cm
                    else:ch=cm
                track('cantera_inverse_T',D(str(cm))-t)
                track('cantera_inverse_residual',D(str(cv))-value)
        for t in [D(500),D(999),D(1001),D(1700)]:
            eps=D('1e-15'); cp,h,e,r,s=mix(t,y)
            before=mix(t-eps,y);after=mix(t+eps,y)
            track('derivative_h',(after[1]-before[1])/(2*eps)-cp)
            track('derivative_e',(after[2]-before[2])/(2*eps)-(cp-r))
            track('derivative_s',(after[4]-before[4])/(2*eps)-cp/t)
        # Opposite-side initial guesses above already cross the join both ways.
        rows.append(row)
    # Preserve RAW counterexample: same input rho,e,Y, TWO admissible roots, no extrapolation.
    y=comps[4][1]; t=D('999.999999'); target=mix(t,y,raw=True)[2]
    rho=D(100000)/(mix(t,y)[3]*t);roots=[]
    for high,lo,hi in [(False,D(300),D(1000)),(True,D(1000),D(2200))]:
        assert mix(lo,y,high,True)[2]<=target<=mix(hi,y,high,True)[2]
        for _ in range(250):
            mid=(lo+hi)/2
            if mix(mid,y,high,True)[2]<target:lo=mid
            else:hi=mid
        root=(lo+hi)/2; assert (D(1000)<=root<=2200) if high else (D(300)<=root<1000)
        pressure=rho*mix(root,y,high,True)[3]*root
        assert D(50000)<=pressure<=D(5000000)
        roots.append({'branch':'high' if high else 'low','interval_K':['1000','2200'] if high else ['300','1000 (excluded)'],
                      'T_K':str(root),'p_Pa':str(pressure),'e_residual_J_kg':str(mix(root,y,high,True)[2]-target)})
    separation=D(roots[1]['T_K'])-D(roots[0]['T_K']); assert separation>D('1e-8')
    for key,val in maxima.items():
        limit=D('1e-8') if key=='cantera_inverse_T' else D('1e-6') if key.startswith('cantera_') else D('1e-20')
        assert val<limit,(key,val,limit)
    return {'classification':'RESEARCH_ONLY_NON_PRODUCTION_NOT_VAL001_ACCEPTANCE','bcr':'BCR-S03-NASA-INVERSION',
      'accepted_reference_commit':'4a358b13ec357bb6e4ae07f5c418d41a17229d42','raw_sha256':sha(SOURCE),'derived_sha256':sha(OUTPUT),
      'decimal_precision':80,'independent_library':'Cantera 3.2.0; separate polynomial evaluator; no candidate imports',
      'checks':'PASS','composition_count':len(comps),'temperature_count':len(temperatures),
      'inverse_checks':len(comps)*len(temperatures)*2*3,'global_monotonicity':'Exact rational cv/R > 0 certificates cover both full intervals for every species; cp=cv+R > 0; continuity joins strictly increasing h and e. Convex mass mixtures inherit positivity.',
      'max_absolute_errors':{k:str(v) for k,v in maxima.items()},'mixtures':rows,
      'raw_counterexample':{'species':species[4]['name'],'rho_kg_m3':str(rho),'Y':[str(v) for v in y],
                           'received_e_J_kg':str(target),'roots':roots,'separation_K':str(separation),'VAL001_temperature_budget_K':'1e-8'},
      'scope_limits':'No physical uncertainty estimate, experimental validation, predictive validation, engine run or downstream-consumer qualification.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    payload=serialized(run())
    if args.check:assert OUT.read_text()==payload,'Research result drift'
    else:OUT.write_text(payload,encoding='utf-8',newline='\n')
    print('BCR bounded research checks: PASS (not production acceptance)')
