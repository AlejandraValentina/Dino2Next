# GATE_A Auditoría y Normalización — 2026-09-11

## Resumen ejecutivo

- **Artefactos existentes con 101 muestras** (`contact-pair1-u0-N100-CFL0.2`, `contact-pair1-u100-N100-CFL0.2`, `contact-pair1-u-100-N100-CFL0.1`) tenían `.json` y `.npz` pero no `-assessment.json`. No se rerunearon numerics; se ejecutó **assessment exclusivamente desde artifacts**.
- **GATE_A_VERIFIED_COUNT = 11/32** (4 `PASS_REUSABLE` válidos + 7 `PASS` con assessment final). Antes 8/32 reportado; ahora 11/32 tras recuperar 3 assessments.
- **Almacenamiento checkpoints insostenible** (6.5 MB + 333.6 MB + 27 MB = 367 MB por fila contact con checkpoint) normalizado a 17.2 MB (95% reducción) vía `gzip` streaming con equivalencia auditable por hash.
- **Runner atómico** `validation/fixtures/VAL-008/gate_a_runner.py` garantiza `RUN → RAW → ASSESSMENT → PASS/FAIL → CHECKPOINT` sin marcar PASS antes de assessment, con HEAD worktree-aware, exit code real y logs persistentes.

---

## 1. Auditoría de filas GATE_A

Matriz GATE_A: 32 filas (20 contactos +12 shocks) según `validation/fixtures/VAL-008/gate_a_matrix.json`.

| Stem | .json | .npz | -assessment.json antes | Acción |
|---|---|---|---|---|
| `contact-pair1-u0-N100-CFL0.2` | ✅ 942 KB, 101 métricas | ✅ 142 KB, 101 samples | ❌ | Assessment generado (PASS) |
| `contact-pair1-u100-N100-CFL0.2` | ✅ 650 KB | ✅ 106 KB | ❌ | Assessment generado (PASS) |
| `contact-pair1-u-100-N100-CFL0.1` | ✅ 1261 KB | ✅ 112 KB | ❌ | Assessment generado (PASS) |
| `contact-pair0-u0-N100-CFL0.1` etc. (4) | ✅ | ✅ | ✅ | Ya PASS |

**Criterio assessment** (sin rerun, desde `validation/fixtures/VAL-008/execution.py` y `validation/expected/VAL-008/acceptance.json`):
- `max_L1[p] + ref_bound[p]` con `nextafter` ≤ `thr_L1` (5e-4 operacional, 2e-3 thermal)
- `max_Linf[p] + ref_bound[p]` ≤ `thr_Linf` (5e-3 / 2e-2)
- `ledger_max ≤ 1e-10`
- 101 samples, `raw_sha256` y `commit` enlazados.

Resultados (ej. `pair1-u0`): `max_L1 1.41e-12 + 2.84e-12 → 4.26e-12 ≪ 2e-3`, `ledger 2.74e-15 <1e-10` ⇒ **PASS**. Idem otros dos.

Tras generar assessments, `campaign_checkpoint_gate_a.json` actualizado a **11/32 PASS, 21 PENDING**.

---

## 2. Normalización de checkpoints

### 2.1 Duplicación

- `checkpoint.json` (6.5 MB) duplica `output` (101 estados Regional) ya en `.npz`+`metrics`.
- `steps.jsonl` (333 MB, 874 steps) repite `face_integrals` ya agregados en `regional_ledger_samples` (101 samples).
- `trials.jsonl` (27 MB, 596 retries) duplica diagnósticos ya resumidos en `regional_rejected_trials`.

Contrato exige: `input versionado`, `raw time series`, `hashes`, `mesh/dt`, `all retries`, `ledgers`, `metrics/order`, `PASS/FAIL`. No exige conservar 333 MB de pasos aceptados para filas PASS.

### 2.2 Solución sin pérdida contractual

Para cada fila PASS con checkpoint:
1. Calcular `sha256(original)` y verificar contra `raw_json.regional_*_audit_sha256`.
2. Comprimir streaming `gzip -6` (sin RAM masiva).
3. Verificar `sha256(gzip -dc) == original_sha`; sólo entonces borrar original y conservar `.gz`.
4. `manifest.json` documenta `original_sha`, `compressed_size` y nota de equivalencia.

**Resultado `contact-pair1-u100-N100-CFL0.2`:**
- `checkpoint.json` 6.5 MB → 0.46 MB (7.1%)
- `steps.jsonl` 333.6 MB → 15.66 MB (4.7%)
- `trials.jsonl` 27 MB → 1.07 MB (4.0%)
- **Total 367 MB → 17.2 MB (-95%)**, verificable vía `gzip -dc | sha256sum`.

Equivalencia auditable: cualquiera puede `gzip -dc steps.jsonl.gz | sha256sum` y comparar con `artifacts/VAL-008/<stem>.json:regional_step_audit_sha256`.

