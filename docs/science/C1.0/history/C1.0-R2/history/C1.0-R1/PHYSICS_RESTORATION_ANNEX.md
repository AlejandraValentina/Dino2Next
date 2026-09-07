> **Normative — C1.0-R1** · Status: `SCIENTIFIC_IMPLEMENTATION_BASELINE_FROZEN`
> Revision: `NORMATIVE_COMPLETENESS_REVISION`; scientific decisions changed: NO. This restoration does not assert all specification gaps are closed.

# Restored zones, outputs, thermal and losses

## PH-001 — two-zone balances (PHY-003)
Source: C03PHY PHY-003 SELECTED, retained by current C1. T3 storage replaces only superseded port representations, not these zone equations.



Cárter: una zona homogénea con m_k[kg], U[J], Vcc conocido; dm_k=Σṁ_jYdonor,k dt; dU/dt=−pVdot+Qdot+Σṁh0. Gas entrante pierde energía cinética resuelta al mezclarse pero conserva h0. No se integra un momentum ficticio de cárter.

Cilindro: una zona fuera del barrido; **dos zonas A (admisión) y B (bulk)** desde primera apertura de transfer hasta cierre final del escape. Requiere transfers cerrados al EPC y combustión posterior al EPC. Presión común, temperaturas/composición separadas; no se resuelven jets espaciales. Al activar: B contiene todo, A tiene masa y volumen cero. Al EPC: sumar m_k y U, e invertir EOS de la zona única; no promediar temperaturas.

Entradas de transfers →A; reingreso de escape→B, cada una con Y y h0 reales. Salida de escape: β=mA/(mA+χmB); Yout=βYA+(1−β)YB; hout=βhA+(1−β)hB. Salida inversa por transfers: δ=mA/(mA+mB) con las mismas combinaciones usando δ. Cada caudal se descompone entre zonas con esos pesos. Mezcla interna A→B: ṁmix=mA/τ, τ=κ/ω, ω=2πN/60. A cero no produce salida. χ>0 y κ>0 son dos inputs adimensionales, constantes por geometría dentro del dominio calificado; se identifican mediante trazadores temporales y trapping, no mediante torque. No existe valor universal por defecto.

Estados útiles H_z=Σm_zk hk(Tz), m_zk y presión; Utotal=ΣH_z−pVc. Rm_z=Σm_zkRk; Vz=Rm_zTz/p; Sz=Qz+Σṁ_j h0,j, incluyendo intercambio interno firmado. Bz=Σhk(Tz) ṁ_zk; αz=Rm_z/(mz cp,z). Entonces:

pdot=[Σz{αz(Sz−Bz)+Tz ΣkRk ṁ_zk}−p Vdotc]/[Vc−ΣzαzVz];
Hdot_z=Vz pdot+Sz; Tdot_z=(Hdot_z−Bz)/(mz cp,z).

Denominador=ΣVz cv,z/cp,z>0. Al nacer A vacía con varios donors: Ybirth=Σṁj+Yj/Σṁj+, hbirth=Σṁj+h0j/Σṁj+; obtener Tbirth invirtiendo h(Tbirth,Ybirth)=hbirth a presión común. Usar ese límite para T,Y,α, con VA=0; si no entra masa, omitir zona vacía. No introducir una masa semilla. El calor superficial se reparte por Vz/Vc, aproximación geométrica explícita. h_z es entalpía de mezcla a Tz; no sólo entalpía sensible.

Demostración de conservación: el intercambio A→B aparece con igual m_k y h en signos opuestos; Σdm_zk conserva el balance externo por especie. Sumando Hdot y diferenciando U=ΣH−pV: Udot=ΣSz−pVdot. Suma de volúmenes obtenida de EOS da Vdotc por la ecuación de pdot. El merge conserva exactamente m_k,U; las diferencias discretas son NUMERICAL_RESIDUAL.

Fuentes: balances abiertos y familia multizona revisada en C0.2; β y τ son closure reducido propio adjudicado, no correlación publicada de Blair/Benson. No pretende resolver estructura tridimensional ni universalidad de χ,κ. Evidencia algebraica: research/scavenging_balance.py; validación independiente pendiente VAL-019/EX. Se exige identificación local de rango completo del Jacobiano de observables respecto de logχ,logκ y bandas de confianza; parámetros no identificables impiden calificar hardware, no autorizan ajuste adicional libre.


