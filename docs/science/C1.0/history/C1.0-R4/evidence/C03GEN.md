# Contrato operativo GEN1 y estado de freeze

Versión: **C0.3-final-adjudication** · 2026-09-06

Estado: **SCIENTIFIC_BASELINE_NOT_READY**. C0.1 y C0.2 se conservan sin modificación. Este corpus adjudica cláusulas, pero no autoriza arquitectura ni producción. SELECTED no significa validación experimental ejecutada.

## Scope operativo

Configuración exacta del PRODUCT_AND_CAPABILITY_CONTRACT, topología PHY-004, química PHY-002. SALVAGE; MANDATORY_LEGACY_CODE_DEPENDENCY=NONE. Modelo de motor independiente del código histórico. Capacidad definida no equivale a autorización de construirla mientras siga SPEC_NOT_EXECUTABLE.

Physics required: PHY-001–010; PHY-005 parcial por C03-BLK-001.

Numerics required: NUM-001–010; cierre conjunto bloqueado según NUM-005–009.

Validation required: VAL-001–011,013,014,016–024,027,028; VAL-012 generaljunction y015 legacy no obligatorios. VAL-025/026 para claims predictivos específicos. V4–V6 no deben ejecutarse para freeze documental, pero su contrato debe estar cerrado; sí hacen falta para afirmar validación científica/predictiva del producto.

## Required inputs — semántica y unidades

| Grupo | Nombre y significado | Unidad / dominio | Provenance |
|---|---|---|---|
| Geometría | B,S,l,Vclear,Vcc,TDC | m,m³; positivos,l>S/2,Vcc,min>0 | Metrología e incertidumbre |
| Puertos | A_i(θ),count_i,timings,normal,estaciones | m²,rad,entero≥1 | Contorno medido y mapa de apertura |
| Ductos | L_i,A_i(x),Pw_i(x),ε_i,ℓcurva_i | m,m²; A>0,área continua | Geometría completa y reducción1D |
| Fluido | NASA/transport hashes,φ,p0,T0,Yamb | φ.6–.8,Pa,K; PHY-002 | Fuel puro certificado,aire seco,datos versionados |
| Operación | N,listaRPM,θSOC,Δθ,a,n,ηburn | rpm2000–6000,rad,adimensional; PHY-006 | Ignición/quemado medidos sólo calibración |
| Scavenging | χ,κ | adimensional>0; constantes por hardware/dominio | Tracer temporal y análisis identificabilidad |
| Descarga | Cd_dirección(apertura,Π) | adimensional≥0; sin extrapolación | Bancada con estados de remanso/área exactos |
| Calor | Tw_s,Hcc(N,T,Tw),aAnnand,Cq | K,W/K,adimensional; PHY-007 | Termometría/ensayo térmico independiente |
| Pérdidas | K_j(dirección,Re),FMEPmech,Waux,Tlub |1,Pa,J/rev,K | Estaciones/curvas,bancada y frontera mecánica |
| Inicialización | m_k,U/H,Q_i,tags,θ inicial | SI y admisibilidad PHY-002/003 | Cold explícito o warm con hash y estado periódico previo |
| Numérica | malla y referencia por fixture | NUM-001–010 | Valores fuente/coupling/periodicidad pendientes: NO default |
| Validación | dataset split,operadores,covarianza | Unidades por observable | EX-01–05 y BCR-EX-C03 |

Inputs térmicos/pérdidas no disponibles impiden calificar una simulación de motor; no se sustituyen por cero. Falta mapa mecánico sólo deshabilita brake. Required outputs: OUT-001–012 exactos del contrato de producto. Unsupported cases: todas las exclusiones y estados fuera del dominio; presentar fallo en sweep, no interpolarlo como convergido.

## BCR-EX-C03 — adoptado, OI-09 permanece CLOSED_CAMPAIGN_CONTRACT

Motivo: decisiones concretas de fuel/fase, calor/cárter, mapas de pérdidas y cohortes afectan entradas y operador experimental de C02. Evidencia: PHY-002/003/007/008/009. Documentos afectados: PHYSICS_SPEC,VALIDATION_SPEC,GEN1_CONTRACT,SCIENTIFIC_DECISIONS,registro y trazabilidad. Impacto futuro: inputs de composición/térmica/estaciones; tests de fase,calor ytag; volver a reducir datos antiguos con las nuevas definiciones antes de comparación. No se ha revelado held-out ni ejecutado campaña, por lo que no hay validación previa declarada que se pierda.

