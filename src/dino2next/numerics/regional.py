"""MR-008 interior material route; ordinary NK arithmetic remains in its module.

The caller supplies physical boundary fluxes and owns global source/event
composition. This module does not create materials at a physical boundary.
"""
from dataclasses import dataclass
from math import fsum
import numpy as np

from dino2next.gasdynamics import Mesh1D
from dino2next.gasdynamics.regional import RegionalDuctState
from dino2next.units import ValueContractError
from . import NumericalKernel, EPS, NONNEGATIVE, frozen_array, diagnostic_tuple, finite_scalar, fail


@dataclass(frozen=True, slots=True)
class RegionalRHS:
    volume_speed: np.ndarray
    high: np.ndarray
    low: np.ndarray
    sources: np.ndarray
    face_areas: np.ndarray
    patch: np.ndarray
    diagnostics: tuple = ()

    def __post_init__(self):
        h = frozen_array(self.high)
        if h.ndim != 2 or h.shape[1] != 12 or len(h) < 2:
            fail('STAGE_INADMISSIBLE', '/regional_rhs', 'Expected twelve shared face fluxes')
        n = len(h)-1
        for name, shape in [('high',(n+1,12)),('low',(n+1,12)),('sources',(n,12)),
                            ('volume_speed',(n+1,)),('face_areas',(n+1,))]:
            object.__setattr__(self,name,frozen_array(getattr(self,name),shape))
        object.__setattr__(self,'patch',frozen_array(self.patch,(n,),boolean=True))
        object.__setattr__(self,'diagnostics',diagnostic_tuple(self.diagnostics))
        if np.any(self.face_areas <= 0) or np.any(self.volume_speed[[0,-1]] != 0):
            fail('UNSUPPORTED_REGIONAL_EVENT','/boundary','Only fixed physical endpoints are supported')
        if not np.array_equal(self.high[[0,-1]],self.low[[0,-1]]):
            fail('STAGE_INADMISSIBLE','/boundary','Both flux candidates must use the same physical exchange')


@dataclass(frozen=True, slots=True)
class RegionalStepAttempt:
    state: RegionalDuctState | None
    rejection: str | None
    diagnostics: tuple
    face_integrals: np.ndarray | None = None
    source_integrals: np.ndarray | None = None
    stage_states: tuple = ()
    face_stage_integrals: np.ndarray | None = None

    def __post_init__(self):
        if (self.state is None) == (self.rejection is None):
            fail('STAGE_INADMISSIBLE','/attempt','State or rejection must be exclusive')
        if self.state is not None and not isinstance(self.state,RegionalDuctState):
            fail('STAGE_INADMISSIBLE','/attempt','Regional state required')
        if self.state is None and (not isinstance(self.rejection,str) or not self.rejection):
            fail('STAGE_INADMISSIBLE','/attempt/rejection','Rejected trial requires a nonempty immutable failure code')
        object.__setattr__(self,'diagnostics',diagnostic_tuple(self.diagnostics))
        object.__setattr__(self,'stage_states',tuple(self.stage_states))
        for name in ('face_integrals','source_integrals'):
            value=getattr(self,name)
            if value is not None:
                if self.state is None:
                    fail('STAGE_INADMISSIBLE','/attempt','Rejected trials cannot publish committed ledgers')
                n=len(self.state.labels)
                object.__setattr__(self,name,frozen_array(value,(n+1,12) if name=='face_integrals' else (n,12)))
        if self.face_stage_integrals is not None:
            if self.state is None:
                fail('STAGE_INADMISSIBLE','/attempt','Rejected trials cannot publish stage ledgers')
            object.__setattr__(self,'face_stage_integrals',frozen_array(self.face_stage_integrals,(2,n+1,12)))
        if any(not isinstance(s,RegionalDuctState) for s in self.stage_states):
            fail('STAGE_INADMISSIBLE','/attempt','Physical stage snapshots required')

    @property
    def accepted(self):
        return self.state is not None


