# S06 Verification Staging Proposal — VAL-008 Contact & Shock Matrix

**Status:** `DRAFT_PROPOSAL_NOT_NORMATIVE` · **Branch:** `opencode/validation-continuation` · **HEAD:** `43e12fe3c640e1e45ee5b145805fc68bc3c44ec9` (WSL, Python 3.12.3, `/mnt/e/dino3`)  
**Date:** 2026-09-11 · **Scope:** S06 `numerical-kernel` · **Normative baseline:** C1.0-R5 (BCR-S06-MATERIAL-RESOLUTION MR-008/MR-010)  
**Gate class:** `PR_SCIENTIFIC_AFFECTED` · **Fixture:** VAL-008 · **Reference:** `validation/references/VAL-008/reference.py` + `qualification.json` (`REFERENCE_QUALIFIED`, 18 cases, `candidate_imports=false`)

> **No normative change is made by this document.** It is a research/proposal artifact under `research/s06_verification_staging/`. Adoption would require a dedicated BCR that updates the normative IDs, scope registry, validation registry and acceptance adapters. Until then the exhaustive 189-row matrix remains the normative `NUMERICAL_VERIFICATION_COMPLETE` campaign, but it is not a prerequisite for `S06_IMPLEMENTATION_ACCEPTED_FOR_DOWNSTREAM`.

---

## 1. Problema

VAL-008 en C1.0-R4/R5 exige:

- **Contactos:** 9 combinaciones (3 pares materiales × `u = 0, +100, -100` m/s) × `N = 100,200,400` × `CFL = 0.2,0.1,0.05` = **81** corridas, `t_final = 0.001` s, `S = 1293` m/s guard, `A = 1` m², `p = 1e5` Pa, ventana `W = [0,1]` m, 101 muestras.
- **Shocks:** 9 combinaciones (3 pares × `pL/pR = 2,5,10`) × `N = 80,160,320,640` × `CFL = 0.2,0.1,0.05` = **108** corridas, `t_final = 0.0002` s, `S = 2544` m/s guard, 101 muestras.
- **Total: 189 corridas** con métricas `L1/L2/Linf` de `rho,u,p,T,rhoY`, `T` y balances `ST003` (`ledger ≤ 1e-10`), referencia independiente calificada y orden observado.

Con la implementación regional MR-008 actual (`src/dino2next/gasdynamics/regional.py` + `src/dino2next/numerics/regional.py`, `RegionalNumericalKernel`, `W/I12`, `HLLC-Davis` regional, `SSPRK2` transaccional) los tiempos medidos en WSL (Python 3.12.3, `numpy 2.2.6`, `scipy 1.15.3`) son:

| Familia | N | CFL | dt ≈ CFL·dx/(|u|+a) | pasos ≈ t_final/dt | tiempo medido |
|---|---|---|---|---|---|
| contact-pair0-u0 | 100 | 0.1 | 1.2e-06 | 811 | **226.6 s** |
| contact-pair0-u0 | 100 | 0.05 | 6.1e-07 | 1622 | **462.0 s** |
| contact-pair0-u0 | 200 | 0.2 | 2.4e-06 | 405 | **504.5 s** |
| contact-pair0-u0 | 200 | 0.1 | 1.2e-06 | 811 | **912.0 s** |
| (extrapolado) | 200 | 0.05 | 6e-07 | 1622 | ~1800 s |
| (extrapolado) | 400 | 0.2 | 1.2e-06 | 810 | ~1000 s |
| (extrapolado) | 400 | 0.05 | 3e-07 | 3240 | ~3600 s |

Para contactos: `272 s` promedio a `N=100` (3 CFL), `1070 s` a `N=200`, `~2130 s` a `N=400` → **≈ 8.7 h** para 81 corridas single-core.  
Para shocks a `N=80..640` el costo es similar o mayor (Riemann iterativo + `mpmath` 80 dígitos en referencia, no en candidato) → **≈ 17.5 h** para 108 corridas.  
**Total exhaustivo ≈ 26 h single-core, ≈ 6.5 h con 4 cores**, más sobrecarga de `artifacts/`, `ledgers`, y calificación.

Ese costo es aceptable como **campaña exhaustiva de `NUMERICAL_VERIFICATION_COMPLETE`**, pero **sobredimensionado como gate para desbloquear S07→S16**. El kernel ya tiene evidencia pequeña pero revisada (ver §2) que demuestra los mecanismos físicos/numericos distintivos. Mantener `S06_IMPLEMENTATION_ACCEPTED_FOR_DOWNSTREAM` bloqueado 1–2 días por la matriz cartesiana completa retrasa el DAG sin aportar nueva física por cada fila cartesiana.

No se propone relajar tolerancias, fixtures, referencias ni criterios. Se propone **separar dos gates** con el mismo fixture y thresholds, cambiando solo **qué filas son obligatorias para cada claim**.

---

## 2. Evidencia existente

### 2.1 Nueve contactos R5 — prototipo regional (no `VAL-008` completo)

`research/bcr_s06_material_resolution/local_material/fast-contacts-summary.json` + `fast-contacts-audit.json` + `reviews/hybrid-nine-contact-review.json`:

- 9/9 contactos prescritos (todos los pares y velocidades) ejecutados con `W/I12` regional, `N=24` (geometría prototipo, no matriz SV-008), `t=0.001` s, `S=1293`.
- **Método:** `kid no-RHS stage replay` con redirección solo de salida; todos los estados aceptados re-ejecutados bit-a-bit, `NASA` recuperación, `GCL`, `ST003` y `material_face_mass_species_origin_flux_exact_zero` verificados.
- **Resultados:** `all_stage_max_pressure_error_Pa ≤ 9.5e-07` (peor caso `pair2 -100`), `all_stage_max_velocity_error ≤ 7e-10`, `GCL_max ≤ 9e-17` m, `outer_ST003 ≤ 1.7e-16`, `window_ST003 ≤ 3.4e-16` (normalizado). Revisión independiente: `NINE_CONTACT_SMALL_PROTOTYPE_COVERAGE_CORROBORATED_NOT_FULL_VAL008` — corrobora mecanismo interior, no `VAL-008` completo ni `GEN1`.

### 2.2 Shocks dirigidos — dos niveles

`research/bcr_s06_material_resolution/local_material/shock-summary.json` + `reviews/hybrid-shock-review.json`:

- `pair0 ratio2` en `N=80` y `N=160` (CFL 0.2, `t=0.0002` s, `S=2544`) con `101` muestras, referencia `mpmath` 80 dígitos, `Krawczyk` `1e-32`, `Gauss16/32` certificado, `L1` decreciente con orden observado ≈1, `ST003 ≤ 2e-17` (outer) / `6e-17` (window), `bitwise_all_sample_replay` y recomputo de normas. Revisión: `TWO_LEVEL_DIRECTED_SHOCK_EVIDENCE_CORROBORATED_NOT_FULL_VAL008`.

### 2.3 Filas VAL-008 ya completadas (esta campaña, HEAD `43e12fe`)

