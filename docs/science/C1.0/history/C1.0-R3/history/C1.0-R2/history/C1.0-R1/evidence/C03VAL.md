# Ensayos adjudicados y cierre de aceptación

Versión: **C0.3-final-adjudication** · 2026-09-06

Estado: **SCIENTIFIC_BASELINE_NOT_READY**. C0.1 y C0.2 se conservan sin modificación. Este corpus adjudica cláusulas, pero no autoriza arquitectura ni producción. SELECTED no significa validación experimental ejecutada.

## Reglas verificables

Ningún VAL de producción se declara ejecutado. Los ensayos de investigación aportan evidencia de selección y nunca sustituyen ejecución posterior de la implementación. UNIT_TEST ≠ REGRESSION_TEST ≠ NUMERICAL_VERIFICATION ≠ SCIENTIFIC_VALIDATION ≠ EXPERIMENTAL_VALIDATION. Calibración dentro de todos los VAL: **NO**. Los ajustes sólo se realizan antes, en CALIBRATION_DATA.

Artefactos comunes: inputs efectivos y unidades, hashes de ecuación/dataset/referencia, arrays inicial/final/serie, malla, cada dt, condiciones de borde, normas, escala, root/retry log, balances por interfaz/dominio, versión del comparador y decisión. Valor faltante no produce PASS. Referencia numérica debe tener error <10% del umbral candidato; si no, REFERENCE_NOT_RESOLVED. No usar incertidumbre de modelo inflada para absorber discrepancia.

Conservación: residual y SQ de NUM-010, condición |RQ|/SQ≤10^−10 para cada cantidad conservada en fixtures numéricos de hasta10^5 pasos; justificación: presupuesto de acumulación float64 conservativo por encima de residuos ~10^−15 observados, separado del error de solución. Para identidades locales usar γn=nε/(1−nε), ε=2^−52, n=128 y condición κ=max(1,Σ|términos|/escala_física). Acceptance |r|≤γ128 κ escala; no dividir por diferencia casi nula. Estos son presupuestos numéricos declarados, no precisión experimental.

## Fixtures cerrados o parcialidad identificada

Cada entrada fija objetivo/componente, nivel, tipo, input, referencia, observable, métrica y aceptación. Inputs fuera del dominio físico pueden emplearse como **benchmark EOS ideal** explícito; nunca califican operación GEN1. Los errores de solución exacta son de promedios de celda, salvo donde se indica diagnóstico de centros. Tiempo/longitud adimensional de pruebas gamma usa Lref=1 m, ρref=1 kg/m³, pref=1 Pa y Rref=1 J/(kg K), salvo fixture SI indicado.

### VAL-001 — identidades V0, UNIT_TEST / NUMERICAL_VERIFICATION

PHY-001/002/006. B=.052 m,S=.05 m,l=.101 m,Vclear=1.2e−5 m³,Vcc,TDC=3e−4 m³; θ=jπ/180, j=0…360. Oráculos PMS/PMI exactos y diferenciación analítica. EOS: NASA cinco especies en T={350,400,600,999.999999,1000,1000.000001,1600,2200} K, p={5e4,1e5,1e6,5e6} Pa y cinco puros + premixφ=.6,.7,.8 + productos correspondientes; puros son stress matemático. Observar V,h−u−RT,cp−cv−R,ΣY,elementos,T roundtrip. Identidades: tolerancia γ128κ; roundtripT≤1e−8 K con raíz bracket cerrada y residual de energía≤cv·1e−8 K. Comparación propiedades contra Cantera3.2 con mismo dataset: |δcp|/cp,|δh|/max(|h|,cpT),|δu|/max(|u|,cvT)≤10^−8, margen sobre 7.12e−10 observado en cambio de rama de C02. A1000 exigir convención documentada, derivadas unilaterales; no derivada central entre ramas. Fail significa identidad/inversión/dataset incorrectos, no modelo químico validado. Artefactos tablas y condicionamiento.

