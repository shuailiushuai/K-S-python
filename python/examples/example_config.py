"""
Example: Configuration System and LSD File Parsing
Demonstrates loading and using configuration files
"""


# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from model import Country, LSDConfigParser, load_scenario
from model.random_engine import random_engine
from pathlib import Path
import sys


def example_default_config():
    """Example 1: Using default configuration"""
    print("=" * 70)
    print("Example 1: Default Configuration")
    print("=" * 70)
    print()
    
    # Create country with default config
    country = Country()
    country.initialize()
    
    print(f"Initialized with defaults:")
    print(f"  Capital firms: {len(country.capital_sector.firms)}")
    print(f"  Consumption firms: {len(country.consumption_sector.firms)}")
    print(f"  Banks: {len(country.financial_sector.banks)}")
    print(f"  Workers: {len(country.workers)}")
    print(f"  Tax rate: {country._tr}")
    print(f"  Government spending flag: {country._flagGovExp}")
    print()


def example_custom_config():
    """Example 2: Custom configuration dictionary"""
    print("=" * 70)
    print("Example 2: Custom Configuration")
    print("=" * 70)
    print()
    
    # Create custom configuration
    config = {
        'simulation': {
            'seed': 123,
            'periods': 100,
        },
        'country': {
            'tr': 0.25,  # 25% tax rate
            'flagTax': 1,
            'flagGovExp': 2,
        },
        'capital': {
            'F10': 15,  # Start with 15 capital firms
            'nu': 0.05,  # 5% R&D investment
        },
        'consumption': {
            'F20': 40,  # Start with 40 consumption firms
            'mu20': 0.25,  # 25% initial markup
        },
        'financial': {
            'B': 10,  # 10 banks
            'rT': 0.04,  # 4% target interest rate
        },
        'labor': {
            'Ls0': 800,  # 800 workers
            'Lscale': 10,
            'phi': 0.6,  # 60% unemployment benefit ratio
        },
    }
    
    # Create country with custom config
    country = Country(config=config)
    country.initialize()
    
    print(f"Initialized with custom config:")
    print(f"  Capital firms: {len(country.capital_sector.firms)}")
    print(f"  Consumption firms: {len(country.consumption_sector.firms)}")
    print(f"  Banks: {len(country.financial_sector.banks)}")
    print(f"  Workers: {len(country.workers)}")
    print(f"  Tax rate: {country._tr}")
    print(f"  Target interest rate: {country.financial_sector._rT}")
    print()


def example_lsd_parser():
    """Example 3: Parsing LSD configuration file"""
    print("=" * 70)
    print("Example 3: LSD Configuration Parser")
    print("=" * 70)
    print()
    
    # Check if LSD files exist
    lsd_dir = Path('..') / 'Cent_wage-Baseline_v2.lsd'
    
    if not lsd_dir.exists():
        print(f"Warning: LSD file not found at {lsd_dir}")
        print("Demonstrating parser structure instead...")
        print()
        
        # Show parser capabilities
        print("LSD Parser Features:")
        print("  - Parses Variable: Type: parameter/variable definitions")
        print("  - Extracts numeric values and converts to Python types")
        print("  - Organizes by configuration sections:")
        print("    * country: General model parameters and flags")
        print("    * capital: Capital goods sector parameters")
        print("    * consumption: Consumption goods sector parameters")
        print("    * financial: Banking and financial parameters")
        print("    * labor: Labor market parameters")
        print()
        
        print("Example of parsed structure:")
        print("  {")
        print("    'simulation': {'seed': 42, 'periods': 500},")
        print("    'country': {'tr': 0.2, 'flagTax': 1, ...},")
        print("    'capital': {'F10': 20, 'nu': 0.04, ...},")
        print("    'consumption': {'F20': 50, 'mu20': 0.2, ...},")
        print("    'financial': {'B': 5, 'rT': 0.03, ...},")
        print("    'labor': {'Ls0': 1000, 'Lscale': 10, ...}")
        print("  }")
        print()
        return
    
    try:
        # Parse LSD file
        parser = LSDConfigParser(str(lsd_dir))
        config = parser.parse()
        
        print(f"Parsed: {lsd_dir.name}")
        print()
        print("Configuration sections:")
        for section in ['simulation', 'country', 'capital', 'consumption', 'financial', 'labor']:
            if section in config:
                n_params = len(config[section])
                print(f"  {section}: {n_params} parameters")
        print()
        
        # Show some key parameters
        print("Key parameters:")
        if 'capital' in config:
            print(f"  F10 (initial capital firms): {config['capital'].get('F10')}")
            print(f"  nu (R&D investment rate): {config['capital'].get('nu')}")
        if 'consumption' in config:
            print(f"  F20 (initial consumption firms): {config['consumption'].get('F20')}")
            print(f"  mu20 (initial markup): {config['consumption'].get('mu20')}")
        if 'financial' in config:
            print(f"  B (number of banks): {config['financial'].get('B')}")
            print(f"  rT (target interest rate): {config['financial'].get('rT')}")
        print()
        
        # Create country with parsed config
        country = Country(config=config)
        country.initialize()
        
        print("Country initialized from LSD file:")
        print(f"  Capital firms: {len(country.capital_sector.firms)}")
        print(f"  Consumption firms: {len(country.consumption_sector.firms)}")
        print(f"  Banks: {len(country.financial_sector.banks)}")
        print(f"  Workers: {len(country.workers)}")
        print()
        
    except Exception as e:
        print(f"Error parsing LSD file: {e}")
        print()


