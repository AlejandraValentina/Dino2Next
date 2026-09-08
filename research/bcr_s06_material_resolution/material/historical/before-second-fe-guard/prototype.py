"""Research-only 1D moving-region conservative Euler prototype; see PLAN.md."""
from dataclasses import dataclass
from functools import lru_cache
from math import fsum
import numpy as np
from dino2next.units import ValueContractError


class TrialRejected(ValueError):
    pass


def frozen(a):
    a = np.asarray(a, dtype=np.float64)
    return np.frombuffer(a.tobytes(), dtype=np.float64).reshape(a.shape)


@dataclass(frozen=True)
class State:
    edges: np.ndarray
    inventory: np.ndarray
    labels: tuple

    def __post_init__(self):
        object.__setattr__(self, 'edges', frozen(self.edges))
        object.__setattr__(self, 'inventory', frozen(self.inventory))
        object.__setattr__(self, 'labels', tuple(self.labels))
        n = len(self.labels)
        if self.edges.shape != (n+1,) or self.inventory.shape != (n,12):
            raise TrialRejected('REGION_SHAPE')
        if not np.isfinite(self.edges).all() or not np.isfinite(self.inventory).all():
            raise TrialRejected('NONFINITE')
        if np.any(np.diff(self.edges) <= 0) or np.any(self.inventory[:,0] <= 0):
            raise TrialRejected('NONPOSITIVE_REGION')
        if np.any(self.inventory[:,3:] < 0):
            raise TrialRejected('NEGATIVE_CONSTITUENT')


class RegionSolver:
    def __init__(self, model):
        self.model = model
        self.records = []
        self._invert = lru_cache(maxsize=65536)(model.invert_energy)

    def initialize(self, edges, physical, labels):
        """physical entries are (T,p,u,Y[5],origin[4]), never oracle trajectories."""
        rows=[]
        for width, (T,p,u,Y,origin) in zip(np.diff(edges), physical, strict=True):
            s=self.model.evaluate(T,p,Y)
            rows.append(width*np.array([s.rho,s.rho*u,s.rho*(s.e+.5*u*u),
                                       *(s.rho*np.array(Y)),*(s.rho*np.array(origin))]))
        state=State(edges,rows,labels)
        self.recover(state)
        return state

    def recover(self,state):
        result=[]
        for width,q in zip(np.diff(state.edges),state.inventory,strict=True):
            rho=float(q[0]/width);u=float(q[1]/q[0]);Y=q[3:8]/q[0]
            total=fsum(Y)
            for sl in (slice(3,8),slice(8,12)):
                discrepancy=fsum(q[sl]/q[0])-1
                if abs(discrepancy)>256*np.finfo(float).eps:
                    raise TrialRejected('SIMPLEX')
            if total!=1:
                self.records.append(('TS004_DERIVED_SUM',total))
            Y=tuple(float(v/total) for v in Y)
            e=float(q[2]/q[0]-.5*u*u)
            s=self._invert(rho,e,Y)
            result.append((rho,u,s.p,s.a,s.T))
        return np.array(result)

    def rhs(self,state):
        w=self.recover(state);n=len(w)
        speed=np.empty(n+1);pressure=np.empty(n+1)
        # Freely moving outer material faces with exterior pressure equal to
        # adjacent state: zero-gradient open reservoir control, ledger explicit.
        speed[[0,-1]]=w[[0,-1],1];pressure[[0,-1]]=w[[0,-1],2]
        for i in range(1,n):
            rl,ul,pl,al,_=w[i-1];rr,ur,pr,ar,_=w[i]
            sl=min(ul-al,ur-ar);sr=max(ul+al,ur+ar)
            dl=rl*(sl-ul);dr=rr*(sr-ur)
            sm=(pr-pl+dl*ul-dr*ur)/(dl-dr)
            ps=pl+dl*(sm-ul)
            if not np.isfinite(sm+ps) or ps<=0 or not sl<sm<sr:
                raise TrialRejected('RIEMANN_INADMISSIBLE')
            speed[i]=sm;pressure[i]=ps
        flux=np.zeros((n+1,12));flux[:,1]=pressure;flux[:,2]=pressure*speed
        return speed,flux

    def suggested_dt(self,state,cfl=.2):
        w=self.recover(state)
        # Mesh follows fluid velocity; acoustic propagation and compression
        # still constrain each interval, including physically tiny intervals.
        v,_=self.rhs(state);width=np.diff(state.edges)
        rate=w[:,3]+np.maximum(abs(w[:,1]-v[:-1]),abs(w[:,1]-v[1:]))
        return float(cfl*np.min(width/rate))

    def step(self,state,dt):
        if not np.isfinite(dt) or dt<=0:raise TrialRejected('BAD_DT')
        v0,f0=self.rhs(state)
        s1=State(state.edges+dt*v0,state.inventory+dt*(f0[:-1]-f0[1:]),state.labels)
        v1,f1=self.rhs(s1)
        out=State(.5*state.edges+.5*(s1.edges+dt*v1),
                  .5*state.inventory+.5*(s1.inventory+dt*(f1[:-1]-f1[1:])),state.labels)
        self.recover(out)
        return out,.5*dt*(f0+f1)

    def attempt(self,state,dt,max_retries=16):
        """Complete trial rollback: immutable state and ledger commit on success."""
        failures=[]
        for _ in range(max_retries+1):
            try:
                if dt>self.suggested_dt(state):raise TrialRejected('STAGE0_DT')
                result,ledger=self.step(state,dt)
                return result,ledger,dt,tuple(failures)
            except (TrialRejected,ValueContractError) as exc:
                failures.append((dt,type(exc).__name__,str(exc)))
                dt*=.5
        raise TrialRejected(('RETRIES_EXHAUSTED',tuple(failures)))

    def sample(self,state,observation_edges):
        """Return geometric pieces and separate physical pressure averages."""
        w=self.recover(state);obs=np.asarray(observation_edges);pieces=[]
        totals=np.zeros((len(obs)-1,12));p=np.zeros(len(obs)-1)
        for j,(a,b) in enumerate(zip(obs[:-1],obs[1:])):
            covered=0.
            for i,(l,r) in enumerate(zip(state.edges[:-1],state.edges[1:])):
                overlap=max(0.,min(b,r)-max(a,l))
                if overlap:
                    amount=state.inventory[i]*(overlap/(r-l))
                    pieces.append((j,i,overlap,frozen(amount)))
                    totals[j]+=amount;p[j]+=overlap*w[i,2];covered+=overlap
            if abs(covered-(b-a))>256*np.finfo(float).eps*max(1,abs(a),abs(b)):
                raise TrialRejected('OBSERVATION_OUTSIDE_DOMAIN')
            p[j]/=b-a
        return frozen(totals),frozen(p),tuple(pieces)

    def split(self,state,index,x):
        """Conservative reorganization only; never mix distinct thermal states."""
        l,r=state.edges[index:index+2]
        if not l<x<r:raise TrialRejected('SPLIT_OUTSIDE_REGION')
        q=state.inventory[index];first=q*((x-l)/(r-l));second=q-first
        out=State(np.insert(state.edges,index+1,x),
                  np.concatenate((state.inventory[:index],[first,second],state.inventory[index+1:])),
                  state.labels[:index]+(state.labels[index],)+state.labels[index:])
        self.recover(out)
        return out
