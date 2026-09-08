# MR-010 — propuesta de adjudicación de precisión por resolución

Estado: **PROPUESTA PARA REVISIÓN INDEPENDIENTE; NO ADJUDICADA**.
Autor: `/root/bcr_science_review`. La revisión de sus contribuciones corresponde
a un revisor distinto. Este archivo no modifica C1.0-R4 ni anticipa aprobación
de R5, VAL-010, S06 o GEN1. No cambia la representación material de MR-008.

## Decisión acotada propuesta

Asignar la precisión final de la reflexión acústica libre de VAL-010 a
N=1600, CFL=0.1 y 0.05, ejecutando epsilon=1e-5 y 5e-6 por separado. Conservar
N=200/400/800 y sus tres CFL originales como obligaciones de estabilidad,
conservación, estudio espacial y sensibilidad temporal, con todos sus errores
publicados. La tabla siguiente sustituiría explícitamente la asignación de
umbrales por resolución del extremo libre; no cambia el método de transporte,
la frontera, la EOS, el integrador ni el caso rígido.

Se conservan sin modificación: los operadores w+/w-/presión total y C_h, A0,
el 1% absoluto y relativo, el presupuesto de fase pi/N, las máscaras definidas
exclusivamente por la referencia, las colas, las 101 muestras y ambos epsilon.
La precisión se atribuye a esas filas concretas, no a cualquier malla o CFL.

## Evidencia que permite proponer la decisión

La reducción independiente precedió al nuevo nivel del kernel. Después se
completaron **cuatro ejecuciones reales**, con ambas amplitudes y ambos CFL;
el revisor independiente corroboró las 101 observaciones y los ledgers de las
cuatro, sin muestras fallidas ni retries. No se sustituyó una amplitud por la
hipótesis de linealidad del kernel completo.

| N | CFL | epsilon | Máx. error absoluto/A0, cota | Máx. amplitud relativa, cota | Máx. fase, cota (rad) | Tiempo wall del proceso |
|---|---|---|---|---|---|---|
| 1600 | .05 | 1e-5 | .000543844053 | .006444409279 | .000341245946 | 35:47.35 |
| 1600 | .05 | 5e-6 | .000509558291 | .006405639852 | .000329318346 | 34:53.43 |
| 1600 | .1 | 1e-5 | .000550871273 | .006543710258 | .000337062605 | 20:47.55 |
| 1600 | .1 | 5e-6 | .000516517372 | .006506035074 | .000316662529 | 22:04.45 |

Los límites comparados son .01, .01 y pi/1600=.00196349540849. Las cotas incluyen
incertidumbre de referencia; no se resta error numérico, resto no lineal ni
diferencia entre amplitudes. El ledger fue corroborado mediante una cota
conservadora más estricta que ST-003: se omitió su throughput positivo del
denominador, manteniendo inventario inicial absoluto y Qref. No se presenta
esa cota como una reconstrucción exacta del denominador original.

La diferencia máxima de coeficiente al cambiar CFL .1→.05, dividida por A0,
es 7.02818e-6 para presión total con epsilon=1e-5 y 6.95908e-6 con epsilon=5e-6;
también se conservaron las diferencias incidentes/reflejadas. Esto mide
sensibilidad temporal. Dos dt no demuestran orden temporal ni certifican el
error en el límite dt→0. Ambas filas satisfacen por sí mismas los umbrales.

Las revisiones y datos portables están vinculados en
[kernel_review/summary.json](kernel_review/summary.json), las cuatro revisiones
individuales y
[kernel_review/resolution-and-cost-scope-review.json](kernel_review/resolution-and-cost-scope-review.json).
El commit registrado fue eadf7ba1f1f3208076347e38ecaac056f2e8755b; el árbol
equivalente publicado se vincula al HEAD 2d04c16fc77b603596f7db04a8ed7d35953afa17
mediante [execution-tree-binding.json](kernel_review/execution-tree-binding.json).
Los archivos realmente consumidos, incluido el driver de almacenamiento que
no se afirma tracked en ese commit, tienen hashes individuales en
[execution-source-pins.json](kernel_review/execution-source-pins.json).

Esta evidencia no demuestra necesidad de cambiar el transporte para satisfacer
**este observable, caso y resolución**. Tampoco demuestra precisión universal
del transporte, aceptación del coste de un motor completo o suficiencia de las
mallas originales. No se propone otra reconstrucción, flux o integrador aquí.

## Texto exacto propuesto para SV-010/free

En `docs/science/C1.0/BCR-S06-VERIFICATION-CONTRACT.md`, sección SV-010, conservar
las definiciones y derivaciones del operador, A0, incertidumbre y máscara.
Sustituir el párrafo que empieza «All101 original samples j=0..100» por:

