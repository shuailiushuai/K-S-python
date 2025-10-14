"""
Debug script to trace D2e (expected demand) calculation
"""

from model import KSModel

def main():
    # Create model
    model = KSModel('config/model_config.yaml', seed=42)
    model.config.update({
        'Labor.Lscale': 1,
        'Labor.Ls0': 20,
        'Capital.F10': 2,
        'Consumption.F20': 3,
        'flagExpect': 0  # Myopic 1-period
    })
    model._initialize()
    
    print("=" * 70)
    print("Debugging D2e (Expected Demand) Calculation")
    print("=" * 70)
    
    # Focus on one firm
    firm = model.firms2[0]
    print(f"\nTracking Firm {firm.id}")
    print(f"Initial state:")
    print(f"  _D2: {firm._D2:.2f}")
    print(f"  _D2d: {firm._D2d:.2f}")
    print(f"  _D2e: {firm._D2e:.2f}")
    print(f"  _f2: {firm._f2:.4f}")
    
    for t in range(5):
        print(f"\n{'='*70}")
        print(f"Period {t+1}")
        print(f"{'='*70}")
        
        # Before time step
        print(f"\nBEFORE time_step:")
        print(f"  _D2: {firm._D2:.2f}")
        print(f"  _D2d: {firm._D2d:.2f}")
        print(f"  _D2e: {firm._D2e:.2f}")
        print(f"  _f2: {firm._f2:.4f}")
        
        # Check history
        d2_hist = firm.history['D2'].get(1)
        d2d_hist = firm.history['D2d'].get(1)
        print(f"  History D2(t-1): {d2_hist if d2_hist is not None else 'None'}")
        print(f"  History D2d(t-1): {d2d_hist if d2d_hist is not None else 'None'}")
        
        # Run time step
        model.time_step()
        
        # After time step
        print(f"\nAFTER time_step:")
        print(f"  _D2: {firm._D2:.2f}")
        print(f"  _D2d: {firm._D2d:.2f}")
        print(f"  _D2e: {firm._D2e:.2f}")
        print(f"  _f2: {firm._f2:.4f}")
        
        # Check what was stored in history
        d2_hist = firm.history['D2'].get(0) if hasattr(firm.history['D2'], 'data') and len(firm.history['D2'].data) > 0 else None
        d2d_hist = firm.history['D2d'].get(0) if hasattr(firm.history['D2d'], 'data') and len(firm.history['D2d'].data) > 0 else None
        print(f"  Current history D2(t): {d2_hist if d2_hist is not None else 'None'}")
        print(f"  Current history D2d(t): {d2d_hist if d2d_hist is not None else 'None'}")
        
        # Aggregates
        gdp = model.aggregates['GDP'][-1]
        unemp = model.aggregates['unemployment'][-1]
        print(f"\n  GDP: ${gdp:.2f}, Unemployment: {unemp:.1%}")

if __name__ == '__main__':
    main()
