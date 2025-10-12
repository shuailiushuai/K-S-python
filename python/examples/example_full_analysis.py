"""
Example: Complete Statistical Analysis Workflow
Demonstrates how to use the K+S statistical analysis module

This script shows the complete workflow from running simulations
to generating comprehensive statistical analysis and plots.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
from analysis import (
    analyze_aggregates,
    analyze_sector_1,
    analyze_sector_2_mc,
    analyze_workers,
    elementary_effects_sa,
    kriging_sobol_sa
)
from analysis.support_functions import save_simulation_results


def generate_sample_data(n_time_steps=500, n_mc_runs=10):
    """
    Generate sample simulation data for demonstration
    
    In real usage, this would come from actual K+S simulations
    """
    print("Generating sample data...")
    
    # Simulate realistic economic time series
    np.random.seed(42)
    
    # GDP growth with trend and cycle
    trend = 0.03
    cycle_period = 50
    time = np.arange(n_time_steps)
    
    data = {}
    
    for mc_run in range(n_mc_runs):
        # Add some variation across MC runs
        shock = np.random.randn() * 0.01
        
        # GDP growth
        cycle = 0.02 * np.sin(2 * np.pi * time / cycle_period)
        noise = np.random.randn(n_time_steps) * 0.01
        dGDP = trend + shock + cycle + noise
        
        # Unemployment (counter-cyclical)
        U = 0.06 - 2 * dGDP + np.random.randn(n_time_steps) * 0.005
        U = np.clip(U, 0.01, 0.15)
        
        # Inflation
        CPI_growth = 0.02 + 0.5 * dGDP + np.random.randn(n_time_steps) * 0.005
        
        # Productivity
        A_growth = 0.025 + shock + np.random.randn(n_time_steps) * 0.008
        A = np.cumprod(1 + A_growth)
        
        # Store data for this MC run
        if mc_run == 0:
            data['dGDP'] = dGDP.reshape(-1, 1)
            data['U'] = U.reshape(-1, 1)
            data['dCPI'] = CPI_growth.reshape(-1, 1)
            data['A'] = A.reshape(-1, 1)
            data['F1'] = (20 + np.random.randint(-2, 3, n_time_steps)).reshape(-1, 1)
            data['F2'] = (100 + np.random.randint(-5, 6, n_time_steps)).reshape(-1, 1)
            data['wAvgReal'] = (1.0 + np.cumsum(0.001 + np.random.randn(n_time_steps) * 0.002)).reshape(-1, 1)
            data['wGini'] = (0.3 + np.random.rand(n_time_steps) * 0.1).reshape(-1, 1)
        else:
            data['dGDP'] = np.hstack([data['dGDP'], dGDP.reshape(-1, 1)])
            data['U'] = np.hstack([data['U'], U.reshape(-1, 1)])
            data['dCPI'] = np.hstack([data['dCPI'], CPI_growth.reshape(-1, 1)])
            data['A'] = np.hstack([data['A'], A.reshape(-1, 1)])
            data['F1'] = np.hstack([data['F1'], (20 + np.random.randint(-2, 3, n_time_steps)).reshape(-1, 1)])
            data['F2'] = np.hstack([data['F2'], (100 + np.random.randint(-5, 6, n_time_steps)).reshape(-1, 1)])
            data['wAvgReal'] = np.hstack([data['wAvgReal'], (1.0 + np.cumsum(0.001 + np.random.randn(n_time_steps) * 0.002)).reshape(-1, 1)])
            data['wGini'] = np.hstack([data['wGini'], (0.3 + np.random.rand(n_time_steps) * 0.1).reshape(-1, 1)])
    
    return data


def main():
    """
    Main demonstration workflow
    """
    print("=" * 70)
    print("K+S Statistical Analysis - Complete Demonstration")
    print("=" * 70)
    print()
    
    # Create output directory
    output_dir = "analysis_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # ========== Step 1: Generate/Load Data ==========
    print("Step 1: Generating sample simulation data...")
    print("-" * 70)
    
    data = generate_sample_data(n_time_steps=500, n_mc_runs=10)
    
    # Save data in the format expected by analysis module
    save_simulation_results(data, folder=output_dir, base_name="Demo")
    
    print(f"✓ Generated data with {data['dGDP'].shape[0]} time steps")
    print(f"✓ {data['dGDP'].shape[1]} Monte Carlo runs")
    print(f"✓ {len(data)} variables")
    print()
    
    # ========== Step 2: Aggregate Analysis ==========
    print("Step 2: Running aggregate analysis...")
    print("-" * 70)
    
    try:
        aggr_analyzer = analyze_aggregates(
            folder=output_dir,
            base_name="Demo",
            n_exp=1,
            ini_drop=100,  # Drop initial transient
            mc_stat="mean",
            ci_level=0.95
        )
        
        # Create time series plots
        print("\nGenerating time series plots...")
        aggr_analyzer.plot_time_series(
            variables=["dGDP", "U", "dCPI", "A"],
            save_path=f"{output_dir}/aggregates_timeseries.png"
        )
        print(f"✓ Saved: {output_dir}/aggregates_timeseries.png")
        
        # Export statistics
        aggr_analyzer.export_results(f"{output_dir}/aggregate_stats.csv")
        print(f"✓ Saved: {output_dir}/aggregate_stats.csv")
        print()
        
    except Exception as e:
        print(f"⚠ Aggregate analysis skipped: {e}")
        print()
    
    # ========== Step 3: Sector Analysis ==========
    print("Step 3: Running sector analysis...")
    print("-" * 70)
    
    # Note: Sector analysis requires sector-specific variables
    # In this demo, we're using simplified data
    print("⚠ Sector analysis requires full sector variables")
    print("  See sector_analysis.py for required variables")
    print()
    
    # ========== Step 4: Worker Analysis ==========
    print("Step 4: Running worker analysis...")
    print("-" * 70)
    
    # Note: Worker analysis requires worker-specific variables
    print("⚠ Worker analysis requires full worker variables")
    print("  See worker_analysis.py for required variables")
    print()
    
    # ========== Step 5: Summary ==========
    print("=" * 70)
    print("Analysis Complete!")
    print("=" * 70)
    print()
    print("Generated outputs:")
    print(f"  - {output_dir}/Demo_results.pkl.gz (simulation data)")
    print(f"  - {output_dir}/aggregates_timeseries.png (time series plot)")
    print(f"  - {output_dir}/aggregate_stats.csv (statistics table)")
    print()
    print("For full analysis with real K+S simulations:")
    print("  1. Run K+S simulation using run_simulation.py")
    print("  2. Data will be automatically saved in correct format")
    print("  3. Run analysis scripts with actual data")
    print()
    print("Example commands:")
    print("  python run_simulation.py --config configs/baseline.yaml --periods 500 --mc-runs 10")
    print("  python examples/example_full_analysis.py")
    print()


if __name__ == "__main__":
    main()
