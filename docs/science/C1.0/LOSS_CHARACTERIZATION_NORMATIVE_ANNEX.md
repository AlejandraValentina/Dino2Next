> **Normative — C1.0-R1** · Status: `SCIENTIFIC_IMPLEMENTATION_BASELINE_FROZEN`
> Revision: `NORMATIVE_COMPLETENESS_REVISION`; scientific decisions changed: NO. This restoration does not assert all specification gaps are closed.

# Restored loss characterization policy

Sources: C09THEORY, C09MAP, C09RUNTIME and C09DATA; current C1 retains offline characterization, no runtime inversion. Their statements of pending numerical gates do not undo later selections.

## LC-001 — sector and certificate
Source: C09THEORY.

Adjudicación de identificabilidad

**SELECTED:** el modelo identifica λ sólo donde las observaciones lo identifican; en los restantes sectores requiere observables suficientes o rechaza la caracterización. La exigencia anterior de unicidad universal Cd→λ queda **SUPERSEDED**. No se reabre T3 ni W2; Cd/Cd0 no se redefine.

Sea G(θ,z) el problema estacionario T3+W2 y su operador de observación, donde θ contiene λ y, sólo si son realmente desconocidos independientes, estados internos no eliminados por los balances. z contiene geometría y Ωwindow fijas, estaciones, apertura, dirección, fluidos, presiones/temperaturas con su tipo, condiciones de borde, cierres de fondo y procedimiento de preparación. La historia del banco no se reemplaza por una selección arbitraria de ramas.

El conjunto factible es ΘD={θ físicamente admisible: G(θ,z) compatible con datos e incertidumbre}. La identificabilidad nominal y la incertidumbre de la estimación son propiedades diferentes.

| Estado | Criterio |
|---|---|
| CD_ONLY_IDENTIFIABLE | Una única λ nominal en todo el dominio admisible certificado |
| CD_ONLY_LOCALLY_IDENTIFIABLE | Raíz única en una vecindad declarada; no se infiere unicidad global |
| CD_ONLY_NONIDENTIFIABLE | Varias λ nominales, incluyendo un intervalo continuo, producen el mismo caudal |
| CD_ONLY_ILL_CONDITIONED | Única λ nominal, pero su conjunto de incertidumbre excede la resolución de caracterización declarada |
| NO_PASSIVE_SOLUTION | No existe λ≥0 compatible con datos/incertidumbre y modelo |

La resolución requerida de caracterización es un input explícito del protocolo de banco, con unidad de λ y presupuesto sobre observables. No es una tolerancia elegida por un root solver. En el ensayo NP se usa presión auxiliar con σ=100 Pa; los errores de referencia deben ser menores que su contribución a la identificación. Una exigencia más estricta requiere instrumentación/precisión adecuadas, no regularización del parámetro.

## Jacobiano

J=∂O/∂θ. Debe escalarse por unidades/escala de parámetros y por covarianza de observación: Jw=ΣO^(−1/2) J Dθ. Registrar rango, singular values, error estimado del Jacobiano y sensibilidad absoluta. Se calcula J con secuencias de perturbación h,h/2,h/4 y se contrasta el resultado con derivadas analíticas donde existan. Un singular value comparable con el error de J no certifica rango.

En un problema con un único parámetro, un Jacobiano no nulo tiene condition number=1 aunque su sensibilidad absoluta sea minúscula. Por tanto ese número aislado no certifica identificabilidad práctica. En NP, Jmdot,λ=0 en la meseta; Jpwindow,λ es no nulo. La presión y h0 finales no añaden rango.

Si se parametriza también posición de choque, deben incluirse las ecuaciones de cierre estacionario al eliminar estados internos. No se cuenta el choque como parámetro libre cuando pexit y los balances ya lo determinan. En el límite de choque de intensidad cero, su coordenada deja de ser una variable observable útil: esto no hace no identificable a λ si el observable de la región W2 sigue siendo sensible.

## Prueba local NP

Con G=ṁ/Ap y h(T)+u²/2=h0, p(u)=GRT(u)/u tiene derivada negativa. Para un tramo W2 uniforme subsónico,

λ=∫[ua,ub] 2[RT−u²(1−R/cp)]/u³ du.

El integrando es positivo cuando M<1. A pexit y G fijos, ub está fijada; ua disminuye al aumentar p_window_in. Por tanto dλ/dp_window_in>0 en el dominio admisible. Se obtiene una inversa única sin seleccionar un extremo de la antigua meseta.

La prueba corresponde al NP y a esa región uniforme subsónica. No se afirma que una sola presión identifique toda geometría posible. Si el conjunto auxiliar contratado no proporciona rango y unicidad, el caracterizador rechaza el dataset. La ausencia del dato real se clasifica ENGINE_INPUT_DATA_NOT_AVAILABLE, nunca SCIENTIFIC_MODEL_UNDEFINED.


## LC-002 — map generation and interpolation
Source: C09MAP.

Generación del mapa físico de pérdida

## Selección GEN1

