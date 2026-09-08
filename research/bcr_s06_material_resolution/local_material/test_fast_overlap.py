import numpy as np
from fast_overlap import MonotoneTargets

def original(left,right,edges):
    return [(j,max(0.,min(right,b)-max(left,a)))
            for j,(a,b) in enumerate(zip(edges[:-1],edges[1:]))
            if min(right,b)>max(left,a)]

def test_monotone_targets_exact_order_and_overlap_bits():
    rng=np.random.default_rng(317)
    geometries=[(np.array([-0.,np.nextafter(0.,1.),.5,1.]),np.array([0.,.2,.5,np.nextafter(.5,1.),1.])),
                (np.array([0.,1.]),np.linspace(0,1,1001)),
                (np.linspace(0,1,1001),np.array([0.,1.]))]
    for _ in range(100):
        geometries.append((np.r_[0.,np.sort(rng.random(rng.integers(1,80))),1.],
                           np.r_[0.,np.sort(rng.random(rng.integers(1,80))),1.]))
    for donors,targets in geometries:
        sweep=MonotoneTargets(targets)
        for left,right in zip(donors[:-1],donors[1:]):
            expected=original(left,right,targets);actual=sweep(left,right)
            assert [j for j,_ in actual]==[j for j,_ in expected]
            assert np.array([v for _,v in actual]).tobytes()==np.array([v for _,v in expected]).tobytes()
