"""
Example usage of the K+S Model Python implementation.

This script demonstrates how to initialize and run the model with a
configuration file.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import load_configuration
from utils import set_rng_seed
from ks_model.agents import Worker


def simple_worker_example():
    """
    Simple example showing Worker agent initialization and usage.
    """
    print("=" * 60)
    print("K+S Model - Simple Worker Example")
    print("=" * 60)
    
    # Set random seed for reproducibility
    set_rng_seed(12345)
    
    # Worker parameters
    params = {
        'Tc': 12,  # Contract term: 12 periods
        'Tr': 40,  # Retirement age: 40 periods
        'w0min': 1.0,  # Minimum wage
        'Ts': 4,  # Wage memory: 4 periods
        'epsilon': 0.05,  # Minimum wage increment to change jobs
        'omega': 5,  # Number of job applications
        'omegaU': 10,  # Applications when unemployed
        'flagSearchMode': 0,  # Always search
        'flagWorkerLBU': 3,  # Learning by vintage and tenure
        'tauT': 0.01,  # Tenure learning rate
        'tauU': 0.02,  # Skills deterioration rate for unemployed
    }
    
    # Create workers
    workers = []
    for i in range(10):
        worker = Worker(worker_id=i+1, initial_params=params)
        workers.append(worker)
        print(f"Created Worker {worker.state.ID}: " +
              f"age={worker.state.age}, " +
              f"w={worker.state.w:.2f}, " +
              f"s={worker.state.s:.2f}")
    
    print("\n" + "-" * 60)
    print("Simulating 5 periods...")
    print("-" * 60 + "\n")
    
    # Simulate a few periods
    for t in range(1, 6):
        print(f"Period {t}:")
        
        for worker in workers:
            # Age workers
            new_age = worker.compute_age(t)
            
            # Update skills (assuming some are employed)
            if t > 1 and worker.state.ID % 3 == 0:  # Every 3rd worker employed
                worker.state.employed = 2
                worker.state.Te = t - 1
            
            skills = worker.compute_skills(t)
            requested_wage = worker.compute_requested_wage(t)
            
            print(f"  Worker {worker.state.ID}: " +
                  f"age={new_age}, " +
                  f"employed={worker.state.employed}, " +
                  f"s={skills:.3f}, " +
                  f"wReq={requested_wage:.2f}")
        
        print()


def load_config_example():
    """
    Example showing how to load an LSD configuration file.
    """
    print("=" * 60)
    print("K+S Model - Configuration Loading Example")
    print("=" * 60)
    
    # Path to configuration file (relative to example location)
    config_path = Path(__file__).parent.parent.parent / "No_skills-Fix_entry-No_fin.lsd"
    
    if not config_path.exists():
        print(f"Configuration file not found: {config_path}")
        print("Please ensure the .lsd files are in the repository root.")
        return
    
    print(f"\nLoading configuration from: {config_path.name}")
    
    try:
        config = load_configuration(str(config_path))
        
        print(f"\nLoaded {len(config['parameters'])} parameters")
        print("\nSample parameters:")
        
        # Display some key parameters
        key_params = [
            'tr', 'B', 'Lambda', 'F10', 'F20', 'Ls0', 
            'delta', 'omega', 'phi', 'mu1', 'mu20'
        ]
        
        for param in key_params:
            if param in config['parameters']:
                value = config['parameters'][param]
                print(f"  {param:15s} = {value}")
        
        print("\n" + "-" * 60)
        print("Configuration loaded successfully!")
        print("-" * 60)
        
    except Exception as e:
        print(f"Error loading configuration: {e}")
        import traceback
        traceback.print_exc()


def main():
    """
    Run all examples.
    """
    # Example 1: Simple worker simulation
    simple_worker_example()
    
    print("\n" * 2)
    
    # Example 2: Configuration loading
    load_config_example()
    
    print("\n" * 2)
    print("=" * 60)
    print("Examples completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Complete Firm1, Firm2, Bank agent implementations")
    print("  2. Implement sector containers")
    print("  3. Build simulation scheduler")
    print("  4. Add data collection and analysis")
    print("  5. Validate against C++ model outputs")


if __name__ == "__main__":
    main()