### VAL-002 — volumen móvil cerrado V1, NUMERICAL_VERIFICATION

PHY-003. Gas gamma1.4,R287, m=1e−3kg, V(t)=1e−3[1+.2sin(2πt)]m³; T0=600K,U0=mR T0/(γ−1); sin flujo/calor. t∈[0,1]s; pasos100,200,400,800. Uexact=U0(V0/V)^(γ−1), pexact=(γ−1)Uexact/V. Métrica **máximo sobre toda trayectoria**, no sólo último ciclo; escalaU0/p0. Error relativo máximo≤10^−4 en800 y orden≥1.8 en últimos dos pares, además balanceU+∫p dV. El presupuesto 10^−4 limita error de integración del trabajo reversible a escala energética del caso; no se hereda el orden3 aparente del error final C02. Referencia exacta; artefactos trayectoria y cuadratura de trabajo refinada. Fail integración/trabajo.

### VAL-003 — calor cerrado V1, NUMERICAL_VERIFICATION

m=.001kg,cv=1000J/kgK,H=hA=2W/K,Tw=600K,T0={400,800}K,V=.001m³; sin flujo. tfin=2s, dt={.02,.01,.005,.0025}s. Texact=Tw+(T0−Tw)exp(−Ht/(mcv)). Métrica max|T−Texact|/|T0−Tw|≤10^−5 último nivel y orden≥1.8; Q=mcv(T−T0) con signo correcto y ledger10^−10. Referencia exacta. El límite se deriva de resolver tiempo térmico τ=.5s con dt/τ=.005 y error global RK2 O((dt/τ)²); no valida h de Annand.

### VAL-004 — descarga entre reservas V1, NUMERICAL_VERIFICATION

Dos reservas quiescentes gasideal gamma1.4,R287,T0=600K,p0=2e5Pa,Ageom=1e−4m²,Cd=.7,count=1; Π={.1,.3,.5282817877,.7,.9,1}; repetir sentidos. ṁexact=Aeff p0/sqrt(RT0) sqrt[2γ/(γ−1)(Π^(2/γ)−Π^((γ+1)/γ))] para Π>Πcrit; Πcrit=(2/(γ+1))^(γ/(γ−1)), debajo usar Πcrit. Sin malla ni tiempo: raíz escalar. Error absoluto |δṁ|≤10^−9 Aeff p0/sqrt(RT0); continuidad, cambio de signo, energía=ṁcpT0. NASA repetir los 27 inputs exactos de nozzle_results C02, con s,h y condiciónv=c, resolución de raíz10^−10 relativa en presión. Comparar evaluación independiente Cantera + maximización escalar; diferenciaG≤10^−7. No valida VAL-013 puerto acoplado. Artefactos pcrit,raíz,masa,h0.

### VAL-005 — reacción/energía V1 y calificación científica de aproximación

Inputs químicos PHY-002/006; φ={.6,.7,.8}, TSOC={350,450,600,750}K, pSOC={.3,.6,1}MPa, residual={0,.2,.4}; sólo casos con producto completoT≤2200K y p≤5MPa, fase admisible. Mezcla residual = productos completos de mismoφ; para estado distinto de una operación, añadir su composición real a la calificación. ReferenciaUV de once especies/dataset C02, Cantera3.2 rtol termodinámico10^−10 y conservación elemental. Candidato de oxidación completa debe tener |Tcomplete−Teq11|/Teq11≤.02; fuera no hay dominio calificado. No afirma equivalencia con química detallada.

Ensayo de Wiebe: a=5,n=2,SOC=0,Δθ=.7rad,η=.9; θ={−.1,0,.1,.35,.7,.8}; evaluar función e integrar derivada por cuadratura independiente subdividida en eventos16/32puntos. |integral−η|≤1e−10; productos según ξ,Σelementos y energía con formación segúnVAL-001. Ni oxígeno ni fuel negativos. Artefactos productos,T,elementos,formación y energía. Química no se calibra contra el oráculo; falla rechaza punto/dominio.

