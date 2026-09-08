> **Normative — C1.0-R3** · Status: `SCIENTIFIC_IMPLEMENTATION_BASELINE_FROZEN`

# Executable validation catalogue

COMMON-001: NASA species order is isooctane,O2,N2,CO2,H2O. Dry air molar O2:1,N2:3.76. Premix at phi has C8H18:1,O2:12.5/phi,N2:47/phi. Complete lean products CO2:8,H2O:9,O2:12.5/phi-12.5,N2:47/phi. Convert molar amounts to mass using selected dataset MW; no rounded alternative coefficients. For tests explicitly using constant-gamma gas, all units remain SI and the EOS is a mathematical numerical-verification adapter, not a changed GEN1 chemistry. Canonical initial tags R unless specified. No reported execution PASS is implied by a complete fiche. Runtime NASA5 is DINO2NEXT_NASA5_CONTINUOUS 1.0.0 under BCR-S03-NASA-INVERSION TI-001; RAW identity is separate.

The JSON companion contains the same field values. All required execution remains mandatory during implementation. Experimental acquisition remains independent. No frozen R1 threshold is relaxed.

## VAL-001 — current GEN1 fiche

**objective**: Geometry/NASA identities and EOS round trip

**type**: UNIT

**physics_numerics**: Current C1.0-R3 physics and NUM-001…010, BC-001…008, TS-001…007. Constant-gamma fixtures explicitly test the homogeneous numerical limit, not GEN1 chemical validity.

**initial_state**: B=.052 m,S=.05 m,l=.101 m,Vclear=1.2e-5 m³,VccTDC=3e-4 m³; theta=j*pi/180,j=0..360. T=[350,400,600,999.999999,1000,1000.000001,1600,2200] K; p=[5e4,1e5,1e6,5e6] Pa. Five pure species (mathematical stress), dry air, premix phi=.6,.7,.8 and their complete lean products. Composition definitions COMMON-001.

**geometry**: Crank-slider and zero-dimensional property evaluations.

**domain**: SI units throughout. NASA5 uses frozen dataset, 300–2200 K and 50 kPa–5 MPa; constant-gamma canonical cases use their stated mathematical domain.

**mesh_sequence**: No spatial mesh: one control-volume/ODE inventory.

**dt_sequence**: No time integration; evaluate specified tuple list.

**boundary_states**: Closed, no external mass flux; only sources explicitly named.

**end_condition**: All Cartesian tuples, no time evolution.

**sampling**: Every tuple and angle.

**independent_reference**: Independent Cantera 3.2.0 evaluation of TI-001 derived representation, analytic crank-slider identities and independent high-precision polynomial arithmetic; no candidate imports.

**reference_resolution**: Identical RAW source coefficients plus the independently derived TI-001 integration constants/anchored definition; 80-digit boundary checks. T=1000 uses selected high cp branch and unilateral derivatives. RAW/derived differences are reported separately.

**observable**: V,dV/dtheta,cp,cv,h,u,gamma,R, h-u-RT,cp-cv-R,sumY,T inverse and elemental mass.; h inverse and signed input-energy/enthalpy residual; continuity and one-sided derivatives per TI-004.

**normalization**: cp by cp; h by max(abs(h),cp*T); u by max(abs(u),cv*T); gamma by gamma. Identity conditioning is sum of absolute operands divided by its nonzero physical reference.

**metric**: Maximum timewise absolute error divided by declared scale, plus L1/L2 and observed log2 refinement order. Ledger is final−initial−external flux−physical source, scaled by initial absolute inventory plus absolute throughput plus nonzero reference inventory.

**threshold**: Scaled cp,h,u,gamma errors≤1e-8; T inversion≤1e-8 K; identities≤gamma_128 times conditioning (gamma_n=n*eps/(1-n*eps)); energy inversion residual≤cv*1e-8 K.

**failure**: IMPLEMENTATION_DEFECT for violated algebra/input/ledger; VERIFICATION_FAILURE for failed numerical acceptance; REFERENCE_NOT_QUALIFIED if oracle allocation fails. No tolerance changes or scientific choices by adapter.

**artifacts**: Versioned SI input JSON, candidate/ref raw time series, source and environment hashes, actual mesh/dt, all retries, ledgers, normalized metrics/order, PASS/FAIL with reason. No synthetic run is experimental validation.

## VAL-002 — current GEN1 fiche

**objective**: Closed moving volume reversible work

**type**: NUMERICAL_VERIFICATION

**physics_numerics**: Current C1.0-R3 physics and NUM-001…010, BC-001…008, TS-001…007. Constant-gamma fixtures explicitly test the homogeneous numerical limit, not GEN1 chemical validity.

**initial_state**: gamma=1.4,R=287 J/kg/K,m=.001 kg,T0=600 K,U0=m*R*T0/(gamma-1).

**geometry**: V=.001*(1+.2*sin(2*pi*t)) m³; no passage.

**domain**: SI units throughout. NASA5 uses frozen dataset, 300–2200 K and 50 kPa–5 MPa; constant-gamma canonical cases use their stated mathematical domain.

**mesh_sequence**: No spatial mesh: one control-volume/ODE inventory.

**dt_sequence**: dt=1/[100,200,400,800] s.

**boundary_states**: Closed, no external mass flux; only sources explicitly named.

**end_condition**: t=1 s.

**sampling**: Initial state, every accepted endpoint and final state. Compare against reference evaluated at identical times, never phase shift.

**independent_reference**: U=U0*(V0/V)^(.4), p=.4*U/V.

**reference_resolution**: Analytic reference evaluated independently in float64 with 80-digit arithmetic spot checks. Reference absolute error must be below 10% of the smallest applicable threshold; otherwise REFERENCE_NOT_QUALIFIED.

**observable**: U(t),p(t),m,U+integral p dV.

**normalization**: U0,p0,m0 respectively; work ledger uses same RK pressure/volume stage and independent analytic U difference.

**metric**: Maximum timewise absolute error divided by declared scale, plus L1/L2 and observed log2 refinement order. Ledger is final−initial−external flux−physical source, scaled by initial absolute inventory plus absolute throughput plus nonzero reference inventory.

**threshold**: Finest maximum trajectory relative error≤1e-4; last two refinement orders≥1.8; ledger≤1e-10.

**failure**: IMPLEMENTATION_DEFECT for violated algebra/input/ledger; VERIFICATION_FAILURE for failed numerical acceptance; REFERENCE_NOT_QUALIFIED if oracle allocation fails. No tolerance changes or scientific choices by adapter.

**artifacts**: Versioned SI input JSON, candidate/ref raw time series, source and environment hashes, actual mesh/dt, all retries, ledgers, normalized metrics/order, PASS/FAIL with reason. No synthetic run is experimental validation.

## VAL-003 — current GEN1 fiche

**objective**: Closed thermal relaxation

**type**: NUMERICAL_VERIFICATION

**physics_numerics**: Current C1.0-R3 physics and NUM-001…010, BC-001…008, TS-001…007. Constant-gamma fixtures explicitly test the homogeneous numerical limit, not GEN1 chemical validity.

**initial_state**: m=.001 kg,cv=1000 J/kg/K,R=287 J/kg/K,T0=400 and 800 K,H=hA=2 W/K,Tw=600 K.

**geometry**: V=.001 m³.

**domain**: SI units throughout. NASA5 uses frozen dataset, 300–2200 K and 50 kPa–5 MPa; constant-gamma canonical cases use their stated mathematical domain.

**mesh_sequence**: No spatial mesh: one control-volume/ODE inventory.

**dt_sequence**: dt=[.02,.01,.005,.0025] s.

**boundary_states**: Closed, no external mass flux; only sources explicitly named.

**end_condition**: t=2 s.

**sampling**: Initial state, every accepted endpoint and final state. Compare against reference evaluated at identical times, never phase shift.

**independent_reference**: T=Tw+(T0-Tw)*exp(-H*t/(m*cv)); Q=m*cv*(T-T0).

**reference_resolution**: Analytic reference evaluated independently in float64 with 80-digit arithmetic spot checks. Reference absolute error must be below 10% of the smallest applicable threshold; otherwise REFERENCE_NOT_QUALIFIED.

**observable**: T, signed heat, energy ledger.

**normalization**: Temperature excursion 200 K; heat m*cv*200 J.

**metric**: Maximum timewise absolute error divided by declared scale, plus L1/L2 and observed log2 refinement order. Ledger is final−initial−external flux−physical source, scaled by initial absolute inventory plus absolute throughput plus nonzero reference inventory.

**threshold**: Finest max abs(T-Tref)/200≤1e-5; order≥1.8; ledger≤1e-10.

**failure**: IMPLEMENTATION_DEFECT for violated algebra/input/ledger; VERIFICATION_FAILURE for failed numerical acceptance; REFERENCE_NOT_QUALIFIED if oracle allocation fails. No tolerance changes or scientific choices by adapter.

**artifacts**: Versioned SI input JSON, candidate/ref raw time series, source and environment hashes, actual mesh/dt, all retries, ledgers, normalized metrics/order, PASS/FAIL with reason. No synthetic run is experimental validation.

## VAL-004 — current GEN1 fiche

**objective**: Ideal capacity identity AND half-Riemann boundary classification; these are separate subcases

**type**: NUMERICAL_VERIFICATION

**physics_numerics**: Current C1.0-R3 physics and NUM-001…010, BC-001…008, TS-001…007. Constant-gamma fixtures explicitly test the homogeneous numerical limit, not GEN1 chemical validity.

**initial_state**: A=2e-4 m²; reservoir pR=600000 Pa,T0=[400,700,1500] K, gamma1.4 R287. Ratios pback/pR=[.1,.3,.6,.9,.999,1]. Repeat NASA air/premix phi.7/products phi.7, T0=[700,1000]. Boundary wave tests: pi=200000 Pa,Ti=700 K,Mi=[-2,-.5,0,.5], pR/pi=[.5,1,2], TR=700 K; NASA compositions same plus air→products contact.

**geometry**: One equal-area boundary and ideal convergent nozzle diagnostic, zero time integration; ideal nozzle is not W2 or Cd inversion.

**domain**: SI units throughout. NASA5 uses frozen dataset, 300–2200 K and 50 kPa–5 MPa; constant-gamma canonical cases use their stated mathematical domain.

