# OI-09 — contrato de campaña experimental

Versión: **C0.2-blocker-resolution** · Fecha: **2026-09-06**.
Estado del expediente: **SCIENTIFIC_BASELINE_NOT_READY**. Evidencia de selección; no especificación de producción. C0.1-review se conserva sin modificación.

## OI-09_RESOLUTION

**Estado: CLOSED — EXPERIMENTAL_CAMPAIGN_CONTRACT_READY.** Cierre del plan y de su procedimiento de decisión, **no disponibilidad garantizada de hardware/datos, ni validación ejecutada**. OI-01–08 conservan sus bloqueos científicos; no se autoriza operar fuera de una especificación de combustible/topología finalmente adjudicada. Afecta VAL-DEC-005, VAL-017–020/022–026 y OUT-012.

## Candidatos y decisión de adquisición

| Candidato | Compatibilidad y evidencia accesible | Datos todavía faltantes | Disposición |
|---|---|---|---|
| Yamaha MT-110 S, tesis Zhang1995 | Monocilíndrico atmosférico loop/piston-port; B52mm,S50mm,l101mm; presiones y banco descritos | Archivos crudos, geometría exhaust exacta por corrida, composición combustible, covarianzas y partición independiente | Primera opción de recuperación y, si se consigue unidad, nueva campaña |
| Motor SI2T gasolina/CNG de Fontanesi et al.2012 | Investigación primaria de combustión/scavenging | Paquete reproducible/licencia/raw y compatibilidad completa no verificados | Candidato secundario de datos, no aceptado como fixture |
| 2T supercharged/poppet/GDI o opposed-piston | Puede tener buenas medidas | Topología ajena a familia GEN1 | No usar como sustituto del motor loop/piston-port |
| Nueva bancada sobre unidad piston-port compatible | Permite medir inputs y reservar condiciones de verdad | Requiere adquirir unidad e instrumentar | Fallback seleccionado |

La cilindrada geométrica del Yamaha resulta≈106.19cm³ de B/S; el valor nominal de tabla100cc no debe sustituir πB²S/4. CR5.8 publicado requiere verificar si es geométrico o efectivo; EPO104°ATDC, TPO128°ATDC, IPO62°BTDC son puntos de inspección, no geometría digitalizada suficiente. No copiar curvas de potencia de configuración desconocida.

## Contrato de campaña EX-01: admisión del hardware

Aceptar una unidad sólo si es SI, atmosférica, piston-port, cárter compresor, loop-scavenged, escape sin regulación móvil y accesible a instrumentación. Registrar número de serie/configuración, desmontaje dimensional antes/después y fotografías; adquirir contornos3D/2D de puertos, alturas, anchuras, puentes, radios, count, áreas descubiertas versus ángulo, volúmenescámara/cárter en varios ángulos, B/S/l y geometría íntegra del escape/intake/transfer por estaciones con incertidumbre. No inferir geometría faltante ajustando torque. Identificar lubricación y auxiliares de bancada.

Si se obtiene MT-110 S, comenzar dentro del intervalo históricamente ensayado2200–4400rpm sujeto a límites reales del hardware y bancada. Fallback: definir Nmin/Nmax por documentación técnica y ensayo de admisión motored seguro; se registra antes de capturar datos de ajuste. El diseño usa coordenada r=(N−Nmin)/(Nmax−Nmin), no un motor inventado.

## EX-02: matriz y partición inmutable

Para una configuración base de escape, definir cargas mediante throttle efectivo25/50/75/100 % de apertura geométrica verificada, además de registrar presión de admisión/masa; no llamar carga a porcentaje de torque desconocido. Velocidades r=0,.125,.25,.375,.5,.625,.75,.875,1. Mezcla: tres niveles en el dominio **ya congelado** de combustible/φ, definidos por tercios del intervalo operativo admitido. Antes de capturar fired, la hoja de setpoints contiene N,apertura,φ,ignición y temperaturas objetivo numéricos, unidades y hash. La sustitución de hardware o dominio obliga a regenerar la hoja antes de usar datos.

