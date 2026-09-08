"""Reproduce bounded analytical/scalar BCR evidence, not S06 kernel acceptance."""
from pathlib import Path
from hashlib import sha256
from fractions import Fraction
import json, shutil, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OUT=ROOT/'artifacts/S06-BCR'
TEMP=OUT/'val027'
TEMP.mkdir(parents=True,exist_ok=True)
manifest=ROOT/'docs/science/C1.0/S06_VERIFICATION_EVIDENCE_SHA256.json'
entries=json.loads(manifest.read_text())['files']
for relative,digest in entries.items():
    path=ROOT/relative
    assert path.resolve().is_relative_to(HERE.resolve()) and not path.is_symlink()
    assert sha256(path.read_bytes()).hexdigest()==digest, ('BCR_EVIDENCE_HASH_MISMATCH',relative)
for path in (HERE/'frozen').iterdir():shutil.copyfile(path,TEMP/path.name)
for script in ['analytical008010.py','certify010.py','scalar009.py','scalar027.py','certify027_residual.py','certify027_target.py']:
    with (OUT/(script+'.log')).open('w',encoding='utf-8') as log:
        result=subprocess.run([sys.executable,str(HERE/script)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
    assert result.returncode==0, (script,result.returncode)
    print(script,'PASS',flush=True)
certificate=json.loads((TEMP/'contact-target-certificate.json').read_text())
reflection=json.loads((OUT/'reference-010-certified.json').read_text())
assert reflection['result']=='PASS'
assert all(Fraction(v)<=Fraction(1,10**11) for v in certificate['full_reference_field_absolute_error_bound_rational'])
intervals={r['candidate']:r for r in certificate['candidate_density_intervals']}
assert Fraction(intervals['actual full kernel original preserved77caaba']['lower_rational'])>Fraction(1,10**10)
assert Fraction(intervals['actual full kernel additional']['upper_rational'])<Fraction(1,10**10)
scalar=json.loads((OUT/'scalar009/VAL009-independent-scalar.json').read_text())
for norm in ['max_L1','max_L2','max_Linf']:
    assert all(1.8<=order<=2.2 for order in scalar['orders']['SC_SLOPE_ONLY'][norm])
summary={'classification':'BCR_BOUNDED_CHECKS_NOT_KERNEL_ACCEPTANCE','result':'PASS',
         'reflection_certificate':str(OUT/'reference-010-certified.json'),
         'temporal_certificate':str(TEMP/'contact-target-certificate.json'),
         'source_sha256':sha256(Path(__file__).read_bytes()).hexdigest()}
(OUT/'checks.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary))
