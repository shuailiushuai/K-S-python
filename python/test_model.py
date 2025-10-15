"""
Unit Tests for K+S Model Components
Tests individual equations and agent behaviors for correctness.
"""

import unittest
import numpy as np
from python.random_generator import RandomEngine, random_engine
from python.agents import BaseAgent, mov_avg_bound, Vintage, FirmRank
from python.config import *
from python.worker import Worker
from python.bank import Bank
from python.firm1 import Firm1
from python.firm2 import Firm2
from python.vintage import Vint, create_vintage


class TestRandomEngine(unittest.TestCase):
    """Test random number generation consistency"""
    
    def test_seed_reproducibility(self):
        """Test that same seed produces same random numbers"""
        engine1 = RandomEngine(42)
        engine2 = RandomEngine(42)
        
        # Generate sequences
        seq1 = [engine1.uniform() for _ in range(100)]
        seq2 = [engine2.uniform() for _ in range(100)]
        
        # Should be identical
        np.testing.assert_array_almost_equal(seq1, seq2)
    
    def test_distributions(self):
        """Test different distribution functions"""
        engine = RandomEngine(42)
        
        # Uniform
        u = engine.uniform(0, 1)
        self.assertGreaterEqual(u, 0)
        self.assertLess(u, 1)
        
        # Normal
        n = engine.normal(0, 1)
        self.assertIsInstance(n, float)
        
        # Beta
        b = engine.beta(2, 2)
        self.assertGreaterEqual(b, 0)
        self.assertLessEqual(b, 1)
        
        # Poisson
        p = engine.poisson(5)
        self.assertIsInstance(p, int)
        self.assertGreaterEqual(p, 0)


class TestBaseAgent(unittest.TestCase):
    """Test base agent functionality"""
    
    def setUp(self):
        self.agent = BaseAgent(1, "TestAgent")
    
    def test_variable_storage(self):
        """Test variable get/set operations"""
        self.agent.WRITE("test_var", 10.0)
        self.assertEqual(self.agent.V("test_var"), 10.0)
    
    def test_lagged_values(self):
        """Test lagged variable access"""
        self.agent.WRITE("test_var", 10.0)
        self.agent.update_lags()
        self.agent.WRITE("test_var", 20.0)
        
        self.assertEqual(self.agent.V("test_var"), 20.0)
        self.assertEqual(self.agent.VL("test_var", 1), 10.0)
    
    def test_increment(self):
        """Test variable increment"""
        self.agent.WRITE("test_var", 10.0)
        result = self.agent.INCR("test_var", 5.0)
        
        self.assertEqual(result, 15.0)
        self.assertEqual(self.agent.V("test_var"), 15.0)
    
    def test_hooks(self):
        """Test hook system"""
        other_agent = BaseAgent(2, "OtherAgent")
        self.agent.WRITE_HOOK(0, other_agent)
        
        self.assertEqual(self.agent.HOOK(0), other_agent)
    
    def test_children(self):
        """Test parent-child relationships"""
        child = BaseAgent(2, "Child", self.agent)
        self.agent.add_child("Child", child)
        
        self.assertEqual(self.agent.count_children("Child"), 1)
        self.assertIn(child, self.agent.get_children("Child"))


class TestWorker(unittest.TestCase):
    """Test worker agent"""
    
    def setUp(self):
        self.worker = Worker(1)
    
    def test_initial_state(self):
        """Test worker initial state"""
        self.assertEqual(self.worker._employed, 0)
        self.assertEqual(self.worker._s, INISKILL)
        self.assertEqual(self.worker._sV, INISKILL)
        self.assertEqual(self.worker._sT, INISKILL)
    
    def test_skills_computation(self):
        """Test skill computation modes"""
        # Mode 0: skills don't affect productivity
        s = self.worker.compute_skills(flagWorkerSkProd=0)
        self.assertEqual(s, INISKILL)
        
        # Mode 1: only vintage skills
        self.worker._sV = 1.5
        s = self.worker.compute_skills(flagWorkerSkProd=1)
        self.assertEqual(s, 1.5)
        
        # Mode 2: only tenure skills
        self.worker._sT = 1.3
        s = self.worker.compute_skills(flagWorkerSkProd=2)
        self.assertEqual(s, 1.3)
        
        # Mode 3: both skills (average)
        s = self.worker.compute_skills(flagWorkerSkProd=3)
        self.assertAlmostEqual(s, (1.5 + 1.3) / 2)
    
    def test_vintage_skills_update(self):
        """Test vintage skills learning"""
        self.worker._employed = 1  # Employed
        sV = self.worker.update_vintage_skills(sVp=1.2, sigma=0.1)
        
        # Should learn toward sVp
        self.assertGreater(sV, INISKILL)
        self.assertLess(sV, 1.2)
    
    def test_tenure_skills_update(self):
        """Test tenure skills learning"""
        self.worker._employed = 1  # Employed
        initial_sT = self.worker._sT
        sT = self.worker.update_tenure_skills(tauT=0.02, tauU=0.01)
        
        # Should increase for employed
        self.assertGreater(sT, initial_sT)
        
        # Should decrease for unemployed
        self.worker._employed = 0
        sT_unemp = self.worker.update_tenure_skills(tauT=0.02, tauU=0.01)
        self.assertLess(sT_unemp, sT)