**mesh_sequence**: No spatial mesh: one control-volume/ODE inventory.

**dt_sequence**: No integration. Algebra roots tolerances BC-005; oracle 80-digit arithmetic, residuals≤1e-12 scaled.

**boundary_states**: Reservoir states as listed; boundary x positive reservoir→pipe. Cases T0=350 K with required sonic T<300 K must fail only if that sonic branch is needed; mild subsonic root above300 remains allowed. Closed Aopen=0 returns wall-only flux. Requested external prescribed Mach+2 fails UNSUPPORTED_SUPERSONIC_INFLOW.

**end_condition**: All tuples; no time integration.

**sampling**: Initial state, every accepted endpoint and final state. Compare against reference evaluated at identical times, never phase shift.

**independent_reference**: Constant gamma: T*=2*T0/(g+1), p*/p0=(2/(g+1))^(g/(g-1)); mdot=A*p0/sqrt(R*T0)*sqrt(2*g/(g-1)*(r^(2/g)-r^((g+1)/g))) for r>r*, critical value otherwise. NASA: independently integrate isentrope h/s and maximize rho*v*A over admissible T using high-precision scalar search; compare BC wave residuals to independent RH/rarefaction evaluations. Wall v=0, transparent zero-flow exact.

**reference_resolution**: Analytic reference evaluated independently in float64 with 80-digit arithmetic spot checks. Reference absolute error must be below 10% of the smallest applicable threshold; otherwise REFERENCE_NOT_QUALIFIED.

**observable**: mdot,h0,sonic status, wave speeds, donor Y/tags and BC failure codes.

**normalization**: Per-observable initial nonzero inventory or explicit scale below; species use total initial mass, energy uses initial sensible cv*T*mass; formation terms remain in ledgers.

**metric**: Maximum timewise absolute error divided by declared scale, plus L1/L2 and observed log2 refinement order. Ledger is final−initial−external flux−physical source, scaled by initial absolute inventory plus absolute throughput plus nonzero reference inventory.

**threshold**: Capacity/h0 error plus qualified oracle error≤0.001 of A*pR/sqrt(R*T0) and cp*T0; sonic residual≤1e-10 scaled. For domain-limited cases exact required failure, not capacity PASS. No implied requirement that a finite pipe instantaneously attains ideal nozzle capacity.

**failure**: IMPLEMENTATION_DEFECT for violated algebra/input/ledger; VERIFICATION_FAILURE for failed numerical acceptance; REFERENCE_NOT_QUALIFIED if oracle allocation fails. No tolerance changes or scientific choices by adapter.

**artifacts**: Versioned SI input JSON, candidate/ref raw time series, source and environment hashes, actual mesh/dt, all retries, ledgers, normalized metrics/order, PASS/FAIL with reason. No synthetic run is experimental validation.

## VAL-005 — current GEN1 fiche

**objective**: Prescribed closed UV combustion without heat-release double counting

**type**: NUMERICAL_VERIFICATION

**physics_numerics**: Current C1.0-R3 physics and NUM-001…010, BC-001…008, TS-001…007. Constant-gamma fixtures explicitly test the homogeneous numerical limit, not GEN1 chemical validity.

**initial_state**: NASA premix phi=[.6,.7,.8],T_SOC=[350,450,600,750] K,p_SOC=[3e5,6e5,1e6] Pa; initial m=pV/(Rmix*T),V=1e-4 m³; eta=[.8,1],Wiebe a=5,n=2, SOC time0,duration=.001 s. Include homogeneous residual mass fraction [0,.2,.4] made from same-phi products.

**geometry**: One closed fixed-volume homogeneous inventory.

**domain**: SI units throughout. NASA5 uses frozen dataset, 300–2200 K and 50 kPa–5 MPa; constant-gamma canonical cases use their stated mathematical domain.

**mesh_sequence**: No spatial mesh: one control-volume/ODE inventory.

**dt_sequence**: dt=.001/[8,16,32,64] s, and one requested step crossing burn end to test event alignment.

**boundary_states**: Closed, no external mass flux; only sources explicitly named.

**end_condition**: t=.001 s, burn end aligned.

**sampling**: Initial state, every accepted endpoint and final state. Compare against reference evaluated at identical times, never phase shift.

**independent_reference**: Independent stoichiometric m_k(t)=m_k0+nu_k M_k eta xi_max xb(t), constant total U; invert independent NASA U(T,m_k). Compute full exact path first: tuples whose exact path exits GEN1 must produce the declared domain failure, not be silently discarded.

**reference_resolution**: Analytic reference evaluated independently in float64 with 80-digit arithmetic spot checks. Reference absolute error must be below 10% of the smallest applicable threshold; otherwise REFERENCE_NOT_QUALIFIED.

**observable**: xi, all chemical/element masses,T,U, terminal extent.

**normalization**: Initial total mass, sensible m*cv(T_SOC)*T_SOC, xi_max; T roundtrip≤1e-8 K as VAL001.

**metric**: Maximum timewise absolute error divided by declared scale, plus L1/L2 and observed log2 refinement order. Ledger is final−initial−external flux−physical source, scaled by initial absolute inventory plus absolute throughput plus nonzero reference inventory.

**threshold**: Admissible tuples: species/energy normalized error≤1e-10 and exact terminal extent within 256 eps*xi_max. Out-of-domain tuples: correct rejection, no truncated burn.

**failure**: IMPLEMENTATION_DEFECT for violated algebra/input/ledger; VERIFICATION_FAILURE for failed numerical acceptance; REFERENCE_NOT_QUALIFIED if oracle allocation fails. No tolerance changes or scientific choices by adapter.

**artifacts**: Versioned SI input JSON, candidate/ref raw time series, source and environment hashes, actual mesh/dt, all retries, ledgers, normalized metrics/order, PASS/FAIL with reason. No synthetic run is experimental validation.

## VAL-006 — current GEN1 fiche

**objective**: Sod shock tube

**type**: NUMERICAL_VERIFICATION

**physics_numerics**: Current C1.0-R3 physics and NUM-001…010, BC-001…008, TS-001…007. Constant-gamma fixtures explicitly test the homogeneous numerical limit, not GEN1 chemical validity.

**initial_state**: gamma1.4,R1; x<.5:rho1,u0,p1; x>.5:rho.125,u0,p.1.

**geometry**: x=[0,1]m,A=1m².

**domain**: SI units throughout. NASA5 uses frozen dataset, 300–2200 K and 50 kPa–5 MPa; constant-gamma canonical cases use their stated mathematical domain.

**mesh_sequence**: Uniform N=[50,100,200,400] on x=[0,1] m, exact cell-average initialization; A=1 m².

**dt_sequence**: CFL=[0.2,0.1,0.05]; spatial assessment at 0.05, temporal separation on finest N. Align to end and sampling times.

**boundary_states**: Constant extrapolation; wave domain of dependence must not reach boundaries.

**end_condition**: t=.2 s.

**sampling**: Initial and final full cell-average fields plus 101 uniformly spaced times using endpoint alignment. Reference averages use Gauss16/32 with exact wave breaks split; no point-value vs average comparison.

**independent_reference**: Exact full Euler Riemann wave solution, independent Clawpack-style pressure root and wave-split cell integration.

**reference_resolution**: Analytic reference evaluated independently in float64 with 80-digit arithmetic spot checks. Reference absolute error must be below 10% of the smallest applicable threshold; otherwise REFERENCE_NOT_QUALIFIED.

**observable**: Cell-average rho,u,p and conservation.

**normalization**: Density scale1 kg/m³; L1=(1/L)sum dx*abs(error).

**metric**: Maximum timewise absolute error divided by declared scale, plus L1/L2 and observed log2 refinement order. Ledger is final−initial−external flux−physical source, scaled by initial absolute inventory plus absolute throughput plus nonzero reference inventory.

**threshold**: N400 L1 rho≤.004375; decreases each level and last-two order≥.5; ledger≤1e-10; rho,p positive.

**failure**: IMPLEMENTATION_DEFECT for violated algebra/input/ledger; VERIFICATION_FAILURE for failed numerical acceptance; REFERENCE_NOT_QUALIFIED if oracle allocation fails. No tolerance changes or scientific choices by adapter.

**artifacts**: Versioned SI input JSON, candidate/ref raw time series, source and environment hashes, actual mesh/dt, all retries, ledgers, normalized metrics/order, PASS/FAIL with reason. No synthetic run is experimental validation.

## VAL-007 — current GEN1 fiche

**objective**: Stationary and advected material contact

**type**: NUMERICAL_VERIFICATION

**physics_numerics**: Current C1.0-R3 physics and NUM-001…010, BC-001…008, TS-001…007. Constant-gamma fixtures explicitly test the homogeneous numerical limit, not GEN1 chemical validity.

**initial_state**: gamma1.4,R1,p=1; rhoL1,rhoR2 atx=.5; u=[0,1] m/s.

**geometry**: x=[0,1]m,A1.

**domain**: SI units throughout. NASA5 uses frozen dataset, 300–2200 K and 50 kPa–5 MPa; constant-gamma canonical cases use their stated mathematical domain.

**mesh_sequence**: N=[100,200,400] uniform.

**dt_sequence**: CFL=[0.2,0.1,0.05]; spatial assessment at 0.05, temporal separation on finest N. Align to end and sampling times.

**boundary_states**: Extrapolation, no wave reaches exterior.

**end_condition**: t=.1 s.

**sampling**: Initial and final full cell-average fields plus 101 uniformly spaced times using endpoint alignment. Reference averages use Gauss16/32 with exact wave breaks split; no point-value vs average comparison.

**independent_reference**: Exact moving step at .5+u*t, exact cut-cell averages.

**reference_resolution**: Analytic reference evaluated independently in float64 with 80-digit arithmetic spot checks. Reference absolute error must be below 10% of the smallest applicable threshold; otherwise REFERENCE_NOT_QUALIFIED.

**observable**: p,u,rho and inventories.

**normalization**: Per-observable initial nonzero inventory or explicit scale below; species use total initial mass, energy uses initial sensible cv*T*mass; formation terms remain in ledgers.

