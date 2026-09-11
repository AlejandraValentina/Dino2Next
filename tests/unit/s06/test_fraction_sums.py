"""Bitwise contract for the nonnegative internal fraction-sum optimization."""
from math import fsum
import numpy as np
import pytest
from dino2next.numerics import NumericalKernel
from dino2next.units import ValueContractError
from .conftest import primitive


@pytest.mark.parametrize('width',[4,5])
def test_sparse_and_dense_fsum_bitwise(width):
    tiny=np.nextafter(0.,1.);rows=[]
    for zero in (0.,-0.):
        rows.append([zero]*width)
        for position in range(width):
            for value in (tiny,np.finfo(float).tiny,1.,np.nextafter(1.,0.),np.nextafter(1.,2.),1e300):
                row=[zero]*width;row[position]=value;rows.append(row)
    rows.extend([[1.,2**-53,tiny]+[0.]*(width-3),
                 [tiny,tiny,tiny]+[-0.]*(width-3),
                 [1e300,1e-300,1.]+[0.]*(width-3)])
    rng=np.random.default_rng(8128)
    rows.extend(np.ldexp(rng.random((400,width)),rng.integers(-1074,900,(400,width))))
    values=np.array(rows);before=values.tobytes()
    expected=np.array([fsum(row) for row in values])
    actual=NumericalKernel._fraction_sums(values)
    assert actual.tobytes()==expected.tobytes()
    assert values.tobytes()==before


def test_empty_noncontiguous_and_overflow_semantics():
    assert NumericalKernel._fraction_sums(np.empty((0,5))).shape==(0,)
    values=np.array([[0.,1.,-0.,1.,0.,1.,0.,1.]])[...,::2]
    assert not values.flags.c_contiguous
    assert NumericalKernel._fraction_sums(values).tobytes()==np.array([fsum(values[0])]).tobytes()
    with pytest.raises(OverflowError):NumericalKernel._fraction_sums(np.array([[1e308,1e308,0.,0.]]))


@pytest.mark.parametrize('invalid',[-1e-300,float('nan'),float('inf')])
def test_recovery_rejects_invalid_constituents_before_sparse_path(kernel,monkeypatch,invalid):
    U=kernel.primitive_to_conservative(primitive(1.,0.,1e5,2))
    U=U.copy();U[0,3]=invalid
    def forbidden(_):raise AssertionError('Invalid input reached sparse sum')
    monkeypatch.setattr(NumericalKernel,'_fraction_sums',staticmethod(forbidden))
    with pytest.raises(ValueContractError):kernel.recover(U)
