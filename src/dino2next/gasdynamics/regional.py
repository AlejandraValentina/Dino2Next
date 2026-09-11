"""MR-008 immutable regional inventories and authoritative volume geometry."""
from dataclasses import dataclass, field, asdict
from fractions import Fraction
from functools import lru_cache
from hashlib import sha256
from math import fsum, isfinite, nextafter, inf
from numbers import Real
from types import SimpleNamespace
import json

from . import (COMPONENTS, EPS, Mesh1D, PolynomialSegment, DuctState, IntegratedInventory,
               ThermodynamicRecovery, ThermoModel, fractions, fail)


def scalar(value,path):
    if isinstance(value,bool) or not isinstance(value,Real):
        fail('MESH_NONCONFORMING',path,'Finite real SI number required')
    try:value=float(value)
    except (OverflowError,ValueError):fail('MESH_NONCONFORMING',path,'Unrepresentable scalar')
    if not isfinite(value):fail('MESH_NONCONFORMING',path,'Finite real SI number required')
    return value


def values(data,path):
    if isinstance(data,(str,bytes,dict)):
        fail('MESH_NONCONFORMING',path,'Sequence required')
    try:return tuple(scalar(x,path) for x in data)
    except TypeError:fail('MESH_NONCONFORMING',path,'Sequence required')


def sequence(data,path):
    if isinstance(data,(str,bytes,dict)):fail('MESH_NONCONFORMING',path,'Sequence required')
    try:return tuple(data)
    except TypeError:fail('MESH_NONCONFORMING',path,'Sequence required')