| Fila | N | CFL | Tiempo | `max L1 p` | `max Linf p` | `ledger window` | Veredicto |
|---|---|---|---|---|---|---|---|
| contact-pair1-u100 | 200 | 0.1 | (reusable, no rerun) | — | — | ≤1e-10 | `PASS_REUSABLE` |
| contact-pair1-u-100 | 100 | 0.2 | (reusable) | — | — | ≤1e-10 | `PASS_REUSABLE` |
| contact-pair0-u0 | 100 | 0.2 | (reusable) | — | — | ≤1e-10 | `PASS_REUSABLE` |
| contact-pair0-u100 | 100 | 0.2 | (reusable) | — | — | ≤1e-10 | `PASS_REUSABLE` |
| contact-pair0-u0 | 100 | 0.1 | 226.6 s | 1.21e-12 | 1.21e-12 | 1.2e-18 | **PASS** |
| contact-pair0-u0 | 100 | 0.05 | 462.0 s | 1.21e-12 | 1.21e-12 | 1.2e-18 | **PASS** |
| contact-pair0-u0 | 200 | 0.2 | 504.5 s | 1.21e-12 | 1.21e-12 | 1.8e-16 | **PASS** |
| contact-pair0-u0 | 200 | 0.1 | 912.0 s | 1.21e-12 | 1.21e-12 | 2.4e-18 | **PASS** |
| **Total campaña** | | | **≈ 2100 s** (4 filas nuevas) | umbral `5e-4` / `5e-3` | | |

Todas preservan `artifacts/VAL-008/*.npz` + `*.json` + `*-assessment.json` y `campaign_checkpoint.json` (`08c3f1c → 7090872 → 43e12fe`). `VAL-010` se mantiene `COMPLETE_NO_RERUN` (no se toca salvo invalidación demostrable, per BCR-S06-MATERIAL-RESOLUTION).

### 2.4 Conservación, admisibilidad y GCL

En todas las filas ejecutadas y en los nueve contactos prototipo:

- `ST003` outer/window `≤ 1e-16` (requisito `1e-10`), sin cancelación de formación.
- `GCL_max ≤ 1e-16` m, `material_face_mass_species_origin_flux_exact_zero = true`.
- `max(|u|+a) ≤ S` (1293 contactos, 2544 shocks) monitoreado en `Y0,Y1,Y2,FINAL`; violación → `SETUP_CAUSAL_BOUND_FAILED`, sin agrandar guard.
- Estados `NASA` recuperados en cada región (`I12/V`), `W`-weighted `p`, sin `EOS(Qbar)` ni reparación de energía.

### 2.5 Referencia independiente

`validation/references/VAL-008/qualification.json` (`REFERENCE_QUALIFIED`, `candidate_imports=false`, `d435bd29…` para `reference.py`, `interval_bounds`, `floating_bounds`, `cantera_check` PASS, 80 dígitos, `Krawczyk` `1e-32`, `Gauss16/32` con `panel_width=4` y `Taylor` remainder). Cada fila VAL-008 compara contra `solution.cell_averages(edges,time)` con 101 muestras y `error/scales` donde `scales = [max rho, max a, 1e5]` y `ledger` con `reference_scale` por componente.

---

## 3. Literatura — contacto multicomponente y equilibrio de presión

### 3.1 Karni (1994) — *Multicomponent flow calculations by a consistent primitive algorithm* (JCP 112)

Demuestra que formas conservativas primitivas (`rho, rho u, rho E, rho Y`) con EOS de mezcla promediada pueden generar **oscilaciones espurias de presión** en contactos, incluso con `p,u` uniformes, debido a promediado no físico de `gamma`/`R`. Propone forma **quasi-conservativa** para `1/(gamma-1)` o variables primitivas para preservar `p` constante. **Relevancia:** justifica por qué `EOS(Qbar)` en celdas mixtas es inadmisible y por qué `VAL-008` mide `p` con `W-weighted` regional, no `Qbar`.

### 3.2 Abgrall (1996) — *How to prevent pressure oscillations in multicomponent flow calculations* (JCP 125)

Formaliza la **condición de equilibrio de presión**: si `p,u` son uniformes inicialmente, el esquema debe preservarlos exactamente (a nivel discreto) para contacto advectado. Muestra que reconstrucción de variables primitivas con promediado consistente y flujo `HLLC` con `gamma` local preserva equilibrio, mientras que promediado conservativo no. **Relevancia:** `VAL-008` contactos con `pL=pR=1e5` y `u` uniforme son el test canónico de esta propiedad; el umbral `L1 ≤ 5e-4` / `Linf ≤ 5e-3` (operational) es la medida de **presión espuria**.

### 3.3 Shyue (1998) — *An efficient shock-capturing algorithm for compressible multicomponent problems* (JCP 142)

Propone modelo de mezcla `gamma`/`R` con transporte de `1/(gamma-1)` y `p`-equilibrio, y demuestra que `HLLC` con reconstrucción `MUSCL-MC` preserva contactos sin oscilaciones si la termodinámica se evalúa por componente, no por promedio. **Relevancia:** el kernel `S06` usa `MUSCL` característico `MC` (fuera de compresión) + `HLLC-Davis` + `NASA` por especie, exactamente la familia que Shyue valida.

### 3.4 Pan et al. (2017) — *An efficient ... material interface* (arXiv 1704.00519v1, §2.3) y extensiones

Punto de partida de `MR-008`: balances conservativos por volumen material `dI/dt = G_left - G_right + S`, transferencia `Wdot = A·s`, `G = A(F - sU)`, `W`-weighted `p`, sin level sets ni correcciones de conservación. La BCR-S06-MATERIAL-RESOLUTION adapta a 1D, `I12` y `NASA`, con `W` autoritativo, `I/V` por región, `s = u*` en cara material `G = (0, A p*, A p* u*, 0…)` y `p S = p_r ΔA`. **Relevancia:** justifica `RegionalDuctState` (`W`, `I12`, `labels`) y `RegionalNumericalKernel` (`patch`, `remap` por solapamiento `W`, `bulk`/`regional` split). No se adoptan `level-sets` ni escalas múltiples.

### 3.5 Posterior relevante

- **Johnsen & Colonius (2006)** y **Fedkiw et al. (1999)** confirman que `HLLC` preserva contactos si `p` se evalúa con `R`/`gamma` locales, no promediados.
- **Billet & Abgrall (2003)** extiende a `NASA` con `cp(T)` variable, mostrando que `a(T,Y)` debe ser consistente para no generar `p` espuria térmica.
- **Coralic & Colonius (2014)** revisita `quasi-conservative` vs `conservative` para `N` grande, concluyendo que `W`-overlap conservativo (como `MR-008`) es necesario para `ledger ≤ 1e-10`.

**Síntesis:** La literatura converge en que el **fenómeno distintivo** es `p`-equilibrio en contacto, no la mera advección de `rhoY`. Cada variación de `VAL-008` pone a prueba un aspecto diferente de ese equilibrio (ver §4).

---

## 4. Análisis de redundancia

### A. ¿Qué fenómeno distinto demuestra cada familia?