class TestBank(unittest.TestCase):
    """Test bank agent"""
    
    def setUp(self):
        self.bank = Bank(1)
    
    def test_initial_state(self):
        """Test bank initial state"""
        self.assertEqual(self.bank._IDb, 1)
        self.assertEqual(self.bank._Depo, 0.0)
        self.assertEqual(self.bank._Loans, 0.0)
    
    def test_bad_debt_fragility(self):
        """Test financial fragility computation"""
        self.bank.WRITE("_BadDeb1", 10.0)
        self.bank.WRITE("_BadDeb2", 5.0)
        self.bank.WRITE("_Loans", 100.0)
        self.bank.update_lags()
        
        Bda = self.bank.compute_bad_debt_fragility()
        self.assertAlmostEqual(Bda, 15.0 / 100.0)
    
    def test_profits(self):
        """Test profit computation"""
        self.bank._Loans = 100.0
        self.bank._Depo = 80.0
        self.bank._Res = 10.0
        self.bank._ExRes = 5.0
        self.bank._BondsB = 10.0
        self.bank._BadDeb1 = 2.0
        self.bank._BadDeb2 = 1.0
        
        PiB = self.bank.compute_profits(rD=0.01, rDeb=0.05, rRes=0.015, rBonds=0.02)
        
        # Interest income - interest expense - bad debt
        expected = (0.05 * 100 + 0.015 * 15 + 0.02 * 10) - (0.01 * 80) - 3.0
        self.assertAlmostEqual(PiB, expected)


class TestFirm1(unittest.TestCase):
    """Test capital-good firm"""
    
    def setUp(self):
        random_engine.seed(42)
        self.firm = Firm1(1)
    
    def test_initial_state(self):
        """Test firm initial state"""
        self.assertEqual(self.firm._ID1, 1)
        self.assertEqual(self.firm._Atau, INIPROD)
        self.assertEqual(self.firm._Btau, INIPROD)
    
    def test_unit_cost(self):
        """Test unit cost computation"""
        self.firm._Btau = 2.0
        c1 = self.firm.compute_unit_cost(w1=1.0, m1=1.0)
        
        self.assertAlmostEqual(c1, 1.0 / 2.0)
    
    def test_price(self):
        """Test price computation"""
        self.firm._c1 = 0.5
        p1 = self.firm.compute_price(mu1=0.25)
        
        self.assertAlmostEqual(p1, 0.5 * 1.25)
    
    def test_production_planning(self):
        """Test production and labor demand"""
        self.firm._D1 = 100.0  # Demand
        self.firm._Btau = 2.0
        self.firm._w1 = 1.0
        self.firm.parent = BaseAgent(0, "Capital")
        self.firm.parent.WRITE("nu", 0.1)
        self.firm.parent.WRITE("m1", 1.0)
        self.firm.WRITE("_S1", 50.0)
        self.firm.update_lags()
        
        Q1, L1d, L1rd = self.firm.compute_production(L1rdMax=0.3)
        
        self.assertEqual(Q1, 100.0)
        self.assertGreater(L1d, 0)
        self.assertGreater(L1rd, 0)


class TestSupportFunctions(unittest.TestCase):
    """Test support functions"""
    
    def test_mov_avg_bound(self):
        """Test moving average growth calculation"""
        values = [110, 105, 100, 95]  # Most recent first
        
        # Without bounds
        g = mov_avg_bound(values, lim=0.0, per=3)
        expected = ((110/105 - 1) + (105/100 - 1) + (100/95 - 1)) / 3
        self.assertAlmostEqual(g, expected)
        
        # With bounds
        g_bounded = mov_avg_bound(values, lim=0.02, per=3)
        self.assertLessEqual(abs(g_bounded), 0.02)
    
    def test_vintage_packing(self):
        """Test vintage ID packing/unpacking"""
        t0 = 10
        supplier = 5
        
        vint_id = VNT(t0, supplier)
        self.assertEqual(T0(vint_id), t0)
        self.assertEqual(SUP(vint_id), supplier)
    
    def test_round_function(self):
        """Test ROUND utility function"""
        self.assertEqual(ROUND(0.51, 0.5, 0.01), 0.51)
        self.assertEqual(ROUND(0.501, 0.5, 0.01), 0.5)  # Within tolerance
        self.assertEqual(ROUND(0.51, 0.5, 0.1), 0.5)


