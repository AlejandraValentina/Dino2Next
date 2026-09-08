"""Bounded independent-reference checks; never imports the kernel."""
import unittest
import numpy as np
import reference as r

class ReferenceChecks(unittest.TestCase):
    def test_original_case_inventory(self):
        self.assertEqual(len(r.cases()),18)
        self.assertEqual(len(set(c.name for c in r.cases())),18)
    def test_material_contact_fraction(self):
        s=r.solve(r.Case(2,100));a=s.cell_averages([.58,.62],.001)
        np.testing.assert_allclose(a['conserved'][0],.5*(s.initial_left[9:]+s.initial_right[9:]),rtol=1e-13,atol=1e-12)
        self.assertEqual(a['conserved'].shape,(1,12));self.assertEqual(a['rhoY'].shape,(1,5))
        np.testing.assert_allclose(a['rhoY'].sum(axis=-1),a['rho'])
        np.testing.assert_allclose(a['conserved'][:,10],a['rho'])
    def test_constant_far_states(self):
        s=r.solve(r.Case(2,0,10));a=s.cell_averages([-2,-1,2,3],.0002)
        np.testing.assert_allclose(a['conserved'][0],s.initial_left[9:])
        np.testing.assert_allclose(a['conserved'][-1],s.initial_right[9:])
    def test_primitive_average_is_direct(self):
        s=r.solve(r.Case(1,0));a=s.cell_averages([.4,.6],0)
        self.assertAlmostEqual(a['T'][0],1200.)
        self.assertAlmostEqual(a['p'][0],1e5)
    def test_shock_RH(self):
        for case in r.cases()[9:]:
            s=r.solve(case);q=s.star_right[9:];qi=s.initial_right[9:]
            def flux(row):
                f=row[9:]*row[1];f=f.copy();f[1]+=row[2];f[2]+=row[2]*row[1];return f
            residual=flux(s.star_right)-flux(s.initial_right)-s.shock_speed*(q-qi)
            scale=np.maximum(1,np.maximum(abs(flux(s.star_right)),abs(s.shock_speed*q)))
            self.assertLess(float(np.max(abs(residual)/scale)),1e-12)
    def test_fan_matches_end_states(self):
        s=r.solve(r.Case(2,0,10));got=s.fan_rows(np.array([s.head,s.tail]))
        np.testing.assert_allclose(got[0],s.initial_left,rtol=1e-12,atol=1e-8)
        np.testing.assert_allclose(got[1],s.star_left,rtol=1e-12,atol=1e-8)
    def test_no_point_average_confusion_at_initial_interface(self):
        s=r.solve(r.Case(0,0));q=s.cell_averages([.49,.51],0)
        self.assertNotAlmostEqual(q['rho'][0],s.point_states([.5],0)['rho'][0])

if __name__=='__main__':unittest.main()
