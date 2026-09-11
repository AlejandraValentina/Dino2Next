# Independent S06 canonical references

Classification: `NUMERICAL_FIXTURE_ONLY`. These are reference oracles, not candidate
solvers, production NASA thermodynamics, or experimental data. Source authority is
the current frozen C1 fixture catalogue and reference execution contract. No
candidate module is imported. Each reference's `qualification.json` binds its code,
the qualification script and fixture source SHA256, plus numerical library versions.

With the pinned `requirements.txt` installed, from repository root run:

```sh
python validation/references/VAL-006/qualify.py --check
```

This checks VAL-006,007,009,010,011. Omit `--check` only to regenerate qualification
records after legitimate implementation changes. The executable assertions use
the frozen quadrature and oracle allocations and fail on unqualified evidence.
They do not run or award acceptance to the candidate numerical kernel.

Each directory supplies `reference.py` with `point_states(x,time=0,...)` and
`cell_averages(edges,time=0,...,order=32)`. Dictionaries contain rho,u,p and
`conserved` with final axis `(rho,rho*u,E)`. Conserved cells integrate products
before averaging; primitive averages are integrals of the primitive fields.
VAL-011 conserved values are means of **A times** the conservative field, while
primitive values are ordinary spatial means over dx. Thus callers must not multiply the
areaweighted conserved result by area again. Its `point_states` returns unweighted
states for physical ghost coordinates, and `area(x)` returns the prescribed area.

Options: VAL-007 `speed=0` or1; VAL-009 `epsilon=1e-5` or5e-6; VAL-010
`kind='rigid'` or `'free'`, epsilon likewise; VAL-011 `smooth=True` orFalse.
VAL-006 is the frozen Sod state and splits every integration cell at exact wave
breaks. Contact cells are integrated analytically, including a contact inside a
cell. Acoustic conserved averages include the nonlinear products of the specified
linear primitive fields; the reference wave evolution remains explicitly linear.

VAL-009/010 `fourier_coefficient(edges,pressure_perturbation)` is the exact spatial
integral of the supplied piecewise-constant cell field times exp(-2*pi*i*x), using
analytic complex cell weights. `exact_fourier(time,epsilon)` instead integrates
the continuous analytic waveform over[0,1]. Both operators are exposed explicitly;
their difference is spatial observation discretization, not oracle uncertainty.
The free-end reference includes the full incident-minus-reflected Gaussian and is
qualified against an independent80-digit whole-domain integral. A pulse peak or
arrival time never replaces that Fourier observable.

Qualification uses independent mpmath80 arithmetic and wave-split integrals for
Sod (whose gamma1.4 fan integrands have polynomial degree at most7), exact cutcell
fractions, trigonometric cell integrals, erf Gaussian integrals and a separate
high-precision subsonic area-Mach root/integral. Gauss16/32 checks include all four
contracted nozzle meshes. No scientific coefficients or tolerances are adjusted.
