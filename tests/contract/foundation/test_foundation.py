import importlib.metadata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def test_editable_package():assert importlib.metadata.version('dino2next')=='0.0.0'
def test_scope_commands_exist():
 for name in ['run_foundation.py','check_contracts.py','check_scopes.py','run_gate.py']:
  assert (ROOT/'scripts'/name).is_file()