Detalle completo en `artifacts/VAL-008/CHECKPOINT_STORAGE_AUDIT.md` y `artifacts/VAL-008/checkpoints/<stem>-checkpoint.manifest.json`.

### 2.3 Runner futuro

`gate_a_runner.py:normalize_checkpoint_storage()` aplica la misma compresión automáticamente tras cada PASS, evitando que futuras filas N=400 produzcan 300 MB descomprimidos permanentes.

---

## 3. Runner atómico GATE_A

**Ubicación:** `validation/fixtures/VAL-008/gate_a_runner.py`

```
RUN (execute) → ARTIFACT RAW (.json/.npz 101) → ASSESSMENT (-assessment.json) → PASS/FAIL → CHECKPOINT UPDATE (atómico)
```

**Garantías:**

- **No PASS antes de assessment:** assessment lee `.json` existente, valida 101 samples, calcula `max_L1/ledger` vs thresholds, escribe `-assessment.json` atómico; sólo después actualiza `campaign_checkpoint_gate_a.json`/`campaign_checkpoint.json`/`campaign_summary.json` con `status=PASS/FAIL`. Si raw existe sin assessment, no rerunea numerics.
- **HEAD worktree WSL:** `_get_head()` / `_get_commit()` resuelven `git rev-parse HEAD` y, en worktree (`E:/dino2/Dino2Next/.git/worktrees/dino3`), leen `commondir` y `refs/heads/...` sin mangling WSL (`/mnt/e/...`) en win32. Probado: `b418efe2726ef…`.
- **Exit code real:** `run_pending()` retorna 0 OK, 1 FAIL, 2 error; `__main__` hace `sys.exit(code)`; no se oculta tras `|| true`.
- **Logs persistentes:** por fila `artifacts/VAL-008/logs/<stem>.log` en append con `flush` + `fsync`, nunca tras `tail`. Mensajes también a stdout para CI, pero el archivo persiste.
- **Escritura atómica checkpoint:** `tmp + fsync + os.replace` con fallback Windows (`unlink` + `replace` o escritura directa).

Uso:

```sh
py validation/fixtures/VAL-008/gate_a_runner.py --batch 1   # siguiente PENDING
py validation/fixtures/VAL-008/gate_a_runner.py --all       # todos los PENDING
py validation/fixtures/VAL-008/gate_a_runner.py --batch 0   # sólo reporta GATE_A_VERIFIED_COUNT
```

**Próxima fila PENDING real:** `contact-pair2-u0-N100-CFL0.2` (thermal reactive stationary), luego `pair2 ±100`, etc. (21 totales).

---

## 4. Correcciones adicionales

- `validation/fixtures/VAL-008/execution.py:27-78` (`_get_commit`) reescrito para worktree sin `"/mnt/..."` en win32.
- `artifacts/VAL-008/campaign_checkpoint_gate_a.json` enriquecido con `max_L1/max_Linf/ledger_max/raw_sha256/elapsed` para las 3 filas recuperadas (antes sólo `elapsed`).
- `campaign_summary.json` actualizado a `11/32` y `next_row_GATE_A`.

---

## 5. Conteo contractual final

- **PASS_REUSABLE válidos:** 4
  - `contact-pair0-u0 100 0.2`
  - `contact-pair0-u100 100 0.2`
  - `contact-pair1-u100 200 0.1`
  - `contact-pair1-u-100 100 0.2`
- **PASS con assessment:** 7
  - `contact-pair0-u0 100 0.1`, `100 0.05`, `200 0.2`, `200 0.1`
  - `contact-pair1-u0 100 0.2`
  - `contact-pair1-u100 100 0.2`
  - `contact-pair1-u-100 100 0.1`
- **GATE_A_VERIFIED_COUNT = 11/32**
- **PENDING reales:** 21 (incl. `pair2` 3, `pair1 400`, `pair2 200`, `pair0 -100`, `shocks 12`).
- Verificación: `py validation/fixtures/VAL-008/gate_a_runner.py --batch 0` ⇒ `GATE_A 11/32 PASS, 21 PENDING`.

---

## 6. Evidencia

- `artifacts/VAL-008/contact-pair1-*-assessment.json` (3 nuevos, no rerun)
- `artifacts/VAL-008/campaign_checkpoint_gate_a.json` (11/32)
- `artifacts/VAL-008/checkpoints/*.gz` + `*.manifest.json` (17 MB)
- `artifacts/VAL-008/CHECKPOINT_STORAGE_AUDIT.md` (análisis detallado)
- `validation/fixtures/VAL-008/gate_a_runner.py` (pipeline atómico)
- `validation/fixtures/VAL-008/execution.py` (HEAD fix)

Antes de continuar nuevas filas, el runner ya deja `RUN→ARTIFACT→ASSESSMENT→PASS/FAIL→CHECKPOINT` atómico y no marca PASS antes de assessment.

