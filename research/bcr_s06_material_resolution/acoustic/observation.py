"""Prototype-only N1600 observation adapter; immutable qualified reference data.

Same return shape as implementation free_observation_reference. No solver,
candidate state or fitted measurement enters this function. This helper does
not add N1600 to the accepted R4 contract.
"""
from pathlib import Path
from hashlib import sha256
import json
import math

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def observation_reference(N, sample_index, epsilon=1e-5):
    if type(N) is not int or N != 1600 or type(sample_index) is not int or not 0 <= sample_index <= 100:
        raise ValueError('Only predefined N1600 and samples 0..100 supported')
    if epsilon not in (1e-5, 5e-6):
        raise ValueError('Both original epsilon values only')
    record = json.loads((HERE / 'free_observation_qualification.json').read_text())
    if record['status'] != 'REFERENCE_QUALIFIED' or record['candidate_imports'] is not False:
        raise ValueError('REFERENCE_NOT_QUALIFIED')
    for path, digest in record['source_hashes'].items():
        if sha256((ROOT / path).read_bytes()).hexdigest() != digest:
            raise ValueError('REFERENCE_NOT_QUALIFIED: ' + path)
    mesh = next(m for m in record['meshes'] if m['N'] == N)
    row = mesh['samples'][sample_index]
    assert row['sample'] == sample_index
    scale = epsilon / 1e-5
    result = {'A0': record['normalization']['stored_A0'] * scale,
              'A0_error_upper': record['normalization']['stored_A0_error_upper'] * scale}
    for component in row['components']:
        result[component['name']] = {
            'C': complex(*component['stored_coefficient']) * scale,
            'error_upper': component['stored_coefficient_error_upper'] * scale,
            'phase_eligible': component['phase_and_relative_amplitude_eligible']}
    a, b = result['incident'], result['reflected']
    total = a['C'] + b['C']
    addition_bound = 2 * (math.ulp(total.real) + math.ulp(total.imag))
    result['pressure'] = {'C': total, 'phase_eligible': False,
                         'error_upper': math.nextafter(a['error_upper'] + b['error_upper'] + addition_bound, math.inf)}
    return result


free_observation_reference = observation_reference
