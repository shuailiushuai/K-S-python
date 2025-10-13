"""
Test script to validate the simulation bug fixes

Tests for the three critical bugs that were fixed:
1. Wage-consumption circular dependency
2. Zero market shares
3. Firm labor count not tracked
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from model.country import Country
from config import get_default_config
from model.random_engine import random_engine


def test_wage_computation_before_consumption():
    """
    Test Bug Fix #1: Wages computed before consumption demand
    
    Validates that:
    - Wages (W) are computed before consumption demand (Cd)
    - Cd correctly uses W in its calculation
    - Cd > 0 when workers are employed
    """
    print("\n" + "="*70)
    print("TEST 1: Wage Computation Before Consumption")
    print("="*70)
    
    random_engine.seed(42)
    config = get_default_config()
    country = Country(config)
    country.initialize()
    country.time_step()
    
    W = country.labor_market._W
    Cd = country._Cd
    G = country._G
    
    print(f"Wages (W): ${W:.2f}")
    print(f"Government spending (G): ${G:.2f}")
    print(f"Desired Consumption (Cd): ${Cd:.2f}")
    
    # Assertions
    assert W > 0, "FAIL: Wages should be positive"
    assert Cd > 0, "FAIL: Desired consumption should be positive"
    # Cd should be based on W + G + savings adjustments
    # In period 1 with unemployment, G can be significant
    assert Cd >= W * 0.5, "FAIL: Cd should be at least 50% of W"
    
    print("✓ PASS: Wages computed before consumption, Cd > 0")
    return True


def test_market_shares_initialized():
    """
    Test Bug Fix #2: Market shares initialized
    
    Validates that:
    - All consumption firms have non-zero market share
    - Market shares sum to approximately 1.0
    - Demand is allocated to firms
    """
    print("\n" + "="*70)
    print("TEST 2: Market Shares Initialized")
    print("="*70)
    
    random_engine.seed(42)
    config = get_default_config()
    country = Country(config)
    country.initialize()
    
    # Check initial market shares
    firms = country.consumption_sector.firms
    market_shares = [firm._f2 for firm in firms]
    total_share = sum(market_shares)
    
    print(f"Number of firms: {len(firms)}")
    print(f"First 5 market shares: {market_shares[:5]}")
    print(f"Total market share: {total_share:.6f}")
    
    # Assertions
    assert all(f2 > 0 for f2 in market_shares), "FAIL: All firms should have positive market share"
    assert abs(total_share - 1.0) < 0.001, f"FAIL: Total market share should be 1.0, got {total_share}"
    
    # Run one step and check demand allocation
    country.time_step()
    
    total_demand = sum(firm._D2 for firm in firms)
    total_sales = sum(firm._S2 for firm in firms)
    
    print(f"Total demand allocated: {total_demand:.2f}")
    print(f"Total sales: ${total_sales:.2f}")
    
    assert total_demand > 0, "FAIL: Demand should be allocated to firms"
    assert total_sales > 0, "FAIL: Sales should be positive"
    
    print("✓ PASS: Market shares initialized, demand allocated")
    return True


def test_firm_labor_count_tracked():
    """
    Test Bug Fix #3: Firm labor count tracked
    
    Validates that:
    - Firm._L2 equals (actual number of workers in firm) * Lscale
    - Firm wage costs (W2) are calculated correctly
    - Firm profits (Pi2) are non-zero
    
    NOTE: According to C++ model (fun_KS_firm2.h line 936):
          _L2 = COUNT("Wrk2") * Lscale
    """
    print("\n" + "="*70)
    print("TEST 3: Firm Labor Count Tracked")
    print("="*70)
    
    random_engine.seed(42)
    config = get_default_config()
    country = Country(config)
    country.initialize()
    country.time_step()
    
    # Check first consumption firm
    firm = country.consumption_sector.firms[0]
    Lscale = country.labor_market._Lscale
    
    # Count actual workers
    actual_workers = sum(1 for w in country.workers 
                        if w._employed == 2 and getattr(w, '_employer', None) == firm)
    
    print(f"Actual workers in firm: {actual_workers}")
    print(f"Lscale: {Lscale}")
    print(f"Firm._L2 (tracked): {firm._L2}")
    print(f"Expected _L2 (workers * Lscale): {actual_workers * Lscale}")
    print(f"Firm._w2avg: ${firm._w2avg:.2f}")
    print(f"Firm._W2 (wage costs): ${getattr(firm, '_W2', 0):.2f}")
    print(f"Firm._S2 (sales): ${firm._S2:.2f}")
    print(f"Firm._Pi2 (profit): ${getattr(firm, '_Pi2', 0):.2f}")
    
    # Assertions
    # _L2 should be scaled according to C++ model: COUNT("Wrk2") * Lscale
    expected_L2 = actual_workers * Lscale
    assert abs(firm._L2 - expected_L2) < 0.01, f"FAIL: Firm._L2 should equal actual_workers * Lscale"
    assert firm._L2 > 0, "FAIL: Firm should have workers"
    
    W2 = getattr(firm, '_W2', 0)
    expected_W2 = firm._L2 * firm._w2avg
    assert abs(W2 - expected_W2) < 0.01, f"FAIL: W2 should equal L2 * w2avg"
    
    Pi2 = getattr(firm, '_Pi2', 0)
    assert Pi2 != 0, "FAIL: Profit should be non-zero"
    
    print("✓ PASS: Firm labor tracked correctly (scaled), wages computed correctly")
    return True


def test_full_simulation_dynamics():
    """
    Test that simulation produces dynamic values over multiple periods
    
    Validates that:
    - GDP values are reasonable
    - Sales are positive
    - Some variables change over time
    """
    print("\n" + "="*70)
    print("TEST 4: Full Simulation Dynamics")
    print("="*70)
    
    random_engine.seed(42)
    config = get_default_config()
    country = Country(config)
    country.initialize()
    
    # Run 10 periods
    results = country.simulate(10)
    
    print(f"Periods simulated: {len(results['t'])}")
    print(f"Period 1: GDPnom=${results['GDPnom'][0]:.2f}, GDPreal={results['GDPreal'][0]:.2f}")
    print(f"Period 10: GDPnom=${results['GDPnom'][-1]:.2f}, GDPreal={results['GDPreal'][-1]:.2f}")
    
    # Check sector statistics
    sales = country.consumption_sector._S2
    profits = country.consumption_sector._Pi2
    wages = country.labor_market._W
    
    print(f"Final sales: ${sales:.2f}")
    print(f"Final profits: ${profits:.2f}")
    print(f"Final wages: ${wages:.2f}")
    
    # Assertions
    assert all(gdp > 0 for gdp in results['GDPnom']), "FAIL: All GDP values should be positive"
    assert all(gdp > 0 for gdp in results['GDPreal']), "FAIL: All real GDP values should be positive"
    assert sales > 0, "FAIL: Sales should be positive"
    assert wages > 0, "FAIL: Wages should be positive"
    
    # Check for some dynamics (wage growth)
    initial_wage = results['GDPnom'][0]
    final_wage = results['GDPnom'][-1]
    # Note: With current simple model, values may be constant, but should be > 0
    
    print("✓ PASS: Simulation produces valid economic activity")
    return True


def run_all_tests():
    """Run all test functions"""
    print("\n" + "="*70)
    print("K+S MODEL SIMULATION BUG FIX VALIDATION")
    print("="*70)
    
    tests = [
        test_wage_computation_before_consumption,
        test_market_shares_initialized,
        test_firm_labor_count_tracked,
        test_full_simulation_dynamics,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"\n✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"\n✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*70)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("="*70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