class TestDataStructures(unittest.TestCase):
    """Test data structures"""
    
    def test_vintage(self):
        """Test Vintage dataclass"""
        v = Vintage(sVp=1.5, sVavg=1.3, workers=10)
        self.assertEqual(v.sVp, 1.5)
        self.assertEqual(v.workers, 10)
    
    def test_firm_rank(self):
        """Test FirmRank dataclass"""
        agent = BaseAgent(1, "Firm")
        rank = FirmRank(NWtoS=0.5, firm=agent)
        self.assertEqual(rank.NWtoS, 0.5)
        self.assertEqual(rank.firm, agent)


class TestFirm2(unittest.TestCase):
    """Test Firm2 (consumption sector) agent"""
    
    def setUp(self):
        """Set up test firm"""
        random_engine.seed(42)
        parent = BaseAgent(0, "Consumption", None)
        self.firm = Firm2(1, parent)
        self.firm.WRITE("_NW2", 100.0)
        self.firm.WRITE("_f2", 0.01)
        self.firm.WRITE("_mu2", 0.25)
        self.firm.WRITE("_c2", 1.0)
        self.firm.WRITE("_p2", 1.25)
    
    def test_initial_state(self):
        """Test firm initial state"""
        self.assertEqual(self.firm._ID2, 1)
        self.assertEqual(self.firm.V("_NW2"), 100.0)
        self.assertEqual(self.firm.V("_mu2"), 0.25)
    
    def test_expected_demand(self):
        """Test demand expectation computation"""
        params = {'flagExpect': 0, 'e0': 0.5}
        self.firm._life2cycle = 5  # Not an entrant
        
        # Set current and lagged values properly
        self.firm.vars["_D2"] = [100.0, 90.0]
        self.firm.vars["_D2d"] = [120.0, 110.0]
        
        D2e = self.firm.compute_expected_demand(params, 10)
        self.assertGreater(D2e, 0)
    
    def test_markup_computation(self):
        """Test variable markup"""
        params = {'f2min': 0.001, 'upsilon': 0.02}
        self.firm.WRITE("_f2", 0.01)
        
        mu2 = self.firm.compute_markup(params)
        self.assertGreater(mu2, 0)
    
    def test_competitiveness(self):
        """Test competitiveness index"""
        params = {'omega1': 1.0, 'omega2': 0.0}
        self.firm.WRITE("_p2", 1.25)
        
        E = self.firm.compute_competitiveness(params)
        self.assertGreater(E, 0)


class TestVintage(unittest.TestCase):
    """Test capital vintage management"""
    
    def setUp(self):
        """Set up test vintage"""
        random_engine.seed(42)
        parent = BaseAgent(0, "Firm2", None)
        self.vintage = Vint(1, parent)
    
    def test_vintage_creation(self):
        """Test vintage creation"""
        parent = BaseAgent(0, "Firm2", None)
        vintage = create_vintage(parent, t=10, n_machines=5,
                                productivity_A=1.5, productivity_B=1.4,
                                price=100.0, vintage_id=1)
        
        self.assertEqual(vintage.V("__tVint"), 10)
        self.assertEqual(vintage.V("__nVint"), 5)
        self.assertEqual(vintage.V("__Avint"), 1.5)
    
    def test_scrap_demand(self):
        """Test scrapping decision"""
        params = {'eta': 20, 'b': 3.0, 'm2': 1.0}
        self.vintage.WRITE("__tVint", 5)
        self.vintage.WRITE("__nVint", 10)
        self.vintage.WRITE("__Avint", 1.0)
        self.vintage._Vint__Avint = 1.0  # Set private attribute
        
        scrap = self.vintage.compute_scrap_demand(
            params, t=10, supplier_Atau=1.5, supplier_p1=100.0,
            firm_w2avg=1.0, firm_postChg=False
        )
        
        self.assertGreaterEqual(scrap, 0)


if __name__ == '__main__':
    unittest.main()
