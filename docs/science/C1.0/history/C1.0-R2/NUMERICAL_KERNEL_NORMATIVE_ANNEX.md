> **Normative — C1.0-R2** · Status: `SCIENTIFIC_IMPLEMENTATION_BASELINE_FROZEN`
> Revision: explicit H-01/H-02/H-03 adjudication. See the R2 BCRs; R1 history is preserved byte-exact.

# Restored numerical kernel

## NK-001 — local NASA eigenstructure (NUM-003/004)
Source: C10EIGEN, Variables through conserved transformation; adopted by AR002 Exact spatial clause. The C10 candidate selection is not imported.



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


## NK-002 — selected stencil, reconstruction, flux B and failure envelope
Source: AR002, exact spatial and joint admissibility clauses. This supersedes C10 candidate contraction and withdrawn AR001.



Use the C10-derived primitive basis at each **cell-average state**: (rho,u,p,independent chemical mass fractions,independent provenance fractions). NASA a²=cp p/(cv rho), with frozen composition in the homogeneous step. Acoustic amplitudes are (delta p ∓rho a delta u)/(2a²), density material amplitude delta rho−delta p/a², and independent composition/tracer differences. The dependent chemical fraction is N2; the dependent provenance fraction is the last of the separately defined tracer simplex. Dependence is imposed on reconstructed slopes, not by altering stored inventories.

For cell i, J=|p(i+1)−p(i−1)|, W=|p(i+2)−p(i−2)|. Strong compression is W>0, J/min[p(i−1),p(i+1)]>.33 and u(i−1)>u(i+1). Let near(i) be the Boolean union over i−2…i+2. Apply minmod to acoustic amplitudes only where near is true; apply MC to those amplitudes elsewhere and to material amplitudes everywhere. The .33 threshold is inherited from the previously tested flattening family; it is not adjusted to the NP data.

For strong-compression cells chi=max(0,min(1,10[J/W−.75])), otherwise0. Multiply all slopes by1−max[chi(i−1),chi(i),chi(i+1)]. Contract all amplitudes together if either reconstructed face is inadmissible. For a failing full slope, start lo=0, hi=1; perform54 bisections, setting lo=mid only when both faces pass and hi=mid otherwise. Return the explicitly checked admissible lo, then apply flattening and recheck faces. No claim that the NASA upper-temperature set is convex is used. Never clip a face or a cell. Chemical/tracer fractions must be nonnegative, rho/p positive, and EOS temperature valid. The EOS-domain comparison has the established roundoff allowance64 epsilon_machine*2200 K; this does not change any state value.

At an interior face between cells b,c with outer cells a,d, use flux B if near(b) or near(c). At the two external physical boundaries use the prescribed physical coupling flux, not flux B. Define

f*_b = (F_a+F_c)/2 − Abar(a,c)(U_c−2U_b+U_a)/2,

f*_c = (F_b+F_d)/2 − Abar(b,d)(U_d−2U_c+U_b)/2,

F_B = (f*_b+f*_c)/2 − |Abar(a,d)|(U_c−U_b)/2.

The full frozen-mixture NASA secant matrix, its absolute-value action, and species/tracer extension are derived in NUMERICAL_REFERENCE_AND_KERNEL_REPORT.md. The production specification must reproduce those equations, not substitute a constant-gamma Roe matrix. A nonpositive secant acoustic eigenvalue squared is a diagnosed inadmissible secant; return ROE_SECANT_NONHYPERBOLIC with the states and matrix diagnostic, never an artificial positive sound speed or an untested flux. A timestep retry may not cure a state-dependent secant failure; exhausted recovery returns no simulation result. Elsewhere use the exact HLLC Davis formula already specified. One face flux is shared by its adjacent inventories.

