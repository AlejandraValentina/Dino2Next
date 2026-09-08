"""Small analytical BCR proposal: no candidate imports or solver campaign."""
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal as D, localcontext, ROUND_CEILING
import json,hashlib,math
import mpmath as mp
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
(ROOT/'artifacts/S06-BCR').mkdir(parents=True,exist_ok=True)
data_path=ROOT/'docs/science/C1.0/datasets/thermo_runtime_continuous_v1.json'
data=json.loads(data_path.read_text());species=data['species']
with localcontext() as ctx:
 ctx.prec=80
 cv_bounds=[F(segment['cv_over_R_lower_exact']) for s in species for branch in ('low','high') for segment in s['global_cv_positivity_certificate'][branch]]
 bF=min(cv_bounds);b=D(bF.numerator)/D(bF.denominator)
 R=[D(data['Ru_J_kmol_K'])/D(s['MW_kg_kmol']) for s in species]
 a_bound=(D(2200)*max(R)*(1+1/b)).sqrt()
 def mixture_r(moles):
  masses=[n*D(s['MW_kg_kmol']) for n,s in zip(moles,species)]
  return sum(m*r for m,r in zip(masses,R))/sum(masses)
 phi=D('.7');product_r=mixture_r([D(0),D('12.5')/phi-D('12.5'),D(47)/phi,D(8),D(9)])
 contact_S=D(100)+a_bound
 shocks=[]
 for pair,rr in [('N2_CO2_isothermal',R[3]),('N2_CO2_thermal',R[3]),('premix_products_thermal',product_r)]:
  for ratio in [2,5,10]:
   ub=(D(ratio-1)*rr*700).sqrt()
   Tupper=D(700)*(b+D(ratio+1)/2)/(b+(1+D(1)/ratio)/2)
   Tlower=D(700)*(D(1)/ratio)**(1/(b+1))
   assert 300<Tlower<=700<Tupper<2200
   shockfront=(rr*700*(D(ratio)+D(ratio+1)/(2*b))).sqrt()
   shocks.append({'pair':pair,'pressure_ratio':ratio,'right_R_J_kg_K':str(rr),'particle_velocity_upper_m_s':str(ub),'right_shock_front_upper_m_s':str(shockfront),'left_fan_T_lower_K':str(Tlower),'right_shock_T_upper_K':str(Tupper),'S_bound_m_s':str(max(ub+a_bound,shockfront))})
 shock_S=max(D(r['S_bound_m_s']) for r in shocks)
 # Upward integer ceilings provide explicit numerical enclosure of the analytic bounds.
 contacts_ceiling=int(contact_S.to_integral_value(rounding=ROUND_CEILING))
 shocks_ceiling=int(shock_S.to_integral_value(rounding=ROUND_CEILING))
 guards=[]
 for family,ns,t,S in [('contacts',[100,200,400],D('.001'),contacts_ceiling),('shocks',[80,160,320,640],D('.0002'),shocks_ceiling)]:
  for n in ns:
   count=int((n*D(S)*t).to_integral_value(rounding=ROUND_CEILING))+4
   g=D(count)/n
   guards.append({'family':family,'N_original_window':n,'dx_m':str(D(1)/n),'guard_cells_each_side':count,'guard_width_m':str(g),'computational_domain_m':[str(-g),str(1+g)],'total_cells':n+2*count,'causal_clearance_m':str(g-D(S)*t),'minimum_stencil_clearance_cells':str((g-D(S)*t)*n)})
 out8={'author':'/root/bcr_science_review','classification':'BCR_PROPOSAL_NOT_ACCEPTANCE','proof_inputs':{'cv_over_R_global_lower_exact':str(bF),'R_species_J_kg_K':list(map(str,R)),'a_global_upper_m_s':str(a_bound),'contacts_S_exact_upper_m_s':str(contact_S),'contacts_S_integer_certificate_m_s':contacts_ceiling,'shocks_S_integer_certificate_m_s':shocks_ceiling},'shocks':shocks,'meshes':guards,
 'sound_speed_proof':'cv/R=sum(Yk Rk (cvk/Rk))/sum(Yk Rk)>=bmin; gamma<=1+1/bmin; R<=maxRk andT<=2200 imply a²<=2200 Rmax(1+1/bmin). Exact rational species Bernstein certificates cover whole domain.',
 'shock_speed_proof':'For leftpL>pR, samezero initialvelocities, p* lies(pR,pL), leftwave rarefaction and rightwave compression. u*²=(p*−pR)(vR−v*) <=(pL−pR)vR; leftfan velocities between0andu*. IndependentlyRH givesSshock²=R_R*T0*(r−1)/(1−Tstar/(r*T0)); insertingTstarupperboundsyieldsSshock²<=R_R*T0*(r+(r+1)/(2b)). Certificateincludesmaximumofthisfrontboundandubound+abound, withoutassumingconvexityfrompositivecvalone.',
 'shock_domain_proof':'dlogT/dlogp=R/cp<=1/(b+1) givesTleft>=700*(pR/pL)^(1/(b+1))>300. Hugoniot e(T)−e(700)+R*T*(1+1/r)/2−R*700*(r+1)/2=0; derivativecv+R*(1+1/r)/2>0 andcv/R>=b boundTstar by700*(b+(r+1)/2)/(b+(1+1/r)/2)<2200. No sampled fans certify these bounds.',
 'required_rules':['Keep originalinterface.5, states,Y,p,u, times, allN/CFLs andsampletimes unchanged. Contacts end.5,.6,.4, neverleaveoriginalwindow.','Uniformdx=1/N on entireextendeddomain; guardcount=ceil(N*S_certificate*t_final)+4; interfaces0and1 remain meshfaces. Constant extension of originalleft/right initialstates, noaddedsource/damping.','Compute every error norm onlyonoriginal[0,1], normalizingbyoriginal1m. Fullextendeddomainledger separately; windowledger mustincludeitsmeasuredfluxes at0and1.','Use independently specified constantendstate boundary flux/stencil; incoming influence cannot reachmeasurementwindow incontinuum givenbuffer. Monitor max|u|+a atallcandidatephysicalstages<=predeclaredS_certificate; violationSETUP_CAUSAL_BOUND_FAILED, neverexpandaftercandidateerrors.','Fourcells arethestencilmargin, notaproofof compact numericaldomain ofdependence: explicitRK+MUSCL numerical support can extendfasterthanPDE characteristics. Preserveadditionalguard-widthcomparison asreference isolationcheck ifrequired; do notclaimzeronumericaltail fromcontinuum bound alone.']}
