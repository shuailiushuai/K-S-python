"""
Debug script to test initialization step by step
"""

import sys
sys.path.insert(0, '.')

import yaml

# Test 1: Load configuration
print("Test 1: Loading configuration...")
try:
    with open('config/model_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    print("  ✓ Configuration loaded successfully")
    print(f"  Keys: {len(config)} parameters")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    sys.exit(1)

# Test 2: Scale down config
print("\nTest 2: Scaling configuration...")
config['Labor.Ls0'] = 10  # Very small for debugging
config['Capital.F10'] = 2
config['Consumption.F20'] = 3
config['Financial.B'] = 1
print(f"  ✓ Scaled to: {config['Labor.Ls0']} workers, {config['Capital.F10']} F1, {config['Consumption.F20']} F2")

# Test 3: Initialize random engine
print("\nTest 3: Initializing random engine...")
try:
    from utils.core_utils import init_random_engine, get_random_engine
    init_random_engine(42)
    rng = get_random_engine()
    test_val = rng.uniform(0, 1)
    print(f"  ✓ Random engine initialized (test value: {test_val:.4f})")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Compute initial conditions
print("\nTest 4: Computing initial conditions...")
try:
    from utils.initialization import compute_initial_conditions
    init_cond = compute_initial_conditions(config)
    print(f"  ✓ Initial conditions computed")
    print(f"    p10={init_cond['p10']:.4f}, p20={init_cond['p20']:.4f}")
    print(f"    D10={init_cond['D10']:.2f}, D20={init_cond['D20']:.2f}")
    print(f"    Ld10={init_cond['Ld10']:.2f}, Ld20={init_cond['Ld20']:.2f}")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Create single bank
print("\nTest 5: Creating single bank...")
try:
    from agents.bank import Bank
    from utils.initialization import initialize_bank
    bank = Bank(1, config)
    initialize_bank(bank, 1, 1, config, init_cond)
    print(f"  ✓ Bank created: ID={bank._IDb}, Equity={bank._EqB:.2f}")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Create single Firm1
print("\nTest 6: Creating single Firm1...")
try:
    from agents.firm1 import Firm1
    from utils.initialization import initialize_firm1
    firm1 = Firm1(1, config)
    firm1.bank = bank
    firm1._bank1 = 1
    initialize_firm1(firm1, 1, config['Capital.F10'], config, init_cond, new_industry=True)
    print(f"  ✓ Firm1 created: Atau={firm1._Atau:.4f}, p1={firm1._p1:.4f}")
    print(f"    D1={firm1._D1:.2f}, L1d={firm1._L1d:.2f}")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 7: Create single Firm2
print("\nTest 7: Creating single Firm2...")
try:
    from agents.firm2 import Firm2
    from utils.initialization import initialize_firm2
    firm2 = Firm2(1, config)
    firm2.bank = bank
    firm2._bank2 = 1
    firm2.supplier = firm1
    initialize_firm2(firm2, 1, config['Consumption.F20'], config, init_cond, new_industry=True)
    print(f"  ✓ Firm2 created: A2={firm2._A2:.4f}, p2={firm2._p2:.4f}")
    print(f"    D2={firm2._D2:.2f}, L2d={firm2._L2d:.2f}, K={firm2._K:.2f}")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 8: Create single Worker
print("\nTest 8: Creating single worker...")
try:
    from agents.worker import Worker
    from utils.initialization import initialize_worker
    worker = Worker(1, config)
    initialize_worker(worker, 1, config, init_cond)
    print(f"  ✓ Worker created: age={worker._age}, sT={worker._sT:.2f}, w={worker._w:.2f}")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 9: Create full model (small)
print("\nTest 9: Creating full model with small scale...")
try:
    from model import KSModel
    
    # Save test config
    with open('config/test_debug.yaml', 'w') as f:
        yaml.dump(config, f)
    
    print("  Initializing model (this might take a moment)...")
    model = KSModel('config/test_debug.yaml', seed=42)
    print(f"  ✓ Model created successfully!")
    print(f"    Workers: {len(model.workers)}")
    print(f"    Firm1: {len(model.firms1)}")
    print(f"    Firm2: {len(model.firms2)}")
    print(f"    Banks: {len(model.banks)}")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("ALL TESTS PASSED!")
print("="*60)
