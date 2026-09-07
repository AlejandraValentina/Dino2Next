"""C1.0-R3 NASA5 ideal-gas properties; all arguments and results are SI.

Dataset bytes are injected and verified, never found implicitly on disk. High
enthalpy and standard entropy use the analytic TI-001 join anchor. No RAW energy
state conversion or transport adapter is supplied here.
"""

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from math import fsum, isfinite, log, log1p, nextafter, sqrt
from pathlib import Path
from sys import float_info

from dino2next.config import ConfigSnapshot
from dino2next.units import ValueContractError

SPECIES = ("C8H18,isooctane", "O2", "N2", "CO2", "H2O")
DATASET_NAME = "DINO2NEXT_NASA5_CONTINUOUS"
DATASET_VERSION = "1.0.0"
# This implementation accepts the single frozen R3 representation. Explicit
# caller expectations are checked independently from this accepted identity.
DERIVED_SHA256 = "5b4d37b8821fcfac906fc2ff726945b6455049e229f16c56ba66b40bec0eda7a"
RAW_SHA256 = "8f7b4d0b11d9a3828c11cfe3b167f5fa7b6103fd036ad6f239175260805ba050"
TRANSPORT_SHA256 = "1e92505751ed3a560a750993b86977847caa36e122e6aed0b3a9491cff6ecba4"
GENERATOR_SHA256 = "723d763319cd272c2eefb8afe0f551eacdfa71e330bf1711d33c3726984219a8"
T_MIN, T_JOIN, T_MAX = 300.0, 1000.0, 2200.0
P_MIN, P_MAX = 50000.0, 5000000.0
TEMPERATURE_BUDGET = 1e-8


def fail(code, path, message, **metadata):
    raise ValueContractError(code, path, message, component="thermo", metadata=metadata)


def finite(value, path, code="EOS_OUT_OF_DOMAIN"):
    if type(value) not in (int, float):
        fail(code, path, "Expected finite SI number")
    try:
        value = float(value)
    except OverflowError:
        fail(code, path, "Number exceeds binary64")
    if not isfinite(value):
        fail(code, path, "Expected finite SI number")
    return value


def temperature(T):
    T = finite(T, "/T")
    if not T_MIN <= T <= T_MAX:
        fail("EOS_OUT_OF_DOMAIN", "/T", "Temperature outside [300,2200] K", value=T)
    return T


def pressure(p):
    p = finite(p, "/p")
    if not P_MIN <= p <= P_MAX:
        fail("EOS_OUT_OF_DOMAIN", "/p", "Pressure outside [50000,5000000] Pa", value=p)
    return p


def composition(Y):
    if not isinstance(Y, (tuple, list)) or len(Y) != 5:
        fail("COMPOSITION_INVALID", "/Y", "Expected five mass fractions in normative species order")
    values = tuple(finite(y, f"/Y/{i}", "COMPOSITION_INVALID") for i, y in enumerate(Y))
    if any(y < 0 or y > 1 for y in values):
        fail("COMPOSITION_INVALID", "/Y", "Mass fractions must be in [0,1]")
    total = fsum(values)
    # gamma_5 bounds summation representation roundoff, not physical slack.
    # The original fractions are retained; no dependent fraction is replaced.
    gamma5 = 5 * float_info.epsilon / (1 - 5 * float_info.epsilon)
    if abs(total - 1) > gamma5 * total:
        fail("COMPOSITION_INVALID", "/Y", "Mass fractions do not sum to one", total=total)
    return values


@dataclass(frozen=True, slots=True)
class _NASA:
    name: str
    R: float
    low: tuple[float, ...]
    high: tuple[float, ...]
    h_join: float
    s_join: float


def _h_low(a, T):
    return fsum([a[i] * T ** (i + 1) / (i + 1) for i in range(5)] + [a[5]])


def _s_low(a, T):
    return fsum([a[0] * log(T)] + [a[i] * T ** i / i for i in range(1, 5)] + [a[6]])


