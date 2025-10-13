"""
K+S Model - Integration Test
Tests the complete simulation workflow
"""

import sys
from pathlib import Path
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from model.country import Country
from model.random_engine import random_engine
from config import get_default_config


@pytest.fixture
def country():
    """Fixture that provides an initialized Country instance"""
    config = get_default_config()
    c = Country(config)
    random_engine.seed(42)
    c.initialize()
    return c


def test_initialization():
    """Test country initialization"""
    print("Test 1: Country Initialization")
    
    config = get_default_config()
    country = Country(config)
    random_engine.seed(42)
    country.initialize()
    
    # Check sectors created
    assert len(country.capital_sector.firms) > 0, "No capital firms created"
    assert len(country.consumption_sector.firms) > 0, "No consumption firms created"
    assert len(country.financial_sector.banks) > 0, "No banks created"
    assert len(country.workers) > 0, "No workers created"
    
    print("  ✓ All sectors initialized")
    print(f"    Capital firms: {len(country.capital_sector.firms)}")
    print(f"    Consumption firms: {len(country.consumption_sector.firms)}")
    print(f"    Banks: {len(country.financial_sector.banks)}")
    print(f"    Workers: {len(country.workers)}")
    print()



def test_single_timestep(country):
    """Test a single time step"""
    print("Test 2: Single Time Step")
    
    initial_t = country._t
    country.time_step()
    
    assert country._t == initial_t + 1, "Time did not advance"
    assert country._GDPreal > 0, "GDP is zero or negative"
    
    print("  ✓ Time step completed successfully")
    print(f"    Time: {country._t}")
    print(f"    Real GDP: ${country._GDPreal:.2f}")
    print(f"    Unemployment: {country.labor_market._Ue * 100:.1f}%")
    print()


def test_multi_timestep(country):
    """Test multiple time steps"""
    print("Test 3: Multiple Time Steps (10 periods)")
    
    results = country.simulate(periods=10)
    
    assert len(results['t']) == 10, "Wrong number of periods"
    assert all(gdp > 0 for gdp in results['GDPreal']), "GDP became zero or negative"
    
    print("  ✓ Multi-period simulation completed")
    print(f"    Periods run: {len(results['t'])}")
    print(f"    Final GDP: ${results['GDPreal'][-1]:.2f}")
    print(f"    Final Unemployment: {results['Unemployment'][-1] * 100:.1f}%")
    print(f"    Final Debt: ${results['Debt'][-1]:.2f}")
    print()


def test_configuration():
    """Test configuration loading"""
    print("Test 4: Configuration System")
    
    # Test default config
    config1 = get_default_config()
    assert 'country' in config1, "Missing country section"
    assert 'capital' in config1, "Missing capital section"
    assert 'consumption' in config1, "Missing consumption section"
    
    # Test config application
    country = Country(config1)
    assert country._tr == config1['country']['tr'], "Tax rate not applied"
    
    print("  ✓ Configuration system working")
    print(f"    Tax rate: {country._tr * 100}%")
    print(f"    Capital firms: {country.capital_sector._F10}")
    print(f"    Consumption firms: {country.consumption_sector._F20}")
    print()


def test_aggregates():
    """Test aggregate calculations"""
    print("Test 5: Aggregate Calculations")
    
    config = get_default_config()
    country = Country(config)
    random_engine.seed(42)
    country.initialize()
    
    # Run a few periods
    for _ in range(5):
        country.time_step()
    
    # Check all aggregates are computed
    assert country._GDPreal >= 0, "Real GDP negative"
    assert country._GDPnom >= 0, "Nominal GDP negative"
    assert 0 <= country.labor_market._Ue <= 1, "Unemployment rate out of range"
    assert country._Deb >= 0, "Negative debt"
    
    print("  ✓ Aggregates computed correctly")
    print(f"    Real GDP: ${country._GDPreal:.2f}")
    print(f"    Nominal GDP: ${country._GDPnom:.2f}")
    print(f"    Productivity: {country._A:.3f}")
    print(f"    Unemployment: {country.labor_market._Ue * 100:.1f}%")
    print(f"    Public Debt: ${country._Deb:.2f}")
    print()


def test_reproducibility():
    """Test simulation reproducibility"""
    print("Test 6: Reproducibility")
    
    config = get_default_config()
    
    # Run 1
    random_engine.seed(42)
    country1 = Country(config)
    country1.initialize()
    results1 = country1.simulate(periods=5)
    
    # Run 2 with same seed
    random_engine.seed(42)
    country2 = Country(config)
    country2.initialize()
    results2 = country2.simulate(periods=5)
    
    # Check results are identical
    for i in range(len(results1['t'])):
        assert results1['GDPreal'][i] == results2['GDPreal'][i], "GDP differs between runs"
        assert results1['Unemployment'][i] == results2['Unemployment'][i], "Unemployment differs"
    
    print("  ✓ Simulations are reproducible with fixed seed")
    print(f"    Both runs: GDP = ${results1['GDPreal'][-1]:.2f}")
    print()


def run_all_tests():
    """Run all integration tests"""
    print("=" * 70)
    print("K+S MODEL - INTEGRATION TESTS")
    print("=" * 70)
    print()
    
    try:
        # Test 1: Initialization
        country = test_initialization()
        
        # Test 2: Single step
        test_single_timestep(country)
        
        # Test 3: Multiple steps
        test_multi_timestep(country)
        
        # Test 4: Configuration
        test_configuration()
        
        # Test 5: Aggregates
        test_aggregates()
        
        # Test 6: Reproducibility
        test_reproducibility()
        
        print("=" * 70)
        print("ALL TESTS PASSED! ✓")
        print("=" * 70)
        print()
        print("The K+S model simulation is working correctly.")
        print("You can now run full simulations with run_simulation.py")
        print()
        
        return 0
        
    except AssertionError as e:
        print()
        print("=" * 70)
        print(f"TEST FAILED: {e}")
        print("=" * 70)
        return 1
    
    except Exception as e:
        print()
        print("=" * 70)
        print(f"ERROR: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
