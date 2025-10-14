#!/usr/bin/env python3
"""
K+S Model Simulation Runner
Main entry point for running K+S ABM simulations
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from model import run_simulation


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Run K+S Agent-Based Model simulation'
    )
    parser.add_argument(
        'config',
        type=str,
        help='Path to YAML configuration file'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=1,
        help='Random seed for reproducibility (default: 1)'
    )
    parser.add_argument(
        '--steps',
        type=int,
        default=None,
        help='Number of simulation steps (default: from config)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output file for results (optional)'
    )
    
    args = parser.parse_args()
    
    # Check config file exists
    if not Path(args.config).exists():
        print(f"Error: Configuration file '{args.config}' not found")
        sys.exit(1)
    
    print(f"K+S Agent-Based Model")
    print(f"Configuration: {args.config}")
    print(f"Random seed: {args.seed}")
    print(f"Steps: {args.steps if args.steps else 'from config'}")
    print()
    
    # Run simulation
    try:
        country = run_simulation(args.config, seed=args.seed, steps=args.steps)
        
        # Get results
        results = country.get_results()
        
        print("\n" + "="*60)
        print("FINAL RESULTS")
        print("="*60)
        for key, value in results.items():
            if isinstance(value, float):
                print(f"{key:20s}: {value:12.4f}")
            else:
                print(f"{key:20s}: {value}")
        
        # Save results if output file specified
        if args.output:
            import json
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\nResults saved to: {args.output}")
        
    except Exception as e:
        print(f"\nSimulation failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
