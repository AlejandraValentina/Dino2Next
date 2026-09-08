# MR-008 — propuesta acotada de representación material interior 1D

Estado: **PROPUESTA NO ADJUDICADA; AREA-02 ABIERTO**.
Autor: `/root/bcr_science_review`. Requiere revisión independiente de sus
contribuciones antes de modificar normativa. Este documento selecciona una
propuesta concreta para el interior de S06; no aprueba ahora su receta completa,
congela la transferencia pendiente, acepta S06 ni declara capacidad GEN1.

## Decisión propuesta y correspondencia física

Representar explícitamente los intervalos materiales declarados dentro del
ducto. Una región puede contener la mezcla de cinco especies y los cuatro
inventarios de origen; su identidad material no es una especie ni un trazador.
Conservar la EOS NASA, sus datos, formación química, dominios e inversión TI
aceptados. Recuperar cada región desde sus propios inventarios y volumen.
Nunca corregir energía/composición para imponer presión ni usar EOS del promedio
conservado de una celda mixta como sustituto de su presión física.

[Pan et al. (2017), sección 2.3](https://arxiv.org/html/1704.00519v1) aporta el
punto de partida publicado: balances conservativos por volumen material y
transferencia de presión/trabajo en interfaces. La adaptación propuesta es
1D, con inventario Dino2Next I12 y NASA; no adopta sus level sets, tratamiento
multidimensional, correcciones de conservación ni eliminación de escalas.
La partición local, el remap y el acoplamiento al kernel detallados aquí son
adaptaciones revisables, no una atribución de sus pruebas al artículo.

En el operador inviscido químicamente congelado, una superficie material se
mueve con el contacto y no tiene difusión de masa a través de ella. Esto no
añade inmiscibilidad, tensión superficial ni una ley que prohíba mezcla física
futura. Una región inicialmente homogénea sigue siendo una mezcla gaseosa.
Preservar p/u uniformes es una propiedad verificada del contacto, no una
condición impuesta donde existen ondas físicas.

## Estado autoritativo y observables

Para geometría estática conocida, definir W(x)=integral(x_ref,x,A(s)ds), en m³.
El estado autoritativo inmutable contiene identidad de geometría/malla base,
W de las caras ordenadas, inventarios extensos I12 por intervalo, identidades
materiales ordenadas e identidad de recuperación/clasificación física. I12
conserva el orden rho, momentum, energía total, cinco especies y cuatro orígenes,
integrados físicamente sobre el intervalo. V_r=W_right-W_left y U_r=I_r/V_r.
Los x físicos se derivan de W mediante la inversión geométrica calificada;
no son una segunda geometría editable. Se conservan brackets, residuos y la
convención explícita de extremos ya revisada, sin modificar W para ocultarlos.

Propiedad de celdas base, fracciones y solapamientos son productos derivados.
La proyección conservativa es la suma de inventarios intersectados dividida
por dx de la celda base, conservando el significado A*U del Q existente.
No se mantienen dos copias editables de masa/energía. Reinicios incluyen W,
I12, orden, identidades materiales y geometría; Q proyectado solo es insuficiente.

Los productos públicos se distinguen explícitamente:

- `regional_states`: estados NASA de cada I12/V, con temperaturas regionales.
- `conservative_projection` e inventario total compensado: cantidades conservadas.
- `pressure_volume_average`: integral(A*p) sobre solapamientos dividida por
  integral(A). Una media de longitud, si se requiere, se nombra separadamente.
- Velocidad bulk y fracciones químicas/de origen proyectadas: cocientes de
  inventarios, por tanto ponderados por masa. No se intercambian con medias
  volumétricas de velocidad o composición. No se publica un ambiguo conjunto
  `primitive_average` que aparente ser un estado EOS homogéneo.

En VAL-008 con A=1, la presión física coincide con su media de longitud. Otros
fixtures conservan su ponderación declarada. Un diagnóstico EOS(Q proyectado),
si se expone, se identifica como homogéneo y no alimenta presión física,
fuentes ni condiciones de interfaz de la ruta regional.

## Receta interior propuesta

**Inicialización.** Se requieren intervalos físicos declarados o un reinicio
regional completo. Datos exclusivamente Q conservan interpretación homogénea;
no permiten reconstruir una historia subcelda única. Composición suave usa
la ruta espacial suave sin crear un contacto por cada salto de discretización,
especie o ID de origen. Seleccionar ruta por representación física del estado,
nunca por nombre de VAL, constantes del caso, posición futura del oráculo o
un atajo gamma/NASA.

**Partición local.** Retener todas las fronteras materiales y los extremos
físicos. Entre pasos completos, excluir caras ordinarias de la malla base
cuya distancia al contacto sea menor que .35*dx_base_min. Se aglomera así la
pieza geométricamente pequeña con material contiguo de la misma región; no se
elimina el contacto. Los contactos reales que delimitan una lámina material
fina permanecen ambos, aunque impongan dt pequeño. No se fusionan regiones
distintas ni se borra masa pequeña por conveniencia.

**Remap.** Repartir cada donante mediante solapamientos dentro de la misma
región; conservar orden y transferencia compartida. La regla de primer orden
propuesta es I_donante por la fracción de volumen representado solapado; el
último receptor recibe el resto conservado del donante. Recuperar y validar
todos los receptores antes de aceptar. No corregir presión tras el remap ni
restar su error de los resultados. La consistencia de esos volúmenes con W
autoritativo está bloqueada por AREA-02: esta regla no queda congelada hasta
el cierre específico descrito más abajo. El barrido monotónico optimiza solo
la búsqueda de intersecciones, con equivalencia exacta ya revisada; no cambia
la regla de reparto.

**Parche y bulk.** Las fronteras materiales y los intervalos que no coinciden
con una celda base ordinaria siembran el parche. Añadir cuatro celdas de
distancia de stencil a ambos lados. En los tramos ordinarios restantes,
llamar la reconstrucción y los fluxes del kernel aceptado sin alterarlos,
con cuatro ghosts de estados regionales reales. Dentro del parche se propone
la representación regional de primer orden y el HLLC-Davis regional revisado.
Las caras de unión bulk/parche usan esa transferencia compartida de bajo orden.
No evaluar HLLC regional sobre caras bulk antes de que el kernel seleccione
su rama, incluida flux B. La igualdad de fluxes fuera del parche está probada
para controles acotados; no prueba identidad de toda la actualización I/Q ni
permite trasladar automáticamente anteriores PASS.

**Balance ALE y geometría.** En cada cara G=A(x_f)(F-sU). En una frontera
material usar s=u* derivado del Riemann y G=(0,A*p*,A*p*u*,0,...,0). En las
caras ordinarias s=0. Un mismo valor suministra ambos signos del intercambio.
Wdot=A(x_f)*s y dI/dt=G_left-G_right+S. Para la representación regional
constante, S tiene solo momentum p_r*(A_right-A_left); bulk conserva la fuente
geométrica correspondiente al kernel/estado aceptados. Flux, área, trabajo y
fuente pertenecen a la misma etapa. La fuente se mantiene idéntica en los
candidatos high/low y se incluye también en el cap de admisibilidad. El ledger
devuelve por separado integrales de caras y de fuentes. No duplicar el trabajo
de una partición numérica como trabajo de pared física.

**Etapas y guardas.** Remap solo entre pasos completos. Mantener topología
común durante SSPRK2 de (W,I): Y1=Yn+dt L(Yn), Y2=Y1+dt L(Y1),
Yfinal=.5Yn+.5Y2. Validar geometría, inventarios, simplex y NASA de Y1, Y2 y
final; la combinación final no puede esconder un Y2 inadmisible. Un único
theta limita la diferencia high-low compartida por todas las caras de la
etapa, conservando la receta revisada de cap, 54 bisecciones y hasta ocho
reducciones de redondeo. Un low-order inadmisible rechaza el trial y requiere
otro dt: no autoriza clipping ni otra EOS. Se preserva la composición física
de etapas que corresponda a la ruta contratada; no asumir un mapa de fuentes
homogéneo sobre Q proyectado cuando el estado está representado por regiones.

Cada intento registra transacción, padre, etapa, candidatos theta aceptables
o rechazados y selección efectiva. El rollback restaura W, I, orden,
identidades, eventos y ledgers juntos. Diagnósticos de trials descartados
permanecen identificados como tales; las observaciones no se convierten en
transacciones aceptadas. No promediar listas regionales con topologías distintas.

## Predictor volumétrico propuesto, con aprobación acotada

El [volume-advisor-review](reviews/volume-advisor-review.json) corroboró el
predictor, no una garantía de positividad no lineal ni la receta de área
completa. Para cada etapa y región:

    bL = a + |u-sL|; bR = a + |u-sR|
    dt_x = .2*dx/max(bL,bR)
    dt_V = .2*V/max(A_L*bL,A_R*bR)
    Vdot = Wdot_R-Wdot_L
    dt_shrink = .5*V/(-Vdot) si Vdot<0; +infinito si no
    dt_advisor = min_regiones(dt_x,dt_V,dt_shrink)

Comprobar el mismo dt en Y0 y Y1. Si el segundo predictor falla, rechazar el
intento completo y volver a Yn; no sustituir dt a mitad de etapa. El término
de contracción limita la pérdida FE de volumen a la mitad en aritmética exacta;
las guardas reales siguen comprobando geometría, redondeo, EOS y constituyentes.
S16 compondrá este límite con los demás límites físicos/eventos adjudicados.
No es una nueva regla global de CFL ni prueba de coste práctico con láminas
materiales arbitrariamente pequeñas.

## AREA-02: requisito abierto que impide congelar la transferencia

El [hallazgo AREA-02](reviews/area-projection-finding.json) demuestra que
reintegrar A usando x derivados y redondeados puede producir un volumen de
solapamiento distinto del DeltaW autoritativo. En un intervalo retenido de
longitud 1e-10, proyectar sobre sus propios bordes produjo error relativo de
masa 1.69568416e-7. El remap y la observación no pueden emplear representaciones
de volumen incoherentes aunque el ledger global sea pequeño.

Antes de adjudicar esta receta se exige cierre independiente con una regla
explícita y común de volumen representado/solapamiento que:

1. Restituya el inventario de una región al proyectar sobre ella misma y
   cubra particiones parciales y completas sin doble conteo ni pérdida.
2. Respete W/I autoritativos, documente residuos de inversión y redondeo y
   preserve intervalos físicos finos, extremos canónicos y signos de energía.
3. Haga coherentes remap, proyección conservativa y observables ponderados;
   no altere inventarios para obtener presión ni use EOS del agregado.
4. Incluya reproducer AREA-02, casos adversos y revisión independiente de
   la fórmula y su implementación, más regresiones afectadas con hashes.

Este documento no decide la corrección aún en desarrollo ni la considera
PASS. El texto técnico definitivo de transferencia y sus bindings deben
incorporarse antes de congelar R5. La aprobación del advisor no levanta este
bloqueo de representación.

## Alcance interior y fronteras: distinción explícita

Se adopta el límite de
[interior-boundary-scope-review.md](reviews/interior-boundary-scope-review.md):
la evidencia del mecanismo interior no acredita nacimiento, salida, colisión,
entrada con inversión de donante ni acoplamiento de fuentes/eventos. Un contacto
que alcanza un extremo físico no soportado provoca rechazo transaccional
diagnosticado; no desaparece, atraviesa el extremo sin ledger o se homogeneiza.
Un cruce de cara de la malla base en el interior sí se trata mediante el remap.
Los joins geométricos y datos de área fuera de la cobertura calificada también
requieren rechazo explícito o contrato previo, nunca interpolación inventada.

La propuesta anterior de interfaz incluía salidas entre lo necesario para
una receta completa. Esta adjudicación sería deliberadamente más estrecha:
distingue selección del mecanismo interior, aceptación de implementación S06
en el alcance que se adjudique con todos sus gates, y aceptación posterior
de consumidores. No relabela una obligación de salida pendiente como COMPLETE
ni convierte la selección BCR en merge automático de S06.

S07 posee las trazas del donante real y el intercambio compartido; S16, la
transacción global, dt y orden de eventos. Esa propiedad no los autoriza a
inventar la ciencia faltante. **Antes de implementar o aceptar esas rutas**,
un contrato explícito debe definir datos físicos de creación/salida, transferencia
regional de geometría e I12, momento del evento, ledger pareado, reversión y
pruebas. Hasta entonces las rutas dependientes permanecen no soportadas; no
se puede anunciar un motor GEN1 funcionando por aprobar el interior.

## Impactos mínimos y autorización de paths que debe contener la BCR

La excepción de S05 debe limitarse a `src/dino2next/gasdynamics/`,
`tests/unit/s05/` y `tests/contract/s05/`: objeto regional aditivo inmutable,
acceso a geometría exacta ya aceptada, proyección/observables explícitos e
identidades de serialización. Mantener significado y restricciones de Mesh1D
y DuctState homogéneos. No introducir flux numéricos en S05 ni rehacerlo.
La extensión puede vivir en módulos nuevos de ese paquete; no requiere
modificar termodinámica, especies, datasets, 0D, Cd, T3 o W2.

S06 conserva la propiedad de reconstrucción, remap, flux, etapas, guardas y
diagnósticos en sus paths vigentes, y prueba la extensión S05 bajo la excepción
expresa. Actualizar de forma coordinada los IDs de almacenamiento/observables
PHY-004/NUM-001/004, la aplicación regional de NK/TS/ST, interfaces públicas,
scope ownership y matriz de verificación; no cambiar tolerancias o referencias
físicas para conseguir aceptación. VAL-008 conserva A físico como observable.
La referencia NASA independiente sigue sin importar el candidato.

S07, S14 y S16 requieren consumo regional explícito de trazas/fuentes/etapas;
S17/S18 deben conservar e identificar el estado necesario; S22 integra solo
rutas aceptadas. Frontend recibe observables del backend, sin duplicar EOS.
Estas son obligaciones de consumidores, no implementaciones ya demostradas.

## Evidencia actual, cobertura pendiente y coste

Las revisiones reales de
[nueve contactos](reviews/hybrid-nine-contact-review.json) y
[choque dirigido](reviews/hybrid-shock-review.json) corroboran el prototipo
pequeño, no la matriz VAL-008 completa. Nueve contactos cubren todas las
composiciones/temperaturas y u=0/±100; se auditaron 1953 estados físicos
seleccionados. Máximo p exterior por etapa: 9.493e-7 Pa; ledgers de dominio
y ventana: hasta 3.42e-16 normalizado. El caso choque pair0/ratio2 a N80/N160
conserva 101 muestras, referencia calificada, estados causales y errores
decrecientes con orden observado cercano a uno. No se afirma orden dos.

Antes de aceptar el método integrado siguen siendo obligatorios:

| Grupo | Cobertura exigida |
|---|---|
| Representación/AREA-02 | Identidad de proyección, reparto completo/parcial, intervalos finos, extremos, signos, rollback y reinicio regional. |
| Contactos VAL-008 | Todos los pares originales, estacionario/móvil ambos sentidos, térmicos, cruces, presión interior/exterior, mallas/CFL/101 muestras y guards originales. |
| Choques VAL-008 | Todos los pares y ratios originales, secuencia completa N80/160/320/640 y CFL, incertidumbre de referencia, órdenes y ledgers. Dos niveles de un par no los sustituyen. |
| Geometría | GCL, reposo/onda/contacto con área, fuente de momentum y trabajo coherentes, advisor Y0/Y1, variación de área dentro de la cobertura adjudicada. |
| S05/S06 regresiones | Suite S05 afectada y todos los gates S06 VAL-006/007/008/009/010/011/027 que consuman rutas cambiadas; hooks de composición física de etapas y límites de admisibilidad. |
| Integridad/integración | Fixtures/referencias/umbrales congelados, manifiestos históricos, pruebas no interrumpidas, revisión real del HEAD, foundation, readiness y CI, y posteriormente consumidores/S22. |

La evidencia homogénea solo puede reutilizarse con identidad y pertinencia
demostradas de fuentes, inputs, estado, aritmética y evaluación consumidos.
Igualdad de flux fuera del parche no basta cuando cambia la actualización
de promedios Q a inventarios I. Mantener explícitamente invalidadas las
coberturas afectadas hasta verificarlas; no borrar fallos previos.

Costes observados: nueve contactos pequeños, 98.17 s más 35.71 s de auditoría;
choque dirigido N80, 52.73 s, y N160, 135.13 s. Son controles concretos del
entorno empleado, no un benchmark de ciclo 2T. La búsqueda de solapamientos
lineal revisada elimina el barrido cuadrático sin cambiar transferencias.
Persisten coste de NASA, tamaño de regiones, dt y eventos; no se inventa un
presupuesto ni se certifica practicidad GEN1. Un benchmark representativo de
integración sigue pendiente. Datos sintéticos no son validación experimental
ni predictiva.

La siguiente acción de adjudicación es cerrar AREA-02 y revisar independientemente
el texto de transferencia resultante junto con esta propuesta. Hasta entonces
solo existe una propuesta interior técnicamente delimitada, no una receta
completa aprobada ni autorización para eludir gates o contratos de consumidores.