**metric**: Maximum timewise absolute error divided by declared scale, plus L1/L2 and observed log2 refinement order. Ledger is final−initial−external flux−physical source, scaled by initial absolute inventory plus absolute throughput plus nonzero reference inventory.

**threshold**: max abs(p-1),abs(u-u0)≤1e-10; L1rho≤2dx*abs(rhoR-rhoL); stationary state conserved at roundoff; advected error decreases.

**failure**: IMPLEMENTATION_DEFECT for violated algebra/input/ledger; VERIFICATION_FAILURE for failed numerical acceptance; REFERENCE_NOT_QUALIFIED if oracle allocation fails. No tolerance changes or scientific choices by adapter.

**artifacts**: Versioned SI input JSON, candidate/ref raw time series, source and environment hashes, actual mesh/dt, all retries, ledgers, normalized metrics/order, PASS/FAIL with reason. No synthetic run is experimental validation.

## VAL-008 — current GEN1 fiche

**objective**: NASA species/thermal contacts and mixed shocks

**type**: NUMERICAL_VERIFICATION

**physics_numerics**: Current C1.0-R3 physics and NUM-001…010, BC-001…008, TS-001…007. Constant-gamma fixtures explicitly test the homogeneous numerical limit, not GEN1 chemical validity.

**initial_state**: At x=.5, pL=pR=1e5 Pa,u=[0,100,-100]m/s. Pairs: pureN2/CO2 both600K; N2 600K/CO2 1800K; premixphi.7 400K/productsphi.7 1800K. Mixed shock subcases same composition pairs, u=0,T both700K,pR=1e5,pL/pR=[2,5,10].

**geometry**: x=[0,1]m,A1.

**domain**: SI units throughout. NASA5 uses frozen dataset, 300–2200 K and 50 kPa–5 MPa; constant-gamma canonical cases use their stated mathematical domain.

**mesh_sequence**: Contacts N=[100,200,400]; mixed shocks N=[80,160,320,640].

**dt_sequence**: CFL=[0.2,0.1,0.05]; spatial assessment at 0.05, temporal separation on finest N. Align to end and sampling times.

**boundary_states**: Constant end states; if domain of dependence reaches an edge, fail fixture setup rather than changing end time.

**end_condition**: Contacts .001s; shocks .0002s (verify wave travel does not reach boundary).

**sampling**: Initial and final full cell-average fields plus 101 uniformly spaced times using endpoint alignment. Reference averages use Gauss16/32 with exact wave breaks split; no point-value vs average comparison.

**independent_reference**: Contacts exact advected material state cell averages. Mixed shocks independent full NASA Riemann solver: two Hugoniot/rarefaction curves in BC-003 with mirrored left-family sign, common p/u pressure root, separate donor compositions, exact wave sampling. Reference must qualify before use.

**reference_resolution**: Analytic reference evaluated independently in float64 with 80-digit arithmetic spot checks. Reference absolute error must be below 10% of the smallest applicable threshold; otherwise REFERENCE_NOT_QUALIFIED.

**observable**: Contact pressure/velocity oscillations, rhoY, T; shock rho,p,u wave profiles and conservation.

**normalization**: Pressure1e5 Pa; species mass by total mass; density by max initial rho; velocity by initial max sound speed.

**metric**: Maximum timewise absolute error divided by declared scale, plus L1/L2 and observed log2 refinement order. Ledger is final−initial−external flux−physical source, scaled by initial absolute inventory plus absolute throughput plus nonzero reference inventory.

**threshold**: Operational pressure contact L1≤5e-4,Linf≤5e-3; thermal contacts L1≤2e-3,Linf≤2e-2 normalized p by1e5. Mixed shocks: positive admissible states, ledger≤1e-10 and decreasing L1 errors with last-two order≥.5 under general discontinuity requirement; no unrecorded new peak tolerance.

**failure**: IMPLEMENTATION_DEFECT for violated algebra/input/ledger; VERIFICATION_FAILURE for failed numerical acceptance; REFERENCE_NOT_QUALIFIED if oracle allocation fails. No tolerance changes or scientific choices by adapter.

**artifacts**: Versioned SI input JSON, candidate/ref raw time series, source and environment hashes, actual mesh/dt, all retries, ledgers, normalized metrics/order, PASS/FAIL with reason. No synthetic run is experimental validation.

## VAL-009 — current GEN1 fiche

**objective**: Traveling acoustic mode

**type**: NUMERICAL_VERIFICATION

**physics_numerics**: Current C1.0-R3 physics and NUM-001…010, BC-001…008, TS-001…007. Constant-gamma fixtures explicitly test the homogeneous numerical limit, not GEN1 chemical validity.

**initial_state**: gamma1.4,R1,rho=1+eps*cos(2pi*x),p=1+1.4eps*cos(2pi*x),u=sqrt(1.4)*eps*cos(2pi*x),eps=1e-5; repeat eps/2.

**geometry**: x=[0,1]m,A1.

**domain**: SI units throughout. NASA5 uses frozen dataset, 300–2200 K and 50 kPa–5 MPa; constant-gamma canonical cases use their stated mathematical domain.

**mesh_sequence**: Uniform N=[50,100,200,400] on x=[0,1] m, exact cell-average initialization; A=1 m².

**dt_sequence**: CFL=[0.2,0.1,0.05]; spatial assessment at 0.05, temporal separation on finest N. Align to end and sampling times.

**boundary_states**: Periodic both ends.

**end_condition**: t=.25 s.

**sampling**: Initial and final full cell-average fields plus 101 uniformly spaced times using endpoint alignment. Reference averages use Gauss16/32 with exact wave breaks split; no point-value vs average comparison.

**independent_reference**: Linear acoustic translation x−sqrt(1.4)*t, exact cell-average sinusoid. Nonlinear remainder checked by halving eps.

**reference_resolution**: Analytic reference evaluated independently in float64 with 80-digit arithmetic spot checks. Reference absolute error must be below 10% of the smallest applicable threshold; otherwise REFERENCE_NOT_QUALIFIED.

**observable**: Complex pressure Fourier mode k=2pi; density/velocity L1,L2.

**normalization**: Mode amplitude eps*gamma, phase radians; linear/nonlinear difference accounted, not subtracted to improve result.

**metric**: Maximum timewise absolute error divided by declared scale, plus L1/L2 and observed log2 refinement order. Ledger is final−initial−external flux−physical source, scaled by initial absolute inventory plus absolute throughput plus nonzero reference inventory.

**threshold**: Relative Fourier amplitude error≤2*(2pi/N)^2+10eps; phase≤pi/N; smooth order≥1.8 above nonlinear/roundoff floor.

**failure**: IMPLEMENTATION_DEFECT for violated algebra/input/ledger; VERIFICATION_FAILURE for failed numerical acceptance; REFERENCE_NOT_QUALIFIED if oracle allocation fails. No tolerance changes or scientific choices by adapter.

**artifacts**: Versioned SI input JSON, candidate/ref raw time series, source and environment hashes, actual mesh/dt, all retries, ledgers, normalized metrics/order, PASS/FAIL with reason. No synthetic run is experimental validation.

## VAL-010 — current GEN1 fiche

**objective**: Separate rigid standing-wave and free-end pulse reflection operators

**type**: NUMERICAL_VERIFICATION

**physics_numerics**: Current C1.0-R3 physics and NUM-001…010, BC-001…008, TS-001…007. Constant-gamma fixtures explicitly test the homogeneous numerical limit, not GEN1 chemical validity.

**initial_state**: gamma1.4,R1,rho0=p0=1,c=sqrt(1.4),eps=1e-5. Rigid: p=1+eps*cos(pi*x),rho=1+eps*cos(pi*x)/c²,u=0. Free: g(x)=eps*exp(-((x-.25)/.05)^2),p=1+g,rho=1+g/c²,u=g/c.

**geometry**: x=[0,1]m,A1.

**domain**: SI units throughout. NASA5 uses frozen dataset, 300–2200 K and 50 kPa–5 MPa; constant-gamma canonical cases use their stated mathematical domain.

**mesh_sequence**: N=[200,400,800] uniform.

**dt_sequence**: CFL=[0.2,0.1,0.05]; spatial assessment at 0.05, temporal separation on finest N. Align to end and sampling times.

**boundary_states**: Rigid: u=0 both ends. Free: right p-prime=0 pressure-release acoustic boundary, left zero incoming acoustic invariant; these are linear canonical BC tests distinct from nonlinear reservoir capacity.

**end_condition**: Rigid t=.6s; free t=1/c s.

**sampling**: Initial and final full cell-average fields plus 101 uniformly spaced times using endpoint alignment. Reference averages use Gauss16/32 with exact wave breaks split; no point-value vs average comparison.

**independent_reference**: Rigid exact linear p-prime=eps*cos(pi*x)*cos(pi*c*t),u=eps/c*sin(pi*x)*sin(pi*c*t). Free p-prime=g(x-c*t)-g(2-x-c*t),u=(g(x-c*t)+g(2-x-c*t))/c. Exact Gaussian cell integrals via erf.

**reference_resolution**: Analytic reference evaluated independently in float64 with 80-digit arithmetic spot checks. Reference absolute error must be below 10% of the smallest applicable threshold; otherwise REFERENCE_NOT_QUALIFIED.

**observable**: Rigid pressure L1; free full reflected spatial waveform Fourier coefficient C=sum dx*p-prime*exp(-2pi i*x) with exact cell-integral operator; pulse peak/time recorded separately as diagnostics.

**normalization**: Rigid eps; free complex reference coefficient, phase radians. Peak diagnostics are not a replacement acceptance operator.

**metric**: Maximum timewise absolute error divided by declared scale, plus L1/L2 and observed log2 refinement order. Ledger is final−initial−external flux−physical source, scaled by initial absolute inventory plus absolute throughput plus nonzero reference inventory.

**threshold**: Rigid L1(p-p_ref)/eps≤.01 atN800; free abs(abs(C)/abs(Cref)-1)≤.01 and abs(arg(C/Cref))≤pi/N. Cref must be nonzero; cannot use peak-time difference as Fourier phase. Repeat eps/2 to bound nonlinear remainder.

**failure**: IMPLEMENTATION_DEFECT for violated algebra/input/ledger; VERIFICATION_FAILURE for failed numerical acceptance; REFERENCE_NOT_QUALIFIED if oracle allocation fails. No tolerance changes or scientific choices by adapter.