### VAL-006 — Sod V2, NUMERICAL_VERIFICATION

Euler gamma1.4,R1,x∈[0,1], discontinuidad .5; (ρ,v,p)L=(1,0,1), R=(.125,0,.1); t=.2, bordes extrapolados fuera de alcance de ondas; N=50,100,200,400; CFL=.3 y .15. Referencia exacta Clawpack C02 preservada, integrar celda cortando todas las ondas con Gauss16/32; discrepancia cuadratura<10^−10. Normas L1 por variable y residual. A400, L1ρ≤2Δx(ρmax−ρmin); se exige reducción L1 con cada refinamiento, pendiente log2≥.5 en últimos pares. Presupuesto de resolución de dos celdas equivalentes de salto integrado, no porcentaje histórico de potencia. Admisibilidadρ,p>0 y conservation10^−10. Falla solver/refinamiento, no física de motor.

### VAL-007 — contacto gamma constante V2

Euler gamma1.4,R1,L=(1,1,1),R=(2,1,1),x0=.5,t=.1; N100,200,400,CFL.3, extrapolación; repetir v=0. Referencia exacta contacto x=.5+vt, promedio de celda. |p−1|∞,|v−v0|∞≤10^−10; L1ρ≤2Δx|ρR−ρL| y reducción por refinamiento. Para v=0, masa/energía inicial recuperada a tolerancia roundoff. NUMERICAL_VERIFICATION; artefactos perfiles/ledger.

### VAL-008 — contacto NASA V2

EOS cinco especies, dominio1m, x0=.5,p=1e5Pa,t=.001s,v={0,100}m/s, N100,200,400,CFL.3 y .15. Casos: N2 puro600K/CO2 puro600K; N2 600K/CO2 1800K; premixφ.7 400K/productosφ.7 1800K. Puros son stress fuera de mezcla operativa. Borde extrapolado, perfiles de ondas no deben contaminar observable por reflexión de borde. Referencia exacta contacto conp,v constantes, posición advectada y composición material; no comparar temperatura de una celda mixta con promedio aritmético deT.

A400: presión estacionaria L∞/p0≤1e−10. Advectado térmico extremo: L1/p0≤.002 y L∞/p0≤.02; mezcla motor: L1/p0≤.0005 y L∞/p0≤.005. Son **presupuestos numéricos adjudicados**: ≤0.05% de presión de fondo integrada y≤0.5% localizada para el caso motor; el caso puro es stress con presupuesto separado. No son tolerancias experimentales ni se extrapolan al error de potencia. L1 debe disminuir en cada nivel, pendiente≥.5; repetir CFL/2, cambio en normaL1<20% del presupuesto correspondiente. Y≥0,ΣY y balances10^−10. C03 ejecutó54 contactos a CFL.3 y añadió tres contactos de mezcla motor/MC a CFL.15. La sensibilidad del stress puro queda en el gate de robustez, no PASS supuesto. No exige abolir a máquina la oscilación térmica advectada a costa de energía.

### VAL-009 — pulso acústico V2

Euler gamma1.4,R1,ρ0=p0=1,ε=1e−5,x∈[0,1] periódico; ρ=1+εcos2πx,p=1+γεcos2πx,v=sqrtγ εcos2πx. t=.25,N50,100,200,400,CFL.3/.15. Oráculo lineal: trasladar x→x−sqrtγ t; controlar error O(ε²) repitiendoε/2. Observable coeficiente Fourier de presión: amplitud y fase, no sólo L1. A400, errorfase≤π/N, pérdida relativa amplitud≤2(2π/N)²+10ε; orden≥1.8 antes del piso lineal/no lineal. Artefactos coeficientes complejos y soluciones.

### VAL-010 — reflexión V2

