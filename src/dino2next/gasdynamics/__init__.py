"""S05: immutable A*U cell averages and physical geometry; no face flux solver."""
from dataclasses import dataclass, field
from fractions import Fraction
from math import comb, fsum, isfinite
from sys import float_info
from typing import Protocol, runtime_checkable

from dino2next.thermo import ThermoModel, SPECIES
from dino2next.geometry import GeometryModel
from dino2next.units import ValueContractError

TRACERS = ('F0', 'F1', 'R', 'X')
COMPONENTS = ('rho', 'rho_u', 'rho_E', *('rho_'+s for s in SPECIES),
              *('rho_'+s for s in TRACERS))
EPS = float_info.epsilon


@runtime_checkable
class ThermodynamicRecovery(Protocol):
    """Injected recovery seam; GEN1 runtime still permits only ThermoModel."""
    def invert_energy(self,rho,e,Y): ...


def fail(code, path, message, **metadata):
    raise ValueContractError(code,path,message,component='gasdynamics',metadata=metadata)


def number(value, path, code='MESH_NONCONFORMING'):
    if type(value) not in (int,float):
        fail(code,path,'Expected a finite SI scalar')
    try:
        value=float(value)
    except OverflowError:
        fail(code,path,'Value exceeds binary64')
    if not isfinite(value):
        fail(code,path,'Expected a finite SI scalar')
    return value


def vector(values, path, code='MESH_NONCONFORMING'):
    if not isinstance(values,(tuple,list)):
        fail(code,path,'Expected an array')
    return tuple(number(x,f'{path}/{i}',code) for i,x in enumerate(values))


def positive_polynomial(coefficients):
    """Certify positivity with exact rational Bernstein subdivision."""
    degree=len(coefficients)-1
    power=tuple(map(Fraction,coefficients))
    bernstein=tuple(sum(power[k]*Fraction(comb(j,k),comb(degree,k)) for k in range(j+1))
                    for j in range(degree+1))
    pending=[(bernstein,0)]
    while pending:
        values,depth=pending.pop()
        if min(values)>0:
            continue
        if values[0]<=0 or values[-1]<=0 or max(values)<=0:
            return False
        if depth==24:
            fail('GEOMETRY_INVALID','/segments','Strict positive polynomial geometry could not be certified',subdivisions=depth)
        levels=[values]
        while len(levels[-1])>1:
            previous=levels[-1]
            levels.append(tuple((a+b)/2 for a,b in zip(previous,previous[1:])))
        pending.extend([(tuple(level[0] for level in levels),depth+1),
                        (tuple(level[-1] for level in reversed(levels)),depth+1)])
    return True


@dataclass(frozen=True,slots=True)
class PolynomialSegment:
    """Explicit A and perimeter polynomials in xi=(x-left)/(right-left).

    Coefficients are declared physical geometry inputs, never fits inferred from
    sparse samples. Arbitrary polynomial degrees are accepted when positivity
    can be certified. Analytic integration uses their exact binary64 input values.
    """
    left: float
    right: float
    area_coefficients: tuple[float,...]
    perimeter_coefficients: tuple[float,...]

    def __post_init__(self):
        object.__setattr__(self,'left',number(self.left,'/segments/left','GEOMETRY_INVALID'))
        object.__setattr__(self,'right',number(self.right,'/segments/right','GEOMETRY_INVALID'))
        if self.right<=self.left or not isfinite(self.right-self.left):
            fail('GEOMETRY_INVALID','/segments','Segment must have positive finite length')
        for name in ('area_coefficients','perimeter_coefficients'):
            values=vector(getattr(self,name),'/segments/'+name,'GEOMETRY_INVALID')
            if not values or not positive_polynomial(values):
                fail('GEOMETRY_INVALID','/segments/'+name,'Polynomial geometry must be strictly positive over the full segment')
            object.__setattr__(self,name,values)

    def _coordinate(self,x):
        x=number(x,'/x','GEOMETRY_INVALID')
        if not self.left<=x<=self.right:
            fail('GEOMETRY_INVALID','/x','No geometry extrapolation')
        return (Fraction(x)-Fraction(self.left))/(Fraction(self.right)-Fraction(self.left))

    def value(self,x,*,perimeter=False):
        xi=self._coordinate(x)
        a=self.perimeter_coefficients if perimeter else self.area_coefficients
        try:
            result=float(sum(Fraction(v)*xi**i for i,v in enumerate(a)))
        except OverflowError:
            fail('GEOMETRY_INVALID','/segments','Geometry evaluation exceeds binary64')
        if not isfinite(result) or result<=0:
            fail('GEOMETRY_INVALID','/segments','Geometry must be positive and representable')
        return result

    def integral(self,left,right,*,perimeter=False):
        a,b=self._coordinate(left),self._coordinate(right)
        if b<a:
            fail('GEOMETRY_INVALID','/segments','Integral bounds must be forward')
        coefficients=self.perimeter_coefficients if perimeter else self.area_coefficients
        result=(Fraction(self.right)-Fraction(self.left))*sum(
            Fraction(v)*(b**(i+1)-a**(i+1))/(i+1) for i,v in enumerate(coefficients))
        try:
            result=float(result)
        except OverflowError:
            fail('GEOMETRY_INVALID','/segments','Geometry integral exceeds binary64')
        if not isfinite(result):
            fail('GEOMETRY_INVALID','/segments','Geometry integral exceeds binary64')
        return result