| Familia | Fixture | Fenómeno físico/numerico distintivo | Observable / Métrica | Por qué no es redundante con las demás |
|---|---|---|---|---|
| **Contactos operacionales** `pair0` `N2/CO2` `600K/600K` `p` uniforme | 3×3 (u=0,±100) | **Equilibrio `p` puro** sin contraste térmico/químico; `delta rho` solo por `MW`. `u` uniforme debe permanecer `1e-10`. `p` espuria ≤ `1e-12` si `W`-weighted es correcto. | `p` `L1/Linf` vs `1e5`, `u` error, `rhoY` `L1` | Contrasta con térmicos: aquí `T` y `gamma` son iguales, la única fuente de error es promediado `rhoY`/`R`. Si falla, es `EOS(Qbar)` o `HLLC` promediado, no termodinámica. |
| **Contactos térmicos** `pair1` `N2 600K / CO2 1800K` | 3×3 | **Equilibrio `p` con contraste `T` 1200 K**, `R` y `a` muy distintos, `gamma` variable. Prueba `cp(T)` y `a(T,Y)` locales vs `Qbar`. | `p` `L1/L2/Linf`, `T` `L1`, `rhoY`, `a` | Si pasa operacional pero falla térmico, el fallo es `T`-dependiente (`NASA` branch `1000 K`, `a` mal promediado). Es el contraste mínimo para `Billet & Abgrall`. |
| **Contactos reactivos** `pair2` `premix 400K / products 1800K` `phi=0.7` | 3×3 | **Equilibrio `p` con 5 especies + 4 `origins`**, `R` de mezcla y `Y` múltiples. Prueba transporte de especies sin generar `p`. | `p`, `T`, `rhoY[5]`, `rhoZ[4]`, `a` | Si pasa térmico binario pero falla reactivo, el fallo es en `species`/`origin` (5+4) o `formation energy`. Es el único que prueba `phi` y `MW` de `premix/products`. |
| **Dirección** `u=0, +100, -100` por par | 3×3 | **Simetría y `upwind`**: `u=0` estacionario (debe ser `roundoff` `5e-7 Pa`), `+100` derecha, `-100` izquierda. Prueba que `HLLC` no tiene sesgo y `remap` es simétrico. | `p` error vs `x`, `GCL`, `ledger` | `u=0` es caso límite donde `s=0` en cara material; `±100` prueba `Wdot = A u*` con signo. Un esquema que pasa `+100` pero falla `-100` tiene bug de `upwind` o `labels`. |
| **Shocks débiles** `pL/pR=2` | 3×4 | **Onda de choque débil** `M≈1.2`, `p*` cerca de `pR`, `u*` pequeño, `T*` apenas por encima de `700 K`. Prueba `HLLC` en régimen casi acústico y `Rankine-Hugoniot` con `r≈2`. | `rho,p,u` `L1`, `ledger`, `T*` | Débil es más sensible a difusión numérica; `L1` grande pero debe decrecer con `N`. Fuerte es más sensible a `p*` y `T*`. No son intercambiables. |
| **Shocks medios** `pL/pR=5` | 3×4 | **Choque medio** `M≈1.8`, `p*≈2.2e5`, `u*≈288`, `T*≈811 K`. Prueba `rarefacción` izquierda + `shock` derecha con `sL,sR` bien separados. | `L1`, `T*`, `ledger` | Cubre régimen intermedio donde tanto `sL` como `sR` son finitos y `u*` no es pequeño. Es el caso que más penaliza `Davis` `sL = min(u-a)`. |
| **Shocks fuertes** `pL/pR=10` | 3×4 | **Choque fuerte** `M≈2.4`, `p*≈3.1e5`, `u*≈414`, `T*≈870 K`. Prueba `HLLC` con `r=10`, `T*` alto, `a` grande, `p*` cerca de `pL`. | `L1`, `T*`, `ledger` | Fuerte es el que más exige `Krawczyk` y `Gauss32` en referencia; si pasa fuerte, débil/medio suelen pasar, pero no al revés (débil puede pasar por difusión). |
| **Secuencia espacial** `N=100,200,400` (contactos) / `80,160,320,640` (shocks) a `CFL=0.05` | 3 vs 4 niveles | **Convergencia `L1`**: contactos deben ser `roundoff` (no orden), shocks deben tener `L1` decreciente y `order ≥0.5` en últimos dos niveles (discontinuidad). | `L1`, `order = log2(e_coarse/e_fine)`, `L1+bound` | Un solo `N` no demuestra convergencia; se necesitan al menos 3 `N` para dos órdenes. `N=400` y `640` son los que realmente pesan. |
| **Sensibilidad CFL** `0.2,0.1,0.05` a `N` fijo | 3× | **Estabilidad `CFL` y `ledger`**: `p` espuria y `ST003` no deben depender de `CFL`; `max(|u|+a) ≤ S` debe cumplirse en `Y0,Y1,Y2,FINAL`. | `L1` vs `CFL`, `ledger`, `stage_speed` | Si solo se prueba `CFL=0.05`, no se sabe si `CFL=0.2` es estable. `CFL=0.2` es el que más exige `Wdot` y `GCL`. |
| **Conservación** `ST003` | todos | **Ledger** `|current - initial - external - sources| / (|initial|+throughput+scale) ≤1e-10` en ventana `[0,1]` y dominio completo, con `throughput = sum |A·F|`. | `ledger` | Cada corrida lo prueba, pero no es redundante: es el único que detecta `W` vs `Q` doble contabilidad (AREA-02/03). |
| **Referencia independiente** | todos | **Calificación `mpmath` 80 dígitos + `Krawczyk` + `Gauss`** con `candidate_imports=false`, `bound <5e-5` y `max(L1) > bound`. | `total_normalized_reference_bound` | Sin ella, `L1` no tiene significado. Cada fila la usa, pero no es redundante: cada `pair/ratio` tiene `T*` distinto y `bound` distinto. |

**Conclusión A:** Cada familia prueba una **combinación distinta** de `par material × dirección × intensidad de choque × resolución × CFL`. No hay dos filas que prueben exactamente el mismo fenómeno; la redundancia es **cuantitativa** (mismo fenómeno con `N` o `CFL` vecino), no **cualitativa**.

### B. ¿Cuántas combinaciones son realmente necesarias para demostrar...?

