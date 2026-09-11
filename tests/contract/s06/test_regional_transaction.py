from pathlib import Path
import runpy

import numpy as np
import pytest

from dino2next.numerics.regional import RegionalNumericalKernel, RegionalRHS
from dino2next.numerics.regional import RegionalStepAttempt
from dino2next.units import ValueContractError


_helpers = runpy.run_path(str(Path(__file__).resolve().parents[2] / "unit/s06/test_regional_kernel.py"))
state = _helpers["state"]
zero_rhs = _helpers["zero_rhs"]
thermo = _helpers["thermo"]


def test_invalid_mapped_final_state_rejects_without_mutating_input(thermo):
    initial = state(thermo)
    kernel = RegionalNumericalKernel(thermo)
    before = np.asarray(initial.inventory).copy()

    def invalid_mapper(Z, time):
        output = np.asarray(Z).copy()
        if time > 0.:
            output[0, 0] = -1.
        return output

    result = kernel.propose_step(initial, lambda candidate, time: zero_rhs(kernel, candidate), 0., 1e-5,
                                 trial_state_mapper=invalid_mapper, initial_Z=initial.inventory)
    assert not result.accepted
    assert result.rejection == "LOW_ORDER_STAGE_INADMISSIBLE_RETRY_DT"
    np.testing.assert_array_equal(initial.inventory, before)
    assert result.face_integrals is None and result.source_integrals is None
    assert result.stage_states == ()
    assert any(item[0] == "transaction" and item[1] == "REJECTED" for item in result.diagnostics)


def test_boundary_volume_motion_is_explicitly_rejected(thermo):
    initial = state(thermo)
    kernel = RegionalNumericalKernel(thermo)
    rhs = zero_rhs(kernel, initial)
    speed = np.asarray(rhs.volume_speed).copy()
    speed[0] = 1.
    try:
        RegionalRHS(speed, rhs.high, rhs.low, rhs.sources, rhs.face_areas, rhs.patch)
    except Exception as error:
        assert getattr(error, "code", None) == "UNSUPPORTED_REGIONAL_EVENT"
    else:
        raise AssertionError("moving physical boundary was accepted")


@pytest.mark.parametrize('value',[[],{},'',0])
def test_rejection_code_is_a_nonempty_immutable_string(value):
    with pytest.raises(ValueContractError) as error:
        RegionalStepAttempt(None,value,())
    assert error.value.code=='STAGE_INADMISSIBLE'