**HYBRID: caracterización offline + evaluación y guardrails online.** La simulación no resuelve Cd→λ en cada timestep. Offline conserva Cd0 y los datos de bancada; runtime consume un producto identificado λ_loss con provenance. No se utiliza continuidad de una raíz anterior como regularización.

ONLINE_INVERSION queda REJECTED para GEN1: confunde condiciones de bancada con estados transitorios y reintroduce la ambigüedad de capacidad. OFFLINE sin guardrails es insuficiente para controlar cobertura. HYBRID separa inversión, incertidumbre y coste de identificación de la evolución temporal conservativa T3.

## Producto obligatorio

Por nodo: λ≥0, unidad adimensional; intervalo/covarianza de incertidumbre; clasificación de identificabilidad; conjunto de observables usados; residual con escala física; Jacobiano escalado/singular values y su error; método de identificación; condiciones y dominio; referencias a puntos Cd originales y datos auxiliares; hashes de geometría, EOS, cierres y protocolo.

Por mapa: active_axes y su justificación, regiones admisibles, máscaras de no identificación, discontinuidades/topología, método de interpolación, error de interpolación calificado con puntos de caracterización independientes de sus vértices. No llamar validación física a esos controles de interpolación.

Dirección es categórica: nunca interpolar entre forward y reverse. Opening puede ser eje continuo; Π sólo si sus datos identifican una dependencia. Un eje constante necesita dominio declarado y evidencia de que omitirlo mantiene el error dentro del presupuesto del componente. No introducir Re, Mach, composición o temperatura como dimensiones ajustables sin datos que las identifiquen. Estos valores siguen siendo metadatos/domain guards aun cuando no sean ejes.

## Inversión offline

Usar todos los observables contratados y sus covarianzas, conservando ecuaciones de estado, balances y admisibilidad. Verificar el conjunto de raíces factibles; una raíz encontrada no constituye certificado global. Si sólo existe identificación local, el producto registra vecindad y condiciones suficientes para permanecer en ella. No elegir minimum λ, maximum λ, λ=0 o una raíz próxima a un valor previo.

Criterio de parada algebraica: el error proyectado a cada observable debe ser inferior al presupuesto numérico de la caracterización; éste se registra separado de incertidumbre de medición. La incompatibilidad de datos no se reduce a un nominal best effort. λ negativo está fuera del dominio físico.

## Interpolación seleccionada

Lineal en un eje; bilineal en celdas rectangulares opening–Π cuando ambos ejes están activos. Los pesos son no negativos y suman uno; con nodos admisibles esto preserva λ≥0. No extrapolar. No atravesar celdas con nodos no identificados o fronteras de régimen/topología sin calificación explícita de la celda. Una frontera de choking no implica por sí sola discontinuidad, pero no se interpola a través de ella sólo porque los vértices existan.

La varianza nodal interpolada es wᵀΣλw, manteniendo covarianza; añadir por separado el error de interpolación estimado con nodos de comprobación. Sin covarianza, usar una cota conservadora explícita, no asumir independencia. No promediar una familia no identificable para fabricar un vértice.

NP produce un punto caracterizado; no se lo convierte en un mapa general de motor. El ensayo transitorio de intensidad material fija prueba una hipótesis sintética definida por el fixture, no extrapolación validada de hardware real.

## Identidad temporal del parámetro

El mapa es persistente. Una propagación de incertidumbre muestrea un mapa coherente por realización y conserva correlaciones entre nodos; no sortea una λ nueva en cada stage. Se registra seed y realización. La corrida nominal usa el mismo producto determinista durante toda su evolución.


## LC-003 — runtime semantics
Source: C09RUNTIME.

Evaluación runtime — sin inversión de Cd

1. Verificar hashes e identidad de geometría, Ωwindow, w, EOS/cierres y producto de caracterización.
2. Verificar T,p,Y, apertura, régimen y demás dominios declarados del mapa. Usar las mismas estaciones y tipos de presión/temperatura. No reemplazar una presión total por presión estática de primera celda.
3. Evaluar los ejes activos y dirección; interpolar sólo dentro de una celda calificada. Devolver λ e incertidumbre/provenance, nunca resolver una raíz Cd-only online.
4. Aplicar Sm=−λ w Aρu|u|/2, SE=SY=Sτ=0 a cada stage. λ nunca modifica Aphysical ni el volumen. El source se opone al movimiento local; si existen flujos locales de sentidos opuestos, cada evaluación usa el mapa direccional correspondiente y sus guards.
5. En u=0 exacto el source es cero; no se necesita elegir un donor ni una λ para producir ese source nulo. En u≠0, por pequeño que sea, rigen todos los guards. No se inventa un valor en un hueco del mapa.

## Coordenadas de observación

Los estados virtuales de las estaciones se obtienen de sus ubicaciones físicas en T3/volúmenes, con el operador de muestreo especificado. Para estación TOTAL en gas ideal con composición congelada, invertir h(T0,Y)=h(T,Y)+u²/2 y conservar s para obtener p0; fallar si excede el dominio termodinámico. Para STATIC usar p,T locales. Π conserva exactamente el cociente del contrato de medición y su dirección, incluso si una inercia transitoria lo lleva fuera del rango de bancada.

