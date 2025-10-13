"""
Main K+S Model Class
Orchestrates the simulation, manages time-stepping and aggregation
"""

import yaml
from typing import Dict, Any, List, Optional
import numpy as np

from agents.worker import Worker
from agents.bank import Bank
from agents.firm1 import Firm1
from agents.firm2 import Firm2
from utils.core_utils import init_random_engine, get_random_engine, INIPROD, INIWAGE, INISKILL
from utils.data_structures import CountryExtension


class KSModel:
    """
    Main K+S Agent-Based Model
    Manages initialization, time-stepping, and results collection
    """
    
    def __init__(self, config_file: str, seed: int = 1):
        """
        Initialize the K+S model
        
        Args:
            config_file: Path to YAML configuration file
            seed: Random seed for reproducibility
        """
        # Load configuration
        with open(config_file, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize random engine with seed
        init_random_engine(seed)
        self.seed = seed
        
        # Time tracking
        self.t = 0
        self.T_max = 0
        
        # Agents
        self.workers: List[Worker] = []
        self.banks: List[Bank] = []
        self.firms1: List[Firm1] = []
        self.firms2: List[Firm2] = []
        
        # Country-level extensions
        self.country_ext = CountryExtension()
        
        # Aggregate variables
        self.aggregates = {
            'GDP': [],
            'GDP_real': [],
            'CPI': [],
            'unemployment': [],
            'total_debt': [],
            'public_debt': [],
            'investment': [],
            'consumption': []
        }
        
        # Initialize the model
        self._initialize()
    
    def _initialize(self):
        """Initialize all agents and set up initial conditions"""
        print("Initializing K+S model...")
        
        # Initialize banks
        B = self.config.get('Financial.B', 1)
        for i in range(B):
            bank = Bank(i + 1, self.config)
            self.banks.append(bank)
            self.country_ext.bank_ptr.append(bank)
        
        # Initialize capital-good firms (Firm1)
        F10 = self.config.get('Capital.F10', 50)
        for i in range(F10):
            firm = Firm1(i + 1, self.config)
            self.firms1.append(firm)
            # Assign bank
            bank_idx = get_random_engine().uniform_int(0, B - 1)
            firm.bank = self.banks[bank_idx]
            firm._bank1 = bank_idx + 1
        
        # Initialize consumption-good firms (Firm2)
        F20 = self.config.get('Consumption.F20', 200)
        for i in range(F20):
            firm = Firm2(i + 1, self.config)
            self.firms2.append(firm)
            self.country_ext.firm2_ptr.append(firm)
            self.country_ext.firm2_map[firm.id] = firm
            # Assign bank
            bank_idx = get_random_engine().uniform_int(0, B - 1)
            firm.bank = self.banks[bank_idx]
            firm._bank2 = bank_idx + 1
            # Assign supplier
            supplier_idx = get_random_engine().uniform_int(0, F10 - 1)
            firm.supplier = self.firms1[supplier_idx]
        
        # Initialize workers
        Ls0 = self.config.get('Labor.Ls0', 1000)
        for i in range(Ls0):
            worker = Worker(i + 1, self.config)
            self.workers.append(worker)
        
        print(f"Initialized: {len(self.workers)} workers, {len(self.firms1)} Firm1, "
              f"{len(self.firms2)} Firm2, {len(self.banks)} banks")
    
    def time_step(self):
        """
        Execute one time step of the model
        Follows the sequence from fun_KS.cpp timeStep equation
        """
        self.t += 1
        
        # 1. Central bank updates prime rate
        # TODO: Implement Taylor rule
        
        # 2. Financial sector updates (banks compute credit supply)
        for bank in self.banks:
            lambda_param = self.config.get('Financial.Lambda', 10.0)
            lambda0 = self.config.get('Financial.Lambda0', 0.0)
            tau_b = self.config.get('Financial.tauB', 0.08)
            flag_credit_rule = self.config.get('flagCreditRule', 0)
            bank.compute_credit_supply(lambda_param, lambda0, tau_b, flag_credit_rule)
        
        # 3. Labor market - workers search for jobs
        # TODO: Implement job search and matching
        
        # 4. Capital-good sector (Firm1)
        for firm in self.firms1:
            # R&D investment
            nu = self.config.get('Capital.nu', 0.04)
            firm.compute_rd_investment(nu)
            
            # Innovation
            alpha1 = self.config.get('Capital.alpha1', 3.0)
            beta1 = self.config.get('Capital.beta1', 3.0)
            xi = self.config.get('Capital.xi', 0.5)
            x1_inf = self.config.get('Capital.x1inf', -0.15)
            x1_sup = self.config.get('Capital.x1sup', 0.15)
            zeta1 = self.config.get('Capital.zeta1', 0.3)
            firm.innovate(alpha1, beta1, xi, x1_inf, x1_sup, zeta1)
            
            # Imitation
            alpha2 = self.config.get('Capital.alpha2', 2.0)
            beta2 = self.config.get('Capital.beta2', 4.0)
            zeta2 = self.config.get('Capital.zeta2', 0.3)
            firm.imitate(alpha2, beta2, xi, self.firms1, zeta2)
            
            # Pricing
            mu1 = self.config.get('Capital.mu1', 0.08)
            firm.compute_price(mu1)
        
        # 5. Consumption-good sector (Firm2)
        for firm in self.firms2:
            # Expected demand
            flag_expect = self.config.get('flagExpect', 0)
            firm.compute_expected_demand(flag_expect)
            
            # Desired production
            iota = self.config.get('Consumption.iota', 0.1)
            firm.compute_desired_production(iota)
            
            # Investment planning
            eta = self.config.get('Consumption.eta', 20.0)
            b = self.config.get(f'Consumption.b{"Chg" if firm._postChg else ""}', 3.0)
            firm.plan_investment(eta, b)
        
        # 6. Machine orders and delivery
        # TODO: Implement machine ordering
        
        # 7. Production in both sectors
        m1 = self.config.get('Capital.m1', 0.1)
        for firm in self.firms1:
            firm.produce(m1)
        
        m2 = self.config.get('Consumption.m2', 1.0)
        for firm in self.firms2:
            firm.produce(m2)
        
        # 8. Goods market - consumption
        # TODO: Implement consumption demand allocation
        
        # 9. Financial results
        for firm in self.firms1:
            firm.compute_profits()
        
        for firm in self.firms2:
            firm.compute_profits()
        
        # 10. Market share updates
        n1 = self.config.get('Capital.n1', 4)
        for firm in self.firms1:
            firm.update_market_share(self.firms1, n1)
        
        chi = self.config.get('Consumption.chi', 1.0)
        for firm in self.firms2:
            omega1 = self.config.get('Consumption.omega1', 1.0)
            omega2 = self.config.get('Consumption.omega2', 1.0)
            omega3 = self.config.get('Consumption.omega3', 0.0)
            firm.compute_competitiveness(omega1, omega2, omega3)
            firm.update_market_share(self.firms2, chi)
        
        # 11. Entry and exit
        # TODO: Implement entry/exit logic
        
        # 12. Update histories
        for worker in self.workers:
            worker.update_history()
        for bank in self.banks:
            bank.update_history()
        for firm in self.firms1:
            firm.update_history()
        for firm in self.firms2:
            firm.update_history()
        
        # 13. Compute aggregates
        self._compute_aggregates()
    
    def _compute_aggregates(self):
        """Compute aggregate macroeconomic variables"""
        # GDP (nominal)
        gdp = sum(f._S2 * f._p2 for f in self.firms2)
        self.aggregates['GDP'].append(gdp)
        
        # Unemployment rate
        employed = sum(1 for w in self.workers if w.is_employed())
        unemployment = 1.0 - employed / len(self.workers) if self.workers else 0.0
        self.aggregates['unemployment'].append(unemployment)
        
        # Total debt
        total_debt = sum(f._Deb1 for f in self.firms1) + sum(f._Deb2 for f in self.firms2)
        self.aggregates['total_debt'].append(total_debt)
        
        # Investment
        investment = sum(f._EI + f._SI for f in self.firms2)
        self.aggregates['investment'].append(investment)
    
    def run(self, periods: int):
        """
        Run the simulation for specified number of periods
        
        Args:
            periods: Number of time periods to simulate
        """
        self.T_max = periods
        
        print(f"Running K+S model for {periods} periods...")
        for t in range(periods):
            if (t + 1) % 10 == 0:
                print(f"  Period {t + 1}/{periods}")
            self.time_step()
        
        print("Simulation complete.")
        return self.aggregates
    
    def get_results(self) -> Dict[str, List[float]]:
        """Return aggregate results"""
        return self.aggregates
    
    def export_results(self, filename: str):
        """Export results to CSV"""
        import pandas as pd
        df = pd.DataFrame(self.aggregates)
        df.to_csv(filename, index=False)
        print(f"Results exported to {filename}")


if __name__ == '__main__':
    # Example usage
    model = KSModel('config/model_config.yaml', seed=1)
    results = model.run(periods=100)
    
    # Print some results
    print("\nFinal period aggregates:")
    print(f"  GDP: {results['GDP'][-1]:.2f}")
    print(f"  Unemployment: {results['unemployment'][-1]:.2%}")
    print(f"  Total Debt: {results['total_debt'][-1]:.2f}")