**artifacts**: Versioned SI input JSON, candidate/ref raw time series, source and environment hashes, actual mesh/dt, all retries, ledgers, normalized metrics/order, PASS/FAIL with reason. No synthetic run is experimental validation.

## VAL-011 — current GEN1 fiche

**objective**: Rest and smooth quasi-1D nozzle balance

**type**: NUMERICAL_VERIFICATION

**physics_numerics**: Current C1.0-R3 physics and NUM-001…010, BC-001…008, TS-001…007. Constant-gamma fixtures explicitly test the homogeneous numerical limit, not GEN1 chemical validity.

**initial_state**: gamma1.4,R1: rest rho=p=1,u0. Smooth p0=T01,Mthroat=.3 atx=.5; subsonic area-Mach solution.

**geometry**: A=1+.4*(x-.5)^2 m² on x0..1.

**domain**: SI units throughout. NASA5 uses frozen dataset, 300–2200 K and 50 kPa–5 MPa; constant-gamma canonical cases use their stated mathematical domain.

**mesh_sequence**: Uniform N=[50,100,200,400] on x=[0,1] m, exact cell-average initialization; A=1 m².

**dt_sequence**: CFL=[0.2,0.1,0.05]; spatial assessment at 0.05, temporal separation on finest N. Align to end and sampling times.

**boundary_states**: Rest rigid walls; smooth exact stationary states at exterior ghost positions.

**end_condition**: Rest .2s; smooth .3s.

**sampling**: Initial and final full cell-average fields plus 101 uniformly spaced times using endpoint alignment. Reference averages use Gauss16/32 with exact wave breaks split; no point-value vs average comparison.

**independent_reference**: Area-Mach A/A*=1/M*[2/(g+1)*(1+(g-1)M²/2)]^((g+1)/(2*(g-1))); choose subsonic root connected to M=.3 atminA. T=1/(1+.2M²),p=T^3.5,rho=p/T,u=M*sqrt(1.4T). Initialize exact area-weighted averages; independently integrate with Gauss16/32.

**reference_resolution**: Analytic reference evaluated independently in float64 with 80-digit arithmetic spot checks. Reference absolute error must be below 10% of the smallest applicable threshold; otherwise REFERENCE_NOT_QUALIFIED.

**observable**: rho,u,p,AF+pDeltaA equilibrium and source ledger.

**normalization**: rho reference1,pressure1,velocitysqrt1.4.

**metric**: Maximum timewise absolute error divided by declared scale, plus L1/L2 and observed log2 refinement order. Ledger is final−initial−external flux−physical source, scaled by initial absolute inventory plus absolute throughput plus nonzero reference inventory.

**threshold**: Rest max abs(u),abs(p-1)≤1e-10; smooth N400 L1rho≤2e-6 and order≥1.8; ledger with physical geometric force≤1e-10.

**failure**: IMPLEMENTATION_DEFECT for violated algebra/input/ledger; VERIFICATION_FAILURE for failed numerical acceptance; REFERENCE_NOT_QUALIFIED if oracle allocation fails. No tolerance changes or scientific choices by adapter.

**artifacts**: Versioned SI input JSON, candidate/ref raw time series, source and environment hashes, actual mesh/dt, all retries, ledgers, normalized metrics/order, PASS/FAIL with reason. No synthetic run is experimental validation.

## VAL-013 — current GEN1 fiche

**objective**: Coupled T3/W2; original fixtures preserved, final reference execution pending

**type**: NUMERICAL_VERIFICATION

**physics_numerics**: Current C1.0-R3 physics and NUM-001…010, BC-001…008, TS-001…007. Constant-gamma fixtures explicitly test the homogeneous numerical limit, not GEN1 chemical validity.

**initial_state**: Left finite V=2e-4 m³,p=130000 Pa,T700,air; right infinite p120000,T700,air. Pipe p,Y cosine blend: b(x)=(1-cos(pi*x/L))/2, p=(1-b)pL+b*pR,Y=(1-b)YL+b*YR; T700,u0; rho fromEOS. All initial originsR except incoming externalgasX.

**geometry**: Persistent pipe L=.2m,A=2e-4m²; W2 support[.15,.2]m,w20m^-1; characterized lambda .04 forward,.06 reverse; no other sources. VAL020 window fraction sin²(pi*(thetaDeg-120)/120) for120..240deg,zero otherwise; other face fullyopen. Other fixtures fullyopen.

**domain**: SI units throughout. NASA5 uses frozen dataset, 300–2200 K and 50 kPa–5 MPa; constant-gamma canonical cases use their stated mathematical domain.

**mesh_sequence**: Candidate N=[80,160,320,640,1280] uniform; reference N=[320,640,1280,2560]. Further refinement only during authorized implementation verification if reference budget fails; no result inferred here.

**dt_sequence**: Candidate CFL .2,.1,.05; reference A CFL .05,.025,.0125 with classical RK4; reference B DOP853 rtol1e-11,atol1e-13 in normalized state, maxstep constrained by CFL .05,.025,.0125 and source bounds. Both align exactly to events. Spatial error at smallest CFL; compare fixed-mesh temporal sequences independently.

**boundary_states**: BC-001…007 on both ends, orientation left→right; true donor. Finite volumes use exact stage state; infinite state fixed. No mass removal at window closure.

**end_condition**: t=.0005s; VAL016 also report original0..2ms separately, extension2..4ms observes reversal.

**sampling**: Every1e-6s, exact endpoint alignment; all interface ledgers every accepted step. Compare initial through final waveforms without shift/filter.

**independent_reference**: Independent reference family A: fifth-order finite-difference WENO-JS conservative flux splitting, global LLF speed max(abs(u)+a), RK4 with own BC scalar solves; family B: piecewise-constant Godunov finite volumes with an independent exact NASA Riemann flux and DOP853 integration. BC wave roots use an independent implementation, never candidate boundary code. Same physical equations and input, no shared candidate reconstruction, flux B or SSPRK2. Both must qualify; a nonqualified reference is not truth.

**reference_resolution**: Need three asymptotic spatial levels with observed order>.5; error estimate 2*last_difference/(2^p-1) plus separately estimated temporal/root/roundoff terms. Cross-family difference must be within sum of estimates and each estimate≤.0001 physical scale. No Richardson waveform correction. If not satisfied REFERENCE_NOT_QUALIFIED.

**observable**: All endpoint reservoirs p,T,m,U,Y; p_window_in atx=.15 using one-sided point reconstruction; face mdot,integrated mass/energy/species,passageinventory,work and phase.

**normalization**: p*=120000Pa,T*=700K,m*=rho_air(120000,700)*Vleft(0),E*=m*cv_air(700)*700,mdot*=rho_air*a_air*2e-4; chemical/origin fractions1; accumulatedmass m*,energyE*,workE*. Phase: earliest unique isolated extremum or interior zero crossing of each reference signal, select once before candidate; nonunique feature uses waveform only, phase marked NOT_APPLICABLE_NONUNIQUE, not automatic pass.

**metric**: Maximum timewise absolute error divided by declared scale, plus L1/L2 and observed log2 refinement order. Ledger is final−initial−external flux−physical source, scaled by initial absolute inventory plus absolute throughput plus nonzero reference inventory.

**threshold**: Per primary observable normalized waveform Linf+reference error≤.001; reference≤.0001,isolated temporalerror≤.0001; phase≤4e-6s; ledger≤1e-10; strictdomain/simplex. Every primary observable passes separately.

**failure**: IMPLEMENTATION_DEFECT for violated algebra/input/ledger; VERIFICATION_FAILURE for failed numerical acceptance; REFERENCE_NOT_QUALIFIED if oracle allocation fails. No tolerance changes or scientific choices by adapter.

**artifacts**: Versioned SI input JSON, candidate/ref raw time series, source and environment hashes, actual mesh/dt, all retries, ledgers, normalized metrics/order, PASS/FAIL with reason. No synthetic run is experimental validation.

## VAL-014 — current GEN1 fiche

**objective**: Coupled T3/W2; original fixtures preserved, final reference execution pending

**type**: NUMERICAL_VERIFICATION

**physics_numerics**: Current C1.0-R3 physics and NUM-001…010, BC-001…008, TS-001…007. Constant-gamma fixtures explicitly test the homogeneous numerical limit, not GEN1 chemical validity.

**initial_state**: Left cylinder B=S=.04m,l=.08m,Vclear8e-6m³,RPM6000,theta0=pi/2,p120000,T700,air; right infinitep120000,T700,air. Pipe p,Y cosine blend: b(x)=(1-cos(pi*x/L))/2, p=(1-b)pL+b*pR,Y=(1-b)YL+b*YR; T700,u0; rho fromEOS. All initial originsR except incoming externalgasX.

**geometry**: Persistent pipe L=.2m,A=2e-4m²; W2 support[.15,.2]m,w20m^-1; characterized lambda .04 forward,.06 reverse; no other sources. VAL020 window fraction sin²(pi*(thetaDeg-120)/120) for120..240deg,zero otherwise; other face fullyopen. Other fixtures fullyopen.

**domain**: SI units throughout. NASA5 uses frozen dataset, 300–2200 K and 50 kPa–5 MPa; constant-gamma canonical cases use their stated mathematical domain.

**mesh_sequence**: Candidate N=[80,160,320,640,1280] uniform; reference N=[320,640,1280,2560]. Further refinement only during authorized implementation verification if reference budget fails; no result inferred here.

**dt_sequence**: Candidate CFL .2,.1,.05; reference A CFL .05,.025,.0125 with classical RK4; reference B DOP853 rtol1e-11,atol1e-13 in normalized state, maxstep constrained by CFL .05,.025,.0125 and source bounds. Both align exactly to events. Spatial error at smallest CFL; compare fixed-mesh temporal sequences independently.

**boundary_states**: BC-001…007 on both ends, orientation left→right; true donor. Finite volumes use exact stage state; infinite state fixed. No mass removal at window closure.

**end_condition**: t=.002s; VAL016 also report original0..2ms separately, extension2..4ms observes reversal.

**sampling**: Every1e-6s, exact endpoint alignment; all interface ledgers every accepted step. Compare initial through final waveforms without shift/filter.

