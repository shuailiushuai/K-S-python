#!/usr/bin/env python3
"""
Parameter Sensitivity Analysis Tool for K+S Model
==================================================

This script facilitates systematic parameter sensitivity analysis
to identify parameter values that yield realistic economic dynamics.

Usage:
    python parameter_tuning_tool.py --param Consumption.e0 --values 0.3,0.5,0.7,1.0 --periods 100
"""

import sys
import os
import yaml
import argparse
import numpy as np
from collections import defaultdict
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import KSModel


def load_base_config():
    """Load base configuration"""
    config_path = 'config/model_config.yaml'
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def run_simulation_with_params(config, seed=42, periods=100):
    """
    Run a simulation with given configuration
    
    Returns:
        dict with aggregate statistics
    """
    # Save temporary config
    temp_config_path = '/tmp/param_test_config.yaml'
    with open(temp_config_path, 'w') as f:
        yaml.dump(config, f)
    
    try:
        # Initialize and run model
        model = KSModel(temp_config_path, seed=seed)
        
        for t in range(periods):
            model.time_step()
        
        # Compute statistics
        employed_counts = []
        for t in range(periods):
            employed = sum(1 for w in model.workers if w._employed > 0)
            employed_counts.append(employed)
        
        employment_rate = [e / len(model.workers) for e in employed_counts]
        
        results = {
            'gdp_mean': np.mean(model.aggregates['GDP']) if model.aggregates['GDP'] else 0,
            'gdp_std': np.std(model.aggregates['GDP']) if model.aggregates['GDP'] else 0,
            'gdp_final': model.aggregates['GDP'][-1] if model.aggregates['GDP'] else 0,
            'employment_mean': np.mean(employment_rate) if employment_rate else 0,
            'employment_final': employment_rate[-1] if employment_rate else 0,
            'unemployment_mean': np.mean(model.aggregates['unemployment']) if model.aggregates['unemployment'] else 0,
            'unemployment_final': model.aggregates['unemployment'][-1] if model.aggregates['unemployment'] else 0,
            'cpi_final': model.aggregates['CPI'][-1] if model.aggregates['CPI'] else 0,
            'success': True,
            'periods_completed': periods
        }
        
        return results
        
    except Exception as e:
        print(f"  ERROR: {e}")
        return {
            'gdp_mean': 0,
            'gdp_std': 0,
            'gdp_final': 0,
            'employment_mean': 0,
            'employment_final': 0,
            'unemployment_mean': 1,
            'unemployment_final': 1,
            'cpi_final': 0,
            'success': False,
            'periods_completed': 0,
            'error': str(e)
        }


def test_parameter_sensitivity(param_name, values, periods=100, seed=42):
    """
    Test sensitivity of model to a single parameter
    
    Args:
        param_name: Parameter name (e.g., 'Consumption.e0')
        values: List of values to test
        periods: Number of periods to simulate
        seed: Random seed
    
    Returns:
        dict mapping values to results
    """
    print(f"\n{'='*80}")
    print(f"PARAMETER SENSITIVITY ANALYSIS")
    print(f"{'='*80}")
    print(f"\nParameter: {param_name}")
    print(f"Values to test: {values}")
    print(f"Periods: {periods}")
    print(f"Seed: {seed}")
    print()
    
    base_config = load_base_config()
    
    # Scale down for faster testing
    base_config['Labor.Ls0'] = 100
    base_config['Labor.Lscale'] = 1
    base_config['Capital.F10'] = 5
    base_config['Consumption.F20'] = 10
    
    results = {}
    
    for i, val in enumerate(values):
        print(f"[{i+1}/{len(values)}] Testing {param_name} = {val}...")
        
        # Create config with modified parameter
        test_config = base_config.copy()
        test_config[param_name] = val
        
        # Run simulation
        result = run_simulation_with_params(test_config, seed=seed, periods=periods)
        results[val] = result
        
        # Print summary
        if result['success']:
            print(f"  ✓ Completed {periods} periods")
            print(f"    Mean employment: {result['employment_mean']:.1%}")
            print(f"    Final employment: {result['employment_final']:.1%}")
            print(f"    Mean GDP: ${result['gdp_mean']:.2f}")
        else:
            print(f"  ✗ Failed after {result.get('periods_completed', 0)} periods")
    
    # Summary comparison
    print(f"\n{'='*80}")
    print("SUMMARY COMPARISON")
    print(f"{'='*80}")
    print(f"\n{'Value':<15} {'Mean Emp.':<15} {'Final Emp.':<15} {'Mean GDP':<15} {'Status':<10}")
    print("-" * 80)
    
    for val, result in results.items():
        status = "✓ OK" if result['success'] else "✗ FAIL"
        print(f"{val:<15} {result['employment_mean']:<14.1%} {result['employment_final']:<14.1%} "
              f"${result['gdp_mean']:<13.2f} {status:<10}")
    
    # Find best value
    successful = {v: r for v, r in results.items() if r['success']}
    if successful:
        best_val = max(successful.items(), key=lambda x: x[1]['employment_mean'])
        print(f"\nBest value for employment: {param_name} = {best_val[0]}")
        print(f"  Mean employment: {best_val[1]['employment_mean']:.1%}")
    
    return results


