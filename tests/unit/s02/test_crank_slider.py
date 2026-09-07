from dataclasses import FrozenInstanceError
from math import pi, sin, cos, sqrt

import pytest

from dino2next.config import freeze_config
from dino2next.geometry import CrankGeometry, GeometryModel
from dino2next.units import ValueContractError


def crank():
    return CrankGeometry(.05, .04, .08, 8e-6, 150e-6)


def test_dead_centers_and_volume_complement():
    geometry = crank()
    swept = pi * .05**2 / 4 * .04
    tdc, bdc = geometry.volumes(0), geometry.volumes(pi)
    assert tdc.Vc == 8e-6
    assert tdc.Vcc == 150e-6
    assert tdc.dVc_dtheta == 0
    assert bdc.Vc == pytest.approx(8e-6 + swept)
    assert bdc.Vcc == pytest.approx(150e-6 - swept)
    for angle in (-8.2, -.1, .3, 2, 4, 15):
        result = geometry.volumes(angle)
        assert result.Vc + result.Vcc == pytest.approx(158e-6, rel=1e-14)
        assert result.dVc_dtheta == -result.dVcc_dtheta
        assert geometry.volumes(angle + 2 * pi).Vc == pytest.approx(result.Vc, rel=1e-14)


@pytest.mark.parametrize("theta", [.01, .4, 1.3, 2.5, 4.2, 5.8])
def test_closed_form_and_independent_finite_difference(theta):
    geometry = crank()
    x = .02 * (1 - cos(theta)) + .08 - sqrt(.08**2 - .02**2 * sin(theta)**2)
    assert geometry.volumes(theta).Vc == pytest.approx(8e-6 + pi * .025**2 * x, rel=1e-13)
    h = 1e-5
    difference = (geometry.volumes(theta + h).Vc - geometry.volumes(theta - h).Vc) / (2 * h)
    assert geometry.volumes(theta).dVc_dtheta == pytest.approx(difference, rel=1e-8)


@pytest.mark.parametrize("field,value,code", [
    ("bore", 0, "GEOMETRY_INVALID"), ("stroke", -1, "GEOMETRY_INVALID"),
    ("rod", .02, "GEOMETRY_INVALID"), ("clearance_volume", 0, "VOLUME_NONPOSITIVE"),
    ("crankcase_tdc_volume", 1e-6, "VOLUME_NONPOSITIVE"),
    ("bore", float("nan"), "GEOMETRY_INVALID"), ("rod", True, "GEOMETRY_INVALID"),
    ("bore", 1e308, "VOLUME_NONPOSITIVE"),
])
def test_invalid_geometry(field, value, code):
    values = dict(bore=.05, stroke=.04, rod=.08, clearance_volume=8e-6, crankcase_tdc_volume=150e-6)
    values[field] = value
    with pytest.raises(ValueContractError) as error:
        CrankGeometry(**values)
    assert error.value.code == code


def test_snapshot_dimensions_identity_and_immutable_values():
    values = dict(bore=.05, stroke=.04, rod=.08, clearance_volume=8e-6, crankcase_tdc_volume=150e-6)
    payload = {"crank": {key: {"value": value, "dimension": "volume" if "volume" in key else "length",
                              "unit": "m3" if "volume" in key else "m"} for key, value in values.items()}}
    snapshot = freeze_config({"schema_version": "1.0", "payload": payload})
    model = GeometryModel.from_snapshot(snapshot)
    assert model.config_hash == snapshot.sha256
    assert model.crank == crank()
    with pytest.raises(FrozenInstanceError):
        model.crank.bore = 1
    payload["crank"]["bore"] = {"value": 1, "dimension": "pressure", "unit": "Pa"}
    with pytest.raises(ValueContractError) as error:
        GeometryModel.from_snapshot(freeze_config({"schema_version": "1.0", "payload": payload}))
    assert error.value.code == "GEOMETRY_INVALID"


def test_multiple_invalid_dimensions_report_first_field_deterministically():
    payload = {"crank": {key: {"value": 1, "dimension": "pressure", "unit": "Pa"}
                         for key in ("rod", "stroke", "bore", "crankcase_tdc_volume", "clearance_volume")}}
    with pytest.raises(ValueContractError) as error:
        GeometryModel.from_snapshot(freeze_config({"schema_version": "1.0", "payload": payload}))
    assert error.value.path == "/payload/crank/bore"
