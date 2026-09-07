"""BCR-S03-NASA-INVERSION: deterministic Decimal derivation, no candidate imports."""
from decimal import Decimal as D, getcontext
from fractions import Fraction as F
from math import comb
from pathlib import Path
import argparse
import hashlib
import json

getcontext().prec = 80
ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'docs/science/C1.0/datasets/thermo_species.json'
OUTPUT = ROOT / 'docs/science/C1.0/datasets/thermo_runtime_continuous_v1.json'
EXPECTED_RAW = '8f7b4d0b11d9a3828c11cfe3b167f5fa7b6103fd036ad6f239175260805ba050'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def integral(a, t):
    return sum(a[i]*t**(i+1)/D(i+1) for i in range(5))+a[5]

def entropy(a, t):
    return a[0]*t.ln()+sum(a[i]*t**i/D(i) for i in range(1,5))+a[6]

def bernstein_bounds(a, lo, hi):
    """Exact rational enclosure over an entire interval by Bernstein convex hull."""
    c = [F(x) for x in a[:5]]
    c[0] -= 1  # cv/R
    lo, hi = F(lo), F(hi)
    power = [sum(c[k]*comb(k,j)*lo**(k-j)*(hi-lo)**j for k in range(j,5)) for j in range(5)]
    b = [sum(power[j]*F(comb(i,j),comb(4,j)) for j in range(i+1)) for i in range(5)]
    if min(b) <= 0:
        assert hi-lo > F(1,1024), 'Cannot prove cv positivity'
        return bernstein_bounds(a,lo,(lo+hi)/2)+bernstein_bounds(a,(lo+hi)/2,hi)
    return [{'interval_K':[str(lo),str(hi)], 'cv_over_R_lower_exact':str(min(b)),
             'cv_over_R_upper_exact':str(max(b))}]

def derive():
    assert sha(SOURCE) == EXPECTED_RAW
    source = json.loads(SOURCE.read_text(),parse_float=D)
    ru=source['Ru_J_kmol_K']
    result={'name':'DINO2NEXT_NASA5_CONTINUOUS','version':'1.0.0',
      'classification':'DERIVED_RUNTIME_REPRESENTATION_NOT_RAW',
      'bcr':'BCR-S03-NASA-INVERSION', 'decimal_precision':80,
      'source_path':str(SOURCE.relative_to(ROOT)).replace('\\','/'),
      'source_sha256':sha(SOURCE),'generator_path':'research/bcr_s03_nasa_inversion/generate.py',
      'generator_sha256':sha(Path(__file__)), 'Ru_J_kmol_K':str(ru),
      'domain_K':['300','2200'],'branch_rule':'low T < 1000; high T >= 1000',
      'definition':'High h(T)=h_RAW_low(1000)+integral_1000^T cp_RAW_high(t)dt; high s(T)=s_RAW_low(1000)+integral_1000^T cp_RAW_high(t)/t dt; lower branch unchanged; e=h-R*T. Stored shifts are 80-digit materializations of the equivalent additive high integration constants.',
      'species':[]}
    for item in source['species'][:5]:
        low=item['coeffs'][8:15]; high=item['coeffs'][1:8]; t=D(1000)
        da6=integral(low,t)-integral(high,t)
        da7=entropy(low,t)-entropy(high,t)
        r=ru/item['MW_kg_kmol']
        result['species'].append({'name':item['name'],
          'composition':{k:str(v) for k,v in item['composition'].items()},
          'MW_kg_kmol':str(item['MW_kg_kmol']),'pref_Pa':str(item['pref_Pa']),
          'raw_nasa7_low':[str(v) for v in low],'raw_nasa7_high':[str(v) for v in high],
          'high_delta_a6_K':str(da6),'high_delta_a7_dimensionless':str(da7),
          'high_delta_h_J_kg':str(r*da6),'high_delta_e_J_kg':str(r*da6),
          'high_delta_s_J_kg_K':str(r*da7),
          'global_cv_positivity_certificate':{
             'method':'Exact rational Bernstein convex hull; finite subinterval covering',
             'low':bernstein_bounds(low,300,1000),'high':bernstein_bounds(high,1000,2200)}})
    return result

def serialized(value):
    return json.dumps(value,indent=2,ensure_ascii=True)+'\n'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    payload=serialized(derive())
    if args.check:
        assert OUTPUT.read_text()==payload, 'Derived representation drift'
    else:
        OUTPUT.write_text(payload,encoding='utf-8',newline='\n')
    print('BCR derived representation: PASS',sha(OUTPUT))

if __name__=='__main__':main()
