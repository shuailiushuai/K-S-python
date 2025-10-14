"""
Debug plan_production to see what's happening
"""

import sys
sys.path.insert(0, '.')

import yaml
from model import KSModel

# Create minimal config
with open('config/model_config.yaml', 'r') as f:
    config = yaml.safe_load(f)

config['Labor.Ls0'] = 10
config['Capital.F10'] = 1
config['Consumption.F20'] = 2
config['Financial.B'] = 1

with open('config/test_plan_prod.yaml', 'w') as f:
    yaml.dump(config, f)

print("Initializing model...")
model = KSModel('config/test_plan_prod.yaml', seed=42)

print("\nInitial state:")
for i, f in enumerate(model.firms2):
    print(f"  F2[{i}]: Q2={f._Q2:.2f}, Q2d={f._Q2d:.2f}, L2d={f._L2d:.2f}, A2={f._A2:.2f}")
    print(f"    NW2={f._NW2:.2f}, c2={f._c2:.2f}, D2e={f._D2e:.2f}")

print("\nRunning one time step...")
print("\nBefore time_step:")
for i, f in enumerate(model.firms2):
    print(f"  F2[{i}]: Q2={f._Q2:.2f}, Q2d={f._Q2d:.2f}")

# Add some debug output in the time_step
original_time_step = model.time_step

def debug_time_step():
    print("\n>>> In time_step, after plan_production:")
    for i, f in enumerate(model.firms2):
        print(f"  F2[{i}]: Q2={f._Q2:.2f}, Q2d={f._Q2d:.2f}, L2d={f._L2d:.2f}")
    
    return original_time_step()

model.time_step = debug_time_step

try:
    model.time_step()
    print("\nAfter time_step:")
    for i, f in enumerate(model.firms2):
        print(f"  F2[{i}]: Q2={f._Q2:.2f}, Q2d={f._Q2d:.2f}, L2d={f._L2d:.2f}, Workers={len(f.workers)}")
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
