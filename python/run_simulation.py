"""
K+S Model Simulation Script

Example script to run the K+S model simulation.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from ks_model import KSModel


def main():
    """
    Run a baseline simulation
    """
    print("="*60)
    print("K+S Agent-Based Macroeconomic Model - Python Implementation")
    print("="*60)
    
    # Create model with baseline configuration
    config_file = os.path.join('config', 'baseline.json')
    
    if os.path.exists(config_file):
        model = KSModel(config_file=config_file, seed=42)
    else:
        print(f"Warning: Config file {config_file} not found, using defaults")
        model = KSModel(seed=42)
    
    # Run simulation
    time_steps = 200
    model.run(time_steps)
    
    # Print summary
    print("\n" + "="*60)
    print("Simulation Summary")
    print("="*60)
    print(model.stats.summary())
    
    # Save results
    output_file = 'results/baseline_simulation.csv'
    os.makedirs('results', exist_ok=True)
    model.save_results(output_file)
    
    # Plot results
    print("\nGenerating plots...")
    try:
        from visualization.plots import plot_aggregate_summary
        plot_aggregate_summary(
            model.get_statistics(),
            save_path='results/aggregate_plots.png'
        )
    except Exception as e:
        print(f"Could not generate plots: {e}")
    
    print("\n" + "="*60)
    print("Simulation completed successfully!")
    print("="*60)


if __name__ == "__main__":
    main()
