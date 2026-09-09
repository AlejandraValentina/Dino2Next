"""Small software control for the MR-008 contact route; not VAL-008 acceptance."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[3]


def route():
    path = ROOT/'validation/fixtures/VAL-008/regional_execution.py'
    spec = importlib.util.spec_from_file_location('regional008', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_declared_thermal_contact_has_physical_pressure_not_homogeneous_eos():
    module = route()
    fixture = __import__('json').loads((ROOT/'validation/fixtures/VAL-008/input.json').read_text())
    case = fixture['cases'][6]  # pair1, u=0, declared N2-600K/CO2-1800K contact
    run = module.run_contact(case, 20, .05, guard_cells=8, end_time=1e-5, samples=2)
    initial = run['states'][0]
    observation = module.pressure_observation(initial, initial.base_mesh.cell_bounds)
    assert np.max(abs(observation['pressure']-1e5)) < 2e-5
    assert np.max(abs(observation['temperature']-np.where(np.asarray(initial.base_mesh.cell_bounds[:-1]) < .5,600.,1800.))) < 2e-8
    np.testing.assert_allclose(np.sum(run['states'][-1].inventory,axis=0),np.sum(initial.inventory,axis=0),
                               rtol=2e-14,atol=2e-10)
    for snapshot in run['ledger_samples']:
        for ledger in ('full', 'window'):
            value = snapshot[ledger]
            residual = (np.asarray(value['inventory']) - np.asarray(value['initial'])
                        - np.asarray(value['external']) - np.asarray(value['sources']))
            scale = (np.abs(np.asarray(value['initial'])) + np.abs(np.asarray(value['external']))
                     + np.abs(np.asarray(value['sources'])) + abs(np.asarray(value['initial'])[0]))
            assert np.max(np.abs(residual) / scale) <= 1e-10


def test_assessment_adapter_keeps_reference_outside_regional_candidate(tmp_path):
    execution = ROOT/'validation/fixtures/VAL-008/execution.py'
    spec = importlib.util.spec_from_file_location('nasa008_execution_adapter', execution)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    fixture = __import__('json').loads((ROOT/'validation/fixtures/VAL-008/input.json').read_text())
    record = module.execute(fixture['cases'][6], 20, .05, output_root=tmp_path)
    assert record['regional_candidate'] == 'NUMERICAL_FIXTURE_ONLY_REGIONAL_CANDIDATE_NOT_ACCEPTANCE'
    assert len(record['metrics']) == 101
    assert set(record['metrics'][0]['ledgers']) == {'full', 'window'}
    assert (tmp_path/'contact-pair1-u0-N20-CFL0.05.npz').is_file()


def test_contractual_mobile_pair1_u100_minimum_mesh():
    execution = ROOT/'validation/fixtures/VAL-008/execution.py'
    spec = importlib.util.spec_from_file_location('nasa008_mobile_execution', execution)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    fixture = __import__('json').loads((ROOT/'validation/fixtures/VAL-008/input.json').read_text())
    case = fixture['cases'][7]  # pair1, u=100, contractual minimum N/CFL
    out = ROOT/'artifacts/VAL-008-mobile-control'
    record = module.execute(case, 100, .05, output_root=out)
    assert len(record['metrics']) == 101
    assert record['regional_candidate'] == 'NUMERICAL_FIXTURE_ONLY_REGIONAL_CANDIDATE_NOT_ACCEPTANCE'
    assert all(max(abs(v) for v in row['ledgers']['full']['normalized']) <= 1e-10 for row in record['metrics'])
    assert all(max(abs(v) for v in row['ledgers']['window']['normalized']) <= 1e-10 for row in record['metrics'])


def test_mobile_pair1_u100_profiled_contractual_prefix(tmp_path):
    module = route()
    fixture = __import__('json').loads((ROOT/'validation/fixtures/VAL-008/input.json').read_text())
    run = module.run_contact(fixture['cases'][7], 100, .05, guard_cells=134, end_time=1e-5,
                             samples=2, profile=True, checkpoint_path=tmp_path/'prefix-restart.json')
    print(__import__('json').dumps(run['profile'], sort_keys=True))
    assert run['profile']['progress']['accepted_steps'] > 0
    assert run['profile']['progress']['rejected_steps'] == 0


def test_mobile_pair1_u100_cfl_point_two_retries_transactionally(tmp_path):
    """A Y1 predictor rejection rolls back and halves dt without losing evidence."""
    module = route()
    fixture = __import__('json').loads((ROOT/'validation/fixtures/VAL-008/input.json').read_text())
    checkpoint = tmp_path/'retry-restart.json'
    run = module.run_contact(fixture['cases'][7], 100, .2, guard_cells=134, end_time=1e-5,
                             samples=2, profile=True, checkpoint_path=checkpoint)
    assert run['profile']['progress']['accepted_steps'] > 0
    assert run['profile']['progress']['rejected_steps'] > 0
    assert run['trials'][0]['rejection'] == 'VOLUMETRIC_STAGE_BOUND_Y1'
    persisted = __import__('json').loads(checkpoint.read_text(encoding='utf-8'))
    journal = checkpoint.with_suffix('.trials.jsonl')
    assert [__import__('json').loads(line) for line in journal.read_text(encoding='utf-8').splitlines()] == list(run['trials'])
    assert persisted['trial_records'] == len(run['trials'])
    assert all('transaction' in ' '.join(item['diagnostics']) for item in run['trials'])


def test_retry_evidence_survives_regional_restart(tmp_path):
    module = route()
    fixture = __import__('json').loads((ROOT/'validation/fixtures/VAL-008/input.json').read_text())
    case = fixture['cases'][7]
    kwargs = dict(guard_cells=134, end_time=4e-6, samples=2, profile=True)
    continuous = module.run_contact(case, 100, .2, **kwargs)
    checkpoint = tmp_path/'retry-interrupted.json'
    module.run_contact(case, 100, .2, **kwargs, checkpoint_path=checkpoint, stop_after_steps=1)
    resumed = module.run_contact(case, 100, .2, **kwargs, checkpoint_path=checkpoint, resume=True)
    assert resumed['trials'] == continuous['trials']
    assert [state.state_identity for state in resumed['states']] == [state.state_identity for state in continuous['states']]
    assert resumed['profile']['progress'] == continuous['profile']['progress']


def test_mobile_pair1_u100_restart_preserves_continuous_trajectory(tmp_path):
    """A committed step can be resumed without changing samples or ledgers."""
    module = route()
    fixture = __import__('json').loads((ROOT/'validation/fixtures/VAL-008/input.json').read_text())
    case = fixture['cases'][7]
    kwargs = dict(guard_cells=134, end_time=1e-6, samples=2, profile=True)
    continuous = module.run_contact(case, 100, .05, **kwargs)
    checkpoint = tmp_path/'mobile-restart.json'
    stopped = module.run_contact(case, 100, .05, **kwargs, checkpoint_path=checkpoint,
                                 stop_after_steps=1)
    assert stopped['classification'] == 'INCOMPLETE_STOPPED_FOR_RESTART'
    resumed = module.run_contact(case, 100, .05, **kwargs, checkpoint_path=checkpoint, resume=True)
    assert resumed['classification'] == 'NUMERICAL_FIXTURE_ONLY_REGIONAL_CANDIDATE_NOT_ACCEPTANCE'
    assert [state.state_identity for state in resumed['states']] == [state.state_identity for state in continuous['states']]
    assert len(resumed['ledger_samples']) == len(continuous['ledger_samples']) == 2
    for actual, expected in zip(resumed['ledger_samples'], continuous['ledger_samples']):
        for ledger in ('full', 'window'):
            for key in ('initial', 'inventory', 'external', 'sources', 'throughput'):
                np.testing.assert_allclose(actual[ledger][key], expected[ledger][key], rtol=0., atol=0.)
    journal = checkpoint.with_suffix('.steps.jsonl')
    assert journal.is_file()
    assert len(journal.read_text(encoding='utf-8').splitlines()) == resumed['profile']['progress']['accepted_steps']


def test_restart_rejects_a_committed_journal_prefix_that_was_truncated(tmp_path):
    module = route()
    fixture = __import__('json').loads((ROOT/'validation/fixtures/VAL-008/input.json').read_text())
    checkpoint = tmp_path/'truncated-restart.json'
    kwargs = dict(guard_cells=134, end_time=1e-6, samples=2, checkpoint_path=checkpoint,
                  stop_after_steps=1)
    module.run_contact(fixture['cases'][7], 100, .05, **kwargs)
    journal = checkpoint.with_suffix('.steps.jsonl')
    with journal.open('r+b') as stream:
        stream.truncate(journal.stat().st_size-10)
    with pytest.raises(ValueError, match='journal'):
        module.run_contact(fixture['cases'][7], 100, .05, guard_cells=134, end_time=1e-6,
                           samples=2, checkpoint_path=checkpoint, resume=True)
