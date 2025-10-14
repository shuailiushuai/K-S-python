"""
More detailed debug to trace Q2 changes
"""

import sys
sys.path.insert(0, '.')

import yaml
from model import KSModel

# Patch Firm2 to trace Q2 changes
from agents.firm2 import Firm2

original_setattr = Firm2.__setattr__

def traced_setattr(self, name, value):
    if name in ['_Q2', '_Q2d', '_L2d'] and hasattr(self, 'id'):
        import traceback
        stack = ''.join(traceback.format_stack()[-3:-1])
        if '_Q2' in name and abs(getattr(self, name, 0) - value) > 1:
            print(f"\n>>> F2[{self.id}].{name} changed: {getattr(self, name, 0):.2f} -> {value:.2f}")
            print(f"    Called from: {stack[:200]}")
    original_setattr(self, name, value)

Firm2.__setattr__ = traced_setattr

# Create minimal config
with open('config/model_config.yaml', 'r') as f:
    config = yaml.safe_load(f)

config['Labor.Ls0'] = 10
config['Capital.F10'] = 1
config['Consumption.F20'] = 1  # Just 1 firm to simplify
config['Financial.B'] = 1

with open('config/test_trace.yaml', 'w') as f:
    yaml.dump(config, f)

print("Initializing model...")
model = KSModel('config/test_trace.yaml', seed=42)

print(f"\nInitial: Q2={model.firms2[0]._Q2:.2f}, Q2d={model.firms2[0]._Q2d:.2f}, L2d={model.firms2[0]._L2d:.2f}")

print("\nRunning time_step...")
try:
    model.time_step()
    print(f"\nFinal: Q2={model.firms2[0]._Q2:.2f}, Q2d={model.firms2[0]._Q2d:.2f}, L2d={model.firms2[0]._L2d:.2f}")
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