**independent_reference**: Independent reference family A: fifth-order finite-difference WENO-JS conservative flux splitting, global LLF speed max(abs(u)+a), RK4 with own BC scalar solves; family B: piecewise-constant Godunov finite volumes with an independent exact NASA Riemann flux and DOP853 integration. BC wave roots use an independent implementation, never candidate boundary code. Same physical equations and input, no shared candidate reconstruction, flux B or SSPRK2. Both must qualify; a nonqualified reference is not truth.

**reference_resolution**: Need three asymptotic spatial levels with observed order>.5; error estimate 2*last_difference/(2^p-1) plus separately estimated temporal/root/roundoff terms. Cross-family difference must be within sum of estimates and each estimate≤.0001 physical scale. No Richardson waveform correction. If not satisfied REFERENCE_NOT_QUALIFIED.

**observable**: All endpoint reservoirs p,T,m,U,Y; p_window_in atx=.15 using one-sided point reconstruction; face mdot,integrated mass/energy/species,passageinventory,work and phase.

**normalization**: p*=120000Pa,T*=700K,m*=rho_air(120000,700)*Vleft(0),E*=m*cv_air(700)*700,mdot*=rho_air*a_air*2e-4; chemical/origin fractions1; accumulatedmass m*,energyE*,workE*. Phase: earliest unique isolated extremum or interior zero crossing of each reference signal, select once before candidate; nonunique feature uses waveform only, phase marked NOT_APPLICABLE_NONUNIQUE, not automatic pass.

**metric**: Maximum timewise absolute error divided by declared scale, plus L1/L2 and observed log2 refinement order. Ledger is final−initial−external flux−physical source, scaled by initial absolute inventory plus absolute throughput plus nonzero reference inventory.

**threshold**: Per primary observable normalized waveform Linf+reference error≤.001; reference≤.0001,isolated temporalerror≤.0001; phase≤4e-6s; ledger≤1e-10; strictdomain/simplex. Every primary observable passes separately.

**failure**: IMPLEMENTATION_DEFECT for violated algebra/input/ledger; VERIFICATION_FAILURE for failed numerical acceptance; REFERENCE_NOT_QUALIFIED if oracle allocation fails. No tolerance changes or scientific choices by adapter.

**artifacts**: Versioned SI input JSON, candidate/ref raw time series, source and environment hashes, actual mesh/dt, all retries, ledgers, normalized metrics/order, PASS/FAIL with reason. No synthetic run is experimental validation.

## VAL-016 — current GEN1 fiche

**objective**: Coupled T3/W2; original fixtures preserved, final reference execution pending

**type**: NUMERICAL_VERIFICATION

**physics_numerics**: Current C1.0-R3 physics and NUM-001…010, BC-001…008, TS-001…007. Constant-gamma fixtures explicitly test the homogeneous numerical limit, not GEN1 chemical validity.

**initial_state**: Left V(t)=2e-4*(1-.08*sin(pi*t/.002)^2)m³,p120000,T700,premixphi.7; right infinitep120000,T700,productsphi.7. Pipe p,Y cosine blend: b(x)=(1-cos(pi*x/L))/2, p=(1-b)pL+b*pR,Y=(1-b)YL+b*YR; T700,u0; rho fromEOS. All initial originsR except incoming externalgasX.

**geometry**: Persistent pipe L=.2m,A=2e-4m²; W2 support[.15,.2]m,w20m^-1; characterized lambda .04 forward,.06 reverse; no other sources. VAL020 window fraction sin²(pi*(thetaDeg-120)/120) for120..240deg,zero otherwise; other face fullyopen. Other fixtures fullyopen.

**domain**: SI units throughout. NASA5 uses frozen dataset, 300–2200 K and 50 kPa–5 MPa; constant-gamma canonical cases use their stated mathematical domain.

**mesh_sequence**: Candidate N=[80,160,320,640,1280] uniform; reference N=[320,640,1280,2560]. Further refinement only during authorized implementation verification if reference budget fails; no result inferred here.

**dt_sequence**: Candidate CFL .2,.1,.05; reference A CFL .05,.025,.0125 with classical RK4; reference B DOP853 rtol1e-11,atol1e-13 in normalized state, maxstep constrained by CFL .05,.025,.0125 and source bounds. Both align exactly to events. Spatial error at smallest CFL; compare fixed-mesh temporal sequences independently.

**boundary_states**: BC-001…007 on both ends, orientation left→right; true donor. Finite volumes use exact stage state; infinite state fixed. No mass removal at window closure.

**end_condition**: t=.004s; VAL016 also report original0..2ms separately, extension2..4ms observes reversal.

**sampling**: Every1e-6s, exact endpoint alignment; all interface ledgers every accepted step. Compare initial through final waveforms without shift/filter.

**independent_reference**: Independent reference family A: fifth-order finite-difference WENO-JS conservative flux splitting, global LLF speed max(abs(u)+a), RK4 with own BC scalar solves; family B: piecewise-constant Godunov finite volumes with an independent exact NASA Riemann flux and DOP853 integration. BC wave roots use an independent implementation, never candidate boundary code. Same physical equations and input, no shared candidate reconstruction, flux B or SSPRK2. Both must qualify; a nonqualified reference is not truth.

**reference_resolution**: Need three asymptotic spatial levels with observed order>.5; error estimate 2*last_difference/(2^p-1) plus separately estimated temporal/root/roundoff terms. Cross-family difference must be within sum of estimates and each estimate≤.0001 physical scale. No Richardson waveform correction. If not satisfied REFERENCE_NOT_QUALIFIED.

**observable**: All endpoint reservoirs p,T,m,U,Y; p_window_in atx=.15 using one-sided point reconstruction; face mdot,integrated mass/energy/species,passageinventory,work and phase.

**normalization**: p*=120000Pa,T*=700K,m*=rho_air(120000,700)*Vleft(0),E*=m*cv_air(700)*700,mdot*=rho_air*a_air*2e-4; chemical/origin fractions1; accumulatedmass m*,energyE*,workE*. Phase: earliest unique isolated extremum or interior zero crossing of each reference signal, select once before candidate; nonunique feature uses waveform only, phase marked NOT_APPLICABLE_NONUNIQUE, not automatic pass.

**metric**: Maximum timewise absolute error divided by declared scale, plus L1/L2 and observed log2 refinement order. Ledger is final−initial−external flux−physical source, scaled by initial absolute inventory plus absolute throughput plus nonzero reference inventory.

**threshold**: Per primary observable normalized waveform Linf+reference error≤.001; reference≤.0001,isolated temporalerror≤.0001; phase≤4e-6s; ledger≤1e-10; strictdomain/simplex. Every primary observable passes separately.

**failure**: IMPLEMENTATION_DEFECT for violated algebra/input/ledger; VERIFICATION_FAILURE for failed numerical acceptance; REFERENCE_NOT_QUALIFIED if oracle allocation fails. No tolerance changes or scientific choices by adapter.

**artifacts**: Versioned SI input JSON, candidate/ref raw time series, source and environment hashes, actual mesh/dt, all retries, ledgers, normalized metrics/order, PASS/FAIL with reason. No synthetic run is experimental validation.

## VAL-018 — current GEN1 fiche

**objective**: Passive momentum sources plus heat, separately and together

**type**: NUMERICAL_VERIFICATION

**physics_numerics**: Current C1.0-R3 physics and NUM-001…010, BC-001…008, TS-001…007. Constant-gamma fixtures explicitly test the homogeneous numerical limit, not GEN1 chemical validity.

**initial_state**: gamma1.4,R287,rho1 kg/m³,T0=700K,u0=[-100,100]m/s. b=[0,2]m^-1,Hvol=[0,2000]W/m³/K,Tw600K; all four combinations. E=rho*(cv*T+u²/2).

**geometry**: Uniform parcel V=.001m³; equivalent window w20m^-1,lambda.2 givesb2; fixed geometry, no flux divergence.

**domain**: SI units throughout. NASA5 uses frozen dataset, 300–2200 K and 50 kPa–5 MPa; constant-gamma canonical cases use their stated mathematical domain.

**mesh_sequence**: No spatial mesh: one control-volume/ODE inventory.

**dt_sequence**: Uniform dt=t_end/[40,80,160,320], clipped exactly at stated events; TS-003 can further reduce steps. Preserve requested and actual steps.

**boundary_states**: Closed, no external mass flux; only sources explicitly named.

**end_condition**: t=.01s.

**sampling**: Initial state, every accepted endpoint and final state. Compare against reference evaluated at identical times, never phase shift.

**independent_reference**: du/dt=-b*u*abs(u); u=u0/(1+b*abs(u0)*t). dT/dt=Hvol/(rho*cv)*(Tw-T)+b*abs(u)^3/cv. Independent integrating factor: T=Tw+(T0-Tw)e^-kt+integral0..t e^-k(t-s)*b*abs(u(s))^3/cv ds, adaptive quadrature. Total energy derivative=Hvol*(Tw-T)/rho.

**reference_resolution**: Independent adaptive Gauss-Kronrod integral rtol1e-12,atol1e-10K,checked by halving tolerances; analytic u exact.

**observable**: u,T,E,heat ledger,entropy production due to drag b*abs(u)^3/T.

**normalization**: Velocity100m/s,T700K,E=rho*cv*700 plus kinetic,entropy cv; referencequadrature error≤.0001 scales.

**metric**: Maximum timewise absolute error divided by declared scale, plus L1/L2 and observed log2 refinement order. Ledger is final−initial−external flux−physical source, scaled by initial absolute inventory plus absolute throughput plus nonzero reference inventory.

**threshold**: All errors plus reference≤.001 respective physical scales; energyledger≤1e-10; dragentropy nonnegative within roundoff. Source separationmust reproduce b0/H0 limits.

**failure**: IMPLEMENTATION_DEFECT for violated algebra/input/ledger; VERIFICATION_FAILURE for failed numerical acceptance; REFERENCE_NOT_QUALIFIED if oracle allocation fails. No tolerance changes or scientific choices by adapter.

**artifacts**: Versioned SI input JSON, candidate/ref raw time series, source and environment hashes, actual mesh/dt, all retries, ledgers, normalized metrics/order, PASS/FAIL with reason. No synthetic run is experimental validation.

## VAL-020 — current GEN1 fiche

