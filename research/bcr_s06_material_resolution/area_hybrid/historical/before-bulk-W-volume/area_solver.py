"""Research-only volume-coordinate extension of the frozen local hybrid."""
from pathlib import Path
from dataclasses import dataclass,field
from fractions import Fraction
import importlib.util,sys,inspect,textwrap,hashlib
import numpy as np

HERE=Path(__file__).resolve().parent;LOCAL=HERE.parent/'local_material'
for path,expected in (
    (LOCAL/'hybrid.py','2bdb700ee7342ceb6f685dff89f0fa009da7b52b1e7adae97fb0ca36c90fe404'),
    (LOCAL/'prototype.py','c2f9d81ce57a8cae741839b5522185e10485c7cabe1070a935500a13387d3eee'),
    (HERE.parent/'regional_geometry/geometry.py','0f2ac4d8ed8556b1f9b161201deccde446338219cc3ab18340632a3a4fb520c2')):
    assert hashlib.sha256(path.read_bytes()).hexdigest()==expected,'RESEARCH_DEPENDENCY_CHANGED'
sys.path.insert(0,str(LOCAL))
import hybrid as H
sys.path.pop(0)
spec=importlib.util.spec_from_file_location('area_volume_map',HERE.parent/'regional_geometry/geometry.py')
G=importlib.util.module_from_spec(spec);sys.modules[spec.name]=G;spec.loader.exec_module(G)

@dataclass(frozen=True)
class AreaState:
    W: np.ndarray
    inventory: np.ndarray
    labels: tuple
    geometry: G.VolumeMap
    edges: np.ndarray=field(init=False)
    inverse_residuals: tuple=field(init=False)
    endpoint_records: tuple=field(init=False)
    def __post_init__(self):
        W=H._base.frozen(self.W)
        if W.ndim!=1 or np.any(np.diff(W)<=0):raise H.TrialRejected('NONPOSITIVE_VOLUME')
        recovered=[];endpoint_records=[]
        try:
            for i,w in enumerate(W):
                canonical=self.geometry.cumulative(self.geometry.segment.right)
                if float(w)==canonical:
                    # Only the geometry provider's canonical stored endpoint.
                    # This is not an enclosure of an out-of-domain real root.
                    x=self.geometry.segment.right
                    residual=self.geometry.exact(x)-Fraction(float(w))
                    recovered.append((x,None,residual))
                    endpoint_records.append((i,'CANONICAL_RIGHT_ENDPOINT',str(residual)))
                else:recovered.append(self.geometry.inverse(float(w)))
        except ValueError as exc:raise H.TrialRejected('GEOMETRY_VOLUME_INVERSION') from exc
        base=H.State([v[0] for v in recovered],self.inventory,self.labels)
        object.__setattr__(self,'W',W);object.__setattr__(self,'inventory',base.inventory)
        object.__setattr__(self,'labels',base.labels);object.__setattr__(self,'edges',base.edges)
        object.__setattr__(self,'inverse_residuals',tuple(float(v[2]) for v in recovered))
        object.__setattr__(self,'endpoint_records',tuple(endpoint_records))

@dataclass(frozen=True)
class AreaLedger:
    faces: np.ndarray
    sources: np.ndarray