def segment_data(bounds,segments):
    if not isinstance(segments,(tuple,list)) or not segments or any(not isinstance(s,PolynomialSegment) for s in segments):
        fail('GEOMETRY_INVALID','/segments','Explicit analytic segments are required; samples alone do not define integrals')
    segments=tuple(segments)
    if segments[0].left!=bounds[0] or segments[-1].right!=bounds[-1] or any(
            a.right!=b.left for a,b in zip(segments,segments[1:])):
        fail('GEOMETRY_INVALID','/segments','Shape segments must cover the mesh exactly, without gaps or overlap')
    if any(s.right not in bounds for s in segments[:-1]):
        fail('MESH_NONCONFORMING','/segments','Analytic segment joins must coincide with mesh faces')
    for a,b in zip(segments,segments[1:]):
        for perimeter in (False,True):
            av,bv=a.value(a.right,perimeter=perimeter),b.value(b.left,perimeter=perimeter)
            if abs(av-bv)>5*EPS/(1-5*EPS)*(abs(av)+abs(bv)):
                fail('GEOMETRY_INVALID','/segments','Discontinuous area/perimeter needs an explicit physical interface')
    def at(x,perimeter=False):
        return next(s.value(x,perimeter=perimeter) for s in segments if s.left<=x<=s.right)
    def average(a,b,perimeter=False):
        return fsum(s.integral(max(a,s.left),min(b,s.right),perimeter=perimeter)
                    for s in segments if max(a,s.left)<min(b,s.right))/(b-a)
    return (tuple(average(a,b) for a,b in zip(bounds,bounds[1:])),tuple(at(x) for x in bounds),
            tuple(average(a,b,True) for a,b in zip(bounds,bounds[1:])))