**objective**: Coupled T3/W2; original fixtures preserved, final reference execution pending

**type**: NUMERICAL_VERIFICATION

**physics_numerics**: Current C1.0-R3 physics and NUM-001…010, BC-001…008, TS-001…007. Constant-gamma fixtures explicitly test the homogeneous numerical limit, not GEN1 chemical validity.

**initial_state**: Left cylinder asVAL014; right finite crankcase Vcc=1.5e-4-Apiston*s(theta), bothp120000,T700,air,theta0=pi/2,RPM6000. Pipe p,Y cosine blend: b(x)=(1-cos(pi*x/L))/2, p=(1-b)pL+b*pR,Y=(1-b)YL+b*YR; T700,u0; rho fromEOS. All initial originsR except incoming externalgasX.

**geometry**: Persistent pipe L=.2m,A=2e-4m²; W2 support[.15,.2]m,w20m^-1; characterized lambda .04 forward,.06 reverse; no other sources. VAL020 window fraction sin²(pi*(thetaDeg-120)/120) for120..240deg,zero otherwise; other face fullyopen. Other fixtures fullyopen.

**domain**: SI units throughout. NASA5 uses frozen dataset, 300–2200 K and 50 kPa–5 MPa; constant-gamma canonical cases use their stated mathematical domain.

**mesh_sequence**: Candidate N=[80,160,320,640,1280] uniform; reference N=[320,640,1280,2560]. Further refinement only during authorized implementation verification if reference budget fails; no result inferred here.

**dt_sequence**: Candidate CFL .2,.1,.05; reference A CFL .05,.025,.0125 with classical RK4; reference B DOP853 rtol1e-11,atol1e-13 in normalized state, maxstep constrained by CFL .05,.025,.0125 and source bounds. Both align exactly to events. Spatial error at smallest CFL; compare fixed-mesh temporal sequences independently.

**boundary_states**: BC-001…007 on both ends, orientation left→right; true donor. Finite volumes use exact stage state; infinite state fixed. No mass removal at window closure.

**end_condition**: t=.005s; VAL016 also report original0..2ms separately, extension2..4ms observes reversal.

**sampling**: Every1e-6s, exact endpoint alignment; all interface ledgers every accepted step. Compare initial through final waveforms without shift/filter.

**independent_reference**: Independent reference family A: fifth-order finite-difference WENO-JS conservative flux splitting, global LLF speed max(abs(u)+a), RK4 with own BC scalar solves; family B: piecewise-constant Godunov finite volumes with an independent exact NASA Riemann flux and DOP853 integration. BC wave roots use an independent implementation, never candidate boundary code. Same physical equations and input, no shared candidate reconstruction, flux B or SSPRK2. Both must qualify; a nonqualified reference is not truth.

**reference_resolution**: Need three asymptotic spatial levels with observed order>.5; error estimate 2*last_difference/(2^p-1) plus separately estimated temporal/root/roundoff terms. Cross-family difference must be within sum of estimates and each estimate≤.0001 physical scale. No Richardson waveform correction. If not satisfied REFERENCE_NOT_QUALIFIED.

**observable**: All endpoint reservoirs p,T,m,U,Y; p_window_in atx=.15 using one-sided point reconstruction; face mdot,integrated mass/energy/species,passageinventory,work and phase.

**normalization**: p*=120000Pa,T*=700K,m*=rho_air(120000,700)*Vleft(0),E*=m*cv_air(700)*700,mdot*=rho_air*a_air*2e-4; chemical/origin fractions1; accumulatedmass m*,energyE*,workE*. Phase: earliest unique isolated extremum or interior zero crossing of each reference signal, select once before candidate; nonunique feature uses waveform only, phase marked NOT_APPLICABLE_NONUNIQUE, not automatic pass.

**metric**: Maximum timewise absolute error divided by declared scale, plus L1/L2 and observed log2 refinement order. Ledger is final−initial−external flux−physical source, scaled by initial absolute inventory plus absolute throughput plus nonzero reference inventory.

**threshold**: Per primary observable normalized waveform Linf+reference error≤.001; reference≤.0001,isolated temporalerror≤.0001; phase≤4e-6s; ledger≤1e-10; strictdomain/simplex. Every primary observable passes separately.

**failure**: IMPLEMENTATION_DEFECT for violated algebra/input/ledger; VERIFICATION_FAILURE for failed numerical acceptance; REFERENCE_NOT_QUALIFIED if oracle allocation fails. No tolerance changes or scientific choices by adapter.

**artifacts**: Versioned SI input JSON, candidate/ref raw time series, source and environment hashes, actual mesh/dt, all retries, ledgers, normalized metrics/order, PASS/FAIL with reason. No synthetic run is experimental validation.

## VAL-021 — current GEN1 fiche

**objective**: Deterministic periodicity detector coupon AND mandatory later full-kernel sensitivity

**type**: NUMERICAL_VERIFICATION

**physics_numerics**: Current C1.0-R3 physics and NUM-001…010, BC-001…008, TS-001…007. Constant-gamma fixtures explicitly test the homogeneous numerical limit, not GEN1 chemical validity.

**initial_state**: Dimensionless normalized persistent-state vector with one coordinate for each TS006 block plus two independent cell coordinates: x_n=xstar+a*r^n, xstar=1, a=[.01,-.01,.005,-.005] applied separately and one species-partition perturbation(+.005,-.005). r=.5 and .9. Full-state scale mapping TS006; ambient120000Pa,350K,air,Vcmax1e-4,Vccmax2e-4,Vd9e-5m³,pipeA2e-4.

**geometry**: No PDE geometry for detector coupon; normalized vector embedded in admissible inventory reference states.

**domain**: SI units throughout. NASA5 uses frozen dataset, 300–2200 K and 50 kPa–5 MPa; constant-gamma canonical cases use their stated mathematical domain.

**mesh_sequence**: No spatial mesh: one control-volume/ODE inventory.

**dt_sequence**: One exact cycle-map step; no physical timestep.

**boundary_states**: No external flow. Future full-kernel qualification runs the exact VAL020 coupled configuration from cold/warm/high/low/composition perturbations plus GEN1 configured validation point, preserving model parameters.

**end_condition**: At most1000cycles, sampled theta0 postevents.

**sampling**: Every cycle and each counter. No phase fitting.

**independent_reference**: Exact recurrence xstar+a*r^n. Outputs normalized y_j=1+.1*(x_n-xstar) for every output; exact output residual known. Multiperiod controls: twocoordinates(1+.01cos(2pi*n/k),1+.01sin(2pi*n/k)),k2..8. Slow failure x_n=1+.01*.9999^n with output alternating+.001/-.001 to ensure no period1 nor lagqualification of state at1000. Multipleattractors use two constant admissiblexstar=1 and1.01 with outputconsistentdifferences.

**reference_resolution**: Closed-form exact recurrences with 80-digit checks at threshold crossings.

**observable**: D1,D2..D8,eachoutputdefect,consecutivecounters,terminationcode,coldwarmcrossdefect.

**normalization**: TS006 fixed scales; coupon written directly in normalized units.

**metric**: Maximum timewise absolute error divided by declared scale, plus L1/L2 and observed log2 refinement order. Ledger is final−initial−external flux−physical source, scaled by initial absolute inventory plus absolute throughput plus nonzero reference inventory.

**threshold**: TS006 thresholds1e-6/1e-4,threecomparisons,max1000 unchanged. Exact recurrence computes firstqualifyingcycle; implementationmustmatch cycle andcodeexactly. Higherperiodk detectedonlyafterthreepasses,neverperiod1. Constantdifferentattractorsmustfailcrosscheck. This tests semantics, not proves full-engine sensitivity.

**failure**: IMPLEMENTATION_DEFECT for violated algebra/input/ledger; VERIFICATION_FAILURE for failed numerical acceptance; REFERENCE_NOT_QUALIFIED if oracle allocation fails. No tolerance changes or scientific choices by adapter.

**artifacts**: Coupon raw sequences/expected earliest stops and failures. Additionally MANDATORY_VERIFICATION_DURING_IMPLEMENTATION: full-kernel state→output sensitivity from distinct initial states, compare to continued converged state and refinement; output residual must stay≤1e-4 fixed scales after declared qualification. Failure blocks NUMERICALLY_VERIFIED_GEN1 and needs BCR, not a changed threshold.

## VAL-022 — current GEN1 fiche

**objective**: Motored experimental validation

**type**: EXPERIMENTAL_VALIDATION

**physics_numerics**: Current C1.0-R3 physics and NUM-001…010, BC-001…008, TS-001…007. Constant-gamma fixtures explicitly test the homogeneous numerical limit, not GEN1 chemical validity.

**initial_state**: Measured hardware/setpoints per EXR001/002; no invented numeric dataset. Required completegeometry,ambientp/T,wallT,gas/fuelcomposition,ignitionwhenfired,RPM/load,rawpressure/torque/flow andcovariance.

**geometry**: MeasuredGEN1hardwareSI;componentcharacterizationseparatefromenginecalibration.

**domain**: SI units throughout. NASA5 uses frozen dataset, 300–2200 K and 50 kPa–5 MPa; constant-gamma canonical cases use their stated mathematical domain.

**mesh_sequence**: Permeasuredgeometry successivefactor2refinementatleastthreelevels untilVAL027 numericalerror allocation qualifies; recordactualmeshes.

**dt_sequence**: Successivefactor2time refinementonfixedfinemesh; encoderphaseacquisition.1degand.05deg integrationbiascheck perEXR.

**boundary_states**: Measuredambient/thermal/inlet/outletstates and their covariance,not arbitrarydefaults.

**end_condition**: AcquireEXR001/002 prescribedcampaign; no executionclaimuntildataavailable.

**sampling**: Initially200consecutivecycles,threeindependentsessions,EXR extensionrule; retainraw individualcyclesandensembleoperator. Nine normalizedspeeds and fourthrottlefractions for motored perVF022.

**independent_reference**: Independentmeasurementoperatorandrawuncertaintycontract EXR001/002 in EXPERIMENTAL_DATA_CONTRACT.md; VAL022 motoredpressureandwork,025validationpartition,026heldoutpartition.

