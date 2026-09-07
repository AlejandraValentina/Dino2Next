# Método numérico adjudicado y gates pendientes

Versión: **C0.3-final-adjudication** · 2026-09-06

Estado: **SCIENTIFIC_BASELINE_NOT_READY**. C0.1 y C0.2 se conservan sin modificación. Este corpus adjudica cláusulas, pero no autoriza arquitectura ni producción. SELECTED no significa validación experimental ejecutada.

## Estado del algoritmo

**SPEC_NOT_EXECUTABLE** por C03-BLK-001/002/003. Se seleccionan flux, reconstrucción, geometría y forma de integración; no se confunde esa adjudicación con una campaña de coupling terminada. No hay elecciones de flux dejadas a Codex. Las cláusulas pendientes son gates de investigación, no tareas de producción.

## NUM-001 — estado y finite volume SELECTED

Estado de celda Qi=(1/Δx)∫A U dx, con U de PHY-004, cinco masas químicas y tags separados. Abar=(1/Δx)∫A dx exacta para geometría tabulada por tramos. Recuperar ρ, v, Y y resolver u(T,Y) con formación. No formar presión con un γ fijo. Estados de volúmenes PHY-003, no duplicar volumen almacenado en puertos. Float64; sumas globales compensadas. Momentum sólo en1D. Fuente geométrica física y fuerza sobre paredes explícitas en ledger.

## NUM-002 — tiempo SELECTED

SSPRK2 explícito no partido para todo RHS cuando esté definido: Q1=Qn+dt L(tn,Qn); Qn+1=(Qn+Q1+dt L(tn+dt,Q1))/2. Misma etapa en0D,1D,fuentes y flujos de interfaz. Intercambios integrados dt(F0+F1)/2 compartidos con signos opuestos. No actualizar reservorio con flujo del tubo a otro tiempo. Lie rechazado por orden1; Strang no elegido porque introduce secuencia adicional sin ventaja demostrada para este núcleo. La comparación lineal no certifica fuentes no lineales (C03-BLK-002).

## NUM-003 — flujo interior SELECTED

HLLC con estimaciones Davis SL=min(vL−cL,vR−cR), SR=max(vL+cL,vR+cR), c según EOS congelada. S*=[pR−pL+ρLvL(SL−vL)−ρRvR(SR−vR)]/[ρL(SL−vL)−ρR(SR−vR)]. Para lado k: ρ*k=ρk(Sk−vk)/(Sk−S*), E*k=Ek+(S*−vk)[S*+pk/(ρk(Sk−vk))]; Uk*=(ρ*,ρ*S*,ρ*E*,ρ*Yk). F*=Fk+Sk(U*k−Uk). Elegir FL si SL≥0; F*L si SL<0≤S*; F*R si S*<0<SR; FR si SR≤0. Masa de especies y tags lleva los mismos estados donor estrella. No usar otra EOS para star recovery. Casos degenerados/estados inadmisibles requieren NUM-006.

Se selecciona conservación estricta sobre double-flux de energía no conservativa. No se exige presión a precisión de máquina en contacto térmico advectado: error medido y refinamiento son obligatorios. HLLC estacionario sí preserva contacto a roundoff en la suite. Este resultado no prueba shocks multiespecie extremos.

## NUM-004 — reconstrucción y geometría SELECTED

MUSCL sobre (p,v,T,Y1…Y4), Y5=1−Σ1..4Y, tags con última fracción derivada. MC(a,b)=minmod((a+b)/2,2a,2b), con a,b diferencias vecinas en malla uniforme. GEN1 usa malla uniforme por segmento; salto de Δx sólo en interfaz de segmentos físicamente conformes y requiere fixture adicional antes de uso, no implementación libre. En cara izquierda/derecha extrapolar ±s/2; derivar ρ por EOS. Un único factor λ∈[0,1] por celda reduce todas las pendientes si una cara sale del simplex de especies/tags o límites p,T; no renormalizar Y cara por cara. λ máximo admisible para restricciones lineales; no se inventa masa ni energía.

Fcara_total=Aface F_HLLC. Source geométrico Si,mom=pi(Ai+1/2−Ai−1/2)/Δx. Es segundo orden para área suave y p representada al centro, y preserva p uniforme,v=0 con A exacta. No promesa de preservar toda solución estacionaria exactamente. Conos continuos por tramos: vértice en cara, integrar cada tramo; salto abrupto no admitido sin ley física. Datos ghost de fixture nozzle deben evaluarse en **cada** centro ghost; repetir una constante en dos posiciones originaba orden1 en C0.2.

## NUM-005 — fuentes y paso combinado, selección parcial