@dataclass(frozen=True,slots=True)
class Mesh1D:
    """One physical passage; areas/perimeters are never aggregate count values.

    Exact supplied cell integrals divided by dx define area_averages. Segment
    boundaries are explicit and must coincide with mesh faces. The constructor
    does not infer an interpolation law from endpoint samples.
    """
    cell_bounds: tuple[float,...]
    area_averages: tuple[float,...]
    face_areas: tuple[float,...]
    perimeter: tuple[float,...]
    segment_boundaries: tuple[float,...] = ()
    component_id: str = 'passage'
    geometry_segments: tuple[PolynomialSegment,...] = ()
    config_hash: str | None = None
    replication_count: int = 1

    def __post_init__(self):
        for field in ('cell_bounds','area_averages','face_areas','perimeter','segment_boundaries'):
            object.__setattr__(self,field,vector(getattr(self,field),'/mesh/'+field))
        x=self.cell_bounds
        n=len(x)-1
        if n<1 or any(b<=a or not isfinite(b-a) for a,b in zip(x,x[1:])):
            fail('MESH_NONCONFORMING','/mesh/cell_bounds','Positive finite cell widths required')
        if len(self.area_averages)!=n or len(self.perimeter)!=n or len(self.face_areas)!=n+1:
            fail('MESH_NONCONFORMING','/mesh','Geometry arrays must align with the mesh')
        if any(v<=0 for v in self.area_averages+self.face_areas+self.perimeter):
            fail('GEOMETRY_INVALID','/mesh','Physical storage area and perimeter must remain positive')
        if not isinstance(self.component_id,str) or not self.component_id:
            fail('GEOMETRY_INVALID','/mesh/component_id','Physical passage identity required')
        if type(self.replication_count) is not int or self.replication_count<1:
            fail('GEOMETRY_INVALID','/mesh/replication_count','Positive integer count provenance required')
        if self.config_hash is not None and (type(self.config_hash) is not str or len(self.config_hash)!=64 or
                                             any(c not in '0123456789abcdef' for c in self.config_hash)):
            fail('GEOMETRY_INVALID','/mesh/config_hash','Expected geometry ConfigSnapshot SHA256')
        if not isinstance(self.geometry_segments,(tuple,list)):
            fail('GEOMETRY_INVALID','/mesh/geometry_segments','Expected explicit segment sequence')
        object.__setattr__(self,'geometry_segments',tuple(self.geometry_segments))
        if self.geometry_segments and segment_data(x,self.geometry_segments)!=(self.area_averages,self.face_areas,self.perimeter):
            fail('GEOMETRY_INVALID','/mesh','Supplied integrals do not match the declared geometry')
        breaks=self.segment_boundaries
        if breaks and (any(b<=a for a,b in zip(breaks,breaks[1:])) or
                       any(b not in x[1:-1] for b in breaks)):
            fail('MESH_NONCONFORMING','/mesh/segment_boundaries','Internal segment boundaries must be ordered mesh faces')
        faces=(x[0],*breaks,x[-1])
        # Check uniform physical segments allowing only coordinate construction
        # roundoff. This compares positions, not a physical mesh tolerance.
        gamma5=5*EPS/(1-5*EPS)
        for left,right in zip(faces,faces[1:]):
            first,last=x.index(left),x.index(right)
            for j in range(first,last+1):
                expected=left+(right-left)*(j-first)/(last-first)
                if abs(x[j]-expected)>gamma5*(abs(left)+abs(right-left)+abs(expected)):
                    fail('MESH_NONCONFORMING','/mesh/cell_bounds','Cells must be uniform within each declared physical segment')
        if any(not isfinite(a*dx) or a*dx<=0 for a,dx in zip(self.area_averages,self.dx)):
            fail('GEOMETRY_INVALID','/mesh/area_averages','Cell volumes must be representable and positive')

    @property
    def dx(self):
        return tuple(b-a for a,b in zip(self.cell_bounds,self.cell_bounds[1:]))

    @property
    def cell_volumes(self):
        return tuple(a*dx for a,dx in zip(self.area_averages,self.dx))

    @classmethod
    def from_segments(cls,cell_bounds,segments,*,segment_boundaries=(),component_id='passage',config_hash=None,replication_count=1):
        bounds=vector(cell_bounds,'/mesh/cell_bounds')
        if len(bounds)<2 or any(b<=a for a,b in zip(bounds,bounds[1:])):
            fail('MESH_NONCONFORMING','/mesh/cell_bounds','Increasing cell faces required')
        return cls(bounds,*segment_data(bounds,segments),segment_boundaries,component_id,tuple(segments),config_hash,replication_count)

    @classmethod
    def from_geometry(cls,geometry,component_id,cell_bounds,*,segments,segment_boundaries=()):
        if not isinstance(geometry,GeometryModel):
            fail('GEOMETRY_INVALID','/geometry','Accepted GeometryModel required')
        samples=next((s for s in geometry.passages if s.component_id==component_id),None)
        if samples is None or samples.area_basis!='PER_PASSAGE':
            fail('GEOMETRY_INVALID','/geometry','Supply measured per-passage geometry; aggregate reports are not flow domains')
        mesh=cls.from_segments(cell_bounds,segments,segment_boundaries=segment_boundaries,
                               component_id=component_id,config_hash=geometry.config_hash,replication_count=samples.count)
        if samples.positions[0]!=mesh.cell_bounds[0] or samples.positions[-1]!=mesh.cell_bounds[-1]:
            fail('GEOMETRY_INVALID','/geometry','Measured and declared segment extents must agree')
        for x,area,perimeter in zip(samples.positions,samples.areas,samples.perimeters):
            segment=next(s for s in mesh.geometry_segments if s.left<=x<=s.right)
            for actual,expected in ((segment.value(x),area),(segment.value(x,perimeter=True),perimeter)):
                if abs(actual-expected)>5*EPS/(1-5*EPS)*(abs(actual)+abs(expected)):
                    fail('GEOMETRY_INVALID','/geometry','Explicit shape disagrees with supplied measurements')
        return mesh


