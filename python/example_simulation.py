"""
K+S Model - Complete Simulation Example
Demonstrates the full Country agent with time-step orchestration
"""

from model.country import Country
from model.random_engine import random_engine
import sys


def main():
    print("=" * 70)
    print("K+S Model - Complete Simulation Example")
    print("=" * 70)
    print()
    
    # Create country with configuration
    config = {
        'country': {
            'flagCons': 2,          # Full savings mode
            'flagGovExp': 2,        # Unemployment benefits
            'flagTax': 1,           # Basic taxation
            'tr': 0.2,              # 20% tax rate
            'gG': 0.01,             # 1% government spending growth
        },
        'capital': {
            'F10': 10,              # 10 initial capital goods firms
            'F1min': 5,
            'F1max': 50,
            'mu1': 0.1,             # 10% mark-up
            'nu': 0.04,             # 4% R&D investment
        },
        'consumption': {
            'F20': 20,              # 20 initial consumption goods firms
            'F2min': 10,
            'F2max': 100,
            'mu20': 0.2,            # 20% initial mark-up
            'b': 3.0,               # 3-period payback
        },
        'financial': {
            'B': 3,                 # 3 banks
            'tauB': 0.08,           # 8% capital adequacy
            'rT': 0.03,             # 3% target rate
        }
    }
    
    # Initialize country
    print("### Initializing Country ###")
    country = Country(config)
    random_engine.seed(42)  # Fixed seed for reproducibility
    country.initialize()
    
    print(f"Capital Sector: {len(country.capital_sector.firms)} firms")
    print(f"Consumption Sector: {len(country.consumption_sector.firms)} firms")
    print(f"Financial Sector: {len(country.financial_sector.banks)} banks")
    print(f"Labor Market: {len(country.workers)} workers")
    print()
    
    # Run simulation
    print("=" * 70)
    print("### Running Simulation (10 periods) ###")
    print("=" * 70)
    print()
    
    try:
        results = country.simulate(periods=10)
        
        # Display results
        print(f"{'Period':<8} {'GDP(real)':<12} {'GDP(nom)':<12} {'Unemp%':<10} {'Debt':<12} {'Deficit':<12}")
        print("-" * 70)
        
        for i in range(len(results['t'])):
            t = results['t'][i]
            gdp_real = results['GDPreal'][i]
            gdp_nom = results['GDPnom'][i]
            unemp = results['Unemployment'][i] * 100
            debt = results['Debt'][i]
            deficit = results['Deficit'][i]
            
            print(f"{t:<8} {gdp_real:<12.2f} {gdp_nom:<12.2f} {unemp:<10.2f} {debt:<12.2f} {deficit:<12.2f}")
        
        print()
        print("=" * 70)
        print("### Summary Statistics ###")
        print("=" * 70)
        
        # Calculate summary stats
        avg_gdp_growth = sum(results['GDPreal'][i] / results['GDPreal'][i-1] - 1 
                             for i in range(1, len(results['GDPreal']))) / (len(results['GDPreal']) - 1) * 100
        avg_unemployment = sum(results['Unemployment']) / len(results['Unemployment']) * 100
        final_debt_gdp = results['Debt'][-1] / results['GDPnom'][-1] * 100 if results['GDPnom'][-1] > 0 else 0
        
        print(f"Average GDP Growth Rate: {avg_gdp_growth:.2f}%")
        print(f"Average Unemployment Rate: {avg_unemployment:.2f}%")
        print(f"Final Debt-to-GDP Ratio: {final_debt_gdp:.2f}%")
        print()
        
        # Labor market stats
        labor = country.labor_market
        print("Labor Market Statistics:")
        print(f"  Total Labor Force: {labor._Ls}")
        print(f"  Employed Workers: {labor._L}")
        print(f"  Unemployment Rate: {labor._Ue * 100:.2f}%")
        print(f"  Average Wage: ${labor._wAvg:.2f}")
        print()
        
        # Sector stats
        print("Sector Statistics:")
        print(f"  Capital Sector:")
        print(f"    Firms: {len(country.capital_sector.firms)}")
        print(f"    Production: {country.capital_sector._Q1e:.2f}")
        print(f"    Average Price: ${country.capital_sector._p1avg:.2f}")
        print(f"  Consumption Sector:")
        print(f"    Firms: {len(country.consumption_sector.firms)}")
        print(f"    Production: {country.consumption_sector._Q2e:.2f}")
        print(f"    Sales: ${country.consumption_sector._S2:.2f}")
        print(f"    Inventories: {country.consumption_sector._N:.2f}")
        print()
        
        # Government stats
        print("Government Statistics:")
        print(f"  Expenditure: ${country._G:.2f}")
        print(f"  Tax Revenue: ${country._Tax:.2f}")
        print(f"  Primary Deficit: ${country._DefP:.2f}")
        print(f"  Total Deficit: ${country._Def:.2f}")
        print(f"  Public Debt: ${country._Deb:.2f}")
        print(f"  Debt-to-GDP: {country._DebGDP * 100:.2f}%")
        print()
        
        print("=" * 70)
        print("Simulation completed successfully!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\nERROR during simulation: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
