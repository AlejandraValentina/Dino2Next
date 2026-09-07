from dataclasses import FrozenInstanceError
from math import nextafter

import pytest

from dino2next.units import ValueContractError

COMPOSITIONS = [tuple(float(i == j) for i in range(5)) for j in range(5)]
COMPOSITIONS += [(0., .232, .768, 0., 0.), (.03, .2, .7, .04, .03)]


@pytest.mark.parametrize("Y", COMPOSITIONS)
@pytest.mark.parametrize("T", [300, 999.999999, 1000, 1000.000001, 2200])
@pytest.mark.parametrize("p", [5e4, 1e5, 1e6, 5e6])
def test_energy_and_enthalpy_roundtrip(model, T, p, Y):
    source = model.evaluate(T, p, Y)
    for inverse, target, capacity in (
        (model.invert_energy(source.rho, source.e, Y), source.e, "cv"),
        (model.invert_enthalpy(p, source.h, Y), source.h, "cp"),
    ):
        assert abs(inverse.T - T) <= 1e-8
        assert inverse.diagnostic.target == target
        assert abs(inverse.diagnostic.residual) <= getattr(inverse, capacity) * 1e-8
        assert inverse.diagnostic.temperature_bracket[1] - inverse.diagnostic.temperature_bracket[0] <= 1e-8
        assert 5e4 <= inverse.p <= 5e6
    assert model.invert_energy(source.rho, source.e, Y).rho == source.rho


@pytest.mark.parametrize("Y", COMPOSITIONS)
def test_crossing_energy_preserves_targets_and_is_seed_independent(model, Y):
    rho = model.evaluate(1000, 1e5, Y).rho
    for T in (999.999999, 1000.000001):
        target = model.evaluate(T, 1e5, Y).e
        results = [model.invert_energy(rho, target, list(Y), initial_guess=guess)
                   for guess in (300, 999.999, 1000, 2200, None)]
        assert results == [results[0]] * len(results)
        assert abs(results[0].T - T) <= 1e-8
        assert results[0].diagnostic.target == target
        assert results[0].rho == rho


@pytest.mark.parametrize("Y", COMPOSITIONS)
def test_enthalpy_crossings_in_both_directions_and_guess_independence(model, Y):
    for old_T, new_T in ((999.999999, 1000.000001), (1000.000001, 999.999999)):
        original = model.evaluate(old_T, 1e5, Y)
        target = model.evaluate(new_T, 1e5, Y).h
        results = [model.invert_enthalpy(original.p, target, Y, initial_guess=guess)
                   for guess in (old_T, 300, 2200, None)]
        assert results == [results[0]] * len(results)
        result = results[0]
        assert abs(result.T - new_T) <= 1e-8
        assert result.diagnostic.target == target
        assert result.diagnostic.residual == result.h - target
        assert abs(result.diagnostic.residual) <= result.cp * 1e-8
        assert result.p == original.p
        assert original.T == old_T


def test_composition_is_not_mutated_or_normalized(model):
    Y = [0., .232, .768, 0., 0.]
    before = Y.copy()
    state = model.evaluate(700, 1e5, Y)
    assert Y == before
    assert state.Y == tuple(before)
    Y[1] = 0
    assert state.Y == tuple(before)
    with pytest.raises(FrozenInstanceError):
        state.e = 0


@pytest.mark.parametrize("Y", [[], [1, 0, 0, 0], [1, 0, 0, 0, 0, 0],
                                  [0, 0, 0, 0, 0], [-1e-16, 1, 0, 0, 0],
                                  [0, .2, .7, 0, 0], [True, 0, 0, 0, 0],
                                  [float("nan"), 1, 0, 0, 0], [1.00001, 0, 0, 0, 0]])
def test_invalid_composition(model, Y):
    with pytest.raises(ValueContractError) as exc:
        model.evaluate(700, 1e5, Y)
    assert exc.value.code == "COMPOSITION_INVALID"


@pytest.mark.parametrize("p", [49999., 5000001., 0., float("inf")])
def test_pressure_domain(model, p):
    with pytest.raises(ValueContractError) as exc:
        model.evaluate(700, p, COMPOSITIONS[0])
    assert exc.value.code == "EOS_OUT_OF_DOMAIN"


@pytest.mark.parametrize("rho", [0, -1, 1e-6, 1e6, 5e-324, 1.7976931348623157e308,
                                  float("nan"), float("inf")])
def test_density_and_recovered_pressure_domain(model, rho):
    Y = COMPOSITIONS[0]
    state = model.evaluate(700, 1e5, Y)
    with pytest.raises(ValueContractError) as exc:
        model.invert_energy(rho, state.e, Y)
    assert exc.value.code == "EOS_OUT_OF_DOMAIN"


@pytest.mark.parametrize("T,direction", [(300, float("-inf")), (2200, float("inf"))])
def test_out_of_range_targets_never_clipped(model, T, direction):
    Y = COMPOSITIONS[4]
    source = model.evaluate(T, 1e5, Y)
    for call, value in ((lambda target: model.invert_energy(source.rho, target, Y), source.e),
                        (lambda target: model.invert_enthalpy(1e5, target, Y), source.h)):
        with pytest.raises(ValueContractError) as exc:
            call(nextafter(value, direction))
        assert exc.value.code == "EOS_OUT_OF_DOMAIN"


def test_pressure_boundary_zero_residual_regression(model):
    # The CO2 1600 K/5 MPa roundtrip can have a zero rounded energy residual
    # at T whose recovered pressure is one ulp too high. Keep the target and
    # select an admissible approximate inverse within the original budget.
    source = model.evaluate(1600, 5e6, COMPOSITIONS[3])
    result = model.invert_energy(source.rho, source.e, source.Y)
    assert result.p <= 5e6
    assert abs(result.T - source.T) <= 1e-8
    assert result.rho == source.rho
    assert result.diagnostic.target == source.e
    assert result.diagnostic.temperature_bracket[0] <= result.T <= result.diagnostic.temperature_bracket[1]


@pytest.mark.parametrize("T", [nextafter(1000., 0.), 1000., nextafter(1000., float("inf"))])
@pytest.mark.parametrize("p", [5e4, 5e6])
@pytest.mark.parametrize("Y", COMPOSITIONS)
def test_adjacent_join_floats_and_pressure_endpoints(model, T, p, Y):
    source = model.evaluate(T, p, Y)
    result = model.invert_energy(source.rho, source.e, Y)
    assert abs(result.T - T) <= 1e-8
    assert abs(result.diagnostic.residual) <= result.cv * 1e-8
    assert 5e4 <= result.p <= 5e6


def test_bracket_failure_is_diagnostic_not_a_plausible_state(model, monkeypatch):
    # Fault injection deliberately violates continuous properties. It verifies
    # the failure path, and is not a scientific dataset or acceptance oracle.
    from dino2next.thermo import ThermoModel
    original = ThermoModel._mixture

    def discontinuous(self, T, Y):
        R, cp, cv, h, e = original(self, T, Y)
        return R, cp, 1e-30, h, (0. if T < 1000.1 else 1.)

    monkeypatch.setattr(ThermoModel, "_mixture", discontinuous)
    with pytest.raises(ValueContractError) as exc:
        model.invert_energy(.5, .5, COMPOSITIONS[1])
    assert exc.value.code == "EOS_INVERSION_FAILED"
    assert exc.value.metadata["target"] == .5
