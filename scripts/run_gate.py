"""Explicit progressive adapters. Missing adapters never pass."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
GATES=('PR_FAST','PR_SCIENTIFIC_AFFECTED','MILESTONE','HEAVY_VERIFICATION')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('gate',choices=GATES);p.add_argument('--val',action='append',default=[]);a=p.parse_args()
 if a.gate=='PR_FAST':
  if a.val: p.error('PR_FAST does not accept scientific fixtures')
  raise SystemExit(subprocess.call([sys.executable,'scripts/run_foundation.py'],cwd=ROOT))
 vals={v['id']:v for v in json.loads((ROOT/'implementation/validation_registry.json').read_text())['validations']}
 if not a.val: p.error('Explicit --val entries required; no implicit heavy suite')
 paths=[]
 for identifier in a.val:
  v=vals.get(identifier)
  if not v or not v['mandatory'] or v['gate_class']!=a.gate or v['execution_status']!='IMPLEMENTED' or not (ROOT/v['test']).is_file():
   print('GATE_UNAVAILABLE: '+identifier);raise SystemExit(2)
  paths.append(v['test'])
 raise SystemExit(subprocess.call([sys.executable,'-m','pytest',*paths],cwd=ROOT))