**reference_resolution**: Measurementcovarianceincludingcalibration,filter,encoder,TDC,repeatability andgeometry; independent numericalerrorbudget required.

**observable**: EXRprespecifiedobservables;025/026 pressure,work/braketorquewithvalidFMEP,flow,temperatures.

**normalization**: UseEXRmeasurementcovariance andrank-aware statistic; never simulatorfitresidualas measurementuncertainty.

**metric**: Maximum timewise absolute error divided by declared scale, plus L1/L2 and observed log2 refinement order. Ledger is final−initial−external flux−physical source, scaled by initial absolute inventory plus absolute throughput plus nonzero reference inventory.

**threshold**: EXR95%covariance-compatibleacceptance,Holmalpha.05,metrologicalcapability3; no tuningonvalidationorheldout. MissingdataREQUIRES_EXPERIMENTAL_DATA,not scientificPASS.

**failure**: REQUIRES_EXPERIMENTAL_DATA if acquisitionmissing;qualifiedfailedcomparisonblocksphysical/predictiveclaim; nevermodifyheldoutmodel.

**artifacts**: Versioned SI input JSON, candidate/ref raw time series, source and environment hashes, actual mesh/dt, all retries, ledgers, normalized metrics/order, PASS/FAIL with reason. No synthetic run is experimental validation.

## VAL-023 — current GEN1 fiche

**objective**: Reaction-limit and event/source composition negative tests

**type**: NUMERICAL_VERIFICATION

**physics_numerics**: Current C1.0-R3 physics and NUM-001…010, BC-001…008, TS-001…007. Constant-gamma fixtures explicitly test the homogeneous numerical limit, not GEN1 chemical validity.

**initial_state**: Use VAL005 exact mixtures/volume; eta=[.8,1],a5,n2,duration1ms. Positive tuples and out-of-domain cases individually classified by independent exactUV path. Add negativeinputs eta1.01,negativefuelmass,openportduringSOC; exactfailcodes required.

**geometry**: Same closed homogeneous volume asVAL005, no heat/work.

**domain**: SI units throughout. NASA5 uses frozen dataset, 300–2200 K and 50 kPa–5 MPa; constant-gamma canonical cases use their stated mathematical domain.

**mesh_sequence**: No spatial mesh: one control-volume/ODE inventory.

**dt_sequence**: dtrequested=[.0007,.00035,.000175,.0000875]s; endpointalignment required.

**boundary_states**: Allportsclosed; explicitinvalidcaseopensportduringburnandmustfailconfigurationvalidation.

**end_condition**: Burnstart0,end.001s,requestdt=.0007s to crossendthenalign.

**sampling**: Initial state, every accepted endpoint and final state. Compare against reference evaluated at identical times, never phase shift.

**independent_reference**: Independent exactextent and stoichiometric masses asVAL005; compare at allnodes inclSOC/end. Repeateta1 exactlimitingreactantzero.

**reference_resolution**: Analytic reference evaluated independently in float64 with 80-digit arithmetic spot checks. Reference absolute error must be below 10% of the smallest applicable threshold; otherwise REFERENCE_NOT_QUALIFIED.

**observable**: No negative chemical inventory; terminalxi,sourceledger,eventcountandretryrollback.

**normalization**: Same asVAL005; all chemical masses byinitialtotalmass,notdepletedreactant.

**metric**: Maximum timewise absolute error divided by declared scale, plus L1/L2 and observed log2 refinement order. Ledger is final−initial−external flux−physical source, scaled by initial absolute inventory plus absolute throughput plus nonzero reference inventory.

**threshold**: Exactextentwithin256eps*xi_max; chemistry/energyledger≤1e-10; inadmissibleinput never best-effort. One committed SOC and burnend; rejectedtrials do notduplicate reaction.

**failure**: IMPLEMENTATION_DEFECT for violated algebra/input/ledger; VERIFICATION_FAILURE for failed numerical acceptance; REFERENCE_NOT_QUALIFIED if oracle allocation fails. No tolerance changes or scientific choices by adapter.

**artifacts**: Versioned SI input JSON, candidate/ref raw time series, source and environment hashes, actual mesh/dt, all retries, ledgers, normalized metrics/order, PASS/FAIL with reason. No synthetic run is experimental validation.

## VAL-024 — current GEN1 fiche

**objective**: Distributed/local passive loss and station semantics

**type**: NUMERICAL_VERIFICATION

**physics_numerics**: Current C1.0-R3 physics and NUM-001…010, BC-001…008, TS-001…007. Constant-gamma fixtures explicitly test the homogeneous numerical limit, not GEN1 chemical validity.

**initial_state**: gamma1.4,R287,rho1,T700,u0=[-100,100]. Laminar shear mu=2e-5Pa*s,Dh=.001m,Re=abs(u)*rho*Dh/mu (initial5000 notlaminar: use u0=[-.01,.01] forlaminar subcase only). Distributedlaminar rate c=32mu/(rho*Dh²). LocalK=.2,w20 givesb2; use±100 forK. Mapquerytests: characterizedlambda points .04/.06 bydirection,opening1,station metadata frozen; wrongstation andoutofdomain explicitfailure.

**geometry**: UniformfixedparcelV.001m³; sourcesonly. LocalKregiondisjointfromW2; test eachseparately.

**domain**: SI units throughout. NASA5 uses frozen dataset, 300–2200 K and 50 kPa–5 MPa; constant-gamma canonical cases use their stated mathematical domain.

**mesh_sequence**: No spatial mesh: one control-volume/ODE inventory.

**dt_sequence**: Uniform dt=t_end/[40,80,160,320], clipped exactly at stated events; TS-003 can further reduce steps. Preserve requested and actual steps.

**boundary_states**: Closedparcel; no momentum pressuregradient. Incoming/outgoingstatesnotpartofthissource-onlytest.

**end_condition**: t=.01s.

**sampling**: Initial state, every accepted endpoint and final state. Compare against reference evaluated at identical times, never phase shift.

**independent_reference**: Laminar u=u0 exp(-c*t), Econstant,T=T0+(u0²-u²)/(2cv). LocalK u=u0/(1+b*abs(u0)*t),sameenergy. Churchill analyticlowRe fD=64/Re evaluatedindependently; no test claiming highReexactlaminar.

**reference_resolution**: Analytic reference evaluated independently in float64 with 80-digit arithmetic spot checks. Reference absolute error must be below 10% of the smallest applicable threshold; otherwise REFERENCE_NOT_QUALIFIED.

**observable**: Sign,noopatu0,kinetictointernal,entropy,lambda lookup andstationerrors.

**normalization**: u0 magnitude(nonzero),cv*T0 andtotalmass; entropycv. Foru0zero requireexactzero source.

**metric**: Maximum timewise absolute error divided by declared scale, plus L1/L2 and observed log2 refinement order. Ledger is final−initial−external flux−physical source, scaled by initial absolute inventory plus absolute throughput plus nonzero reference inventory.

**threshold**: Sign/passivity/zeroenergyledger≤1e-10; analytic source errors≤.001 under VAL018 sharedsource gate,order≥1.8. Directlaminarformula agrees64/Re within1e-10 relative for Re=[.01,.1,1,10]. No extraunknown K inferred fromCd.

**failure**: IMPLEMENTATION_DEFECT for violated algebra/input/ledger; VERIFICATION_FAILURE for failed numerical acceptance; REFERENCE_NOT_QUALIFIED if oracle allocation fails. No tolerance changes or scientific choices by adapter.

**artifacts**: Versioned SI input JSON, candidate/ref raw time series, source and environment hashes, actual mesh/dt, all retries, ledgers, normalized metrics/order, PASS/FAIL with reason. No synthetic run is experimental validation.

## VAL-025 — current GEN1 fiche

**objective**: Fired full-engine validation

**type**: EXPERIMENTAL_VALIDATION

**physics_numerics**: Current C1.0-R3 physics and NUM-001…010, BC-001…008, TS-001…007. Constant-gamma fixtures explicitly test the homogeneous numerical limit, not GEN1 chemical validity.

**initial_state**: Measured hardware/setpoints per EXR001/002; no invented numeric dataset. Required completegeometry,ambientp/T,wallT,gas/fuelcomposition,ignitionwhenfired,RPM/load,rawpressure/torque/flow andcovariance.

**geometry**: MeasuredGEN1hardwareSI;componentcharacterizationseparatefromenginecalibration.

**domain**: SI units throughout. NASA5 uses frozen dataset, 300–2200 K and 50 kPa–5 MPa; constant-gamma canonical cases use their stated mathematical domain.

**mesh_sequence**: Permeasuredgeometry successivefactor2refinementatleastthreelevels untilVAL027 numericalerror allocation qualifies; recordactualmeshes.

**dt_sequence**: Successivefactor2time refinementonfixedfinemesh; encoderphaseacquisition.1degand.05deg integrationbiascheck perEXR.

**boundary_states**: Measuredambient/thermal/inlet/outletstates and their covariance,not arbitrarydefaults.

**end_condition**: AcquireEXR001/002 prescribedcampaign; no executionclaimuntildataavailable.

**sampling**: Initially200consecutivecycles,threeindependentsessions,EXR extensionrule; retainraw individualcyclesandensembleoperator. Nine normalizedspeeds and fourthrottlefractions for motored perVF022.

**independent_reference**: Independentmeasurementoperatorandrawuncertaintycontract EXR001/002 in EXPERIMENTAL_DATA_CONTRACT.md; VAL022 motoredpressureandwork,025validationpartition,026heldoutpartition.

**reference_resolution**: Measurementcovarianceincludingcalibration,filter,encoder,TDC,repeatability andgeometry; independent numericalerrorbudget required.

**observable**: EXRprespecifiedobservables;025/026 pressure,work/braketorquewithvalidFMEP,flow,temperatures.

**normalization**: UseEXRmeasurementcovariance andrank-aware statistic; never simulatorfitresidualas measurementuncertainty.

**metric**: Maximum timewise absolute error divided by declared scale, plus L1/L2 and observed log2 refinement order. Ledger is final−initial−external flux−physical source, scaled by initial absolute inventory plus absolute throughput plus nonzero reference inventory.

**threshold**: EXR95%covariance-compatibleacceptance,Holmalpha.05,metrologicalcapability3; no tuningonvalidationorheldout. MissingdataREQUIRES_EXPERIMENTAL_DATA,not scientificPASS.