The reference for flux B is [Zaide/Roe, original presentation, slides7–9](https://www.cespr.fsu.edu/people/myh/CFD-Conference/Session-7/Zaide_CFDfutures.pdf). The NASA mixture secant is this campaign's derivation, independently verified; the presentation does not establish that extension.

## Joint conservative admissibility

At each FE stage, calculate high flux H and low flux L, where L is first-order local LF with speed max(|uL|+aL,|uR|+aR). At physical coupling boundaries both use the same physical flux. Preserve all physical sources. Test the high-flux FE update. For the second stage also test the actual final SSPRK2 combination with the original accepted state.

If either fails, require the corresponding low-flux FE state and final combination to be admissible. If they are not, return LOW_ORDER_STAGE_INADMISSIBLE_RETRY_DT without changing the accepted state. Otherwise use a **single theta for all faces and all conserved components of that pipe**, Htheta=L+theta(H−L). Bound theta first by nonnegative partial-density/tracer/density linear inequalities; perform54 bisections from checked theta=0 to the linear cap, retaining only explicitly admissible midpoints as the lower endpoint, with the actual EOS checks. The algorithm does not assume convexity of the upper-temperature constraint or claim a global optimum for theta. Recompute the update from the actual returned face fluxes. If roundoff makes that recomputation inadmissible, reduce theta multiplicatively by1−32 epsilon_machine, at most8 times; otherwise return FLUX_LIMIT_ROUND_OFF_RETRY_DT. This changes fluxes, not inventories. Source/admissibility rollback and retry counts are subsequently governed by BLK-002's single global transaction.

This conservative flux-limiting principle follows [Hu, Adams and Shu2013](https://arxiv.org/pdf/1203.1540); their constant-gamma proof is not asserted for the NASA upper-temperature constraint. Every accepted state is checked explicitly. Sum-of-species and tracer ledgers remain separate from nonnegativity checks. No mass, momentum, energy or species may be inserted to make a stage pass.


## NK-003 — full NASA secant action
Source: ARKERNEL, Derivación propia de la matriz secante multispecie, adopted explicitly by AR002.



Con densidades parciales r_k y T_L,T_R, definir barras aritméticas y secantes e_k^d=[e_k(T_R)−e_k(T_L)]/(T_R−T_L). Para temperaturas coincidentes usar cv_k. Sean β=(Σ r̄_k R_k)/(Σ r̄_k e_k^d), ζ_k=T̄R_k−β[e_k(T_L)+e_k(T_R)]/2. La identidad de productos da exactamente:

Δp=βΔ(ρe)+Σζ_kΔr_k.

Las medias Roe de u,H,Y,τ usan pesos√ρ. Con dU=(dρ,dm,dE,dr_k,drτ_j), la presión linealizada es dp=β(dE−ū dm+ū²dρ/2)+Σζ_kdr_k. El producto ĀdU es:

- masa: dm;
- momentum: −ū²dρ+2ūdm+dp;
- energía: −ūH̄dρ+H̄dm+ū(dE+dp);
- especie k: ūdr_k+Ȳ_k(dm−ūdρ);
- tracer j: ūdrτ_j+τ̄_j(dm−ūdρ).

La velocidad acústica secante cumple ā²=Σζ_kȲ_k+β(H̄−ū²/2). Se rechaza ā²≤0, no se reemplaza por un valor positivo artificial. Los vectores acústicos son (1,ū±ā,H̄±ūā,Ȳ,τ̄); el residuo material tras retirar las amplitudes acústicas tiene autovalorū. Esta construcción conserva explícitamente el significado químico y la energía de formación. No es sustituir NASA por gamma constante.


## NK-004 — HLLC Davis away from the selected stencil
Source: C03NUM NUM-003, retained by AR002.



HLLC con estimaciones Davis SL=min(vL−cL,vR−cR), SR=max(vL+cL,vR+cR), c según EOS congelada. S*=[pR−pL+ρLvL(SL−vL)−ρRvR(SR−vR)]/[ρL(SL−vL)−ρR(SR−vR)]. Para lado k: ρ*k=ρk(Sk−vk)/(Sk−S*), E*k=Ek+(S*−vk)[S*+pk/(ρk(Sk−vk))]; Uk*=(ρ*,ρ*S*,ρ*E*,ρ*Yk). F*=Fk+Sk(U*k−Uk). Elegir FL si SL≥0; F*L si SL<0≤S*; F*R si S*<0<SR; FR si SR≤0. Masa de especies y tags lleva los mismos estados donor estrella. No usar otra EOS para star recovery. Casos degenerados/estados inadmisibles requieren NUM-006.

Se selecciona conservación estricta sobre double-flux de energía no conservativa. No se exige presión a precisión de máquina en contacto térmico advectado: error medido y refinamiento son obligatorios. HLLC estacionario sí preserva contacto a roundoff en la suite. Este resultado no prueba shocks multiespecie extremos.


## NK-005 — physical boundary companion

NUM-007/008 are specified in BOUNDARY_CONTRACT.md BC-001…008. The interior AR-002 recipe above remains unchanged. No flux B at physical faces. T3 geometry and W2 do not use an algebraic Cd boundary. NASA roots are domain bounded; the old research 200K bracket is not permitted. TS-001 defines how the joint guard tests actual reaction-mapped SSPRK2 states.