RHS sin splitting incluye calor, shear, geometría, balances de zonas, reacción y trabajo móvil. La forma dt=min(dtCFL,dtfuentes,dtacoplamiento,dtreacción,dtevento) es seleccionada; **coeficientes de las restricciones fuente/coupling no certificados** en C03-BLK-002, no defaults implementables. dtCFL=0.3 min(Δx/(|v|+c)) seleccionado para el núcleo probado. dtevento es distancia temporal exacta hasta siguiente apertura/cierre, SOC, burn-end o múltiplo2π. Reacción no cruza límites de reactantes ni evento. Una condición no puede atravesar Tdomain mediante recorte posterior. El requisito de producir fórmula min completa no se declara satisfecho.

## NUM-006 — admisibilidad, obligación seleccionada / algoritmo pendiente

Prohibidos clipping de presión, densidad, temperatura, especies y reposición de energía. Rechazar toda etapa global si cualquier estado no satisface dominio EOS, masas no negativas, sumas o solver de interfaz. Reintento debe ser global y conservar un único flujo por cara; no corregir un extremo de una interfaz solamente. Falta certificar orden de fallback HLLC→Rusanov/primer orden, límites de reintentos y restricción fuente sin ocultar falla (C03-BLK-002). Los benchmarks C03 no implementan tal política y no son modelo de código listo para copiar. La validez de HLLC interior no constituye teorema de positividad para NASA.

## NUM-007 — acoplamiento

Un único flujo integrado de masa, energía total y especies/tags en cada interfaz; copia opuesta al donor/receptor. Cilindro usa mismo V(t),Vdot(t) en trabajo y EOS. En zonas se resuelven ecuaciones acopladas de presión común PHY-003. **Bloqueado:** estados causales del puerto (C03-BLK-001) y campaña completa de pasos/eventos/depleción (C03-BLK-002). No reemplazar estas condiciones por un orificio con presión de primera celda.

## NUM-008 — bordes/eventos

Topología PHY-004 fija, GENERAL_JUNCTION OPTIONAL_FUTURE. Pared cerrada exige vnormal=0 y reflexión; condición ambiente física de PHY-004, con número correcto de características entrantes. Semántica física elegida no es aún implementación causal validada. Eventos con ángulo desenrollado; cada evento se aplica una sola vez. Merge de zonas conserva U,mk; apertura no introduce masa semilla. No suavizar área/eventos para que converja. Datos de entrada fuera de mapa producen error explícito.

## NUM-009 — periodicidad, parte seleccionada

Comparar estados en mismo θ=0 mod2π tras todos los eventos del borde de ciclo: inventarios0D, estados de todas las celdas, especies y tags físicos normalizados por cohorte equivalente; no comparar IDs históricos crecientes. Observar además trazas interpoladas conservativamente a la misma grilla angular. Comparar diferencias de periodo1 y periodos2…8; si k>1 cumple y1 no, MULTIPERIODIC_UNSUPPORTED. Warm/cold convergentes a soluciones distintas se reportan como ramas, no se promedian. Máximo de ciclos, número consecutivo y umbral definitivo requieren C03-BLK-003: no se selecciona un 1e−5 sin sensibilidad de outputs. Convergencia de ciclo no demuestra resolución espacial ni validez experimental.

## NUM-010 — refinamiento y diagnósticos SELECTED

Refinar malla por2, al menos tres niveles, y tiempo por2 con malla fija. Para separación temporal usar referencia del mismo operador espacial con integrador independiente; para error físico espacial usar solución exacta/promedio de celda con integración controlada. Orden smooth requerido ≥1.8 en los dos últimos pares; contactos discontinuos usan reducción L1 y umbrales propios, no orden2 impuesto. Estado homogéneo quieto debe cerrar momentum geométrico. Reportar masa, energía con formación, elementos y especies; química es PHYSICAL_SOURCE en especies pero no fuente adicional de energía; shear es fuente de momentum, no pérdida externa de energía total. Reportar número/causa de reintentos, minρ/minT/minY, errores de raíz y cambio de dominio.

Residual global RQ=Qfin−Qini−Σtransfer_externo−Σsource_físico. Escala SQ=Σdominios|Qini|+∫Σ|flujo_externo|dt+∫Σ|source|dt+Qref; masa Qref=ρamb Vtotal; energía Qref=ρamb Vtotal cv,air Tref, Tref=350K; momentum Qref=ρamb Vtotal camb. Para species usar escala masa total, no dividir por especie ausente. Formación y sentido de signos preservados. Trazadores incluyen ledger separado de relabel, que no cambia masa química. Una suma global buena no reemplaza balance de cada interfaz.
