**C0.9-port-loss-identification**

Fecha: 2026-09-06. `RESEARCH_ONLY_NON_PRODUCTION`.

# Evaluación runtime — sin inversión de Cd

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
