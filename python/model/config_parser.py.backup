"""
LSD Configuration Parser
Parses .lsd configuration files from the original K+S model
"""

from typing import Dict, List, Optional, Any
import re
from pathlib import Path


class LSDConfigParser:
    """
    Parser for LSD configuration files (.lsd)
    Extracts parameters and initial conditions
    """
    
    def __init__(self, config_path: str):
        """
        Initialize parser
        
        Args:
            config_path: Path to .lsd file
        """
        self.config_path = Path(config_path)
        self.raw_content = ""
        self.parameters = {}
        self.variables = {}
        self.objects = {}
        
    def parse(self) -> Dict[str, Any]:
        """
        Parse the LSD file
        
        Returns:
            Dictionary with parsed configuration
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8', errors='ignore') as f:
            self.raw_content = f.read()
        
        # Parse structure
        self._parse_parameters()
        self._parse_variables()
        self._parse_objects()
        
        # Build configuration dictionary
        config = self._build_config_dict()
        
        return config
    
    def _parse_parameters(self):
        """Extract parameters from LSD file"""
        # LSD format: Variable: name
        #             Type: parameter
        #             Value: <number>
        
        param_pattern = r'Variable:\s+(\w+).*?Type:\s+parameter.*?Value:\s+([-\d.eE+]+)'
        matches = re.findall(param_pattern, self.raw_content, re.DOTALL | re.IGNORECASE)
        
        for name, value in matches:
            try:
                # Try to parse as float
                self.parameters[name] = float(value)
            except ValueError:
                # Keep as string if can't parse
                self.parameters[name] = value
    
    def _parse_variables(self):
        """Extract variables from LSD file"""
        # Variables with initial values
        var_pattern = r'Variable:\s+(\w+).*?Type:\s+variable.*?Value:\s+([-\d.eE+]+)'
        matches = re.findall(var_pattern, self.raw_content, re.DOTALL | re.IGNORECASE)
        
        for name, value in matches:
            try:
                self.variables[name] = float(value)
            except ValueError:
                self.variables[name] = value
    
    def _parse_objects(self):
        """Extract object structure"""
        # Object definitions
        obj_pattern = r'Object:\s+(\w+).*?End Object'
        matches = re.findall(obj_pattern, self.raw_content, re.DOTALL | re.IGNORECASE)
        
        for name in matches:
            if name not in self.objects:
                self.objects[name] = {}
    
    def _build_config_dict(self) -> Dict[str, Any]:
        """
        Build standardized configuration dictionary
        
        Returns:
            Configuration dictionary
        """
        config = {
            'simulation': {
                'seed': self.parameters.get('RND_SEED', 42),
                'periods': 500,  # Default, can be overridden
            },
            'country': self._build_country_config(),
            'capital': self._build_capital_config(),
            'consumption': self._build_consumption_config(),
            'financial': self._build_financial_config(),
            'labor': self._build_labor_config(),
        }
        
        return config
    
    def _build_country_config(self) -> Dict[str, Any]:
        """Build country-level configuration"""
        return {
            # Flags
            'flagCons': int(self.parameters.get('flagCons', 2)),
            'flagTax': int(self.parameters.get('flagTax', 1)),
            'flagGovExp': int(self.parameters.get('flagGovExp', 2)),
            'flagFiscalRule': int(self.parameters.get('flagFiscalRule', 0)),
            'flagExpect': int(self.parameters.get('flagExpect', 0)),
            'flagAddWorkers': int(self.parameters.get('flagAddWorkers', 0)),
            'flagSearchMode': int(self.parameters.get('flagSearchMode', 0)),
            'flagSearchDisc': int(self.parameters.get('flagSearchDisc', 0)),
            'flagHireSeq': int(self.parameters.get('flagHireSeq', 0)),
            'flagAllFirmsChg': int(self.parameters.get('flagAllFirmsChg', 0)),
            
            # Parameters
            'Crec': self.parameters.get('Crec', 0.5),
            'TregChg': int(self.parameters.get('TregChg', 0)),
            'gG': self.parameters.get('gG', 0.0),
            'mLim': self.parameters.get('mLim', 0.1),
            'mPer': int(self.parameters.get('mPer', 4)),
            'omicron': self.parameters.get('omicron', 0.25),
            'stick': self.parameters.get('stick', 0.1),
            'tr': self.parameters.get('tr', 0.2),
            'trChg': self.parameters.get('trChg', 0.2),
            'x2inf': self.parameters.get('x2inf', -0.25),
            'x2sup': self.parameters.get('x2sup', 0.25),
        }
    
    def _build_capital_config(self) -> Dict[str, Any]:
        """Build capital sector configuration"""
        return {
            # Initial conditions
            'F10': int(self.parameters.get('F10', 20)),
            'F1min': int(self.parameters.get('F1min', 10)),
            'F1max': int(self.parameters.get('F1max', 100)),
            'NW10': self.parameters.get('NW10', 100.0),
            'Deb10ratio': self.parameters.get('Deb10ratio', 0.5),
            
            # Production parameters
            'm1': self.parameters.get('m1', 1.0),
            'mu1': self.parameters.get('mu1', 0.1),
            'nu': self.parameters.get('nu', 0.04),
            'd1': self.parameters.get('d1', 0.5),
            'n1': int(self.parameters.get('n1', 4)),
            
            # R&D parameters
            'alpha1': self.parameters.get('alpha1', 1.0),
            'beta1': self.parameters.get('beta1', 1.0),
            'alpha2': self.parameters.get('alpha2', 1.0),
            'beta2': self.parameters.get('beta2', 1.0),
            'xi': self.parameters.get('xi', 0.5),
            'zeta1': self.parameters.get('zeta1', 1.0),
            'zeta2': self.parameters.get('zeta2', 1.0),
            'x1inf': self.parameters.get('x1inf', -0.15),
            'x1sup': self.parameters.get('x1sup', 0.15),
            'x5': self.parameters.get('x5', 0.5),
            
            # Market parameters
            'gamma': self.parameters.get('gamma', 0.25),
            'Phi3': self.parameters.get('Phi3', 0.1),
            'Phi4': self.parameters.get('Phi4', 1.0),
            'L1rdMax': self.parameters.get('L1rdMax', 0.25),
            'L1shortMax': self.parameters.get('L1shortMax', 0.1),
        }
    
    def _build_consumption_config(self) -> Dict[str, Any]:
        """Build consumption sector configuration"""
        return {
            # Initial conditions
            'F20': int(self.parameters.get('F20', 50)),
            'F2min': int(self.parameters.get('F2min', 20)),
            'F2max': int(self.parameters.get('F2max', 200)),
            'NW20': self.parameters.get('NW20', 100.0),
            'Deb20ratio': self.parameters.get('Deb20ratio', 0.5),
            
            # Production parameters
            'm2': self.parameters.get('m2', 1.0),
            'mu20': self.parameters.get('mu20', 0.2),
            'mu20Chg': self.parameters.get('mu20Chg', 0.2),
            'b': self.parameters.get('b', 3.0),
            'bChg': self.parameters.get('bChg', 3.0),
            'd2': self.parameters.get('d2', 0.5),
            'n2': int(self.parameters.get('n2', 4)),
            'eta': self.parameters.get('eta', 20.0),
            'u': self.parameters.get('u', 0.75),
            'iota': self.parameters.get('iota', 0.1),
            
            # Expectation parameters
            'e0': self.parameters.get('e0', 0.2),
            'e0Chg': self.parameters.get('e0Chg', 0.2),
            'e1': self.parameters.get('e1', 1.0),
            'e2': self.parameters.get('e2', 0.0),
            'e3': self.parameters.get('e3', 0.0),
            'e4': self.parameters.get('e4', 0.0),
            'e5': self.parameters.get('e5', 0.0),
            'e6': self.parameters.get('e6', 0.0),
            'e7': self.parameters.get('e7', 0.0),
            'e8': self.parameters.get('e8', 0.0),
            
            # Market parameters
            'chi': self.parameters.get('chi', 2.0),
            'upsilon': self.parameters.get('upsilon', 0.01),
            'omega1': self.parameters.get('omega1', 1.0),
            'omega2': self.parameters.get('omega2', 1.0),
            'omega3': self.parameters.get('omega3', 1.0),
            'f2min': self.parameters.get('f2min', 0.001),
            'f2minPosChg': self.parameters.get('f2minPosChg', 0.1),
            'f2trdChg': self.parameters.get('f2trdChg', 0.0),
            'kappaMin': self.parameters.get('kappaMin', 0.0),
            'kappaMax': self.parameters.get('kappaMax', 0.2),
            'Phi1': self.parameters.get('Phi1', 0.1),
            'Phi2': self.parameters.get('Phi2', 1.0),
            'ent2HldPer': int(self.parameters.get('ent2HldPer', 0)),
            'ent2HldShr': self.parameters.get('ent2HldShr', 0.5),
        }
    
    def _build_financial_config(self) -> Dict[str, Any]:
        """Build financial sector configuration"""
        return {
            # Banking structure
            'B': int(self.parameters.get('B', 5)),
            'EqB0': self.parameters.get('EqB0', 1.0),
            'alphaB': self.parameters.get('alphaB', 2.0),
            'betaB': self.parameters.get('betaB', 2.0),
            'PhiB': self.parameters.get('PhiB', 0.5),
            'dB': self.parameters.get('dB', 0.5),
            'mPerB': int(self.parameters.get('mPerB', 4)),
            
            # Credit parameters
            'Lambda': self.parameters.get('Lambda', 5.0),
            'LambdaChg': self.parameters.get('LambdaChg', 5.0),
            'Lambda0': self.parameters.get('Lambda0', 100.0),
            'deltaB': self.parameters.get('deltaB', 0.1),
            'kConst': self.parameters.get('kConst', 0.01),
            'flagCreditRule': int(self.parameters.get('flagCreditRule', 0)),
            
            # Interest rates
            'rT': self.parameters.get('rT', 0.03),
            'rTchg': self.parameters.get('rTchg', 0.03),
            'muD': self.parameters.get('muD', -0.01),
            'muDeb': self.parameters.get('muDeb', 0.02),
            'muRes': self.parameters.get('muRes', -0.005),
            'muResChg': self.parameters.get('muResChg', -0.005),
            'muBonds': self.parameters.get('muBonds', 0.01),
            'rAdj': self.parameters.get('rAdj', 0.0025),
            'rhoBonds': self.parameters.get('rhoBonds', 0.0),
            'thetaBonds': self.parameters.get('thetaBonds', 10.0),
            
            # Monetary policy
            'piT': self.parameters.get('piT', 0.02),
            'Ut': self.parameters.get('Ut', 0.05),
            'gammaPi': self.parameters.get('gammaPi', 1.5),
            'gammaU': self.parameters.get('gammaU', 0.5),
            
            # Fiscal policy
            'DebRule': self.parameters.get('DebRule', 0.6),
            'DefPrule': self.parameters.get('DefPrule', 0.03),
            'deltaDeb': self.parameters.get('deltaDeb', 0.1),
            'Trule': int(self.parameters.get('Trule', 10)),
            
            # Regulation
            'tauB': self.parameters.get('tauB', 0.08),
            'tauBchg': self.parameters.get('tauBchg', 0.08),
        }
    
    def _build_labor_config(self) -> Dict[str, Any]:
        """Build labor market configuration"""
        return {
            # Labor supply
            'Ls0': int(self.parameters.get('Ls0', 1000)),
            'Lscale': int(self.parameters.get('Lscale', 10)),
            'delta': self.parameters.get('delta', 0.01),
            
            # Worker parameters
            'Tc': int(self.parameters.get('Tc', 12)),
            'Tp': int(self.parameters.get('Tp', 0)),
            'Tr': int(self.parameters.get('Tr', 0)),
            'Ts': int(self.parameters.get('Ts', 1)),
            'TsChg': int(self.parameters.get('TsChg', 1)),
            
            # Job search
            'omega': self.parameters.get('omega', 2.0),
            'omegaPreChg': self.parameters.get('omegaPreChg', 2.0),
            'omegaPosChg': self.parameters.get('omegaPosChg', 2.0),
            'omegaU': self.parameters.get('omegaU', 3.0),
            'epsilon': self.parameters.get('epsilon', 0.01),
            'kappa': self.parameters.get('kappa', 2.0),
            'lambda': self.parameters.get('lambda', 1.0),
            
            # Wages
            'w0min': self.parameters.get('w0min', 0.5),
            'wCap': self.parameters.get('wCap', 2.0),
            'phi': self.parameters.get('phi', 0.5),
            'phiChg': self.parameters.get('phiChg', 0.5),
            'psi1': self.parameters.get('psi1', 0.5),
            'psi2': self.parameters.get('psi2', 0.5),
            'psi3': self.parameters.get('psi3', -0.5),
            'psi4': self.parameters.get('psi4', 0.5),
            'psi5': self.parameters.get('psi5', 0.5),
            'psi6': self.parameters.get('psi6', 0.5),
            'rho': self.parameters.get('rho', 0.5),
            
            # Skills
            'sigma': self.parameters.get('sigma', 0.5),
            'tauG': self.parameters.get('tauG', 1.0),
            'tauT': self.parameters.get('tauT', 0.01),
            'tauU': self.parameters.get('tauU', 0.01),
            'theta': self.parameters.get('theta', 0.1),
            'Gamma': self.parameters.get('Gamma', 0.5),
            'GammaCost': self.parameters.get('GammaCost', 0.1),
            
            # Behavior flags
            'flagLearn1': int(self.parameters.get('flagLearn1', 0)),
            'flagWorkerLBU': int(self.parameters.get('flagWorkerLBU', 0)),
            'flagWorkerSkProd': int(self.parameters.get('flagWorkerSkProd', 0)),
            'flagHeterWage': int(self.parameters.get('flagHeterWage', 0)),
            'flagWageOffer': int(self.parameters.get('flagWageOffer', 0)),
            'flagWagePremium': int(self.parameters.get('flagWagePremium', 0)),
            'flagIndexWage': int(self.parameters.get('flagIndexWage', 0)),
            'flagIndexMinWage': int(self.parameters.get('flagIndexMinWage', 0)),
            'flagIndexMinWageChg': int(self.parameters.get('flagIndexMinWageChg', 0)),
            'flagHireOrder1': int(self.parameters.get('flagHireOrder1', 0)),
            'flagHireOrder1Chg': int(self.parameters.get('flagHireOrder1Chg', 0)),
            'flagHireOrder2': int(self.parameters.get('flagHireOrder2', 0)),
            'flagHireOrder2Chg': int(self.parameters.get('flagHireOrder2Chg', 0)),
            'flagFireOrder1': int(self.parameters.get('flagFireOrder1', 0)),
            'flagFireOrder1Chg': int(self.parameters.get('flagFireOrder1Chg', 0)),
            'flagFireOrder2': int(self.parameters.get('flagFireOrder2', 0)),
            'flagFireOrder2Chg': int(self.parameters.get('flagFireOrder2Chg', 0)),
            'flagFireRule': int(self.parameters.get('flagFireRule', 0)),
            'flagFireRuleChg': int(self.parameters.get('flagFireRuleChg', 0)),
        }


def parse_lsd_config(config_path: str) -> Dict[str, Any]:
    """
    Parse an LSD configuration file
    
    Args:
        config_path: Path to .lsd file
        
    Returns:
        Configuration dictionary
    """
    parser = LSDConfigParser(config_path)
    return parser.parse()


# Predefined configurations matching the original scenarios
SCENARIO_CONFIGS = {
    'baseline': 'Cent_wage-Baseline_v2.lsd',
    'benchmark': 'Cent_wage-Benchmark_v1.lsd',
    'no_skills': 'No_skills-Fix_entry-No_fin.lsd',
    'ten_skills_no_fin': 'Ten_skills-Free_entry-No_fin.lsd',
    'ten_skills_full_fin': 'Ten_skills-Free_entry-Full_fin.lsd',
    'ten_skills_bas_fin': 'Ten_skills-Free_entry-Bas_fin.lsd',
}


def load_scenario(scenario_name: str, base_path: str = '..') -> Dict[str, Any]:
    """
    Load a predefined scenario configuration
    
    Args:
        scenario_name: Name of scenario (e.g., 'baseline', 'benchmark')
        base_path: Base path to configuration files
        
    Returns:
        Configuration dictionary
    """
    if scenario_name not in SCENARIO_CONFIGS:
        available = ', '.join(SCENARIO_CONFIGS.keys())
        raise ValueError(f"Unknown scenario '{scenario_name}'. Available: {available}")
    
    config_file = SCENARIO_CONFIGS[scenario_name]
    config_path = Path(base_path) / config_file
    
    return parse_lsd_config(str(config_path))
