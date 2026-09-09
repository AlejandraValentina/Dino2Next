from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

import numpy as np
import pytest

from dino2next.gasdynamics import CumulativeVolumeGeometry, Mesh1D, PolynomialSegment, RegionalDuctState
from dino2next.numerics.regional import RegionalNumericalKernel, RegionalRHS
from dino2next.thermo import ThermoDataset, ThermoModel


@pytest.fixture(scope="module")
def thermo():
    root = Path(__file__).resolve().parents[3]
    base = root / "docs/science/C1.0/datasets"
    paths = (base / "thermo_runtime_continuous_v1.json", base / "thermo_species.json",
             base / "thermo_transport.yaml", root / "research/bcr_s03_nasa_inversion/generate.py")
    digest = lambda path: sha256(path.read_bytes()).hexdigest()
    return ThermoModel(ThermoDataset.from_files(*paths, expected_sha256=digest(paths[0]),
        expected_raw_sha256=digest(paths[1]), expected_transport_sha256=digest(paths[2]),
        expected_generator_sha256=digest(paths[3])))


def state(thermo, *, edges=(0., .5, 1.), labels=("N2", "N2"), velocity=0., base_edges=None):
    geometry = CumulativeVolumeGeometry(PolynomialSegment(0., 1., (1., 0., 2.), (1.,)))
    bounds = base_edges or edges
    mesh = Mesh1D(tuple(bounds), tuple(geometry.segment.integral(a, b) / (b-a) for a, b in zip(bounds, bounds[1:])),
                  tuple(geometry.segment.value(x) for x in bounds), (1.,) * (len(bounds)-1))
    physical = [(600., 1e5, velocity, (0., 0., 1., 0., 0.), (0., 0., 1., 0.))] * (len(edges)-1)
    if len(labels) > 1 and labels[1] == "CO2":
        physical[1] = (1800., 1e5, velocity, (0., 0., 0., 1., 0.), (0., 0., 1., 0.))
    return RegionalDuctState.from_physical(geometry, mesh, edges, physical, labels, thermo)


def zero_rhs(kernel, value):
    n = len(value.labels)
    area = np.array([value.geometry.segment.value(x) for x in value.edges])
    return RegionalRHS(np.zeros(n+1), np.zeros((n+1, 12)), np.zeros((n+1, 12)),
                       np.zeros((n, 12)), area, kernel.patch_cells(value))


def test_constant_state_step_is_immutable_and_has_extensive_ledgers(thermo):
    initial = state(thermo)
    kernel = RegionalNumericalKernel(thermo)
    before = np.asarray(initial.inventory).copy()
    result = kernel.propose_step(initial, lambda candidate, time: zero_rhs(kernel, candidate), 0., 1e-5)
    assert result.accepted and result.rejection is None
    np.testing.assert_array_equal(result.state.inventory, before)
    np.testing.assert_array_equal(result.face_integrals, np.zeros((3, 12)))
    np.testing.assert_array_equal(result.source_integrals, np.zeros((2, 12)))
    assert result.stage_states[0] is initial
    assert any(record[0] == "transaction" and record[1] == "ACCEPTED" for record in result.diagnostics)


def test_bulk_only_regional_rhs_uses_python_scalar_perimeters(thermo):
    value = state(thermo, edges=tuple(map(float, np.linspace(0., 1., 41))),
                  labels=("N2",) * 40, velocity=10.)
    kernel = RegionalNumericalKernel(thermo)
    rhs = kernel.rhs(value, 0., boundary_flux=np.zeros((2, 12)))
    assert not rhs.patch.any()
    assert any(row[0] == 'bulk' for row in rhs.diagnostics)


def test_contact_flux_is_material_only_and_does_not_mix_constituents(thermo):
    value = state(thermo, labels=("N2", "CO2"), velocity=20.)
    kernel = RegionalNumericalKernel(thermo)
    rhs = kernel.rhs(value, 0., boundary_flux=np.zeros((2, 12)))
    assert rhs.patch.tolist() == [True, True]
    face = rhs.high[1] / rhs.face_areas[1]
    assert np.all(face[[0, 3, 4, 5, 6, 7, 8, 9, 10, 11]] == 0.)
    assert face[1] == pytest.approx(1e5, rel=2e-12)
    assert face[2] == pytest.approx(2e6, rel=3e-11)


def test_limited_shared_flux_records_selected_guard_and_preserves_inventory(thermo):
    initial = state(thermo)
    kernel = RegionalNumericalKernel(thermo)
    U = np.asarray(initial.inventory) / np.asarray(initial.volumes)[:, None]

    def rhs(candidate, time):
        result = zero_rhs(kernel, candidate)
        high = np.asarray(result.high).copy()
        high[1] = U[0] * 100000.
        return RegionalRHS(result.volume_speed, high, result.low, result.sources,
                           result.face_areas, result.patch)

    result = kernel.propose_step(initial, rhs, 0., 1e-5)
    assert result.accepted
    selected = next(record for record in result.diagnostics if record[0] == "selected_guards")
    assert 0. < selected[1][0] < 1.
    np.testing.assert_allclose(np.sum(result.state.inventory, axis=0), np.sum(initial.inventory, axis=0), rtol=2e-15, atol=1e-15)


def test_reorganization_retains_material_face_and_is_conservative(thermo):
    initial = state(thermo, edges=(0., .2, .21, 1.), labels=("N2", "CO2", "CO2"),
                    base_edges=(0., .25, .5, .75, 1.))
    remapped = RegionalNumericalKernel(thermo).reorganize(initial)
    assert .2 in remapped.edges and "N2" in remapped.labels and "CO2" in remapped.labels
    np.testing.assert_allclose(np.sum(remapped.inventory, axis=0), np.sum(initial.inventory, axis=0), rtol=2e-15, atol=1e-15)