@dataclass(frozen=True,slots=True)
class ThermodynamicSnapshot:
    """Detached result protocol; fixture states never acquire a NASA identity."""
    T: float
    p: float
    rho: float
    R: float
    cp: float
    cv: float
    h: float
    e: float
    gamma: float
    a: float
    Y: tuple[float,...]
    source_kind: str
    model_identity: str
    target_energy: float
    energy_residual: float

    def __post_init__(self):
        for name in ('T','p','rho','R','cp','cv','h','e','gamma','a','target_energy','energy_residual'):
            value=number(getattr(self,name),'/state/'+name,'EOS_OUT_OF_DOMAIN')
            if name not in ('h','e','target_energy','energy_residual') and value<=0:
                fail('EOS_OUT_OF_DOMAIN','/state/'+name,'Positive thermodynamic property required')
            object.__setattr__(self,name,value)
        values=vector(self.Y,'/state/Y','EOS_OUT_OF_DOMAIN')
        if len(values)!=5 or any(y<0 for y in values) or abs(fsum(values)-1)>256*EPS:
            fail('EOS_OUT_OF_DOMAIN','/state/Y','Invalid recovered composition')
        object.__setattr__(self,'Y',values)
        if self.source_kind not in ('GEN1_RUNTIME','NUMERICAL_FIXTURE_ONLY') or not isinstance(self.model_identity,str) or not self.model_identity:
            fail('EOS_OUT_OF_DOMAIN','/state/model_identity','Explicit recovery implementation and source kind required')
        if self.energy_residual!=self.e-self.target_energy:
            fail('EOS_OUT_OF_DOMAIN','/state/energy_residual','Residual must retain the original target')


@dataclass(frozen=True,slots=True)
class PrimitiveArrays:
    states: tuple[ThermodynamicSnapshot,...]
    u: tuple[float,...]
    tracers: tuple[tuple[float,...],...]
    roundoff_records: tuple[tuple[int,str,float],...] = ()

    def __post_init__(self):
        if not isinstance(self.states,(tuple,list)) or any(not isinstance(s,ThermodynamicSnapshot) for s in self.states):
            fail('EOS_OUT_OF_DOMAIN','/states','Expected immutable thermodynamic states')
        object.__setattr__(self,'states',tuple(self.states))
        object.__setattr__(self,'u',vector(self.u,'/u','EOS_OUT_OF_DOMAIN'))
        if not isinstance(self.tracers,(tuple,list)):
            fail('EOS_OUT_OF_DOMAIN','/tracers','Expected tracer rows')
        tracers=tuple(vector(t,'/tracers','EOS_OUT_OF_DOMAIN') for t in self.tracers)
        if not self.states or len(self.states)!=len(self.u) or len(tracers)!=len(self.u) or any(len(t)!=4 for t in tracers):
            fail('EOS_OUT_OF_DOMAIN','/states','Primitive columns must align')
        if any(any(v<0 for v in t) or abs(fsum(t)-1)>256*EPS for t in tracers):
            fail('EOS_OUT_OF_DOMAIN','/tracers','Invalid derived tracer simplex')
        object.__setattr__(self,'tracers',tracers)
        if not isinstance(self.roundoff_records,(tuple,list)):
            fail('EOS_OUT_OF_DOMAIN','/roundoff_records','Expected explicit derived-fraction roundoff records')
        records=[]
        for record in self.roundoff_records:
            if not isinstance(record,(tuple,list)) or len(record)!=3 or type(record[0]) is not int or not 0<=record[0]<len(self.states) or record[1] not in ('/chemical','/tracers'):
                fail('EOS_OUT_OF_DOMAIN','/roundoff_records','Invalid correction provenance')
            value=number(record[2],'/roundoff_records','EOS_OUT_OF_DOMAIN')
            if abs(value-1)>256*EPS:
                fail('EOS_OUT_OF_DOMAIN','/roundoff_records','Correction exceeds TS-004 roundoff bound')
            records.append((record[0],record[1],value))
        object.__setattr__(self,'roundoff_records',tuple(records))

    @property
    def rho(self):return tuple(s.rho for s in self.states)
    @property
    def p(self):return tuple(s.p for s in self.states)
    @property
    def T(self):return tuple(s.T for s in self.states)
    @property
    def Y(self):return tuple(s.Y for s in self.states)


