"""Selected NK-001..004 kernel; physical boundaries and global time policy are injected."""

from dataclasses import dataclass, field
from math import fsum
from types import MappingProxyType
import numpy as np

from dino2next.gasdynamics import DuctState, Mesh1D
from dino2next.thermo import ThermoModel
from dino2next.units import ValueContractError

EPS = np.finfo(float).eps
NONNEGATIVE = (0, *range(3, 12))
CHEM_INDEPENDENT = (3, 4, 6, 7)


def fail(code, path, message, **metadata):
    raise ValueContractError(code, path, message, component="numerics", metadata=metadata)


def frozen_array(value, shape=None, *, boolean=False):
    try:
        a = np.asarray(value, dtype=bool if boolean else np.float64)
    except (ValueError, TypeError, OverflowError) as exc:
        fail("STAGE_INADMISSIBLE", "/array", "Invalid numerical array", reason=str(exc))
    if shape is not None and a.shape != shape:
        fail("STAGE_INADMISSIBLE", "/array", "Array shape differs", actual=a.shape, expected=shape)
    if not boolean and not np.all(np.isfinite(a)):
        fail("STAGE_INADMISSIBLE", "/array", "Nonfinite array")
    # Immutable backing bytes also prevent a caller re-enabling writes.
    return np.frombuffer(a.tobytes(), dtype=a.dtype).reshape(a.shape)


def finite_scalar(value, path):
    if type(value) not in (int, float):
        fail("STAGE_INADMISSIBLE", path, "Expected finite scalar")
    try:
        value=float(value)
    except OverflowError:
        fail("STAGE_INADMISSIBLE",path,"Scalar exceeds binary64")
    if not np.isfinite(value):
        fail("STAGE_INADMISSIBLE",path,"Expected finite scalar")
    return value


def diagnostic_tuple(value):
    if not isinstance(value,(tuple,list)):
        fail("STAGE_INADMISSIBLE","/diagnostics","Expected diagnostic sequence")
    def freeze(v):
        if isinstance(v,(tuple,list)):return tuple(freeze(x) for x in v)
        if isinstance(v,np.generic):v=v.item()
        if v is None or type(v) in (str,int,bool):return v
        if type(v) is float and np.isfinite(v):return v
        fail("STAGE_INADMISSIBLE","/diagnostics","Diagnostic values must be immutable finite scalars/sequences")
    return tuple(freeze(x) for x in value)


@dataclass(frozen=True, slots=True)
class NumericalProfile:
    contract: str = "C1.0-R4 NK-001..004 TS-001 SV-009"
    acoustic_cfl: float = .2
    compression_threshold: float = .33
    flatten_start: float = .75
    flatten_factor: float = 10.
    guard_bisections: int = 54
    roundoff_reductions: int = 8

    def __post_init__(self):
        if (self.contract, self.acoustic_cfl, self.compression_threshold, self.flatten_start,
                self.flatten_factor, self.guard_bisections, self.roundoff_reductions) != (
                "C1.0-R4 NK-001..004 TS-001 SV-009", .2, .33, .75, 10., 54, 8):
            fail("SCIENTIFIC_CHANGE_REQUIRED", "/profile", "Only the frozen numerical profile is supported")


@dataclass(frozen=True, slots=True)
class KernelState:
    mesh: Mesh1D
    Q: np.ndarray
    source_kind: str
    recovery_identity: str

    def __post_init__(self):
        if not isinstance(self.mesh, Mesh1D):
            fail("STAGE_INADMISSIBLE", "/mesh", "Accepted Mesh1D required")
        object.__setattr__(self, "Q", frozen_array(self.Q, (len(self.mesh.dx), 12)))
        if self.source_kind not in ("GEN1_RUNTIME", "NUMERICAL_FIXTURE_ONLY") or not isinstance(self.recovery_identity, str) or not self.recovery_identity:
            fail("STAGE_INADMISSIBLE", "/identity", "Explicit thermodynamic classification/identity required")

    @classmethod
    def from_duct(cls, duct):
        if not isinstance(duct, DuctState):
            fail("STAGE_INADMISSIBLE", "/state", "Expected accepted DuctState")
        return cls(duct.mesh, duct.Q, duct.source_kind, duct.recovery_identity)


@dataclass(frozen=True, slots=True)
class PrimitiveBatch:
    V: np.ndarray
    T: np.ndarray
    e: np.ndarray
    cp: np.ndarray
    cv: np.ndarray
    R: np.ndarray
    a: np.ndarray
    roundoff_records: tuple = ()

    def __post_init__(self):
        a = frozen_array(self.V)
        if a.ndim != 2 or a.shape[1] != 12:
            fail("STAGE_INADMISSIBLE", "/V", "Expected twelve primitive columns")
        object.__setattr__(self, "V", a)
        for name in ("T", "e", "cp", "cv", "R", "a"):
            object.__setattr__(self, name, frozen_array(getattr(self, name), (len(a),)))
        object.__setattr__(self, "roundoff_records", diagnostic_tuple(self.roundoff_records))