## PH-002 — tracers, metrics and work (PHY-009/010)
Source: C03PHY PHY-009/010 SELECTED. Validation ID references below are historical; active ownership is the R1 VALIDATION_SPEC and registry.



Cada masa lleva partición de tags F0 (fresco no visitó cilindro en ventana actual), F1 (fresco ya visitó), R (material del cilindro expuesto a combustión anterior) y X (gas exterior ajeno a la entrega fresca). No especies químicas. Ambiente de admisión F0=1; ambiente de escape X=1. R no es sinónimo químico de gas quemado: incluye fuel que pudo quedar sin quemar después de SOC. Reportar por separado fracción química de productos y fracción externa mX/mcyl. Las cuatro fracciones suman1; residual fraction=mR/mcyl no incluye aire exterior X.

En TPO, F1→F0 en toda la red finita, registrando relabel explícito. En transferencia hacia cilindro, F0→F1 en receptor; Dunique=integral de masa F0 entrante por transfers. Entradas sucesivas de F1 no se cuentan de nuevo. En SOC, tags del cilindro→R para nueva cohorte residual, sin cambiar especies/energía. En reingreso de escape conservar tags/Y/h del verdadero donor; no reemplazar por aire salvo extremo externo.

Al EPC: delivery ratio gross=masa fresca positiva suministrada por transfers/(ρref Vd), ρref del premix a p0,T0 de admisión; trapping efficiency=mF1,cyl/Dunique; scavenging efficiency=(mF0+mF1)cyl/mcyl; residual fraction=mR/mcyl; charging efficiency=(mF0+mF1)cyl/(ρrefVd). Short-circuit fraction net=integral neta F1 a través del puerto de escape/Dunique. También informar gross y retorno por separado: net puede diferir del flujo bruto. Masa F1 que regresa al cárter no es short-circuit de escape. Dunique=F1retenida+F1fuera_del_cilindro+F1exportada_exterior_neta, al partir F1=0. Denominador cero→UNDEFINED_METRIC, no cero físico. Las definiciones de cohorte difieren de fórmulas estacionarias sin reflujo: metadatos obligatorios en comparación experimental. Parámetros de tags no calibrables; VAL-016/019.

## PHY-010 — performance SELECTED

Wc=∮pcdVc; Wcc=∮pccdVcc; Wg=Wc+Wcc; IMEPc=Wc/Vd; IMEPnet,g=Wg/Vd. Indicados: Tc=Wc/(2π), Pc=Wc N/60, con N[rpm]. Reportar gas-net por separado; no restar bombeo dos veces. Mapa FMEPmech(N,IMEPnet,g,Tlub,Twall)[Pa] de C0.2, interpolación multilineal dentro de envolvente rectangular medida; no extrapolar. Wb=Wg−FMEPmechVd−Waux; BMEP=Wb/Vd; Tb=Wb/(2π); Pb=WbN/60. Waux[J/rev] con lista de auxiliares y plano de medida. Sin mapa válido: BRAKE_OUTPUT_UNAVAILABLE. Pérdidas mecánicas no se descomponen ficticiamente entre anillos/cojinetes. Eficiencia al fuel se refiere a fuel suministrado y LHVg, no sólo retenido. VAL-022/024/025 y EX de C0.2. Fuentes primer principio y frontera adjudicada C0.2.


## PH-003 — thermal/transport/loss equations (PHY-007/008)
Source: C03PHY PHY-007/008 SELECTED, including C03-R04…R08 attribution. No correlation or numerical coefficient is reselected.

 con límites

Qgas=Σh_s A_s(Tw_s−Tgas); positivo hacia gas. Tw[300,1000]K prescritas por superficie/segmento medido, no estados estructurales. No promesa de temperatura del metal. Áreas: head/piston medidas; liner expuesta según geometría. Para dos zonas asignar A_s,z=A_s Vz/Vc.

Cilindro/head/piston: Annand convectivo h=a k/B Re^0.7, Re=ρ(2SN/60)B/μ. a input identificado independiente de torque, 0.35–0.8; propiedades de mezcla a Tgas. No heredar coeficiente de motor grande como calibración de GEN1. Se selecciona ley de calor integrada efectiva; radiación no separada, ni flujo local de pared predictivo. Compensación del término omitido sólo mediante a dentro del dominio experimental identificado. Exigir comparación calor integrado y presión motored/fired; si a sale de rango o residuo térmico sistemático persiste, el modelo falla y requiere BCR, no ampliar a silenciosamente. C03-R04. Este párrafo no afirma que la correlación esté validada en este 2T.

