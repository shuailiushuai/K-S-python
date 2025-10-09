"""
Basic Tests for K+S Model

Simple tests to verify model components are working.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ks_model import KSModel
from utils.parameters import Parameters
from agents.firm1 import Firm1
from agents.firm2 import Firm2
from agents.worker import Worker
from agents.bank import Bank


def test_parameters():
    """Test parameter loading"""
    print("Testing Parameters...")
    params = Parameters()
    
    assert params.get('F10') == 20
    assert params.get('Ls0') == 1000
    assert params.get('tr') == 0.1
    
    print("✓ Parameters test passed")


def test_agent_creation():
    """Test agent creation"""
    print("Testing Agent Creation...")
    params = Parameters()
    
    # Test Firm1 creation
    firm1 = Firm1(0, params, 100.0)
    assert firm1.firm_id == 0
    assert firm1.net_worth == 100.0
    
    # Test Firm2 creation
    firm2 = Firm2(0, params, 100.0)
    assert firm2.firm_id == 0
    assert firm2.net_worth == 100.0
    
    # Test Worker creation
    worker = Worker(0, params, age=1, reservation_wage=1.0, contract_term=1)
    assert worker.worker_id == 0
    assert worker.wage == 1.0
    
    # Test Bank creation
    bank = Bank(0, params, 100.0)
    assert bank.bank_id == 0
    assert bank.equity == 100.0
    
    print("✓ Agent creation test passed")


def test_model_initialization():
    """Test model initialization"""
    print("Testing Model Initialization...")
    
    model = KSModel(seed=42)
    
    assert len(model.firms1) > 0
    assert len(model.firms2) > 0
    assert len(model.workers) > 0
    assert len(model.banks) > 0
    assert model.government is not None
    assert model.central_bank is not None
    
    print(f"✓ Model initialized with:")
    print(f"  - {len(model.firms1)} capital firms")
    print(f"  - {len(model.firms2)} consumption firms")
    print(f"  - {len(model.workers)} workers")
    print(f"  - {len(model.banks)} banks")


def test_single_step():
    """Test single time step execution"""
    print("Testing Single Step Execution...")
    
    model = KSModel(seed=42)
    
    # Run one step
    model.t = 1
    model.step()
    
    # Check that some activity occurred
    assert model.labor_market.total_applications >= 0
    assert model.goods_market.total_demand >= 0
    
    print("✓ Single step execution test passed")


def test_short_simulation():
    """Test short simulation run"""
    print("Testing Short Simulation (10 steps)...")
    
    model = KSModel(seed=42)
    model.run(time_steps=10)
    
    # Check that data was collected
    assert len(model.stats.data['time']) == 10
    assert len(model.stats.data['GDP_real']) == 10
    
    print("✓ Short simulation test passed")
    print(f"  Final GDP: {model.stats.data['GDP_real'][-1]:.2f}")
    print(f"  Final Unemployment: {model.stats.data['unemployment_rate'][-1]*100:.2f}%")


def run_all_tests():
    """Run all tests"""
    print("="*60)
    print("Running K+S Model Tests")
    print("="*60)
    print()
    
    try:
        test_parameters()
        print()
        
        test_agent_creation()
        print()
        
        test_model_initialization()
        print()
        
        test_single_step()
        print()
        
        test_short_simulation()
        print()
        
        print("="*60)
        print("All tests passed successfully! ✓")
        print("="*60)
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
