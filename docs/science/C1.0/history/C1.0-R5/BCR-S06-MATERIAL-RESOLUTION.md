> **Normative — C1.0-R5** · Status: `SCIENTIFIC_IMPLEMENTATION_BASELINE_FROZEN`

# BCR S06 — material representation and acoustic resolution

The authorized BCR adjudicates two bounded selections: MR-008 interior material
representation and MR-010 free-end precision assigned to explicit resolution
rows. This is specification selection, not acceptance of S06 implementation,
all GEN1 boundaries, experimental validation or predictive validation. Existing
contracts remain effective outside the expressly changed clauses below.

MR-008 preserves NASA data, formation energies, EOS domains, inversion and the
physical conserved inventories. MR-010 preserves its reference formulas,
operators, masks, 101 samples, both amplitudes and numerical error thresholds;
it changes which explicit rows require final precision. Rigid-end obligations
and historical R4 failures remain unchanged. Required affected verification
and final coordinated normative-HEAD review are not waived.

Scientific selections were independently reviewed before this incorporation:

| Selection | Reviewed source SHA256 | Independent review |
|---|---|---|
| MR-008 | `513fd6c15eeb323779204edee953b5736f08eb851f147eda3c4409ec82cf6843` | [MR008 review](../../../research/bcr_s06_material_resolution/reviews/mr008-interior-adjudication-review.json) |
| MR-010 | `2d2638c69180f343d514f319324a2ad386734592f1dfdc6ab14be2c36dddf8cc` | [MR010 review](../../../research/bcr_s06_material_resolution/reviews/mr010-specification-review.json) |

Prototype paths cited below are relative to
`research/bcr_s06_material_resolution/`; their hashes identify research evidence,
not already accepted production implementations. A patch or file hash is never
a replacement for executing affected gates against the implementation HEAD.

## MR-008 — decisión y correspondencia física

Representar explícitamente los intervalos materiales declarados dentro del
ducto. Una región puede contener la mezcla de cinco especies y los cuatro
inventarios de origen; su identidad material no es una especie ni un trazador.
Conservar la EOS NASA, sus datos, formación química, dominios e inversión TI
aceptados. Recuperar cada región desde sus propios inventarios y volumen.
Nunca corregir energía/composición para imponer presión ni usar EOS del promedio
conservado de una celda mixta como sustituto de su presión física.