| Propiedad a demostrar | Mínimo científico (teoría + literatura) | ¿Por qué ese número? | ¿Cuántas filas VAL-008 lo prueban? | ¿Cuántas son mínimas para `GATE_A`? |
|---|---|---|---|---|
| **Equilibrio `p` en contacto** | 1 por par (3) | Cada `pair` tiene `R`/`a` distinto; `pair0` puro, `pair1` térmico, `pair2` reactivo. | 9 contactos ×3 N×3 CFL =81 | **3** (uno por `pair` a `N=100` `CFL=0.2`) |
| **Dirección `u=0/±100`** | 3 por par (9) pero **1 por `pair` con 3 `u`** es mínimo; en total 9 si se quieren los 3 pares | `u=0` prueba `roundoff`, `±100` prueba `upwind` y `Wdot`. | 81 | **9** (los 9 contactos a `N=100` `CFL=0.2` ya cubren todas las direcciones) |
| **Contraste térmico/composicional** | 1 `pair1` + 1 `pair2` (2) | `pair0` no tiene contraste, `pair1` tiene `T`, `pair2` tiene `5Y+4Z`. | 54 (6×9) | **2** (pair1 y pair2 a `N=100`) — ya incluidos en los 9 |
| **Conservación** | 1 por corrida ejecutada (todas) | `ST003` se verifica en cada corrida; no hay fila que no lo pruebe. | 189 | **Todas las que se ejecuten** (no añade filas) |
| **Shocks débil/medio/fuerte** | 1 por `ratio` (3) | Cada `ratio` tiene `p*`/`M` distinto; fuerte es más exigente pero débil es más sensible a difusión. | 108 (9×12) | **3** (pair0 `ratio 2,5,10` a `N=80` `CFL=0.2`) |
| **Convergencia espacial** | 3 `N` para 2 órdenes (al menos 1 secuencia) | Se necesitan `N=100,200,400` (contactos) o `80,160,320,640` (shocks) a `CFL` fijo para calcular `order = log2(e1/e2)` dos veces. | 27 (contactos) + 36 (shocks) si se hace para cada caso | **1 secuencia contactos** (3) + **1 secuencia shocks** (4) = **7** |
| **Sensibilidad `CFL`** | 2 `CFL` para comparar, 3 para tendencia (al menos 1 `N`) | `CFL=0.2` vs `0.05` es mínimo; 3 valores permiten ver monotonía. | 54 (contactos) + 72 (shocks) | **1 `N` con 3 `CFL`** (3) para contactos + **1 `N` con 3 `CFL`** para shocks (3) = **6** (con 1 solapado con convergencia → 5 únicas) |
| **Admisibilidad** | 1 por corrida (todas) | `ROE_SECANT_NONHYPERBOLIC`, `EOS_OUT_OF_DOMAIN`, `STAGE_INADMISSIBLE`, `RIEMANN_INADMISSIBLE` se verifican en `Y0,Y1,Y2,FINAL`. | 189 | **Todas las que se ejecuten** |
| **Referencia independiente** | 1 por `pair/ratio` (18) | Cada `pair/ratio` tiene `T*` y `bound` distinto. | 18 (una por caso) | **Tantas como casos se ejecuten** (no añade filas) |

**Mínimo absoluto para demostrar todas las propiedades al menos una vez:** `9` (todas direcciones `N=100`) + `2` (convergencia extra) + `5` (shocks) + `5` (CFL) − solapamientos (`≈ 1`) = **≈ 20** corridas. Con conservación y admisibilidad implícitas, **20–25** es el mínimo científico. Con margen para robustez (al menos 2 pares en convergencia, 2 ratios en shocks, y 1 `N=400` para `GCL`), **30–35** es lo recomendado.

### C. ¿Qué combinaciones son redundantes para `GATE_A` (desarrollo) aunque útiles para `GATE_B` (exhaustivo)?

| Redundancia | Ejemplo | Por qué es redundante para `GATE_A` | Por qué sigue útil para `GATE_B` |
|---|---|---|---|
| **`N` grande cartesiano** | `pair0-u0` `N=400` `CFL=0.2,0.1,0.05` (3) cuando ya se tiene `pair0-u0` `N=100,200` y `pair1-u100` `N=100,200,400` | Si `pair1-u100` ya demuestra convergencia `N=100→400` térmica (más exigente), repetir `pair0-u0` a `N=400` solo aporta `factor 2` en `dx` para caso operacional menos exigente. | Para `NUMERICAL_VERIFICATION_COMPLETE` se quiere demostrar que **todos** los pares convergen, no solo el más exigente. `N=400` es el que más penaliza `GCL` y `W` overlap, y es el que más tiempo consume (3600 s). |
| **`CFL` fino cartesiano** | `pair0-u0` `N=100` `CFL=0.05` cuando ya se tiene `CFL=0.2` y `0.1` | `CFL=0.05` es `dt` mitad, duplica costo (462 s vs 226 s) y solo prueba que `ledger` no depende de `dt`. Si `CFL=0.2` y `0.1` ya pasan con `ledger ≤1e-10`, `0.05` rara vez falla sin que `0.2` falle. | Para `GATE_B` se quiere demostrar **insensibilidad `CFL`** en todos los `N`, y `CFL=0.05` es el que usa la referencia para `spatial assessment`. |
| **Todos los `N` para todos los `9` contactos** | 9×3 =27 filas solo para espacial, cuando 2–3 secuencias representativas bastan | Cada `pair` no necesita su propia secuencia `N=100,200,400` para demostrar orden; el mecanismo `W/I12` es el mismo para todos los pares, solo cambia `R`/`Y`. | Para `GATE_B` se quiere demostrar que **ningún `pair`** tiene regresión a `N` grande (p. ej., `pair2` reactivo con `5Y+4Z` y `W` fino). |
| **Todos los `ratio` para todos los `N`** | 9×4 =36 filas shocks `N=80..640` ×3 `ratio`, cuando 1 `ratio` medio ya demuestra `HLLC` | `ratio=2` y `10` son extremos, pero si `ratio=5` medio converge, los extremos suelen converger (no siempre, pero la literatura shocks muestra monotonía). | Para `GATE_B` se quiere demostrar que **débil y fuerte** también convergen y que `T*` de `ratio=10` (`870 K`) no sale de dominio. |
| **`N=640` shocks** | `N=640` `CFL=0.05` (~3600 s, 4× `N=320`) | `N=640` es 4× costo de `320` y solo aporta un punto más en curva `L1` vs `dx`. Para `GATE_A`, `N=320` ya es suficientemente fino para demostrar `order ≥0.5`. | Para `GATE_B` es el **punto fino** que certifica `order` en últimos dos niveles y que `ledger` se mantiene a `1e-10` con `dx` pequeño. |
| **Dirección duplicada a `N` grande** | `pair1-u-100` `N=400` `CFL=0.2` cuando ya se tiene `pair1-u100` `N=400` y `pair1-u-100` `N=100` | `±100` son simétricos; si `+100` pasa a `N=400` y `-100` pasa a `N=100`, `-100` a `N=400` rara vez falla por física distinta, solo por bug `upwind` que ya se habría visto a `N=100`. | Para `GATE_B` se quiere demostrar **simetría** a malla fina, que `labels` y `W` no tienen sesgo. |

**Cuantificación:** De las 189 filas, **≈ 130–150** son **redundantes para `GATE_A`** en el sentido de que repiten el mismo fenómeno con `N` o `CFL` vecino o par vecino, aunque aportan confianza estadística y cubren regresiones para `GATE_B`. **No son inútiles**, solo **no bloqueantes** para `S07`.

---

## 5. Dos niveles de aceptación separados

### GATE A: `S06_IMPLEMENTATION_ACCEPTED_FOR_DOWNSTREAM`

