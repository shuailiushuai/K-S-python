"""
Parameters Management

Loads and manages model parameters from configuration files.
"""

import json
from typing import Any, Dict, Optional


class Parameters:
    """
    Model parameters manager
    
    Loads parameters from JSON configuration files and provides
    access to parameter values with defaults.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize parameters
        
        Args:
            config_file: Path to JSON configuration file
        """
        self.params = self._load_defaults()
        
        if config_file:
            self.load_from_file(config_file)
        
        # Store regime change parameters
        self._regime_change_params = {}
        self._extract_regime_change_params()
    
    def _load_defaults(self) -> Dict[str, Any]:
        """
        Load default parameter values
        
        These correspond to a baseline configuration similar to
        the original model's default setup.
        """
        return {
            # Simulation
            'seed': 42,
            
            # Country-level
            'Crec': 0.5,
            'TregChg': 0,  # No regime change by default
            'gG': 0.0,
            'omicron': 0.5,
            'stick': 0.1,
            'tr': 0.1,
            'trChg': 0.1,
            
            # Financial sector
            'B': 10,
            'DebRule': 0.9,
            'DefPrule': 0.03,
            'EqB0': 0.1,
            'Lambda': 10.0,
            'LambdaChg': 10.0,
            'Lambda0': 1.0,
            'PhiB': 0.1,
            'Trule': 50,
            'Ut': 0.05,
            'alphaB': 2.0,
            'betaB': 1.0,
            'dB': 0.5,
            'deltaB': 0.1,
            'deltaDeb': 0.1,
            'gammaPi': 1.5,
            'gammaU': 0.5,
            'muBonds': 0.5,
            'muD': 0.5,
            'muDeb': 0.5,
            'muRes': 0.9,
            'muResChg': 0.9,
            'piT': 0.02,
            'rAdj': 0.001,
            'rT': 0.03,
            'rTchg': 0.03,
            'tauB': 0.08,
            'tauBchg': 0.08,
            
            # Capital-good sector
            'F10': 20,
            'F1max': 50,
            'F1min': 10,
            'L1rdMax': 0.2,
            'L1shortMax': 0.5,
            'NW10': 100.0,
            'alpha1': 3.0,
            'alpha2': 3.0,
            'beta1': 3.0,
            'beta2': 3.0,
            'd1': 0.5,
            'gamma': 0.5,
            'm1': 1.0,
            'mu1': 0.04,
            'nu': 0.04,
            'x1inf': -0.15,
            'x1sup': 0.15,
            'xi': 0.5,
            'zeta1': 0.3,
            'zeta2': 0.3,
            'pK0': 1.0,  # Will be recalculated during initialization
            'x2inf': -0.15,
            'x2sup': 0.15,
            
            # Consumption-good sector
            'F20': 100,
            'F2max': 200,
            'F2min': 50,
            'NW20': 100.0,
            'b': 20.0,
            'bChg': 20.0,
            'chi': 1.0,
            'd2': 0.5,
            'e0': 0.5,
            'e0Chg': 0.5,
            'e1': 0.4,
            'e2': 0.3,
            'e3': 0.2,
            'e4': 0.1,
            'e5': 0.5,
            'eta': 20.0,
            'f2min': 0.0001,
            'iota': 0.1,
            'kappaMax': 0.2,
            'kappaMin': 0.0,
            'm2': 1.0,
            'mu20': 0.35,
            'mu20Chg': 0.35,
            'omega1': 1.0,
            'omega2': 1.0,
            'omega3': 0.0,
            'u': 0.75,
            'upsilon': 0.02,
            'initial_demand': 100.0,
            'pC0': 1.0,  # Will be recalculated during initialization
            
            # Labor market
            'Gamma': 0.0,
            'GammaCost': 0.1,
            'Ls0': 1000,
            'Lscale': 1,
            'Tc': 1,
            'Tr': 0,
            'Ts': 4,
            'TsChg': 4,
            'delta': 0.01,
            'epsilon': 0.01,
            'kappa': 1.0,
            'lambda': 1.0,
            'omega': 1.0,
            'omegaU': 3.0,
            'phi': 0.5,
            'phiChg': 0.5,
            'psi1': 0.5,
            'psi2': 0.5,
            'psi3': 0.0,
            'psi4': 0.0,
            'psi5': 0.0,
            'psi6': 0.0,
            'sigma': 0.5,
            'tauG': 0.005,
            'tauT': 0.01,
            'tauU': 0.01,
            'theta': 0.0,
            'w0min': 1.0,
            'wCap': 0.0,
            
            # Control flags
            'flagCons': 0,
            'flagGovExp': 2,
            'flagTax': 0,
            'flagCreditRule': 2,
            'flagFiscalRule': 0,
            'flagExpect': 0,
            'flagAddWorkers': 0,
            'flagSearchMode': 0,
            'flagSearchDisc': 0,
            'flagHireSeq': 0,
            'flagHireOrder1': 0,
            'flagHireOrder2': 0,
            'flagFireOrder1': 0,
            'flagFireOrder2': 0,
            'flagFireRule': 4,
            'flagHeterWage': 0,
            'flagWageOffer': 0,
            'flagWagePremium': 1,
            'flagIndexWage': 1,
            'flagIndexMinWage': 0,
            'flagLearn1': 0,
            'flagWorkerLBU': 0,
            'flagWorkerSkProd': 0,
        }
    
    def load_from_file(self, filename: str):
        """
        Load parameters from JSON file
        
        Args:
            filename: Path to JSON configuration file
        """
        try:
            with open(filename, 'r') as f:
                loaded_params = json.load(f)
                self.params.update(loaded_params)
        except FileNotFoundError:
            print(f"Warning: Configuration file '{filename}' not found. Using defaults.")
        except json.JSONDecodeError:
            print(f"Warning: Error parsing '{filename}'. Using defaults.")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get parameter value
        
        Args:
            key: Parameter name
            default: Default value if parameter not found
            
        Returns:
            Parameter value
        """
        return self.params.get(key, default)
    
    def set(self, key: str, value: Any):
        """
        Set parameter value
        
        Args:
            key: Parameter name
            value: Parameter value
        """
        self.params[key] = value
    
    def _extract_regime_change_params(self):
        """
        Extract parameters that have 'Chg' suffix for regime change
        """
        for key in self.params:
            if key.endswith('Chg'):
                base_key = key[:-3]  # Remove 'Chg' suffix
                self._regime_change_params[base_key] = self.params[key]
    
    def apply_regime_change(self):
        """
        Apply regime change by updating parameters with 'Chg' values
        """
        for base_key, chg_value in self._regime_change_params.items():
            self.params[base_key] = chg_value
        
        print("Regime change parameters applied:")
        for base_key in self._regime_change_params:
            print(f"  {base_key}: {self.params[base_key]}")
    
    def save_to_file(self, filename: str):
        """
        Save current parameters to JSON file
        
        Args:
            filename: Output filename
        """
        with open(filename, 'w') as f:
            json.dump(self.params, f, indent=2)
    
    def __repr__(self):
        return f"Parameters({len(self.params)} parameters loaded)"