mp.mp.dps=80
sigma=mp.mpf('.05');k=2*mp.pi
def C(mu,eps=mp.mpf('1e-5')):
 z=k*sigma/2
 return eps*sigma*mp.sqrt(mp.pi)/2*mp.exp(-1j*k*mu-z*z)*(mp.erf((1-mu)/sigma+1j*z)-mp.erf(-mu/sigma+1j*z))
A0=abs(C(mp.mpf('.25')))
# Uniform lower bound for centers inside[0,1]. Atleastone side oflengthsigma isinside.
# Positive cos on |x-mu|<=1/4; subtracttotalGaussian tailoutside1/4.
lower=mp.mpf('1e-5')*sigma*(mp.cos(k*sigma)*mp.sqrt(mp.pi)/2*mp.erf(1)-mp.sqrt(mp.pi)*mp.erfc(mp.mpf('.25')/sigma))
assert lower>0
rows=[];discrete=[]
for j in range(101):
 ct=mp.mpf(j)/100;muplus=mp.mpf('.25')+ct;muminus=mp.mpf('1.75')-ct
 cp=C(muplus);cm=-C(muminus)
 if j<=75:assert abs(cp)>=lower
 if j>=75:assert abs(cm)>=lower
 if j==75:assert cp+cm==0 and cp!=0 and cm!=0
 rows.append({'sample':j,'ct':str(ct),'incident_center':str(muplus),'reflected_center':str(muminus),'incident_phase_observable':j<=75,'reflected_phase_observable':j>=75,'incident_C_abs_over_A0':str(abs(cp)/A0),'reflected_C_abs_over_A0':str(abs(cm)/A0),'total_C_abs_over_A0':str(abs(cp+cm)/A0)})