def identity(data):
    return sha256(json.dumps(data,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


@dataclass(frozen=True,slots=True)
class VolumeInverse:
    x: float
    bracket: tuple[float,float] | None
    residual_exact: Fraction
    kind: str

    def __post_init__(self):
        object.__setattr__(self,'x',scalar(self.x,'/inverse/x'))
        if self.bracket is not None:
            b=values(self.bracket,'/inverse/bracket')
            if len(b)!=2 or not b[0]<=self.x<=b[1]:
                fail('GEOMETRY_INVALID','/inverse','Invalid inverse bracket')
            object.__setattr__(self,'bracket',b)
        if not isinstance(self.residual_exact,Fraction) or self.kind not in ('BRACKETED_ROOT','CANONICAL_RIGHT_ENDPOINT'):
            fail('GEOMETRY_INVALID','/inverse','Exact residual and known certificate kind required')
        if (self.bracket is None)!=(self.kind=='CANONICAL_RIGHT_ENDPOINT'):
            fail('GEOMETRY_INVALID','/inverse','Canonical endpoint and root bracket are distinct certificates')


@dataclass(frozen=True,slots=True)
class CumulativeVolumeGeometry:
    """Qualified single accepted polynomial, W(left)=0. No extrapolation/joins."""
    segment: PolynomialSegment
    identity: str = field(init=False)

    def __post_init__(self):
        if not isinstance(self.segment,PolynomialSegment):
            fail('GEOMETRY_INVALID','/geometry','One qualified PolynomialSegment required; joins are unsupported')
        object.__setattr__(self,'identity',identity(asdict(self.segment)))

    def exact(self,x):
        x=scalar(x,'/geometry/x');s=self.segment
        xi=s._coordinate(x)
        return (Fraction(s.right)-Fraction(s.left))*sum(
            Fraction(v)*xi**(i+1)/(i+1) for i,v in enumerate(s.area_coefficients))

    def cumulative(self,x):
        try:w=float(self.exact(x))
        except OverflowError:fail('GEOMETRY_INVALID','/geometry/W','Unrepresentable volume')
        if not isfinite(w):fail('GEOMETRY_INVALID','/geometry/W','Unrepresentable volume')
        return w

    def inverse(self,W):return _inverse(self,scalar(W,'/geometry/W'))


@lru_cache(maxsize=65536)
def _inverse(geometry,W):
    s=geometry.segment;target=Fraction(W)
    if W==geometry.cumulative(s.right):
        return VolumeInverse(s.right,None,geometry.exact(s.right)-target,'CANONICAL_RIGHT_ENDPOINT')
    if target<0 or target>geometry.exact(s.right):
        fail('GEOMETRY_VOLUME_INVERSION','/W','Volume outside the physical domain')
    lo,hi=s.left,s.right
    if target==0:return VolumeInverse(lo,(lo,lo),Fraction(0),'BRACKETED_ROOT')
    # Exact signs; terminate only at an exact root or adjacent binary64 x.
    while nextafter(lo,inf)<hi:
        mid=lo+(hi-lo)*.5
        if not lo<mid<hi:break
        residual=geometry.exact(mid)-target
        if residual==0:return VolumeInverse(mid,(mid,mid),residual,'BRACKETED_ROOT')
        if residual<0:lo=mid
        else:hi=mid
    a,b=geometry.exact(lo)-target,geometry.exact(hi)-target
    x=lo if abs(a)<=abs(b) else hi
    return VolumeInverse(x,(lo,hi),geometry.exact(x)-target,'BRACKETED_ROOT')


@dataclass(frozen=True,slots=True)
class RegionalProjection:
    target_edges: tuple
    W: tuple
    inventory: tuple
    conservative_projection: tuple
    pressure_volume_average: tuple
    bulk_velocity: tuple
    chemical_mass_fractions: tuple
    tracer_mass_fractions: tuple
    geometry_residuals: tuple
    roundoff_records: tuple
    state_identity: str

    @property
    def Q(self):return self.conservative_projection

    def __post_init__(self):
        # Products are detached even when constructed directly by a caller.
        for name in ('target_edges','W','pressure_volume_average','bulk_velocity'):
            object.__setattr__(self,name,values(getattr(self,name),'/projection/'+name))
        for name in ('inventory','conservative_projection','chemical_mass_fractions','tracer_mass_fractions'):
            object.__setattr__(self,name,tuple(values(row,'/projection/'+name) for row in sequence(getattr(self,name),'/projection/'+name)))
        object.__setattr__(self,'geometry_residuals',sequence(self.geometry_residuals,'/projection/residuals'))
        records=[]
        for r in sequence(self.roundoff_records,'/projection/roundoff_records'):
            if not isinstance(r,(tuple,list)) or len(r)!=3 or type(r[0]) is not int or r[1] not in ('/chemical','/tracers'):
                fail('MESH_NONCONFORMING','/projection/roundoff_records','Typed fraction records required')
            records.append((r[0],r[1],scalar(r[2],'/projection/roundoff_records')))
        object.__setattr__(self,'roundoff_records',tuple(records))
        n=len(self.W)-1
        if n<1 or len(self.target_edges)!=n+1 or any(b<=a for a,b in zip(self.W,self.W[1:])) or any(b<=a for a,b in zip(self.target_edges,self.target_edges[1:])):
            fail('MESH_NONCONFORMING','/projection','Invalid observation geometry')
        for name,width in (('inventory',12),('conservative_projection',12),('chemical_mass_fractions',5),('tracer_mass_fractions',4)):
            data=getattr(self,name)
            if len(data)!=n or any(len(row)!=width for row in data):fail('MESH_NONCONFORMING','/projection','Invalid observation shape')
        if len(self.pressure_volume_average)!=n or len(self.bulk_velocity)!=n or len(self.geometry_residuals)!=n+1 or any(not isinstance(r,Fraction) for r in self.geometry_residuals):
            fail('MESH_NONCONFORMING','/projection','Invalid observation certificate shape')
        if any(p<=0 for p in self.pressure_volume_average) or any(row[0]<=0 or any(v<0 for v in row[3:]) for row in self.inventory):
            fail('EOS_OUT_OF_DOMAIN','/projection','Positive mass/pressure and nonnegative constituents required')
        if any(any(v<0 for v in row) or abs(fsum(row)-1)>256*EPS for row in self.chemical_mass_fractions+self.tracer_mass_fractions):
            fail('EOS_OUT_OF_DOMAIN','/projection','Invalid mass-weighted constituent fractions')
        if any(not 0<=r[0]<n or abs(r[2]-1)>256*EPS for r in records):
            fail('MESH_NONCONFORMING','/projection/roundoff_records','Invalid derived-fraction record')
        if not isinstance(self.state_identity,str) or len(self.state_identity)!=64 or any(c not in '0123456789abcdef' for c in self.state_identity):
            fail('MESH_NONCONFORMING','/projection','Source state identity required')


@dataclass(frozen=True,slots=True)
class RegionalDuctState:
    geometry: CumulativeVolumeGeometry
    base_mesh: Mesh1D
    W: tuple
    inventory: tuple
    labels: tuple
    thermo: ThermodynamicRecovery
    source_kind: str = 'GEN1_RUNTIME'
    component_order: tuple = COMPONENTS
    edges: tuple = field(init=False)
    volumes: tuple = field(init=False)
    inverse_certificates: tuple = field(init=False)
    recovery_identity: str = field(init=False)
    state_identity: str = field(init=False)
    regional_states: object = field(init=False,repr=False)

    def __post_init__(self):
        if not isinstance(self.geometry,CumulativeVolumeGeometry) or not isinstance(self.base_mesh,Mesh1D):
            fail('GEOMETRY_INVALID','/geometry','Explicit volume geometry and base Mesh1D required')
        if self.base_mesh.segment_boundaries or (self.base_mesh.geometry_segments and self.base_mesh.geometry_segments!=(self.geometry.segment,)):
            fail('GEOMETRY_INVALID','/geometry','Unqualified joins or inconsistent analytic geometry')
        seg=self.geometry.segment;bounds=self.base_mesh.cell_bounds
        expected=(tuple(seg.integral(a,b)/(b-a) for a,b in zip(bounds,bounds[1:])),
                  tuple(seg.value(x) for x in bounds),
                  tuple(seg.integral(a,b,perimeter=True)/(b-a) for a,b in zip(bounds,bounds[1:])))
        if expected!=(self.base_mesh.area_averages,self.base_mesh.face_areas,self.base_mesh.perimeter):
            fail('GEOMETRY_INVALID','/base_mesh','Base mesh must describe the supplied physical geometry')
        W=values(self.W,'/W')
        if len(W)<2 or any(b<=a or not isfinite(b-a) for a,b in zip(W,W[1:])):
            fail('NONPOSITIVE_VOLUME','/W','Strictly positive represented region volumes required')
        certificates=tuple(self.geometry.inverse(w) for w in W);edges=tuple(c.x for c in certificates)
        if any(b<=a for a,b in zip(edges,edges[1:])):
            fail('GEOMETRY_VOLUME_INVERSION','/W','Distinct volumes require representably ordered physical faces')
        if (W[0],W[-1])!=tuple(self.geometry.cumulative(x) for x in (self.base_mesh.cell_bounds[0],self.base_mesh.cell_bounds[-1])):
            fail('REGIONAL_BOUNDARY_UNSUPPORTED','/W','Regional domain must retain both physical base endpoints')
        rows=tuple(values(row,'/inventory') for row in sequence(self.inventory,'/inventory'))
        labels=sequence(self.labels,'/labels')
        if len(rows)!=len(W)-1 or any(len(row)!=12 for row in rows) or len(labels)!=len(rows):
            fail('MESH_NONCONFORMING','/inventory','One I12 and material identity per interval required')
        if any(not isinstance(label,str) or not label for label in labels):
            fail('MESH_NONCONFORMING','/labels','Nonempty physical material identities required')
        if not isinstance(self.component_order,(tuple,list)) or tuple(self.component_order)!=COMPONENTS:
            fail('EOS_OUT_OF_DOMAIN','/component_order','Normative I12 order required')
        if not isinstance(self.thermo,ThermodynamicRecovery):fail('EOS_OUT_OF_DOMAIN','/thermo','Recovery protocol required')
        if self.source_kind=='GEN1_RUNTIME':
            if type(self.thermo) is not ThermoModel:fail('EOS_OUT_OF_DOMAIN','/thermo','Accepted NASA required')
            dataset=self.thermo.dataset;bound=dataset.name+' '+dataset.version+' '+dataset.sha256
        elif self.source_kind=='NUMERICAL_FIXTURE_ONLY':
            name=getattr(self.thermo,'identity',None);ref=getattr(self.thermo,'reference_sha256',None)
            if getattr(self.thermo,'source_kind',None)!=self.source_kind or not isinstance(name,str) or not name or not isinstance(ref,str) or len(ref)!=64 or any(c not in '0123456789abcdef' for c in ref):
                fail('EOS_OUT_OF_DOMAIN','/thermo','Explicit fixture identity/reference required')
            bound=name+' '+ref
        else:fail('EOS_OUT_OF_DOMAIN','/source_kind','Unknown classification')
        for name,value in (('W',W),('inventory',rows),('labels',labels),('component_order',COMPONENTS),
                           ('edges',edges),('volumes',tuple(b-a for a,b in zip(W,W[1:]))),
                           ('inverse_certificates',certificates),('recovery_identity',bound)):
            object.__setattr__(self,name,value)
        # Reuse the accepted S05 recovery exactly: row=I, divisor=V. This is an
        # internal algebra view, not a physical Mesh1D or a second editable state.
        view=SimpleNamespace(Q=rows,mesh=SimpleNamespace(area_averages=self.volumes),
            thermo=self.thermo,source_kind=self.source_kind,recovery_identity=bound)
        object.__setattr__(self,'regional_states',DuctState._recover(view))
        object.__setattr__(self,'state_identity',identity(self._payload()))

    @property
    def U(self):return tuple(tuple(value/V for value in row) for row,V in zip(self.inventory,self.volumes))

    def integrated_inventory(self):
        try:total=tuple(fsum(row[j] for row in self.inventory) for j in range(12))
        except (OverflowError,ValueError):fail('EOS_OUT_OF_DOMAIN','/inventory','Total unrepresentable')
        return IntegratedInventory(*total[:3],total[3:8],total[8:])

    def projection(self,target_edges=None):
        x=values(self.base_mesh.cell_bounds if target_edges is None else target_edges,'/projection/edges')
        if len(x)<2 or any(b<=a for a,b in zip(x,x[1:])) or x[0]<self.edges[0] or x[-1]>self.edges[-1]:
            fail('MESH_NONCONFORMING','/projection','Ordered observation bounds within the regional domain required')
        inherited=dict(zip(self.edges,self.W))
        W=tuple(inherited[a] if a in inherited else self.geometry.cumulative(a) for a in x)
        rows=[];pressures=[];records=[];chemical=[];tracers=[]
        for index,(a,b) in enumerate(zip(W,W[1:])):
            if b<=a:fail('NONPOSITIVE_VOLUME','/projection','Observation interval has no represented volume')
            intersections=[(j,min(b,right)-max(a,left)) for j,(left,right) in enumerate(zip(self.W,self.W[1:])) if min(b,right)>max(a,left)]
            if len(intersections)==1 and intersections[0][1]==self.volumes[intersections[0][0]]:
                row=self.inventory[intersections[0][0]]
            else:
                row=tuple(fsum(self.inventory[j][k] if overlap==self.volumes[j] else self.inventory[j][k]*(overlap/self.volumes[j]) for j,overlap in intersections) for k in range(12))
            if row[0]<=0:fail('EOS_OUT_OF_DOMAIN','/projection','Observation mass must be positive and representable')
            rows.append(row);pressures.append(fsum(self.regional_states.p[j]*overlap for j,overlap in intersections)/(b-a))
            chemical.append(fractions(row[3:8],row[0],'/chemical',index,records))
            tracers.append(fractions(row[8:],row[0],'/tracers',index,records))
        return RegionalProjection(x,W,tuple(rows),tuple(tuple(v/(b-a) for v in row) for row,a,b in zip(rows,x,x[1:])),
            tuple(pressures),tuple(row[1]/row[0] for row in rows),tuple(chemical),tuple(tracers),
            tuple(self.geometry.exact(a)-Fraction(w) for a,w in zip(x,W)),tuple(records),self.state_identity)

    def _payload(self):
        return dict(schema_version='MR-008-1',geometry=asdict(self.geometry.segment),base_mesh=asdict(self.base_mesh),
                    W=self.W,inventory=self.inventory,labels=self.labels,component_order=COMPONENTS,
                    source_kind=self.source_kind,recovery_identity=self.recovery_identity)

    def to_restart(self):
        result=self._payload();result['state_identity']=self.state_identity
        return result

    @classmethod
    def from_restart(cls,payload,thermo):
        try:
            if payload['schema_version']!='MR-008-1':raise ValueError('schema')
            geometry=CumulativeVolumeGeometry(PolynomialSegment(**payload['geometry']))
            mesh_data=dict(payload['base_mesh']);mesh_data['geometry_segments']=tuple(PolynomialSegment(**s) for s in mesh_data['geometry_segments'])
            state=cls(geometry,Mesh1D(**mesh_data),payload['W'],payload['inventory'],payload['labels'],thermo,payload['source_kind'],payload['component_order'])
            if state.recovery_identity!=payload['recovery_identity'] or state.state_identity!=payload['state_identity']:raise ValueError('identity')
            return state
        except (KeyError,TypeError,ValueError) as exc:
            fail('REGIONAL_RESTART_IDENTITY','/restart','Complete matching regional restart required',reason=str(exc))

    @classmethod
    def from_physical(cls,geometry,base_mesh,edges,physical_states,labels,thermo,source_kind='GEN1_RUNTIME'):
        edges=values(edges,'/initial/edges');W=tuple(geometry.cumulative(x) for x in edges)
        data=sequence(physical_states,'/initial')
        if len(data)!=len(W)-1:fail('MESH_NONCONFORMING','/initial','One physical state per declared interval required')
        rows=[]
        for item,a,b in zip(data,W,W[1:]):
            item=sequence(item,'/initial')
            if len(item)!=5:fail('MESH_NONCONFORMING','/initial','Expected T,p,u,Y,tracers')
            T,p,u=tuple(scalar(v,'/initial') for v in item[:3]);Y=values(item[3],'/initial/Y');tags=values(item[4],'/initial/tracers')
            if len(Y)!=5 or len(tags)!=4:fail('EOS_OUT_OF_DOMAIN','/initial','Chemical/origin shape')
            # Physical input is evaluated as supplied, never inferred from Qbar.
            if not callable(getattr(thermo,'evaluate',None)):
                fail('EOS_OUT_OF_DOMAIN','/thermo','Physical initialization requires the classified EOS evaluation interface')
            result=thermo.evaluate(T,p,Y);mass=result.rho*(b-a)
            rows.append((mass,mass*u,mass*(result.e+.5*u*u),*(mass*y for y in Y),*(mass*t for t in tags)))
        return cls(geometry,base_mesh,W,tuple(rows),labels,thermo,source_kind)