@dataclass(frozen=True, slots=True)
class FaceStates:
    left: np.ndarray
    right: np.ndarray
    cell_U: np.ndarray
    cell_V: np.ndarray
    outer_U: np.ndarray
    near: np.ndarray
    contraction: np.ndarray
    flattening: np.ndarray
    boundary: str
    source_kind: str
    recovery_identity: str
    roundoff_records: tuple = ()
    acoustic_extrema: tuple = ()

    def __post_init__(self):
        u = frozen_array(self.cell_U)
        if u.ndim != 2 or u.shape[1] != 12:
            fail("STAGE_INADMISSIBLE", "/cell_U", "Expected twelve conservative columns")
        n = len(u)
        object.__setattr__(self, "cell_U", u)
        for name, shape in (("left", (n+1, 12)), ("right", (n+1, 12)),
                            ("cell_V", (n, 12)), ("outer_U", (n+2, 12))):
            object.__setattr__(self, name, frozen_array(getattr(self, name), shape))
        object.__setattr__(self, "near", frozen_array(self.near, (n,), boolean=True))
        for name in ("contraction", "flattening"):
            a = frozen_array(getattr(self, name), (n,))
            if np.any((a < 0) | (a > 1)):
                fail("STAGE_INADMISSIBLE", "/"+name, "Limiter factor outside [0,1]")
            object.__setattr__(self, name, a)
        if self.boundary not in ("periodic", "physical"):
            fail("STAGE_INADMISSIBLE", "/boundary", "Explicit boundary kind required")
        if type(self.source_kind) is not str or self.source_kind not in ("GEN1_RUNTIME", "NUMERICAL_FIXTURE_ONLY"):
            fail("STAGE_INADMISSIBLE", "/source_kind", "Explicit face thermodynamic classification required")
        if type(self.recovery_identity) is not str or not self.recovery_identity.strip():
            fail("STAGE_INADMISSIBLE", "/recovery_identity", "Immutable nonempty thermodynamic identity required")
        object.__setattr__(self,"roundoff_records",diagnostic_tuple(self.roundoff_records))
        object.__setattr__(self,"acoustic_extrema",diagnostic_tuple(self.acoustic_extrema))


@dataclass(frozen=True, slots=True)
class FaceFluxes:
    high: np.ndarray
    low: np.ndarray
    flux_b: np.ndarray
    physical_boundaries: bool
    diagnostics: tuple = ()

    def __post_init__(self):
        high = frozen_array(self.high)
        if high.ndim != 2 or high.shape[1] != 12:
            fail("STAGE_INADMISSIBLE", "/flux", "Expected twelve face flux columns")
        object.__setattr__(self, "high", high)
        object.__setattr__(self, "low", frozen_array(self.low, high.shape))
        object.__setattr__(self, "flux_b", frozen_array(self.flux_b, (len(high),), boolean=True))
        if type(self.physical_boundaries) is not bool:
            fail("STAGE_INADMISSIBLE", "/physical_boundaries", "Expected boolean")
        if self.physical_boundaries and (not np.array_equal(self.high[[0,-1]], self.low[[0,-1]]) or np.any(self.flux_b[[0,-1]])):
            fail("STAGE_INADMISSIBLE", "/boundary", "Physical boundary flux must be identical in high/low and never flux B")
        object.__setattr__(self,"diagnostics",diagnostic_tuple(self.diagnostics))


@dataclass(frozen=True, slots=True)
class StageRHS:
    fluxes: FaceFluxes
    sources: np.ndarray
    diagnostics: tuple = ()

    def __post_init__(self):
        if not isinstance(self.fluxes, FaceFluxes):
            fail("STAGE_INADMISSIBLE", "/rhs", "Expected FaceFluxes")
        object.__setattr__(self, "sources", frozen_array(self.sources, (len(self.fluxes.high)-1, 12)))
        object.__setattr__(self,"diagnostics",diagnostic_tuple(self.diagnostics))


@dataclass(frozen=True, slots=True)
class StepAttempt:
    state: KernelState | None
    rejection: str | None
    diagnostics: tuple
    face_integrals: np.ndarray | None = None
    source_integrals: np.ndarray | None = None

    def __post_init__(self):
        if (self.state is None) == (self.rejection is None):
            fail("STAGE_INADMISSIBLE", "/attempt", "Accepted state or rejection must be exclusive")
        if self.state is not None and not isinstance(self.state, KernelState):
            fail("STAGE_INADMISSIBLE", "/attempt", "Expected immutable KernelState")
        if self.rejection is not None and (type(self.rejection) is not str or not self.rejection.strip()):
            fail("STAGE_INADMISSIBLE", "/rejection", "Rejection requires a nonempty immutable code string")
        object.__setattr__(self, "diagnostics", diagnostic_tuple(self.diagnostics))
        for name in ("face_integrals", "source_integrals"):
            value = getattr(self, name)
            if value is not None:
                if self.state is None:
                    fail("STAGE_INADMISSIBLE", "/attempt", "Rejected step cannot publish committed ledgers")
                n = len(self.state.Q)
                shape = (n + 1, 12) if name == "face_integrals" else (n, 12)
                object.__setattr__(self, name, frozen_array(value, shape))

    @property
    def accepted(self):
        return self.state is not None


