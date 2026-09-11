"""Independent Cantera thermodynamic check, run in the pinned Cantera environment.

Reads decimal RAW coefficients and derives the TI-001 integration shifts itself.
Does not import reference.py, candidate thermo, or the BCR generator.
"""
from decimal import Decimal as D,localcontext
from pathlib import Path
import hashlib,json,platform
import cantera as ct
import numpy as np

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'artifacts/S06-R4/reference008'

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    assert ct.__version__=='3.2.0'
    source=ROOT/'docs/science/C1.0/datasets/thermo_species.json'
    with localcontext() as ctx:
        ctx.prec=80;raw=json.loads(source.read_text(),parse_float=D)
        phases={}
        for branch in ('low','high'):
            species=[]
            for row in raw['species'][:5]:
                low=row['coeffs'][8:];high=row['coeffs'][1:8]
                def h(a):return sum(a[j]*D(1000)**(j+1)/D(j+1) for j in range(5))+a[5]
                def s(a):return a[0]*D(1000).ln()+sum(a[j]*D(1000)**j/D(j) for j in range(1,5))+a[6]
                high[5]+=h(low)-h(high);high[6]+=s(low)-s(high)
                a=low if branch=='low' else high
                sp=ct.Species(row['name'],{k:float(v) for k,v in row['composition'].items()})
                sp.thermo=ct.NasaPoly2(300,2200,float(row['pref_Pa']),[1000,*map(float,a),*map(float,a)])
                species.append(sp)
            phases[branch]=ct.Solution(thermo='ideal-gas',species=species)
    inputs=OUT/'cantera-inputs.json';rows=json.loads(inputs.read_text());errors=[]
    for row in rows:
        gas=phases['low' if row['T']<1000 else 'high'];gas.TPY=row['T'],row['p'],row['Y']
        observed=dict(cp=gas.cp_mass,h=gas.enthalpy_mass,e=gas.int_energy_mass,rho=gas.density,a=gas.sound_speed)
        err={k:abs(observed[k]-row[k])/max(1,abs(row[k])) for k in observed}
        assert max(err.values())<2e-12,(row,err)
        errors.append(dict(case=row['case'],T=row['T'],p=row['p'],relative_errors=err))
    report=dict(status='PASS',cases=len(rows),errors=errors,raw_sha256=digest(source),input_sha256=digest(inputs),code_sha256=digest(Path(__file__)),environment=dict(python=platform.python_version(),numpy=np.__version__,cantera=ct.__version__))
    path=OUT/'cantera-check.json';path.write_text(json.dumps(report,indent=2)+'\n');print('Cantera independent check PASS',len(rows))

if __name__=='__main__':main()
