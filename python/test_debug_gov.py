"""
Debug script to understand government expenditure impact
"""
import sys
sys.path.insert(0, '.')

from model import KSModel
import yaml

# Create small test config
with open('config/model_config.yaml', 'r') as f:
    config = yaml.safe_load(f)

config['Labor.Ls0'] = 100
config['Capital.F10'] = 5
config['Consumption.F20'] = 10
config['Financial.B'] = 1
config['Labor.Lscale'] = 1

# Save
with open('config/test_debug_gov.yaml', 'w') as f:
    yaml.dump(config, f)

# Initialize model
print("Initializing model...")
model = KSModel('config/test_debug_gov.yaml', seed=42)

print(f"\nInitial state:")
print(f"  Workers: {len(model.workers)}")
print(f"  Employment: {sum(1 for w in model.workers if w._employed > 0)}")
print(f"  Initial GDP: ${model.aggregates['GDP'][-1] if model.aggregates['GDP'] else 0:.2f}")

# Run one time step with detailed output
print(f"\n{'='*70}")
print("RUNNING TIME STEP 1")
print(f"{'='*70}")

# Step through manually to see what happens
model.t += 1

# Track key variables
print(f"\nAfter t increment:")
print(f"  t = {model.t}")

# 1. Central bank
inflation = model._compute_inflation()
unemployment = model._compute_unemployment_rate()
model.central_bank.update_prime_rate(inflation, unemployment, model.t)
print(f"\n1. Central Bank:")
print(f"  Prime rate: {model.central_bank.prime_rate:.4f}")
print(f"  Inflation: {inflation:.4f}")
print(f"  Unemployment: {unemployment:.4f}")

# 8. Production
m2 = model.config.get('Consumption.m2', 1.0)
print(f"\n8. Before Production (Firm2):")
for i, firm in enumerate(model.firms2[:3]):
    print(f"  F2[{i}]: Workers={len(firm.workers)}, Q2={getattr(firm, '_Q2', 0):.2f}, A2={firm._A2:.4f}")

for firm in model.firms2:
    firm.produce(m2)

print(f"\n8. After Production (Firm2):")
for i, firm in enumerate(model.firms2[:3]):
    print(f"  F2[{i}]: Q2e={firm._Q2e:.2f}")

# 9. Government expenditure
model._update_labor_stats()
print(f"\n9. Labor Stats:")
print(f"  Ls: {model.labor_stats['Ls']}")
print(f"  L: {model.labor_stats['L']}")
print(f"  wAvg: {model.labor_stats['wAvg']:.4f}")
print(f"  wU: {model.labor_stats['wU']:.4f}")

gov_expenditure = model.government.compute_expenditure(model.workers, model.labor_stats)
print(f"\n9. Government Expenditure:")
print(f"  G = ${gov_expenditure:.2f}")

# 10. Consumption demand
past_bonus = sum(getattr(w, '_Bon', 0) for w in model.workers)
past_dividends = 0.0

flag_tax = model.config.get('Country.flagTax', 1)
tr = model.config.get('Country.tr', 0.1)
wage_tax = 0.0
if flag_tax >= 1:
    wage_tax = sum((w._w + getattr(w, '_Bon', 0)) * tr 
                  for w in model.workers if w._employed > 0)

print(f"\n10. Before Consumption Demand:")
print(f"  Past bonus: ${past_bonus:.2f}")
print(f"  Wage tax: ${wage_tax:.2f}")
print(f"  Gov expenditure: ${gov_expenditure:.2f}")

consumption_demand, model.savings_acc = model.goods_market.compute_consumption_demand(
    model.workers, gov_expenditure, past_bonus, past_dividends,
    wage_tax, 0.0, model.savings_acc)

print(f"\n10. Consumption Demand:")
print(f"  Total demand: ${consumption_demand:.2f}")
print(f"  Savings acc: ${model.savings_acc:.2f}")

# Allocate
total_fulfilled = model.goods_market.allocate_consumption_demand(
    model.firms2, consumption_demand)

print(f"\n10. After Allocation:")
print(f"  Total fulfilled: {total_fulfilled:.2f} units")
for i, firm in enumerate(model.firms2[:3]):
    print(f"  F2[{i}]: D2={firm._D2:.2f}, S2=${firm._D2 * firm._p2:.2f}")
