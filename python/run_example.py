"""
Simple Example: Running the K+S Model
Demonstrates basic usage of the K+S Python implementation
"""

import sys
sys.path.insert(0, '.')

from model import KSModel
import yaml

def create_test_config():
    """Create a small-scale test configuration"""
    with open('config/model_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Scale down for testing (original has 250K workers!)
    config['Labor.Ls0'] = 100         # 100 workers
    config['Capital.F10'] = 5          # 5 capital-good firms
    config['Consumption.F20'] = 10     # 10 consumption-good firms
    config['Financial.B'] = 1          # 1 bank
    config['Labor.Lscale'] = 1         # 1:1 worker objects to workers (for small tests)
    
    # Save test config
    with open('config/test_config.yaml', 'w') as f:
        yaml.dump(config, f)
    
    return 'config/test_config.yaml'


def main():
    print("="*70)
    print(" "*15 + "K+S Agent-Based Model - Python Implementation")
    print("="*70)
    
    # Create test configuration
    print("\n1. Creating test configuration...")
    config_file = create_test_config()
    print(f"   ✓ Configuration saved to {config_file}")
    
    # Initialize model
    print("\n2. Initializing model...")
    model = KSModel(config_file, seed=42)
    print(f"   ✓ Model initialized")
    print(f"   - {len(model.workers)} workers")
    print(f"   - {len(model.firms1)} capital-good firms")
    print(f"   - {len(model.firms2)} consumption-good firms")
    print(f"   - {len(model.banks)} banks")
    
    # Run simulation
    print("\n3. Running simulation for 20 periods...")
    print("   Period | GDP    | Unemp | Infl  | Rate")
    print("   " + "-"*47)
    
    for t in range(20):
        model.time_step()
        
        if (t + 1) % 5 == 0:  # Print every 5 periods
            gdp = model.aggregates['GDP'][-1] if model.aggregates['GDP'] else 0
            unemp = model.aggregates['unemployment'][-1] if model.aggregates['unemployment'] else 0
            infl = model.aggregates['inflation'][-1] if model.aggregates['inflation'] else 0
            rate = model.aggregates['prime_rate'][-1] if model.aggregates['prime_rate'] else 0
            
            print(f"   {t+1:4d}   | ${gdp:5.0f}  | {unemp:4.1%} | {infl:4.1%} | {rate:4.2%}")
    
    # Display final results
    print("\n" + "="*70)
    print(" "*15 + "SIMULATION COMPLETED SUCCESSFULLY")
    print("="*70)
    
    print(f"\nFinal Results (Period {model.t}):")
    print(f"  Economic Output:")
    print(f"    GDP:                   ${model.aggregates['GDP'][-1]:,.2f}")
    print(f"    Consumption:           {model.aggregates['consumption'][-1]:,.2f} units")
    print(f"    Investment:            ${model.aggregates['investment'][-1]:,.2f}")
    
    print(f"\n  Labor Market:")
    print(f"    Unemployment Rate:     {model.aggregates['unemployment'][-1]:.1%}")
    print(f"    Total Workers:         {len(model.workers)}")
    
    print(f"\n  Financial System:")
    print(f"    Prime Interest Rate:   {model.aggregates['prime_rate'][-1]:.3%}")
    print(f"    Inflation Rate:        {model.aggregates['inflation'][-1]:.2%}")
    print(f"    Private Debt:          ${model.aggregates['total_debt'][-1]:,.2f}")
    print(f"    Public Debt:           ${model.aggregates['public_debt'][-1]:,.2f}")
    
    print(f"\n  Firm Statistics:")
    print(f"    Capital-Good Firms:    {len(model.firms1)}")
    print(f"    Consumption Firms:     {len(model.firms2)}")
    print(f"    Banks:                 {len(model.banks)}")
    
    print("\n" + "="*70)
    print("Model Features Implemented:")
    print("  ✓ Labor market search and matching")
    print("  ✓ Goods market allocation with rationing")
    print("  ✓ Capital market machine orders")
    print("  ✓ Government fiscal policy (taxes, benefits)")
    print("  ✓ Central bank monetary policy (Taylor rule)")
    print("  ✓ Heterogeneous agents (workers, firms, banks)")
    print("  ✓ Innovation and technology diffusion")
    print("  ✓ Market share dynamics")
    print("="*70)
    
    # Optionally export results
    export = input("\nExport results to CSV? (y/n): ").lower()
    if export == 'y':
        model.export_results('simulation_results.csv')
        print("✓ Results exported to simulation_results.csv")
    
    print("\nThank you for using the K+S Model!")


if __name__ == '__main__':
    main()