> All 101 original samples j=0..100, ct=j/100, remain mandatory at every row of
> the MR-010 resolution-obligation table, for epsilon=1e-5 and epsilon=5e-6
> executed separately. Evaluate and retain each directional component and
> total-pressure complex error at every sample, including sample75 and every
> tiny-signal tail. At each FINAL_PRECISION row require
> |C_candidate-C_reference|/A0<=.01 for all three signals at all samples.
> STUDY rows retain the same error measurements and threshold comparisons;
> their required acceptance conditions are stability, conservation and the
> declared convergence/sensitivity study, not a claim of final precision.
> No measured remainder is subtracted. At FINAL_PRECISION rows this absolute
> complex gate covers zero-reference instants as well as all weaker tails.

En el párrafo de la máscara, sustituir únicamente el fragmento que exige
amplitud/fase «at the original mesh/CFL assessment levels» por:

> On this reference-qualified mask require relative amplitude error<=.01 and
> abs(arg(C_candidate*conj(C_reference)))<=pi/N for each directional component
> at every FINAL_PRECISION row of the MR-010 table. Evaluate and retain those
> same comparisons at STUDY rows without relabeling a failed precision
> comparison as PASS. The mask is qualified and frozen independently at every
> mesh before candidate execution, including N1600; it is never copied from
> another mesh without qualification. The qualified N1600 mask retains
> incident j=0..83 and reflected j=67..100 for both epsilon values.

Conservar las reglas de candidato cero, fase indefinida y etiqueta
`NOT_ASSESSED_BELOW_DECLARED_ABSOLUTE_RESOLUTION`. Fuera de la máscara no se
declara fase PASS. En particular, la presión total de referencia que se anula
en j75 conserva control absoluto, nunca una división por su coeficiente cero.

Añadir como norma la tabla y obligaciones siguientes. «Reporte» exige publicar
valor, incertidumbre y comparación con el límite original; no significa PASS.
Cada fila comprende ambos epsilon y las 101 muestras.

| N | CFL | Tipo | Estabilidad y conservación | Estudio obligatorio | Precisión absoluta | Precisión relativa | Fase |
|---|---|---|---|---|---|---|---|
| 200 | .2 | STUDY | Obligatorio | Sensibilidad temporal | Reporte | Reporte en máscara | Reporte en máscara |
| 200 | .1 | STUDY | Obligatorio | Sensibilidad temporal | Reporte | Reporte en máscara | Reporte en máscara |
| 200 | .05 | STUDY | Obligatorio | Secuencia espacial | Reporte | Reporte en máscara | Reporte en máscara |
| 400 | .2 | STUDY | Obligatorio | Sensibilidad temporal | Reporte | Reporte en máscara | Reporte en máscara |
| 400 | .1 | STUDY | Obligatorio | Sensibilidad temporal | Reporte | Reporte en máscara | Reporte en máscara |
| 400 | .05 | STUDY | Obligatorio | Secuencia espacial | Reporte | Reporte en máscara | Reporte en máscara |
| 800 | .2 | STUDY | Obligatorio | Sensibilidad temporal | Reporte | Reporte en máscara | Reporte en máscara |
| 800 | .1 | STUDY | Obligatorio | Sensibilidad temporal | Reporte | Reporte en máscara | Reporte en máscara |
| 800 | .05 | STUDY | Obligatorio | Secuencia espacial | Reporte | Reporte en máscara | Reporte en máscara |
| 1600 | .1 | FINAL_PRECISION | Obligatorio | Comparación temporal a N fijo | <=.01 A0, tres señales | <=.01 en máscara | <=pi/1600 en máscara |
| 1600 | .05 | FINAL_PRECISION | Obligatorio | Extremo espacial y comparación temporal | <=.01 A0, tres señales | <=.01 en máscara | <=pi/1600 en máscara |

Estabilidad significa completar la evolución y todas las muestras con estados
admisibles, conservando reintentos/rechazos y su significado vigente. Una
ejecución interrumpida no pasa. Conservación mantiene los ledgers y umbrales
vigentes; una gráfica o coeficiente estable no los sustituye.

Para cada epsilon, en CFL=.05 la secuencia N200→400→800→1600 debe mostrar
descenso estricto del máximo temporal del error complejo absoluto/A0 de cada
señal: incidente, reflejada y presión total. Comparar las cotas de referencia:
la cota superior del error fino debe ser menor que la cota inferior del grueso.
Si las cotas se solapan, no se ha demostrado ese descenso. Publicar las tres
razones log2, los L1/L2 de campos y sus órdenes observados. No imponer ni
atribuir un nuevo orden global dos a partir de la ecuación modificada local.