Subcaso pared: fixture reflection C02 (ρ=1+εcosπx,p=1+γεcosπx,v=0), gamma1.4,R1,paredesv=0,t=.6,N50/100/200/400,CFL.3; referencia linealρ′=εcosπx cos(πsqrtγt),v=εsqrtγ sinπx sin(πsqrtγt). Error normalizado porε,orden≥1.8 antes del pisoε; L1p/(γε)≤.01 a400.

Subcaso extremo libre **obligatorio, no ejecutado en C03**: ecuaciones acústicas linealesρ0=p0=1,c=sqrtγ,impedanciaZ=c; x[0,1], pulso derecho p′=ε exp[−((x−.25)/.05)²],v′=p′/Z,ρ′=p′/c²; extremo derechop′=0,izquierdo característico anecoico; tfin=1/c,N200/400/800,CFL.3. Referencia por características: onda incidente f(x−ct), reflejada−f(2−x−ct), v′=[f(x−ct)+f(2−x−ct)]/Z. Error de amplitud reflejada≤1%, signo negativo, errorfase≤π/N, conservación de energía acústica hasta flujo exterior a error de discretización. Este test valida BC lineal, no acoplamiento gas caliente NASA. La aplicación no lineal de frontera queda en BLK-001/004.

### VAL-011 — área variable V2

A=1+.4(x−.5)²m², x[0,1], gamma1.4,R1. Reposoρ=p=1,v=0,paredes,t=.2,N50/100/200/400; max|v|,|p−1|≤10^−10. Nozzle suave: p0=T0=1,Mthroat=.3; A/A*=M^−1[2/(γ+1)(1+(γ−1)M²/2)]^((γ+1)/(2(γ−1))); raíz subsónica. T=1/(1+.2M²),p=T^3.5,ρ=p/T,v=M sqrt(γT); t=.3,ghosts exactos en cada centro, N50/100/200/400,CFL.3. Referencia estacionaria, promedios ∫AQ por Gauss16/32 (delta<1e−10); L1ρ/ρref≤2e−6 a400 y orden≥1.8. C03 verificó orden con diagnóstico de centros; el fixture contractual exige además promedio de celda, no atribuirlo al ensayo ejecutado. Conservation con fuente geométrica. Transición cónica continua: vértices en caras y mismo control de refinamiento; no salto discontinuo en GEN1.

### VAL-012 — junction general

OPTIONAL_FUTURE, fuera del conjunto obligatorio. No elimina interacción de transfers vía inventario0D.

### VAL-013 / VAL-014 / VAL-016 / VAL-020

Objetivos respectivamente reservoir–pipe, volumen móvil–pipe, inversión con composición y cárter–transfer. NivelV3 para13/14/16, V4 para20. NUMERICAL_VERIFICATION/SUBSYSTEM_VALIDATION. **NO_CERRADA: C03-BLK-001/002/004.** Inputs y oráculo deben corresponder a ley causal final, no toy isothermal ni flujo prescrito. No existe threshold final defendible de esos ensayos en este corpus. Artefactos mínimos: flujos integrados de cada extremo, ondasp,v,T,Y, cierre energético incluyendo trabajo, estacionesCd, estado crítico y error independiente de referencia. Falla no implica code bug probado si el ensayo aún no está especificado. Esta falta basta para impedir freeze.

### VAL-015 — legacy

No obligatorio, MANDATORY_LEGACY_CODE_DEPENDENCY=NONE. Sólo después de admisión explícita y ejecución de ensayos aplicables de este contrato; regression antigua no basta.

### VAL-017 / VAL-018 / VAL-019 / VAL-022 / VAL-023 / VAL-024