No usar abs, min/max ni una inversión de estaciones para forzar Π dentro de un mapa de descarga. Un mapa que no cubra una inversión inercial debe rechazarse o caracterizarse en el dominio dinámico correspondiente antes de usarlo. Que un motor necesite esos datos no autoriza extrapolación silenciosa.

## Errores obligatorios

LOSS_CHARACTERIZATION_INSUFFICIENT; LOSS_PARAMETER_NONIDENTIFIABLE; LOSS_PARAMETER_ILL_CONDITIONED; AUXILIARY_MEASUREMENT_REQUIRED; LOSS_INVERSION_NO_ROOT (offline); LOSS_DATA_OUT_OF_DOMAIN; EOS_OUT_OF_DOMAIN; INADMISSIBLE_WINDOW_STATE. Cada error registra punto, estaciones, composición, ejes y certificado faltante. No devolver best effort.

## Clasificación epistemológica

Falta de medición de un hardware: ENGINE_INPUT_DATA_NOT_AVAILABLE. Falta de identificación del dataset: LOSS_PARAMETER_NONIDENTIFIABLE. Error de una implementación/discretización al reproducir el problema caracterizado: NUMERICAL_VERIFICATION_FAILURE. No confundirlos ni transferir un fallo numérico a Cd o W2.

No se modifican las reglas aún pendientes de dt combinado, recuperación ni periodicidad; pertenecen a los gates posteriores. Clipping sigue REJECTED. Este contrato de evaluación no es arquitectura de software.


## LC-004 — hardware characterization data
Source: C09DATA.

PORT_LOSS_CHARACTERIZATION_CONTRACT

## Hardware y estaciones — obligatorios

Identificador/version/hash de hardware; longitud física [m]; Aphysical(x,θ) [m²] y perímetro [m]; volumen físico [m³]; cinemática y función Aopen(θ) [m²]; Ωwindow y w normalizada [m⁻¹]; regiones de pérdidas de fondo separadas para impedir doble contabilización.

Para cada estación: coordenada física [m], orientación, presión STATIC/TOTAL [Pa], temperatura STATIC/TOTAL [K], sensor/operador de medida, área de referencia [m²], multiplicidad y definición exacta de Π. Cd permanece como valor de bancada adimensional. Registrar flujo con signo [kg/s], dirección y protocolo steady/transient con historia de preparación.

## Mínimo por sector

1. Sector Cd-only identificado: Cd, p/T de reducción, composición, geometría, opening, Π, dirección, incertidumbre conjunta y certificado de unicidad/admisibilidad.
2. Sector NP no identificable: todo lo anterior **más p_window_in estática a x=.02 m**. Es el MINIMUM_IDENTIFYING_OBSERVABLE_SET demostrado para NP. No añadir pexit o h0 como supuesta información nueva: ya forman parte del problema.
3. Si ese conjunto no identifica otra geometría/régimen: AUXILIARY_MEASUREMENT_REQUIRED o LOSS_PARAMETER_NONIDENTIFIABLE. No se inventa un segundo sensor ni un regularizador durante engine simulation. Una caracterización extendida debe declarar sus observables, operador, rango e incertidumbre y demostrar identificabilidad antes de producir un mapa admisible.

## Provenance

Banco, fecha, operador/procedimiento, instrumentación, certificados de calibración de sensores, posiciones/tolerancia de montaje, sincronización y promediado, condiciones de fluido/T, composición y humedad cuando apliquen, covarianzas, datos brutos y hashes. Conservar los puntos fuente Cd sin renombrar Crel como Cd ni sobrescribir mediciones.

El rango Reynolds/Mach se registra si fue caracterizado. No se agrega un eje Re/Mach a una tabla sólo por disponibilidad del valor derivado. Un parámetro no identificado no puede declararse preciso por disponer de un nominal.

## Datos reales pendientes

REQUIRED_ENGINE_DATA_NOT_YET_ACQUIRED es un estado de disponibilidad. Si el dataset no satisface este contrato, el motor no puede correr con un parámetro inventado. Esto no reabre OI-09 ni vuelve indefinida a W2. La campaña de caracterización de componente es distinta de la validación del motor.

## Cerrado, reversante y fuera de rango

La caracterización debe cubrir las aperturas y sentidos que se utilizarán, incluyendo el comportamiento de la región de pérdida cuando la ventana está cerrada pero conserva gas en movimiento. No se asigna λ(0)=0 por falta de descarga estacionaria. Una curva de descarga puede ser insuficiente allí; si no existe caracterización dinámica o una ley de material caracterizada que cubra el estado, se rechaza la entrada. No se borra inventario ni se reinicializa el pasaje para evitar ese dato.


## LC-005 — interpretation of certificate inputs
C09 explicitly assigns required parameter resolution and observation-error budget to the characterization protocol. These are measured/protocol inputs with units and provenance, not a universal condition-number cutoff chosen by Codex. A missing declared resolution or a singular value not distinguishable from Jacobian error cannot certify a node. Direction remains categorical; only the selected linear/bilinear cells are allowed. No axis normalization changing that interpolant, extrapolation or nearest-node fallback is authorized. Cell qualification and covariance are required before engine use.

