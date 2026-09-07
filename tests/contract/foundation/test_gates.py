from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[3]
def test_unavailable_scientific_gate_fails():
 p=subprocess.run([sys.executable,'scripts/run_gate.py','HEAVY_VERIFICATION','--val','VAL-013'],cwd=ROOT,capture_output=True,text=True)
 assert p.returncode==2 and 'GATE_UNAVAILABLE' in p.stdout

def test_fast_contains_no_scientific_suite():
 sys.path.insert(0,str(ROOT/'scripts'))
 from run_foundation import COMMANDS
 assert any('tests/contract/foundation' in c for c in COMMANDS)
 assert all('tests/numerical' not in ' '.join(c) for c in COMMANDS)
