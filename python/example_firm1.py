"""
Example: Firm1 R&D and Innovation
Demonstrates the capital goods firm innovation/imitation process
"""

from model.firm1 import Firm1
from model.agent import Agent
from model.random_engine import random_engine

# Initialize random engine for reproducibility
random_engine.seed(42)

# Create mock Capital sector parent
capital = Agent("Capital", None)
capital.set_param("L1rdMax", 0.3)
capital.set_param("f1min", 0.001)
capital.write("w1avg", 1.0, 1)

# Create mock Country grandparent
country = Agent("Country", None)
country.add_child(capital)

# Create three competing firms
firms = []
for i in range(1, 4):
    firm = Firm1(firm_id=i, parent=capital)
    firms.append(firm)
    
    # Initialize with different technologies
    firm.write("_Atau", 1.0 + 0.1 * i, 1)
    firm.write("_Btau", 1.0 + 0.1 * i, 1)
    firm.write("_p1", 1.5 + 0.1 * i, 1)
    firm.write("_L1rd", 2, 1)
    firm.write("_S1", 100.0, 1)
    firm.write("_NW1", 50.0, 1)

print("=" * 70)
print("K+S Model - Firm1 R&D and Innovation Example")
print("=" * 70)

# R&D parameters
params = {
    'xi': 0.5,           # 50% of R&D for innovation
    'zeta1': 3.0,        # Innovation success elasticity
    'zeta2': 3.0,        # Imitation success elasticity
    'alpha1': 3.0,       # Beta distribution alpha
    'beta1': 3.0,        # Beta distribution beta
    'alpha2': 3.0,       # Beta distribution alpha (imitation)
    'beta2': 3.0,        # Beta distribution beta (imitation)
    'x1inf': -0.15,      # Lower bound productivity change
    'x1sup': 0.15,       # Upper bound productivity change
    'm1': 1.0,           # Machine modularity
    'mu1': 0.1,          # Mark-up
    'w1avg': 1.0,        # Average wage sector 1
    'w2avg': 1.0,        # Average wage sector 2
    'Ls0': 1000,         # Initial labor supply
    'Ls': 1000,          # Current labor supply
    'p1avg': 1.6,        # Average machine price
    'c2avg': 0.9,        # Average operating cost
    'b': 10              # Payback period
}

print("\n### Initial Firm Technologies ###")
for i, firm in enumerate(firms, 1):
    print(f"Firm {i}: Atau = {firm.read('_Atau', 1):.3f}, "
          f"Btau = {firm.read('_Btau', 1):.3f}, "
          f"Price = {firm.read('_p1', 1):.3f}")

# Simulate R&D for 5 periods
print("\n" + "=" * 70)
for t in range(1, 6):
    print(f"\n--- Period {t}: R&D and Innovation ---\n")
    
    for i, firm in enumerate(firms, 1):
        # Compute R&D expenditure
        rd = firm.compute_rd_expenditure(nu=0.04)
        
        # Perform R&D: innovation and imitation
        Atau_new, Btau_new = firm.compute_innovation_imitation(params)
        
        # Compute price
        firm.write("_c1", params['w1avg'] / Btau_new)
        price_new = firm.compute_price(mu1=params['mu1'])
        
        # Check if technology changed
        Atau_old = firm.read("_Atau", 1)
        improved = "✓ IMPROVED" if Atau_new > Atau_old else "- same"
        
        print(f"Firm {i}: "
              f"Atau: {Atau_old:.3f} → {Atau_new:.3f} {improved}")
        print(f"         "
              f"Btau: {firm.read('_Btau', 1):.3f} → {Btau_new:.3f}, "
              f"Price: {firm.read('_p1', 1):.3f} → {price_new:.3f}")
        print(f"         R&D: ${rd:.2f}")
        
        # Update lags for next period
        firm.update_lags()

print("\n" + "=" * 70)
print("### Final Firm Technologies ###")
for i, firm in enumerate(firms, 1):
    print(f"Firm {i}: Atau = {firm.read('_Atau', 0):.3f}, "
          f"Btau = {firm.read('_Btau', 0):.3f}, "
          f"Price = {firm.read('_p1', 0):.3f}")

print("\n" + "=" * 70)
print("Innovation simulation completed successfully!")
print("=" * 70)

print("\n### Key Observations ###")
print("- Firms perform R&D with innovation and imitation")
print("- Innovation: Beta-distributed productivity improvements")
print("- Imitation: Distance-based selection of competitor technology")
print("- Technology selection: Minimize client unit cost")
print("- Higher productivity → lower prices → competitive advantage")