@dataclass(frozen=True,slots=True)
class IntegratedInventory:
    mass: float
    momentum: float
    total_energy: float
    species_mass: tuple[float,...]
    tracer_mass: tuple[float,...]

    def __post_init__(self):
        for name in ('mass','momentum','total_energy'):
            object.__setattr__(self,name,number(getattr(self,name),'/'+name,'EOS_OUT_OF_DOMAIN'))
        for name,n in (('species_mass',5),('tracer_mass',4)):
            value=vector(getattr(self,name),'/'+name,'EOS_OUT_OF_DOMAIN')
            if len(value)!=n or any(v<0 for v in value):
                fail('EOS_OUT_OF_DOMAIN','/'+name,'Invalid extensive constituent masses')
            object.__setattr__(self,name,value)
        if self.mass<=0:
            fail('EOS_OUT_OF_DOMAIN','/mass','Positive mass required')
        try:
            inconsistent=any(abs(fsum(values)-self.mass)>256*EPS*self.mass for values in (self.species_mass,self.tracer_mass))
        except OverflowError:
            fail('EOS_OUT_OF_DOMAIN','/mass','Constituent total exceeds binary64')
        if inconsistent:
            fail('EOS_OUT_OF_DOMAIN','/mass','Integrated constituent totals must match total mass to roundoff')


def fractions(masses,total,path,cell,records):
    if any(m<0 for m in masses):
        fail('EOS_OUT_OF_DOMAIN',path,'Negative constituent inventory is inadmissible')
    values=tuple(m/total for m in masses)
    value_sum=fsum(values)
    if not isfinite(value_sum) or abs(value_sum-1)>256*EPS:
        fail('EOS_OUT_OF_DOMAIN',path,'Constituent masses do not form the stored total mass',fraction_sum=value_sum)
    if value_sum!=1:
        # TS-004 explicitly permits correction of DERIVED fractions alone.
        # The original Q columns remain untouched, including their roundoff.
        records.append((cell,path,value_sum))
        values=tuple(v/value_sum for v in values)
    return values


