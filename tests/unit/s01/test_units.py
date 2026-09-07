from dataclasses import FrozenInstanceError
from math import pi

import pytest

from dino2next.units import Quantity, ValueContractError, to_si


@pytest.mark.parametrize("unit,dimension,value,expected", [
    ("mm", "length", 125, .125), ("m", "length", 2, 2),
    ("mm2", "area", 500, .0005), ("m2", "area", 2, 2),
    ("cm3", "volume", 125, .000125), ("m3", "volume", 2, 2),
    ("Pa", "pressure", 2, 2), ("kPa", "pressure", 101.325, 101325),
    ("bar", "pressure", 1, 100000), ("deg", "angle", 180, pi),
    ("rad", "angle", 2, 2), ("K", "temperature", 300, 300),
    ("degC", "temperature", -273.15, 0), ("degC", "temperature", 25, 298.15),
    ("rpm", "speed", 60, 2 * pi), ("rad/s", "speed", 2, 2),
    ("W", "power", 2, 2), ("kW", "power", 3, 3000),
])
def test_all_supported_units(unit, dimension, value, expected):
    assert to_si(Quantity(value, unit, dimension)) == pytest.approx(expected)
    assert isinstance(to_si(Quantity(value, unit, dimension)), float)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf"), 1e308, 10**400])
def test_nonfinite_and_overflow(value):
    with pytest.raises(ValueContractError) as exc:
        Quantity(value, "bar", "pressure")
    assert exc.value.code == "NONFINITE_VALUE"
    assert exc.value.path == "/value"


@pytest.mark.parametrize("unit,dimension", [("psi", "pressure"), ("m", "area"), ([], "area")])
def test_unknown_units_and_mismatched_dimensions(unit, dimension):
    with pytest.raises(ValueContractError) as exc:
        Quantity(1, unit, dimension)
    assert exc.value.code == "UNIT_DIMENSION_MISMATCH"


@pytest.mark.parametrize("value", [True, "12", None])
def test_non_numeric_values(value):
    with pytest.raises(ValueContractError) as exc:
        Quantity(value, "m", "length")
    assert exc.value.code == "INVALID_VALUE"


def test_immutable_and_no_physical_clipping():
    value = Quantity(-10, "mm", "length")
    assert to_si(value) == -.01
    with pytest.raises(FrozenInstanceError):
        value.value = 12
