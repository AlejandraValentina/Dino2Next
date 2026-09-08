# C0.10 — Eigenestructura característica NASA

Estado: derivación y verificación matemática completadas. **RESEARCH_ONLY_NON_PRODUCTION**. Este documento no congela GEN1 ni cambia su flux.

## Alcance y evidencia heredada

Se verifica C09 mediante sus 637 hashes, sin discrepancias. Permanecen T3, W2, λ identificada, NASA/especies y geometría NP. No se reidentifica ningún parámetro. Las composiciones son aire, productos y premezcla del expediente. El fluido es mezcla ideal térmicamente perfecta, químicamente congelada en este operador; las fuentes químicas se evalúan fuera de la eigenestructura homogénea.

Los coeficientes NASA7 se conservan en `research/c10/inputs/thermo_species.json`, con su procedencia NASA TM4513/Cantera y hash de origen. No se añade mezcla entre tramos ni extrapolación. En 1000 K se utiliza el tramo contractual superior; una derivada que atraviese el cambio de tramo no sirve de oráculo local. Los controles de derivadas usan estados separados de ese cambio.

## Variables y ecuaciones

Para K especies y K−1 fracciones independientes:

\[
V=(\rho,u,p,Y_1,\ldots,Y_{K-1}),\quad Y_K=1-\sum_{j<K}Y_j.
\]

En la formulación general, K designa la especie dependiente después de permutar índices. En los controles de transporte se elige N2 como dependiente para que especies ausentes no introduzcan una restricción espuria por redondeo. El orden físico conservado de los archivos heredados permanece combustible/O2/N2/CO2/H2O; no se cambia el significado de un índice silenciosamente.

\[
U=(\rho,\rho u,\rho E,\rho Y_1,\ldots,\rho Y_{K-1}),\quad
F=(\rho u,\rho u^2+p,u(\rho E+p),\rho uY_j).
\]

Unidades: ρ kg/m³; u m/s; p Pa; E,e,h J/kg; T K; R,cp,cv J/(kg K); Y adimensional. Área se excluye del Jacobiano local homogéneo y se incorpora en AF y los sources.

\[
R=\sum Y_kR_k,\quad h=\sum Y_kh_k(T),\quad e=h-RT,
\quad c_v=\sum Y_kc_{p,k}(T)-R.
\]

Las integrales NASA de h incluyen sus constantes de formación. Por ello e y E pueden ser negativas: la admisibilidad se comprueba mediante inversión EOS y temperatura, no imponiendo E>0. Para composición congelada, De/Dt=cv DT/Dt; masa y energía dan DT/Dt=−p∂xu/(ρcv). De ahí, exactamente:

\[
D\rho/Dt=-\rho\partial_xu,\quad Du/Dt=-\partial_xp/\rho,
\quad Dp/Dt=-\rho a^2\partial_xu,\quad DY_j/Dt=0,
\qquad a^2=(c_v+R)RT/c_v.
\]

No es una sustitución aproximada de γ constante. La forma primitiva resulta exacta para esta EOS ideal, con cp variable y composición congelada. No se extiende a química en equilibrio instantáneo o a una EOS real.

## Jacobiano primitivo y eigenpares

\[
B=\begin{pmatrix}u&\rho&0&0\\0&u&1/\rho&0\\0&\rho a^2&u&0\\0&0&0&uI\end{pmatrix}.
\]

Eigenvalues: u−a, u con multiplicidad K, u+a. Con ρ>0, T>0, R>0 y cv>0, a>0; las familias acústicas son distintas. La multiplicidad material no produce defecto de eigenvectores. Sonicidad u=±a hace nula una velocidad respecto de la malla, pero no singulariza la base local.

Columnas acústicas: r−=(1,−a/ρ,a²,0), r+=(1,a/ρ,a²,0). Columna de densidad/contacto: r0=(1,0,0,0). Cada columna de composición tiene una unidad en su propia Y y ceros en ρ,u,p. Esa perturbación sí cambia energía conservada.

La proyección inversa de cualquier incremento es:

\[
\alpha_-=(\Delta p-\rho a\Delta u)/(2a^2),\quad
\alpha_0=\Delta\rho-\Delta p/a^2,\quad
\alpha_+=(\Delta p+\rho a\Delta u)/(2a^2),\quad
\alpha_{Y_j}=\Delta Y_j.
\]

Estas expresiones definen L sin invertir una matriz numéricamente. La transformación inversa es Δρ=α−+α0+α+, Δu=a(α+−α−)/ρ, Δp=a²(α−+α+).

