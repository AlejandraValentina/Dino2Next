**C0.9-port-loss-identification**

Fecha: 2026-09-06. `RESEARCH_ONLY_NON_PRODUCTION`.

# Adenda experimental: datos de identificación de pérdida del puerto

**APPROVED. OI-09 permanece CLOSED_CAMPAIGN_CONTRACT.**

Motivo: C08 demostró no identificabilidad Cd-only; C09 identifica NP añadiendo presión estática a la entrada de Ωwindow. El observable adicional se agrega a la caracterización del componente, no se reutiliza como validación independiente.

| Conjunto | Uso permitido | Separación |
|---|---|---|
| COMPONENT_CALIBRATION_DATA | Cd, p_window_in y demás observables que identifican λ | No valida independientemente λ en esos puntos |
| ENGINE_CALIBRATION_DATA | Ajustes restantes del motor autorizados | No consume held-out |
| ENGINE_VALIDATION_DATA | Comparación independiente de outputs del motor | Condiciones no usadas en calibración correspondiente |
| HELD_OUT_PREDICTIVE_DATA | Evaluación final de predictividad | No modifica modelo ni parámetros |

Para NP: añadir toma estática x=.02 m; registrar sensor, ubicación/volumen de cavidad, frecuencia de respuesta, calibración, sincronización, incertidumbre y covarianza con pexit/p0. El ensayo sintético usa σp=100 Pa; no se afirma que ese sensor ya exista ni que esa cifra sea una incertidumbre experimental real.

La toma se mide en las mismas condiciones de Cd y no desplaza estaciones existentes. Un shock que atraviese una toma cambia el operador físico de medida; su tratamiento y anchura temporal deben registrarse, no ocultarse por promediado.

Impacto contractual: PHY-005 distingue ley W2 de caracterización; NUM-007/008 consumen λ identificado; validación de componente conserva parámetros/observables de identificación; GEN1 debe rechazar datos insuficientes. Los oráculos numéricos siguen siendo independientes de los datos de calibración.

No cambiar combustible, scavenging, térmica, legacy o topología. No afirmar validación experimental ejecutada. Adquirir datos reales permanece REQUIRED_ENGINE_DATA_NOT_YET_ACQUIRED y no es por sí solo blocker científico de baseline.
