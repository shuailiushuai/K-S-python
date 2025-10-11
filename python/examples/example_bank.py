"""
Example: Bank Agent Operations
Demonstrates bank credit allocation and financial operations
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from model.bank import Bank
from model.firm1 import Firm1
from model.firm2 import Firm2
from model.agent import Agent
from model.random_engine import random_engine

# Initialize random engine for reproducibility
random_engine.seed(456)

# Create mock Financial sector parent
financial = Agent("Financial", None)
financial.write("r", 0.03, 1)         # Base rate
financial.write("iBonds", 0.025, 1)   # Bond rate

# Create mock Country grandparent
country = Agent("Country", None)
country.add_child(financial)

# Create bank
bank = Bank(bank_id=1, parent=financial)

print("=" * 70)
print("K+S Model - Bank Agent Example")
print("=" * 70)

# Initialize bank
init_params = {
    'bank_id': 1,
    'NWb': 15.0,       # Net worth
    'Depo': 80.0,      # Deposits
    'Loans': 70.0,     # Outstanding loans
    'Cl': 15,          # Number of clients
    'lambda': 0.05     # Reserve requirement
}
bank.initialize(init_params)

print("\n### Bank Initialization ###")
print(f"Bank ID: {bank._IDb}")
print(f"Net Worth: ${bank._NWb:.2f}")
print(f"Deposits: ${bank._Depo:.2f}")
print(f"Loans Outstanding: ${bank._Loans:.2f}")
print(f"Clients: {bank._Cl}")

# Compute reserves
reserves, excess = bank.compute_reserves(lambda_val=0.05)
print(f"\nRequired Reserves (5%): ${bank._Depo * 0.05:.2f}")
print(f"Actual Reserves: ${reserves:.2f}")
print(f"Excess Reserves: ${excess:.2f}")

# Interest rates
print("\n" + "=" * 70)
print("### Interest Rate Setting ###")

r = 0.03  # Central bank rate
spread = 0.02  # Bank spread
spread_deposit = -0.01  # Deposit spread

loan_rate = bank.compute_interest_rate(r, spread)
deposit_rate = bank.compute_deposit_rate(r, spread_deposit)

print(f"Central Bank Rate: {r:.2%}")
print(f"Bank Spread: {spread:.2%}")
print(f"Loan Interest Rate: {loan_rate:.2%}")
print(f"Deposit Interest Rate: {deposit_rate:.2%}")

# Total credit supply
print("\n" + "=" * 70)
print("### Credit Supply Calculation ###")

credit_params = {
    'alpha': 0.08,      # Capital adequacy ratio (8%)
    'betaB': 0.9,       # Leverage ratio
    'lambda': 0.05      # Reserve requirement
}

total_credit = bank.compute_total_credit(credit_params)
print(f"Capital Adequacy Ratio: {credit_params['alpha']:.1%}")
print(f"Leverage Ratio: {credit_params['betaB']:.1%}")
print(f"\nTotal Credit Available: ${total_credit:.2f}")

# Create mock firms requesting credit
print("\n" + "=" * 70)
print("### Credit Allocation - Sector 1 (Capital Goods) ###")

# Create mock Capital sector
capital = Agent("Capital", None)
capital.set_param("L1rdMax", 0.3)

# Create Firm1 agents requesting credit
firms1 = []
for i in range(1, 4):
    firm = Firm1(firm_id=i, parent=capital)
    firm.write("_NW1", 5.0 + i * 2, 1)   # Varying net worth
    firm.write("_S1", 20.0 + i * 5, 1)   # Varying sales
    firm.write("_Deb1", 10.0, 1)         # Current debt
    firm.write("_Deb1max", 20.0 + i * 3, 0)  # Max debt
    firms1.append(firm)
    
    nw_to_s = firm.read("_NW1", 1) / firm.read("_S1", 1)
    credit_requested = firm.read("_Deb1max", 0) - firm.read("_Deb1", 1)
    print(f"Firm1-{i}: NW/S={nw_to_s:.3f}, Credit Requested=${credit_requested:.2f}")

sector1_demand = sum(firm.read("_Deb1max", 0) - firm.read("_Deb1", 1) 
                     for firm in firms1)
print(f"\nTotal Sector 1 Credit Demand: ${sector1_demand:.2f}")

allocated1, allocations1 = bank.allocate_credit_sector1(firms1, sector1_demand)
print(f"Total Credit Allocated: ${allocated1:.2f}")
print(f"Free Credit Remaining: ${bank._TC1free:.2f}")

print("\nCredit Allocations:")
for firm, amount in allocations1:
    print(f"  Firm1-{firm._ID}: ${amount:.2f}")

# Sector 2 credit allocation
print("\n" + "=" * 70)
print("### Credit Allocation - Sector 2 (Consumption Goods) ###")

# Create mock Consumption sector
consumption = Agent("Consumption", None)
consumption.set_param("f2min", 0.001)

# Create Firm2 agents requesting credit
firms2 = []
for i in range(1, 5):
    firm = Firm2(firm_id=i, parent=consumption)
    firm.write("_NW2", 8.0 + i * 3, 1)   # Varying net worth
    firm.write("_S2", 30.0 + i * 8, 1)   # Varying sales
    firm.write("_Deb2", 15.0, 1)         # Current debt
    firm.write("_Deb2max", 25.0 + i * 4, 0)  # Max debt
    firms2.append(firm)
    
    nw_to_s = firm.read("_NW2", 1) / firm.read("_S2", 1)
    credit_requested = firm.read("_Deb2max", 0) - firm.read("_Deb2", 1)
    print(f"Firm2-{i}: NW/S={nw_to_s:.3f}, Credit Requested=${credit_requested:.2f}")

sector2_demand = sum(firm.read("_Deb2max", 0) - firm.read("_Deb2", 1) 
                     for firm in firms2)
print(f"\nTotal Sector 2 Credit Demand: ${sector2_demand:.2f}")
print(f"Credit Available for Sector 2: ${bank._TC1free:.2f}")

allocated2, allocations2 = bank.allocate_credit_sector2(firms2, sector2_demand)
print(f"Total Credit Allocated: ${allocated2:.2f}")
print(f"Free Credit Remaining: ${bank._TC2free:.2f}")

print("\nCredit Allocations:")
for firm, amount in allocations2:
    print(f"  Firm2-{firm._ID2}: ${amount:.2f}")

# Profit calculation
print("\n" + "=" * 70)
print("### Bank Profitability ###")

# Set up balance sheet components
bank.write("_Loans", allocated1 + allocated2 + 50.0, 1)  # Previous + new loans
bank.write("_BondsB", 20.0, 1)  # Some government bonds
bank.write("_iB", loan_rate, 1)
bank.write("_iDb", deposit_rate, 1)
bank.write("_BadDeb1", 2.0, 0)  # Some bad debts
bank.write("_BadDeb2", 1.5, 0)

profits = bank.compute_profits()
print(f"Interest Income from Loans: ${bank.read('_Loans', 1) * loan_rate:.2f}")
print(f"Income from Bonds: ${20.0 * 0.025:.2f}")
print(f"Interest Expense on Deposits: ${bank._Depo * deposit_rate:.2f}")
print(f"Bad Debts (write-offs): ${2.0 + 1.5:.2f}")
print(f"\nGross Profits: ${profits:.2f}")

# Update balance sheet
print("\n" + "=" * 70)
print("### Balance Sheet Update ###")

bank.write("_Loans", allocated1 + allocated2 + 50.0, 0)
bank.write("_Depo", 85.0, 0)  # Updated deposits
bank.write("_BondsB", 20.0, 0)
bank.write("_LoansCB", 10.0, 0)  # Central bank loan

bank.update_balance_sheet()

print(f"Assets:")
print(f"  Loans: ${bank.read('_Loans', 0):.2f}")
print(f"  Reserves: ${bank._Res:.2f}")
print(f"  Bonds: ${bank.read('_BondsB', 0):.2f}")
print(f"  Total: ${bank.read('_Loans', 0) + bank._Res + bank.read('_BondsB', 0):.2f}")

print(f"\nLiabilities:")
print(f"  Deposits: ${bank.read('_Depo', 0):.2f}")
print(f"  CB Loans: ${bank.read('_LoansCB', 0):.2f}")
print(f"  Total: ${bank.read('_Depo', 0) + bank.read('_LoansCB', 0):.2f}")

print(f"\nNet Worth (Equity): ${bank._NWb:.2f}")

# Market share
print("\n" + "=" * 70)
print("### Market Position ###")

market_share = bank.compute_market_share()
print(f"Clients: {bank._Cl}")
print(f"Market Share: {market_share:.1%}")

# Bankruptcy check
is_bankrupt = bank.check_bankruptcy()
print(f"\nBankruptcy Status: {'BANKRUPT' if is_bankrupt else 'Solvent'}")
print(f"Net Worth: ${bank._NWb:.2f}")

print("\n" + "=" * 70)
print("Bank simulation completed successfully!")
print("=" * 70)

print("\n### Key Observations ###")
print("- Banks set interest rates as spread over central bank rate")
print("- Total credit limited by capital adequacy and leverage ratios")
print("- Credit allocated using pecking order (NW/Sales ratio)")
print("- Higher creditworthiness firms get priority access")
print("- Banks earn profits from lending minus deposit costs and bad debts")
print("- Balance sheet must balance: Assets = Liabilities + Equity")
print("- Basel-like capital adequacy rules constrain lending")
print("- Banks can face bankruptcy if losses exceed equity")
