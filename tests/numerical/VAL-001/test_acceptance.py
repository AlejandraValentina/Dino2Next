"""Frozen VAL-001 catalogue acceptance, with independent qualified references."""
from dataclasses import asdict
from decimal import Decimal as D, localcontext
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path
import sys

import pytest

from dino2next.geometry import CrankGeometry
from dino2next.thermo import ThermoDataset, ThermoModel

ROOT = Path(__file__).resolve().parents[3]
REFERENCE = ROOT/'validation/references/VAL-001/reference.json'
FIXTURE = ROOT/'validation/fixtures/VAL-001/input.json'
EXPECTED = ROOT/'validation/expected/VAL-001/acceptance.json'


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope='module')
def model():
    base=ROOT/'docs/science/C1.0/datasets'
    paths=[base/'thermo_runtime_continuous_v1.json',base/'thermo_species.json',
           base/'thermo_transport.yaml',ROOT/'research/bcr_s03_nasa_inversion/generate.py']
    return ThermoModel(ThermoDataset.from_files(
        *paths,expected_sha256=digest(paths[0]),expected_raw_sha256=digest(paths[1]),
        expected_transport_sha256=digest(paths[2]),expected_generator_sha256=digest(paths[3])))


def test_qualified_independent_reference_identity():
    ref,fixture=load(REFERENCE),load(FIXTURE)
    assert ref['qualification']['result']=='PASS'
    assert ref['qualification']['decimal_digits']==80
    assert ref['environment']['cantera']=='3.2.0'
    assert ref['environment']['numpy']=='2.2.6'
    assert ref['qualification']['property_scaled_max']<=1e-8
    assert ref['qualification']['candidate_imports'] is False
    assert ref['qualification']['generator_evaluator_imports'] is False
    assert ref['fixture_sha256']==digest(FIXTURE)
    for path,sha in ref['hashes'].items():
        assert digest(ROOT/path)==sha, f'Reference stale: {path}'
    assert fixture['temperatures_K']==['300','350','400','600','999.999999','1000','1000.000001','1600','2200']
    assert fixture['pressures_Pa']==[50000,100000,1000000,5000000]
    assert len(fixture['compositions'])==12
    assert len(ref['rows'])==108
    assert ref['physical_uncertainty']=='NOT_ESTIMATED'
    assert {(r['composition'],r['T']) for r in ref['rows']} == {
        (c['name'],t) for c in fixture['compositions'] for t in fixture['temperatures_K']}
    # These are frozen contract values, not caller-controlled tolerance inputs.
    limits=load(EXPECTED)
    assert limits['property_scaled_max']==limits['temperature_error_K']==1e-8
    assert limits['energy_residual_cv_K']==limits['enthalpy_residual_cp_K']==1e-8
    assert limits['identity_gamma_n']==128


def test_certified_cv_positive_on_entire_domain(model):
    """Recompute the frozen exact rational certificate, not positivity sampling."""
    derived=load(ROOT/'docs/science/C1.0/datasets/thermo_runtime_continuous_v1.json')
    for i,species in enumerate(derived['species']):
        for branch,start,end in (('low',300,1000),('high',1000,2200)):
            coefficients=list(map(F,species['raw_nasa7_'+branch][:5]))
            # Identity with the coefficients actually installed in production.
            assert getattr(model.dataset.species[i],branch)[:5]==tuple(map(float,coefficients))
            coefficients[0]-=1
            certificates=species['global_cv_positivity_certificate'][branch]
            previous=F(start)
            for certificate in certificates:
                a,b=map(F,certificate['interval_K'])
                assert a==previous and b>a
                power=[sum(coefficients[j]*math.comb(j,k)*a**(j-k)*(b-a)**k
                           for j in range(k,5)) for k in range(5)]
                bernstein=[sum(power[k]*F(math.comb(j,k),math.comb(4,k))
                               for k in range(j+1)) for j in range(5)]
                assert min(bernstein)==F(certificate['cv_over_R_lower_exact'])>0
                assert max(bernstein)==F(certificate['cv_over_R_upper_exact'])
                previous=b
            assert previous==end


