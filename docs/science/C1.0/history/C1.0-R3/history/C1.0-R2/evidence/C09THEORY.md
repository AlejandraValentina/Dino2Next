**C0.9-port-loss-identification**

Fecha: 2026-09-06. `RESEARCH_ONLY_NON_PRODUCTION`.

# Adjudicación de identificabilidad

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