@dataclass(frozen=True, slots=True)
class ThermoDataset:
    derived_bytes: bytes = field(repr=False)
    raw_bytes: bytes = field(repr=False)
    transport_bytes: bytes = field(repr=False)
    generator_bytes: bytes = field(repr=False)
    expected_sha256: str
    expected_raw_sha256: str
    expected_transport_sha256: str
    expected_generator_sha256: str
    species: tuple[_NASA, ...] = field(init=False, repr=False)
    name: str = field(init=False, default=DATASET_NAME)
    version: str = field(init=False, default=DATASET_VERSION)

    def __post_init__(self):
        for label, data, expected, accepted in (
            ("derived", self.derived_bytes, self.expected_sha256, DERIVED_SHA256),
            ("raw", self.raw_bytes, self.expected_raw_sha256, RAW_SHA256),
            ("transport", self.transport_bytes, self.expected_transport_sha256, TRANSPORT_SHA256),
            ("generator", self.generator_bytes, self.expected_generator_sha256, GENERATOR_SHA256),
        ):
            if type(data) is not bytes:
                fail("DATASET_HASH_MISMATCH", "/dataset/" + label, "Dataset requires original immutable bytes")
            actual = sha256(data).hexdigest()
            if actual != expected or actual != accepted:
                fail("DATASET_HASH_MISMATCH", "/dataset/" + label,
                     "Supplied bytes, expected hash and accepted R3 identity must agree",
                     actual=actual, expected=expected, accepted=accepted)
        data = json.loads(self.derived_bytes)
        entries = []
        for row in data["species"]:
            low = tuple(map(float, row["raw_nasa7_low"]))
            high = tuple(map(float, row["raw_nasa7_high"]))
            R = float(data["Ru_J_kmol_K"]) / float(row["MW_kg_kmol"])
            entries.append(_NASA(row["name"], R, low, high,
                                 R * _h_low(low, T_JOIN), R * _s_low(low, T_JOIN)))
        object.__setattr__(self, "species", tuple(entries))

    @property
    def sha256(self):
        return self.expected_sha256

    @property
    def raw_sha256(self):
        return self.expected_raw_sha256

    @property
    def transport_sha256(self):
        return self.expected_transport_sha256

    @property
    def generator_sha256(self):
        return self.expected_generator_sha256

    def to_mapping(self):
        """Detached provenance metadata; resource IDs remain caller-owned."""
        return {"schema_version": "1.0", "name": self.name, "version": self.version,
                "sha256": self.sha256, "raw_sha256": self.raw_sha256,
                "transport_sha256": self.transport_sha256,
                "generator_sha256": self.generator_sha256, "species": list(SPECIES)}

    @classmethod
    def from_files(cls, derived_path, raw_path, transport_path, generator_path, *,
                   expected_sha256, expected_raw_sha256, expected_transport_sha256,
                   expected_generator_sha256):
        data = []
        for label, path in zip(("derived", "raw", "transport", "generator"),
                               (derived_path, raw_path, transport_path, generator_path)):
            try:
                data.append(Path(path).read_bytes())
            except (OSError, TypeError, ValueError) as exc:
                fail("DATASET_HASH_MISMATCH", "/dataset/" + label,
                     "Required dataset resource unavailable", reason=str(exc))
        return cls(*data, expected_sha256, expected_raw_sha256,
                   expected_transport_sha256, expected_generator_sha256)