Cárter: cierre lumped medido Hcc(N,Tgas,Tw)[W/K]≥0, hcc=Hcc/Awet. Mapa tridimensional multilineal, sin extrapolación. Qcc=Hcc(Tw−Tgas). Hcc se obtiene de ensayo térmico/motored y caudal independiente, no de torque; input con incertidumbre y geometría. No adiabático por falta de datos: MISSING_THERMAL_DATA. Modelo Newton de conductancia global identifica efecto térmico sin atribuir turbulencia de cilindro al cárter.

Ductos: se adjudica **Gnielinski cuasiestacionario de conducto equivalente**, con Tw prescrita y factor multiplicativo Cq por familia geométrica identificado en bancada térmica pulsante; Cq>0, fijo por geometría/intervalo calificado, no por cada dato held-out. h=Cq k Nu/Dh, Re=ρ|v|Dh/μ, Pr=μcp/k. Longitud L es longitud física del segmento térmico definido en inputs, no Δx; Dh=4A/Pw. El coeficiente es promedio efectivo del segmento aplicado localmente usando propiedades locales; esta localización es aproximación explícita.

Laminar UWT: NuL=[3.66³+0.7³+(1.615(RePrDh/L)^(1/3)−0.7)³+{(2/(1+22Pr))^(1/6)(RePrDh/L)^(1/2)}³]^(1/3). Turbulento: fT=(1.8 log10Re−1.5)^−2; NuT=(fT/8)(Re−1000)Pr/[1+12.7 sqrt(fT/8)(Pr^(2/3)−1)]·[1+(Dh/L)^(2/3)]·(Tgas/Tw)^0.45. Para Re≤2300 usar NuL; Re≥4000 NuT; en medio interpolación lineal entre valores en2300/4000. Límite v=0 finito, sin división por v. fT es auxiliar de correlación de calor; NO sustituye fDarcy del balance de momentum.

Dominio adjudicado: 0≤Re≤10^6, 0.6≤Pr≤1.0, 0<Dh/L≤0.1; gas monofásico y pared medida, conducto equivalente no separación masiva. Conos/curvaturas se califican por presión/calor medido y Cq, no por afirmar que una correlación de tubo recto los valida. La aplicación instantánea en reversión no resuelve memoria de capa límite; se exige validar calor por ciclo y enfriamiento medio en VAL-018. No se publicará h instantánea como medición predicha. Se permite esta aproximación porque el objetivo térmico GEN1 es pérdida integral y estado del gas; discrepancia fuera de incertidumbre obliga a revisar el modelo, no normalizar resultados. Fuente original C03-R05; extensión declarada propia.

Transporte: modelo dilute-gas mixture-averaged de Cantera3.2/Kee, con NASA del dataset y parámetros en thermo_transport.yaml. Isooctano no lineal: σ=6.414Å, ε/kB=458.5K, dipolo0, polarizabilidad0, relajación rotacional1; otros cuatro gases: parámetros GRI3 exportados, no termodinámica GRI sustituta. μmezcla=ΣXi μi/ΣjXjΦij, Φij=[1+sqrt(μi/μj)(Mj/Mi)^0.25]²/sqrt(8(1+Mi/Mj)); kmezcla=0.5[ΣXi ki+1/(ΣXi/ki)]; Pr derivado. Propiedades puras por teoría cinética y colisiones de C03-R07; input exportado versionable fija la referencia. T300–2200K; no difusión de especies molecular resuelta. Se requiere equivalencia numérica a referencia3.2 o tabla certificada; no dejar elegir otra regla de mezcla. El dataset de transporte es estimado, con incertidumbre propagada en validación térmica; no recalibrar μ/k contra potencia.

## PHY-008 — pérdidas SELECTED

Darcy: fD=8[(8/Re)^12+1/(A+B)^(3/2)]^(1/12); A=[2.457 ln(1/((7/Re)^0.9+0.27ε/Dh))]^16; B=(37530/Re)^16. Re=ρ|v|Dh/μ; τw=fDρv|v|/8; Sf=−fDρv|v|Aduct/(2Dh). En Re→0 usar límite Sf=−32μv Aduct/Dh²; en v=0 Sf=0. Potencias en logaritmos para evitar overflow. 0≤ε/Dh≤0.05, Re≤10^6; régimen cuasiestacionario equivalente; no memoria viscosa predictiva. Fuente C03-R08. Energía total no tiene sumidero de fricción de pared fija adiabática; pérdida cinética se convierte en interna.