def test_multiple_parameters(param_configs, periods=100, seed=42):
    """
    Test multiple parameter combinations
    
    Args:
        param_configs: List of dicts, each with parameters to test
        periods: Number of periods
        seed: Random seed
    """
    print(f"\n{'='*80}")
    print(f"MULTIPLE PARAMETER COMBINATIONS TEST")
    print(f"{'='*80}")
    print(f"\nTesting {len(param_configs)} parameter combinations")
    print(f"Periods: {periods}")
    print(f"Seed: {seed}")
    print()
    
    base_config = load_base_config()
    base_config['Labor.Ls0'] = 100
    base_config['Labor.Lscale'] = 1
    base_config['Capital.F10'] = 5
    base_config['Consumption.F20'] = 10
    
    results = []
    
    for i, param_set in enumerate(param_configs):
        print(f"[{i+1}/{len(param_configs)}] Testing combination:")
        for k, v in param_set.items():
            print(f"  {k} = {v}")
        
        # Create config
        test_config = base_config.copy()
        test_config.update(param_set)
        
        # Run simulation
        result = run_simulation_with_params(test_config, seed=seed, periods=periods)
        result['params'] = param_set
        results.append(result)
        
        if result['success']:
            print(f"  ✓ Mean employment: {result['employment_mean']:.1%}, Mean GDP: ${result['gdp_mean']:.2f}")
        else:
            print(f"  ✗ Failed")
        print()
    
    # Summary
    print(f"\n{'='*80}")
    print("RESULTS SUMMARY")
    print(f"{'='*80}")
    
    successful = [r for r in results if r['success']]
    if successful:
        # Sort by employment
        successful.sort(key=lambda x: x['employment_mean'], reverse=True)
        
        print(f"\nTop 5 parameter combinations by employment:")
        for i, result in enumerate(successful[:5]):
            print(f"\n{i+1}. Mean employment: {result['employment_mean']:.1%}")
            print(f"   Parameters:")
            for k, v in result['params'].items():
                print(f"     {k} = {v}")
    
    return results


def save_results(results, filename):
    """Save results to JSON file"""
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {filename}")


def main():
    parser = argparse.ArgumentParser(description='Parameter sensitivity analysis for K+S model')
    parser.add_argument('--param', type=str, help='Parameter name (e.g., Consumption.e0)')
    parser.add_argument('--values', type=str, help='Comma-separated values to test (e.g., 0.3,0.5,0.7,1.0)')
    parser.add_argument('--periods', type=int, default=100, help='Number of periods to simulate')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--output', type=str, help='Output JSON file for results')
    parser.add_argument('--preset', type=str, choices=['demand', 'wage', 'production'], 
                        help='Use preset parameter tests')
    
    args = parser.parse_args()
    
    if args.preset == 'demand':
        # Test demand expectation parameters
        print("\nRunning preset: DEMAND EXPECTATIONS")
        param_configs = [
            {'Consumption.e0': 0.3},
            {'Consumption.e0': 0.5},
            {'Consumption.e0': 0.7},
            {'Consumption.e0': 0.9},
            {'Consumption.e0': 1.0},
        ]
        results = []
        for config in param_configs:
            param_name = list(config.keys())[0]
            values = [config[param_name]]
            result = test_parameter_sensitivity(param_name, values, args.periods, args.seed)
            results.append(result)
        
    elif args.preset == 'wage':
        # Test wage adjustment parameters
        print("\nRunning preset: WAGE ADJUSTMENT")
        results = test_parameter_sensitivity(
            'Labor.psi3', 
            [-0.1, -0.3, -0.5, -0.7], 
            args.periods, 
            args.seed
        )
        
    elif args.preset == 'production':
        # Test production/capacity parameters
        print("\nRunning preset: PRODUCTION CAPACITY")
        results = test_parameter_sensitivity(
            'Consumption.u', 
            [0.7, 0.8, 0.9, 0.95], 
            args.periods, 
            args.seed
        )
        
    elif args.param and args.values:
        # Custom parameter test
        values = [float(v) for v in args.values.split(',')]
        results = test_parameter_sensitivity(args.param, values, args.periods, args.seed)
        
    else:
        parser.print_help()
        return
    
    if args.output:
        save_results(results, args.output)


if __name__ == '__main__':
    main()
