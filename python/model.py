"""
K+S Model Main Country/Model Class
Translated from fun_KS_country.h and fun_KS.cpp
"""

import yaml
from typing import Dict, Any, List, Optional
from agents import Worker, Firm1, Firm2, Bank
from markets import LaborMarket, CapitalGoodsSector, ConsumptionGoodsSector, FinancialSector
from utils import set_seed, get_random_generator


class Country:
    """
    Main country container for K+S model
    Coordinates all sectors and manages simulation
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize country
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.t = 0  # Current time period
        
        # Sectors
        self.financial = FinancialSector(config)
        self.labor = LaborMarket(config)
        self.capital = CapitalGoodsSector(config)
        self.consumption = ConsumptionGoodsSector(config)
        
        # Government variables
        self.G = 0.0  # Government expenditure
        self.Tax = 0.0  # Total tax revenue
        self.TaxDiv = 0.0  # Tax on dividends
        self.Def = 0.0  # Government deficit
        self.Deb = 0.0  # Government debt
        
        # Macroeconomic variables
        self.GDPnom = 0.0  # Nominal GDP
        self.GDPreal = 0.0  # Real GDP
        self.C = 0.0  # Total consumption
        self.Cd = 0.0  # Desired consumption
        self.Creal = 0.0  # Real consumption
        self.A = 1.0  # Aggregate productivity
        self.dAb = 0.0  # Productivity growth
        self.Sav = 0.0  # Savings
        self.Div = 0.0  # Total dividends
        
        # Control flags
        self.flagCons = int(config.get('flagCons', 1))
        self.flagTax = int(config.get('flagTax', 1))
        self.flagGovExp = int(config.get('flagGovExp', 2))
        self.flagFiscalRule = int(config.get('flagFiscalRule', 0))
        
        # Simulation control
        self.max_step = config.get('simulation', {}).get('max_step', 500)
        
    def initialize(self):
        """Initialize the country model"""
        print(f"Initializing K+S model at t={self.t}")
        
        # Initialize sectors
        print("  Initializing financial sector...")
        self.financial.initialize(self.config)
        
        print("  Initializing labor market...")
        self.labor.initialize(self.config)
        
        print("  Initializing capital goods sector...")
        self.capital.initialize(self.config)
        
        print("  Initializing consumption goods sector...")
        self.consumption.initialize(self.config)
        
        # Link agents (simplified)
        self._link_agents()
        
        print(f"Initialization complete:")
        print(f"  Workers: {len(self.labor.workers)}")
        print(f"  Firm1: {len(self.capital.firms)}")
        print(f"  Firm2: {len(self.consumption.firms)}")
        print(f"  Banks: {len(self.financial.banks)}")
    
    def _link_agents(self):
        """Link agents to each other (banks to firms, etc.)"""
        # Assign banks to firms
        if self.financial.banks:
            for i, firm in enumerate(self.capital.firms):
                bank_idx = i % len(self.financial.banks)
                bank = self.financial.banks[bank_idx]
                firm.add_hook('bank', bank)
                bank.add_client(firm, 1)
            
            for i, firm in enumerate(self.consumption.firms):
                bank_idx = i % len(self.financial.banks)
                bank = self.financial.banks[bank_idx]
                firm.add_hook('bank', bank)
                bank.add_client(firm, 2)
    
    def step(self):
        """Execute one time step of the simulation"""
        self.t += 1
        
        if self.t % 10 == 0:
            print(f"\n=== Time step {self.t} ===")
        
        # Execute time step for each sector in correct order
        # Following the order from fun_KS.cpp timeStep equation
        
        # 1. Financial sector updates interest rates
        self.financial.step(self.t)
        
        # 2. Consumption goods firms form expectations and plan
        self.consumption.step(self.t)
        
        # 3. Capital goods firms do R&D and receive orders
        self.capital.step(self.t)
        
        # 4. Labor market: workers apply, firms hire/fire
        self.labor.step(self.t)
        
        # 5. Production in both sectors
        # (Already done in sector steps)
        
        # 6. Consumption goods market clearing
        self.calculate_consumption()
        self.consumption.allocate_demand(self.Cd, self.t)
        
        # 7. Capital goods market (machine orders)
        self.process_machine_orders()
        
        # 8. Firms update finances
        # (Already done in sector steps)
        
        # 9. Government collects taxes and manages budget
        self.government_step()
        
        # 10. Calculate macroeconomic aggregates
        self.calculate_macro_variables()
        
        # 11. Handle entry/exit
        # (Already done in sector steps)
        
        if self.t % 10 == 0:
            self.print_summary()
    
    def calculate_consumption(self):
        """Calculate desired consumption"""
        # Workers' net income
        W = self.labor.W
        Bon = sum(w._Bon for w in self.labor.workers)
        TaxW = sum(w._TaxW for w in self.labor.workers)
        
        # Net income
        net_income = W + self.G + Bon - TaxW + self.Div - self.TaxDiv
        
        # Desired consumption
        if self.flagCons == 0:
            # Ignore unfilled past demand
            self.Cd = net_income
        elif self.flagCons == 1:
            # Add all unfilled past demand
            self.Cd = net_income + self.Sav
        else:
            # Add limited unfilled past demand
            Crec = self.config.get('Crec', 0.5) * self.C
            self.Cd = net_income + min(self.Sav, Crec)
        
        # Update savings (unfilled consumption)
        self.Sav = max(0, self.Cd - self.consumption.Q2)
    
    def process_machine_orders(self):
        """Process machine orders from Firm2 to Firm1"""
        # Calculate total investment demand
        total_EI = sum(f._EI for f in self.consumption.firms)
        total_SI = sum(f._SI for f in self.consumption.firms)
        total_investment = total_EI + total_SI
        
        # Distribute orders to capital goods firms
        # Simplified: distribute proportionally to market share
        if self.capital.firms and total_investment > 0:
            total_share = sum(f._f1 for f in self.capital.firms)
            if total_share > 0:
                for firm1 in self.capital.firms:
                    firm1._D1 = (firm1._f1 / total_share) * total_investment
    
    def government_step(self):
        """Government fiscal operations"""
        # Collect taxes
        tax_firms1 = sum(f._Tax1 for f in self.capital.firms)
        tax_firms2 = sum(f._Tax2 for f in self.consumption.firms)
        tax_banks = sum(b._TaxB for b in self.financial.banks)
        tax_workers = sum(w._TaxW for w in self.labor.workers)
        
        if self.flagTax == 0:
            # Tax only firm profits
            self.Tax = tax_firms1 + tax_firms2 + tax_banks
        else:
            # Tax firms and workers
            self.Tax = tax_firms1 + tax_firms2 + tax_banks + tax_workers
        
        # Government expenditure
        w0min = self.config.get('w0min', 1.0)
        
        if self.flagGovExp == 0:
            # Minimum subsistence income
            self.G = self.labor.U * w0min
        elif self.flagGovExp == 1:
            # Plus fixed expenditure
            gG = self.config.get('gG', 0.0)
            self.G = self.labor.U * w0min + gG
        elif self.flagGovExp >= 2:
            # Plus unemployment benefits
            phi = self.config.get('phi', 0.5)
            self.G = self.labor.U * phi * self.labor.wAvg
        
        # Deficit
        self.Def = self.G - self.Tax
        
        # Debt
        self.Deb += self.Def
    
    def calculate_macro_variables(self):
        """Calculate macroeconomic aggregates"""
        # GDP (production approach)
        self.GDPnom = self.consumption.Q2 * self.consumption.p2avg + \
                      self.capital.Q1 * self.capital.p1avg
        
        # Real GDP (using base prices)
        self.GDPreal = self.consumption.Q2 + self.capital.Q1
        
        # Consumption
        self.C = self.consumption.D2 * self.consumption.p2avg
        self.Creal = self.consumption.D2
        
        # Dividends
        self.Div = sum(f._Div1 for f in self.capital.firms) + \
                   sum(f._Div2 for f in self.consumption.firms) + \
                   sum(b._DivB for b in self.financial.banks)
        
        # Productivity
        weighted_A = self.capital.A1 * self.capital.L1 + \
                     self.consumption.A2 * self.consumption.L2
        total_L = self.capital.L1 + self.consumption.L2
        self.A = weighted_A / total_L if total_L > 0 else 1.0
        
        # Productivity growth
        A_prev = 1.0  # Simplified - should get from history
        self.dAb = (self.A - A_prev) / A_prev if A_prev > 0 else 0.0
    
    def print_summary(self):
        """Print simulation summary"""
        print(f"  GDP (nominal): {self.GDPnom:.2f}")
        print(f"  GDP (real): {self.GDPreal:.2f}")
        print(f"  Unemployment rate: {self.labor.Ue*100:.2f}%")
        print(f"  Avg wage: {self.labor.wAvg:.2f}")
        print(f"  Avg productivity: {self.A:.2f}")
        print(f"  Consumption: {self.C:.2f}")
        print(f"  Firms Sector 1: {self.capital.F1}")
        print(f"  Firms Sector 2: {self.consumption.F2}")
        print(f"  Gov debt/GDP: {self.Deb/self.GDPnom*100 if self.GDPnom > 0 else 0:.2f}%")
    
    def run(self, steps: Optional[int] = None):
        """
        Run simulation for specified steps
        
        Args:
            steps: Number of time steps (uses max_step from config if None)
        """
        if steps is None:
            steps = self.max_step
        
        print(f"\n{'='*60}")
        print(f"Running K+S simulation for {steps} steps")
        print(f"{'='*60}")
        
        for _ in range(steps):
            try:
                self.step()
            except Exception as e:
                print(f"\nError at time step {self.t}: {e}")
                import traceback
                traceback.print_exc()
                break
        
        print(f"\n{'='*60}")
        print(f"Simulation completed at t={self.t}")
        print(f"{'='*60}")
        self.print_summary()
    
    def get_results(self) -> Dict[str, Any]:
        """
        Get simulation results
        
        Returns:
            Dictionary of key results
        """
        return {
            't': self.t,
            'GDPnom': self.GDPnom,
            'GDPreal': self.GDPreal,
            'unemployment_rate': self.labor.Ue,
            'avg_wage': self.labor.wAvg,
            'productivity': self.A,
            'consumption': self.C,
            'firms_sector1': self.capital.F1,
            'firms_sector2': self.consumption.F2,
            'govt_debt': self.Deb,
            'deficit': self.Def,
        }


def load_config(config_file: str) -> Dict[str, Any]:
    """
    Load configuration from YAML file
    
    Args:
        config_file: Path to YAML configuration file
        
    Returns:
        Configuration dictionary
    """
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    # Flatten object parameters into top-level config
    flat_config = {}
    
    if 'objects' in config:
        for obj_name, obj_data in config['objects'].items():
            if 'parameters' in obj_data:
                for param_name, param_value in obj_data['parameters'].items():
                    flat_config[param_name] = param_value
    
    # Add simulation parameters
    if 'simulation' in config:
        flat_config['simulation'] = config['simulation']
    
    return flat_config


def run_simulation(config_file: str, seed: Optional[int] = None, 
                   steps: Optional[int] = None) -> Country:
    """
    Run K+S simulation from configuration file
    
    Args:
        config_file: Path to YAML configuration file
        seed: Random seed (None for default)
        steps: Number of simulation steps (None for config default)
        
    Returns:
        Country object with simulation results
    """
    # Load configuration
    config = load_config(config_file)
    
    # Set random seed
    if seed is not None:
        set_seed(seed)
    else:
        set_seed(config.get('seed', 1))
    
    # Create and initialize country
    country = Country(config)
    country.initialize()
    
    # Run simulation
    country.run(steps)
    
    return country