**failure**: REQUIRES_EXPERIMENTAL_DATA if acquisitionmissing;qualifiedfailedcomparisonblocksphysical/predictiveclaim; nevermodifyheldoutmodel.

**artifacts**: Versioned SI input JSON, candidate/ref raw time series, source and environment hashes, actual mesh/dt, all retries, ledgers, normalized metrics/order, PASS/FAIL with reason. No synthetic run is experimental validation.

## VAL-026 — current GEN1 fiche

**objective**: Held-out predictive validation

**type**: EXPERIMENTAL_VALIDATION

**physics_numerics**: Current C1.0-R3 physics and NUM-001…010, BC-001…008, TS-001…007. Constant-gamma fixtures explicitly test the homogeneous numerical limit, not GEN1 chemical validity.

**initial_state**: Measured hardware/setpoints per EXR001/002; no invented numeric dataset. Required completegeometry,ambientp/T,wallT,gas/fuelcomposition,ignitionwhenfired,RPM/load,rawpressure/torque/flow andcovariance.

**geometry**: MeasuredGEN1hardwareSI;componentcharacterizationseparatefromenginecalibration.

**domain**: SI units throughout. NASA5 uses frozen dataset, 300–2200 K and 50 kPa–5 MPa; constant-gamma canonical cases use their stated mathematical domain.

**mesh_sequence**: Permeasuredgeometry successivefactor2refinementatleastthreelevels untilVAL027 numericalerror allocation qualifies; recordactualmeshes.

**dt_sequence**: Successivefactor2time refinementonfixedfinemesh; encoderphaseacquisition.1degand.05deg integrationbiascheck perEXR.

**boundary_states**: Measuredambient/thermal/inlet/outletstates and their covariance,not arbitrarydefaults.

**end_condition**: AcquireEXR001/002 prescribedcampaign; no executionclaimuntildataavailable.

**sampling**: Initially200consecutivecycles,threeindependentsessions,EXR extensionrule; retainraw individualcyclesandensembleoperator. Nine normalizedspeeds and fourthrottlefractions for motored perVF022.

**independent_reference**: Independentmeasurementoperatorandrawuncertaintycontract EXR001/002 in EXPERIMENTAL_DATA_CONTRACT.md; VAL022 motoredpressureandwork,025validationpartition,026heldoutpartition.

**reference_resolution**: Measurementcovarianceincludingcalibration,filter,encoder,TDC,repeatability andgeometry; independent numericalerrorbudget required.

**observable**: EXRprespecifiedobservables;025/026 pressure,work/braketorquewithvalidFMEP,flow,temperatures.

**normalization**: UseEXRmeasurementcovariance andrank-aware statistic; never simulatorfitresidualas measurementuncertainty.

**metric**: Maximum timewise absolute error divided by declared scale, plus L1/L2 and observed log2 refinement order. Ledger is final−initial−external flux−physical source, scaled by initial absolute inventory plus absolute throughput plus nonzero reference inventory.

**threshold**: EXR95%covariance-compatibleacceptance,Holmalpha.05,metrologicalcapability3; no tuningonvalidationorheldout. MissingdataREQUIRES_EXPERIMENTAL_DATA,not scientificPASS.

**failure**: REQUIRES_EXPERIMENTAL_DATA if acquisitionmissing;qualifiedfailedcomparisonblocksphysical/predictiveclaim; nevermodifyheldoutmodel.

**artifacts**: Versioned SI input JSON, candidate/ref raw time series, source and environment hashes, actual mesh/dt, all retries, ledgers, normalized metrics/order, PASS/FAIL with reason. No synthetic run is experimental validation.

## VAL-027 — current GEN1 fiche

**objective**: Isolate temporal order at fixed semidiscrete mesh

**type**: NUMERICAL_VERIFICATION

**physics_numerics**: Current C1.0-R3 physics and NUM-001…010, BC-001…008, TS-001…007. Constant-gamma fixtures explicitly test the homogeneous numerical limit, not GEN1 chemical validity.

**initial_state**: gamma1.4,R1,rho=1+.01sin(2pi*x),u=.3,p1; periodic.

**geometry**: x0..1,A1,N40fixed.

**domain**: SI units throughout. NASA5 uses frozen dataset, 300–2200 K and 50 kPa–5 MPa; constant-gamma canonical cases use their stated mathematical domain.

**mesh_sequence**: N40fixed; no spatialrefinementin temporal estimate.

**dt_sequence**: dt=[.002,.001,.0005,.00025]s.

**boundary_states**: Periodicbothends.

**end_condition**: t=.1s.

**sampling**: Initial state, every accepted endpoint and final state. Compare against reference evaluated at identical times, never phase shift.

**independent_reference**: DOP853 independent integrator applied to exactly same selected semidiscrete RHS; this is temporal reference only, not independent spatial truth. rtol2.3e-14,atol1e-16,maxstep.0001; crosscheckrtol1e-13,atol1e-15.

**reference_resolution**: Twoindependent integrator tolerance runs; discrepancy≤1e-11. SpatialqualificationseparateVAL006…011.

**observable**: rho L1temporal error,fullstate norms,order.

**normalization**: rho1kg/m³,L1meanoverlength1.

**metric**: Maximum timewise absolute error divided by declared scale, plus L1/L2 and observed log2 refinement order. Ledger is final−initial−external flux−physical source, scaled by initial absolute inventory plus absolute throughput plus nonzero reference inventory.

**threshold**: FinestL1≤1e-10,order1.8..2.2 firsttwopairs,referenceerror≤1e-11. If errorfloorpreventsordermeasurementreportREFERENCE_NOT_QUALIFIED,notPASS.

**failure**: IMPLEMENTATION_DEFECT for violated algebra/input/ledger; VERIFICATION_FAILURE for failed numerical acceptance; REFERENCE_NOT_QUALIFIED if oracle allocation fails. No tolerance changes or scientific choices by adapter.

**artifacts**: Versioned SI input JSON, candidate/ref raw time series, source and environment hashes, actual mesh/dt, all retries, ledgers, normalized metrics/order, PASS/FAIL with reason. No synthetic run is experimental validation.

## VAL-028 — current GEN1 fiche

**objective**: Two-zone mixing,birth,merge,re-entry exact limits

**type**: NUMERICAL_VERIFICATION

**physics_numerics**: Current C1.0-R3 physics and NUM-001…010, BC-001…008, TS-001…007. Constant-gamma fixtures explicitly test the homogeneous numerical limit, not GEN1 chemical validity.

**initial_state**: cp1000,R287,cv713; mixingmA.0003,mB.0007kg,TA400,TB900K,p1e5Pa,HA120J,HB630J,tau.01s. Birthsubcase A0,B.001kg,Tboth700,p1e5,mdotintoA=.01kg/s,tau.01. Reentrysubcase initiallysameemptyA,B.001,T700,externalmdotintoB=.01kg/s taggedX; existingBtagR.

**geometry**: MixV=R*(mA*TA+mB*TB)/1e5 fixed. Birth/reentryV(t)=R*700*(.001+.01*t)/1e5; exact movingvolume dictatedbyconstantp/T; no heat.

**domain**: SI units throughout. NASA5 uses frozen dataset, 300–2200 K and 50 kPa–5 MPa; constant-gamma canonical cases use their stated mathematical domain.

**mesh_sequence**: No spatial mesh: one control-volume/ODE inventory.

**dt_sequence**: dt=.02/[40,80,160,320]s; merge event .01 exactlyaligned; mixing rate1/tau.

**boundary_states**: Mixclosed; birthprescribedincomingenthalpycp*700andairwithF1tag toA; reentrysameairbutXtagtoB. Theseareclosurecoupons,not replacementsfor reversing T3 VAL016.

**end_condition**: Mix/birth/reentryt=.02s; mergesubcaseat.01s,thencontinuehomogeneous.

**sampling**: Initial state, every accepted endpoint and final state. Compare against reference evaluated at identical times, never phase shift.

**independent_reference**: Mix mA=mA0exp(-t/tau),HA=HA0exp(-t/tau),mB=mtot-mA,HB=Htot-HA. BirthmA=.01*tau*(1-exp(-t/tau)),mB=.001+.01*t-mA,H_z=cp700m_z. ReentryA0,B=.001+.01t,H_B=cp700mB; Xmass=.01t,Rmass.001. Merge sumsM/species/tags,U=sumH-pV andsolvesT=U/(mtotcv); no deleted inventory.

**reference_resolution**: Analyticmass/enthalpy and stoichiometric ledger withhighprecisionpointchecks. NASA algebra companion evaluates PHY003 volume/energyidentities for Cartesian mA=[1e-6,3e-4],mB=[1e-5,7e-4],TA=[400,700],TB=[700,1000],p1e5,air/products; HfromNASA,V=sumRmT/p,externalrate0,exchange tau.01; identitynormalizedresidual≤1e-11 asrestored.

**observable**: mA,mB,HA,HB,p,T,chemical/origininventory,Vdot,Udot,birthdonorcomposition,mergeconservation.

**normalization**: Mixmass.001kg,enthalpy750J;birth/reentrymass.0012kg,enthalpy840J,pressure1e5Pa. All species/originsuseparentmassscale.

**metric**: Maximum timewise absolute error divided by declared scale, plus L1/L2 and observed log2 refinement order. Ledger is final−initial−external flux−physical source, scaled by initial absolute inventory plus absolute throughput plus nonzero reference inventory.

**threshold**: Finestmaxrelative≤1e-6,order≥1.8 where nonzero discretizationerror; ledger≤1e-10; algebraiczero-errorcasesrequire256epsscaledagreement,no spuriousorderfit. Birthfromexactzerowithoutseed, reentrytrueXdonor, mergeconservesU.

**failure**: IMPLEMENTATION_DEFECT for violated algebra/input/ledger; VERIFICATION_FAILURE for failed numerical acceptance; REFERENCE_NOT_QUALIFIED if oracle allocation fails. No tolerance changes or scientific choices by adapter.

**artifacts**: Versioned SI input JSON, candidate/ref raw time series, source and environment hashes, actual mesh/dt, all retries, ledgers, normalized metrics/order, PASS/FAIL with reason. No synthetic run is experimental validation.