Pérdidas de curvas realmente presentes: por cada tramo geométrico medido j, K_j(dirección,Re)≥0 con estaciones y velocidad de referencia locales, mapa lineal por Re sin extrapolación; distribuir κj=Kj/ℓj [1/m] sobre longitud física de la curva. Añadir Sf,j=−κjρv|v|A/2, sin sumidero de energía total. Es cierre medido de fuerza efectiva, no K universal. Rectos: κ=0. K reducido de bancada debe descontar fricción distribuida y excluir estaciones de puertos que ya están en Cd. Inputs deben mostrar esa reducción y su incertidumbre; si falta, MISSING_LOSS_DATA. Saltos de área abruptos/uniones universales no entran en GEN1. Presión geométrica pA′ no es pérdida empírica.

VAL-018 mide el cierre conjunto pulsante; función cuasiestacionaria no predice histéresis de esfuerzo. La aceptación de presión/calor integrado delimita puntos válidos; no se ajusta K para compensar dispersión numérica.


## PH-004 — dataset identity
The byte-preserved `datasets/thermo_transport.yaml` is the C03 selected Cantera 3.2.0 export; `datasets/thermo_species.json` is its selected NASA extract. The active manifest records their SHA-256. The YAML state stanza is export metadata, never an engine initial condition. Runtime/install version and loaded-file hash must be recorded and compared to the manifest; there is no invented future installation hash. A different coefficient or transport dataset is not an interchangeable installation.

## PH-005 — inherited scientific source attribution


- C03-R01: [NASA TM4513, McBride et al., 1993](https://ntrs.nasa.gov/citations/19940013151), dataset `nasa_gas.yaml` de Cantera 3.2.0 preservado por C0.2 y extracto numérico en research/inputs/thermo_species.json. No confundir con NASA9.
- C03-R02: [NIST SRD69, isooctano](https://webbook.nist.gov/cgi/cbook.cgi?ID=C540841&Mask=4&Type=ANTOINE&Plot=on), datos originales de Willingham et al. 1945, DOI 10.6028/jres.035.009. Masa molar se fija por la tabla atómica del dataset, no mezclando redondeos NIST.
- C03-R03: [IAPWS SR1-86(1992), saturación](https://iapws.org/technical-guidance/release/Supp-sat.download). Se usa para admisibilidad de fase; no reemplaza la EOS gaseosa.
- C03-R04: [Annand, 1963](https://doi.org/10.1243/PIME_PROC_1963_177_069_02), original consultado también en [reproducción](https://www.scribd.com/document/830191556/Annand). Se selecciona sólo término convectivo; no se reconstruye un exponente ilegible del término radiativo.
- C03-R05: Gnielinski, “On heat transfer in tubes”, IJHMT 63 (2013),134–140, [original reproducido](https://www.scribd.com/document/786670780/Gnielinski-single-phase). Correlación de tubos estacionarios; la extensión cuasiestacionaria GEN1 es una aproximación adjudicada, no resultado experimental de ese artículo.
- C03-R06: [Yelvington, MIT, 2004, tesis doctoral](https://dspace.mit.edu/server/api/core/bitstreams/4cf65d4e-a294-4623-b1b2-8b6b238fc37d/content), apéndice de transporte: isooctano, parámetros atribuidos a LLNL. Son parámetros estimados de transporte, no mediciones de GEN1.
- C03-R07: [Cantera 3.2, MixTransport](https://cantera.org/3.2/cxx/d9/d17/classCantera_1_1MixTransport.html), formulación basada en Kee et al. Dataset combinado exportado en thermo_transport.yaml; referencia de propiedades, no solver Dyn2T.
- C03-R08: [Churchill, 1977, original](https://files.engineering.com/files/85c0f3a6-a102-4a22-9d35-f15858c0dd2b/CEM_-_Friction-factor_equation_%281977%29.pdf), inspeccionado en C0.2; conversión Darcy conservada.
- C03-R09: [Levine y Schwinger, 1948](https://doi.org/10.1103/PhysRev.73.383), límite acústico de extremo sin brida. Condición de presión impuesta GEN1 es su aproximación de baja frecuencia, no una frontera sin reflexión.
- Fuentes de Euler/FV/HLLC/SSPRK y scavenging finalistas: registro R01–R38/NR01–NR16 de C0.2. El nuevo closure de dos zonas se declara derivación reducida propia a partir de balances; no se atribuyen sus parámetros a Benson o Blair.

