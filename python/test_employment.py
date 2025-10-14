"""
Test multi-period simulation to check employment dynamics
"""

import sys
sys.path.insert(0, '.')

import yaml
from model import KSModel

print("="*70)
print(" "*10 + "K+S Model - Multi-Period Employment Test")
print("="*70)

# Create very small config for quick testing
with open('config/model_config.yaml', 'r') as f:
    config = yaml.safe_load(f)

config['Labor.Ls0'] = 50  # 50 workers
config['Capital.F10'] = 3  # 3 capital firms
config['Consumption.F20'] = 5  # 5 consumption firms
config['Financial.B'] = 1  # 1 bank
config['Labor.Lscale'] = 1  # Set to 1 for testing (each worker object = 1 worker)

with open('config/test_employment.yaml', 'w') as f:
    yaml.dump(config, f)

print("\n1. Initializing model...")
model = KSModel('config/test_employment.yaml', seed=42)

# Count initial employment
initial_employed = sum(1 for w in model.workers if w._employed > 0)
initial_unemployment = 1 - (initial_employed / len(model.workers))

print(f"   ✓ Model initialized")
print(f"   - Workers: {len(model.workers)}")
print(f"   - Employed: {initial_employed} ({(1-initial_unemployment)*100:.1f}%)")
print(f"   - Unemployed: {len(model.workers) - initial_employed} ({initial_unemployment*100:.1f}%)")

# Check labor demands
total_L1d = sum(getattr(f, '_L1d', 0) for f in model.firms1)
total_L2d = sum(getattr(f, '_L2d', 0) for f in model.firms2)
print(f"   - Initial L1d: {total_L1d:.1f}, L2d: {total_L2d:.1f}, Total: {total_L1d + total_L2d:.1f}")

print("\n2. Running simulation for 10 periods...")
print("\n   Period | Employed | Unemp% | L1d  | L2d  | GDP   ")
print("   " + "-"*57)

for t in range(10):
    try:
        model.time_step()
        
        # Count employment
        employed = sum(1 for w in model.workers if w._employed > 0)
        unemployment = 1 - (employed / len(model.workers))
        
        # Get labor demands
        L1d = sum(getattr(f, '_L1d', 0) for f in model.firms1)
        L2d = sum(getattr(f, '_L2d', 0) for f in model.firms2)
        
        # Get GDP
        gdp = model.aggregates['GDP'][-1] if model.aggregates['GDP'] else 0
        
        print(f"   {t+1:4d}   | {employed:4d}     | {unemployment*100:5.1f}% | {L1d:4.1f} | {L2d:4.1f} | ${gdp:5.0f}")
        
        # Check for critical issues
        if unemployment > 0.95:
            print(f"\n   ⚠️  WARNING: Very high unemployment ({unemployment*100:.1f}%) at period {t+1}")
            print(f"       L1d={L1d:.1f}, L2d={L2d:.1f}, Total demand={L1d+L2d:.1f}")
            
            # Debug: Check firms' production plans
            print(f"\n       Firm1 details:")
            for i, f in enumerate(model.firms1):
                print(f"         F1[{i}]: Q1={getattr(f, '_Q1', 0):.2f}, L1d={getattr(f, '_L1d', 0):.2f}, Workers={len(f.workers)}")
            
            print(f"\n       Firm2 details:")
            for i, f in enumerate(model.firms2):
                print(f"         F2[{i}]: Q2={getattr(f, '_Q2', 0):.2f}, Q2d={getattr(f, '_Q2d', 0):.2f}, L2d={getattr(f, '_L2d', 0):.2f}, A2={getattr(f, '_A2', 0):.2f}, Workers={len(f.workers)}")
            
            break
            
    except Exception as e:
        print(f"\n   ✗ Error at period {t+1}: {e}")
        import traceback
        traceback.print_exc()
        break

print("\n" + "="*70)
if t >= 9:
    print(" "*15 + "SIMULATION COMPLETED SUCCESSFULLY!")
    print("="*70)
    print("\nEmployment remained stable across all periods ✓")
else:
    print(" "*15 + "SIMULATION STOPPED EARLY")
    print("="*70)
    print(f"\nStopped at period {t+1} - needs investigation")

print("\nThank you for testing!")
