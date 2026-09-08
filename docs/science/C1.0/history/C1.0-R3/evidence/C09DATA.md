**C0.9-port-loss-identification**

Fecha: 2026-09-06. `RESEARCH_ONLY_NON_PRODUCTION`.

# PORT_LOSS_CHARACTERIZATION_CONTRACT

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
