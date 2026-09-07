> **Normative — C1.0-R2** · Status: `SCIENTIFIC_IMPLEMENTATION_BASELINE_FROZEN`
> Revision: explicit H-01/H-02/H-03 adjudication. See the R2 BCRs; R1 history is preserved byte-exact.

# Restored stage constraints and remaining omission

## ST-001 — shared stage and ledger requirements
Source: C03NUM NUM-002, retained by current C1.



SSPRK2 explícito no partido para todo RHS cuando esté definido: Q1=Qn+dt L(tn,Qn); Qn+1=(Qn+Q1+dt L(tn+dt,Q1))/2. Misma etapa en0D,1D,fuentes y flujos de interfaz. Intercambios integrados dt(F0+F1)/2 compartidos con signos opuestos. No actualizar reservorio con flujo del tubo a otro tiempo. Lie rechazado por orden1; Strang no elegido porque introduce secuencia adicional sin ventaja demostrada para este núcleo. La comparación lineal no certifica fuentes no lineales (C03-BLK-002).


## ST-002 — selected physical reaction law; temporal realization in TS-001
Source: C03PHY PHY-006 SELECTED.



C8H18+12.5O2→8CO2+9H2O. Entrada φ=0.6–0.8; φ=1 o rico fuera de GEN1. No se oxida todo el O2 en mezcla pobre; sobrante permanece. Fuel no consumido permanece químicamente fuel, aunque su etiqueta sea residual. No CO/H2 ni disociación en evolución; dominio y calificación PHY-002.

Al SOC, zona homogénea cerrada: ξmax=min(nfuel,nO2/12.5), kmol, fijo para ese evento. ξ(θ)=ηburn ξmax xb(θ), 0<ηburn≤1. xb=(1−exp(−a z^(n+1)))/(1−exp(−a)), z=(θ−SOC)/Δθ entre0 y1, luego0/1; a>0,n≥0,Δθ>0. Requerir SOC y burn-end en intervalo de puertos cerrados. Actualizar cantidades con coeficientes estequiométricos; resolver T con U y composición nueva. No añadir Q=LHV ξ. Masa elemental conservada; energía química se transforma al cambiar composición.

SOC, duración, a,n,ηburn son inputs de ajuste de presión/heat release sobre CALIBRATION_DATA; no cambios con held-out. Curvas tabuladas de parámetros contra RPM/carga con ejes medidos e interpolación multilineal, sin extrapolación. Ignición prescrita no predice estabilidad de llama. Fuente Wiebe C0.2 y balances; VAL-005/023/025.


## ST-003 — comparison phase and residual scales
Source: C03NUM NUM-009 first paragraph and NUM-010 residual definition. These do not specify periodic per-block reference scales.



Comparar estados en mismo θ=0 mod2π tras todos los eventos del borde de ciclo: inventarios0D, estados de todas las celdas, especies y tags físicos normalizados por cohorte equivalente; no comparar IDs históricos crecientes. Observar además trazas interpoladas conservativamente a la misma grilla angular. Comparar diferencias de periodo1 y periodos2…8; si k>1 cumple y1 no, MULTIPERIODIC_UNSUPPORTED. Warm/cold convergentes a soluciones distintas se reportan como ramas, no se promedian. 
Residual global RQ=Qfin−Qini−Σtransfer_externo−Σsource_físico. Escala SQ=Σdominios|Qini|+∫Σ|flujo_externo|dt+∫Σ|source|dt+Qref; masa Qref=ρamb Vtotal; energía Qref=ρamb Vtotal cv,air Tref, Tref=350K; momentum Qref=ρamb Vtotal camb. Para species usar escala masa total, no dividir por especie ausente. Formación y sentido de signos preservados. Trazadores incluyen ledger separado de relabel, que no cambia masa química. Una suma global buena no reemplaza balance de cada interfaz.

## ST-004 — R2 completion

TIME_EVENT_PERIODICITY_CONTRACT.md TS-001…007 now specifies the exact stage composition, bounds, events and scales. Constants 0.2/0.5, sixteen retries, 1e-6/1e-4, three cycles and 1000-cycle maximum are unchanged.

## ST-005 — restored selected ray algebra, ray algebra used by TS-003

Authority: current C1 NUM-005/006 explicitly selects formation-aware quadratic temperature rays, nonnegative donor/species rays and opposing-force sign preservation; ARTIME states their formation-energy rationale; ARRAY is the matching algebraic research realization, not an authority to select missing source ordering.

For one inventory q=(M,P,E,M_k), current stage derivative qdot=(dM,dP,dE,dM_k), and fixed boundary temperature Tb, define I=E−ΣM_k e_k(Tb), dI=dE−ΣdM_k e_k(Tb). The temperature-ray polynomial coefficients are

c0=2MI−P²;
c1=2(M dI+dM I−P dP);
c2=2 dM dI−dP².

Use c for Tmin and −c for Tmax. The ray is the first positive exit from c0+c1 t+c2 t²≥0, not a remote re-entry root. A tangency that does not leave the set is not an exit. A violated initial margin is an inadmissible stage. With no exit, this bound is +infinity. Use the current C1 factor0.5; retain M>0 and species constraints separately. Formation-inclusive e_k is required, not a positive sensible-energy floor. The EOS is still checked on both FE stages and the final SSPRK2 combination.

For a nonnegative inventory a with negative stage derivative da, its FE depletion bound is a/(−da); if a=0 and da<0 the RHS is inadmissible, never repaired with seed mass. Nonnegative derivative supplies no depletion limit. Current C1 factor0.5 is retained. Summed-outgoing donor accounting and reaction interaction are specified in TS-001/003.

W2 alone obeys u_dot=−b u|u| with b=λw/2. Its FE no-sign-reversal bound is 1/(b|u|) for b|u|>0 and +infinity otherwise, using current C1 factor0.5. Other opposing forces belong in the combined force budget; heat and reaction also affect thermal margins. TS-001 supplies the selected exact-extent/SSPRK2 composition.
