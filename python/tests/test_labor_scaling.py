"""
Test labor scaling unit fixes
Verifies that firm and sector labor counts are properly scaled
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from model.country import Country
from model.constants import INIWAGE, INISKILL

def test_labor_scaling():
    """Test that labor scaling is correctly applied at firm and sector levels"""
    
    # Create country with known Lscale
    country = Country()
    
    # Initialize sectors and workers
    country.initialize()
    
    # Run one time step to match workers to firms
    country.time_step()
    
    # Set up labor market with specific Lscale
    labor = country.labor_market
    Lscale = labor._Lscale
    print(f"Lscale = {Lscale}")
    
    # Get initial counts
    cap_sector = country.capital_sector
    con_sector = country.consumption_sector
    
    # Count actual worker objects
    workers_sector1 = sum(1 for w in country.workers if w._employed == 1)
    workers_sector2 = sum(1 for w in country.workers if w._employed == 2)
    
    print(f"\n=== Initial State ===")
    print(f"Actual worker objects in sector 1: {workers_sector1}")
    print(f"Actual worker objects in sector 2: {workers_sector2}")
    
    # Run production to update firm labor counts
    country._production_and_pricing()
    
    # Verify firm-level scaling
    print(f"\n=== Firm-Level Labor (should be scaled) ===")
    total_firm_L1 = 0
    for i, firm in enumerate(cap_sector.firms[:3]):  # Check first 3 firms
        workers_in_firm = sum(1 for w in country.workers 
                            if w._employed == 1 and getattr(w, '_employer', None) == firm)
        expected_L1 = workers_in_firm * Lscale
        print(f"Firm1[{i}]: workers={workers_in_firm}, _L1={firm._L1}, expected={expected_L1}")
        assert abs(firm._L1 - expected_L1) < 0.01, \
            f"Firm1[{i}]._L1 mismatch: {firm._L1} != {expected_L1}"
        total_firm_L1 += firm._L1
    
    total_firm_L2 = 0
    for i, firm in enumerate(con_sector.firms[:3]):  # Check first 3 firms
        workers_in_firm = sum(1 for w in country.workers 
                            if w._employed == 2 and getattr(w, '_employer', None) == firm)
        expected_L2 = workers_in_firm * Lscale
        print(f"Firm2[{i}]: workers={workers_in_firm}, _L2={firm._L2}, expected={expected_L2}")
        assert abs(firm._L2 - expected_L2) < 0.01, \
            f"Firm2[{i}]._L2 mismatch: {firm._L2} != {expected_L2}"
        total_firm_L2 += firm._L2
    
    # Verify sector-level aggregation
    print(f"\n=== Sector-Level Labor (aggregated from firms) ===")
    
    # Capital sector: Should be COUNT(workers) * Lscale
    expected_sector_L1 = workers_sector1 * Lscale
    print(f"Capital Sector L1: {cap_sector._L1}, expected={expected_sector_L1}")
    assert abs(cap_sector._L1 - expected_sector_L1) < 0.01, \
        f"Sector L1 mismatch: {cap_sector._L1} != {expected_sector_L1}"
    
    # Consumption sector: Should be SUM(firm._L2)
    con_sector.compute_aggregates()  # Aggregate from firms
    expected_sector_L2 = workers_sector2 * Lscale
    print(f"Consumption Sector L2: {con_sector._L2}, expected={expected_sector_L2}")
    print(f"  (Sum of firm._L2: {total_firm_L2})")
    assert abs(con_sector._L2 - expected_sector_L2) < 0.01, \
        f"Sector L2 mismatch: {con_sector._L2} != {expected_sector_L2}"
    
    # Verify that total labor matches
    total_L = cap_sector._L1 + con_sector._L2
    expected_total = (workers_sector1 + workers_sector2) * Lscale
    print(f"\n=== Total Labor ===")
    print(f"Total L (L1 + L2): {total_L}, expected={expected_total}")
    assert abs(total_L - expected_total) < 0.01, \
        f"Total labor mismatch: {total_L} != {expected_total}"
    
    print(f"\n✓ All labor scaling tests passed!")
    return True


def test_wage_computation():
    """Test that wages are correctly computed using scaled labor"""
    
    country = Country()
    
    # Initialize
    country.initialize()
    
    # Run one time step to match workers
    country.time_step()
    
    labor = country.labor_market
    Lscale = labor._Lscale
    country._production_and_pricing()
    
    # Get sector aggregates
    cap_sector = country.capital_sector
    con_sector = country.consumption_sector
    con_sector.compute_aggregates()
    
    print(f"\n=== Wage Computation Test ===")
    print(f"Lscale = {Lscale}")
    
    # Check a consumption firm's wage calculation
    for i, firm in enumerate(con_sector.firms[:2]):
        L2 = firm._L2  # Should be scaled
        w2avg = firm._w2avg
        W2 = firm.compute_total_wages()  # Should use scaled L2
        
        expected_W2 = L2 * w2avg
        print(f"Firm2[{i}]: L2={L2}, w2avg={w2avg:.2f}, W2={W2:.2f}, expected={expected_W2:.2f}")
        
        assert abs(W2 - expected_W2) < 0.01, \
            f"Firm2[{i}] wage mismatch: {W2} != {expected_W2}"
    
    print(f"✓ Wage computation tests passed!")
    return True


if __name__ == "__main__":
    print("="*60)
    print("LABOR SCALING UNIT TEST")
    print("="*60)
    
    try:
        test_labor_scaling()
        test_wage_computation()
        print("\n" + "="*60)
        print("ALL TESTS PASSED ✓")
        print("="*60)
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
