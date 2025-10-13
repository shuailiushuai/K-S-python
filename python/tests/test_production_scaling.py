"""
Test production scaling fix

This test verifies that production is correctly scaled by Lscale to match
the C++ model implementation, fixing the critical labor matching unit mismatch.
"""

import sys
sys.path.insert(0, '.')

from model.country import Country
from config import get_default_config
from model.random_engine import random_engine


def test_production_scaling():
    """
    Test that production is correctly scaled by Lscale
    
    The bug was that wages were scaled (W = actual_wages * Lscale) but
    production was not (Q = actual_workers * productivity), causing
    massive negative profits.
    
    After the fix, production should be: Q = actual_workers * productivity * Lscale
    """
    random_engine.seed(42)
    config = get_default_config()
    country = Country(config)
    country.initialize()
    
    # Run simulation for 100 periods
    for t in range(100):
        country.time_step()
    
    # Get Lscale
    Lscale = country.labor_market._Lscale
    
    # Check consumption sector
    con_sector = country.consumption_sector
    
    # Verify that production is scaled correctly
    # With 98 actual workers (approximating from employment), productivity ~1, m2=1, Lscale=10
    # Expected production should be around: 98 * 1 * 1 * 10 = 980
    assert con_sector._Q2e > 900, f"Production too low: {con_sector._Q2e}, expected ~980"
    assert con_sector._Q2e < 1100, f"Production too high: {con_sector._Q2e}, expected ~980"
    
    # Check individual firm
    firm = con_sector.firms[0]
    workers_in_firm = sum(1 for w in country.workers if w._employed == 2 and getattr(w, '_employer', None) == firm)
    
    # Verify firm L2 is scaled
    expected_L2 = workers_in_firm * Lscale
    assert firm._L2 == expected_L2, f"Firm L2 not scaled correctly: {firm._L2} != {expected_L2}"
    
    # Verify firm production is scaled
    expected_Q2e_min = workers_in_firm * firm._A2 * con_sector._m2 * Lscale * 0.9
    expected_Q2e_max = workers_in_firm * firm._A2 * con_sector._m2 * Lscale * 1.1
    assert expected_Q2e_min <= firm._Q2e <= expected_Q2e_max, \
        f"Firm production not scaled: {firm._Q2e} not in [{expected_Q2e_min}, {expected_Q2e_max}]"
    
    # Check capital sector
    cap_sector = country.capital_sector
    
    # Verify capital sector production is also scaled
    total_workers_s1 = sum(1 for w in country.workers if w._employed == 1)
    if total_workers_s1 > 0:
        # Production should be scaled by Lscale
        expected_Q1e_min = total_workers_s1 * 0.8 * cap_sector._m1 * Lscale * 0.5
        expected_Q1e_max = total_workers_s1 * 1.2 * cap_sector._m1 * Lscale * 2.0
        assert expected_Q1e_min <= cap_sector._Q1e <= expected_Q1e_max, \
            f"Capital sector production not scaled: {cap_sector._Q1e} not in [{expected_Q1e_min}, {expected_Q1e_max}]"
    
    print("✓ Production scaling test passed")
    print(f"  Consumption production: {con_sector._Q2e}")
    print(f"  Capital production: {cap_sector._Q1e}")
    print(f"  Lscale: {Lscale}")
    return True


def test_wage_production_consistency():
    """
    Test that wages and production are consistent in their scaling
    
    Both wages and production should be scaled by Lscale, so the ratio
    of wages to sales should be reasonable (not 10x off).
    """
    random_engine.seed(42)
    config = get_default_config()
    country = Country(config)
    country.initialize()
    
    # Run simulation for 100 periods
    for t in range(100):
        country.time_step()
    
    con_sector = country.consumption_sector
    
    # Total wages in sector 2
    total_W2 = sum(f._W2 for f in con_sector.firms)
    
    # Total sales
    total_S2 = con_sector._S2
    
    # Wage-to-sales ratio should be reasonable (not 10x or more)
    # In the buggy version, wages were ~2656 and sales were ~118, ratio ~22
    # After fix, wages ~2656 and sales ~1176, ratio ~2.3
    wage_to_sales_ratio = total_W2 / total_S2 if total_S2 > 0 else float('inf')
    
    assert wage_to_sales_ratio < 5.0, \
        f"Wage-to-sales ratio too high: {wage_to_sales_ratio:.2f}, suggests production not scaled"
    
    # Profits should not be absurdly negative (more than 2x sales)
    total_Pi2 = con_sector._Pi2
    if total_S2 > 0:
        profit_to_sales_ratio = abs(total_Pi2) / total_S2
        assert profit_to_sales_ratio < 3.0, \
            f"Profit-to-sales ratio too high: {profit_to_sales_ratio:.2f}, suggests severe unit mismatch"
    
    print("✓ Wage-production consistency test passed")
    print(f"  Total wages (W2): ${total_W2:.2f}")
    print(f"  Total sales (S2): ${total_S2:.2f}")
    print(f"  Wage/Sales ratio: {wage_to_sales_ratio:.2f}")
    print(f"  Total profits (Pi2): ${total_Pi2:.2f}")
    return True


def test_gdp_scaling():
    """
    Test that GDP reflects scaled production
    
    GDP should be calculated from scaled production (Q2e * Lscale), not
    from unscaled production.
    """
    random_engine.seed(42)
    config = get_default_config()
    country = Country(config)
    country.initialize()
    
    # Run simulation for 100 periods
    for t in range(100):
        country.time_step()
    
    # Get final GDP
    gdp_real = country._GDPreal
    gdp_nom = country._GDPnom
    
    # With production ~980, GDP should be in the range of 900-1100
    # In the buggy version, GDP was ~98
    assert gdp_real > 900, f"GDP too low: {gdp_real}, expected ~980 (was ~98 before fix)"
    assert gdp_real < 1100, f"GDP too high: {gdp_real}, expected ~980"
    
    # Nominal GDP should also reflect scaled production
    assert gdp_nom > 1000, f"Nominal GDP too low: {gdp_nom}, expected ~1176"
    assert gdp_nom < 1300, f"Nominal GDP too high: {gdp_nom}, expected ~1176"
    
    print("✓ GDP scaling test passed")
    print(f"  Real GDP: ${gdp_real:.2f}")
    print(f"  Nominal GDP: ${gdp_nom:.2f}")
    return True


if __name__ == "__main__":
    test_production_scaling()
    test_wage_production_consistency()
    test_gdp_scaling()
    print("\n✅ All production scaling tests passed!")
