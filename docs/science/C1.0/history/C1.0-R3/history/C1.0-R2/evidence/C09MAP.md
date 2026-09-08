**C0.9-port-loss-identification**

Fecha: 2026-09-06. `RESEARCH_ONLY_NON_PRODUCTION`.

# Generación del mapa físico de pérdida

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