class AreaHybrid(H.HybridSolver):
    def __init__(self,model,base_edges,geometry):
        super().__init__(model,base_edges);self.geometry=geometry;self.projection_records=[]
    def make_state(self,W,inventory,labels):return AreaState(W,inventory,labels,self.geometry)
    def initialize(self,edges,physical,labels):
        plain=super().initialize(edges,physical,labels)
        W=np.array([self.geometry.cumulative(float(x)) for x in edges])
        state=self.make_state(W,plain.inventory*(np.diff(W)/np.diff(edges))[:,None],labels)
        self.recover(state);return state
    def unit_state(self,state):
        if not isinstance(state,AreaState):return state
        return H.State(state.edges,state.inventory*(np.diff(state.edges)/np.diff(state.W))[:,None],state.labels)
    def recover(self,state):return super().recover(self.unit_state(state))
    def bulk_call(self,state,start,end,boundary_flux):
        if not isinstance(state,AreaState):return super().bulk_call(state,start,end,boundary_flux)
        edges=state.edges[start:end+1];width=np.diff(edges)
        avg=np.array([self.geometry.segment.integral(float(a),float(b))/(b-a)
                      for a,b in zip(edges[:-1],edges[1:])])
        area=np.array([self.geometry.segment.value(float(x)) for x in edges])
        perimeter=tuple(self.geometry.segment.integral(float(a),float(b),perimeter=True)/(b-a) for a,b in zip(edges[:-1],edges[1:]))
        mesh=H.Mesh1D(tuple(map(float,edges)),tuple(map(float,avg)),tuple(map(float,area)),tuple(map(float,perimeter)))
        U=state.inventory/np.diff(state.W)[:,None];n=len(U)
        local=self.kernel.state(mesh,state.inventory[start:end]/width[:,None])
        ghosts=(U[np.clip(np.arange(start-4,start),0,n-1)],U[np.clip(np.arange(end,end+4),0,n-1)])
        faces=self.kernel.reconstruct(local,boundary='physical',ghosts=ghosts)
        boundary=np.asarray(boundary_flux)/area[[0,-1],None]
        flux=self.kernel.interior_flux(faces,boundary_flux=boundary)
        return flux,area
    def rhs_options(self,state):
        patch=self.patch_cells(state);plain=self.unit_state(state)
        speeds,regional=super().regional_options(plain,patch)
        area=np.array([self.geometry.segment.value(float(x)) for x in state.edges])
        regional=area[:,None]*regional;high=regional.copy();low=regional.copy()
        n=len(patch);i=0;bulk_faces=np.zeros(n+1,bool)
        while i<n:
            if patch[i]:i+=1;continue
            end=i+1
            while end<n and not patch[end]:end+=1
            flux,local_area=self.bulk_call(state,i,end,(regional[i],regional[end]))
            high[i+1:end]=local_area[1:-1,None]*flux.high[1:-1]
            low[i+1:end]=local_area[1:-1,None]*flux.low[1:-1]
            bulk_faces[i+1:end]=True;i=end
        source=np.zeros_like(state.inventory)
        source[:,1]=self.recover(state)[:,2]*np.diff(area)
        return area*speeds,high,low,patch,bulk_faces,source
    def suggested_dt(self,state,cfl=.2):
        return super().suggested_dt(self.unit_state(state),cfl)
    def _step(self,state,dt):
        if not np.isfinite(dt) or dt<=0:raise H.TrialRejected('BAD_DT')
        self._context['stage']='Y0_RHS'
        v0,h0,l0,p0,b0,s0=self.rhs_options(state);self._guard_source=s0
        self._context['stage']='Y1_GUARD'
        stage,f0,t0,r0=self._guard(state,state,dt,v0,h0,l0,False)
        self._context['stage']='Y1_RHS'
        v1,h1,l1,p1,b1,s1=self.rhs_options(stage);self._guard_source=s1
        self._context['stage']='Y2_AND_FINAL_GUARD'
        second,f1,t1,r1=self._guard(stage,state,dt,v1,h1,l1,True)
        final=self.make_state(.5*state.W+.5*second.W,.5*state.inventory+.5*second.inventory,state.labels)
        gcl=np.diff(final.W)-np.diff(state.W)-.5*dt*(np.diff(v0)+np.diff(v1))
        self.stage_records.append(dict(transaction_id=self._transaction_id,dt=dt,
            volume_speed0=v0.tolist(),volume_speed1=v1.tolist(),source0=s0.tolist(),source1=s1.tolist(),
            max_GCL_volume=float(np.max(abs(gcl))),inverse_residuals=final.inverse_residuals,
            endpoint_records=final.endpoint_records))
        self.hybrid_records.append(dict(transaction_id=self._transaction_id,theta=(t0,t1),
            roundoff_reductions=(r0,r1),patch0=p0.tolist(),patch1=p1.tolist(),bulk_faces0=b0.tolist(),bulk_faces1=b1.tolist()))
        return final,AreaLedger(H._base.frozen(.5*dt*(f0+f1)),H._base.frozen(.5*dt*(s0+s1)))
    def reorganize(self,state):
        material=state.edges[self.interfaces(state)]
        keep=[x for x in self.grid[1:-1] if not len(material) or np.min(abs(material-x))>=self.exclusion*self.dx]
        edges=np.array(sorted([state.edges[0],*keep,*material,state.edges[-1]]))
        if np.array_equal(edges,state.edges):return state
        W=np.array([self.geometry.cumulative(float(x)) for x in edges])
        # Existing material boundaries retain their authoritative W exactly.
        for j,x in enumerate(edges):
            found=np.flatnonzero(state.edges==x)
            if len(found):W[j]=state.W[found[0]]
        labels=tuple(state.labels[min(len(state.labels)-1,np.searchsorted(state.edges,x,side='right')-1)] for x in (edges[:-1]+edges[1:])/2)
        inventory=np.zeros((len(labels),12))
        for i,(left,right) in enumerate(zip(state.edges[:-1],state.edges[1:])):
            targets=[(j,max(left,a),min(right,b)) for j,(a,b) in enumerate(zip(edges[:-1],edges[1:])) if min(right,b)>max(left,a)]
            remainder=state.inventory[i].copy()
            for k,(j,a,b) in enumerate(targets):
                if labels[j]!=state.labels[i]:raise H.TrialRejected('REMAP_CROSSES_MATERIAL')
                overlap=min(state.W[i+1],W[j+1])-max(state.W[i],W[j])
                amount=remainder.copy() if k==len(targets)-1 else state.inventory[i]*(overlap/float(state.W[i+1]-state.W[i]))
                inventory[j]+=amount;remainder-=amount
        result=self.make_state(W,inventory,labels);self.recover(result)
        self.remap_records.append(dict(transaction_id=self._transaction_id,residual=(result.inventory.sum(axis=0)-state.inventory.sum(axis=0)).tolist()))
        return result
    def sample(self,state,observation_edges):
        obs=np.asarray(observation_edges);w=self.recover(state)
        observation_W=[]
        for x in obs:
            found=np.flatnonzero(state.edges==x)
            observation_W.append(state.W[found[0]] if len(found) else self.geometry.cumulative(float(x)))
        observation_W=np.asarray(observation_W)
        if np.any(np.diff(observation_W)<=0):raise H.TrialRejected('OBSERVATION_NONPOSITIVE_VOLUME')
        self.projection_records.append(dict(transaction_id=self._transaction_id,
            coordinates=obs.tolist(),volume_coordinates=observation_W.tolist(),
            exact_coordinate_residuals=[str(self.geometry.exact(float(x))-Fraction(float(v)))
                                       for x,v in zip(obs,observation_W)]))
        totals=np.zeros((len(obs)-1,12));pressure=np.zeros(len(obs)-1);pieces=[]
        for j,(a,b) in enumerate(zip(obs[:-1],obs[1:])):
            volume=observation_W[j+1]-observation_W[j];covered=0.
            for i,(l,r) in enumerate(zip(state.edges[:-1],state.edges[1:])):
                left,right=max(observation_W[j],state.W[i]),min(observation_W[j+1],state.W[i+1])
                if right>left:
                    overlap=right-left
                    amount=state.inventory[i]*(overlap/(state.W[i+1]-state.W[i]))
                    totals[j]+=amount;pressure[j]+=overlap*w[i,2];covered+=overlap
                    pieces.append((j,i,overlap,H._base.frozen(amount)))
            if abs(covered-volume)>256*np.finfo(float).eps*max(1.,volume):
                raise H.TrialRejected('OBSERVATION_OUTSIDE_DOMAIN')
            pressure[j]/=volume
        return H._base.frozen(totals),H._base.frozen(pressure),tuple(pieces)

# Reuse the reviewed shared H/L guard with explicit geometric/source changes.
guard=textwrap.dedent(inspect.getsource(H.HybridSolver._guard))
replacements={
 'edges=base.edges+dt*speeds':'edges=base.W+dt*speeds',
 'trial=State(edges,base.inventory+dt*(flux[:-1]-flux[1:]),base.labels)':
 'trial=self.make_state(edges,base.inventory+dt*(flux[:-1]-flux[1:]+self._guard_source),base.labels)',
 'final=State(.5*initial.edges+.5*trial.edges,.5*initial.inventory+.5*trial.inventory,base.labels)':
 'final=self.make_state(.5*initial.W+.5*trial.W,.5*initial.inventory+.5*trial.inventory,base.labels)',
 'hi_inventory=base.inventory+dt*(high[:-1]-high[1:])':
 'hi_inventory=base.inventory+dt*(high[:-1]-high[1:]+self._guard_source)'}
for a,b in replacements.items():
    assert guard.count(a)==1,a
    guard=guard.replace(a,b)
namespace=dict(H.HybridSolver._guard.__globals__)
exec(compile(guard,str(HERE/'adapted_guard.py'),'exec'),namespace)
AreaHybrid._guard=namespace['_guard']
