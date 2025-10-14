"""
Debug market share dynamics
"""

from model import KSModel

def main():
    # Create small model
    model = KSModel('config/model_config.yaml', seed=42)
    model.config.update({
        'Labor.Lscale': 1,
        'Labor.Ls0': 20,
        'Capital.F10': 2,
        'Consumption.F20': 3
    })
    model._initialize()
    
    print("=" * 70)
    print("Debugging Market Share Dynamics")
    print("=" * 70)
    
    for t in range(5):
        print(f"\n{'='*70}")
        print(f"Period {t+1}")
        print(f"{'='*70}")
        
        # Before time step
        print(f"\nBEFORE time_step:")
        total_f2 = sum(f._f2 for f in model.firms2)
        print(f"  Total market share: {total_f2:.4f}")
        for i, firm in enumerate(model.firms2):
            print(f"  Firm {firm.id}: f2={firm._f2:.4f}, E={getattr(firm, '_E', 0):.4f}, "
                  f"D2e={getattr(firm, '_D2e', 0):.2f}, p2={getattr(firm, '_p2', 0):.2f}")
        
        # Run time step
        model.time_step()
        
        # After time step
        print(f"\nAFTER time_step:")
        total_f2 = sum(f._f2 for f in model.firms2)
        print(f"  Total market share: {total_f2:.4f}")
        for i, firm in enumerate(model.firms2):
            print(f"  Firm {firm.id}: f2={firm._f2:.4f}, E={firm._E:.4f}, "
                  f"D2={firm._D2:.2f}, D2d={firm._D2d:.2f}, D2e={firm._D2e:.2f}, "
                  f"p2={firm._p2:.2f}, l2={getattr(firm, '_l2', 0):.2f}")
        
        # Check rescaling
        print(f"\n  Market share sum after rescaling: {total_f2:.6f}")
        
        # Aggregates
        gdp = model.aggregates['GDP'][-1]
        unemp = model.aggregates['unemployment'][-1]
        print(f"\n  GDP: ${gdp:.2f}, Unemployment: {unemp:.1%}")

if __name__ == '__main__':
    main()