[Pan et al. (2017), sección 2.3](https://arxiv.org/html/1704.00519v1) aporta el
punto de partida publicado: balances conservativos por volumen material y
transferencia de presión/trabajo en interfaces. La adaptación seleccionada es
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
no son una segunda geometría editable. Conservar brackets válidos de inversión
y residuos exactos de integral menos W. El extremo canónico derecho que coincide
con el W almacenado del proveedor se representa por su x físico y residuo
firmado explícitos, no por un falso bracket de raíz fuera del dominio. Rechazar
el siguiente W representable fuera del dominio; no modificar W para ocultarlo.

Propiedad de celdas base, fracciones y solapamientos son productos derivados.
La proyección conservativa es la suma de inventarios intersectados dividida
por dx de la celda base, conservando el significado A*U del Q existente.
No se mantienen dos copias editables de masa/energía. Reinicios incluyen W,
I12, orden, identidades materiales y geometría; Q proyectado solo es insuficiente.

Los productos públicos se distinguen explícitamente:

- `regional_states`: estados NASA de cada I12/V, con temperaturas regionales.
- `conservative_projection` e inventario total compensado: cantidades conservadas.
- `pressure_volume_average`: sum_r(p_r*DeltaW_interseccion_r)/DeltaW_objetivo,
  con la misma medida W representada que remap/proyección. Esta es la
  discretización declarada de integral(A*p)/integral(A); no reintegrar A en
  x redondeados para sus pesos o denominador. Registrar residuos respecto a
  la integral física exacta. Una media de longitud se nombra separadamente.
- Velocidad bulk y fracciones químicas/de origen proyectadas: cocientes de
  inventarios, por tanto ponderados por masa. No se intercambian con medias
  volumétricas de velocidad o composición. No se publica un ambiguo conjunto
  `primitive_average` que aparente ser un estado EOS homogéneo.

En VAL-008 con A=1, la presión física coincide con su media de longitud. Otros
fixtures conservan su ponderación declarada. Un diagnóstico EOS(Q proyectado),
si se expone, se identifica como homogéneo y no alimenta presión física,
fuentes ni condiciones de interfaz de la ruta regional.

## Receta interior seleccionada

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
distintas ni se borra masa pequeña por conveniencia. El valor .35 y el ancho
de parche de cuatro celdas son elecciones explícitas de esta BCR,
respaldadas por controles acotados y sujetas a las regresiones pendientes;
no son teoremas heredados de Pan ni garantías de precisión universal.

**Remap.** Repartir cada donante mediante solapamientos dentro de la misma
región; conservar orden y transferencia compartida. La regla de primer orden
seleccionada es I_donante por la fracción de volumen representado solapado; el
último receptor recibe el resto conservado del donante. Recuperar y validar
todos los receptores antes de aceptar. No corregir presión tras el remap ni
restar su error de los resultados. La consistencia de esos volúmenes con W
autoritativo y su consumo bulk tienen cierre acotado AREA-02/03, con la
convención explícita descrita más abajo. El barrido monotónico optimiza solo
la búsqueda de intersecciones, con equivalencia exacta ya revisada; no cambia
la regla de reparto.

**Parche y bulk.** Las fronteras materiales y los intervalos que no coinciden
con una celda base ordinaria siembran el parche. Añadir cuatro celdas de
distancia de stencil a ambos lados. En los tramos ordinarios restantes,
llamar la reconstrucción y los fluxes de la ruta candidata S06/PR8 sin alterarlos,
con cuatro ghosts de estados regionales reales. Su fuente de investigación está
identificada por SHA256 84e5fba185fabf8008936c6ca533d0610b8cb87aa87b48833cf3d821328bfac9;
implementa la receta normativa, pero ese kernel candidato no está aceptado en main.
Dentro del parche se adopta
la representación regional de primer orden y el HLLC-Davis regional revisado.
Las caras de unión bulk/parche usan esa transferencia compartida de bajo orden.
No evaluar HLLC regional sobre caras bulk antes de que el kernel seleccione
su rama, incluida flux B. La igualdad de fluxes fuera del parche está probada
para controles acotados; no prueba identidad de toda la actualización I/Q ni
permite trasladar automáticamente anteriores PASS.

**Riemann regional seleccionado.** La fuente concreta es
`local_material/prototype.py`, SHA256
c2f9d81ce57a8cae741839b5522185e10485c7cabe1070a935500a13387d3eee,
funciones `rhs` y `flux`, consumidas selectivamente por el híbrido. Para
estados NASA izquierdos/derechos físicamente recuperados:

    sL = min(uL-aL,uR-aR); sR = max(uL+aL,uR+aR)
    dL = rhoL*(sL-uL); dR = rhoR*(sR-uR)
    u* = (pR-pL+dL*uL-dR*uR)/(dL-dR)
    p* = pL+dL*(u*-uL)

Rechazar transaccionalmente `RIEMANN_INADMISSIBLE` si la operación no es
finita, p*<=0 o no sL<u*<sR; no ajustar presión o energía. En cara material,
s=u* y el flux ALE usa p* como se define abajo. En cara ordinaria usar FL si
sL>=0, FR si sR<=0; en otro caso elegir K=L si u*>=0 y K=R si u*<0:

    rho*K = rhoK*(sK-uK)/(sK-u*)
    U*K = UK*(rho*K/rhoK), excepto momentum y energía
    momentum*K = rho*K*u*
    energy*K = rho*K*(energyK/rhoK+(u*-uK)*(u*+pK/(rhoK*(sK-uK))))
    F_HLLC = FK+sK*(U*K-UK)

Recuperar el estado estrella con NASA estricta antes de consumir ese flux;
el fallo rechaza el trial, no habilita otra EOS. Especies y orígenes siguen
la misma razón de densidad. F(U) tiene advección uU, con p añadido al
momentum y pu a energía. Estas son elecciones Davis/HLLC concretas de la
adaptación; no se atribuyen las aproximaciones de velocidad de Pan a ellas.
No se aplica esta selección a caras bulk que pertenecen a la receta NK.
**Balance ALE y geometría.** En cada cara G=A(x_f)(F-sU). En una frontera
material usar s=u* derivado del Riemann y G=(0,A*p*,A*p*u*,0,...,0). En las
caras ordinarias s=0. Un mismo valor suministra ambos signos del intercambio.
Wdot=A(x_f)*s y dI/dt=G_left-G_right+S. Para la representación regional
constante, S tiene solo momentum p_r*(A_right-A_left); bulk conserva la fuente
geométrica correspondiente a la receta normativa y a la ruta candidata identificada. Flux, área, trabajo y
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

## Predictor volumétrico seleccionado

El [volume-advisor-review](../../../research/bcr_s06_material_resolution/reviews/volume-advisor-review.json) corroboró el
predictor, no una garantía de positividad no lineal ni la receta de área
completa. Para cada etapa y región:

    bL = a + |u-s_face,L|; bR = a + |u-s_face,R|
    dt_x = .2*dx/max(bL,bR)
    dt_V = .2*V/max(A_L*bL,A_R*bR)
    Vdot = Wdot_R-Wdot_L
    dt_shrink = .5*V/(-Vdot) si Vdot<0; +infinito si no
    dt_advisor = min_regiones(dt_x,dt_V,dt_shrink)

Aquí s_face,L/R son velocidades numéricas de caras Wdot/A: cero en caras
ordinarias y u* en materiales. No son las cotas acústicas Davis sL/sR del
Riemann. Comprobar el mismo dt en Y0 y Y1. Si el segundo predictor falla, rechazar el
intento completo y volver a Yn; no sustituir dt a mitad de etapa. El término
de contracción limita la pérdida FE de volumen a la mitad en aritmética exacta;
las guardas reales siguen comprobando geometría, redondeo, EOS y constituyentes.
S16 compondrá este límite con los demás límites físicos/eventos adjudicados.
No es una nueva regla global de CFL ni prueba de coste práctico con láminas
materiales arbitrariamente pequeñas.

## Medida W: cierre acotado AREA-01/02/03

Se preservan los hallazgos y borradores anteriores. AREA-02 documentó error
relativo de masa 1.69568416e-7 en auto-proyección de una región de longitud
1e-10; AREA-03 documentó presión bulk cercana a 99999.983 Pa frente a presión
regional 100000.00000012 Pa por usar una segunda medida geométrica.
La [revisión final independiente](../../../research/bcr_s06_material_resolution/reviews/area03-closure-and-W-review.json)
cierra AREA-01/02/03 en `area_hybrid/area_solver.py`, SHA256
3c956e1a76ebe9b29331374f761d7331b11b93958e081f34e181a73a674a841a;
`advisor.py` SHA256
ed03f21099f20570dd3793dd42f64f547593d89ccdd836ef8848deb8f55c8c13.
Incluye 17 tests independientes PASS y ambas presiones del reproducer
100000.00000012126 Pa. No equivale a aprobación completa S06/GEN1.

Un extremo de intersección coincidente con cara existente hereda su W
autoritativo; un extremo físico nuevo usa W canónico del proveedor. La
medida de intersección es la diferencia de esos W. Conservar los residuos
exactos integral menos W, incluyendo inversión. Remap, proyección y presión
ponderada consumen esa misma medida. No reparar inventarios ni EOS.

Bulk consume Q=I/dx y area_average=DeltaW/dx; sus ghosts consumen I/DeltaW.
Así desaparece la segunda medida integral(x_derivado). La multiplicación/
división del puente regional deja redondeo ordinario explícito, no identidad
aritmética universal. Áreas físicas de caras, perímetro y fuente siguen
evaluándose en coordenadas derivadas con sus residuos registrados. El kernel
original identificado permanece intacto; la adaptación de almacenamiento y
geometría se declara aquí, no se esconde como equivalencia global bitwise.

La trayectoria de reposo nueva cambió inventarios finales hasta 2.22644e-15
y fluxes hasta 4.03733e-11; se preservan datos previos y nuevos. Los seis
controles de un paso del advisor permanecieron byte idénticos. El cierre
acredita consistencia acotada de la representación, no convergencia completa
de ondas con área variable, joins no cubiertos ni eventos de frontera.
## Alcance interior y fronteras: distinción explícita

Se adopta el límite de
[interior-boundary-scope-review.md](../../../research/bcr_s06_material_resolution/reviews/interior-boundary-scope-review.md):
la evidencia del mecanismo interior no acredita nacimiento, salida, colisión,
entrada con inversión de donante ni acoplamiento de fuentes/eventos. Un contacto
que alcanza un extremo físico no soportado provoca rechazo transaccional
diagnosticado; no desaparece, atraviesa el extremo sin ledger o se homogeneiza.
Un cruce de cara de la malla base en el interior sí se trata mediante el remap.
Los joins geométricos y datos de área fuera de la cobertura calificada también
requieren rechazo explícito o contrato previo, nunca interpolación inventada.

La selección anterior de interfaz incluía salidas entre lo necesario para
una receta completa. Esta adjudicación es deliberadamente más estrecha:
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

## Impactos mínimos y autorización de paths de esta BCR

Se autoriza la excepción S05 exclusivamente para:

- `src/dino2next/gasdynamics/regional.py` (nuevo): objeto regional inmutable,
  acceso a geometría exacta, proyección/observables e identidad de reinicio.
- `src/dino2next/gasdynamics/__init__.py`: únicamente exportación aditiva de
  la nueva interfaz; conservar implementación y comportamiento existentes.
- `src/dino2next/gasdynamics/README.md`: documentación de la nueva interfaz.

No se comparte el subtree S05 completo. Las pruebas nuevas pertenecen a
`tests/unit/s06/` y `tests/contract/s06/`, bajo ownership S06. Mantener intactos
los tests S05 existentes y ejecutar como regresión
`tests/unit/s05/test_cell_inventory.py` y
`tests/contract/s05/test_geometry_balance.py`, con su conftest sin cambios:
Mesh1D, DuctState homogéneo, inventarios, guardas y balance geométrico conservan
su significado. No introducir flux numéricos en S05, cambiar otras rutas S05
ni modificar termodinámica, especies, datasets, 0D, Cd, T3 o W2.
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
[nueve contactos](../../../research/bcr_s06_material_resolution/reviews/hybrid-nine-contact-review.json) y
[choque dirigido](../../../research/bcr_s06_material_resolution/reviews/hybrid-shock-review.json) corroboran el prototipo
pequeño, no la matriz VAL-008 completa. Nueve contactos cubren todas las
composiciones/temperaturas y u=0/±100; se auditaron 1953 estados físicos
seleccionados. Máximo p exterior por etapa: 9.493e-7 Pa; ledgers de dominio
y ventana: hasta 3.42e-16 normalizado. El caso choque pair0/ratio2 a N80/N160
conserva 101 muestras, referencia calificada, estados causales y errores
decrecientes con orden observado cercano a uno. No se afirma orden dos.

Antes de aceptar el método integrado siguen siendo obligatorios:

| Grupo | Cobertura exigida |
|---|---|
| Representación/AREA-02/AREA-03 | Identidad de proyección, reparto completo/parcial, intervalos finos, extremos, signos, rollback y reinicio regional. |
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


## MR-010 — free-end reflection operator and resolution obligations

R3 measures total pressure C/Cref at every sample. Let a=g(x-ct) and
b=g(2-x-ct), with g(z)=epsilon*exp(-((z-.25)/.05)^2). At ct=.75 both centers
are1 and a=b pointwise, hence p'=a-b=0 and Cref=0 exactly. This occurs at
required sample75 for both amplitudes. Floating cancellation noise cannot define
a physical phase, and no denominator offset or sample removal is authorized.

Replace that undefined relative operator by characteristic reflection components:

    w+ = (p-p0 + rho0*c*u)/2 = a
    w- = (p-p0 - rho0*c*u)/2 = -b
    p0=rho0=1; c=sqrt(1.4); sigma=.05; k=2*pi
    C_h(w) = sum_i wbar_i * integral(cell_i, exp(-i*k*x) dx)
    A0 = abs(integral(0,1, g(x)*exp(-i*k*x) dx)) > 0

For the candidate use the recovered cell pressure/velocity with fixed rho0, not
local rho in the acoustic decomposition. For the reference apply the SAME C_h
to exact analytic Gaussian cell averages; do not compare a discrete cell-average
operator with a different continuous operator. The continuous integral defines
only the fixed nonzero scale A0, approximately8.6462771789e-7 at epsilon1e-5;
it scales linearly for epsilon/2. This explicitly changes the former observation
discretization and separates directional waves instead of their canceling sum.

All 101 original samples j=0..100, ct=j/100, remain mandatory at every row of
the MR-010 resolution-obligation table, for epsilon=1e-5 and epsilon=5e-6
executed separately. Evaluate and retain each directional component and
total-pressure complex error at every sample, including sample75 and every
tiny-signal tail. At each FINAL_PRECISION row require
|C_candidate-C_reference|/A0<=.01 for all three signals at all samples.
STUDY rows retain the same error measurements and threshold comparisons;
their required acceptance conditions are stability, conservation and the
declared convergence/sensitivity study, not a claim of final precision.
No measured remainder is subtracted. At FINAL_PRECISION rows this absolute
complex gate covers zero-reference instants as well as all weaker tails.

Define the declared phase-resolution mask from the reference ONLY:
abs(C_reference,h)>=.01*A0. The cutoff is the existing absolute1% resolution
budget, not a fitted candidate error or an assertion that weaker nonzero signals
have mathematically undefined phase. Qualify and freeze the mask before running
the candidate. For the original three meshes and either epsilon it gives incident
j=0..83 and reflected j=67..100, retaining resolvable pulse tails. Both components
are assessed at75. On this reference-qualified mask require relative amplitude error<=.01 and
abs(arg(C_candidate*conj(C_reference)))<=pi/N for each directional component
at every FINAL_PRECISION row of the MR-010 table. Evaluate and retain those
same comparisons at STUDY rows without relabeling a failed precision
comparison as PASS. The mask is qualified and frozen independently at every
mesh before candidate execution, including N1600; it is never copied from
another mesh without qualification. The qualified N1600 mask retains
incident j=0..83 and reflected j=67..100 for both epsilon values. A zero candidate in an observable interval fails
amplitude; its phase is undefined, never phase PASS. Outside the mask mark phase
NOT_ASSESSED_BELOW_DECLARED_ABSOLUTE_RESOLUTION and enforce the absolute gate
at FINAL_PRECISION rows; retain the same comparison at STUDY rows.
Only a zero coefficient has undefined phase; no phase PASS is claimed for either
category. This changes coverage/interpretation explicitly: relative phase applies
to directional signals resolved above the declared physical absolute budget,
and absolute vector error covers all weaker tails and every cancellation.

### MR-010 resolution-obligation table (free end only)

Each row requires both epsilon values and all 101 samples. Report means retain
the measured value, uncertainty and original threshold comparison, not PASS.
The rigid-end matrix and thresholds are unchanged. Historical R4 failures
retain their original status. These obligations do not assert execution or
reference qualification; source-bound qualification must precede execution.

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

Nonzero observability follows analytically: whenever the center is inside W,
at least one sigma-wide side is inside. Rotate C by its center phase. Its real
part is bounded below by epsilon*sigma*[cos(2*pi*sigma)*sqrt(pi)*erf(1)/2
-sqrt(pi)*erfc(.25/sigma)]. This is positive. The cell-average operator differs
from the continuous coefficient by at most2*pi*dx*epsilon*sigma*sqrt(pi);
subtracting this bound at the coarsest N200 still leaves a strictly positive
lower bound. The additional tail mask is qualified with high-precision exact
cell integrals. At N200, the incident j83 and j84 magnitudes are approximately
.0120913079*A0 and .00557899248*A0, with the other grids giving the same mask.
Reference arithmetic must have an absolute enclosure no larger than
min(.001,.1*sin(pi/N))*.01*A0 and certify each coefficient's side of the cutoff.
Differences between two precision settings alone are sensitivity checks, not
certified enclosures. Failure to qualify is REFERENCE_NOT_QUALIFIED.

Retain epsilon/2, every field/time/mesh, existing boundaries and conservation
checks. Peak/time diagnostics do not replace amplitude or phase. Rigid-wall
operators and thresholds are unchanged; a kernel change still requires regression
evidence. This decision preserves the1% and pi/N physical budgets but does not
claim equivalence to a relative phase that was undefined for total pressure.


## MR-010 implementation, reuse and cost obligations

The normative fixture and its catalogue assign STUDY rows N200/400/800 at
CFL .2/.1/.05 and FINAL_PRECISION rows N1600 at CFL .1/.05, each for both
amplitudes executed separately. The adapter must publish separate study results,
precision comparisons and historical R4 status. It must retain masks, uncertainty,
retries, raw fields, traces, ledgers, actual dt, costs and consumed source hashes.
The full spatial study and complete rigid suite remain required for acceptance.

Extend reference coverage to N1600 and bind the portable qualification to its
actual generator, input data, catalogue and certificate. Requalify a published
artifact whose sources or bindings changed; do not merely replace a checksum
to conceal stale qualification. This BCR does not declare that implementation
qualification has occurred. Gaussian formulas and uncertainty allocation remain
unchanged. The research four-run evidence is selection evidence only until
consumed inputs, reference, state representation, arithmetic and evaluation
identity with the acceptance candidate are demonstrated. A changed material,
recovery, transfer, integrator or evaluation path requires affected verification.

S06 owns this verification; S18 traceability and S22 integrated verification must
record actual coverage. S16 acquires no new global CFL rule from this fixture.
No production API, frontend physics or unrelated fixture is changed by MR-010.

Four individually reviewed N1600 runs satisfy the observed precision gates for
both amplitudes at both CFLs; they do not complete the required coarse study or
rigid suite. Their measured process wall time was about 20–36 minutes per
canonical acoustic transit, with four initially concurrent processes, not a
full two-stroke engine benchmark. See the [four-run evidence and source bindings](../../../research/bcr_s06_material_resolution/acoustic/kernel_review/summary.json).
There is no demonstrated numerical need to replace transport for this specific
observable at these resolutions. This establishes neither universal transport
accuracy nor practical whole-engine cost. A representative GEN1 benchmark must
declare model, physical horizon, ducts, smallest cell, material coupling, hardware
and an explicit cost budget before claiming practicality; no SLA is invented.
Two CFLs measure sensitivity, not temporal order or a certified dt-to-zero error.
No remainder is subtracted and no historical precision failure is relabeled PASS.