def test_preserved_raw_duplicate_root_regression():
    """Both original roots still solve the unchanged RAW problem on valid branches."""
    example=load(ROOT/'research/bcr_s03_nasa_inversion/results.json')['raw_counterexample']
    with localcontext() as ctx:
        ctx.prec=80
        source=json.loads((ROOT/'docs/science/C1.0/datasets/thermo_species.json').read_text(),parse_float=D)
        water=source['species'][4]
        r=source['Ru_J_kmol_K']/water['MW_kg_kmol']
        target=D(example['received_e_J_kg'])
        rho=D(example['rho_kg_m3'])
        assert list(map(D,example['Y']))==[0,0,0,0,1]
        temperatures=[]
        for root in example['roots']:
            t=D(root['T_K'])
            if root['branch']=='low':
                assert 300<=t<1000
                a=water['coeffs'][8:]
            else:
                assert root['branch']=='high' and 1000<=t<=2200
                a=water['coeffs'][1:8]
            h=r*(sum(a[j]*t**(j+1)/D(j+1) for j in range(5))+a[5])
            residual=h-r*t-target
            cv=r*(sum(a[j]*t**j for j in range(5))-1)
            assert abs(residual)<=cv*D('1e-8')
            assert D(50000)<=rho*r*t<=D(5000000)
            temperatures.append(t)
        assert len(temperatures)==2 and temperatures[1]-temperatures[0]>D('1e-8')


def test_all_property_and_inverse_cartesian_tuples(model):
    ref,fixture=load(REFERENCE),load(FIXTURE)
    compositions={c['name']:tuple(map(float,c['Y'])) for c in fixture['compositions']}
    eps=sys.float_info.epsilon
    gamma128=128*eps/(1-128*eps)
    rows=[]
    failures=[]
    for expected in ref['rows']:
        name=expected['composition']
        y=compositions[name]
        t=float(expected['T'])
        values={k:float(v) for k,v in expected['decimal80'].items()}
        species=model.species_properties(t)
        entropy_terms=[yi*si for yi,si in zip(y,species.s)]
        assert abs(math.fsum(entropy_terms)-values['s'])<=gamma128*math.fsum(map(abs,entropy_terms))
        for p in fixture['pressures_Pa']:
            state=model.evaluate(t,p,y)
            scaled={}
            for key in ('R','cp','cv','h','e','gamma','a'):
                scale=abs(values[key])
                if key=='h':scale=max(scale,values['cp']*t)
                if key=='e':scale=max(scale,values['cv']*t)
                scaled[key]=abs(getattr(state,key)-values[key])/scale
            scaled['rho']=abs(state.rho-p/(values['R']*t))/(p/(values['R']*t))
            identities={
                'h_e_RT':(abs(state.h-state.e-state.R*t),abs(state.h)+abs(state.e)+abs(state.R*t)),
                'cp_cv_R':(abs(state.cp-state.cv-state.R),abs(state.cp)+abs(state.cv)+abs(state.R)),
                'sum_Y':(abs(math.fsum(y)-1),math.fsum(map(abs,y))+1),
            }
            inverse=[]
            for kind in ('energy','enthalpy'):
                target=state.e if kind=='energy' else state.h
                recovered=[]
                for guess in (300,1000,2200):
                    result=(model.invert_energy(state.rho,target,y,initial_guess=guess)
                            if kind=='energy' else model.invert_enthalpy(p,target,y,initial_guess=guess))
                    diagnostic=result.diagnostic
                    residual=getattr(result,'e' if kind=='energy' else 'h')-target
                    capacity=result.cv if kind=='energy' else result.cp
                    assert diagnostic.target==target
                    assert diagnostic.residual==residual
                    assert tuple(result.Y)==y
                    assert abs(result.T-t)<=1e-8, (name,t,p,kind,result.T)
                    assert abs(residual)<=capacity*1e-8, (name,t,p,kind,residual)
                    assert 300<=result.T<=2200 and 50000<=result.p<=5000000
                    recovered.append(result)
                assert recovered[0]==recovered[1]==recovered[2]
                inverse.append({'kind':kind,'target':target,'state':asdict(recovered[0]),
                                'temperature_error_K':abs(recovered[0].T-t)})
            row={'composition':name,'T_K':t,'p_Pa':p,'Y':y,'candidate':asdict(state),
                 'reference':values,'scaled_property_errors':scaled,'identities':identities,'inverses':inverse}
            rows.append(row)
            if max(scaled.values())>1e-8 or any(a>gamma128*b for a,b in identities.values()):
                failures.append((name,t,p,scaled,identities))
    out=ROOT/'artifacts/S03/VAL-001-results.json'
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({'result':'FAIL' if failures else 'PASS','tuples':len(rows),
                              'fixture_sha256':digest(FIXTURE),'reference_sha256':digest(REFERENCE),
                              'classification':'NUMERICAL_VERIFICATION_NOT_EXPERIMENTAL',
                              'rows':rows,'failures':failures},indent=2)+'\n',encoding='utf-8')
    assert len(rows)==432
    assert not failures