def example_scenario_loading():
    """Example 4: Loading predefined scenarios"""
    print("=" * 70)
    print("Example 4: Predefined Scenarios")
    print("=" * 70)
    print()
    
    # List available scenarios
    scenarios = {
        'baseline': 'Cent_wage-Baseline_v2.lsd - Baseline with financial market',
        'benchmark': 'Cent_wage-Benchmark_v1.lsd - Benchmark minimal finance',
        'no_skills': 'No_skills-Fix_entry-No_fin.lsd - No skills, fixed entry',
        'ten_skills_no_fin': 'Ten_skills-Free_entry-No_fin.lsd - With tenure skills',
        'ten_skills_full_fin': 'Ten_skills-Free_entry-Full_fin.lsd - Full financial',
        'ten_skills_bas_fin': 'Ten_skills-Free_entry-Bas_fin.lsd - Basic financial',
    }
    
    print("Available predefined scenarios:")
    for name, desc in scenarios.items():
        print(f"  {name:20s} - {desc}")
    print()
    
    print("To load a scenario:")
    print("  from model import load_scenario")
    print("  config = load_scenario('baseline', base_path='..')")
    print("  country = Country(config=config)")
    print("  country.initialize()")
    print()


def example_comparison():
    """Example 5: Compare different configurations"""
    print("=" * 70)
    print("Example 5: Configuration Comparison")
    print("=" * 70)
    print()
    
    # Create two different configurations
    configs = {
        'low_tax': {
            'country': {'tr': 0.15},  # 15% tax
            'capital': {'F10': 20},
            'consumption': {'F20': 50},
        },
        'high_tax': {
            'country': {'tr': 0.35},  # 35% tax
            'capital': {'F10': 20},
            'consumption': {'F20': 50},
        },
    }
    
    for config_name, config in configs.items():
        country = Country(config=config)
        country.initialize()
        
        print(f"{config_name.upper()} Configuration:")
        print(f"  Tax rate: {country._tr * 100:.1f}%")
        print(f"  Firms: {len(country.capital_sector.firms)} capital, "
              f"{len(country.consumption_sector.firms)} consumption")
        print(f"  Workers: {len(country.workers)}")
        print()


def main():
    """Run all examples"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "K+S MODEL CONFIGURATION SYSTEM" + " " * 23 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    try:
        example_default_config()
        example_custom_config()
        example_lsd_parser()
        example_scenario_loading()
        example_comparison()
        
        print("=" * 70)
        print("All configuration examples completed successfully!")
        print("=" * 70)
        print()
        
        print("Next steps:")
        print("  1. Create custom configuration for your experiments")
        print("  2. Parse existing LSD files to match original scenarios")
        print("  3. Run simulations with different parameter combinations")
        print("  4. Compare results across configurations")
        print()
        
    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
