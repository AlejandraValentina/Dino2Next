"""Independent TI-001 oracle: Decimal80 and Cantera, never candidate imports.

Run with the pinned reference environment from this checkout. The reference
derives shifts from RAW rather than trusting the production/generator evaluator.
"""
from decimal import Decimal as D, localcontext
import hashlib
import json
from pathlib import Path
import platform
import sys

import cantera as ct
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / "docs/science/C1.0/datasets/thermo_species.json"
DERIVED = ROOT / "docs/science/C1.0/datasets/thermo_runtime_continuous_v1.json"
GENERATOR = ROOT / "research/bcr_s03_nasa_inversion/generate.py"
TRANSPORT = ROOT / "docs/science/C1.0/datasets/thermo_transport.yaml"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def polynomial(a, t):
    cp = sum(a[j] * t**j for j in range(5))
    h = sum(a[j] * t**(j+1) / D(j+1) for j in range(5)) + a[5]
    s = a[0]*t.ln() + sum(a[j]*t**j / D(j) for j in range(1, 5)) + a[6]
    return cp, h, s


def build():
    assert ct.__version__ == '3.2.0', 'VAL-001 requires Cantera 3.2.0'
    assert np.__version__ == '2.2.6', 'Use the pinned reference environment'
    raw = json.loads(SOURCE.read_text(), parse_float=D)
    species = raw['species'][:5]
    ru = raw['Ru_J_kmol_K']
    mw = [x['MW_kg_kmol'] for x in species]
    shifts, phases = [], {}
    for row in species:
        a = row['coeffs']
        low, high = a[8:], a[1:8]
        _, hl, sl = polynomial(low, D(1000))
        _, hh, sh = polynomial(high, D(1000))
        shifts.append((hl-hh, sl-sh))
    for branch in ('low', 'high'):
        ct_species = []
        for row, shift in zip(species, shifts):
            coeffs = list(row['coeffs'][8:] if branch == 'low' else row['coeffs'][1:8])
            if branch == 'high':
                coeffs[5] += shift[0]
                coeffs[6] += shift[1]
            sp = ct.Species(row['name'], {k:float(v) for k,v in row['composition'].items()})
            # Duplicate selected interval to enforce high equality at exactly 1000 K.
            sp.thermo = ct.NasaPoly2(300, 2200, float(row['pref_Pa']),
                                   [1000, *map(float, coeffs), *map(float, coeffs)])
            ct_species.append(sp)
        phases[branch] = ct.Solution(thermo='ideal-gas', species=ct_species)
        assert np.array_equal(phases[branch].molecular_weights, np.array(list(map(float,mw))))
    compositions = []
    for i, row in enumerate(species):
        compositions.append((row['name'], [D(int(j==i)) for j in range(5)]))
    molar = [('air', [D(0),D(1),D('3.76'),D(0),D(0)])]
    for phi in map(D, ['0.6','0.7','0.8']):
        molar.extend([(f'premix_{phi}', [D(1),D('12.5')/phi,D(47)/phi,D(0),D(0)]),
                      (f'products_{phi}', [D(0),D('12.5')/phi-D('12.5'),D(47)/phi,D(8),D(9)])])
    for name, n in molar:
        mass = [ni*mi for ni,mi in zip(n,mw)]
        compositions.append((name, [m/sum(mass) for m in mass]))
    temperatures = ['300','350','400','600','999.999999','1000','1000.000001','1600','2200']
    inputs = {
        'schema_version':'1.0', 'classification':'NUMERICAL_VERIFICATION_NOT_EXPERIMENTAL',
        'normative_fixture':'VAL-001', 'baseline':'C1.0-R3',
        'temperatures_K':temperatures, 'pressures_Pa':[50000,100000,1000000,5000000],
        'compositions':[{'name':n,'Y':[str(v) for v in y]} for n,y in compositions],
        'geometry':{'bore':.052,'stroke':.05,'rod':.101,'clearance_volume':1.2e-5,
                    'crankcase_tdc_volume':3e-4, 'angle_degrees':list(range(361))},
        'original_temperatures_retained':True, 'added_temperature_reason':'TI-004 endpoint 300 K',
    }
    rows, max_scaled = [], 0.0
    for name,y in compositions:
        for ts in temperatures:
            t = D(ts)
            totals = {key:D(0) for key in ('R','cp','h','s')}
            for row, yi, shift in zip(species,y,shifts):
                a = row['coeffs'][8:] if t < 1000 else row['coeffs'][1:8]
                cp,h,s = polynomial(a,t)
                if t >= 1000:
                    h += shift[0]
                    s += shift[1]
                r = ru/row['MW_kg_kmol']
                for k,v in zip(('R','cp','h','s'),(r,cp*r,h*r,s*r)):
                    totals[k] += yi*v
            totals['e'] = totals['h']-totals['R']*t
            totals['cv'] = totals['cp']-totals['R']
            totals['gamma'] = totals['cp']/totals['cv']
            totals['a'] = (totals['gamma']*totals['R']*t).sqrt()
            phase = phases['low' if t < 1000 else 'high']
            phase.set_unnormalized_mass_fractions(list(map(float,y)))
            phase.TP = float(t), 100000
            independent = {'cp':phase.cp_mass,'cv':phase.cv_mass,'h':phase.enthalpy_mass,
                           'e':phase.int_energy_mass,'R':ct.gas_constant/phase.mean_molecular_weight,
                           'gamma':phase.cp_mass/phase.cv_mass,'a':phase.sound_speed}
            for key, value in independent.items():
                scale = abs(totals[key])
                if key=='h':scale=max(scale,totals['cp']*t)
                if key=='e':scale=max(scale,totals['cv']*t)
                err = abs(value-float(totals[key]))/float(scale)
                max_scaled=max(max_scaled,err)
                assert err<=1e-8, (name,ts,key,err)
            rows.append({'composition':name,'T':ts,'decimal80':{k:str(v) for k,v in totals.items()},
                         'cantera':independent})
    return inputs, {
        'schema_version':'1.0','classification':'INDEPENDENT_NUMERICAL_REFERENCE_NOT_EXPERIMENTAL',
        'representation':'DINO2NEXT_NASA5_CONTINUOUS 1.0.0',
        'qualification':{'result':'PASS','property_scaled_max':max_scaled,'budget':1e-8,
                         'decimal_digits':80,'rows':len(rows),'candidate_imports':False,
                         'generator_evaluator_imports':False},
        'environment':{'python':platform.python_version(),'cantera':ct.__version__,'numpy':np.__version__},
        'hashes':{str(p.relative_to(ROOT)):digest(p) for p in
                  (SOURCE,DERIVED,TRANSPORT,GENERATOR,Path(__file__),HERE/'requirements.txt',
                   ROOT/'docs/science/C1.0/EXECUTABLE_VALIDATION_FIXTURES.json',
                   ROOT/'research/bcr_s03_nasa_inversion/results.json')},
        'raw_derived_difference':[
            {'species':s['name'],'high_h_e_shift_J_kg':str(shift[0]*ru/s['MW_kg_kmol']),
             'high_standard_s_shift_J_kg_K':str(shift[1]*ru/s['MW_kg_kmol']),
             'low_h_e_s_shift':0,'cp_shift':0} for s,shift in zip(species,shifts)],
        'physical_uncertainty':'NOT_ESTIMATED', 'rows':rows,
    }


if __name__ == '__main__':
    with localcontext() as ctx:
        ctx.prec=80
        inputs,result=build()
    fixture=ROOT/'validation/fixtures/VAL-001/input.json'
    encoded=json.dumps(inputs,indent=2)+'\n'
    result['fixture_sha256']=hashlib.sha256(encoded.encode()).hexdigest()
    outputs={fixture:encoded,HERE/'reference.json':json.dumps(result,indent=2)+'\n'}
    for path,value in outputs.items():
        if '--check' in sys.argv:
            assert path.read_bytes()==value.encode(), f'Stale reference: {path}'
        else:
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(value,encoding='utf-8',newline='\n')
    print(json.dumps(result['qualification']))