La obligación temporal compara, para cada epsilon, las trazas de coeficientes
de CFL .1 y .05 a N1600 y publica sus diferencias normalizadas y márgenes de
los tres gates; ambas filas deben cumplir precisión por separado. En las
mallas de estudio se conservan también las diferencias entre sus tres CFL.
No se infiere orden temporal ni una cota al límite dt=0 de dos pasos; esa
afirmación más fuerte requeriría evidencia y obligación adicionales explícitas.

## Cambios coordinados, interfaces y reutilización

- Ficha VAL-010 en `EXECUTABLE_VALIDATION_FIXTURES.json` y catálogo generado:
  modificar sólo `mesh_sequence`, `dt_sequence`, `metric`, `threshold` y la
  descripción de cobertura de referencia/free para expresar la tabla. Mantener
  inicialización, dominio, fronteras, tiempos, operadores y amplitudes. El caso
  rígido conserva íntegramente su matriz y su precisión L1 en N800.
- Fixture/adaptador VAL-010 de S06: versionar la tabla por fila, ejecutar todas
  sus obligaciones y separar resultado de estudio, comparaciones de precisión
  y resultado histórico R4. Persistir todos los errores, máscaras, incertidumbre,
  retries, identidades y costes. No deducir un PASS global de las cuatro filas
  finas ni modificar otros VAL para acomodar esta decisión.
- Referencia VAL-010: incorporar N1600 al coverage/validador y su certificado
  portable con hashes del generador, fuentes, catálogo y artefactos correctos.
  Conservar los certificados históricos. Recalificar el artefacto que se
  publique si cambian sus fuentes o bindings; no actualizar un hash para
  disimular una calificación obsoleta. Las fórmulas Gaussianas no cambian.
- Scopes: S06 recibe la obligación de verificación. La trazabilidad de S18 y
  la verificación integrada de S22 deben reflejar la resolución y cobertura
  real; no se cambian por ello los contratos físicos de sus consumidores,
  almacenamiento S05, API o flujo de frontend. S16 no recibe una regla CFL
  global nueva: la tabla pertenece a este caso de verificación.

Las cuatro ejecuciones son evidencia para esta adjudicación y para exactamente
las obligaciones verificadas. Su reutilización en aceptación posterior exige
identidad demostrada de fuentes consumidas, inputs, referencia, representación
del estado, ruta aritmética y operadores de evaluación, con vinculación al
árbol aceptado. No bastan el mismo nombre de test, el mismo número de PASS o
un commit sin los pins efectivos. Un cambio material/híbrido, de recuperación,
transferencia, integrador o evaluación que afecte esa ruta obliga a verificar
de nuevo lo afectado; estas ejecuciones no aprueban automáticamente ese cambio.

Los FAIL R4 de N200/N400/N800, incluidos los cuatro fallos finos anteriores,
permanecen FAIL R4 con sus métricas y fuentes en `historical/`. Esta es una
modificación explícita de obligaciones futuras, no la eliminación retroactiva
de una obligación para cambiar la etiqueta de una fila. La secuencia espacial
completa y la batería rígida siguen pendientes de demostrar para la aceptación
integrada correspondiente; la presente evidencia no las completa.

## Coste y límite de la calificación

Los tiempos medidos son aproximadamente **20–36 minutos por tránsito acústico
canónico**, sobre t=1/sqrt(1.4) s físico, con cuatro procesos inicialmente
concurrentes. Son tiempos de proceso medidos por GNU time en ese entorno, no
benchmarks aislados ni una predicción del tiempo de un ciclo 2T. Los detalles
de CPU, memoria y etiquetas de tiempo están en la revisión de coste citada.

Se propone aceptar una resolución de verificación para este observable con
esa limitación de coste expresamente retenida. No se inventa presupuesto, SLA,
hardware objetivo ni exigencia de tiempo real. La practicidad de GEN1 necesita
un benchmark posterior con modelo representativo, horizonte físico, ductos,
menor celda, acoplamiento material y hardware declarados, junto con un presupuesto
de coste explícito antes de afirmar que lo satisface. Ese benchmark sigue como
obligación/límite de integración; no se da por cumplido ni se transforma su
ausencia en permiso para relajar el 1%.

La decisión propuesta habilita precisión asociada a resolución; no certifica
practicidad del motor completo, validación experimental o validación predictiva.
Debe revisarse y adjudicarse independientemente antes de cualquier edición
normativa R5. Las fuentes y resultados congelados de esta investigación no
se modifican mediante este texto.