- CALIBRATION_DATA: r=0,.25,.5,.75,1 con aperturas25/75/100 y mezcla central; mapas Cd/termales/mecánicos se obtienen en campañas de subsistema identificadas.
- VALIDATION_DATA: r=.125,.375,.625,.875 con aperturas25/75/100 y mezcla central, sin ajuste de parámetros después de revelar datos.
- HELD_OUT_PREDICTIVE_DATA: apertura50 % a todas las r; extremos de mezcla en r=.25,.5,.75; además segundo escape con cambio conocido de longitud del header de+10 % dentro de límites de hardware. Ese10 % es intervención de diseño del experimento, no tolerancia científica.

Custodio conserva hashes y bloquea revelación de held-out hasta versión de modelo/calibración cerrada. Si se usa un punto para seleccionar modelo, pasa a CALIBRATION_DATA y debe obtenerse reserva nueva. Si una condición no es operable, registrar fallo y dominio excluido antes de usar sus outputs para ajustar; no reemplazar selectivamente un error. Tres sesiones independientes por condición, con orden aleatorizado por bloques térmicos; inicialmente200 ciclos consecutivos por sesión. Ampliar adquisición mediante regla previa hasta que error estándar de la media estabilice o se alcance límite documentado de bancada; no descartar ciclos salvo fallo instrumental trazable.

### Campaña arrastrada y de subsistemas

Antes de los datos fired, adquirir motored sin combustible en las nueve velocidades r de EX-02 y aperturas25/50/75/100 %, con dos estados térmicos de pared/lubricación medidos (frío estabilizado de bancada y caliente estabilizado sin combustión). Registrar su valor numérico; no usar temperatura nominal. Mismo número inicial de ciclos/sesiones y reglas de partición por r. Comparar Wc,Wcc, presiones y balance térmico; no transferir automáticamente fricción motored a fired. Una fuente externa de calor/motor eléctrico pertenece a la frontera de bancada y se mide. Los mapas de puertos requieren ambas direcciones y apertura, desde razón de presión cercana1 hasta cubrir la envolvente del ensayo real; fuera de cobertura se rechaza, no se extrapola. La bancada debe documentar estaciones y reducción Cd compatibles con OI-03 antes de adjudicar mapa.

## EX-03: operadores de medición y archivos requeridos

| Observable | Operador sobre simulación | Medición / metadatos indispensables |
|---|---|---|
| Presión cilindro | p0D(θ) frente a media ensemble a fase geométrica; no p local3D predicha | Sensor flush, posición, sensibilidad/drift/pegging, encoder, TDC motored independiente, ciclos individuales |
| Presión escape/transfer | p(xsensor,θ) convolucionada con respuesta de transductor/línea | Coordenada exacta, volumen de cavidad, ancho de banda, filtro analógico/digital, fase |
| Wc/Wcc/IMEP | Integración con V(θ) medida, mismo criterio angular | Cárter y cilindro sincronizados; covarianza presión/geometría/TDC |
| Brake torque/power | Torque medio al plano real del dinamómetro; P=2πNT/60 | Célula/torquímetro y brazo si aplica, calibración antes/después, pérdidas de acoplamiento, auxiliares; no corrección normativa tácita |
| Caudal de aire/fuel | Media temporal del plano e inventario medidos | Sensor/calibración, reversibilidad o depósito amortiguador caracterizado, combustible por masa y temperatura |
| Temperatura | Operador de sensor con inercia/radiación/conducción según ubicación | Termopar, ubicación/profundidad, diámetro, Tw por superficie; no comparar Tgas instantánea a lectura lenta sin modelo |
| Scavenging/trapping | Misma cohorte y ventana que el closure final | Trazador calibrado o muestreo rápido de cilindro y escape; blanco, recuperación, retardo, balance de trazador |
| Calor de pared | Calor integrado / flujo local según sensor | Calorimetría por dominio y/o sensores de flujo térmico calibrados; no deducir h sólo ajustando p |

Frecuencia de adquisición fijada por ancho de banda observado en ensayo instrumental, con antialiasing y sobremuestreo; rejilla angular inicial0.1°CA y ensayo0.05°CA para verificar sesgo de integración. Registrar señal cruda en tiempo y encoder, no únicamente promedios remuestreados. Fuentes de presión absoluta/TDC no se ajustan a posteriori para mejorar coincidencia del modelo.

## EX-04: incertidumbre y aceptación ejecutable