EX-01 adquisición: conservar candidato y protocolo geométrico C02, sin asumir que motor publicado incorpora estas condiciones. Alimentación con isooctano puro vaporificado externamente, combustible y aire secos certificados; medir T,p de premix antes del conducto y verificar ausencia de gotas/condensación y balance gravimétrico de fuel. Vaporizer/calefacción son equipo de campaña, no modelo de evaporación del simulador. N operativo dentro2000–6000 y límites térmicos/seguridad de hardware. Si hardware no mantiene dominio, no ajustar contrato con sus datos.

EX-02 partición: conservar matriz RPM normalizada y throttles C02, en intervalo común calificado. φniveles=.6,.7,.8; calibración central.7,validación intermediaRPM,held-out extremosφ y throttle50%/escape nuevo según C02. Antes de reservar datos, calificar que condiciones cumplen mezcla/fase y combustión estable; no escoger después cuáles resultados ocultar. Medir sensoresp,cárter/cilindro/escape,suministro ytemperaturas tal como C02.

EX-03 añadir medición de calor/conductancia de cárter: campaña motored de entrada/salida entalpía,paredT ybalance energético con pV, en al menos3RPM×3Tgas×3Tw de la envolvente prevista,3repeticiones; Hcc=Q/(Tw−T) sólo con |Tw−T|≥20K y propagación de incertidumbre; no inferirH de divisióncasi0. Ajustar mapa rectangular usando esos datos, validar puntos intermedios reservados. Cq de ductos: ensayos pulsantes de cada familia geométrica con tres amplitudes y tres frecuencias cubriendoRPM, paredes/T/ṁ y p en estaciones; calor por ciclo del balance de entalpía, incertidumbre y comparación de presión. K de curvas: Δp y caudal en ambos sentidos, cincoRe en envolvente, restar fricción y excluir puertos, documentar covarianza. χ/κ: trazador de admisión, salida de escape y carga retenida sincronizados conθ, no sólo eficiencia escalar. Si los dos parámetros no son identificables con esa señal, adquirir segundo observable retenido por muestreo/trazador antes de calibrar. Estas mediciones pueden efectuarse en componentes aparte; no se contaminan datos held-out de motor.

EX-04 operador: pressure0D vsensemble angulado, escape local con sensor/filtrado conocido; calor integrado por ciclo, no h de correlación vs termopar; tagR excluye aire externo X y producto químico es otra variable. Preserve GUM/covarianzas, criterio95%Holmα.05 y capacidad metrológica C02. Presupuesto incluye entalpía de fuel gaseoso, incertidumbre de propiedad estimada, flujo, pV, Tw, fase/TDC y señal tracer. No aumentar artificialmente incertidumbre para aceptar modelo. EX-05: manifiesto/registro irrevocable de parámetros antes de revelar reserva. Mantiene EXPERIMENTAL_CAMPAIGN_CONTRACT_READY, sin datos ejecutados.

## Criterios de completitud

Scientifically complete GEN1: implementación de todas las cláusulas seleccionadas, cero blockers científicos, verificaciones requeridas ejecutadas, estudio espacial/temporal, conservación por inventario/interfaz, calificación de modelos físicos con campaña definida, datos y provenance reproducibles. Código terminado o ciclo estable no cumple.

Predictively validated GEN1: además, aceptación VAL-025/026 correspondiente sobre reserva independiente sin reajuste, dominio/observables y necesidad de mapas de componente explícitos. No predicción universal del mercado de motores.

## Freeze y precedencia

Estado actual SCIENTIFIC_BASELINE_NOT_READY. C1.0 y C1_BASELINE_MANIFEST_SHA256.json **no se emiten**. Precedencia final prevista, sólo tras consistencia y freeze: GEN1_CONTRACT > PRODUCT_AND_CAPABILITY_CONTRACT > PHYSICS_SPEC > NUMERICAL_METHOD_SPEC > VALIDATION_SPEC > SCIENTIFIC_DECISIONS > LEGACY_DISPOSITION > BASELINE_DECISION_REGISTER > investigación/auditoría > legacy. No resolver contradicciones ocultándolas con esa prioridad.

Después de freeze todo cambio científico exige BASELINE_CHANGE_REQUEST con motivo,evidencia,documentos,impactos implementación/tests/validación yrevalidación. Este expediente C03 ya conserva huellas de C02 y decisiones explícitas; no retroescribe su historia.
