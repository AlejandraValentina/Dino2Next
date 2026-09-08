"""Proposed local first-order patch with unchanged pinned bulk kernel calls."""
from pathlib import Path
import importlib.util
import hashlib
import sys
import numpy as np
from dino2next.gasdynamics import Mesh1D
from prototype import LocalSolver, State, TrialRejected, _base

_path=Path(__file__).resolve().with_name('kernel_source.py')
assert hashlib.sha256(_path.read_bytes()).hexdigest()=='84e5fba185fabf8008936c6ca533d0610b8cb87aa87b48833cf3d821328bfac9'
_spec=importlib.util.spec_from_file_location('pinned_S06_kernel',_path)
KERNEL=importlib.util.module_from_spec(_spec);sys.modules[_spec.name]=KERNEL;_spec.loader.exec_module(KERNEL)


class HybridSolver(LocalSolver):
    def __init__(self,model,base_edges):
        super().__init__(model,base_edges)
        self.kernel=KERNEL.NumericalKernel(model)
        self.hybrid_records=[]

    def patch_cells(self,state):
        n=len(state.labels);seed=np.zeros(n,bool)
        for i in self.interfaces(state):seed[i-1:i+1]=True
        # Exact base-grid membership, no approximate interpolation/alignment.
        for i,(l,r) in enumerate(zip(state.edges[:-1],state.edges[1:])):
            j=int(np.searchsorted(self.grid,l))
            if j>=len(self.grid)-1 or self.grid[j]!=l or self.grid[j+1]!=r:seed[i]=True
        patch=seed.copy()
        for i in np.flatnonzero(seed):patch[max(0,i-4):min(n,i+5)]=True
        return patch

    @staticmethod
    def mesh(edges):
        n=len(edges)-1
        return Mesh1D(tuple(map(float,edges)),(1.,)*n,(1.,)*(n+1),(1.,)*n)

    def bulk_call(self,state,start,end,boundary_flux):
        U=state.inventory/np.diff(state.edges)[:,None]
        n=len(U)
        local=self.kernel.state(self.mesh(state.edges[start:end+1]),U[start:end])
        ghosts=(U[np.clip(np.arange(start-4,start),0,n-1)],U[np.clip(np.arange(end,end+4),0,n-1)])
        faces=self.kernel.reconstruct(local,boundary='physical',ghosts=ghosts)
        return self.kernel.interior_flux(faces,boundary_flux=boundary_flux)

    def rhs_options(self,state):
        # Every input row is its own regional U. No aggregate observation Q is
        # recovered or supplied as an invented ghost thermodynamic state.
        speeds,regional=super().rhs(state)
        high=regional.copy();low=regional.copy();patch=self.patch_cells(state)
        n=len(patch);i=0;bulk_faces=np.zeros(n+1,bool)
        while i<n:
            if patch[i]:i+=1;continue
            end=i+1
            while end<n and not patch[end]:end+=1
            flux=self.bulk_call(state,i,end,(regional[i],regional[end]))
            high[i+1:end]=flux.high[1:-1];low[i+1:end]=flux.low[1:-1]
            bulk_faces[i+1:end]=True
            i=end
        return speeds,high,low,patch,bulk_faces

    def _guard(self,base,initial,dt,speeds,high,low,second):
        edges=base.edges+dt*speeds
        def candidate(theta):
            flux=high if theta==1 else low+theta*(high-low)
            trial=State(edges,base.inventory+dt*(flux[:-1]-flux[1:]),base.labels)
            self.recover(trial)
            if second:
                final=State(.5*initial.edges+.5*trial.edges,.5*initial.inventory+.5*trial.inventory,base.labels)
                self.recover(final)
            return trial,flux
        try:return (*candidate(1.),1.,0)
        except (TrialRejected,_base.ValueContractError):pass
        try:lo_state,lo_flux=candidate(0.)
        except (TrialRejected,_base.ValueContractError) as exc:
            raise TrialRejected('LOW_ORDER_STAGE_INADMISSIBLE_RETRY_DT') from exc
        cap=1.
        hi_inventory=base.inventory+dt*(high[:-1]-high[1:])
        pairs=[(lo_state.inventory,hi_inventory)]
        if second:pairs.append((.5*(initial.inventory+lo_state.inventory),.5*(initial.inventory+hi_inventory)))
        for a,b in pairs:
            a,b=a[:,KERNEL.NONNEGATIVE],b[:,KERNEL.NONNEGATIVE];negative=b<0
            if np.any(negative):cap=min(cap,float(np.min(a[negative]/(a-b)[negative])))
        lower,upper=0.,cap
        for _ in range(54):
            mid=(lower+upper)/2
            try:candidate(mid);lower=mid
            except (TrialRejected,_base.ValueContractError):upper=mid
        for reduction in range(9):
            try:return (*candidate(lower),lower,reduction)
            except (TrialRejected,_base.ValueContractError):lower*=1-32*KERNEL.EPS
        raise TrialRejected('FLUX_LIMIT_ROUND_OFF_RETRY_DT')

    def _step(self,state,dt):
        if not np.isfinite(dt) or dt<=0:raise TrialRejected('BAD_DT')
        self._context['stage']='Y0_RHS'
        v0,h0,l0,p0,b0=self.rhs_options(state)
        self._context['stage']='Y1_GUARD'
        stage,f0,theta0,reduce0=self._guard(state,state,dt,v0,h0,l0,False)
        self._context['stage']='Y1_RHS'
        v1,h1,l1,p1,b1=self.rhs_options(stage)
        self._context['stage']='Y2_AND_FINAL_GUARD'
        second,f1,theta1,reduce1=self._guard(stage,state,dt,v1,h1,l1,True)
        final=State(.5*state.edges+.5*second.edges,.5*state.inventory+.5*second.inventory,state.labels)
        gcl=np.diff(final.edges)-np.diff(state.edges)-.5*dt*(np.diff(v0)+np.diff(v1))
        self.stage_records.append({'transaction_id':self._transaction_id,'dt':dt,'fixed_labels':state.labels,
            'speed0':v0.tolist(),'speed1':v1.tolist(),'flux0':f0.tolist(),'flux1':f1.tolist(),
            'max_GCL_absolute_m':float(np.max(abs(gcl)))})
        self.hybrid_records.append({'transaction_id':self._transaction_id,'theta':(theta0,theta1),
            'roundoff_reductions':(reduce0,reduce1),'patch0':p0.tolist(),'patch1':p1.tolist(),
            'bulk_faces0':b0.tolist(),'bulk_faces1':b1.tolist()})
        return final,.5*dt*(f0+f1)