Cada observable y condición lleva vector de entradas medibles z, certificados, distribuciones y matriz de covarianza Cz. TipoA: dispersión entre ciclos/sesiones, con autocorrelación y tamaño efectivo. TipoB: calibración, resolución, drift, posición, TDC, geometría, filtros y perturbación por instrumentación. Propagar Cy=J Cz Jᵀ; usar Monte Carlo con distribuciones registradas cuando no linealidad/pegging/trazador lo requiera. No combinar todo como independiente sin evidencia. Referencia metodológica JCGM; no se inventan incertidumbres medidas.

Presupuesto por observable:

- p(θ): sensibilidad/offset/drift, repetibilidad, respuesta dinámica, error angular mediante dp/dθ·uθ y covarianza común del ciclo.
- W=Σpi ΔVi: términos de presión, B/S/l/Vclear, TDC, cuadratura y correlaciones; uW²=gᵀ C g.
- Tbrake: escala/offset/histéresis, brazo y g si balanza, vibración y repetibilidad; P incluye N y cov(N,T).
- ṁfuel/aire: calibración, tiempo, densidad cuando sea volumétrico, drift y amortiguador/retorno.
- Temperaturas: calibración, posición, radiación/conducción, dinámica y repetibilidad; no confundir sesgo con ruido.
- ηtr/ηsc: calibración/recuperación de trazador, muestreo, masas de referencia y covarianza de cocientes.

**Regla fijada de aceptación de consistencia experimental:** para cada observable escalar, comparar residuo d=ysim−yobs con intervalo combinado95 %, que incluye incertidumbre experimental, propagación de inputs y error numérico estimado por refinamiento. Parámetros ya congelados; **no incluir una incertidumbre de modelo ajustada para ensanchar aceptación**. Para vectores de presión usar dᵀ C⁺d y grados de libertad=rank(C), con covarianza estimable y distribución verificada; si la hipótesis gaussiana no es adecuada, construir distribución del estadístico por Monte Carlo antes de abrir reserva. Familia de comparaciones por campaña con control Holm α=.05. No rechazo estadístico se informa como compatibilidad dentro de incertidumbre, no equivalencia comercial ni exactitud universal.

**Gate contra incertidumbre inútil:** antes de la campaña de validación, medir la resolución de las variaciones que se pretende predecir. Para cada contraste de condición de calibración, exigir intervalo expandido de su diferencia menor que un tercio de la variación física medida que se pretende discriminar. Si la variación es indistinguible de0, ese contraste no acredita sensibilidad predictiva y se registra no informativo; no amplía claims. El factor3 es requisito de capacidad metrológica de este contrato, no ley física ni porcentaje heredado. Determinar valores instrumentales en EX-01/03 antes de revelar reserva; fallar el gate obliga a mejorar medida o reducir el claim, no ajustar la tolerancia sobre held-out.

## EX-05: entregables y decisión

Obligatorios: geometría y hashes; input efectivo por corrida; datos crudos/certificados; mapasCd con reducción compatible; fuel/composición/lubricación; presupuesto y operadores; partición firmada; scripts de reducción versionados; estados del simulador/refinamiento; resultados pass/fail/no-informativo por observable y dominio. Publicación de una curva no sustituye ninguno de éstos. La ejecución debe presupuestarse y conseguirse posteriormente; este encargo no contactó autores ni adquirió hardware.

**Riesgos residuales:** acceso/coste, sensores que perturban ports, química/heat/scavenging aún abiertos. Si el modelo final requiere nuevos estados medidos, ampliar protocolo antes de capturar/revelar reserva mediante BCR. La falta de una medición ejecutada no reabre por sí sola el contrato de campaña, pero impide afirmar validación científica/predictiva.

Fuentes: [NR14: Zhang (1995), tesis experimental de motor 2T](https://vuir.vu.edu.au/18232/1/ZHANG_1995compressed.pdf); [NR16: Fontanesi et al. (2012), gasolina/CNG en motor SI2T](https://www.researchgate.net/publication/320434187_Investigation_of_Scavenging_Combustion_and_Knock_in_a_Two-Stroke_SI_Engine_Operated_with_Gasoline_and_CNG/fulltext/5e59bfb04585152ce8f8523c/Investigation-of-Scavenging-Combustion-and-Knock-in-a-Two-Stroke-SI-Engine-Operated-with-Gasoline-and-CNG.pdf); [NR15: JCGM, guías de metrología](https://www.bipm.org/en/committees/jc/jcgm/publications). La matriz, partición y reglas EX-01–05 son decisiones explícitas del presente expediente, no resultados publicados por esas fuentes.