## Transformación conservada: formación y composición

Sea H=∂U/∂V, ΔRj=Rj−RK, Δej=ej−eK. Sus filas de masa y momentum son (1,0,0,0) y (u,ρ,0,0). La fila de energía es:

\[
H_{E,\rho}=e-c_vT+u^2/2,\quad H_{E,u}=\rho u,\quad H_{E,p}=c_v/R,
\quad H_{E,Y_j}=\rho[\Delta e_j-c_vT\Delta R_j/R].
\]

Las filas de especies tienen HρYj,ρ=Yj y HρYj,Yj=ρ. Entonces:

\[
A=\partial F/\partial U=HBH^{-1},\quad R_U=HR_V,\quad L_U=L_VH^{-1}.
\]

Omitir Δej o usar energía sensible sin la referencia contractual rompe esta transformación. La eigenestructura primitiva simple no autoriza tal omisión.

## Verificación independiente

`eigensystem.py`: 420 estados, tres composiciones, T=300/500/800/999/1001/1500/2200 K; p=50/100/600/5000 kPa; Mach=−2/−0.1/0/0.5/2. Comprueba LR−I y BR−RΛ. Contrasta H y A con diferenciación compleja de evaluaciones directas de los polinomios NASA, sin reutilizar las fórmulas de H/B.

`high_precision_check.py`: 36 estados adicionales, diferencias finitas centrales de cuarto orden con 60 dígitos, perturbación relativa 1e−12 en U y una inversión termodinámica de alta precisión. El oráculo calcula F(U) y sus diferencias; no se limita a comprobar una inversión de matriz. Las perturbaciones de diferenciación son evaluaciones formales del polinomio local: no autorizan estados de simulación con fracciones negativas en el borde del simplex.

Los archivos `eigenstates.json` y `high_precision_jacobian.json` conservan errores por elemento. Las magnitudes numéricas finales se resumen en el informe de benchmarks. Los errores del Jacobiano conservado incluyen cancelación dimensional; no se interpretan como error físico relativo cuando el elemento exacto es cero.

Esta verificación acredita la derivación local. No acredita captura de shocks, positividad global del integrador, transporte sin error de contacto ni un puerto experimental.

## Reconstrucción candidata C1

1. Recuperar V_i del promedio conservado de cada celda usando la EOS NASA.
2. Usar **el estado local V_i de la celda** como estado de proyección para ambas diferencias. Sin promedio Roe ni aritmético entre celdas.
3. Proyectar V_i−V_{i−1} y V_{i+1}−V_i con L(V_i).
4. Aplicar MC a cada amplitud: cero si cambian de signo; en otro caso signo(a)·min(2|a|,2|b|,|a+b|/2).
5. Volver con R(V_i), reconstruir V_i±s_i/2 y recuperar la especie dependiente por identidad, no por clipping.
6. Contraer conjuntamente toda la pendiente si la trayectoria sale del dominio admisible; no modificar el promedio conservado.
7. Convertir estados de cara a U mediante NASA y usar HLLC Davis sin modificar sus velocidades de onda.

Para una garantía de trayectoria con composición variable, las restricciones de temperatura se escriben p(θ)−Tmin ρ(θ)R(Y(θ))≥0 y Tmax ρ(θ)R(Y(θ))−p(θ)≥0. Son polinomios de grado≤2. Se toma el primer intervalo conectado admisible desde θ=0, junto con ρ>0,p>0,Y≥0, para ambas caras. No se salta a una raíz remota admisible. `admissible_reconstruction.py` verifica este cálculo sobre 2000 pendientes sintéticas. En el control de composición constante NP esas restricciones son lineales; la bisección de contracción utilizada allí es equivalente. Los controles de transporte preservados no activaron contracción de pendientes.

Una contracción altera sólo la representación subcelda y se registra. No es clipping de inventarios. Un promedio inadmisible debe rechazar la etapa; no puede repararse con el limiter. La política global de recuperación GEN1 sigue dependiendo de BLK-002 y no se inventa aquí.

## Fuentes y límite de autoridad

La derivación de este documento procede de los balances y de la EOS contractual, y se verifica computacionalmente. La distinción entre evolución de presión y energía en gas térmicamente perfecto también se estudia en [Fedkiw et al., manuscrito primario](https://physbam.stanford.edu/papers/cam1997-27.pdf). No se adopta su corrección no conservativa. Los coeficientes y su procedencia exacta permanecen en el fixture versionado.

C1 es una alternativa **evaluada**, no una selección contractual automática. Su adjudicación depende del ensayo NP y los controles siguientes.