for n in [200,400,800]:
 edges=np.linspace(0,1,n+1);weights=(np.exp(-2j*np.pi*edges[1:])-np.exp(-2j*np.pi*edges[:-1]))/(-2j*np.pi)
 minobs=float('inf')
 for j in range(101):
  for mu,active in [(.25+j/100,j<=75),(1.75-j/100,j>=75)]:
   if not active:continue
   avg=np.array([1e-5*.05*math.sqrt(math.pi)/2*(math.erf((r-mu)/.05)-math.erf((l-mu)/.05))/(r-l) for l,r in zip(edges[:-1],edges[1:])])
   minobs=min(minobs,abs(np.dot(avg,weights))/float(A0))
 assert minobs>.4
 discrete.append({'N':n,'minimum_observable_reference_abs_over_A0':minobs})
discrete_lower=lower-k/mp.mpf(200)*mp.mpf('1e-5')*sigma*mp.sqrt(mp.pi)
assert discrete_lower>0
out10={'author':'/root/bcr_science_review','classification':'BCR_PROPOSAL_NOT_ACCEPTANCE','A0_incident_initial_continuous_Fourier_abs':str(A0),'uniform_observable_continuous_lower_bound':str(lower),'lower_bound_over_A0':str(lower/A0),'uniform_observable_cell_operator_lower_bound_over_A0':str(discrete_lower/A0),'cell_operator_lower_bound_proof':'|C_h(g)-C(g)|<=k*dx*integral|g|<=2*pi*dx*epsilon*sigma*sqrt(pi); usecoarsestcontractedN200, subtractfromcontinuouslower. Boundappliesallphaseobservablecenters, notsampleminimumonly.','samples':rows,'cell_operator_diagnostic':discrete,
 'definition':{'w_plus':'(p_prime+rho0*c*u)/2 = incident positive Gaussian a','w_minus':'(p_prime-rho0*c*u)/2 = negative reflected Gaussian -b','rho0':'1 kg/m3','c':'sqrt(1.4) m/s','pressure_prime':'p-p0, p0=1Pa','operator':'C_h(w)=sum_i wbar_i * integral(x_i,x_i+1,exp(-2pi*i*x)dx), original[0,1]. Exact reference is SAME operator applied to exactanalytic GaussianCELLAVERAGES, not continuousC used onlyasfixedA0.','A0':'Magnitude ofexactcontinuousinitialincidentFourier coefficient, positive andproportionaltoepsilon; recomputeforfull/half amplitude analytically.','phase_observable':'Incident j0..75; reflectedj75..100; both at75. These intervalsderivefrom pulsecenterinside[0,1], ensuringnonzero signalviaanalyticlowerbound, notcandidateerror.','relative_amplitude':'For eachobservablecomponent: abs(abs(Ccandidate)/abs(Creference)-1)<=.01.','phase':'For eachobservablecomponent: abs(arg(Ccandidate*conj(Creference)))<=pi/N onitscontractedmesh; no inventedphasewhenreferenceundefined orcandidatezero.','absolute_all_samples':'AtALL101samples: abs(Ccandidate-Creference)/A0<=.01 individuallyforincident, reflected, andtotalpressure coefficient. Thisincludesreferencecancellation sample75withoutdivisionbyzero.','inactive_phase':'NOT_OBSERVABLE, neverPASS; absolutecomplexgate stillmandatory.','rigid':'Unchanged.','interpretation_change':'Previous totalpressure relativephase nearincident/reflectedcancellation replacedbyseparatedwave reflectionphase/amplitude; originalbudgetvaluespreserved, totalpressureabsolutecheck retained. No claimtheold undefinedphaseisnowPASS.'}}
# Revised proposal following independent review: retain measurable tails rather
# than declaring their mathematically nonzero phase unobservable by center alone.
threshold=mp.mpf('.01');masks=[];boundary_checks=[]
def discrete_mp(n,mu,precision):
 with mp.workdps(precision):
  sig=mp.mpf('.05');kk=2*mp.pi;eps=mp.mpf('1e-5');total=mp.mpc(0)
  for i in range(n):
   l=mp.mpf(i)/n;r=mp.mpf(i+1)/n
   avg=eps*sig*mp.sqrt(mp.pi)/2*(mp.erf((r-mu)/sig)-mp.erf((l-mu)/sig))*n
   weight=(mp.exp(-1j*kk*r)-mp.exp(-1j*kk*l))/(-1j*kk)
   total+=avg*weight
  return total