Validación experimental de Cd, escape/calor/pérdidas, scavenging, motored, fired y eje/consumo. OI-09 CLOSED_CAMPAIGN_CONTRACT. Referencia/input/operador/incertidumbre/partición/criterio: contrato EX-01–05 de C02, cuyo texto y hash permanecen en expediente; modificaciones concretas BCR-EX-C03 en GEN1_CONTRACT. Observables respectivamente ṁ(θ),pescape/T/heat-cycle,curvastrazador/masa fresca retenida,pc/pcc motored,pc fired/heat release,braketorque/ṁfuel. Instrumentos/procedimiento deben resolver el observable, nunca comparar presión local con temperatura/media no correspondiente. Compatibilidad estadística95% con corrección Holm α=.05 y capacidad metrológica Ucontraste<|variación objetivo|/3, sin inflar incertidumbre de modelo. No equivale a una promesa universal de error máximo de ingeniería. Parámetros congelados antes de usar VALIDATION_DATA. Artifact datos crudos,operador,incertidumbre/covarianza,intervalos,errores. No ejecutados.

### VAL-021 — periodo1

NUMERICAL_VERIFICATION y diagnóstico operativo; NUM-009. **NO_CERRADA C03-BLK-003.** Referencias requeridas: trayectoria period1 con modo lento, period2…8 conocidos y arranques diferentes en fixture acoplado. No hay maxcycles/threshold definitivo deducido de ondas. Un RMS bajo de presión por sí solo no pasa.

### VAL-025 / VAL-026 — predictividad V6

HELD_OUT_PREDICTIVE_DATA de EX-C02, BCR-EX-C03. Condiciones nuevas / geometría de escape nueva, respectivamente. Mismos operadores y error metrológico anterior; cero calibración después de revelado. VAL-026 requiere que closures térmicos/pérdidas del nuevo escape sean aportados por mediciones independientes de componente antes de revelar datos de motor: no usar los datos de motor para Cq/K. Claim limitado a combinación de modelos con inputs de componentes conocidos, no predicción de escape sin información de pérdidas. Datos insuficientes→no claim predictivo, no remplazar por sweep sintético.

### VAL-027 — refinamiento y tiempo aislado

Espacial: reglas por caso anteriores. Temporal interior: N40 fijo, Euler gamma1.4,R1,ρ=1+.01sin2πx,v=.3,p=1,periódico,t=.1. MUSCL-MC/HLLC seleccionado; se conserva también el ensayo minmod para continuidad de evidencia. Las dos variantes se ejecutan separadamente. dt=.002,.001,.0005,.00025. Referencia semidiscreta DOP853 rtol2.3e−14,atol1e−16,maxstep=.0001, contrastada con rtol1e−13/atol1e−15; discrepancia1.4322e−14 L∞ para minmod. MC se contrastó en time_mc.json. Escala1, L1error≤1e−10 último dt y orden1.8–2.2 en dos primeros pares (verificar además que error de referencia sea menor al10% del umbral). No usar esta referencia semidiscreta como verdad física espacial. Para fuente lineal, matrices y y0 en source_selection.json, t1, pasos20/40/80/160, oráculo expm; exigir orden≥1.8 para método seleccionado. Fuente no lineal conjunta sigue BLK-002, no sustituida por expm.

### VAL-028 — balance de dos zonas (nuevo requisito)

V0/V1 NUMERICAL_VERIFICATION, PHY-003. Exact limit: cp1000,R287,mA=.0003,mB=.0007kg,TA400,TB900K,τ=.01s,Vconst=ΣmRT/1e5, p=1e5Pa,sin flujos externos/calor; tfin=.02s, pasos40/80/160/320. Oráculo mA=mA0exp(−t/τ), HA=HA0exp(−t/τ),mB=mtot−mA,HB=Htot−HA; pconst por gas igual y energía total constante. Error max escalado por mtot/Htot≤1e−6 a320, orden≥1.8; balances10^−10. Ensayo algebraico NASA: semilla2302,1000 estados exactos del script con escala e inputs preservados; identidades deVdot yUdot≤1e−11. Es verificación de cierre, no calificación empíricaχ/κ. Nacimiento/merge/reingreso de zonas están cubiertos por el gate BLK-002, no por este límite.
