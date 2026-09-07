from dataclasses import FrozenInstanceError
import pytest

from dino2next.geometry import PassageSamples, CrankGeometry, GeometryModel
from dino2next.units import ValueContractError


def test_count_exactly_once_and_measured_storage_preserved():
    areas = [.001, .002]
    single = PassageSamples("transfer", [0, .02], areas, [.12, .13], 3, "PER_PASSAGE")
    total = PassageSamples("aggregate", [0, .02], [.003, .006], [.36, .39], 3, "AGGREGATE")
    assert single.aggregate_areas == total.aggregate_areas == (.003, .006)
    assert single.areas == (.001, .002)
    assert total.areas == (.003, .006)
    assert single.count == total.count == 3
    areas[0] = 0
    assert single.areas[0] == .001
    with pytest.raises(FrozenInstanceError):
        single.count = 1
    model = GeometryModel(CrankGeometry(.05, .04, .08, 8e-6, 150e-6), [single])
    assert model.passage_geometry() == (single,)
    assert model.passage_geometry()[0].aggregate_areas == (.003, .006)


def test_aggregate_values_are_not_multiplied_even_during_validation():
    measured = PassageSamples("aggregate", [0, 1], [1e308, 1e308], [1, 1], 100, "AGGREGATE")
    assert measured.aggregate_areas == (1e308, 1e308)


@pytest.mark.parametrize("kwargs", [
    {"positions": [0, 0]}, {"positions": [1, 0]}, {"areas": [0, .001]},
    {"perimeters": [-1, 1]}, {"areas": [.001]}, {"count": True}, {"count": 0},
    {"area_basis": "UNKNOWN"}, {"areas": [float("inf"), .001]},
    {"count": 10**400},
])
def test_invalid_measured_data(kwargs):
    values = dict(component_id="t", positions=[0, .02], areas=[.001, .001], perimeters=[.1, .1])
    values.update(kwargs)
    with pytest.raises(ValueContractError) as error:
        PassageSamples(**values)
    assert error.value.code in ("GEOMETRY_INVALID", "AREA_DOMAIN_ERROR")