@dataclass(frozen=True, slots=True)
class SpeciesProperties:
    names: tuple[str, ...]
    cp: tuple[float, ...]
    cv: tuple[float, ...]
    h: tuple[float, ...]
    e: tuple[float, ...]
    s: tuple[float, ...]
    R: tuple[float, ...]

    def __post_init__(self):
        if not isinstance(self.names, (tuple, list)) or tuple(self.names) != SPECIES:
            fail("COMPOSITION_INVALID", "/names", "Expected normative species order")
        object.__setattr__(self, "names", tuple(self.names))
        for key in ("cp", "cv", "h", "e", "s", "R"):
            values = getattr(self, key)
            if not isinstance(values, (tuple, list)) or len(values) != 5:
                fail("EOS_OUT_OF_DOMAIN", "/" + key, "Expected five species properties")
            values = tuple(finite(v, f"/{key}/{i}") for i, v in enumerate(values))
            if key in ("cp", "cv", "R") and any(v <= 0 for v in values):
                fail("EOS_OUT_OF_DOMAIN", "/" + key, "Property must be positive")
            object.__setattr__(self, key, values)


@dataclass(frozen=True, slots=True)
class InversionDiagnostic:
    kind: str
    target: float
    residual: float
    iterations: int
    temperature_bracket: tuple[float, float]

    def __post_init__(self):
        if self.kind not in ("energy", "enthalpy"):
            fail("EOS_INVERSION_FAILED", "/diagnostic/kind", "Unknown inverse kind")
        for key in ("target", "residual"):
            object.__setattr__(self, key, finite(getattr(self, key), "/diagnostic/" + key,
                                               "EOS_INVERSION_FAILED"))
        if type(self.iterations) is not int or self.iterations < 1:
            fail("EOS_INVERSION_FAILED", "/diagnostic/iterations", "Expected positive iteration count")
        bracket = self.temperature_bracket
        if not isinstance(bracket, (tuple, list)) or len(bracket) != 2:
            fail("EOS_INVERSION_FAILED", "/diagnostic/temperature_bracket", "Expected two bounds")
        bracket = tuple(temperature(t) for t in bracket)
        if bracket[0] > bracket[1] or bracket[1] - bracket[0] > TEMPERATURE_BUDGET:
            fail("EOS_INVERSION_FAILED", "/diagnostic/temperature_bracket", "Invalid final bracket")
        object.__setattr__(self, "temperature_bracket", bracket)


@dataclass(frozen=True, slots=True)
class ThermoState:
    T: float
    p: float
    rho: float
    R: float
    cp: float
    cv: float
    h: float
    e: float
    gamma: float
    a: float
    Y: tuple[float, ...]
    dataset_sha256: str
    diagnostic: InversionDiagnostic | None = None

    def __post_init__(self):
        object.__setattr__(self, "T", temperature(self.T))
        object.__setattr__(self, "p", pressure(self.p))
        object.__setattr__(self, "Y", composition(self.Y))
        for key in ("rho", "R", "cp", "cv", "h", "e", "gamma", "a"):
            value = finite(getattr(self, key), "/" + key)
            if key not in ("h", "e") and value <= 0:
                fail("EOS_OUT_OF_DOMAIN", "/" + key, "Property must be positive")
            object.__setattr__(self, key, value)
        if self.dataset_sha256 != DERIVED_SHA256:
            fail("DATASET_HASH_MISMATCH", "/dataset_sha256", "Expected accepted runtime identity")
        if self.diagnostic is not None:
            if not isinstance(self.diagnostic, InversionDiagnostic):
                fail("EOS_INVERSION_FAILED", "/diagnostic", "Expected immutable inversion diagnostic")
            lo, hi = self.diagnostic.temperature_bracket
            if not lo <= self.T <= hi:
                fail("EOS_INVERSION_FAILED", "/diagnostic/temperature_bracket", "Returned T outside final bracket")

    def to_mapping(self):
        """Detached versioned JSON object; all numerical values are SI."""
        result = asdict(self)
        result["schema_version"] = "1.0"
        result["Y"] = list(self.Y)
        if result["diagnostic"] is not None:
            result["diagnostic"]["temperature_bracket"] = list(self.diagnostic.temperature_bracket)
        return result


