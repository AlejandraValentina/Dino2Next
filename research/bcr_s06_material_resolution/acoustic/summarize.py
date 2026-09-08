"""Read-only evidence audit and temporal comparison; no new trajectory."""
from pathlib import Path
from hashlib import sha256
import json
import math
import numpy as np
from observation import observation_reference

HERE = Path(__file__).resolve().parent


def digest(name):
    return sha256((HERE / name).read_bytes()).hexdigest()


reports = []
for cfl in (.05, .1):
    name = f'linear-N1600-CFL{cfl}'
    record = json.loads((HERE / (name + '.json')).read_text())
    assert record['code_sha256'] == digest('acoustic_reduction.py')
    assert record['raw_sha256'] == digest(name + '.npz')
    assert record['certified_observation_sha256'] == digest('free_observation_qualification.json')
    assert len(record['samples']) == 101
    for j in range(101):
        full = observation_reference(1600, j)
        half = observation_reference(1600, j, 5e-6)
        assert full['A0'] == 2 * half['A0']
        for component in ('incident', 'reflected', 'pressure'):
            assert full[component]['C'] == 2 * half[component]['C']
            assert full[component]['phase_eligible'] == half[component]['phase_eligible']
            row = record['samples'][j]['components'][component]
            reconstructed = complex(*row['Cref_over_A0']) * full['A0']
            assert abs(reconstructed - full[component]['C']) <= 8 * math.ulp(full['A0'])
            assert row['phase_eligible'] == full[component]['phase_eligible']
        if j == 75:
            assert full['pressure']['C'] == 0
            assert record['samples'][j]['components']['pressure']['relative_amplitude_error'] is None
    reports.append(record)

temporal = {}
for component in ('incident', 'reflected', 'pressure'):
    values = [np.array([complex(*row['components'][component]['C_over_A0']) for row in record['samples']]) for record in reports]
    difference = abs(values[1] - values[0])
    j = int(np.argmax(difference))
    temporal[component] = {'max_coefficient_difference_over_A0': float(difference[j]), 'sample': j,
                           'differences_over_A0_all_samples': difference.tolist()}

summary = {
    'classification': 'INDEPENDENT_RESOLUTION_PROTOTYPE_NOT_KERNEL_ACCEPTANCE',
    'result': 'SUFFICIENT_LINEAR_RESOLUTION_FOR_BOUNDED_KERNEL_CONFIRMATION' if all(not r['failed_samples'] for r in reports) else 'LINEAR_RESOLUTION_FAILURE',
    'epsilon_coverage': [1e-5, 5e-6],
    'epsilon_basis': 'Exact positive homogeneity of dimensionless reduction; nonlinear kernel must execute both.',
    'levels': [{key: record[key] for key in ('N', 'CFL', 'steps', 'elapsed_seconds', 'failed_samples', 'maxima', 'bounded_vs_folded_max_C_over_A0', 'raw_sha256', 'code_sha256')} for record in reports],
    'temporal_comparison': temporal,
    'temporal_limit': 'Two fixed-N dt values show sensitivity and both pass. They do not establish temporal order or a rigorous dt=0 bound.',
    'historical_status': 'All N200/N400/N800 R4 failures remain failures; see historical/manifest.json and all-sample evidence.',
    'kernel_status': 'NOT_EXECUTED_BY_THIS_PROTOTYPE',
    'source_hashes': {name: digest(name) for name in ('acoustic_reduction.py', 'qualify_free.py', 'reference.py', 'observation.py', 'free_observation_qualification.json', 'summarize.py', 'upstream.json')},
    'proposed_obligations': 'README.md; not adjudicated by its author.'}
(HERE / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print(summary['result'])
print('wrapper101x2 and source/raw bindings PASS; summary SHA256', digest('summary.json'))
