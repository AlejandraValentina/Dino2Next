"""Explicit mathematical EOS shared by the S06 constant-gamma fixtures only.

This file is outside the production package. It cannot supply GEN1 chemistry,
experimental data, or a NASA fallback. All five artificial species have the
same gas constant and heat capacity in this canonical homogeneous limit.
"""
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from dino2next.units import ValueContractError


class CanonicalGamma:
    source_kind = "NUMERICAL_FIXTURE_ONLY"
    identity = "C1.0-R3/S06/canonical-gamma-1.4-R-1/v1"
    gamma = 1.4
    R = 1.0

    @property
    def reference_sha256(self):
        return sha256(Path(__file__).read_bytes()).hexdigest()

    @staticmethod
    def _positive(*arrays):
        if any(np.any(~np.isfinite(a)) or np.any(a <= 0) for a in arrays):
            raise ValueContractError("EOS_OUT_OF_DOMAIN", "/canonical_eos",
                                     "Canonical rho, p, T and e must be positive")

    def evaluate_batch(self, rho, p, Y):
        rho, p = np.asarray(rho), np.asarray(p)
        self._positive(rho, p)
        T = p / rho
        cv = np.full_like(T, self.R / (self.gamma - 1))
        return dict(p=p, T=T, e=cv*T, cp=cv+self.R, cv=cv,
                    R=np.full_like(T, self.R), a=np.sqrt(self.gamma*p/rho))

    def recover_batch(self, rho, e, Y):
        rho, e = np.asarray(rho), np.asarray(e)
        self._positive(rho, e)
        p = (self.gamma - 1)*rho*e
        return self.evaluate_batch(rho, p, Y)

    def species_properties_batch(self, T):
        T = np.asarray(T)
        self._positive(T)
        cv = np.full(T.shape+(5,), self.R/(self.gamma-1))
        return dict(e=cv*T[..., None], cv=cv, R=np.ones_like(cv))

    def invert_energy(self, rho, e, Y):
        self._positive(np.asarray(rho), np.asarray(e))
        cv = self.R/(self.gamma-1)
        T = e/cv
        p = rho*self.R*T
        return SimpleNamespace(T=T, p=p, rho=rho, R=self.R, cp=cv+self.R,
                               cv=cv, h=e+self.R*T, e=e, gamma=self.gamma,
                               a=(self.gamma*p/rho)**.5, Y=tuple(Y))
