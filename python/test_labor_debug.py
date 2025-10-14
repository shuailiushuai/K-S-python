"""
Debug labor demand calculations
"""
import yaml
from model import KSModel

# Create small test config
config = {
    'Labor.Ls0': 100,
    'Labor.Lscale': 1,
    'Capital.F10': 5,
    'Consumption.F20': 10,
    'Financial.B': 1,
}

# Load base config and update
with open('config/model_config.yaml', 'r') as f:
    base_config = yaml.safe_load(f)
base_config.update(config)

# Save test config
with open('config/test_labor_debug.yaml', 'w') as f:
    yaml.dump(base_config, f)

# Initialize model
print("=" * 70)
print("INITIALIZING MODEL")
print("=" * 70)
model = KSModel('config/test_labor_debug.yaml', seed=1)

print(f"\nInitial state:")
print(f"  Workers: {len(model.workers)}")
print(f"  Firm1: {len(model.firms1)}")
print(f"  Firm2: {len(model.firms2)}")

# Check initial L2d values
print(f"\nInitial L2d values:")
for i, firm in enumerate(model.firms2):
    print(f"  Firm2[{i}]: Q2={getattr(firm, '_Q2', 0):.2f}, A2={getattr(firm, '_A2', 1):.4f}, L2d={getattr(firm, '_L2d', 0)}, L2={getattr(firm, '_L2', 0)}")

total_L2d = sum(f._L2d for f in model.firms2)
print(f"  Total L2d: {total_L2d}")

print(f"\nInitial L1d values:")
for i, firm in enumerate(model.firms1):
    print(f"  Firm1[{i}]: Q1={getattr(firm, '_Q1', 0):.2f}, Btau={getattr(firm, '_Btau', 1):.4f}, L1d={getattr(firm, '_L1d', 0)}, L1={getattr(firm, '_L1', 0)}")

total_L1d = sum(f._L1d for f in model.firms1)
print(f"  Total L1d: {total_L1d}")

# Run one time step
print("\n" + "=" * 70)
print("RUNNING PERIOD 1")
print("=" * 70)

# Check consumption before time step
total_wages = sum(w._w for w in model.workers if w._employed > 0)
print(f"Total wages paid: ${total_wages:.2f}")
print(f"Number of employed workers: {sum(1 for w in model.workers if w._employed > 0)}")

# Check Firm2 investment desires before time step
print(f"\nFirm2 capital stock (BEFORE time step):")
for i, firm in enumerate(model.firms2):
    print(f"  Firm2[{i}]: K={getattr(firm, '_K', 0):.2f}, Kd={getattr(firm, '_Kd', 0):.2f}, Q2d={getattr(firm, '_Q2d', 0):.2f}, A2={getattr(firm, '_A2', 1):.4f}, EI={getattr(firm, '_EI', 0):.2f}, SI={getattr(firm, '_SI', 0):.2f}")

model.time_step()

# Check actual consumption
consumption = model.aggregates['consumption'][-1] if model.aggregates['consumption'] else 0
print(f"Consumption: {consumption:.2f} units")

# Check machine orders
print(f"\nFirm1 machine orders (AFTER period 1):")
for i, firm in enumerate(model.firms1):
    print(f"  Firm1[{i}]: D1={getattr(firm, '_D1', 0):.2f}, Q1={getattr(firm, '_Q1', 0):.2f}, orders={len(firm.orders) if hasattr(firm, 'orders') else 0}")

print(f"\nFirm2 capital stock (AFTER period 1):")
for i, firm in enumerate(model.firms2):
    print(f"  Firm2[{i}]: K={getattr(firm, '_K', 0):.2f}, Kd={getattr(firm, '_Kd', 0):.2f}, Q2d={getattr(firm, '_Q2d', 0):.2f}, A2={getattr(firm, '_A2', 1):.4f}, EI={getattr(firm, '_EI', 0):.2f}, SI={getattr(firm, '_SI', 0):.2f}")

# Check L2d after time step
print(f"\nAfter period 1 - L2d values:")
for i, firm in enumerate(model.firms2):
    D2e = getattr(firm, '_D2e', 0)
    D2d = getattr(firm, '_D2d', 0)
    D2 = getattr(firm, '_D2', 0)
    print(f"  Firm2[{i}]: D2={D2:.2f}, D2d={D2d:.2f}, D2e={D2e:.2f}, Q2={getattr(firm, '_Q2', 0):.2f}, A2={getattr(firm, '_A2', 1):.4f}, L2d={getattr(firm, '_L2d', 0)}, L2={getattr(firm, '_L2', 0)}, workers={len(firm.workers)}")

total_L2d = sum(f._L2d for f in model.firms2)
total_L2 = sum(len(f.workers) for f in model.firms2)
print(f"  Total L2d: {total_L2d}, Total L2 (workers): {total_L2}")

print(f"\nAfter period 1 - L1d values:")
for i, firm in enumerate(model.firms1):
    print(f"  Firm1[{i}]: Q1={getattr(firm, '_Q1', 0):.2f}, Btau={getattr(firm, '_Btau', 1):.4f}, L1d={getattr(firm, '_L1d', 0)}, L1={getattr(firm, '_L1', 0)}, workers={len(firm.workers)}")

total_L1d = sum(f._L1d for f in model.firms1)
total_L1 = sum(len(f.workers) for f in model.firms1)
print(f"  Total L1d: {total_L1d}, Total L1 (workers): {total_L1}")

# Run period 2
print("\n" + "=" * 70)
print("RUNNING PERIOD 2")
print("=" * 70)
model.time_step()

print(f"\nAfter period 2 - L2d values:")
for i, firm in enumerate(model.firms2):
    print(f"  Firm2[{i}]: Q2={getattr(firm, '_Q2', 0):.2f}, A2={getattr(firm, '_A2', 1):.4f}, L2d={getattr(firm, '_L2d', 0)}, L2={getattr(firm, '_L2', 0)}, workers={len(firm.workers)}")

total_L2d = sum(f._L2d for f in model.firms2)
total_L2 = sum(len(f.workers) for f in model.firms2)
print(f"  Total L2d: {total_L2d}, Total L2 (workers): {total_L2}")

unemployed = sum(1 for w in model.workers if w._employed == 0)
print(f"\nUnemployed workers: {unemployed}/{len(model.workers)} ({unemployed/len(model.workers)*100:.1f}%)")
