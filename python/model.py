"""
Main K+S Model Class
Orchestrates the simulation, manages time-stepping and aggregation
"""

import yaml
from typing import Dict, Any, List, Optional
import numpy as np
import math

from agents.worker import Worker
from agents.bank import Bank
from agents.firm1 import Firm1
from agents.firm2 import Firm2
from utils.core_utils import init_random_engine, get_random_engine, INIPROD, INIWAGE, INISKILL
from utils.data_structures import CountryExtension
from utils.initialization import (compute_initial_conditions, initialize_firm1, 
                                  initialize_firm2, initialize_worker, initialize_bank)
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
        
        # Compute initial equilibrium conditions
        print("  Computing initial equilibrium conditions...")
        init_cond = compute_initial_conditions(self.config)
        
        # Initialize banks
        B = self.config.get('Financial.B', 1)
        print(f"  Creating {B} banks...")
        for i in range(B):
            bank = Bank(i + 1, self.config)
            initialize_bank(bank, i + 1, B, self.config, init_cond)
            self.banks.append(bank)
            self.country_ext.bank_ptr.append(bank)
        
        # Initialize capital-good firms (Firm1)
        F10 = self.config.get('Capital.F10', 50)
        print(f"  Creating {F10} capital-good firms...")
        for i in range(F10):
            firm = Firm1(i + 1, self.config)
            # Assign bank
            bank_idx = get_random_engine().uniform_int(0, B - 1)
            firm.bank = self.banks[bank_idx]
            firm._bank1 = bank_idx + 1
            # Initialize with proper values
            initialize_firm1(firm, i + 1, F10, self.config, init_cond, new_industry=True)
            self.firms1.append(firm)
        
        # Initialize consumption-good firms (Firm2)
        F20 = self.config.get('Consumption.F20', 200)
        print(f"  Creating {F20} consumption-good firms...")
        for i in range(F20):
            firm = Firm2(i + 1, self.config)
            self.country_ext.firm2_ptr.append(firm)
            self.country_ext.firm2_map[firm.id] = firm
            # Assign bank
            bank_idx = get_random_engine().uniform_int(0, B - 1)
            firm.bank = self.banks[bank_idx]
            firm._bank2 = bank_idx + 1
            # Assign supplier
            supplier_idx = get_random_engine().uniform_int(0, F10 - 1)
            firm.supplier = self.firms1[supplier_idx]
            # Initialize with proper values
            initialize_firm2(firm, i + 1, F20, self.config, init_cond, new_industry=True)
            self.firms2.append(firm)
        
        # Initialize workers
        Ls0 = self.config.get('Labor.Ls0', 1000)
        Lscale = self.config.get('Labor.Lscale', 1)
        n_worker_objects = math.ceil(Ls0 / Lscale)
        print(f"  Creating {n_worker_objects} worker objects (representing {Ls0} workers with Lscale={Lscale})...")
        for i in range(n_worker_objects):
            worker = Worker(i + 1, self.config)
            initialize_worker(worker, i + 1, self.config, init_cond)
            self.workers.append(worker)
        
        # Allocate initial employment to firms based on their labor demand
        print("  Allocating initial employment...")
        self._initialize_employment()
        
        # Set up initial bank assets based on firm loans
        print("  Setting up initial bank balance sheets...")
        self._initialize_bank_assets()
        
        # Initialize aggregate tracking
        print("  Initializing aggregate statistics...")
        initial_cpi = init_cond['p20']
        self.aggregates['CPI'].append(initial_cpi)
        
        print(f"Initialized: {len(self.workers)} workers, {len(self.firms1)} Firm1, "
              f"{len(self.firms2)} Firm2, {len(self.banks)} banks")
        print(f"  Initial conditions: GDP≈${init_cond['D10']*init_cond['p10'] + init_cond['D20']*init_cond['p20']:.0f}, "
              f"Wage=${init_cond['w_avg']:.2f}, CPI=${initial_cpi:.2f}")
    
    def _initialize_bank_assets(self):
        """
        Set up initial bank balance sheets based on firm loans
        Banks need assets (loans) = liabilities (deposits) + equity
        """
        # Aggregate firm debt and deposits across all banks
        for bank in self.banks:
            total_loans = 0.0
            total_deposits = 0.0
            
            # Sum loans and deposits from Firm1
            for firm in self.firms1:
                if firm.bank == bank:
                    total_loans += firm._Deb1
                    total_deposits += firm._NW1
            
            # Sum loans and deposits from Firm2
            for firm in self.firms2:
                if firm.bank == bank:
                    total_loans += firm._Deb2
                    total_deposits += firm._NW2
            
            # Set bank balance sheet
            bank._LoanB = total_loans
            bank._DepB = total_deposits
            
            # Compute required reserves (e.g., 10% of deposits)
            reserve_ratio = self.config.get('Financial.rho', 0.1)
            bank._ResB = reserve_ratio * bank._DepB
            
            # Adjust equity to balance: Assets = Liabilities + Equity
            # Assets = Loans + Reserves
            # Liabilities = Deposits
            # Equity = Assets - Liabilities
            bank._EqB = bank._LoanB + bank._ResB - bank._DepB
    
    def _initialize_employment(self):
        """
        Allocate initial workers to firms based on labor demand
        Simulates an economy that's already running
        """
        unemployed_workers = list(self.workers)
        get_random_engine().shuffle(unemployed_workers)
        
        Lscale = self.config.get('Labor.Lscale', 1)
        
        # Calculate total labor demand (in worker objects)
        total_L1d = sum(getattr(f, '_L1d', 0) for f in self.firms1) / Lscale
        total_L2d = sum(getattr(f, '_L2d', 0) for f in self.firms2) / Lscale
        total_demand = total_L1d + total_L2d
        
        # If demand exceeds supply, scale down proportionally
        if total_demand > len(self.workers):
            scale_factor = len(self.workers) / total_demand
            print(f"    Scaling labor demands by {scale_factor:.2f} to match supply")
        else:
            scale_factor = 1.0
        
        worker_idx = 0
        
        # Allocate workers to Firm1 (capital-good sector)
        for firm in self.firms1:
            if not hasattr(firm, '_L1d'):
                continue
            
            # L1d is in units of actual workers, divide by Lscale to get worker objects
            workers_needed = int((firm._L1d / Lscale) * scale_factor)
            for _ in range(workers_needed):
                if worker_idx >= len(unemployed_workers):
                    break
                
                worker = unemployed_workers[worker_idx]
                worker._employed = 1  # Employed in sector 1
                worker._w = INIWAGE  # Initial wage
                worker._Te = 0  # Initial tenure
                firm.workers.append(worker)
                worker_idx += 1
        
        # Allocate workers to Firm2 (consumption-good sector)
        for firm in self.firms2:
            if not hasattr(firm, '_L2d'):
                continue
            
            # L2d is in units of actual workers, divide by Lscale to get worker objects
            workers_needed = int((firm._L2d / Lscale) * scale_factor)
            for _ in range(workers_needed):
                if worker_idx >= len(unemployed_workers):
                    break
                
                worker = unemployed_workers[worker_idx]
                worker._employed = 2  # Employed in sector 2
                worker._w = INIWAGE  # Initial wage
                worker._Te = 0  # Initial tenure
                firm.workers.append(worker)
                worker_idx += 1
        
        employed_count = worker_idx
        unemployment_rate = 1.0 - (employed_count / len(self.workers))
        print(f"    Employed: {employed_count}/{len(self.workers)} ({unemployment_rate:.1%} unemployment)")
    
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
        # 3. CONSUMPTION-GOOD SECTOR: Demand expectations, production planning, and labor demand
        # ==================================================================
        # IMPORTANT: Must calculate L2d BEFORE worker applications!
        m2 = self.config.get('Consumption.m2', 1.0)
        for firm in self.firms2:
            # Expected demand
            flag_expect = self.config.get('flagExpect', 0)
            firm.compute_expected_demand(flag_expect)
            
            # Desired production
            iota = self.config.get('Consumption.iota', 0.1)
            firm.compute_desired_production(iota)
            
            # Planned production (considering financing constraints)
            # This sets Q2 (planned) from Q2d (desired)
            firm.plan_production(m2)
            
            # Compute desired capital stock
            u = self.config.get('Consumption.u', 0.75)  # Target utilization
            firm.compute_desired_capital(m2, u)
            
            # Investment planning (expansion + substitution)
            eta = self.config.get('Consumption.eta', 20.0)
            b = self.config.get(f'Consumption.b{"Chg" if getattr(firm, "_postChg", False) else ""}', 3.0)
            firm.plan_investment(eta, b)
            
            # Compute labor demand based on PLANNED production Q2 (not desired Q2d)
            if hasattr(firm, '_Q2') and hasattr(firm, '_A2'):
                import math
                firm._L2d = math.ceil(firm._Q2 / firm._A2) if firm._A2 > 0 else 0
        
        # ==================================================================
        # 4. CAPITAL-GOOD SECTOR: R&D, innovation, and production planning
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
        # 5. CAPITAL MARKET: Machine orders and delivery
        # ==================================================================
        # Process machine orders from sector 2 to sector 1
        total_orders = self.capital_market.process_machine_orders(
            self.firms1, self.firms2, self.country_ext)
        
        # Compute desired production for sector 1 based on orders
        m1 = self.config.get('Capital.m1', 0.1)
        for firm in self.firms1:
            # Compute demand from orders
            firm.compute_demand()
            
            # Plan production considering financing constraints
            # This sets Q1 (planned) from D1 (orders)
            firm.plan_production()
            
            # Compute labor demand: L1d = R&D workers + production workers
            # Production workers = Q1 / (Btau * m1)
            if hasattr(firm, '_Q1') and hasattr(firm, '_Btau'):
                prod_workers = math.ceil(firm._Q1 / (firm._Btau * m1)) if firm._Btau > 0 and m1 > 0 else 0
                rd_workers = getattr(firm, '_L1rd', 0)
                firm._L1d = rd_workers + prod_workers
        
        # ==================================================================
        # 6. LABOR MARKET: Workers apply for jobs, firms post openings
        # ==================================================================
        # Workers post applications
        total_applications = self.labor_market.worker_applications(
            self.workers, self.firms1, self.firms2, self.country_ext)
        
        # Compute job openings (NOW we have L2d and L1d calculated!)
        total_labor = len(self.workers)
        L2d = sum(f._L2d for f in self.firms2 if hasattr(f, '_L2d'))
        JO1 = self.labor_market.compute_job_openings_sector1(self.firms1, total_labor, L2d)
        
        # Create wage offers for sector 2
        self.labor_market.create_wage_offers_sector2(self.firms2, self.country_ext)
        
        # ==================================================================
        # 7. LABOR MARKET: Hiring and firing
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
        # 8. PRODUCTION: Both sectors produce
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
        # 9. GOVERNMENT EXPENDITURE: Calculate G based on finalized employment
        # ==================================================================
        # Update labor statistics (now employment is finalized after hiring/firing)
        self._update_labor_stats()
        
        # Compute government expenditure (unemployment benefits + training)
        # This matches C++ step 19: NEW_VS( v[19], THIS, "G" )
        gov_expenditure = self.government.compute_expenditure(self.workers, self.labor_stats)
        
        # ==================================================================
        # 11. GOODS MARKET: Consumption allocation
        # ==================================================================
        # Compute consumption demand
        # Note: Wage taxes are computed on-the-fly from current wages
        # (in C++, TaxW is computed lazily when Cd is accessed)
        past_bonus = sum(getattr(w, '_Bon', 0) for w in self.workers)
        past_dividends = 0.0  # Simplified
        
        # Compute wage taxes on-the-fly (like C++ lazy evaluation)
        flag_tax = self.config.get('Country.flagTax', 1)
        tr = self.config.get('Country.tr', 0.1)
        wage_tax = 0.0
        if flag_tax >= 1:
            wage_tax = sum((w._w + getattr(w, '_Bon', 0)) * tr 
                          for w in self.workers if w._employed > 0)
        
        consumption_demand, self.savings_acc = self.goods_market.compute_consumption_demand(
            self.workers, gov_expenditure, past_bonus, past_dividends,
            wage_tax, 0.0, self.savings_acc)  # dividend_tax=0 for now
        
        # Allocate consumption to firms
        total_fulfilled = self.goods_market.allocate_consumption_demand(
            self.firms2, consumption_demand)
        
        # Compute sales revenue and update inventories
        self.goods_market.compute_sales_revenue(self.firms2)
        self.goods_market.update_inventories(self.firms2)
        
        # ==================================================================
        # 12. FINANCIAL RESULTS: Profits and dividends
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
        # 13. TAX COLLECTION: Collect taxes on profits
        # ==================================================================
        # This matches C++ steps 27-29: Tax1, Tax2, TaxB
        tax_data = self.government.collect_taxes(self.firms1, self.firms2, 
                                                 self.banks, self.workers)
        
        # ==================================================================
        # 14. MARKET SHARE DYNAMICS
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
        
        # Rescale market shares to sum to 1.0 (equivalent to f2rescale in C++)
        self._rescale_market_shares()
        
        # ==================================================================
        # 15. GOVERNMENT: Update public debt
        # ==================================================================
        self.government.update_public_debt(self.central_bank.prime_rate)
        
        # ==================================================================
        # 16. CENTRAL BANK: Bailout insolvent banks
        # ==================================================================
        total_bailout = self.central_bank.bailout_banks(self.banks)
        
        # ==================================================================
        # 17. ENTRY AND EXIT (Simplified for now)
        # ==================================================================
        # TODO: Implement full entry/exit logic
        
        # ==================================================================
        # 18. CAPITAL STOCK: Age vintages and scrap old machines
        # ==================================================================
        self.capital_market.age_vintages(self.firms2)
        
        # ==================================================================
        # 19. UPDATE HISTORIES: All agents
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
        # 20. AGGREGATE STATISTICS
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
    
    def _rescale_market_shares(self):
        """
        Rescale market shares to ensure they sum to 1.0
        Equivalent to f2rescale equation in C++ (fun_KS_consumption.h)
        """
        # Sector 1 (capital goods)
        if self.firms1:
            total_f1 = sum(f._f1 for f in self.firms1 if hasattr(f, '_f1'))
            if abs(total_f1 - 1.0) > 0.001:  # Ignore rounding errors
                if total_f1 > 0:
                    for firm in self.firms1:
                        if hasattr(firm, '_f1'):
                            firm._f1 = firm._f1 / total_f1
                else:
                    # Equal shares if no production
                    fair_share = 1.0 / len(self.firms1)
                    for firm in self.firms1:
                        firm._f1 = fair_share
        
        # Sector 2 (consumption goods)
        if self.firms2:
            total_f2 = sum(f._f2 for f in self.firms2 if hasattr(f, '_f2'))
            if abs(total_f2 - 1.0) > 0.001:  # Ignore rounding errors
                if total_f2 > 0:
                    for firm in self.firms2:
                        if hasattr(firm, '_f2'):
                            firm._f2 = firm._f2 / total_f2
                else:
                    # Equal shares if no production
                    fair_share = 1.0 / len(self.firms2)
                    for firm in self.firms2:
                        firm._f2 = fair_share
    
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
