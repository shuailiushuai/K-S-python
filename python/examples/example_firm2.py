"""
Example: Firm2 Agent Basic Operations
Demonstrates consumption goods firm functionality
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from model.firm2 import Firm2
from model.firm1 import Firm1
from model.vintage import VintageAgent
from model.agent import Agent
from model.random_engine import random_engine

# Initialize random engine for reproducibility
random_engine.seed(123)

# Create mock Consumption sector parent
consumption = Agent("Consumption", None)
consumption.set_param("f2min", 0.001)
consumption.write("p1avg", 1.5, 1)

# Create mock Capital sector for suppliers
capital = Agent("Capital", None)
capital.set_param("L1rdMax", 0.3)
capital.set_param("f1min", 0.001)
capital.write("w1avg", 1.0, 1)

# Create mock Country grandparent
country = Agent("Country", None)
country.add_child(consumption)
country.add_child(capital)

# Create suppliers (Firm1 agents)
suppliers = []
for i in range(1, 3):
    supplier = Firm1(firm_id=i, parent=capital)
    supplier.write("_Atau", 1.0 + 0.1 * i, 1)
    supplier.write("_Btau", 1.0 + 0.1 * i, 1)
    supplier.write("_p1", 1.5 + 0.05 * i, 1)
    suppliers.append(supplier)

# Create Firm2 agent
firm = Firm2(firm_id=1, parent=consumption)

print("=" * 70)
print("K+S Model - Firm2 (Consumption Goods) Example")
print("=" * 70)

# Initialize firm
init_params = {
    'entry_time': 0,
    'life_cycle': 0,
    'A2': 1.2,
    'NW2': 50.0,
    'mu2': 0.2
}
firm.initialize(init_params)

print("\n### Firm Initialization ###")
print(f"Firm ID: {firm._ID2}")
print(f"Initial Productivity: {firm._A2:.3f}")
print(f"Initial Net Worth: ${firm._NW2:.2f}")
print(f"Initial Mark-up: {firm._mu2:.1%}")

# Simulate demand expectation
print("\n" + "=" * 70)
print("### Demand Expectation Modes ###")

# Set up past sales data
for lag in range(1, 5):
    firm.write("_S2", 100.0 + lag * 5, lag)

exp_params = {'e': 4, 'rho': 0.9, 'wCent': 1.0, 'w0min': 0.5}

for mode in range(5):
    demand = firm.compute_demand_expectation(mode, exp_params)
    mode_names = ['Myopic', 'Accelerating', 'Adaptive', 'Extrapolative', 'Hybrid']
    print(f"Mode {mode} ({mode_names[mode]:13s}): Expected demand = ${demand:.2f}")

# Production planning
print("\n" + "=" * 70)
print("### Production Planning ###")

# Use hybrid mode
firm.compute_demand_expectation(4, exp_params)
desired_prod = firm.compute_desired_production(u=0.1)
print(f"Expected Demand: ${firm._D2e:.2f}")
print(f"Desired Production: ${desired_prod:.2f}")

# Compute labor productivity (simplified - would need vintages)
firm.write("_LdVint", 10, 0)  # Mock: 10 workers
productivity = firm.compute_labor_productivity()
print(f"Labor Productivity: {productivity:.3f}")

# Capital and investment
print("\n" + "=" * 70)
print("### Capital and Investment ###")

firm.write("_K", 80.0, 1)  # Current capital
desired_capital = firm.compute_desired_capital(m2=5.0)
print(f"Current Capital: ${firm.read('_K', 1):.2f}")
print(f"Desired Capital: ${desired_capital:.2f}")

investment_params = {'eta': 20, 'm2': 5.0, 'current_time': 10}
EI, SI, total = firm.compute_investment_plan(investment_params)
print(f"Expansion Investment: ${EI:.2f}")
print(f"Substitution Investment: ${SI:.2f}")
print(f"Total Investment: ${total:.2f}")

# Labor demand
print("\n" + "=" * 70)
print("### Labor Management ###")

labor_demand = firm.compute_labor_demand(m2=5.0)
print(f"Desired Labor Force: {labor_demand} workers")

# Set past values for wage calculation
firm.write("_w2avg", 1.0, 1)
firm.write("_Pi2", 20.0, 1)
firm.write("_S2", 100.0, 1)

wage_params = {'flagWageMode': 1, 'wCent': 1.0, 'w0min': 0.5}
wage_offer = firm.compute_wage_offer(wage_params)
print(f"Wage Offer: ${wage_offer:.3f}")

# Pricing
print("\n" + "=" * 70)
print("### Pricing ###")

firm.write("_A2", 1.2)
unit_cost = firm.compute_unit_cost(w2avg=1.0)
print(f"Unit Cost: ${unit_cost:.3f}")

price_params = {'mu20': 0.2, 'omega1': 0.1}
price = firm.compute_price(price_params)
print(f"Mark-up: {firm._mu2:.1%}")
print(f"Price: ${price:.3f}")

# Supplier selection
print("\n" + "=" * 70)
print("### Supplier Selection ###")

print("\nAvailable Suppliers:")
for i, supplier in enumerate(suppliers, 1):
    print(f"  Supplier {i}: Productivity={supplier.read('_Atau', 1):.3f}, "
          f"Price=${supplier.read('_p1', 1):.3f}")

selected = firm.select_supplier(suppliers)
if selected:
    print(f"\nSelected Supplier: Productivity={firm._Atau:.3f}")
    print(f"                   Price=${selected.read('_p1', 1):.3f}")

# Market share
print("\n" + "=" * 70)
print("### Market Share ###")

# Set up sales history
for lag in range(1, 4):
    firm.write("_S2", 100.0 + lag * 10, lag)

market_share = firm.compute_market_share(n2=3)
print(f"Market Share: {market_share:.1%}")

# Exit conditions
print("\n" + "=" * 70)
print("### Exit Conditions ###")

should_exit = firm.check_exit_conditions()
print(f"Should Exit: {should_exit}")
print(f"Market Share: {firm._f2:.3f} (min: 0.001)")
print(f"Net Worth: ${firm._NW2:.2f}")

print("\n" + "=" * 70)
print("### Vintage Example ###")

# Create a vintage
vintage = VintageAgent(vintage_id=1, parent=firm)
vintage.initialize(
    vintage_id=1,
    creation_time=5,
    productivity=1.3,
    num_machines=10
)

print(f"Vintage ID: {vintage._IDvint}")
print(f"Created at t={vintage._tVint}")
print(f"Productivity: {vintage._Avint:.3f}")
print(f"Machines: {vintage._nVint}")

# Check scrapping
vintage._toUseVint = 5
scrap_params = {
    'current_time': 10,
    'eta': 20,
    'b': 10,
    'bChg': 8,
    'postChg': False,
    'm2': 5.0,
    'w2avg': 1.0,
    'supplier': selected
}

to_scrap = vintage.compute_scrapping(scrap_params)
print(f"\nMachines to scrap: {to_scrap}")
print(f"Reason: {'Out of technical life' if to_scrap < 0 else 'Economical replacement' if to_scrap > 0 else 'Keep machines'}")

# Production from vintage
production = vintage.compute_production(m2=5.0, Lscale=1.0)
print(f"Production from vintage: {production:.2f}")

print("\n" + "=" * 70)
print("Firm2 and Vintage simulation completed successfully!")
print("=" * 70)

print("\n### Key Observations ###")
print("- Firm2 forms demand expectations using multiple modes")
print("- Production planning considers inventories and capacity")
print("- Investment decisions based on expansion and substitution needs")
print("- Labor demand calculated from production requirements")
print("- Wages can include performance-based premiums")
print("- Prices set using mark-up over unit cost")
print("- Supplier selection based on price and productivity")
print("- Vintages track machine generations and enable learning-by-using")
print("- Scrapping decisions based on age and economic viability")