@dataclass(frozen=True,slots=True)
class DuctState:
    mesh: Mesh1D
    Q: tuple[tuple[float,...],...]
    thermo: ThermodynamicRecovery
    component_order: tuple[str,...] = COMPONENTS
    source_kind: str = 'GEN1_RUNTIME'
    recovery_identity: str = field(init=False)
    _primitives: PrimitiveArrays = field(init=False,repr=False)

    def __post_init__(self):
        if not isinstance(self.mesh,Mesh1D):
            fail('MESH_NONCONFORMING','/mesh','Expected Mesh1D')
        if not isinstance(self.thermo,ThermodynamicRecovery):
            fail('EOS_OUT_OF_DOMAIN','/thermo','Thermodynamic recovery protocol required')
        if self.source_kind=='GEN1_RUNTIME':
            if type(self.thermo) is not ThermoModel:
                fail('EOS_OUT_OF_DOMAIN','/thermo','GEN1 runtime requires the accepted NASA implementation')
            bound_identity=self.thermo.dataset.name+' '+self.thermo.dataset.version+' '+self.thermo.dataset.sha256
        elif self.source_kind=='NUMERICAL_FIXTURE_ONLY':
            identity=getattr(self.thermo,'identity',None)
            reference=getattr(self.thermo,'reference_sha256',None)
            if getattr(self.thermo,'source_kind',None)!=self.source_kind or not isinstance(identity,str) or not identity or type(reference) is not str or len(reference)!=64 or any(c not in '0123456789abcdef' for c in reference):
                fail('EOS_OUT_OF_DOMAIN','/thermo','Mathematical fixture adapter requires explicit identity, source kind and reference hash')
            bound_identity=identity+' '+reference
        else:
            fail('EOS_OUT_OF_DOMAIN','/source_kind','Unknown state classification')
        object.__setattr__(self,'recovery_identity',bound_identity)
        if not isinstance(self.component_order,(tuple,list)) or tuple(self.component_order)!=COMPONENTS:
            fail('EOS_OUT_OF_DOMAIN','/component_order','Chemical and tracer columns must use the normative order')
        object.__setattr__(self,'component_order',COMPONENTS)
        if not isinstance(self.Q,(tuple,list)) or len(self.Q)!=len(self.mesh.dx):
            fail('MESH_NONCONFORMING','/Q','One average row per cell is required')
        rows=tuple(vector(row,f'/Q/{i}','EOS_OUT_OF_DOMAIN') for i,row in enumerate(self.Q))
        if any(len(row)!=len(COMPONENTS) for row in rows):
            fail('MESH_NONCONFORMING','/Q','Expected density, momentum, energy, five chemical and four tracer columns')
        object.__setattr__(self,'Q',rows)
        # Fail before publishing an accepted immutable state; no partial recovery.
        object.__setattr__(self,'_primitives',self._recover())

    def primitive(self):
        return self._primitives

    def _recover(self):
        states,velocity,tags,records=[],[],[],[]
        for i,(row,area) in enumerate(zip(self.Q,self.mesh.area_averages)):
            rho=row[0]/area
            if rho<=0 or not isfinite(rho):
                fail('EOS_OUT_OF_DOMAIN',f'/Q/{i}/rho','Cell density must be positive and representable')
            u=row[1]/row[0]
            e=row[2]/row[0]-.5*u*u
            if not isfinite(u) or not isfinite(e):
                fail('EOS_OUT_OF_DOMAIN',f'/Q/{i}','Primitive energy/velocity not representable')
            y=fractions(row[3:8],row[0],'/chemical',i,records)
            tau=fractions(row[8:12],row[0],'/tracers',i,records)
            result=self.thermo.invert_energy(rho,e,y)
            try:
                if result.rho!=rho or tuple(result.Y)!=y:
                    fail('EOS_OUT_OF_DOMAIN',f'/Q/{i}','Recovery must retain supplied density and composition')
                state=ThermodynamicSnapshot(*(getattr(result,key) for key in ('T','p','rho','R','cp','cv','h','e','gamma','a')),
                                            y,self.source_kind,self.recovery_identity,e,result.e-e)
            except (AttributeError,TypeError) as exc:
                fail('EOS_OUT_OF_DOMAIN',f'/Q/{i}','Recovery returned an invalid result protocol',reason=str(exc))
            states.append(state)
            velocity.append(u)
            tags.append(tau)
        return PrimitiveArrays(tuple(states),tuple(velocity),tuple(tags),tuple(records))

    def integrated_inventory(self):
        try:
            columns=tuple(fsum(row[j]*dx for row,dx in zip(self.Q,self.mesh.dx)) for j in range(12))
        except (OverflowError,ValueError):
            fail('EOS_OUT_OF_DOMAIN','/Q','Integrated inventory exceeds binary64')
        return IntegratedInventory(*columns[:3],columns[3:8],columns[8:12])

    def geometry_source(self):
        p=self.primitive().p
        result=tuple(pressure*(right-left)/dx for pressure,left,right,dx in
                     zip(p,self.mesh.face_areas,self.mesh.face_areas[1:],self.mesh.dx))
        if any(not isfinite(value) for value in result):
            fail('GEOMETRY_INVALID','/mesh','Geometry source exceeds binary64')
        return result


def _duct(value):
    if not isinstance(value,DuctState):
        fail('EOS_OUT_OF_DOMAIN','/duct','Expected DuctState')
    return value


def primitive(duct):return _duct(duct).primitive()
def integrated_inventory(duct):return _duct(duct).integrated_inventory()
def geometry_source(duct):return _duct(duct).geometry_source()


# MR-008 additive state representation; homogeneous S05 definitions unchanged.
from .regional import (CumulativeVolumeGeometry, VolumeInverse,
                       RegionalDuctState, RegionalProjection)