def minmod(a, b):
    return np.where(a*b > 0, np.sign(a)*np.minimum(np.abs(a), np.abs(b)), 0.)


def mc(a, b):
    return minmod((a+b)/2, minmod(2*a, 2*b))


class NumericalKernel:
    """Stateless array backend with constructor-injected, classified EOS."""

    def __init__(self, thermo, *, source_kind="GEN1_RUNTIME", profile=None):
        self.profile = profile or NumericalProfile()
        if not isinstance(self.profile, NumericalProfile):
            fail("SCIENTIFIC_CHANGE_REQUIRED", "/profile", "Expected immutable NumericalProfile")
        self.thermo = thermo
        self.source_kind = source_kind
        if source_kind == "GEN1_RUNTIME" and type(thermo) is ThermoModel:
            self.identity = thermo.dataset.name+" "+thermo.dataset.version+" "+thermo.dataset.sha256
            self._R = np.asarray(thermo.species_properties(300).R)
        elif source_kind == "NUMERICAL_FIXTURE_ONLY":
            if getattr(thermo, "source_kind", None) != source_kind or any(not callable(getattr(thermo, name, None)) for name in (
                    "evaluate_batch", "recover_batch", "species_properties_batch")):
                fail("EOS_OUT_OF_DOMAIN", "/thermo", "Classified fixture batch EOS protocol required")
            reference = getattr(thermo, "reference_sha256", "")
            if not isinstance(reference, str) or len(reference) != 64 or any(c not in "0123456789abcdef" for c in reference):
                fail("EOS_OUT_OF_DOMAIN", "/thermo", "Fixture reference SHA256 required")
            name = getattr(thermo, "identity", None)
            if not isinstance(name, str) or not name:
                fail("EOS_OUT_OF_DOMAIN", "/thermo", "Fixture identity required")
            self.identity = name+" "+reference
        else:
            fail("EOS_OUT_OF_DOMAIN", "/thermo", "GEN1 permits only accepted ThermoModel")

    def state(self, mesh, Q):
        result = KernelState(mesh, Q, self.source_kind, self.identity)
        self.recover(result.Q / np.asarray(mesh.area_averages)[:, None])
        return result

    def _state(self, state):
        state = KernelState.from_duct(state) if isinstance(state, DuctState) else state
        if not isinstance(state, KernelState) or (state.source_kind, state.recovery_identity) != (self.source_kind, self.identity):
            fail("EOS_OUT_OF_DOMAIN", "/identity", "State and kernel thermochemistry differ")
        return state

    def _thermo(self, rho, value, Y, *, recover):
        if self.source_kind == "NUMERICAL_FIXTURE_ONLY":
            rho,value,Y=(frozen_array(a) for a in (rho,value,Y))
            result = (self.thermo.recover_batch(rho, value, Y) if recover else self.thermo.evaluate_batch(rho, value, Y))
            out = {k: np.asarray(result[k], float) for k in ("T", "p", "e", "cp", "cv", "R", "a")}
        else:
            rows = []
            for density, v, y in zip(rho, value, Y):
                y = tuple(map(float, y))
                if recover:
                    r = self.thermo.invert_energy(float(density), float(v), y)
                else:
                    R = fsum(a*b for a,b in zip(y,self._R))
                    r = self.thermo.evaluate(float(v/(density*R)), float(v), y)
                rows.append(r)
            out = {k: np.asarray([getattr(r,k) for r in rows]) for k in ("T", "p", "e", "cp", "cv", "R", "a")}
        if any(v.shape != rho.shape or not np.all(np.isfinite(v)) for v in out.values()) or any(np.any(out[k] <= 0) for k in ("T","p","cp","cv","R","a")):
            fail("EOS_OUT_OF_DOMAIN", "/thermo", "Invalid EOS batch result")
        return out

    def recover(self, U):
        U = np.asarray(U, float)
        if U.ndim != 2 or U.shape[1] != 12 or not np.all(np.isfinite(U)) or np.any(U[:,0] <= 0) or np.any(U[:,3:] < 0):
            fail("EOS_OUT_OF_DOMAIN", "/U", "Inadmissible conservative density/constituents")
        rho, u = U[:,0], U[:,1]/U[:,0]
        Y, tau = U[:,3:8]/rho[:,None], U[:,8:]/rho[:,None]
        records = []
        for name, values in (("chemical",Y),("tracers",tau)):
            sums = np.asarray([fsum(row) for row in values])
            if np.any(np.abs(sums-1)>256*EPS):
                fail("EOS_OUT_OF_DOMAIN", "/"+name, "Constituents do not match stored total density")
            for i in np.flatnonzero(sums != 1):
                records.append((int(i),name,float(sums[i])))
            values /= sums[:,None]
        out = self._thermo(rho, U[:,2]/rho-.5*u*u, Y, recover=True)
        V = np.column_stack((rho,u,out["p"],Y,tau))
        return PrimitiveBatch(V, *(out[k] for k in ("T","e","cp","cv","R","a")), tuple(records))

    def primitive_to_conservative(self, V):
        V = np.asarray(V,float)
        if V.ndim != 2 or V.shape[1] != 12 or not np.all(np.isfinite(V)) or np.any(V[:,0] <= 0) or np.any(V[:,2] <= 0) or np.any(V[:,3:] < 0):
            fail("EOS_OUT_OF_DOMAIN", "/V", "Inadmissible face primitive state")
        for block in (V[:,3:8],V[:,8:]):
            if np.any(np.abs(np.sum(block,axis=1)-1)>256*EPS):
                fail("EOS_OUT_OF_DOMAIN", "/V", "Invalid face simplex")
        out = self._thermo(V[:,0],V[:,2],V[:,3:8],recover=False)
        U = V.copy()
        U[:,1] = V[:,0]*V[:,1]
        U[:,2] = V[:,0]*(out["e"]+.5*V[:,1]**2)
        U[:,3:] *= V[:,0,None]
        return U

    def admissible(self,U):
        try:
            self.recover(U)
            return True
        except ValueContractError:
            return False

    def _faces_valid(self,center,slope,center_U=None):
        result = np.ones(len(center),bool)
        for side in (-.5,.5):
            V=center+side*slope
            unchanged=np.all(V==center,axis=1) if center_U is not None else np.zeros(len(center),bool)
            ids=np.flatnonzero(~unchanged)
            if not len(ids):continue
            try:
                self.primitive_to_conservative(V[ids])
            except ValueContractError:
                for i in ids:
                    try:self.primitive_to_conservative(V[i:i+1])
                    except ValueContractError:result[i]=False
        return result

    @staticmethod
    def _project(d,V,a):
        out = d.copy()
        out[:,0] = (d[:,2]-V[:,0]*a*d[:,1])/(2*a*a)
        out[:,1] = d[:,0]-d[:,2]/(a*a)
        out[:,2] = (d[:,2]+V[:,0]*a*d[:,1])/(2*a*a)
        return out

    @staticmethod
    def _unproject(d,V,a):
        out = d.copy()
        out[:,0] = d[:,0]+d[:,1]+d[:,2]
        out[:,1] = a*(d[:,2]-d[:,0])/V[:,0]
        out[:,2] = a*a*(d[:,0]+d[:,2])
        out[:,5] = -np.sum(out[:,CHEM_INDEPENDENT],axis=1)
        out[:,11] = -np.sum(out[:,8:11],axis=1)
        return out

    def reconstruct(self,state,*,boundary="periodic",ghosts=None):
        state = self._state(state)
        U = state.Q / np.asarray(state.mesh.area_averages)[:,None]
        primitive = self.recover(U)
        if boundary == "periodic":
            extended = np.concatenate((U[np.arange(-4,0)%len(U)],U,U[np.arange(4)%len(U)]))
        elif boundary == "physical":
            if ghosts is None or len(ghosts)!=2:
                fail("STAGE_INADMISSIBLE", "/ghosts", "Physical stencil requires four explicitly supplied ghost cells per side")
            extended = np.concatenate((frozen_array(ghosts[0],(4,12)),U,frozen_array(ghosts[1],(4,12))))
        else:
            fail("STAGE_INADMISSIBLE", "/boundary", "Explicit physical or periodic boundary required")
        ext = self.recover(extended).V
        n=len(U)
        p,u=ext[:,2],ext[:,1]
        J=np.abs(p[2:]-p[:-2])
        W=np.abs(p[4:]-p[:-4])
        strong=np.zeros(len(ext),bool)
        strong[2:-2]=(W>0)&(J[1:-1]/np.minimum(p[1:-3],p[3:-1])>.33)&(u[1:-3]>u[3:-1])
        chi=np.zeros(len(ext))
        inside=np.flatnonzero(strong)
        chi[inside]=np.maximum(0,np.minimum(1,10*(np.abs(p[inside+1]-p[inside-1])/np.abs(p[inside+2]-p[inside-2])-.75)))
        center=primitive.V
        near=np.logical_or.reduce([strong[4+j:4+j+n] for j in range(-2,3)])
        flatten=1-np.maximum.reduce([chi[3:3+n],chi[4:4+n],chi[5:5+n]])
        dl=self._project(center-ext[3:3+n],center,primitive.a)
        dr=self._project(ext[5:5+n]-center,center,primitive.a)
        # SV-009: every difference uses this center's SAME primitive basis L_i.
        dmm=self._project(ext[3:3+n]-ext[2:2+n],center,primitive.a)
        dpp=self._project(ext[6:6+n]-ext[5:5+n],center,primitive.a)
        amplitudes=mc(dl,dr)
        extrema=[]
        for k in (0,2):
            active=(~near)&(np.minimum(dl[:,k]*dr[:,k],dmm[:,k]*dpp[:,k])<0)
            ids=np.flatnonzero(active)
            dm,dp=dl[ids,k],dr[ids,k]
            dc=(dm+dp)/2
            qm,qc,qp=dm-dmm[ids,k],dp-dm,dpp[ids,k]-dp
            s2=np.sign(qc)
            curvature=np.minimum(np.abs(qc),np.minimum(np.maximum(s2*qm,0),np.maximum(s2*qp,0)))
            side=np.where(s2*dc<0,np.abs(dm),np.abs(dp))
            bound=np.minimum((3/2)*(5/4)*curvature,2*side)
            selected=np.sign(dc)*np.minimum(np.abs(dc),bound)
            extrema.extend((int(i),k,float(amplitudes[i,k]),float(value)) for i,value in zip(ids,selected))
            amplitudes[ids,k]=selected
            amplitudes[near,k]=minmod(dl[near,k],dr[near,k])
        slope=self._unproject(amplitudes,center,primitive.a)
        valid=self._faces_valid(center,slope,U)
        contraction=np.ones(n)
        ids=np.flatnonzero(~valid)
        if len(ids):
            lo=np.zeros(len(ids)); hi=np.ones(len(ids))
            if not np.all(self._faces_valid(center[ids],slope[ids]*0,U[ids])):
                fail("EOS_OUT_OF_DOMAIN", "/reconstruct", "Cell-average faces are inadmissible")
            for _ in range(54):
                mid=(lo+hi)/2
                passed=self._faces_valid(center[ids],slope[ids]*mid[:,None],U[ids])
                lo=np.where(passed,mid,lo); hi=np.where(passed,hi,mid)
            contraction[ids]=lo
        slope*=contraction[:,None]*flatten[:,None]
        if not np.all(self._faces_valid(center,slope,U)):
            fail("EOS_OUT_OF_DOMAIN", "/reconstruct", "Returned contracted/flattened face is inadmissible")
        def face(side):
            V=center+side*slope
            changed=np.any(V!=center,axis=1)
            result=U.copy()
            if np.any(changed):result[changed]=self.primitive_to_conservative(V[changed])
            return result
        minus,plus=face(-.5),face(.5)
        left=np.vstack((plus[-1] if boundary=="periodic" else extended[3],plus))
        right=np.vstack((minus,minus[0] if boundary=="periodic" else extended[-4]))
        return FaceStates(left,right,U,center,extended[3:-3],near,contraction,flatten,boundary,self.source_kind,self.identity,
                          primitive.roundoff_records,tuple(extrema))

    def physical_flux(self,U):
        U=np.asarray(U,float); p=self.recover(U).V
        F=U*p[:,1,None]
        F[:,0]=U[:,1]
        F[:,1]+=p[:,2]
        F[:,2]+=p[:,1]*p[:,2]
        return F

    def hllc(self,left,right):
        left,right=np.asarray(left,float),np.asarray(right,float)
        l,r=self.recover(left),self.recover(right)
        rhoL,uL,pL=l.V[:,:3].T; rhoR,uR,pR=r.V[:,:3].T
        SL=np.minimum(uL-l.a,uR-r.a); SR=np.maximum(uL+l.a,uR+r.a)
        FL,FR=self.physical_flux(left),self.physical_flux(right)
        F=np.empty_like(left)
        ml=SL>=0; mr=SR<=0; middle=~(ml|mr)
        F[ml]=FL[ml]; F[mr]=FR[mr]
        ids=np.flatnonzero(middle)
        if len(ids):
            denominator=rhoL[ids]*(SL[ids]-uL[ids])-rhoR[ids]*(SR[ids]-uR[ids])
            if np.any(denominator==0):
                fail("STAGE_INADMISSIBLE","/hllc","Degenerate Davis contact denominator")
            contact=(pR[ids]-pL[ids]+rhoL[ids]*uL[ids]*(SL[ids]-uL[ids])-rhoR[ids]*uR[ids]*(SR[ids]-uR[ids]))/denominator
            for use_left in (True,False):
                selected=contact>=0 if use_left else contact<0
                ix=ids[selected]; star=contact[selected]
                if not len(ix):continue
                Uk,Pk,Fk,S=(left,l.V,FL,SL) if use_left else (right,r.V,FR,SR)
                rho,u,p=Pk[ix,:3].T
                if np.any(S[ix]-star==0) or np.any(S[ix]-u==0):
                    fail("STAGE_INADMISSIBLE","/hllc","Degenerate star-state denominator")
                density=rho*(S[ix]-u)/(S[ix]-star)
                energy=Uk[ix,2]/rho+(star-u)*(star+p/(rho*(S[ix]-u)))
                Ustar=Uk[ix]*(density/rho)[:,None]
                Ustar[:,1]=density*star; Ustar[:,2]=density*energy
                if not self.admissible(Ustar):
                    fail("STAGE_INADMISSIBLE","/hllc","Davis star state is inadmissible")
                F[ix]=Fk[ix]+S[ix,None]*(Ustar-Uk[ix])
        return F

    def _species(self,T):
        if self.source_kind=="NUMERICAL_FIXTURE_ONLY":
            values=self.thermo.species_properties_batch(frozen_array(T))
            result={key:np.asarray(values[key],float) for key in ("e","cv","R")}
        else:
            rows=[self.thermo.species_properties(float(t)) for t in T]
            result={key:np.asarray([getattr(row,key) for row in rows]) for key in ("e","cv","R")}
        if any(a.shape!=(len(T),5) or not np.all(np.isfinite(a)) for a in result.values()):
            fail("EOS_OUT_OF_DOMAIN","/species","Invalid independent-species EOS batch")
        return result

    def secant_action(self,left,right,delta,*,absolute=False):
        """NK-003 full NASA secant action, including all chemical and origin columns."""
        L,R,d=np.asarray(left,float),np.asarray(right,float),np.asarray(delta,float)
        if L.shape!=R.shape or d.shape!=L.shape or L.ndim!=2 or L.shape[1]!=12:
            fail("STAGE_INADMISSIBLE","/secant","Aligned twelve-column state/delta batches required")
        l,r=self.recover(L),self.recover(R)
        sl,sr=self._species(l.T),self._species(r.T)
        dt=r.T-l.T
        ed=sl["cv"].copy()
        differing=dt!=0
        ed[differing]=(sr["e"][differing]-sl["e"][differing])/dt[differing,None]
        partial=(L[:,3:8]+R[:,3:8])/2
        denominator=np.sum(partial*ed,axis=1)
        if np.any(denominator<=0) or not np.all(np.isfinite(denominator)):
            fail("ROE_SECANT_NONHYPERBOLIC","/secant","Nonpositive secant heat-capacity denominator",
                 denominator=tuple(map(float,denominator)))
        beta=np.sum(partial*sl["R"],axis=1)/denominator
        zeta=(l.T+r.T)[:,None]*sl["R"]/2-beta[:,None]*(sl["e"]+sr["e"])/2
        wl,wr=np.sqrt(L[:,0]),np.sqrt(R[:,0]); weight=wl+wr
        mean=lambda a,b:(wl[:,None]*a+wr[:,None]*b)/weight[:,None]
        velocity=(wl*l.V[:,1]+wr*r.V[:,1])/weight
        H=(wl*(L[:,2]+l.V[:,2])/L[:,0]+wr*(R[:,2]+r.V[:,2])/R[:,0])/weight
        Y=mean(l.V[:,3:8],r.V[:,3:8]); tau=mean(l.V[:,8:],r.V[:,8:])
        a2=np.sum(zeta*Y,axis=1)+beta*(H-.5*velocity*velocity)
        if np.any(a2<=0) or not np.all(np.isfinite(a2)):
            fail("ROE_SECANT_NONHYPERBOLIC","/secant","Nonpositive secant sound-speed square",
                 acoustic_square=tuple(map(float,a2)),left=tuple(map(tuple,L)),right=tuple(map(tuple,R)))
        dp=beta*(d[:,2]-velocity*d[:,1]+.5*velocity**2*d[:,0])+np.sum(zeta*d[:,3:8],axis=1)
        if absolute:
            a=np.sqrt(a2)
            dm=d[:,1]-velocity*d[:,0]
            minus=(dp-a*dm)/(2*a2); plus=(dp+a*dm)/(2*a2)
            acoustic_minus=np.column_stack((np.ones(len(L)),velocity-a,H-velocity*a,Y,tau))
            acoustic_plus=np.column_stack((np.ones(len(L)),velocity+a,H+velocity*a,Y,tau))
            material=d-minus[:,None]*acoustic_minus-plus[:,None]*acoustic_plus
            return (np.abs(velocity-a)[:,None]*minus[:,None]*acoustic_minus+
                    np.abs(velocity+a)[:,None]*plus[:,None]*acoustic_plus+
                    np.abs(velocity)[:,None]*material)
        out=np.empty_like(d)
        out[:,0]=d[:,1]
        out[:,1]=-velocity**2*d[:,0]+2*velocity*d[:,1]+dp
        out[:,2]=-velocity*H*d[:,0]+H*d[:,1]+velocity*(d[:,2]+dp)
        transport=d[:,1]-velocity*d[:,0]
        out[:,3:8]=velocity[:,None]*d[:,3:8]+Y*transport[:,None]
        out[:,8:]=velocity[:,None]*d[:,8:]+tau*transport[:,None]
        return out

    def flux_b(self,a,b,c,d):
        fa,fb,fc,fd=(self.physical_flux(x) for x in (a,b,c,d))
        star_b=(fa+fc-self.secant_action(a,c,c-2*b+a))/2
        star_c=(fb+fd-self.secant_action(b,d,d-2*c+b))/2
        return (star_b+star_c-self.secant_action(a,d,c-b,absolute=True))/2

    def interior_flux(self,faces,*,boundary_flux=None):
        if not isinstance(faces,FaceStates) or (faces.source_kind,faces.recovery_identity)!=(self.source_kind,self.identity):
            fail("EOS_OUT_OF_DOMAIN","/faces","Face classification/identity differs from kernel")
        n=len(faces.cell_U)
        high=np.empty((n+1,12))
        physical=faces.boundary=="physical"
        selected=np.zeros(n+1,bool)
        if n>1:selected[1:-1]=faces.near[:-1]|faces.near[1:]
        if not physical:selected[[0,-1]]=faces.near[-1]|faces.near[0]
        hllc_faces=~selected
        hllc_faces[-1]=False  # Periodic final face is the same shared face as zero.
        if physical:
            if boundary_flux is None or len(boundary_flux)!=2:
                fail("STAGE_INADMISSIBLE","/boundary_flux","Two prescribed physical face fluxes required")
            high[0]=frozen_array(boundary_flux[0],(12,))
            high[-1]=frozen_array(boundary_flux[1],(12,))
            hllc_faces[0]=False
        if np.any(hllc_faces):
            high[hllc_faces]=self.hllc(faces.left[hllc_faces],faces.right[hllc_faces])
        lowL,lowR=faces.outer_U[:-1],faces.outer_U[1:]
        pl,pr=self.recover(lowL),self.recover(lowR)
        speed=np.maximum(np.abs(pl.V[:,1])+pl.a,np.abs(pr.V[:,1])+pr.a)
        low=(self.physical_flux(lowL)+self.physical_flux(lowR)-speed[:,None]*(lowR-lowL))/2
        ids=np.flatnonzero(selected[1:-1])+1
        if len(ids):
            e=faces.outer_U
            high[ids]=self.flux_b(e[ids-1],e[ids],e[ids+1],e[ids+2])
        if physical:
            low[[0,-1]]=high[[0,-1]]
        else:
            if selected[0]:
                u=faces.cell_U
                high[0]=self.flux_b(u[[-2%n]],u[[-1]],u[[0]],u[[1%n]])[0]
            high[-1]=high[0]; low[-1]=low[0]
        records=(
            ("derived_fraction_roundoff",faces.roundoff_records),
            ("acoustic_extrema",faces.acoustic_extrema),
            ("reconstruction_contraction",tuple((int(i),float(faces.contraction[i])) for i in np.flatnonzero(faces.contraction<1))),
            ("flattening",tuple((int(i),float(faces.flattening[i])) for i in np.flatnonzero(faces.flattening<1))),
            ("flux_b_faces",tuple(map(int,np.flatnonzero(selected)))),
        )
        return FaceFluxes(high,low,selected,physical,records)

    @staticmethod
    def divergence(flux,mesh):
        weighted=np.asarray(flux)*np.asarray(mesh.face_areas)[:,None]
        return -(weighted[1:]-weighted[:-1])/np.asarray(mesh.dx)[:,None]

    def _mapped(self,Z,time,mapper):
        frozen=frozen_array(Z)
        Q=frozen if mapper is None else mapper(frozen,time)
        return frozen_array(Q,frozen.shape)

    def _guard(self,state,Zbase,Zinitial,stage_rhs,dt,end_time,mapper,*,second):
        mesh=state.mesh; area=np.asarray(mesh.area_averages)[:,None]
        H,L=stage_rhs.fluxes.high,stage_rhs.fluxes.low
        if stage_rhs.sources.shape!=state.Q.shape:
            fail("STAGE_INADMISSIBLE","/sources","Source and state shapes differ")

        def candidate(theta):
            # Recompute from the actual returned shared flux, never interpolate
            # repaired inventories or individually limited face/cell components.
            flux=L+theta*(H-L) if theta!=1 else H
            Z=Zbase+dt*(self.divergence(flux,mesh)+stage_rhs.sources)
            Q=self._mapped(Z,end_time,mapper)
            checks=[Q]
            if second:checks.append(self._mapped((Zinitial+Z)/2,end_time,mapper))
            good=all(self.admissible(q/area) for q in checks)
            return good,Z,flux,checks

        high=candidate(1.)
        if high[0]:return high[1],high[2],1.,0
        low=candidate(0.)
        if not low[0]:
            fail("STAGE_INADMISSIBLE","/guard","LOW_ORDER_STAGE_INADMISSIBLE_RETRY_DT",
                 reason="LOW_ORDER_STAGE_INADMISSIBLE_RETRY_DT",stage=2 if second else 1)
        cap=1.
        for qlo,qhi in zip(low[3],high[3]):
            a,b=qlo[:,NONNEGATIVE],qhi[:,NONNEGATIVE]
            negative=b<0
            if np.any(negative):
                cap=min(cap,float(np.min(a[negative]/(a-b)[negative])))
        lo,hi=0.,cap
        for _ in range(54):
            mid=(lo+hi)/2
            if candidate(mid)[0]:lo=mid
            else:hi=mid
        for reduction in range(9):
            result=candidate(lo)
            if result[0]:return result[1],result[2],lo,reduction
            lo*=1-32*EPS
        fail("STAGE_INADMISSIBLE","/guard","FLUX_LIMIT_ROUND_OFF_RETRY_DT",
             reason="FLUX_LIMIT_ROUND_OFF_RETRY_DT")

    def propose_step(self,state,rhs,time,dt,*,trial_state_mapper=None,initial_Z=None):
        """One immutable unsplit SSPRK2 proposal; rejection performs no retry."""
        state=self._state(state)
        time=finite_scalar(time,"/time"); dt=finite_scalar(dt,"/dt")
        if dt<=0 or not np.isfinite(time+dt) or time+dt<=time:
            fail("STAGE_INADMISSIBLE","/dt","Positive representable time step required")
        if not callable(rhs) or (trial_state_mapper is not None and not callable(trial_state_mapper)):
            fail("STAGE_INADMISSIBLE","/callback","Read-only RHS/mapper callbacks required")
        if trial_state_mapper is not None and initial_Z is None:
            fail("STAGE_INADMISSIBLE","/initial_Z","Prescribed source mapping requires explicit initial transformed state")
        Z0=frozen_array(state.Q if initial_Z is None else initial_Z,state.Q.shape)
        diagnostics=[]
        try:
            self.recover(state.Q/np.asarray(state.mesh.area_averages)[:,None])
            if not np.array_equal(self._mapped(Z0,time,trial_state_mapper),state.Q):
                fail("STAGE_INADMISSIBLE","/initial_Z","Initial physical mapping differs from accepted state")
            K0=rhs(state,time)
            if not isinstance(K0,StageRHS):
                fail("STAGE_INADMISSIBLE","/rhs","Callback must return immutable StageRHS")
            diagnostics.extend(("rhs",1,*entry) for entry in K0.fluxes.diagnostics+K0.diagnostics)
            Z1,F0,theta0,reductions0=self._guard(state,Z0,Z0,K0,dt,time+dt,trial_state_mapper,second=False)
            diagnostics.append(("stage",1,"theta",theta0,"roundoff_reductions",reductions0))
            Q1=self._mapped(Z1,time+dt,trial_state_mapper)
            stage1=KernelState(state.mesh,Q1,state.source_kind,state.recovery_identity)
            K1=rhs(stage1,time+dt)
            if not isinstance(K1,StageRHS):
                fail("STAGE_INADMISSIBLE","/rhs","Callback must return immutable StageRHS")
            diagnostics.extend(("rhs",2,*entry) for entry in K1.fluxes.diagnostics+K1.diagnostics)
            Z2,F1,theta1,reductions1=self._guard(state,Z1,Z0,K1,dt,time+dt,trial_state_mapper,second=True)
            diagnostics.append(("stage",2,"theta",theta1,"roundoff_reductions",reductions1))
            Qnew=self._mapped((Z0+Z2)/2,time+dt,trial_state_mapper)
            accepted=self.state(state.mesh,Qnew)
            face_integrals=dt*(F0+F1)/2*np.asarray(state.mesh.face_areas)[:,None]
            source_integrals=dt*(K0.sources+K1.sources)/2*np.asarray(state.mesh.dx)[:,None]
            return StepAttempt(accepted,None,tuple(diagnostics),face_integrals,source_integrals)
        except ValueContractError as exc:
            diagnostics.append(("failure",exc.code,exc.path,exc.message))
            def evidence(value):
                if isinstance(value,(tuple,list)):return tuple(evidence(x) for x in value)
                if isinstance(value,np.generic):value=value.item()
                if type(value) is float and not np.isfinite(value):return repr(value)
                if type(value) in (str,int,bool,float) or value is None:return value
                return repr(value)
            diagnostics.append(("failure_metadata",tuple((str(k),evidence(v)) for k,v in exc.metadata.items())))
            return StepAttempt(None,exc.metadata.get("reason",exc.code),tuple(diagnostics))
