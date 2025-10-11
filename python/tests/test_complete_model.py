#!/usr/bin/env python3
"""
Complete K+S Model Validation Test
Tests all major components and equations
"""

from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from model import Country
from config import load_scenario
import sys


def test_basic_simulation():
    """Test basic simulation functionality"""
    print("\n" + "="*70)
    print("TEST 1: Basic Simulation (10 periods)")
    print("="*70)
    
    country = Country()
    country.initialize()
    
    print(f"Initial state:")
    print(f"  Firms (Sector 1): {len(country.capital_sector.firms)}")
    print(f"  Firms (Sector 2): {len(country.consumption_sector.firms)}")
    print(f"  Banks: {len(country.financial_sector.banks)}")
    print(f"  Workers (actual): {len(country.workers)}")
    print(f"  Labor supply (notional): {country.labor_market._Ls}")
    
    # Run 10 periods
    results = country.simulate(10)
    
    print(f"\nAfter 10 periods:")
    print(f"  GDP (real): {results['GDPreal'][-1]:.2f}")
    print(f"  GDP (nominal): {results['GDPnom'][-1]:.2f}")
    print(f"  Unemployment: {results['Unemployment'][-1]*100:.2f}%")
    print(f"  Inflation: {results['Inflation'][-1]:.2f}%")
    print(f"  Debt: {results['Debt'][-1]:.2f}")
    print(f"  Deficit: {results['Deficit'][-1]:.2f}")
    
    # Basic sanity checks
    assert results['GDPreal'][-1] > 0, "GDP should be positive"
    assert 0 <= results['Unemployment'][-1] <= 1, "Unemployment should be in [0,1]"
    assert len(country.capital_sector.firms) > 0, "Should have firms in sector 1"
    assert len(country.consumption_sector.firms) > 0, "Should have firms in sector 2"
    
    print("\n✅ Test 1 PASSED")
    return True


def test_determinism():
    """Test that same seed gives same results"""
    print("\n" + "="*70)
    print("TEST 2: Determinism (same seed = same results)")
    print("="*70)
    
    # Run 1
    country1 = Country()
    country1.initialize()
    results1 = country1.simulate(5)
    
    # Run 2 (same seed)
    country2 = Country()
    country2.initialize()
    results2 = country2.simulate(5)
    
    # Check if results match
    for key in ['GDPreal', 'GDPnom', 'Unemployment']:
        val1 = results1[key][-1]
        val2 = results2[key][-1]
        diff = abs(val1 - val2)
        print(f"  {key}: Run1={val1:.6f}, Run2={val2:.6f}, Diff={diff:.6e}")
        assert diff < 1e-6, f"{key} should match across runs"
    
    print("\n✅ Test 2 PASSED")
    return True


def test_financial_equations():
    """Test financial sector equations"""
    print("\n" + "="*70)
    print("TEST 3: Financial Sector Equations")
    print("="*70)
    
    country = Country()
    country.initialize()
    country.time_step()
    
    fin = country.financial_sector
    
    print(f"Interest rates:")
    print(f"  Prime rate (r): {fin._r:.4f}")
    print(f"  Bond rate (rBonds): {fin._rBonds:.4f}")
    print(f"  Deposit rate (rD): {fin._rD:.4f}")
    print(f"  Debt rate (rDeb): {fin._rDeb:.4f}")
    print(f"  Reserve rate (rRes): {fin._rRes:.4f}")
    
    print(f"\nFinancial aggregates:")
    print(f"  Total deposits: {fin._Depo:.2f}")
    print(f"  Total loans: {fin._Loans:.2f}")
    print(f"  Total NW (banks): {fin._NWb:.2f}")
    print(f"  Bad debt: {fin._BadDeb:.2f}")
    print(f"  Bonds (banks): {fin._BondsB:.2f}")
    print(f"  Bonds (CB): {fin._BondsCB:.2f}")
    print(f"  Bond supply: {fin._BS:.2f}")
    
    # Sanity checks
    assert fin._r >= 0, "Interest rate should be non-negative"
    assert fin._rDeb >= fin._r, "Debt rate should be >= prime rate (firms pay more)"
    # Note: rD can be > r if muD is negative (deposit spread can be positive)
    assert abs(fin._rD - fin._r) < 0.1, "Deposit rate should be close to prime rate"
    
    print("\n✅ Test 3 PASSED")
    return True


def test_government_equations():
    """Test government fiscal equations"""
    print("\n" + "="*70)
    print("TEST 4: Government Fiscal Equations")
    print("="*70)
    
    country = Country()
    country.initialize()
    
    for t in range(5):
        country.time_step()
    
    print(f"Government variables:")
    print(f"  Expenditure (G): {country._G:.2f}")
    print(f"  Tax revenue: {country._Tax:.2f}")
    print(f"  Dividend tax: {country._TaxDiv:.2f}")
    print(f"  Primary deficit: {country._DefP:.2f}")
    print(f"  Total deficit: {country._Def:.2f}")
    print(f"  Public debt: {country._Deb:.2f}")
    print(f"  Debt/GDP: {country._DebGDP:.4f}")
    
    print(f"\nConsumption:")
    print(f"  Desired (Cd): {country._Cd:.2f}")
    print(f"  Actual (C): {country._C:.2f}")
    print(f"  Forced savings: {country._Sav:.2f}")
    print(f"  Accumulated savings: {country._SavAcc:.2f}")
    
    # Sanity checks
    assert country._G >= 0, "Government spending should be non-negative"
    assert country._Cd >= 0, "Desired consumption should be non-negative"
    assert country._Sav >= 0, "Forced savings should be non-negative"
    
    print("\n✅ Test 4 PASSED")
    return True


