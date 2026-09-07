from dataclasses import FrozenInstanceError
from math import nextafter
from sys import float_info

import pytest

from dino2next.thermo import SPECIES
from dino2next.units import ValueContractError


@pytest.mark.parametrize("T", [300, 350, 999.999999, 1000, 1000.000001, 2200])
def test_species_identities_positive_and_immutable(model, T):
    props = model.species_properties(T)
    assert props.names == SPECIES
    for cp, cv, h, e, R in zip(props.cp, props.cv, props.h, props.e, props.R):
        assert cp > cv > 0 and R > 0
        assert cp - cv == pytest.approx(R, rel=1e-14)
        gamma128 = 128 * float_info.epsilon / (1 - 128 * float_info.epsilon)
        assert abs(h - e - R * T) <= gamma128 * (abs(h) + abs(e) + abs(R * T))
    with pytest.raises(TypeError):
        props.cp[0] = 0
    with pytest.raises(FrozenInstanceError):
        props.h = ()


def test_exact_high_cp_convention_and_join_anchors(model):
    props = model.species_properties(1000)
    below = model.species_properties(nextafter(1000, 0))
    for i, row in enumerate(model.dataset.species):
        expected_cp = row.R * sum(row.high[j] * 1000 ** j for j in range(5))
        assert props.cp[i] == pytest.approx(expected_cp, rel=1e-14)
        assert props.h[i] == row.h_join
        assert props.s[i] == row.s_join
        assert abs(props.h[i] - below.h[i]) < 1e-8
        assert abs(props.s[i] - below.s[i]) < 1e-10


@pytest.mark.parametrize("T,direction", [(300, 1), (700, 1), (1000, 1), (1000, -1), (2200, -1)])
def test_unilateral_derivatives(model, T, direction):
    # A second-order unilateral finite difference does not cross the NASA join.
    step = direction * .01
    p0, p1, p2 = (model.species_properties(t) for t in (T, T + step, T + 2 * step))
    side = model.species_properties(nextafter(T, 0)) if T == 1000 and direction < 0 else p0
    for i in range(5):
        dh = (-3 * p0.h[i] + 4 * p1.h[i] - p2.h[i]) / (2 * step)
        de = (-3 * p0.e[i] + 4 * p1.e[i] - p2.e[i]) / (2 * step)
        ds = (-3 * p0.s[i] + 4 * p1.s[i] - p2.s[i]) / (2 * step)
        assert dh == pytest.approx(side.cp[i], rel=2e-8)
        assert de == pytest.approx(side.cv[i], rel=2e-8)
        assert ds == pytest.approx(side.cp[i] / T, rel=2e-8)


@pytest.mark.parametrize("T", [299.99999, 2200.00001, float("nan"), float("inf"), True, "1000"])
def test_temperature_domain_errors(model, T):
    with pytest.raises(ValueContractError) as exc:
        model.species_properties(T)
    assert exc.value.code == "EOS_OUT_OF_DOMAIN"
    assert exc.value.component == "thermo"


def test_formation_reference_is_not_zeroed(model):
    props = model.species_properties(300)
    assert props.h[0] < -1e6
    assert props.h[3] < -8e6
    assert props.h[4] < -1e7


def test_no_implicit_dataset(model):
    from dino2next.thermo import ThermoModel
    with pytest.raises(TypeError):
        ThermoModel()
    with pytest.raises(ValueContractError, match="verified ThermoDataset"):
        ThermoModel(None)