def test_elemental_mass_and_composition_identity():
    fixture=load(FIXTURE)
    raw=load(ROOT/'docs/science/C1.0/datasets/thermo_species.json')['species'][:5]
    comp={c['name']:tuple(map(float,c['Y'])) for c in fixture['compositions']}
    for phi in ('0.6','0.7','0.8'):
        for element in ('C','H','O','N'):
            before=math.fsum(y*s['composition'].get(element,0)/s['MW_kg_kmol']
                             for y,s in zip(comp['premix_'+phi],raw))
            after=math.fsum(y*s['composition'].get(element,0)/s['MW_kg_kmol']
                            for y,s in zip(comp['products_'+phi],raw))
            g=128*sys.float_info.epsilon/(1-128*sys.float_info.epsilon)
            assert abs(before-after)<=g*(abs(before)+abs(after))


def test_all_geometry_angles_against_independent_analytic_reference():
    args=load(FIXTURE)['geometry']
    geom=CrankGeometry(**{k:v for k,v in args.items() if k!='angle_degrees'})
    r,l=args['stroke']/2,args['rod']
    area=math.pi*args['bore']**2/4
    gamma128=128*sys.float_info.epsilon/(1-128*sys.float_info.epsilon)
    for degree in args['angle_degrees']:
        theta=degree*math.pi/180
        sine,cosine=math.sin(theta),math.cos(theta)
        root=math.sqrt(l*l-r*r*sine*sine)
        x=r*(1-cosine)+l-root
        dx=r*sine+r*r*sine*cosine/root
        value=geom.volumes(theta)
        assert abs(value.Vc-(args['clearance_volume']+area*x))<=gamma128*(args['clearance_volume']+area*(abs(r*(1-cosine))+l+root))
        assert abs(value.Vcc-(args['crankcase_tdc_volume']-area*x))<=gamma128*(args['crankcase_tdc_volume']+area*(abs(r*(1-cosine))+l+root))
        assert abs(value.dVc_dtheta-area*dx)<=gamma128*area*(abs(r*sine)+abs(r*r*sine*cosine/root))
        assert value.dVcc_dtheta == -value.dVc_dtheta
    assert len(args['angle_degrees'])==361
    assert geom.volumes(0).Vc==args['clearance_volume']
    assert abs(geom.volumes(math.pi).Vc-(args['clearance_volume']+area*args['stroke']))<=gamma128*(args['clearance_volume']+area*args['stroke'])
