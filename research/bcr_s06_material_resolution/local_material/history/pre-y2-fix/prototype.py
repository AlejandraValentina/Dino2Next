"""Research-only local moving-material-face FV prototype, not GEN1 approval."""
from pathlib import Path
import importlib.util
import sys
import numpy as np

_path = Path(__file__).resolve().parent.parent / 'material/prototype.py'
_spec = importlib.util.spec_from_file_location('material_recovery_base', _path)
_base = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _base
_spec.loader.exec_module(_base)
State, TrialRejected = _base.State, _base.TrialRejected


class LocalSolver(_base.RegionSolver):
    def __init__(self, model, base_edges, exclusion=.35):
        super().__init__(model)
        self.grid = _base.frozen(base_edges)
        if len(self.grid) < 3 or np.any(np.diff(self.grid) <= 0):
            raise TrialRejected('INVALID_BASE_GRID')
        self.dx = float(np.min(np.diff(self.grid)))
        self.exclusion = exclusion
        if not 0 < exclusion < .5:
            raise TrialRejected('INVALID_EXCLUSION')
        self.remap_records = []
        self.stage_records = []

    @staticmethod
    def interfaces(state):
        return [i for i in range(1, len(state.labels)) if state.labels[i-1] != state.labels[i]]

    def reorganize(self, state):
        """Only between full steps; conservative overlaps never cross a label.

        Retain every physical material boundary. Remove only ordinary grid
        faces within exclusion*dx of it; no small material slab is deleted.
        """
        material = state.edges[self.interfaces(state)]
        keep = [x for x in self.grid[1:-1]
                if not len(material) or np.min(abs(material-x)) >= self.exclusion*self.dx]
        edges = np.array(sorted([state.edges[0], *keep, *material, state.edges[-1]]))
        if np.array_equal(edges, state.edges):
            return state
        labels = tuple(state.labels[min(len(state.labels)-1, np.searchsorted(state.edges, x, side='right')-1)]
                       for x in (edges[:-1]+edges[1:])/2)
        inventory = np.zeros((len(labels), 12))
        for i, (left, right) in enumerate(zip(state.edges[:-1], state.edges[1:])):
            targets = [(j, max(0., min(right, b)-max(left, a)))
                       for j, (a, b) in enumerate(zip(edges[:-1], edges[1:]))
                       if min(right, b) > max(left, a)]
            remainder = state.inventory[i].copy()
            for k, (j, overlap) in enumerate(targets):
                if labels[j] != state.labels[i]:
                    raise TrialRejected('REMAP_CROSSES_MATERIAL')
                amount = remainder.copy() if k == len(targets)-1 else state.inventory[i]*(overlap/(right-left))
                inventory[j] += amount
                remainder -= amount
        result = State(edges, inventory, labels)
        self.recover(result)
        residual = np.sum(result.inventory, axis=0)-np.sum(state.inventory, axis=0)
        self.remap_records.append((len(state.labels), len(result.labels), residual.tolist()))
        return result

    @staticmethod
    def flux(U, w):
        result = U*w[1]
        result[1] += w[2]
        result[2] += w[2]*w[1]
        return result

    def rhs(self, state):
        w = self.recover(state)
        U = state.inventory/np.diff(state.edges)[:, None]
        n = len(w)
        speed = np.zeros(n+1)
        flux = np.empty((n+1, 12))
        # Fixed exterior faces, zero-gradient physical control with ledger.
        flux[0] = self.flux(U[0], w[0]); flux[-1] = self.flux(U[-1], w[-1])
        for i in range(1, n):
            rl, ul, pl, al, _ = w[i-1]; rr, ur, pr, ar, _ = w[i]
            sl = min(ul-al, ur-ar); sr = max(ul+al, ur+ar)
            dl, dr = rl*(sl-ul), rr*(sr-ur)
            sm = (pr-pl+dl*ul-dr*ur)/(dl-dr)
            ps = pl+dl*(sm-ul)
            if not np.isfinite(sm+ps) or ps <= 0 or not sl < sm < sr:
                raise TrialRejected('RIEMANN_INADMISSIBLE')
            if state.labels[i-1] != state.labels[i]:
                speed[i] = sm
                flux[i] = 0.
                flux[i, 1:3] = (ps, ps*sm)
                continue
            if sl >= 0:
                flux[i] = self.flux(U[i-1], w[i-1]); continue
            if sr <= 0:
                flux[i] = self.flux(U[i], w[i]); continue
            j, s = (i-1, sl) if sm >= 0 else (i, sr)
            rho, u, p = w[j, :3]
            density = rho*(s-u)/(s-sm)
            star = U[j]*(density/rho)
            star[1] = density*sm
            star[2] = density*(U[j, 2]/rho+(sm-u)*(sm+p/(rho*(s-u))))
            # Strict NASA admissibility; no alternate EOS or pressure repair.
            self.recover(State([0., 1.], [star], ('star',)))
            flux[i] = self.flux(U[j], w[j])+s*(star-U[j])
        return speed, flux

    def advance(self, state, requested_dt):
        """Atomic remap + fixed-topology SSPRK2; caller commits only success."""
        prepared = self.reorganize(state)
        dt = min(requested_dt, self.suggested_dt(prepared))
        result, ledger, used, failures = self.attempt(prepared, dt)
        return result, ledger, used, failures

    def step(self, state, dt):
        if not np.isfinite(dt) or dt <= 0:
            raise TrialRejected('BAD_DT')
        v0, f0 = self.rhs(state)
        stage = State(state.edges+dt*v0, state.inventory+dt*(f0[:-1]-f0[1:]), state.labels)
        v1, f1 = self.rhs(stage)
        result = State(.5*state.edges+.5*(stage.edges+dt*v1),
                       .5*state.inventory+.5*(stage.inventory+dt*(f1[:-1]-f1[1:])), state.labels)
        self.recover(result)
        gcl = np.diff(result.edges)-np.diff(state.edges)-.5*dt*(np.diff(v0)+np.diff(v1))
        self.stage_records.append({'dt': dt, 'fixed_labels': state.labels,
                                   'speed0': v0.tolist(), 'speed1': v1.tolist(),
                                   'flux0': f0.tolist(), 'flux1': f1.tolist(),
                                   'max_GCL_absolute_m': float(np.max(abs(gcl)))})
        return result, .5*dt*(f0+f1)
