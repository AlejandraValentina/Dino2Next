"""VAL-027 temporal reference: independent DOP853, selected spatial RHS.

The frozen fiche expressly requires this same-semidiscretization comparison.
It is not an independent spatial validation, NASA validation or experiment.
"""
import numpy as np
from scipy.integrate import solve_ivp


def cell_averages(edges, time=0.):
    if time != 0:
        raise ValueError('Analytic contact is initialization only; temporal reference requires DOP853')
    edges = np.asarray(edges); dx = np.diff(edges)
    rho = 1+.01*(np.cos(2*np.pi*edges[:-1])-np.cos(2*np.pi*edges[1:]))/(2*np.pi*dx)
    u = np.full_like(rho, .3); p = np.ones_like(rho)
    return dict(rho=rho, u=u, p=p, conserved=np.column_stack((rho, rho*u, p/.4+rho*u*u/2)))


def integrate(kernel, state, rhs, *, crosscheck=False):
    shape = state.Q.shape
    def derivative(t, flat):
        trial = kernel.state(state.mesh, flat.reshape(shape))
        stage = rhs(trial, t)
        return (kernel.divergence(stage.fluxes.high, state.mesh)+stage.sources).ravel()
    result = solve_ivp(derivative, (0., .1), state.Q.ravel(), method='DOP853',
                       rtol=1e-13 if crosscheck else 2.3e-14,
                       atol=1e-15 if crosscheck else 1e-16, max_step=.0001,
                       t_eval=np.linspace(0, .1, 401))
    if not result.success or result.t[-1] != .1:
        raise AssertionError('REFERENCE_NOT_QUALIFIED: DOP853 did not finish')
    return result.t, result.y.T.reshape((-1,)+shape), result.nfev