def test_entry_exit():
    """Test entry/exit dynamics"""
    print("\n" + "="*70)
    print("TEST 5: Entry/Exit Dynamics")
    print("="*70)
    
    country = Country()
    country.initialize()
    
    # Record initial counts
    F1_init = len(country.capital_sector.firms)
    F2_init = len(country.consumption_sector.firms)
    
    print(f"Initial firms: F1={F1_init}, F2={F2_init}")
    
    # Simulate some periods
    for t in range(10):
        country.time_step()
        if t == 4:
            # Force some exits by setting negative net worth
            if country.capital_sector.firms:
                country.capital_sector.firms[0]._NW1 = -10.0
            if country.consumption_sector.firms:
                country.consumption_sector.firms[0]._NW2 = -10.0
    
    F1_final = len(country.capital_sector.firms)
    F2_final = len(country.consumption_sector.firms)
    
    print(f"Final firms: F1={F1_final}, F2={F2_final}")
    print(f"Entry cost: {country._cEntry:.2f}")
    print(f"Exit credit: {country._cExit:.2f}")
    
    # Sanity checks
    assert F1_final >= country.capital_sector._F1min, "Should maintain minimum firms in sector 1"
    assert F2_final >= country.consumption_sector._F2min, "Should maintain minimum firms in sector 2"
    
    print("\n✅ Test 5 PASSED")
    return True


def test_regime_change():
    """Test regime change mechanism"""
    print("\n" + "="*70)
    print("TEST 6: Regime Change Mechanism")
    print("="*70)
    
    country = Country()
    country._TregChg = 5  # Schedule change at t=5
    country._trChg = 0.3  # New tax rate
    country.initialize()
    
    print(f"Initial tax rate: {country._tr:.2f}")
    
    # Run to before regime change
    for t in range(4):
        country.time_step()
    
    print(f"Tax rate at t=4: {country._tr:.2f}")
    
    # Regime change happens
    country.time_step()
    
    print(f"Tax rate at t=5 (after change): {country._tr:.2f}")
    
    assert country._tr == 0.3, "Tax rate should change at TregChg"
    
    print("\n✅ Test 6 PASSED")
    return True


def test_aggregates():
    """Test macroeconomic aggregates"""
    print("\n" + "="*70)
    print("TEST 7: Macroeconomic Aggregates")
    print("="*70)
    
    country = Country()
    country.initialize()
    
    for t in range(10):
        country.time_step()
    
    stats = country.statistics
    
    print(f"Macroeconomic statistics:")
    print(f"  Real GDP: {stats._GDPreal:.2f}")
    print(f"  Nominal GDP: {stats._GDPnom:.2f}")
    print(f"  Productivity (A): {stats._A:.4f}")
    print(f"  GDP growth: {country._dGDP*100:.2f}%")
    print(f"  Productivity growth: {country._dAb*100:.2f}%")
    print(f"  Employment (L): {stats._L}")
    print(f"  Labor supply (Ls): {stats._Ls}")
    print(f"  Unemployment rate: {stats._Ue*100:.2f}%")
    
    print(f"\nSectoral statistics:")
    print(f"  Firms sector 1: {stats._F1}")
    print(f"  Firms sector 2: {stats._F2}")
    print(f"  Avg productivity (A): {stats._AtauAvg:.4f}")
    print(f"  Avg productivity (B): {stats._BtauAvg:.4f}")
    print(f"  Capacity utilization: {stats._HCavg:.4f}")
    
    # Sanity checks
    assert stats._GDPreal > 0, "Real GDP should be positive"
    assert stats._A > 0, "Productivity should be positive"
    assert 0 <= stats._Ue <= 1, "Unemployment rate in [0,1]"
    
    print("\n✅ Test 7 PASSED")
    return True


def run_all_tests():
    """Run all validation tests"""
    print("\n" + "="*70)
    print("K+S MODEL COMPLETE VALIDATION SUITE")
    print("="*70)
    
    tests = [
        ("Basic Simulation", test_basic_simulation),
        ("Determinism", test_determinism),
        ("Financial Equations", test_financial_equations),
        ("Government Equations", test_government_equations),
        ("Entry/Exit Dynamics", test_entry_exit),
        ("Regime Change", test_regime_change),
        ("Macroeconomic Aggregates", test_aggregates),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"\n❌ Test {name} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*70)
    print(f"SUMMARY: {passed}/{len(tests)} tests passed")
    if failed == 0:
        print("🎉 ALL TESTS PASSED!")
    else:
        print(f"⚠️  {failed} test(s) failed")
    print("="*70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
