"""
Debug worker allocation during time_step
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

with open('config/test_workers.yaml', 'w') as f:
    yaml.dump(config, f)

print("Initializing model...")
model = KSModel('config/test_workers.yaml', seed=42)

print("\n=== INITIAL STATE ===")
print(f"Total workers: {len(model.workers)}")
employed_initial = sum(1 for w in model.workers if w._employed > 0)
print(f"Employed: {employed_initial}")

print(f"\nFirm1 workers:")
for i, f in enumerate(model.firms1):
    print(f"  F1[{i}]: {len(f.workers)} workers, L1d={f._L1d:.0f}")

print(f"\nFirm2 workers:")
for i, f in enumerate(model.firms2):
    print(f"  F2[{i}]: {len(f.workers)} workers, L2d={f._L2d:.0f}")

print(f"\n=== RUNNING TIME STEP ===")

# Check at different stages
original_fire = model.labor_market.fire_workers_sector1

def debug_fire_sector1(firms):
    print(f"\n>>> Before firing sector 1:")
    for i, f in enumerate(firms):
        print(f"    F1[{i}]: {len(f.workers)} workers")
    result = original_fire(firms)
    print(f"    Fired: {result}")
    for i, f in enumerate(firms):
        print(f"    F1[{i}] after: {len(f.workers)} workers")
    return result

model.labor_market.fire_workers_sector1 = debug_fire_sector1

original_fire2 = model.labor_market.fire_workers_sector2

def debug_fire_sector2(firms):
    print(f"\n>>> Before firing sector 2:")
    for i, f in enumerate(firms):
        print(f"    F2[{i}]: {len(f.workers)} workers")
    result = original_fire2(firms)
    print(f"    Fired: {result}")
    for i, f in enumerate(firms):
        print(f"    F2[{i}] after: {len(f.workers)} workers")
    return result

model.labor_market.fire_workers_sector2 = debug_fire_sector2

try:
    model.time_step()
    
    print(f"\n=== AFTER TIME STEP ===")
    employed_final = sum(1 for w in model.workers if w._employed > 0)
    print(f"Employed: {employed_final} (was {employed_initial})")
    
    print(f"\nFirm1 workers:")
    for i, f in enumerate(model.firms1):
        print(f"  F1[{i}]: {len(f.workers)} workers, L1d={f._L1d:.0f}")
    
    print(f"\nFirm2 workers:")
    for i, f in enumerate(model.firms2):
        print(f"  F2[{i}]: {len(f.workers)} workers, L2d={f._L2d:.0f}")
        
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