for n in [200,400,800]:
 edges=np.linspace(0,1,n+1);weights=(np.exp(-2j*np.pi*edges[1:])-np.exp(-2j*np.pi*edges[:-1]))/(-2j*np.pi)
 plus=[];minus=[];ratios=[]
 for j in range(101):
  rr=[]
  for mu in [.25+j/100,1.75-j/100]:
   avg=np.array([1e-5*.05*math.sqrt(math.pi)/2*(math.erf((r-mu)/.05)-math.erf((l-mu)/.05))/(r-l) for l,r in zip(edges[:-1],edges[1:])])
   rr.append(abs(np.dot(avg,weights))/float(A0))
  if rr[0]>=float(threshold):plus.append(j)
  if rr[1]>=float(threshold):minus.append(j)
  ratios.append(rr)
 assert plus==list(range(84)) and minus==list(range(67,101))
 masks.append({'N':n,'incident_phase_and_relative_amplitude_samples':plus,'reflected_phase_and_relative_amplitude_samples':minus,'all_sample_abs_reference_over_A0':ratios,'minimum_binary64_distance_to_mask_threshold':min(abs(v-.01) for rr in ratios for v in rr)})
 for j in [66,67,83,84]:
  mu=mp.mpf('.25')+mp.mpf(j)/100 if j>=75 else mp.mpf('1.75')-mp.mpf(j)/100
  c80=discrete_mp(n,mu,80);c60=discrete_mp(n,mu,60)
  ratio=abs(c80)/A0
  eligible=ratio>=threshold
  assert eligible==(j in [67,83])
  boundary_checks.append({'N':n,'sample':j,'component':'incident' if j>=75 else 'reflected','reference_abs_over_A0_80digits':str(ratio),'distance_to_threshold':str(abs(ratio-threshold)),'eligible':bool(eligible),'60_vs_80_abs_difference_over_A0':str(abs(c60-c80)/A0)})
out10['proposal_revision']='2; geometric-window-only proposal retained in history/010-geometric-window-v1'
out10['prior_geometric_nonzero_proof_role']='Sufficient nonzero lower bound for central windows only; it is no longer the phase-assessment mask.'
out10['definition']['phase_observable']='At each prescribed N/sample, assess phase and relative amplitude iff abs(C_reference_h)>=.01*A0. The mask is frozen from the qualified analytic reference before candidate execution. Here incident j0..83 and reflected j67..100 for every original N and either amplitude.'
out10['definition']['inactive_phase']='NOT_ASSESSED_BELOW_DECLARED_ABSOLUTE_RESOLUTION for nonzero reference below .01*A0; this is not a claim that its mathematical phase is undefined. Absolute complex gate remains mandatory at every sample. Exact zero reference has undefined phase.'
out10['definition']['interpretation_change']='Characteristic-component phase/amplitude covers tails down to the existing1%A0 absolute amplitude resolution. Threshold derives from that declared physical error budget, never candidate behavior. This expands the initial center-only proposal, without asserting a phase for the canceled total pressure. All101 samples retain absolute gates.'
out10['mask_reference_qualification']='For each coefficient enclose reference error below min(.001,.1*sin(pi/N))*.01*A0; also prove its interval lies wholly on one side of .01*A0 threshold. If not, refine reference arithmetic, never select mask from candidate results. Equality is eligible by definition; exact equality requires exact classification.'
out10['masks']=masks;out10['high_precision_mask_boundary_checks']=boundary_checks
out={'VAL008':out8,'VAL010free':out10,'source_dataset_sha256':hashlib.sha256(data_path.read_bytes()).hexdigest(),'limitations':['Proposalrequiresindependentreview/BCR; no candidatequalification oracceptanceperformed.','Numericalcompact-supportisnotidenticaltoPDEcharacteristiccone; guardisolationwordingscopeexplicit.','Referencecelloperatorqualificationmustboundarithmetic/quadratureerrorbeforeacceptance.']}
(ROOT/'artifacts/S06-BCR/proposal-008-010.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'VAL008_certificate':out8['proof_inputs'],'guard_meshes':guards,'VAL010_A0':str(A0),'VAL010_nonzero_lower':str(lower/A0),'cell_operator':discrete},indent=2))
