"""Independent closed-form isentrope; no production or candidate imports."""

from decimal import Decimal, localcontext
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "validation/fixtures/VAL-002/input.json"
OUTPUT = Path(__file__).with_name("reference.json")
PI = Decimal("3.1415926535897932384626433832795028841971693993751058209749445923078164062862089986280348253421170679")


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def sine(x):
    # Argument range [-pi,pi], independent high-precision power series.
    x = (x + PI) % (2 * PI) - PI
    term = x
    result = term
    n = 1
    while True:
        term *= -x * x / Decimal((2 * n) * (2 * n + 1))
        updated = result + term
        if updated == result:
            return result
        result = updated
        n += 1


def exact_rows(fixture, precision):
    with localcontext() as ctx:
        ctx.prec = precision
        D = Decimal
        gamma, gas, mass = (D(fixture[k]) for k in ("gamma", "R_J_kg_K", "mass_kg"))
        v0, amp = D(fixture["V0_m3"]), D(fixture["volume_amplitude"])
        u0 = mass * gas * D(fixture["T0_K"]) / (gamma - 1)
        p0 = (gamma - 1) * u0 / v0
        rows = []
        for i in range(801):
            t = D(i) / 800
            v = v0 * (1 + amp * sine(2 * PI * t))
            u = u0 * ((v0 / v).ln() * (gamma - 1)).exp()
            p = (gamma - 1) * u / v
            rows.append({"t": str(t), "V": str(v), "U": str(u), "p": str(p), "work": str(u0 - u)})
        return str(u0), str(p0), rows


def build():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    u0, p0, rows = exact_rows(fixture, 80)
    _, _, low = exact_rows(fixture, 60)
    with localcontext() as ctx:
        ctx.prec = 80
        error = max(abs(Decimal(a[k]) - Decimal(b[k])) / Decimal(u0 if k == "U" else p0)
                    for a, b in zip(rows, low) for k in ("U", "p"))
    if error >= Decimal("1e-55"):
        raise RuntimeError("Independent analytic arithmetic did not qualify")
    return {"schema_version": "1.0", "id": "VAL-002",
            "classification": "EXACT_ANALYTIC_MATHEMATICAL_REFERENCE_NOT_EXPERIMENTAL",
            "formula": "U=U0*(V0/V)^(gamma-1); p=(gamma-1)*U/V; work=U0-U",
            "qualification": {"result": "PASS", "precision_digits": 80,
                              "independent_precision_digits": 60,
                              "scaled_arithmetic_difference": str(error),
                              "candidate_imports": False, "method": "Analytic isentrope, Decimal Taylor sine"},
            "environment": {"implementation": "Python standard library decimal", "precision": 80},
            "hashes": {str(FIXTURE.relative_to(ROOT)).replace("\\", "/"): digest(FIXTURE),
                       str(Path(__file__).resolve().relative_to(ROOT)).replace("\\", "/"): digest(Path(__file__)),
                       "docs/science/C1.0/C1_BASELINE_MANIFEST_SHA256.json": digest(ROOT / "docs/science/C1.0/C1_BASELINE_MANIFEST_SHA256.json")},
            "U0_J": u0, "p0_Pa": p0, "rows": rows}


def encoded():
    return (json.dumps(build(), indent=2, sort_keys=True) + "\n").encode("utf-8")


if __name__ == "__main__":
    data = encoded()
    if "--check" in sys.argv:
        if OUTPUT.read_bytes() != data:
            raise SystemExit("REFERENCE_STALE")
    else:
        OUTPUT.write_bytes(data)
    print("VAL-002 independent analytic reference PASS: 801 endpoints")
