"""
Configuration Loader for K+S Model
Loads and validates YAML configuration files
"""

import yaml
from typing import Dict, Any
from pathlib import Path


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from YAML file
    
    Args:
        config_path: Path to YAML configuration file
        
    Returns:
        Configuration dictionary
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    # Validate configuration
    validate_config(config)
    
    return config


def validate_config(config: Dict[str, Any]):
    """
    Validate configuration structure and values
    
    Args:
        config: Configuration dictionary to validate
        
    Raises:
        ValueError: If configuration is invalid
    """
    required_sections = ['country', 'capital', 'consumption', 'financial', 'labor']
    
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required configuration section: {section}")
    
    # Validate country parameters
    country = config['country']
    if 'tr' in country and not (0 <= country['tr'] <= 1):
        raise ValueError("Tax rate (tr) must be between 0 and 1")
    
    # Validate capital sector
    capital = config['capital']
    if capital.get('F10', 0) < capital.get('F1min', 0):
        raise ValueError("F10 must be >= F1min")
    if capital.get('F10', 0) > capital.get('F1max', 0):
        raise ValueError("F10 must be <= F1max")
    
    # Validate consumption sector
    consumption = config['consumption']
    if consumption.get('F20', 0) < consumption.get('F2min', 0):
        raise ValueError("F20 must be >= F2min")
    if consumption.get('F20', 0) > consumption.get('F2max', 0):
        raise ValueError("F20 must be <= F2max")
    
    # Validate financial sector
    financial = config['financial']
    if financial.get('B', 0) < 1:
        raise ValueError("Number of banks (B) must be >= 1")
    if financial.get('tauB', 0) <= 0:
        raise ValueError("Capital adequacy ratio (tauB) must be > 0")
    
    # Validate labor market
    labor = config['labor']
    if labor.get('Ls0', 0) < labor.get('Lscale', 1):
        raise ValueError("Ls0 must be >= Lscale")


def get_default_config() -> Dict[str, Any]:
    """
    Get default configuration
    
    Returns:
        Default configuration dictionary
    """
    return {
        'country': {
            'flagCons': 2,
            'flagGovExp': 2,
            'flagFiscalRule': 0,
            'flagTax': 1,
            'flagWorkerLBU': 1,
            'flagWorkerSkProd': 3,
            'TregChg': 9999,
            'gG': 0.01,
            'Crec': 0.5,
            'tr': 0.2,
            'mLim': 0.05,
            'mPer': 4,
        },
        'capital': {
            'F10': 20,
            'F1min': 10,
            'F1max': 100,
            'm1': 1.0,
            'mu1': 0.1,
            'nu': 0.04,
        },
        'consumption': {
            'F20': 50,
            'F2min': 20,
            'F2max': 200,
            'm2': 1.0,
            'b': 3.0,
            'mu20': 0.2,
            'f2min': 0.001,
        },
        'financial': {
            'B': 5,
            'tauB': 0.08,
            'rT': 0.03,
            'muBonds': -0.01,
            'muD': -0.01,
            'muDeb': 0.02,
            'muRes': -0.01,
        },
        'labor': {
            'Ls0': 10000,
            'Lscale': 10,
            'Tc': 12,
            'Tr': 480,
            'w0min': 0.5,
            'phi': 0.5,
        },
        'simulation': {
            'periods': 100,
            'seed': 42,
            'warmup': 20,
        }
    }


def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two configuration dictionaries
    
    Args:
        base: Base configuration
        override: Override configuration (takes precedence)
        
    Returns:
        Merged configuration
    """
    merged = base.copy()
    
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = merge_configs(merged[key], value)
        else:
            merged[key] = value
    
    return merged


if __name__ == "__main__":
    # Test configuration loading
    import sys
    
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
        try:
            config = load_config(config_path)
            print(f"Successfully loaded configuration from {config_path}")
            print("\nCountry parameters:")
            for key, value in config['country'].items():
                print(f"  {key}: {value}")
        except Exception as e:
            print(f"Error loading configuration: {e}")
            sys.exit(1)
    else:
        print("Usage: python config.py <config_file.yaml>")
        print("\nExample: python config.py configs/baseline.yaml")