@dataclass(frozen=True, slots=True)
class ThermoModel:
    dataset: ThermoDataset
    config_snapshot: ConfigSnapshot | None = field(default=None, repr=False)

    def __post_init__(self):
        if not isinstance(self.dataset, ThermoDataset):
            fail("DATASET_HASH_MISMATCH", "/dataset", "A verified ThermoDataset is required")
        if self.config_snapshot is not None:
            if not isinstance(self.config_snapshot, ConfigSnapshot):
                fail("DATASET_HASH_MISMATCH", "/config_snapshot", "Expected immutable ConfigSnapshot")
            supplied = {ref.sha256 for ref in self.config_snapshot.resource_refs}
            required = {self.dataset.sha256, self.dataset.raw_sha256,
                        self.dataset.transport_sha256, self.dataset.generator_sha256}
            if not required <= supplied:
                fail("DATASET_HASH_MISMATCH", "/config_snapshot/resource_refs",
                     "Snapshot must bind RAW, derived, transport and generator identities",
                     missing=tuple(sorted(required - supplied)))

    def species_properties(self, T):
        T = temperature(T)
        cp, h, e, s, gas = [], [], [], [], []
        for row in self.dataset.species:
            a = row.low if T < T_JOIN else row.high
            cp_value = row.R * fsum(a[i] * T ** i for i in range(5))
            if T < T_JOIN:
                h_value = row.R * _h_low(a, T)
                s_value = row.R * _s_low(a, T)
            else:
                # Factor T^n-Tm^n as (T-Tm)*sum(T^j*Tm^(n-1-j)).
                # This is the exact analytic integral with stable join behavior.
                delta = T - T_JOIN
                powers = [delta * fsum(T ** j * T_JOIN ** (n - 1 - j)
                                      for j in range(n)) for n in range(1, 6)]
                h_value = row.h_join + row.R * fsum(a[i] * powers[i] / (i + 1)
                                                   for i in range(5))
                s_value = row.s_join + row.R * fsum(
                    [a[0] * log1p(delta / T_JOIN)] +
                    [a[i] * powers[i - 1] / i for i in range(1, 5)])
            cp.append(cp_value)
            h.append(h_value)
            e.append(h_value - row.R * T)
            s.append(s_value)
            gas.append(row.R)
        return SpeciesProperties(SPECIES, tuple(cp), tuple(c - r for c, r in zip(cp, gas)),
                                 tuple(h), tuple(e), tuple(s), tuple(gas))

    def _mixture(self, T, Y):
        properties = self.species_properties(T)
        R = fsum(y * value for y, value in zip(Y, properties.R))
        cp = fsum(y * value for y, value in zip(Y, properties.cp))
        h = fsum(y * value for y, value in zip(Y, properties.h))
        return R, cp, cp - R, h, h - R * T

    def _state(self, T, p, rho, Y, diagnostic=None):
        R, cp, cv, h, e = self._mixture(T, Y)
        gamma = cp / cv
        return ThermoState(T, p, rho, R, cp, cv, h, e, gamma,
                           sqrt(gamma * R * T), Y, self.dataset.sha256, diagnostic)

    def evaluate(self, T, p, Y):
        T, p, Y = temperature(T), pressure(p), composition(Y)
        R = fsum(y * row.R for y, row in zip(Y, self.dataset.species))
        return self._state(T, p, p / (R * T), Y)

    def _invert(self, target, Y, kind, *, rho=None, p=None):
        index, derivative = (4, 2) if kind == "energy" else (3, 1)
        lo, hi = T_MIN, T_MAX
        lower, upper = self._mixture(lo, Y)[index], self._mixture(hi, Y)[index]
        if target < lower or target > upper:
            fail("EOS_OUT_OF_DOMAIN", "/e" if kind == "energy" else "/h",
                 "Target outside the contracted thermodynamic range",
                 target=target, minimum=lower, maximum=upper)
        # Explicitly select one continuous interval at the NASA join.
        join = self._mixture(T_JOIN, Y)[index]
        if target < join:
            hi = T_JOIN
        else:
            lo = T_JOIN
        R = fsum(y * row.R for y, row in zip(Y, self.dataset.species))
        if rho is not None and (rho * (R * T_MAX) < P_MIN or rho * (R * T_MIN) > P_MAX):
            fail("EOS_OUT_OF_DOMAIN", "/rho", "No temperature in domain yields an admissible pressure")
        best = None
        for iteration in range(1, 100):
            mid = lo + (hi - lo) / 2
            values = self._mixture(mid, Y)
            residual = values[index] - target
            if best is None or abs(residual) < abs(best[1]):
                best = mid, residual
            if residual < 0:
                lo = mid
            elif residual > 0:
                hi = mid
            if hi - lo <= TEMPERATURE_BUDGET or residual == 0:
                # Select a representable state in the final temperature/error
                # bracket that also respects strict pressure bounds. The input
                # rho/energy is never corrected, nor is computed pressure clipped.
                root_bracket = (mid, mid) if residual == 0 else (lo, hi)
                candidates = {lo, hi, mid}
                if lo <= best[0] <= hi:
                    candidates.add(best[0])
                if rho is not None:
                    for bound in (P_MIN, P_MAX):
                        point = bound / (rho * R)
                        for value in (point, nextafter(point, float("-inf")),
                                      nextafter(point, float("inf"))):
                            # Across the continuous join, rounded equal targets
                            # can lie on adjacent representable temperatures.
                            # Enclose candidate AND the root bracket; never
                            # enlarge the contracted final temperature budget.
                            width = max(root_bracket[1], value) - min(root_bracket[0], value)
                            if T_MIN <= value <= T_MAX and width <= TEMPERATURE_BUDGET:
                                candidates.add(value)
                valid = []
                for T in candidates:
                    final_bracket = (min(T, root_bracket[0]), max(T, root_bracket[1]))
                    if final_bracket[1] - final_bracket[0] > TEMPERATURE_BUDGET:
                        continue
                    v = self._mixture(T, Y)
                    delta = v[index] - target
                    recovered_p = rho * (R * T) if rho is not None else p
                    if P_MIN <= recovered_p <= P_MAX and abs(delta) <= v[derivative] * TEMPERATURE_BUDGET:
                        valid.append((abs(delta), T, recovered_p, delta, final_bracket))
                if valid:
                    _, T, recovered_p, delta, final_bracket = min(valid)
                    result_rho = rho if rho is not None else p / (R * T)
                    diagnostic = InversionDiagnostic(kind, target, delta, iteration, final_bracket)
                    return self._state(T, recovered_p, result_rho, Y, diagnostic)
                if residual == 0:
                    break
                if mid == lo == hi or nextafter(lo, hi) >= hi:
                    break
        if rho is not None and not P_MIN <= rho * (R * best[0]) <= P_MAX:
            fail("EOS_OUT_OF_DOMAIN", "/p", "Recovered pressure outside contracted range",
                 recovered_pressure=rho * (R * best[0]), target=target)
        fail("EOS_INVERSION_FAILED", "/e" if kind == "energy" else "/h",
             "Bracketed solve did not satisfy temperature and residual criteria",
             target=target, bracket=(lo, hi), iterations=iteration)

    def invert_energy(self, rho, e, Y, *, initial_guess=None):
        """Recover properties retaining original rho and diagnostic e target.

        initial_guess is an intentionally ignored compatibility hint: neither
        branch selection nor results depend on it.
        """
        rho, e, Y = finite(rho, "/rho"), finite(e, "/e"), composition(Y)
        if rho <= 0:
            fail("EOS_OUT_OF_DOMAIN", "/rho", "Density must be positive")
        return self._invert(e, Y, "energy", rho=rho)

    def invert_enthalpy(self, p, h, Y, *, initial_guess=None):
        """Recover unique temperature retaining the original enthalpy target."""
        return self._invert(finite(h, "/h"), composition(Y), "enthalpy", p=pressure(p))
