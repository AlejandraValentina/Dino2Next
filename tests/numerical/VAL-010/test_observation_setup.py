"""SV-010 observation setup controls, not a candidate acceptance run."""
import importlib.util
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[3]


def load(path):
    spec = importlib.util.spec_from_file_location('check_'+Path(path).stem,ROOT/path)
    obj = importlib.util.module_from_spec(spec); spec.loader.exec_module(obj)
    return obj


def test_every_reference_sample_has_absolute_coverage_and_fixed_phase_mask():
    ref = load('validation/references/VAL-010/reference.py')
    assessment = load('validation/fixtures/VAL-006/assessment.py')
    for n in (200,400,800):
        edges = np.linspace(0,1,n+1)
        for eps in (1e-5,5e-6):
            for j in range(101):
                qualified = ref.free_observation_reference(n,j,eps)
                assert qualified['incident']['phase_eligible'] == (j <= 83)
                assert qualified['reflected']['phase_eligible'] == (j >= 67)
                exact = ref.cell_averages(edges,j/(100*ref.C),'free',eps)
                primitive = np.column_stack((exact['rho'],exact['u'],exact['p']))
                result = assessment.assess_reflection_sample(ref,edges,primitive,qualified,n,j/(100*ref.C),j)
                assert result['passed'], (n,eps,j,result)
                if j == 75:
                    assert abs(qualified['pressure']['C']) <= qualified['pressure']['error_upper']
                    assert all(result['components'][name]['phase_status']=='ASSESSED' for name in ('incident','reflected'))


def test_zero_candidate_in_observable_interval_fails_with_undefined_phase():
    ref = load('validation/references/VAL-010/reference.py')
    assessment = load('validation/fixtures/VAL-006/assessment.py')
    n = 200; edges = np.linspace(0,1,n+1)
    primitive = np.column_stack((np.ones(n),np.zeros(n),np.ones(n)))
    result = assessment.assess_reflection_sample(ref,edges,primitive,ref.free_observation_reference(n,75,1e-5),n,.75/ref.C,75)
    assert not result['passed']
    for name in ('incident','reflected'):
        assert result['components'][name]['phase_status']=='UNDEFINED_ZERO_CANDIDATE'
        assert result['components'][name]['phase_error_upper'] is None
