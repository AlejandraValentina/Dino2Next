"""Run only available foundation checks; never scientific/heavy fixtures."""
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
COMMANDS=[
 [sys.executable,'-m','compileall','-q','src','scripts','tests'],
 [sys.executable,'scripts/check_contracts.py'],
 [sys.executable,'scripts/check_scopes.py'],
 [sys.executable,'-m','pytest','tests/contract/foundation','-q'],
 ['npm','--prefix','frontend','run','check'],
]
if __name__=='__main__':
 for command in COMMANDS:
  print('+ '+' '.join(command),flush=True)
  result=subprocess.run(command,cwd=ROOT)
  if result.returncode: raise SystemExit(result.returncode)
 print('PR_FAST = PASS; scientific verification and global readiness NOT ASSERTED')
