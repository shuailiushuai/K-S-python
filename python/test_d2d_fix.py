"""
Test script to validate D2d (desired demand) calculation fix
"""

from model import KSModel
import yaml

def test_d2d_calculation():
    """Test that D2d is properly computed and used in expected demand"""
    
    # Create small test configuration
    config_file = 'config/model_config.yaml'
    model = KSModel(config_file, seed=42)
    
    # Override for small scale
    model.config['Labor.Lscale'] = 1
    model.config['Labor.Ls0'] = 50
    model.config['Capital.F10'] = 3
    model.config['Consumption.F20'] = 5
    
    # Reinitialize with new config
    model = KSModel(config_file, seed=42)
    model.config.update({
        'Labor.Lscale': 1,
        'Labor.Ls0': 50,
        'Capital.F10': 3,
        'Consumption.F20': 5
    })
    model._initialize()
    
    print("=" * 70)
    print("Testing D2d (Desired Demand) Calculation")
    print("=" * 70)
    
    # Run a few periods and check D2d
    for t in range(5):
        print(f"\n{'='*70}")
        print(f"Period {t+1}")
        print(f"{'='*70}")
        
        # Before time step
        print("\nBefore time step:")
        print(f"  Number of firms2: {len(model.firms2)}")
        
        # Check if firms have D2d before step
        has_d2d_before = sum(1 for f in model.firms2 if hasattr(f, '_D2d') and f._D2d > 0)
        print(f"  Firms with _D2d > 0: {has_d2d_before}")
        
        # Run time step
        model.time_step()
        
        # After time step
        print("\nAfter time step:")
        
        # Check market shares sum
        total_f2 = sum(f._f2 for f in model.firms2)
        print(f"  Total market share (f2): {total_f2:.4f}")
        
        # Check D2d was computed
        has_d2d_after = sum(1 for f in model.firms2 if hasattr(f, '_D2d') and f._D2d > 0)
        print(f"  Firms with _D2d > 0: {has_d2d_after}/{len(model.firms2)}")
        
        if has_d2d_after > 0:
            total_d2d = sum(f._D2d for f in model.firms2 if hasattr(f, '_D2d'))
            print(f"  Total _D2d: {total_d2d:.2f} units")
            
            # Check against expected demand
            total_d2e = sum(f._D2e for f in model.firms2 if hasattr(f, '_D2e'))
            print(f"  Total _D2e: {total_d2e:.2f} units")
        
        # Check if D2d in history
        firms_with_d2d_history = sum(1 for f in model.firms2 
                                      if hasattr(f, 'history') 
                                      and 'D2d' in f.history 
                                      and hasattr(f.history['D2d'], 'data')
                                      and len(f.history['D2d'].data) > 0)
        print(f"  Firms with D2d in history: {firms_with_d2d_history}/{len(model.firms2)}")
        
        # Sample one firm's expected demand calculation
        if model.firms2:
            firm = model.firms2[0]
            print(f"\n  Sample firm {firm.id}:")
            print(f"    Market share (_f2): {firm._f2:.4f}")
            print(f"    Desired demand (_D2d): {getattr(firm, '_D2d', 0):.2f}")
            print(f"    Expected demand (_D2e): {getattr(firm, '_D2e', 0):.2f}")
            print(f"    Actual demand (_D2): {getattr(firm, '_D2', 0):.2f}")
            
            if hasattr(firm, 'history') and 'D2d' in firm.history:
                d2d_hist_len = len(firm.history['D2d'].data) if hasattr(firm.history['D2d'], 'data') else 0
                print(f"    D2d history length: {d2d_hist_len}")
                if d2d_hist_len > 0:
                    last_d2d = firm.history['D2d'].get(1)
                    if last_d2d is not None:
                        print(f"    Last D2d: {last_d2d:.2f}")
        
        # Aggregates
        gdp = model.aggregates['GDP'][-1] if model.aggregates['GDP'] else 0
        unemp = model.aggregates['unemployment'][-1] if model.aggregates['unemployment'] else 0
        print(f"\n  Aggregates:")
        print(f"    GDP: ${gdp:.2f}")
        print(f"    Unemployment: {unemp:.1%}")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    
    # Validate results
    print("\nValidation:")
    
    # All firms should have positive D2d
    firms_with_d2d = sum(1 for f in model.firms2 if hasattr(f, '_D2d') and f._D2d > 0)
    print(f"✓ Firms with _D2d > 0: {firms_with_d2d}/{len(model.firms2)}")
    
    # All firms should have D2d in history
    firms_with_history = sum(1 for f in model.firms2 
                             if hasattr(f, 'history') 
                             and 'D2d' in f.history 
                             and hasattr(f.history['D2d'], 'data')
                             and len(f.history['D2d'].data) > 0)
    print(f"✓ Firms with D2d history: {firms_with_history}/{len(model.firms2)}")
    
    # Market shares should sum to 1
    total_f2 = sum(f._f2 for f in model.firms2)
    print(f"✓ Market shares sum: {total_f2:.4f} (should be ~1.0)")
    
    # Expected demand should be reasonable
    if model.firms2:
        avg_d2e = sum(f._D2e for f in model.firms2) / len(model.firms2)
        print(f"✓ Average expected demand: {avg_d2e:.2f} units/firm")

if __name__ == '__main__':
    test_d2d_calculation()
