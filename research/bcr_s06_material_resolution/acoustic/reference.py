"""Independent linear standing/reflected waves; NUMERICAL_FIXTURE_ONLY."""
import math
import numpy as np

C=math.sqrt(1.4)

def point_states(x,time=0.,kind='rigid',epsilon=1e-5):
    x=np.asarray(x)
    if kind=='rigid':
        v=epsilon*np.cos(np.pi*x)*math.cos(np.pi*C*time)
        u=epsilon/C*np.sin(np.pi*x)*math.sin(np.pi*C*time)
    elif kind=='free':
        a=epsilon*np.exp(-((x-C*time-.25)/.05)**2);b=epsilon*np.exp(-((2-x-C*time-.25)/.05)**2)
        v=a-b;u=(a+b)/C
    else:raise ValueError(kind)
    rho=1+v/(C*C);p=1+v
    return dict(rho=rho,u=u,p=p,conserved=np.stack([rho,rho*u,p/.4+rho*u*u/2],axis=-1))

def gaussian_integral(left,right,center,epsilon):
    return epsilon*.05*math.sqrt(math.pi)/2*(math.erf((right-center)/.05)-math.erf((left-center)/.05))

def cell_averages(edges,time=0.,kind='rigid',epsilon=1e-5,order=32):
    edges=np.asarray(edges);dx=np.diff(edges);mid=(edges[:-1]+edges[1:])/2
    if kind=='rigid':
        v=epsilon*np.cos(np.pi*mid)*np.sinc(dx/2)*math.cos(np.pi*C*time)
        u=epsilon/C*np.sin(np.pi*mid)*np.sinc(dx/2)*math.sin(np.pi*C*time)
    elif kind=='free':
        a=np.array([gaussian_integral(l,r,.25+C*time,epsilon) for l,r in zip(edges[:-1],edges[1:])])/dx
        b=np.array([gaussian_integral(l,r,1.75-C*time,epsilon) for l,r in zip(edges[:-1],edges[1:])])/dx
        v=a-b;u=(a+b)/C
    else:raise ValueError(kind)
    z,w=np.polynomial.legendre.leggauss(order)
    q=np.array([np.tensordot(w,point_states(m+d*z/2,time,kind,epsilon)['conserved'],axes=(0,0))/2 for m,d in zip(mid,dx)])
    return dict(rho=1+v/(C*C),u=u,p=1+v,conserved=q)

def fourier_coefficient(edges,pressure_perturbation):
    edges=np.asarray(edges);weights=(np.exp(-2j*np.pi*edges[1:])-np.exp(-2j*np.pi*edges[:-1]))/(-2j*np.pi)
    return complex(np.dot(pressure_perturbation,weights))

def exact_fourier(time,epsilon=1e-5,order=32):
    """Full incident-minus-reflected waveform integral; no peak surrogate."""
    z,w=np.polynomial.legendre.leggauss(order);result=0j
    # Fixed fine panels resolve both Gaussian centers, even outside the domain.
    for l,r in zip(np.linspace(0,1,65)[:-1],np.linspace(0,1,65)[1:]):
        x=(l+r)/2+(r-l)*z/2
        pp=epsilon*(np.exp(-((x-C*time-.25)/.05)**2)-np.exp(-((2-x-C*time-.25)/.05)**2))
        result+=(r-l)/2*np.dot(w,pp*np.exp(-2j*np.pi*x))
    return complex(result)


def free_component_cell_averages(edges, time=0., epsilon=1e-5):
    """Exact Gaussian cell averages of SV-010 w+ and w-, not total-pressure ratios."""
    edges=np.asarray(edges,dtype=float);dx=np.diff(edges)
    if edges.ndim!=1 or len(edges)<2 or not np.isfinite(edges).all() or np.any(dx<=0):
        raise ValueError('Strictly increasing finite cell edges required')
    if not math.isfinite(time) or epsilon not in (1e-5,5e-6):
        raise ValueError('Finite time and a contracted amplitude required')
    incident=np.array([gaussian_integral(l,r,.25+C*time,epsilon) for l,r in zip(edges[:-1],edges[1:])])/dx
    reflected=-np.array([gaussian_integral(l,r,1.75-C*time,epsilon) for l,r in zip(edges[:-1],edges[1:])])/dx
    return dict(incident=incident,reflected=reflected)


def free_observation_reference(N, sample_index, epsilon=1e-5):
    """Qualified SV-010 C_h coefficients at exact ct=j/100; no candidate input.

    The qualification binds this source, qualifier and current catalogue. Both
    amplitude masks are fixed from interval reference coefficients before use.
    """
    if type(N) is not int or N not in (200,400,800) or type(sample_index) is not int or not 0<=sample_index<=100:
        raise ValueError('Contracted mesh and sample index required')
    if epsilon not in (1e-5,5e-6):raise ValueError('Contracted amplitude required')
    record=_free_qualified_record()
    mesh=next(m for m in record['meshes'] if m['N']==N)
    row=mesh['samples'][sample_index];scale=epsilon/1e-5
    result={'A0':record['normalization']['stored_A0']*scale,
            'A0_error_upper':record['normalization']['stored_A0_error_upper']*scale}
    for component in row['components']:
        result[component['name']]={'C':complex(*component['stored_coefficient'])*scale,
                'phase_eligible':component['phase_and_relative_amplitude_eligible'],
                'error_upper':component['stored_coefficient_error_upper']*scale}
    a=result['incident'];b=result['reflected']
    total=a['C']+b['C']
    addition_bound=2*(math.ulp(total.real)+math.ulp(total.imag))
    result['pressure']={'C':total, 'error_upper':math.nextafter(a['error_upper']+b['error_upper']+addition_bound,math.inf)}
    return result


def _free_qualified_record():
    # Small immutable files; validate each call so stale generated data never pass
    # merely because a previous caller populated a cache before a source change.
    from pathlib import Path
    from hashlib import sha256
    import json
    here=Path(__file__).resolve().parent;root=here.parents[2]
    record=json.loads((here/'free_observation_qualification.json').read_text())
    if record['status']!='REFERENCE_QUALIFIED' or record['candidate_imports'] is not False:
        raise ValueError('REFERENCE_NOT_QUALIFIED')
    for path,digest in record['source_hashes'].items():
        if sha256((root/path).read_bytes()).hexdigest()!=digest:
            raise ValueError('REFERENCE_NOT_QUALIFIED: source hash mismatch '+path)
    return record
