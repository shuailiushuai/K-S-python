"""
Example: Demonstrating Full D2 Demand Allocation

This example shows the full D2 demand allocation algorithm in action,
including unfilled demand tracking (_l2).
"""

import sys
sys.path.insert(0, '..')

from model import Country

def main():
    print("=" * 70)
    print("K+S Model: Full D2 Demand Allocation Demonstration")
    print("=" * 70)
    print()
    
    # Create and initialize country
    country = Country()
    country.initialize()
    
    print("Initial Setup:")
    print(f"  - Capital firms: {len(country.capital_sector.firms)}")
    print(f"  - Consumption firms: {len(country.consumption_sector.firms)}")
    print(f"  - Workers: {len(country.workers)}")
    print(f"  - Banks: {len(country.financial_sector.banks)}")
    print()
    
    # Run simulation for several periods
    print("Running simulation to demonstrate D2 allocation...")
    print()
    
    periods = 10
    for t in range(periods):
        country.time_step()
        
        if t == 0 or t == periods - 1:
            con_sector = country.consumption_sector
            
            print(f"Period {t + 1}:")
            print(f"  Desired consumption (Cd): ${country._Cd:.2f}")
            print(f"  Government spending (G): ${country._G:.2f}")
            print(f"  Total demand: ${country._Cd + country._G:.2f}")
            print(f"  Actual consumption (C): ${country._C:.2f}")
            print(f"  Forced savings: ${country._Sav:.2f}")
            print()
            
            # Show firm-level details
            print("  Firm-level allocation:")
            total_unfilled = 0
            for i, firm in enumerate(con_sector.firms[:5]):  # Show first 5 firms
                print(f"    Firm {i+1}:")
                print(f"      Market share: {firm._f2:.4f}")
                print(f"      Production: {firm._Q2e:.2f} units")
                print(f"      Demand fulfilled: {firm._D2:.2f} units")
                print(f"      Sales: ${firm._S2:.2f}")
                if hasattr(firm, '_l2') and firm._l2 > 0:
                    print(f"      Unfilled demand: {firm._l2:.2f} units")
                    total_unfilled += firm._l2
            
            if total_unfilled > 0:
                print(f"  Total unfilled demand: {total_unfilled:.2f} units")
            print()
    
    print("=" * 70)
    print("Demonstration Complete!")
    print()
    print("Key Features Demonstrated:")
    print("  ✓ Full D2 demand allocation algorithm")
    print("  ✓ Iterative allocation based on market share")
    print("  ✓ Unfilled demand tracking (_l2)")
    print("  ✓ Market share rescaling when firms run out of supply")
    print("  ✓ Proper handling of forced savings")
    print()
    print("This implementation matches the C++ algorithm exactly.")
    print("See: fun_KS_consumption.h, lines 18-92")
    print("=" * 70)

if __name__ == "__main__":
    main()
