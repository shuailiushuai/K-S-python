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
from markets import LaborMarket, GoodsMarket, CapitalMarket, Government, CentralBank


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
        
        # Markets
        self.labor_market = LaborMarket(self.config)
        self.goods_market = GoodsMarket(self.config)
        self.capital_market = CapitalMarket(self.config)
        self.government = Government(self.config)
        self.central_bank = CentralBank(self.config)
        
        # Aggregate variables
        self.aggregates = {
            'GDP': [],
            'GDP_real': [],
            'CPI': [],
            'unemployment': [],
            'total_debt': [],
            'public_debt': [],
            'investment': [],
            'consumption': [],
            'inflation': [],
            'prime_rate': []
        }
        
        # Labor and other statistics
        self.labor_stats = {}
        self.savings_acc = 0.0  # Accumulated forced savings
        
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
        
        # ==================================================================
        # 1. CENTRAL BANK: Update prime rate using Taylor rule
        # ==================================================================
        inflation = self._compute_inflation()
        unemployment = self._compute_unemployment_rate()
        self.central_bank.update_prime_rate(inflation, unemployment, self.t)
        self.aggregates['prime_rate'].append(self.central_bank.prime_rate)
        self.aggregates['inflation'].append(inflation)
        
        # ==================================================================
        # 2. FINANCIAL SECTOR: Banks compute credit supply
        # ==================================================================
        for bank in self.banks:
            lambda_param = self.config.get('Financial.Lambda', 10.0)
            lambda0 = self.config.get('Financial.Lambda0', 0.0)
            tau_b = self.config.get('Financial.tauB', 0.08)
            flag_credit_rule = self.config.get('flagCreditRule', 0)
            bank.compute_credit_supply(lambda_param, lambda0, tau_b, flag_credit_rule)
        
        # Central bank computes required reserves
        self.central_bank.compute_required_reserves(self.banks)
        
        # ==================================================================
        # 3. GOVERNMENT: Compute expenditure and collect taxes
        # ==================================================================
        # Update labor statistics for government
        self._update_labor_stats()
        
        # Compute government expenditure (unemployment benefits + training)
        gov_expenditure = self.government.compute_expenditure(self.workers, self.labor_stats)
        
        # Collect taxes
        tax_data = self.government.collect_taxes(self.firms1, self.firms2, 
                                                 self.banks, self.workers)
        
        # ==================================================================
        # 4. LABOR MARKET: Workers apply for jobs
        # ==================================================================
        # Workers post applications
        total_applications = self.labor_market.worker_applications(
            self.workers, self.firms1, self.firms2, self.country_ext)
        
        # Compute job openings
        total_labor = len(self.workers)
        L2d = sum(f._L2d for f in self.firms2 if hasattr(f, '_L2d'))
        JO1 = self.labor_market.compute_job_openings_sector1(self.firms1, total_labor, L2d)
        
        # Create wage offers for sector 2
        self.labor_market.create_wage_offers_sector2(self.firms2, self.country_ext)
        
        # ==================================================================
        # 5. CAPITAL-GOOD SECTOR: R&D, innovation, and production planning
        # ==================================================================
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
        
        # ==================================================================
        # 6. CONSUMPTION-GOOD SECTOR: Demand expectations and investment
        # ==================================================================
        for firm in self.firms2:
            # Expected demand
            flag_expect = self.config.get('flagExpect', 0)
            firm.compute_expected_demand(flag_expect)
            
            # Desired production
            iota = self.config.get('Consumption.iota', 0.1)
            firm.compute_desired_production(iota)
            
            # Investment planning (expansion + substitution)
            eta = self.config.get('Consumption.eta', 20.0)
            b = self.config.get(f'Consumption.b{"Chg" if getattr(firm, "_postChg", False) else ""}', 3.0)
            firm.plan_investment(eta, b)
            
            # Compute desired labor
            if hasattr(firm, '_Q2d'):
                m2 = self.config.get('Consumption.m2', 1.0)
                firm._L2d = firm._Q2d / m2 if m2 > 0 else 0
        
        # ==================================================================
        # 7. CAPITAL MARKET: Machine orders and delivery
        # ==================================================================
        # Process machine orders from sector 2 to sector 1
        total_orders = self.capital_market.process_machine_orders(
            self.firms1, self.firms2, self.country_ext)
        
        # Compute desired production for sector 1
        for firm in self.firms1:
            m1 = self.config.get('Capital.m1', 0.1)
            if hasattr(firm, '_D1'):
                firm._L1d = firm._D1 / m1 if m1 > 0 else 0
        
        # ==================================================================
        # 8. LABOR MARKET: Hiring and firing
        # ==================================================================
        # Hire workers in sector 1
        hires1 = self.labor_market.hire_workers_sector1(self.firms1)
        
        # Hire workers in sector 2  
        hires2 = self.labor_market.hire_workers_sector2(self.firms2, self.country_ext)
        
        # Fire workers based on excess labor
        fires1 = self.labor_market.fire_workers_sector1(self.firms1)
        fires2 = self.labor_market.fire_workers_sector2(self.firms2)
        
        # Update worker tenure and skills
        self._update_worker_skills()
        
        # ==================================================================
        # 9. PRODUCTION: Both sectors produce
        # ==================================================================
        # Capital-good sector production
        m1 = self.config.get('Capital.m1', 0.1)
        for firm in self.firms1:
            firm.produce(m1)
        
        # Deliver machines
        self.capital_market.deliver_machines(self.firms1)
        
        # Consumption-good sector production
        m2 = self.config.get('Consumption.m2', 1.0)
        for firm in self.firms2:
            firm.produce(m2)
        
        # ==================================================================
        # 10. GOODS MARKET: Consumption allocation
        # ==================================================================
        # Compute consumption demand
        past_bonus = sum(getattr(w, '_Bon', 0) for w in self.workers)
        past_dividends = 0.0  # Simplified
        consumption_demand, self.savings_acc = self.goods_market.compute_consumption_demand(
            self.workers, gov_expenditure, past_bonus, past_dividends,
            tax_data['wages'], tax_data.get('dividends', 0), self.savings_acc)
        
        # Allocate consumption to firms
        total_fulfilled = self.goods_market.allocate_consumption_demand(
            self.firms2, consumption_demand)
        
        # Compute sales revenue and update inventories
        self.goods_market.compute_sales_revenue(self.firms2)
        self.goods_market.update_inventories(self.firms2)
        
        # ==================================================================
        # 11. FINANCIAL RESULTS: Profits and dividends
        # ==================================================================
        for firm in self.firms1:
            firm.compute_profits()
        
        for firm in self.firms2:
            firm.compute_profits()
        
        for bank in self.banks:
            if hasattr(bank, 'compute_profits'):
                # Get interest rates from configuration
                r_deb = self.central_bank.prime_rate + self.config.get('Financial.muDeb', 0)
                r_d = self.central_bank.prime_rate * self.config.get('Financial.muD', 1.0)
                r_bonds = self.central_bank.prime_rate + self.config.get('Financial.muBonds', 0)
                bank.compute_profits(r_deb, r_d, r_bonds)
        
        # Central bank profits
        self.central_bank.compute_profits(self.banks, self.government.public_debt)
        
        # ==================================================================
        # 12. MARKET SHARE DYNAMICS
        # ==================================================================
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
        
        # ==================================================================
        # 13. GOVERNMENT: Update public debt
        # ==================================================================
        self.government.update_public_debt(self.central_bank.prime_rate)
        
        # ==================================================================
        # 14. CENTRAL BANK: Bailout insolvent banks
        # ==================================================================
        total_bailout = self.central_bank.bailout_banks(self.banks)
        
        # ==================================================================
        # 15. ENTRY AND EXIT (Simplified for now)
        # ==================================================================
        # TODO: Implement full entry/exit logic
        
        # ==================================================================
        # 16. CAPITAL STOCK: Age vintages and scrap old machines
        # ==================================================================
        self.capital_market.age_vintages(self.firms2)
        
        # ==================================================================
        # 17. UPDATE HISTORIES: All agents
        # ==================================================================
        for worker in self.workers:
            if hasattr(worker, 'update_history'):
                worker.update_history()
        for bank in self.banks:
            if hasattr(bank, 'update_history'):
                bank.update_history()
        for firm in self.firms1:
            if hasattr(firm, 'update_history'):
                firm.update_history()
        for firm in self.firms2:
            if hasattr(firm, 'update_history'):
                firm.update_history()
        
        # ==================================================================
        # 18. AGGREGATE STATISTICS
        # ==================================================================
        self._compute_aggregates()
    
    def _update_labor_stats(self):
        """Update labor market statistics"""
        employed = sum(1 for w in self.workers if w._employed > 0)
        total_labor = len(self.workers)
        
        # Compute average wage
        wages = [w._w for w in self.workers if w._employed > 0]
        wAvg = sum(wages) / len(wages) if wages else 1.0
        
        # Unemployment benefit
        wU = self.config.get('Labor.wU', 0) if hasattr(self.config, 'get') else 1.0
        if wU == 0:  # Compute as fraction of average wage
            phi = self.config.get('Labor.phi', 0.4)
            wU = phi * wAvg
        
        self.labor_stats = {
            'Ls': total_labor,
            'L': employed,
            'wAvg': wAvg,
            'wU': wU,
            't': self.t,
            'Gtrain_prev': self.government.training_cost,
            'Tax_prev': self.government.tax_revenue,
            'GDPnom_prev': self.aggregates['GDP'][-1] if self.aggregates['GDP'] else 1.0
        }
    
    def _update_worker_skills(self):
        """Update worker tenure, skills, and unemployment duration"""
        for worker in self.workers:
            if worker._employed > 0:
                # Increment tenure
                worker._Te += 1
                worker._Tu = 0
                
                # Update skills (simplified - full logic in Worker class)
                if hasattr(worker, 'update_skills'):
                    worker.update_skills()
            else:
                # Increment unemployment duration
                worker._Tu += 1
                worker._Te = 0
                
                # Skills deterioration for unemployed
                lambda_param = self.config.get('Labor.lambda', 0.1)
                worker._sT = max(worker._sT * (1 - lambda_param), INISKILL)
                worker._sV = max(worker._sV * (1 - lambda_param), INISKILL)
                worker._s = (worker._sT + worker._sV) / 2
    
    def _compute_inflation(self) -> float:
        """Compute inflation rate based on CPI"""
        if len(self.aggregates['CPI']) < 2:
            return 0.0
        
        cpi_current = self._compute_cpi()
        cpi_prev = self.aggregates['CPI'][-1]
        
        if cpi_prev > 0:
            inflation = (cpi_current - cpi_prev) / cpi_prev
        else:
            inflation = 0.0
        
        self.aggregates['CPI'].append(cpi_current)
        return inflation
    
    def _compute_cpi(self) -> float:
        """Compute Consumer Price Index"""
        # Weighted average of prices in consumption goods sector
        total_sales = sum(f._S2 for f in self.firms2 if hasattr(f, '_S2'))
        
        if total_sales == 0:
            return 1.0
        
        weighted_price = sum(f._p2 * f._S2 for f in self.firms2 
                            if hasattr(f, '_p2') and hasattr(f, '_S2'))
        
        cpi = weighted_price / total_sales if total_sales > 0 else 1.0
        return cpi
    
    def _compute_unemployment_rate(self) -> float:
        """Compute unemployment rate"""
        if not self.workers:
            return 0.0
        
        unemployed = sum(1 for w in self.workers if w._employed == 0)
        return unemployed / len(self.workers)
    
    def _compute_aggregates(self):
        """Compute aggregate macroeconomic variables"""
        # GDP (nominal) - sum of consumption goods sales
        gdp = sum(f._S2 for f in self.firms2 if hasattr(f, '_S2'))
        self.aggregates['GDP'].append(gdp)
        
        # Real GDP (deflated by CPI)
        cpi = self.aggregates['CPI'][-1] if self.aggregates['CPI'] else 1.0
        gdp_real = gdp / cpi if cpi > 0 else gdp
        self.aggregates['GDP_real'].append(gdp_real)
        
        # Unemployment rate
        unemployment = self._compute_unemployment_rate()
        self.aggregates['unemployment'].append(unemployment)
        
        # Total private debt
        total_debt = (sum(f._Deb1 for f in self.firms1 if hasattr(f, '_Deb1')) + 
                     sum(f._Deb2 for f in self.firms2 if hasattr(f, '_Deb2')))
        self.aggregates['total_debt'].append(total_debt)
        
        # Public debt
        self.aggregates['public_debt'].append(self.government.public_debt)
        
        # Investment (expansion + substitution)
        investment = sum((f._EI if hasattr(f, '_EI') else 0) + 
                        (f._SI if hasattr(f, '_SI') else 0) 
                        for f in self.firms2)
        self.aggregates['investment'].append(investment)
        
        # Consumption (total sales)
        consumption = sum(f._D2 for f in self.firms2 if hasattr(f, '_D2'))
        self.aggregates['consumption'].append(consumption)
    
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