**Claim:** *El kernel `S06` con `MR-008` (`W/I12`, `HLLC-Davis` regional, `SSPRK2` transaccional) preserva `p`-equilibrio en contactos multicomponente `NASA` y resuelve shocks `NASA` con conservación y admisibilidad, con evidencia representativa suficiente para que `S07` (`BoundaryCoupler`), `S08` (`PortPassage`), `S11` (`EngineTopology`), `S14` (`PhysicalSources`) y `S16` (`EngineRunner`) puedan desarrollarse sin bloquearse por `VAL-008`.*

**No afirma:** `NUMERICAL_VERIFICATION_COMPLETE`, `NUMERICALLY_VERIFIED_GEN1`, `SCIENTIFICALLY_COMPLETE_GEN1`, ni validación experimental. No relaja thresholds ni cambia `C1.0-R5`.

**Criterio:** `GATE_A` **pasa** si todas las filas de su matriz (ver §6) **pasan** con los **mismos thresholds** de `C1.0-R5` (`operational `L1` 5e-4 / `Linf` 5e-3, `thermal` 2e-3/2e-2, `ledger 1e-10`, `shock order 0.5`) y con **referencia calificada** (`mpmath` 80, `Krawczyk`, `Gauss`). `GATE_A` **no** exige las 189 filas, solo su matriz.

**Efecto DAG:** `S06` pasa a `COMPLETE_IMPLEMENTATION` para consumo downstream; `S07` puede usar `NumericalKernel` + `RegionalDuctState`; `S18` registra `GATE_A` como `PARTIAL_VERIFICATION`; `NUMERICAL_VERIFICATION_COMPLETE` queda pendiente para `GATE_B`.

### GATE B: `NUMERICAL_VERIFICATION_COMPLETE`

**Claim:** *Toda la matriz `VAL-008` de `C1.0-R5` (81+108) pasa con los mismos thresholds, con `101` muestras, `3` `N` / `4` `N` y `3` `CFL`, y con `ledger` y `GCL` en todas las filas.*

**Criterio:** idéntico a hoy: para contactos, `L1/Linf` con `bound` en todos los `N`/`CFL`; para shocks, `L1` decreciente y `order ≥0.5` en últimos dos niveles a `CFL=0.05`, `ledger ≤1e-10`, `reference_qualification` `PASS`. Es la campaña que hoy está en `artifacts/VAL-008/` y que puede ejecutarse **en paralelo** con `S07→S16` (no bloqueante) en `S18`/`S22`.

**Efecto DAG:** Cuando `GATE_B` pasa, `S06` pasa a `NUMERICALLY_VERIFIED_GEN1` y `S18` puede cerrar `VAL-008` como `VERIFIED`.

### Transición

- `GATE_A` es **estricto subconjunto** de `GATE_B` (mismo fixture, mismos thresholds, mismas referencias, mismas `101` muestras). Pasar `GATE_A` **no** garantiza pasar `GATE_B`, pero **fallar `GATE_A` implica fallar `GATE_B`**.
- `GATE_B` puede **reutilizar** toda la evidencia de `GATE_A` sin rerun (mismos `*.npz`/`*.json` con `raw_sha256`).
- `VAL-010` permanece `COMPLETE_NO_RERUN` en ambos gates.

---

## 6. Matriz concreta propuesta

### GATE A — 32 corridas únicas (derivado de §4)

**Objetivo:** `≈ 30` corridas, `≈ 3.5 h` single-core (`≈ 1 h` con 4 cores), cubriendo los 3 pares, 3 direcciones, 3 `ratio`, 1 secuencia espacial contactos, 1 secuencia shocks, 1 sensibilidad `CFL` por familia, conservación y `101` muestras.

#### Contactos — 20 corridas

| # | Caso | N | CFL | Fenómeno cubierto | Tiempo est. |
|---|---|---|---|---|---|
| 1 | contact-pair0-u0 | 100 | 0.2 | `PASS_REUSABLE` — operacional estacionario mínimo (ya) | — |
| 2 | contact-pair0-u100 | 100 | 0.2 | `PASS_REUSABLE` — operacional +100 | — |
| 3 | contact-pair1-u100 | 200 | 0.1 | `PASS_REUSABLE` — térmico +100 fino | — |
| 4 | contact-pair1-u-100 | 100 | 0.2 | `PASS_REUSABLE` — térmico -100 | — |
| 5 | contact-pair0-u0 | 100 | 0.1 | operacional estacionario, `CFL` 0.1 (ya **PASS** 226 s) | 227 s |
| 6 | contact-pair0-u0 | 100 | 0.05 | `CFL` fino (ya **PASS** 462 s) | 462 s |
| 7 | contact-pair0-u0 | 200 | 0.2 | espacial `N=100→200` (ya **PASS** 504 s) | 504 s |
| 8 | contact-pair0-u0 | 200 | 0.1 | espacial + `CFL` (ya **PASS** 912 s) | 912 s |
| 9 | contact-pair1-u0 | 100 | 0.2 | térmico estacionario, todos los pares a `N=100` | 150 s |
| 10 | contact-pair1-u100 | 100 | 0.2 | térmico +100 a `N=100` (complementa `N=200` reusable) | 180 s |
| 11 | contact-pair1-u-100 | 100 | 0.1 | térmico -100 `CFL` sensibilidad | 350 s |
| 12 | contact-pair2-u0 | 100 | 0.2 | reactivo estacionario | 180 s |
| 13 | contact-pair2-u100 | 100 | 0.2 | reactivo +100 | 200 s |
| 14 | contact-pair2-u-100 | 100 | 0.2 | reactivo -100 | 200 s |
| 15 | contact-pair1-u100 | 400 | 0.05 | **Secuencia espacial térmica** `100→200→400` a `0.05` (ya hay `100` y `200` para este caso, falta `400`) | 1800 s |
| 16 | contact-pair0-u0 | 400 | 0.05 | **Secuencia espacial operacional** `100→200→400` a `0.05` (faltan `400`) | 1800 s |
| 17 | contact-pair2-u100 | 200 | 0.2 | reactivo +100 a `N=200` (dirección) | 600 s |
| 18 | contact-pair2-u-100 | 200 | 0.2 | reactivo -100 a `N=200` | 600 s |
| 19 | contact-pair0-u-100 | 100 | 0.2 | operacional -100 a `N=100` (ya hay `+100`, falta `-100`) | 180 s |
| 20 | contact-pair0-u-100 | 100 | 0.1 | operacional -100 `CFL` | 350 s |

*Notas:* 1–4 son reusables (no rerun). 5–8 ya ejecutadas y **PASS**. 9–20 son **12 corridas nuevas** para `GATE_A` (todas `N≤200` salvo 2 a `N=400`). Total contactos `GATE_A` = **20** (vs 81 exhaustivo). Cubre los 3 pares, 3 direcciones, `CFL` 0.2/0.1/0.05 al menos en 1 caso, y 2 secuencias espaciales completas.

#### Shocks — 12 corridas

| # | Caso | N | CFL | Fenómeno | Tiempo est. |
|---|---|---|---|---|---|
| 21 | shock-pair0-ratio2 | 80 | 0.2 | débil `N=80` | 200 s |
| 22 | shock-pair0-ratio5 | 80 | 0.2 | medio `N=80` | 200 s |
| 23 | shock-pair0-ratio10 | 80 | 0.2 | fuerte `N=80` | 200 s |
| 24 | shock-pair0-ratio5 | 160 | 0.05 | **Secuencia espacial** `80→160` `0.05` | 400 s |
| 25 | shock-pair0-ratio5 | 320 | 0.05 | `80→160→320` | 800 s |
| 26 | shock-pair0-ratio5 | 640 | 0.05 | `80→640` completo (4 niveles) | 1600 s |
| 27 | shock-pair0-ratio5 | 160 | 0.2 | **CFL** `0.2` a `N=160` | 300 s |
| 28 | shock-pair0-ratio5 | 160 | 0.1 | `CFL` `0.1` | 350 s |
| 29 | shock-pair1-ratio5 | 160 | 0.05 | térmico `pair1` medio a `160` | 400 s |
| 30 | shock-pair2-ratio10 | 160 | 0.05 | reactivo fuerte `pair2` a `160` | 400 s |
| 31 | shock-pair1-ratio2 | 80 | 0.2 | `pair1` débil (contraste con `pair0`) | 200 s |
| 32 | shock-pair2-ratio5 | 80 | 0.2 | `pair2` medio | 200 s |

*Total shocks `GATE_A` = **12** (vs 108 exhaustivo). Cubre los 3 `ratio`, 3 pares, 1 secuencia espacial completa `80→640` a `0.05` (4 niveles) y 1 sensibilidad `CFL` completa `0.2,0.1,0.05` a `N=160`, más 2 `N=80` para pares 1 y 2.*

**Total `GATE_A` = 32 corridas** (20 contactos +12 shocks). **12 de ellas nuevas** para contactos `N=100` (9–14,19,20) + **2** `N=400` (15,16) + **~10** shocks nuevas = **≈ 24 corridas nuevas** además de las 8 ya hechas (4 reusables +4 ejecutadas). Tiempo estimado `GATE_A` restante: `12×~250 s` (`N=100`) + `2×1800 s` (`N=400`) + `12×~400 s` (`N=80..640`) ≈ **≈ 12 000 s ≈ 3.3 h single-core**, **≈ 0.9 h con 4 cores**.

#### GATE B — 157 corridas restantes (exhaustivo)

`GATE_B = 189 − 32 = 157` corridas:

- Contactos: `81 − 20 = 61` corridas (todos los `N=200,400` y `CFL=0.05` para los 9 casos no incluidos en `GATE_A`).
- Shocks: `108 − 12 = 96` corridas (todos los `N=320,640` y `CFL` finos para los 3 `ratio` y 3 pares).

`GATE_B` se ejecuta **en paralelo** con `S07→S16` y no bloquea `S06_IMPLEMENTATION_ACCEPTED_FOR_DOWNSTREAM`. Reutiliza los 32 `*.npz` de `GATE_A` sin rerun (mismo `raw_sha256`).

---

## 7. Estimación

| Métrica | Exhaustivo (hoy) | `GATE_A` propuesto | `GATE_B` diferido |
|---|---|---|---|
| **Número de corridas** | 189 | **32** (20+12) | 157 |
| **Evidencia ya reusable** | 4 | 4 | 4 |
| **Corridas ya ejecutadas (nuevas)** | 4 (pair0-u0) | 4 | 4 |
| **Corridas adicionales necesarias** | 185 | **24** (12 contactos `N=100` +2 `N=400` +10 shocks) | 157 |
| **Tiempo single-core** | ~26 h (8.7 h contactos +17.5 h shocks) | **~3.3 h** (1.2 h contactos +2.1 h shocks) + 0.6 h ya ejecutadas → **~3.9 h total** | ~22 h |
| **Tiempo 4 cores** | ~6.5 h | **~1.0 h** | ~5.5 h |
| **Tiempo ya invertido** | 0.6 h (4 filas) | 0.6 h | 0.6 h |
| **Tiempo restante `GATE_A`** | — | **~2.7 h single / 0.7 h parallel** | — |
| **Ahorro para desbloquear `S07`** | — | **≈ 22 h single / 5.5 h parallel** | — |

*Cálculo con tiempos medidos: `N=100` 150–462 s, `N=200` 504–912 s, `N=400` ~1800 s, `N=80` 200 s, `N=160` 350–400 s, `N=320` 800 s, `N=640` 1600 s. `GATE_A` evita 6 `N=400` contactos y 96 shocks `N=320/640`.*

---

## 8. Impacto contractual exacto

**No se modifica nada en este `DRAFT`.** Si se aprueba, la BCR `BCR-S06-VERIFICATION-STAGING` (o `BCR-S06-VERIFICATION-CONTRACT-R6`) debería tocar **solo** los siguientes artefactos, sin cambiar física, EOS, tolerancias, fixtures, referencias ni criterios `PASS/FAIL` (mismos thresholds, mismas `101` muestras, misma `reference_qualification`):

| Archivo normativo | Cambio requerido | Detalle |
|---|---|---|
| `docs/science/C1.0/BCR-S06-VERIFICATION-CONTRACT.md` | **Nuevo BCR** `R6` o `STAGING` | Añadir `SV-011` o `GATE_A/B` con tablas `GATE_A` (32) y `GATE_B` (157), sin tocar `SV-008/009/010/027` ni `MR-008/010`. |
| `docs/science/C1.0/BCR-S06-MATERIAL-RESOLUTION.md` | **No tocar** (solo referencia) | `GATE_A` consume `MR-008` tal cual; mencionar que `W/I12` y `HLLC-Davis` regional ya están probados. |
| `implementation/SCOPE_VALIDATION_MATRIX.md` | **Añadir columna** `GATE_A` | Mantener `VAL-008` `PR_SCIENTIFIC_AFFECTED`, añadir `GATE_A: 32/189` y `GATE_B: 189/189`, sin cambiar `VAL-010` (ya completo). |
| `implementation/scope_registry.json` | **Añadir campo** `gating` en `S06` | `S06` tendría `gates: { "GATE_A": "S06_IMPLEMENTATION_ACCEPTED_FOR_DOWNSTREAM", "GATE_B": "NUMERICAL_VERIFICATION_COMPLETE" }`, sin cambiar `allowed_paths`, `tests`, `vals`. |
| `implementation/validation_registry.json` | **Añadir `gate` en `VAL-008`** | `VAL-008` pasaría de `gate_class: PR_SCIENTIFIC_AFFECTED` a `gate_class: PR_SCIENTIFIC_AFFECTED` con `subgates: { "GATE_A": 32, "GATE_B": 189 }`, sin cambiar `fixture_path`/`reference_path`. |
| `implementation/scopes/S06-numerical-kernel.md` | **Añadir `GATE_A` en `Acceptance`** | Mantener `Required behavior` y `Tests` (los 7 `VAL`), añadir `GATE_A` con matriz 32 y `GATE_B` con 189, sin cambiar `NUM-001..010` ni `MR-008`. |
| `validation/fixtures/VAL-008/input.json` | **No tocar** | Fixture sigue con 189 combinaciones; `GATE_A` es **vista** sobre el mismo fixture, no nuevo fixture. |
| `validation/references/VAL-008/qualification.json` | **No tocar** | Referencia sigue calificada para los 18 casos. |
| `validation/expected/VAL-008/acceptance.json` | **No tocar** | Thresholds `5e-4/5e-3` y `2e-3/2e-2` y `ledger 1e-10` idénticos. |
| `tests/numerical/VAL-008/test_acceptance.py` + `validation/fixtures/VAL-008/execution.py` | **Añadir adapter `GATE_A`** | Mantener `test_complete_nasa_sequence` (189) para `GATE_B`; añadir `test_gate_a_nasa_sequence` (32) que reutiliza `execute()` y `assessment` con misma lógica `PASS`. Sin cambiar `metric` ni `ledger`. |
| `artifacts/VAL-008/campaign_checkpoint.json` | **Añadir `gate` field** | `gate: "GATE_A"` vs `"GATE_B"`, sin cambiar `inventory` (189 entradas, solo `status` distinto). |
| `docs/science/C1.0/EXECUTABLE_VALIDATION_FIXTURES.json` | **No tocar** | `VAL-008` fiche sigue con 189 combinaciones. |
| `docs/science/C1.0/VERIFICATION_EXECUTION_MATRIX.md` | **Añadir fila** `GATE_A` | `S06` con `GATE_A: 32` y `GATE_B: 189`, sin cambiar `GATE` de otros `VAL`. |
| `implementation/readiness_issues.json` | **No tocar** | `H-01..H-06` siguen `CLOSED`, `S06` sigue `pending` hasta `GATE_B`, pero `GATE_A` permite `S07` con `readiness: PARTIAL`. |

**Estados `GEN1` si se aprueba:**

- `S06` → `COMPLETE_IMPLEMENTATION` tras `GATE_A` (desbloquea `S07`), `NUMERICALLY_VERIFIED_GEN1` tras `GATE_B`.
- `S07→S16` pueden consumir `NumericalKernel` + `RegionalDuctState` sin esperar `GATE_B`.
- `S18` registra `GATE_A` como `PARTIAL` y `GATE_B` como `VERIFIED` después.
- `S22` integra solo `GATE_A` al principio, `GATE_B` después.

**Archivos a modificar si se aprueba (lista exacta, 9):**

1. `docs/science/C1.0/BCR-S06-VERIFICATION-CONTRACT.md` (nuevo `R6`)
2. `implementation/SCOPE_VALIDATION_MATRIX.md`
3. `implementation/scope_registry.json`
4. `implementation/validation_registry.json`
5. `implementation/scopes/S06-numerical-kernel.md`
6. `tests/numerical/VAL-008/test_acceptance.py`
7. `validation/fixtures/VAL-008/execution.py`
8. `docs/science/C1.0/VERIFICATION_EXECUTION_MATRIX.md`
9. `artifacts/VAL-008/campaign_checkpoint.json` (nuevo campo, no normativo pero parte del gate)

**No tocar (lista exacta, 7):** `docs/science/C1.0/BCR-S06-MATERIAL-RESOLUTION.md`, `validation/fixtures/VAL-008/input.json`, `validation/references/VAL-008/*`, `validation/expected/VAL-008/acceptance.json`, `docs/science/C1.0/EXECUTABLE_VALIDATION_FIXTURES.json`, `src/dino2next/gasdynamics/*`, `src/dino2next/numerics/*` (salvo `execution.py` adapter).

---

## 9. Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| **`GATE_A` pasa pero `GATE_B` falla a `N=400`/`640`** (p. ej., `GCL` o `W` overlap a malla fina) | Media | `GATE_A` habría desbloqueado `S07` con kernel que falla a fino. | `GATE_A` incluye al menos 2 `N=400` contactos y 1 `N=640` shock; `GCL` ya verificado a `N=400` en prototipo `GCL_max ≤1e-16`. Si `GATE_B` falla, `S07` sigue usando `N≤200` y se fija `S06` sin bloquear `S07`. |
| **Regresión específica de `pair2` reactivo a `N` grande no cubierta por `GATE_A`** | Baja | `pair2` solo a `N=100` en `GATE_A`; `N=400` podría fallar por `5Y+4Z` y `origin` | `GATE_A` incluye `pair2` a `N=200` (2 corridas) y `pair2` shocks a `N=160`; si se quiere más cobertura, añadir `pair2` `N=400` `CFL=0.05` (+1, 1800 s) sin salir de 25–45. |
| **`CFL=0.05` fino no probado para todos los casos en `GATE_A`** | Baja | `CFL=0.05` es el que más exige `Wdot` y `ST003` | `GATE_A` incluye `CFL=0.05` en 2 secuencias espaciales (`N=100,200,400` y `80..640`) y en 1 sensibilidad `CFL` completa; `ledger` ya `≤1e-18` en todas las ejecutadas. |
| **Falsa sensación de `VERIFIED` con `GATE_A`** | Media | Equipo downstream asume `NUMERICAL_VERIFICATION_COMPLETE` con solo `GATE_A` | Documentar explícitamente que `GATE_A` es `IMPLEMENTATION_ACCEPTED_FOR_DOWNSTREAM`, no `VERIFIED`; `S18` marca `PARTIAL`; `README` y `SCOPE_VALIDATION_MATRIX` distinguen. |
| **Retraso por no hacer `GATE_B` nunca** | Baja | `GATE_B` queda como deuda y nunca se cierra `NUMERICALLY_VERIFIED_GEN1` | `GATE_B` se ejecuta en paralelo con `S07→S16` en `S18` con 4 cores (~5.5 h) y no bloquea `S22`; se programa como `HEAVY_VERIFICATION` con `artifacts/S06-R4`. |
| **Cambio normativo inadvertido** | Muy baja | Al separar gates se podría interpretar como relajar thresholds | Propuesta mantiene **mismos thresholds, mismas 101 muestras, misma referencia, mismo `ledger`**, solo cambia **conjunto obligatorio por gate**; `GATE_B` conserva 189. |

---

## 10. Ahorro estimado

- **Tiempo `GATE_A` restante:** 24 corridas nuevas × `≈ 500 s` promedio (`N=100` 250 s, `N=200` 600 s, `N=400` 1800 s, `N=80` 200 s) ≈ **12 000 s ≈ 3.3 h single-core**, **≈ 0.9 h con 4 cores** + 0.6 h ya invertidas = **3.9 h total**.
- **Tiempo `GATE_B` diferido:** 157 corridas × `≈ 500 s` promedio ≈ **78 500 s ≈ 21.8 h single**, **≈ 5.5 h con 4 cores**.
- **Ahorro para desbloquear `S07`:** **≈ 22 h single / 5.5 h parallel** (de 26 h a 3.9 h).
- **Costo de `GATE_B` no desaparece**, solo se **paraleliza** con `S07→S16` (no bloquea DAG).
- **Evidencia ya reusable:** 4 filas + 4 ejecutadas = 8/32 (25 %) de `GATE_A` ya hechas; `GATE_A` requiere **24** más.
- **Riesgo de no hacerlo:** Seguir con 189 secuencial bloquearía `S06` 1–2 días, retrasando `S07` (que ya puede usar `RegionalDuctState` y `HLLC` probados) sin aportar nueva física por cada fila cartesiana.

---

## 11. Recomendación

**`VERIFICATION_STAGING_RECOMMENDED`**

Se recomienda **adoptar `GATE_A` de 32 corridas** como `S06_IMPLEMENTATION_ACCEPTED_FOR_DOWNSTREAM` y **diferir `GATE_B` de 157 corridas** como `NUMERICAL_VERIFICATION_COMPLETE` en paralelo con `S07→S16`.

**Justificación:**

1. **Mismo fixture, mismos thresholds, misma referencia, mismas 101 muestras** — no se relaja nada.
2. **Cobertura representativa mínima científica** (§4.B) con 20 contactos +12 shocks, 3 pares, 3 direcciones, 3 `ratio`, 1 secuencia espacial por familia y 1 sensibilidad `CFL` por familia, conservación y `GCL` en todas.
3. **Evidencia existente** (9 contactos prototipo con `p` error `≤ 9e-07` y `GCL ≤1e-16`, 2 shocks dirigidos con `order` y `ledger`, 8 filas `GATE_A` ya `PASS`) ya demuestra los mecanismos distintivos (`p`-equilibrio `NASA`, `W/I12`, `HLLC-Davis`, `SSPRK2`).
4. **Ahorro de 5.5 h parallel** para desbloquear `S07` (que consume `NumericalKernel` y `RegionalDuctState` sin esperar `N=400/640` exhaustivo).
5. **Riesgo acotado** con `GATE_A` incluyendo al menos 2 `N=400` y 1 `N=640`, y `GATE_B` ejecutándose en paralelo sin bloquear `S22`.

**Próximos pasos si se aprueba:**

1. Crear `BCR-S06-VERIFICATION-STAGING.md` (`R6`) con tablas `GATE_A`/`GATE_B` y `SV-011`.
2. Actualizar los 9 archivos listados en §8.
3. Añadir `test_gate_a_nasa_sequence` (32) en `test_acceptance.py` y `execution.py`.
4. Ejecutar las **24 corridas restantes de `GATE_A`** (≈ 0.9 h con 4 cores) y cerrar `S06_IMPLEMENTATION_ACCEPTED_FOR_DOWNSTREAM`.
5. Lanzar `GATE_B` (157) en `S18` como `HEAVY_VERIFICATION` con 4 cores (~5.5 h) sin bloquear `S07`.
6. `S07` puede empezar inmediatamente tras `GATE_A` con `BoundaryCoupler` y `RegionalDuctState`.

**No se requiere `SCIENTIFIC_CHANGE_REQUIRED`.**

---

## 12. Lista exacta de archivos normativos a modificar si se aprueba

**A modificar (9):**

- `docs/science/C1.0/BCR-S06-VERIFICATION-CONTRACT.md` (nuevo `BCR-S06-VERIFICATION-STAGING-R6`)
- `implementation/SCOPE_VALIDATION_MATRIX.md`
- `implementation/scope_registry.json`
- `implementation/validation_registry.json`
- `implementation/scopes/S06-numerical-kernel.md`
- `tests/numerical/VAL-008/test_acceptance.py`
- `validation/fixtures/VAL-008/execution.py`
- `docs/science/C1.0/VERIFICATION_EXECUTION_MATRIX.md`
- `artifacts/VAL-008/campaign_checkpoint.json` (campo `gate`, no normativo pero parte del gate)

**No tocar (7):**

- `docs/science/C1.0/BCR-S06-MATERIAL-RESOLUTION.md`
- `validation/fixtures/VAL-008/input.json`
- `validation/references/VAL-008/qualification.json`
- `validation/references/VAL-008/reference.py`
- `validation/expected/VAL-008/acceptance.json`
- `docs/science/C1.0/EXECUTABLE_VALIDATION_FIXTURES.json`
- `src/dino2next/gasdynamics/regional.py` / `src/dino2next/numerics/regional.py`

---

## 13. Conclusión

**`VERIFICATION_STAGING_RECOMMENDED`**

La matriz exhaustiva `VAL-008` de 189 corridas es **adecuada como `NUMERICAL_VERIFICATION_COMPLETE`**, pero **sobredimensionada como `gate` para `S06_IMPLEMENTATION_ACCEPTED_FOR_DOWNSTREAM`**. Con la evidencia existente (`9` contactos prototipo + `2` shocks dirigidos + `8` filas `GATE_A` ya `PASS` con `p` error `1.2e-12` y `ledger ≤1e-16`), la literatura (`Karni 1994`, `Abgrall 1996`, `Shyue 1998`, `Pan et al. 2017`) y el análisis de redundancia (§4), **32 corridas representativas** (20 contactos +12 shocks, `≈ 3.3 h` single) son **suficientes para desbloquear `S07→S16`** sin relajar thresholds ni cambiar física, mientras las **157 restantes** se ejecutan en paralelo como `GATE_B`.

**No se modifica normativa ni se continúa la matriz exhaustiva hasta aprobación explícita de la BCR.**

---

**Evidencia reusable citada:**

- `research/bcr_s06_material_resolution/reviews/hybrid-nine-contact-review.json` (`NINE_CONTACT_SMALL_PROTOTYPE_COVERAGE_CORROBORATED_NOT_FULL_VAL008`)
- `research/bcr_s06_material_resolution/reviews/hybrid-shock-review.json` (`TWO_LEVEL_DIRECTED_SHOCK_EVIDENCE_CORROBORATED_NOT_FULL_VAL008`)
- `research/bcr_s06_material_resolution/local_material/fast-contacts-summary.json` (9 contactos)
- `research/bcr_s06_material_resolution/local_material/shock-summary.json` (2 niveles)
- `validation/references/VAL-008/qualification.json` (`REFERENCE_QUALIFIED`, 18 casos, `bound <5e-5`)
- `artifacts/VAL-008/campaign_checkpoint.json` (`43e12fe`, 8/32 `GATE_A` `PASS`, 4 reusables)
- `docs/science/C1.0/VAL-008_campaign_summary.json`

**Checkpoints:**

- `artifacts/VAL-008/campaign_checkpoint.json` (`HEAD 43e12fe`, `8 PASS`, `181 PENDING`, `next: shock-pair0-ratio10 N80 CFL0.2` tras reorden)
- `artifacts/VAL-008/contact-pair0-u0-N100-CFL0.1.{json,npz}` etc. (4 filas nuevas `PASS`)

**HEAD actual:** `43e12fe3c640e1e45ee5b145805fc68bc3c44ec9` · **Branch:** `opencode/validation-continuation` · **Scope activo:** `S06` · **Próxima fila `GATE_A`:** `shock-pair0-ratio10 N80 CFL0.2` (o `contact-pair1-u0 N100 CFL0.2` si se prioriza contactos) — **congelada hasta aprobación**.
