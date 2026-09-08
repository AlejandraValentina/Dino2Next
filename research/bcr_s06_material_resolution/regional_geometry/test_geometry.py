from fractions import Fraction as F
import numpy as np
import pytest
from geometry import VolumeMap,algebra_rhs,manufactured_ssprk2
from dino2next.gasdynamics import PolynomialSegment

def geometry():return VolumeMap(PolynomialSegment(0.,3.,(1.,0.,9.),(1.,)))

def test_volume_integral_matches_exact_polynomial_and_s05():
    g=geometry()
    for x in (0.,.1,.5,1.,2.,3.):
        assert g.exact(x)==F(x)+F(x)**3/3
        assert g.cumulative(x)==float(g.exact(x))
    assert g.segment.integral(.5,1.5)==float(g.exact(1.5)-g.exact(.5))

def test_inverse_returns_enclosed_root_and_explicit_roundoff():
    g=geometry()
    for w in (0.,.1,.7,2.,5.,12.):
        x,(lo,hi),residual=g.inverse(w)
        assert g.exact(lo)<=F(w)<=g.exact(hi)
        assert residual==g.exact(x)-F(w)
        assert lo==hi or np.nextafter(lo,np.inf)==hi
    with pytest.raises(ValueError):g.inverse(-.1)

def test_direct_edge_fe_and_ssprk_fail_geometric_conservation():
    A=lambda x:1+x*x;W=lambda x:x+x**3/3
    left,right,s,dt=F(1,2),F(1),F(1,5),F(1,10)
    volume=W(right)-W(left)
    fe_volume=volume+dt*s*(A(right)-A(left))
    actual_fe=W(right+dt*s)-W(left+dt*s)
    assert actual_fe-fe_volume==F(1,5000)
    rhs0=s*(A(right)-A(left))
    rhs1=s*(A(right+dt*s)-A(left+dt*s))
    final_volume=volume+dt*(rhs0+rhs1)/2
    # Equal face speeds in a quadratic area happen to integrate the volume
    # difference exactly at final RK2; FE-stage violation still remains.
    assert actual_fe==final_volume
    # Unequal face motion exposes a nonzero final mismatch as well.
    sl,sr=F(1,10),F(1,5)
    rhs0=A(right)*sr-A(left)*sl
    rhs1=A(right+dt*sr)*sr-A(left+dt*sl)*sl
    rkvolume=volume+dt*(rhs0+rhs1)/2
    actual=W(right+dt*sr)-W(left+dt*sl)
    assert actual-rkvolume==-(sr**3-sl**3)*dt**3/6

def test_rest_pressure_area_source_cancels_momentum_flux():
    g=geometry();W=np.array([g.cumulative(.5),g.cumulative(1.5)])
    U=np.array([1.,0.,-2e6,0.,0.,1.,0.,0.,0.,0.,1.,0.])
    dW,dQ,flux,source=algebra_rhs(g,W,U,1e5,[0.,0.])
    np.testing.assert_array_equal(dW,[0.,0.])
    np.testing.assert_allclose(dQ,0.,atol=256*np.finfo(float).eps*1e5)
    assert source[1]!=0 and not np.any(source[[0,2,3,4,5,6,7,8,9,10,11]])

def test_volume_coordinate_preserves_all_uniform_inventories_at_every_stage():
    g=geometry();W=np.array([g.cumulative(.5),g.cumulative(1.5)])
    U=np.array([1.,0.,-2e6,0.,0.,.3,.7,0.,0.,0.,1.,0.]);Q=U*np.diff(W)[0]
    newW,newQ,stages=manufactured_ssprk2(g,W,Q,U,1e5,[.1,.2],.01)
    for stageW,stageQ in (*stages,(newW,newQ)):
        np.testing.assert_allclose(stageQ,U*np.diff(stageW)[0],rtol=5e-16,atol=1e-10)
    assert newQ[2]!=Q[2]  # Actual conservative mesh-sweep transfer, not energy repair.
