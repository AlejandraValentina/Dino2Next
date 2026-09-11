"""Execute every frozen mesh/CFL for this independently referenced case."""
import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[3]

@pytest.mark.parametrize('case_index', range(2))
def test_full_canonical_sequence(case_index):
    spec = importlib.util.spec_from_file_location('s06_assessment', ROOT/'validation/fixtures/VAL-006/assessment.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    module.run_case('VAL-011', case_index)
