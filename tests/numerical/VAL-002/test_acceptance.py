"""VAL-002 mathematical limit using production inventory/work/RHS primitives."""

from hashlib import sha256
import importlib.util
import json
from math import cos, fsum, log2, pi, sin, sqrt
from pathlib import Path
from sys import float_info
import platform

from dino2next.volumes import (
    VolumeInventory, StageVolume, StagePressure, StageWork,
    apply_increment, balance_rates,
)

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "validation/fixtures/VAL-002/input.json"
REFERENCE = ROOT / "validation/references/VAL-002/reference.json"
EXPECTED = ROOT / "validation/expected/VAL-002/acceptance.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def test_reference_identity_and_frozen_fixture():
    fixture, reference, expected = load(FIXTURE), load(REFERENCE), load(EXPECTED)
    assert fixture["steps"] == [100, 200, 400, 800]
    assert [fixture[k] for k in ("gamma", "R_J_kg_K", "mass_kg", "T0_K", "V0_m3", "volume_amplitude")] == [
        "1.4", "287", "0.001", "600", "0.001", "0.2"]
    assert expected["trajectory_relative_error_max"] == 1e-4
    assert expected["observed_order_min"] == 1.8
    assert expected["order_pairs"] == [[200, 400], [400, 800]]
    assert expected["ledger_normalized_max"] == 1e-10
    assert expected["mass_scale"] == "m0"
    assert reference["qualification"]["result"] == "PASS"
    assert reference["qualification"]["candidate_imports"] is False
    for path, value in reference["hashes"].items():
        assert digest(ROOT / path) == value, path
    path = ROOT / "validation/references/VAL-002/generate.py"
    spec = importlib.util.spec_from_file_location("val002_independent_reference", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.encoded() == REFERENCE.read_bytes()


def test_full_trajectory_order_and_same_stage_work():
    fixture, reference, expected = load(FIXTURE), load(REFERENCE), load(EXPECTED)
    gamma = float(fixture["gamma"])
    mass, gas, t0 = (float(fixture[k]) for k in ("mass_kg", "R_J_kg_K", "T0_K"))
    v0, amplitude = float(fixture["V0_m3"]), float(fixture["volume_amplitude"])
    u0 = mass * gas * t0 / (gamma - 1)
    p0 = (gamma - 1) * u0 / v0
    levels = []
    for steps in fixture["steps"]:
        dt = 1 / steps
        inventory = VolumeInventory((mass, 0, 0, 0, 0), u0, (mass, 0, 0, 0))
        work_terms, absolute_work_terms, rows = [], [], []

        def stage_rhs(q, t, stage_id):
            # Explicit mathematical EOS ONLY in this fixture adapter. Runtime
            # state() accepts NASA ThermoModel exclusively; no gamma fallback.
            V = v0 * (1 + amplitude * sin(2 * pi * t))
            Vdot = v0 * amplitude * 2 * pi * cos(2 * pi * t)
            geometry = StageVolume(V, Vdot, t, stage_id, "VAL-002")
            pressure = StagePressure((gamma - 1) * q.internal_energy / V, t, stage_id, "VAL-002")
            work = StageWork(pressure, geometry)
            return balance_rates((), 0., work, volume_id="VAL-002")

        for i in range(steps + 1):
            t = i / steps
            V = v0 * (1 + amplitude * sin(2 * pi * t))
            p = (gamma - 1) * inventory.internal_energy / V
            exact = reference["rows"][i * (800 // steps)]
            error_u = abs(inventory.internal_energy - float(exact["U"])) / u0
            error_p = abs(p - float(exact["p"])) / p0
            work = fsum(work_terms)
            ledger = fsum((inventory.internal_energy, -u0, work))
            conditioning = abs(inventory.internal_energy) + abs(u0) + fsum(abs(x) for x in work_terms)
            assert abs(ledger) <= 256 * float_info.epsilon * conditioning
            # Catalogue/ST-003: initial absolute inventory + absolute physical
            # source throughput + nonzero reference inventory (this case U0).
            ledger_scale = 2 * abs(u0) + fsum(absolute_work_terms)
            normalized_ledger = abs(ledger) / ledger_scale
            mass_error = abs(inventory.mass - mass) / mass
            assert inventory.mass == mass  # Closed case has identically zero mass RHS.
            assert normalized_ledger <= 1e-10
            rows.append({"time": t, "U": inventory.internal_energy, "p": p, "work": work,
                         "mass_kg": inventory.mass, "mass_error_m0": mass_error,
                         "error_U": error_u, "error_p": error_p, "work_residual": ledger,
                         "work_ledger_scale_J": ledger_scale, "work_ledger_normalized": normalized_ledger,
                         "analytic_work_error_U0": abs(work - float(exact["work"])) / u0})
            if i == steps:
                break
            k0 = stage_rhs(inventory, t, f"{steps}:{i}:0")
            q1 = apply_increment(inventory, k0.integrated(dt))
            k1 = stage_rhs(q1, (i + 1) / steps, f"{steps}:{i}:1")
            q2 = apply_increment(q1, k1.integrated(dt))
            # TS-001 with b=0: Qnew=(Qn+Q2)/2. Stored masses unchanged.
            inventory = VolumeInventory(
                tuple(fsum((a, b)) / 2 for a, b in zip(inventory.species_mass, q2.species_mass)),
                fsum((inventory.internal_energy, q2.internal_energy)) / 2,
                tuple(fsum((a, b)) / 2 for a, b in zip(inventory.tracer_mass, q2.tracer_mass)))
            work_terms.append(dt * fsum((k0.pressure_work, k1.pressure_work)) / 2)
            absolute_work_terms.append(dt * fsum((abs(k0.pressure_work), abs(k1.pressure_work))) / 2)
        # Time-normalized trapezoidal norms; the same endpoint grid is used
        # for both candidate and independent reference, without phase shifting.
        norms = {}
        for observable in ("U", "p"):
            errors = [row["error_" + observable] for row in rows]
            norms["L1_" + observable] = dt * fsum((a + b) / 2 for a, b in zip(errors, errors[1:]))
            norms["L2_" + observable] = sqrt(dt * fsum((a*a + b*b) / 2 for a, b in zip(errors, errors[1:])))
        levels.append({"steps": steps, "max_U": max(row["error_U"] for row in rows),
                       "max_p": max(row["error_p"] for row in rows),
                       "max_mass_error_m0": max(row["mass_error_m0"] for row in rows),
                       "max_work_ledger_normalized": max(row["work_ledger_normalized"] for row in rows),
                       "norms": norms, "rows": rows})
    orders = [{"pair": [a["steps"], b["steps"]],
               "U": log2(a["max_U"] / b["max_U"]), "p": log2(a["max_p"] / b["max_p"]),
               "norms": {key: log2(a["norms"][key] / b["norms"][key]) for key in a["norms"]}}
              for a, b in zip(levels[1:-1], levels[2:])]
    passed = max(levels[-1]["max_U"], levels[-1]["max_p"]) <= 1e-4 and all(
        min(row["U"], row["p"], *row["norms"].values()) >= 1.8 for row in orders) and all(
            row["max_mass_error_m0"] == 0 and row["max_work_ledger_normalized"] <= 1e-10 for row in levels)
    output = ROOT / "artifacts/S04/VAL-002-results.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"result": "PASS" if passed else "FAIL", "levels": levels, "orders": orders,
                                 "fixture_sha256": digest(FIXTURE), "reference_sha256": digest(REFERENCE),
                                 "expected_sha256": digest(EXPECTED),
                                 "candidate_hashes": {name: digest(ROOT / name) for name in (
                                     "src/dino2next/volumes/__init__.py",
                                     "tests/numerical/VAL-002/test_acceptance.py")},
                                 "environment": {"python": platform.python_version(), "platform": platform.platform()},
                                 "retries": 0,
                                 "classification": "NUMERICAL_VERIFICATION_NOT_EXPERIMENTAL"}, indent=2) + "\n",
                      encoding="utf-8")
    assert len(levels) == 4 and [len(level["rows"]) for level in levels] == [101, 201, 401, 801]
    assert passed, [(x["steps"], x["max_U"], x["max_p"]) for x in levels]
