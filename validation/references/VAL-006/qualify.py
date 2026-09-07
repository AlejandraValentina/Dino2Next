"""Independent reference qualification across five canonical fixtures; no candidate imports."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import math
import platform
import numpy as np
import mpmath as mp

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'validation/references'
mp.mp.dps=80

def load(number):
    spec=importlib.util.spec_from_file_location('reference_'+number,BASE/('VAL-'+number)/'reference.py')
    obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def qualify():
    result={}
    def record(number,checks):
        result[number]={'classification':'NUMERICAL_FIXTURE_ONLY','status':'REFERENCE_QUALIFIED',
          'fixture':'VAL-'+number,'candidate_imports':False,'precision_digits':80,
          'environment':{'python':platform.python_version(),'numpy':np.__version__,'mpmath':mp.__version__},
          'reference_sha256':digest(BASE/('VAL-'+number)/'reference.py'),
          'qualification_sha256':digest(Path(__file__)),
          'fixture_source_sha256':digest(ROOT/'docs/science/C1.0/EXECUTABLE_VALIDATION_FIXTURES.json'),
          'checks':checks,'meaning':'Reference qualification only; candidate numerical acceptance remains separate.'}
    g=mp.mpf('1.4');c=mp.sqrt(g)
    def qualify_fourier_operator(ref):
        edges=np.linspace(0,1,51);values=np.cos(2*np.pi*(edges[:-1]+edges[1:])/2)*1e-5
        exact=mp.mpc(0)
        for l,r,value in zip(edges[:-1],edges[1:],values):
            exact+=mp.mpf(float(value))*(mp.exp(-2j*mp.pi*mp.mpf(float(r)))-mp.exp(-2j*mp.pi*mp.mpf(float(l))))/(-2j*mp.pi)
        error=abs(mp.mpc(ref.fourier_coefficient(edges,values))-exact)
        assert error<mp.mpf('1e-18')
        return str(error)
    def wave(p,rho,pk):
        return (p-pk)*mp.sqrt(2/((g+1)*rho)/(p+(g-1)/(g+1)*pk)) if p>pk else 2*mp.sqrt(g*pk/rho)/(g-1)*((p/pk)**((g-1)/(2*g))-1)
    pstar=mp.findroot(lambda p:wave(p,1,1)+wave(p,mp.mpf('.125'),mp.mpf('.1')),(mp.mpf('.2'),mp.mpf('.4')))
    ustar=(wave(pstar,mp.mpf('.125'),mp.mpf('.1'))-wave(pstar,1,1))/2
    ref=load('006');pressure_error=abs(mp.mpf(ref.PSTAR)-pstar);assert pressure_error<mp.mpf('1e-14')
    cs=c*pstar**((g-1)/(2*g));shock=mp.sqrt(g*mp.mpf('.1')/mp.mpf('.125'))*mp.sqrt((g+1)/(2*g)*pstar/mp.mpf('.1')+(g-1)/(2*g))
    breaks=[-c,ustar-cs,ustar,shock]
    def sod(x,t):
        z=(x-mp.mpf('.5'))/t
        if z<=-c:return [mp.mpf(1),mp.mpf(0),mp.mpf(1)]
        if z<ustar-cs:
            ac=2/(g+1)*(c-(g-1)*z/2)
            return [(ac/c)**(2/(g-1)),2/(g+1)*(c+z),(ac/c)**(2*g/(g-1))]
        if z<=ustar:return [pstar**(1/g),ustar,pstar]
        if z<shock:
            ratio=pstar/mp.mpf('.1');beta=(g-1)/(g+1)
            return [mp.mpf('.125')*(ratio+beta)/(beta*ratio+1),ustar,pstar]
        return [mp.mpf('.125'),mp.mpf(0),mp.mpf('.1')]
    max_quad=0.;max_mp=mp.mpf(0)
    for t in [.002,.1,.2]:
        # Off-grid cells deliberately cross each exact shock/fan/contact break.
        centers=[.5+float(v)*t for v in breaks]
        for center in centers:
            edges=np.array([center-.0031,center+.0017]);a=ref.cell_averages(edges,t,16);b=ref.cell_averages(edges,t,32)
            max_quad=max(max_quad,float(np.max(np.abs(a['conserved']-b['conserved']))))
            l,r=map(lambda x:mp.mpf(str(x)),edges);tm=mp.mpf(str(t));cuts=[l,*sorted(mp.mpf('.5')+v*tm for v in breaks if l<mp.mpf('.5')+v*tm<r),r]
            for j,key in enumerate(['rho','u','p']):
                exact=mp.fsum(mp.quad(lambda x:sod(x,tm)[j],[aa,bb]) for aa,bb in zip(cuts[:-1],cuts[1:]))/(r-l)
                max_mp=max(max_mp,abs(mp.mpf(float(b[key][0]))-exact))
            def conserved(x,j):
                rho,u,p=sod(x,tm)
                return [rho,rho*u,p/(g-1)+rho*u*u/2][j]
            for j in range(3):
                exact=mp.fsum(mp.quad(lambda x:conserved(x,j),[aa,bb]) for aa,bb in zip(cuts[:-1],cuts[1:]))/(r-l)
                max_mp=max(max_mp,abs(mp.mpf(float(b['conserved'][0,j]))-exact))
    assert max_quad<1e-10 and max_mp<mp.mpf('1e-10')
    record('006',{'pressure_root_80':str(pstar),'pressure_root_abs_error':str(pressure_error),
      'wave_split_gauss16_32_max':max_quad,'cell_average_80_max':str(max_mp),
      'allocation':'Both quadrature and 80-digit discrepancy <1e-10, tighter than 10% density gate; exact wave-split integrands polynomial degree<=7 for gamma1.4.'})
    ref=load('007');err=mp.mpf(0)
    for speed in [0.,1.]:
        for t in [0.,.001,.057,.1]:
            edges=np.linspace(0,1,101);data=ref.cell_averages(edges,t,speed)
            for i,(l,r) in enumerate(zip(edges[:-1],edges[1:])):
                lm,rm=mp.mpf(float(l)),mp.mpf(float(r));join=mp.mpf('.5')+mp.mpf(speed)*mp.mpf(str(t))
                rho=2-max(mp.mpf(0),min(rm,join)-lm)/(rm-lm)
                err=max(err,abs(mp.mpf(float(data['rho'][i]))-rho))
    assert err<mp.mpf('1e-11');record('007',{'cutcell_80_max':str(err),'allocation':'<1e-11, 10% of1e-10 p/u gate; p/u analytic constants exact.'})
    ref=load('009');err=mp.mpf(0);fourier_err=mp.mpf(0)
    for eps in [1e-5,5e-6]:
        for time in [0.,.0025,.125,.25]:
            edges=np.linspace(0,1,51);actual=ref.cell_averages(edges,time,eps)
            for i in [0,17,49]:
                l,r=map(lambda v:mp.mpf(float(v)),edges[i:i+2]);v=mp.mpf(str(eps))*(mp.sin(2*mp.pi*(r-c*mp.mpf(str(time))))-mp.sin(2*mp.pi*(l-c*mp.mpf(str(time)))))/(2*mp.pi*(r-l))
                err=max(err,abs(mp.mpf(float(actual['p'][i]))-(1+g*v)))
            exact=g*mp.mpf(str(eps))/2*mp.exp(-2j*mp.pi*c*mp.mpf(str(time)))
            fourier_err=max(fourier_err,abs(mp.mpc(ref.exact_fourier(time,eps))-exact))
    assert err<mp.mpf('1e-14') and fourier_err<mp.mpf('1e-18')
    record('009',{'cell_sinusoid_80_max':str(err),'continuous_fourier_80_max':str(fourier_err),'cell_fourier_operator_80':qualify_fourier_operator(ref),
      'allocation':'Absolute pressure error<1e-14 versus finest eps/2 pressure allocation ~3.8e-10; Fourier abs error<1e-18.'})
    ref=load('010');err=mp.mpf(0);fourier_err=mp.mpf(0);quad=0.
    for eps in [1e-5,5e-6]:
        for time in [0.,.3,1/ref.C]:
            edges=np.linspace(0,1,201);a=ref.cell_averages(edges,time,'free',eps)
            for i in [0,49,99,149,199]:
                l,r=map(lambda v:mp.mpf(float(v)),edges[i:i+2]);tm=mp.mpf(float(time));em=mp.mpf(str(eps))
                def integ(center):return em*mp.mpf('.05')*mp.sqrt(mp.pi)/2*(mp.erf((r-center)/mp.mpf('.05'))-mp.erf((l-center)/mp.mpf('.05')))
                exact=1+(integ(mp.mpf('.25')+c*tm)-integ(mp.mpf('1.75')-c*tm))/(r-l)
                err=max(err,abs(mp.mpf(float(a['p'][i]))-exact))
            exact=mp.quad(lambda x:em*(mp.exp(-((x-c*tm-mp.mpf('.25'))/mp.mpf('.05'))**2)-mp.exp(-((2-x-c*tm-mp.mpf('.25'))/mp.mpf('.05'))**2))*mp.exp(-2j*mp.pi*x),[mp.mpf(i)/8 for i in range(9)])
            f16=ref.exact_fourier(time,eps,16);f32=ref.exact_fourier(time,eps,32)
            quad=max(quad,abs(f16-f32));fourier_err=max(fourier_err,abs(mp.mpc(f32)-exact))
            assert abs(exact)>mp.mpf('1e-8')
    assert err<mp.mpf('1e-14') and fourier_err<mp.mpf('1e-18') and quad<1e-18
    # Rigid cell-average cosine/sine checked at80digits independently.
    rigiderr=mp.mpf(0)
    for time in [0.,.3,.6]:
        edges=np.linspace(0,1,201);a=ref.cell_averages(edges,time,'rigid')
        for i in [0,89,199]:
            l,r=map(lambda v:mp.mpf(float(v)),edges[i:i+2]);tm=mp.mpf(str(time))
            exact=1+mp.mpf('1e-5')*(mp.sin(mp.pi*r)-mp.sin(mp.pi*l))/(mp.pi*(r-l))*mp.cos(mp.pi*c*tm)
            rigiderr=max(rigiderr,abs(mp.mpf(float(a['p'][i]))-exact))
    assert rigiderr<mp.mpf('1e-14')
    record('010',{'free_erf_cells_80_max':str(err),'rigid_cells_80_max':str(rigiderr),'full_waveform_fourier_80_max':str(fourier_err),'fourier_gauss16_32':quad,'cell_fourier_operator_80':qualify_fourier_operator(ref),
      'allocation':'Pressure<1e-14 versus rigid eps/2 allocation5e-9; nonzero full Gaussian Fourier abs reference error<1e-18 versus relative amplitude allocation.001 and phase pi/800/10.'})
    ref=load('011');quad=0.;err=mp.mpf(0)
    def nozzle(x):
        area=1+mp.mpf('.4')*(x-mp.mpf('.5'))**2
        fun=lambda m:((5+m*m)/6)**3/m
        m=mp.findroot(lambda m:fun(m)-area*fun(mp.mpf('.3')),(mp.mpf('.2'),mp.mpf('.3')))
        t=1/(1+mp.mpf('.2')*m*m);p=t**mp.mpf('3.5');rho=p/t;u=m*mp.sqrt(g*t)
        return [area*rho,area*rho*u,area*(p/(g-1)+rho*u*u/2)]
    for n in [50,100,200,400]:
        edges=np.linspace(0,1,n+1);a=ref.cell_averages(edges,order=16);b=ref.cell_averages(edges,order=32)
        quad=max(quad,float(np.max(np.abs(a['conserved']-b['conserved']))))
        for i in [0,n//2,n-1]:
            l,r=map(lambda v:mp.mpf(float(v)),edges[i:i+2])
            for j in range(3):
                exact=mp.quad(lambda x:nozzle(x)[j],[l,r])/(r-l)
                err=max(err,abs(mp.mpf(float(b['conserved'][i,j]))-exact))
    assert quad<1e-10 and err<mp.mpf('1e-10')
    record('011',{'areaweighted_gauss16_32_max':quad,'areaweighted_cell80_max':str(err),
      'allocation':'Both<1e-10 versus required quadrature1e-10 and density allocation2e-7. Smooth subsonic branch anchored Mthroat=.3; rest exact.'})
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    for number,result in qualify().items():
        out=BASE/('VAL-'+number)/'qualification.json';payload=json.dumps(result,indent=2)+'\n'
        if args.check:assert json.loads(out.read_text())==result,('reference qualification drift',number)
        else:out.write_text(payload,encoding='utf-8',newline='\n')
        print('VAL-'+number,'REFERENCE_QUALIFIED (not candidate PASS)')