class RegionalNumericalKernel:
    """Selected local material patch, volume stages and conservative remap.

    A proposal never retries or mutates its input. Reorganization is a separate
    immutable operation between complete steps; the caller commits both only
    after its outer transaction succeeds. Transformed I arrays use the same
    explicit (Z,time)->physical-I mapping seam as the ordinary kernel.
    """
    def __init__(self,thermo,*,source_kind='GEN1_RUNTIME'):
        self.bulk=NumericalKernel(thermo,source_kind=source_kind)
        self.thermo=thermo
        self.source_kind=source_kind
        self.identity=self.bulk.identity

    def _state(self,state):
        if not isinstance(state,RegionalDuctState) or (state.source_kind,state.recovery_identity)!=(self.source_kind,self.identity):
            fail('EOS_OUT_OF_DOMAIN','/regional_state','State and kernel identities differ')
        return state

    def _new(self,base,W,I,labels=None):
        return RegionalDuctState(base.geometry,base.base_mesh,W,I,
                                 base.labels if labels is None else labels,
                                 self.thermo,source_kind=self.source_kind)

    @staticmethod
    def interfaces(state):
        return tuple(i for i in range(1,len(state.labels)) if state.labels[i-1]!=state.labels[i])

    def patch_cells(self,state):
        state=self._state(state)
        edges=np.asarray(state.edges);grid=np.asarray(state.base_mesh.cell_bounds)
        n=len(state.labels);seed=np.zeros(n,bool)
        for i in self.interfaces(state):seed[i-1:i+1]=True
        for i,(left,right) in enumerate(zip(edges[:-1],edges[1:])):
            j=int(np.searchsorted(grid,left))
            if j>=len(grid)-1 or grid[j]!=left or grid[j+1]!=right:seed[i]=True
        patch=seed.copy()
        for i in np.flatnonzero(seed):patch[max(0,i-4):min(n,i+5)]=True
        return frozen_array(patch,boolean=True)

    def recover(self,state):
        state=self._state(state)
        return self.bulk.recover(np.asarray(state.inventory)/np.asarray(state.volumes)[:,None])

    @staticmethod
    def physical_flux(U,primitive):
        result=np.asarray(U)*primitive[1]
        result[1]+=primitive[2]
        result[2]+=primitive[2]*primitive[1]
        return result

    def _regional_face(self,left,right,wl,wr,al,ar,material):
        rl,ul,pl=wl[:3];rr,ur,pr=wr[:3]
        sl=min(ul-al,ur-ar);sr=max(ul+al,ur+ar)
        dl=rl*(sl-ul);dr=rr*(sr-ur)
        sm=(pr-pl+dl*ul-dr*ur)/(dl-dr)
        ps=pl+dl*(sm-ul)
        if not np.isfinite(sm+ps) or ps<=0 or not sl<sm<sr:
            fail('RIEMANN_INADMISSIBLE','/regional_face','Davis contact state is inadmissible')
        if material:
            flux=np.zeros(12);flux[1:3]=(ps,ps*sm)
            return sm,flux
        if sl>=0:return 0.,self.physical_flux(left,wl)
        if sr<=0:return 0.,self.physical_flux(right,wr)
        U,w,s=(left,wl,sl) if sm>=0 else (right,wr,sr)
        rho,u,p=w[:3];density=rho*(s-u)/(s-sm)
        star=U*(density/rho);star[1]=density*sm
        star[2]=density*(U[2]/rho+(sm-u)*(sm+p/(rho*(s-u))))
        self.bulk.recover(star[None,:])
        return 0.,self.physical_flux(U,w)+s*(star-U)

    def rhs(self,state,time,*,boundary_flux):
        """Return A-weighted face fluxes and extensive geometric source rates.

        boundary_flux is a caller-supplied (2,12) per-area physical exchange.
        No reservoir, material insertion or donor reversal is inferred here.
        """
        state=self._state(state);finite_scalar(time,'/time')
        external=frozen_array(boundary_flux,(2,12))
        edges=np.asarray(state.edges);I=np.asarray(state.inventory)
        volume=np.asarray(state.volumes);U=I/volume[:,None]
        # The immutable state already recovered this exact I/V representation.
        primitive=state.regional_states;V=np.column_stack((
            tuple(snapshot.rho for snapshot in primitive.states),
            primitive.u,
            tuple(snapshot.p for snapshot in primitive.states),
            tuple(snapshot.Y for snapshot in primitive.states),
            primitive.tracers,
        ))
        sound=np.asarray(tuple(snapshot.a for snapshot in primitive.states))
        n=len(I);patch=self.patch_cells(state)
        area=np.array([state.geometry.segment.value(float(x)) for x in edges])
        speed=np.zeros(n+1);regional=np.zeros((n+1,12))
        regional[[0,-1]]=external
        for i in range(1,n):
            if not (patch[i-1] or patch[i]):continue
            speed[i],regional[i]=self._regional_face(U[i-1],U[i],V[i-1],V[i],
                sound[i-1],sound[i],state.labels[i-1]!=state.labels[i])
        high=area[:,None]*regional;low=high.copy();records=[]
        i=0
        while i<n:
            if patch[i]:i+=1;continue
            end=i+1
            while end<n and not patch[end]:end+=1
            segment_edges=edges[i:end+1];width=np.diff(segment_edges)
            averages=volume[i:end]/width
            perimeters=tuple(float(state.geometry.segment.integral(float(a),float(b),perimeter=True)/(b-a))
                             for a,b in zip(segment_edges[:-1],segment_edges[1:]))
            mesh=Mesh1D(tuple(map(float,segment_edges)),tuple(map(float,averages)),
                        tuple(map(float,area[i:end+1])),perimeters)
            ordinary=self.bulk.state(mesh,I[i:end]/width[:,None])
            ghosts=(U[np.clip(np.arange(i-4,i),0,n-1)],U[np.clip(np.arange(end,end+4),0,n-1)])
            faces=self.bulk.reconstruct(ordinary,boundary='physical',ghosts=ghosts)
            flux=self.bulk.interior_flux(faces,boundary_flux=regional[[i,end]])
            high[i+1:end]=area[i+1:end,None]*flux.high[1:-1]
            low[i+1:end]=area[i+1:end,None]*flux.low[1:-1]
            records.append(('bulk',i,end,flux.diagnostics))
            i=end
        sources=np.zeros_like(I);sources[:,1]=V[:,2]*np.diff(area)
        records.append(('regional_fraction_roundoff',primitive.roundoff_records))
        return RegionalRHS(area*speed,high,low,sources,area,patch,tuple(records))

    def timestep_bounds(self,state,stage_rhs):
        state=self._state(state)
        if not isinstance(stage_rhs,RegionalRHS) or len(stage_rhs.sources)!=len(state.labels):
            fail('STAGE_INADMISSIBLE','/regional_rhs','Regional RHS shape/type required')
        p=state.regional_states;dx=np.diff(state.edges);volume=np.asarray(state.volumes)
        area=stage_rhs.face_areas;speed=stage_rhs.volume_speed/area
        sound=np.asarray(tuple(snapshot.a for snapshot in p.states))
        velocity=np.asarray(p.u)
        left=sound+abs(velocity-speed[:-1]);right=sound+abs(velocity-speed[1:])
        bx=.2*(dx/np.maximum(left,right))
        bv=.2*(volume/np.maximum(area[:-1]*left,area[1:]*right))
        change=np.diff(stage_rhs.volume_speed);shrink=np.full(len(volume),np.inf)
        negative=change<0;shrink[negative]=.5*volume[negative]/(-change[negative])
        local=np.minimum(np.minimum(bx,bv),shrink)
        if np.any(local<=0) or not np.all(np.isfinite(local)):
            fail('STAGE_INADMISSIBLE','/dt','No positive regional predictor')
        detail=tuple((int(i),float(bx[i]),float(bv[i]),None if np.isinf(shrink[i]) else float(shrink[i])) for i in range(len(volume)))
        return float(np.min(local)),detail

    @staticmethod
    def _mapped(Z,time,mapper):
        frozen=frozen_array(Z)
        return frozen if mapper is None else frozen_array(mapper(frozen,time),frozen.shape)

    def _guard(self,base,initial,Zbase,Zinitial,R,dt,end_time,mapper,second,records):
        nextW=np.asarray(base.W)+dt*R.volume_speed
        initialW=np.asarray(initial.W)
        for i in self.interfaces(base):
            if not nextW[0]<nextW[i]<nextW[-1]:
                fail('UNSUPPORTED_REGIONAL_EVENT','/material_face','Material reaches unsupported physical endpoint')
        if np.any(np.diff(nextW)<=0):
            fail('STAGE_INADMISSIBLE','/W','Euler endpoint has nonpositive region volume')
        # W does not depend on theta. Validate its inverse geometry once.
        derived=[base.geometry.inverse(float(w)).x for w in nextW]
        if np.any(np.diff(derived)<=0):
            fail('STAGE_INADMISSIBLE','/W','Regional coordinates are not representably ordered')
        def candidate(theta):
            flux=R.high if theta==1 else R.low+theta*(R.high-R.low)
            Z=Zbase+dt*(flux[:-1]-flux[1:]+R.sources)
            I=self._mapped(Z,end_time,mapper)
            checks=[(nextW,I)]
            if second:checks.append((.5*initialW+.5*nextW,self._mapped(.5*Zinitial+.5*Z,end_time,mapper)))
            good=True;reason='';roundoff=[]
            try:
                candidates=[]
                for W,Q in checks:
                    if np.any(np.diff(W)<=0):fail('STAGE_INADMISSIBLE','/W','Final volume is nonpositive')
                    # Constructing the immutable candidate performs the same
                    # recovery that used to be performed here, and preserves
                    # the validated primitive state for its next consumer.
                    candidate_state=self._new(base,W,Q)
                    candidates.append(candidate_state)
                    roundoff.append(candidate_state.regional_states.roundoff_records)
            except ValueContractError as exc:good=False;reason=exc.code
            records.append(('guard_candidate',2 if second else 1,float(theta),good,reason,tuple(roundoff)))
            return good,Z,flux,I,checks,tuple(candidates) if good else ()
        high=candidate(1.)
        if high[0]:return high[1],high[2],high[5][0],1.,0
        low=candidate(0.)
        if not low[0]:
            fail('STAGE_INADMISSIBLE','/guard','Low-order Euler endpoint is inadmissible',reason='LOW_ORDER_STAGE_INADMISSIBLE_RETRY_DT')
        cap=1.
        for (_,lo),(_,hi) in zip(low[4],high[4]):
            a,b=lo[:,NONNEGATIVE],hi[:,NONNEGATIVE];negative=b<0
            if np.any(negative):cap=min(cap,float(np.min(a[negative]/(a-b)[negative])))
        lower,upper=0.,cap
        for _ in range(54):
            mid=(lower+upper)/2
            if candidate(mid)[0]:lower=mid
            else:upper=mid
        for reduction in range(9):
            trial=candidate(lower)
            if trial[0]:return trial[1],trial[2],trial[5][0],lower,reduction
            lower*=1-32*EPS
        fail('STAGE_INADMISSIBLE','/guard','Flux roundoff retry required',reason='FLUX_LIMIT_ROUND_OFF_RETRY_DT')

    def propose_step(self,state,rhs,time,dt,*,trial_state_mapper=None,initial_Z=None):
        state=self._state(state);time=finite_scalar(time,'/time');dt=finite_scalar(dt,'/dt')
        if dt<=0 or not np.isfinite(time+dt) or time+dt<=time:
            fail('STAGE_INADMISSIBLE','/dt','Positive representable step required')
        if not callable(rhs) or (trial_state_mapper is not None and not callable(trial_state_mapper)):
            fail('STAGE_INADMISSIBLE','/callback','Read-only RHS and mapper required')
        if trial_state_mapper is not None and initial_Z is None:
            fail('STAGE_INADMISSIBLE','/initial_Z','Explicit transformed regional inventories required')
        I0=np.asarray(state.inventory);Z0=frozen_array(I0 if initial_Z is None else initial_Z,I0.shape)
        records=[]
        try:
            if not np.array_equal(self._mapped(Z0,time,trial_state_mapper),I0):
                fail('STAGE_INADMISSIBLE','/initial_Z','Physical mapping differs from initial regional inventory')
            R0=rhs(state,time);limit0,b0=self.timestep_bounds(state,R0)
            records.extend([('rhs',0,R0.diagnostics),('volume_predictor','Y0',dt,limit0,b0)])
            if dt>limit0:fail('STAGE_INADMISSIBLE','/dt','Y0 volume predictor failed',reason='VOLUMETRIC_STAGE_BOUND_Y0')
            Z1,F0,stage,t0,r0=self._guard(state,state,Z0,Z0,R0,dt,time+dt,trial_state_mapper,False,records)
            R1=rhs(stage,time+dt);limit1,b1=self.timestep_bounds(stage,R1)
            records.extend([('rhs',1,R1.diagnostics),('volume_predictor','Y1',dt,limit1,b1)])
            if dt>limit1:fail('STAGE_INADMISSIBLE','/dt','Y1 volume predictor failed',reason='VOLUMETRIC_STAGE_BOUND_Y1')
            Z2,F1,second,t1,r1=self._guard(stage,state,Z1,Z0,R1,dt,time+dt,trial_state_mapper,True,records)
            final=self._new(state,.5*np.asarray(state.W)+.5*np.asarray(second.W),self._mapped(.5*Z0+.5*Z2,time+dt,trial_state_mapper))
            gcl=np.diff(final.W)-np.diff(state.W)-.5*dt*(np.diff(R0.volume_speed)+np.diff(R1.volume_speed))
            records.extend([('selected_guards',(t0,t1),(r0,r1)),('max_GCL_volume',float(np.max(abs(gcl)))),
                            ('transaction','ACCEPTED','parent',state.state_identity,'child',final.state_identity)])
            return RegionalStepAttempt(final,None,tuple(records),.5*dt*(F0+F1),
                                       .5*dt*(R0.sources+R1.sources),(state,stage,second,final),
                                       (.5*dt*F0,.5*dt*F1))
        except ValueContractError as exc:
            records.extend([('failure',exc.code,exc.path,exc.message),
                            ('transaction','REJECTED','parent',state.state_identity)])
            return RegionalStepAttempt(None,exc.metadata.get('reason',exc.code),tuple(records))

    def reorganize(self,state):
        """Conservative same-material W overlaps, only between full steps."""
        state=self._state(state);edges=np.asarray(state.edges);Wold=np.asarray(state.W)
        Iold=np.asarray(state.inventory);grid=np.asarray(state.base_mesh.cell_bounds)
        material=edges[list(self.interfaces(state))];dx=float(np.min(np.diff(grid)))
        keep=[x for x in grid[1:-1] if not len(material) or np.min(abs(material-x))>=.35*dx]
        target=np.array(sorted([edges[0],*keep,*material,edges[-1]]))
        if np.array_equal(target,edges):return state
        lookup=dict(zip(edges,Wold))
        W=np.array([lookup[float(x)] if float(x) in lookup else state.geometry.cumulative(float(x)) for x in target])
        # Label lookup uses left faces: a rounded midpoint may land on a thin
        # region's right endpoint. Material boundaries remain explicit targets.
        labels=tuple(state.labels[min(len(state.labels)-1,int(np.searchsorted(edges,float(x),side='right'))-1)] for x in target[:-1])
        inventories=np.zeros((len(labels),12));j=0
        for i,(left,right) in enumerate(zip(Wold[:-1],Wold[1:])):
            while j<len(labels) and W[j+1]<=left:j+=1
            targets=[];k=j
            while k<len(labels) and W[k]<right:
                overlap=min(right,W[k+1])-max(left,W[k])
                if overlap>0:targets.append((k,overlap))
                k+=1
            if not targets:fail('STAGE_INADMISSIBLE','/remap','Donor has no receiver')
            remainder=Iold[i].copy()
            for t,(k,overlap) in enumerate(targets):
                if labels[k]!=state.labels[i]:
                    fail('STAGE_INADMISSIBLE','/remap','Transfer crosses material identity')
                amount=remainder.copy() if t==len(targets)-1 else Iold[i]*(overlap/(right-left))
                inventories[k]+=amount;remainder-=amount
        return self._new(state,W,inventories,labels)
