"""
K+S Agent-Based Model - Python Implementation

Main model class that orchestrates the simulation.
"""

import numpy as np
from typing import Dict, List, Optional, Any
import json

from agents.firm1 import Firm1
from agents.firm2 import Firm2
from agents.worker import Worker
from agents.bank import Bank
from agents.government import Government, CentralBank
from markets.labor_market import LaborMarket
from markets.goods_market import GoodsMarket
from markets.capital_market import CapitalMarket
from markets.financial_market import FinancialMarket
from utils.parameters import Parameters
from utils.statistics import Statistics
from utils.random_utils import set_seed


class KSModel:
    """
    Main K+S (Keynes+Schumpeter) Agent-Based Model
    
    This class orchestrates the entire simulation, managing all agents,
    markets, and the flow of time steps according to the model's logic.
    """
    
    def __init__(self, config_file: Optional[str] = None, seed: Optional[int] = None):
        """
        Initialize the K+S model
        
        Args:
            config_file: Path to JSON configuration file
            seed: Random seed for reproducibility
        """
        # Load parameters
        self.params = Parameters(config_file)
        
        # Set random seed
        if seed is not None:
            set_seed(seed)
        else:
            set_seed(self.params.get('seed', 42))
        
        # Time tracking
        self.t = 0
        self.max_time = 0
        
        # Initialize containers for agents
        self.firms1: List[Firm1] = []
        self.firms2: List[Firm2] = []
        self.workers: List[Worker] = []
        self.banks: List[Bank] = []
        
        # Initialize government and central bank
        self.government = None
        self.central_bank = None
        
        # Initialize markets
        self.labor_market = None
        self.goods_market = None
        self.capital_market = None
        self.financial_market = None
        
        # Statistics collection
        self.stats = Statistics()
        
        # Entry/exit tracking
        self.entry_firms1 = 0
        self.exit_firms1 = 0
        self.entry_firms2 = 0
        self.exit_firms2 = 0
        
        # Initialize the model
        self._initialize()
    
    def _initialize(self):
        """Initialize all model components"""
        print("Initializing K+S Model...")
        
        # Create government and central bank
        self.government = Government(self.params)
        self.central_bank = CentralBank(self.params)
        
        # Create banks
        self._initialize_banks()
        
        # Create workers
        self._initialize_workers()
        
        # Create firms in capital-good sector (Firm1)
        self._initialize_firms1()
        
        # Create firms in consumption-good sector (Firm2)
        self._initialize_firms2()
        
        # Initialize markets
        self.labor_market = LaborMarket(self.params, self.workers, 
                                       self.firms1, self.firms2)
        self.goods_market = GoodsMarket(self.params, self.workers, self.firms2)
        self.capital_market = CapitalMarket(self.params, self.firms1, self.firms2)
        self.financial_market = FinancialMarket(self.params, self.banks, 
                                               self.firms1, self.firms2)
        
        # Establish initial relationships (firm-bank, firm-supplier, etc.)
        self._establish_relationships()
        
        # Assign initial employment (workers to firms) for full employment start
        self._assign_initial_employment()
        
        print(f"Model initialized: {len(self.firms1)} capital firms, "
              f"{len(self.firms2)} consumption firms, "
              f"{len(self.workers)} workers, {len(self.banks)} banks")
    
    def _initialize_banks(self):
        """Create initial bank population"""
        B = self.params.get('B', 10)  # Number of banks
        EqB0 = self.params.get('EqB0', 0.1)  # Initial equity multiple
        alphaB = self.params.get('alphaB', 2.0)  # Pareto shape for size distribution
        
        for i in range(B):
            bank = Bank(
                bank_id=i,
                params=self.params,
                initial_equity=EqB0  # Will be adjusted after firms are created
            )
            self.banks.append(bank)
    
    def _initialize_workers(self):
        """Create initial worker population"""
        Ls0 = self.params.get('Ls0', 1000)  # Initial labor force
        Lscale = self.params.get('Lscale', 1)  # Workers per object
        Tr = self.params.get('Tr', 0)  # Retirement age (0 = no retirement)
        Tc = self.params.get('Tc', 1)  # Contract term
        wU = self.params.get('w0min', 1.0)  # Initial reservation wage
        
        n_workers = int(Ls0 / Lscale)
        
        for i in range(n_workers):
            # Random initial age if retirement is enabled
            age = np.random.randint(1, Tr + 1) if Tr > 0 else 1
            
            worker = Worker(
                worker_id=i,
                params=self.params,
                age=age,
                reservation_wage=wU,
                contract_term=Tc
            )
            self.workers.append(worker)
    
    def _initialize_firms1(self):
        """Create initial population of capital-good firms (Firm1)"""
        F10 = self.params.get('F10', 20)  # Initial number of firms
        NW10 = self.params.get('NW10', 100)  # Average initial net worth
        
        # Initial values for technology (from C++ INIPROD, etc.)
        INIPROD = 1.0
        mu1 = self.params.get('mu1', 0.04)
        m1 = self.params.get('m1', 1.0)
        m2 = self.params.get('m2', 1.0)
        b = self.params.get('b', 20)  # Payback period
        INIWAGE = 1.0
        
        # Calculate initial labor productivity for sector 1
        # From C++ logic: Btau0 = (1 + mu1) * INIPROD / (m1 * m2 * b)
        Btau0 = (1 + mu1) * INIPROD / (m1 * m2 * b)
        c10 = INIWAGE / (Btau0 * m1)  # Initial unit cost
        p10 = (1 + mu1) * c10  # Initial price
        
        # Calculate initial demand for sector 1 (needed for sales history)
        Ls0 = self.params.get('Ls0', 1000)
        eta = self.params.get('eta', 20)
        K0 = Ls0 * INIWAGE / ((1 + self.params.get('mu20', 0.35)) * (INIWAGE / INIPROD))
        D10 = K0 / (m2 * eta)  # Initial demand for machines
        
        # Store critical initial values in params (C++ lines 516-518)
        self.params.set('Btau0', Btau0)
        self.params.set('pK0', p10)  # Initial capital goods price
        
        for i in range(F10):
            firm = Firm1(
                firm_id=i,
                params=self.params,
                initial_net_worth=NW10 * (0.5 + np.random.random())  # Random variation
            )
            
            # Initialize technology and pricing
            firm.machine_productivity = INIPROD  # A_tau
            firm.labor_productivity_output = Btau0  # B_tau
            firm.unit_cost = c10
            firm.price = p10
            firm.market_share = 1.0 / F10  # Fair share
            firm.competitiveness = 1.0
            
            # Initialize sales history for R&D calculations
            # Use initial demand D10 distributed among firms
            # This will be retrieved later at line 238
            initial_sales = D10 / F10  # Fair share of initial demand
            initial_revenue = initial_sales * p10
            firm.revenue = initial_revenue
            # Also populate sales_history so R&D uses correct past sales
            firm.sales_history = [initial_sales]  # Past sales (units, not $)
            
            self.firms1.append(firm)
    
    def _initialize_firms2(self):
        """Create initial population of consumption-good firms (Firm2)"""
        F20 = self.params.get('F20', 100)  # Initial number of firms
        NW20 = self.params.get('NW20', 100)  # Average initial net worth
        
        # Get parameters for initial setup (matching C++ fun_KS_country.h)
        Ls0 = self.params.get('Ls0', 1000)
        m1 = self.params.get('m1', 1.0)
        m2 = self.params.get('m2', 1.0)
        mu1 = self.params.get('mu1', 0.04)
        mu20 = self.params.get('mu20', 0.35)
        eta = self.params.get('eta', 20)  # Machine lifetime
        iota = self.params.get('iota', 0.1)  # Inventory propensity
        u = self.params.get('u', 0.75)  # Planned capacity utilization
        phi = self.params.get('phi', 0.5)  # Unemployment benefit rate
        nu = self.params.get('nu', 0.04)  # R&D intensity
        flagTax = self.params.get('flagTax', 1)
        tr = self.params.get('tr', 0.1) if flagTax > 0 else 0.0
        
        INIWAGE = 1.0
        INIPROD = 1.0  # Initial productivity in sector 2
        
        # Get Btau0 from params (set during Firm1 initialization)
        Btau0 = self.params.get('Btau0', 0.052)
        
        # Calculate initial values matching C++ logic (lines 479-482)
        c10 = INIWAGE / (Btau0 * m1)  # Initial cost in sector 1
        c20 = INIWAGE / INIPROD  # Initial cost in sector 2
        p10 = (1 + mu1) * c10  # Initial price sector 1
        p20 = (1 + mu20) * c20  # Initial price sector 2
        trW = tr  # Tax rate on wages
        
        # Store initial consumption price (C++ line 517)
        self.params.set('pC0', p20)
        
        K0_total = Ls0 * INIWAGE / p20  # Full employment capital required
        D10 = K0_total / (m2 * eta)  # Initial demand for sector 1
        RD0 = nu * D10 * p10  # Initial R&D expense
        
        # Initial demand for sector 2 (correct formula from C++)
        D20_total = ((D10 * c10 + RD0) * (1 - phi - trW) + Ls0 * INIWAGE * phi) / \
                    (mu20 + phi + trW) * c20
        D20 = D20_total / F20  # Per firm
        
        # Initial labor demands
        Ld10 = RD0 / INIWAGE + D10 / (Btau0 * m1)
        Ld20 = D20_total / INIPROD
        
        # Store initial labor demands for use in employment assignment
        self.params.set('Ld10', Ld10)  # Total labor demand for Firm1 sector
        self.params.set('Ld20', Ld20)  # Total labor demand for Firm2 sector
        self.params.set('D10', D10)    # Initial production demand for Firm1 sector
        
        # Calculate capital per firm to meet demand
        K0_per_firm = K0_total / F20
        
        for i in range(F20):
            firm = Firm2(
                firm_id=i,
                params=self.params,
                initial_net_worth=NW20 * (0.5 + np.random.random())  # Random variation
            )
            
            # Initialize capital stock with vintages (matches C++ add_vintage logic)
            n_machines = max(1, int(np.ceil(K0_per_firm / m2)))
            firm.capital_stock = n_machines * m2
            firm.capital_desired = firm.capital_stock
            
            # Create initial mix of vintages (old to new)
            # Distribute machines across vintages of different ages
            machines_per_vintage = max(1, int(np.ceil(n_machines / eta)))
            age = eta
            remaining_machines = n_machines
            
            from agents.vintage import Vintage
            while remaining_machines > 0 and age > 0:
                n_vint = min(machines_per_vintage, remaining_machines)
                if n_vint > 0:
                    # Select a random supplier (will be properly assigned later)
                    supplier_id = np.random.randint(0, len(self.firms1)) if self.firms1 else 0
                    birth_time = 1 - age  # Vintage age (negative for initial vintages)
                    
                    # Create vintage with proper parameter order
                    vintage_id = birth_time * 10000 + supplier_id
                    vintage = Vintage(
                        vintage_id=vintage_id,
                        birth_time=birth_time,
                        supplier_id=supplier_id,
                        productivity=INIPROD,  # Initial productivity
                        machines=n_vint,
                        price=p20 / m2  # Price per machine
                    )
                    firm.vintages.append(vintage)
                    remaining_machines -= n_vint
                age -= 1
            
            # Initialize production variables
            # Output and demand should be consistent with capital stock
            # Labor productivity = INIPROD, so output capacity = capital_stock
            initial_output = firm.capital_stock  # With INIPROD=1.0
            
            firm.output_desired = initial_output
            firm.demand_expected = initial_output  # Expect to sell what can be produced
            firm.output_planned = initial_output * u  # Planned at u capacity utilization
            firm.inventories = iota * initial_output  # Initial inventories
            firm.price = p20
            firm.unit_cost = c20
            firm.market_share = 1.0 / F20  # Fair share
            firm.competitiveness = 1.0
            firm.quality = 1.0
            
            # CRITICAL FIX: Set initial labor_demand consistent with planned output at u utilization
            # This prevents massive firing in period 1
            # Labor demand = output_planned / productivity
            firm.labor_demand = firm.output_planned / INIPROD
            firm.life_cycle = 3  # Start as incumbent
            
            self.firms2.append(firm)
    
    def _establish_relationships(self):
        """Establish initial relationships between agents"""
        # Assign banks to firms
        self.financial_market.assign_banks_to_firms(self.firms1, self.firms2, self.banks)
        
        # Establish supplier-customer relationships in capital market
        self.capital_market.establish_initial_relationships()
        
        # Adjust bank equity based on total firm net worth
        self._adjust_bank_equity()
    
    def _adjust_bank_equity(self):
        """Adjust bank equity based on firm net worth"""
        EqB0 = self.params.get('EqB0', 0.1)
        
        # Calculate total firm net worth
        total_nw = sum(f.net_worth for f in self.firms1 + self.firms2)
        
        # Distribute equity among banks
        for bank in self.banks:
            bank.equity = EqB0 * total_nw / len(self.banks)
    
    def _assign_initial_employment(self):
        """
        Assign workers to firms initially to achieve near-full employment.
        This matches the C++ model's initial state where workers start employed.
        
        Uses the calculated initial labor demands (Ld10, Ld20) from initialization.
        """
        # Get calculated initial labor demands (from _initialize_firms2)
        Ld10 = self.params.get('Ld10', 200)  # Total labor demand sector 1
        D10 = self.params.get('D10', 37)     # Production demand sector 1
        
        m1 = self.params.get('m1', 1.0)
        Btau0 = self.params.get('Btau0', 0.052)
        INIWAGE = 1.0
        nu = self.params.get('nu', 0.04)
        
        # Calculate labor needs for Firm1 sector
        # Each firm needs: (production workers) + (R&D workers)
        # Production workers per firm = (D10 / F1) / (Btau0 * m1)
        # R&D workers per firm = nu * (D10 / F1) * p10 / INIWAGE
        
        F1 = len(self.firms1)
        F2 = len(self.firms2)
        
        # Distribute labor among Firm1 firms
        labor_per_firm1 = Ld10 / F1 if F1 > 0 else 0
        for firm in self.firms1:
            firm.labor_demand = labor_per_firm1
            firm.labor_actual = labor_per_firm1
        
        # For Firm2, use the labor_demand already set during initialization
        # (which accounts for u utilization) - DO NOT override it here
        # This is already correctly set in _initialize_firms2 based on output_planned
        
        # Shuffle workers for random assignment
        available_workers = list(self.workers)
        np.random.shuffle(available_workers)
        
        total_workers = len(self.workers)
        worker_idx = 0
        INIWAGE = 1.0
        
        # Assign workers to Firm2 first (largest employer)
        for firm in self.firms2:
            # Use the labor_demand set during initialization (accounts for u utilization)
            n_workers_needed = int(firm.labor_demand)
            firm.labor_actual = n_workers_needed
            for _ in range(n_workers_needed):
                if worker_idx < len(available_workers):
                    worker = available_workers[worker_idx]
                    worker.employed = True
                    worker.employer = firm
                    worker.employer_sector = 2
                    worker.wage = INIWAGE
                    worker.tenure = 0
                    worker.unemployment_duration = 0
                    firm.workers.append(worker)
                    worker_idx += 1
                else:
                    break
        
        # Assign remaining workers to Firm1
        for firm in self.firms1:
            n_workers_needed = int(firm.labor_actual)
            for _ in range(n_workers_needed):
                if worker_idx < len(available_workers):
                    worker = available_workers[worker_idx]
                    worker.employed = True
                    worker.employer = firm
                    worker.employer_sector = 1
                    worker.wage = INIWAGE
                    worker.tenure = 0
                    worker.unemployment_duration = 0
                    firm.workers.append(worker)
                    worker_idx += 1
                else:
                    break
        
        # Remaining workers stay unemployed (target ~5% unemployment)
        print(f"Initial employment: {worker_idx}/{total_workers} workers employed "
              f"({100*worker_idx/total_workers:.1f}%)")
    
    def run(self, time_steps: int):
        """
        Run the simulation for a given number of time steps
        
        Args:
            time_steps: Number of time steps to simulate
        """
        self.max_time = time_steps
        print(f"\nRunning simulation for {time_steps} time steps...")
        
        for t in range(1, time_steps + 1):
            self.t = t
            
            # Execute one time step
            self.step()
            
            # Collect statistics
            self.stats.collect(self, t)
            
            # Print progress
            if t % 50 == 0:
                print(f"Time step {t}/{time_steps} completed")
        
        print("\nSimulation completed!")
    
    def step(self):
        """
        Execute one time step of the model
        
        This method implements the precise equation sequencing defined in
        the original model's timeStep equation to ensure stock-flow consistency.
        """
        t = self.t
        
        # Reset entry/exit counters at start of time step
        self.entry_firms1 = 0
        self.exit_firms1 = 0
        self.entry_firms2 = 0
        self.exit_firms2 = 0
        
        # 1. Regulatory regime change (if applicable)
        self._apply_regime_change()
        
        # 2. Central bank updates interest rates (Taylor rule)
        self.central_bank.update_interest_rate(self.stats, t)
        
        # 3. Financial market updates interest rate structure
        self.financial_market.update_interest_rates(self.central_bank.prime_rate)
        
        # 4. Consumption-good firms form expectations and plan production
        for firm in self.firms2:
            firm.form_expectations(t)
            firm.plan_production(t)
            firm.determine_labor_demand(t)
            firm.determine_investment_demand(t)
        
        # 5. Capital-good firms receive orders and plan production
        self.capital_market.process_orders(t)
        for firm in self.firms1:
            firm.plan_production(t)
            firm.determine_labor_demand(t)
        
        # 5.5. Handle firing decisions (before workers apply)
        self.labor_market.handle_firing(t)
        
        # 6. Workers submit job applications
        for worker in self.workers:
            worker.apply_for_jobs(t, self.labor_market)
        
        # 7. Firms post job openings and labor market matches
        self.labor_market.firms_post_vacancies(t)
        self.labor_market.match_workers_to_jobs(t)
        
        # 7.25. Allocate R&D and production workers in capital-good sector
        # This is the critical L1rd equation - MUST happen after hiring
        self.labor_market.allocate_sector1_rd_labor()
        
        # 7.5. Banks collect deposits and allocate credit to firms
        self.financial_market.process_credit_requests(t)
        
        # 8. Production is adjusted to actual labor hired
        for firm in self.firms1:
            firm.produce(t)
            firm.set_price(t)
        
        for firm in self.firms2:
            firm.produce(t)
            firm.set_price(t)
        
        # 8.5. Capital market delivers machines to Firm2
        self.capital_market.deliver_machines(t)
        
        # 9. Government determines expenditure
        self.government.determine_expenditure(t, self.workers, self.central_bank)
        
        # 10. Workers spend income on consumption goods
        for worker in self.workers:
            worker.determine_consumption(t)
        
        # 11. Goods market matches demand and supply
        self.goods_market.match_demand_supply(t)
        
        # 12. Firms calculate profits and pay taxes
        for firm in self.firms1:
            firm.calculate_profit(t)
            firm.pay_taxes(t, self.government)
            firm.update_net_worth(t)
        
        for firm in self.firms2:
            firm.calculate_profit(t)
            firm.pay_taxes(t, self.government)
            firm.update_net_worth(t)
        
        # 13. Banks calculate profits and pay taxes
        for bank in self.banks:
            bank.calculate_profit(t)
            bank.pay_taxes(t, self.government)
        
        # 14. Government collects taxes and updates public debt
        self.government.collect_taxes(t)
        self.government.update_public_debt(t)
        
        # 15. Calculate macroeconomic aggregates
        self._calculate_aggregates(t)
        
        # 16. Entry and exit of firms
        self._handle_entry_exit(t)
        
        # 17. Banks update credit scores
        self.financial_market.update_credit_scores(t)
    
    def _apply_regime_change(self):
        """Apply regime change if scheduled for current time"""
        TregChg = self.params.get('TregChg', 0)
        
        if TregChg > 0 and self.t == TregChg:
            print(f"\nApplying regime change at t={self.t}")
            # Update parameters with post-change values
            self.params.apply_regime_change()
    
    def _calculate_aggregates(self, t: int):
        """Calculate and store aggregate economic variables"""
        # These calculations are used by the statistics module
        pass
    
    def _handle_entry_exit(self, t: int):
        """Handle firm entry and exit in both sectors"""
        # Exit firms with near-zero market share or negative net worth
        self._exit_firms()
        
        # Entry of new firms based on market conditions
        self._entry_firms(t)
    
    def _exit_firms(self):
        """Remove firms that should exit the market"""
        f2min = self.params.get('f2min', 0.0001)  # Minimum market share
        n1 = self.params.get('n1', 4)  # Market participation period for Firm1
        
        # Check Firm2 exits
        surviving_firms2 = []
        for firm in self.firms2:
            should_exit = False
            
            # Exit if bankrupt (negative net worth)
            if firm.net_worth < 0:
                should_exit = True
            # Exit if incumbent firm with near-zero market share
            elif self.t >= firm.entry_time + n1 and firm.market_share < f2min:
                should_exit = True
            
            if should_exit:
                # Handle exit: fire workers, default on loans
                if hasattr(firm, 'exit'):
                    firm.exit(self.labor_market, self.financial_market)
                else:
                    # Simplified exit: just fire workers
                    for worker in firm.workers:
                        worker.employed = False
                        worker.employer = None
                        worker.unemployment_duration = 0
                self.exit_firms2 += 1
            else:
                surviving_firms2.append(firm)
        
        self.firms2 = surviving_firms2
        
        # Check Firm1 exits (similar logic)
        surviving_firms1 = []
        for firm in self.firms1:
            should_exit = False
            
            # Exit if bankrupt
            if firm.net_worth < 0:
                should_exit = True
            # Exit if incumbent with no clients for n1 periods
            elif self.t >= firm.entry_time + n1:
                # Check if firm has had any clients in recent periods
                if len(firm.clients) == 0:
                    should_exit = True
            
            if should_exit:
                if hasattr(firm, 'exit'):
                    firm.exit(self.labor_market, self.financial_market)
                else:
                    for worker in firm.workers:
                        worker.employed = False
                        worker.employer = None
                        worker.unemployment_duration = 0
                self.exit_firms1 += 1
            else:
                surviving_firms1.append(firm)
        
        self.firms1 = surviving_firms1
    
    def _entry_firms(self, t: int):
        """
        Create new entrant firms based on market conditions
        
        Entry follows the C++ model logic using market conditions (MC) 
        and various parameters.
        """
        # Get parameters
        omicron = self.params.get('omicron', 0.5)  # Entry sensitivity to market conditions
        x2inf = self.params.get('x2inf', -0.15)  # Entry distribution lower bound
        x2sup = self.params.get('x2sup', 0.15)  # Entry distribution upper bound
        stick = self.params.get('stick', 0.0)  # Stickiness parameter
        
        # Firm1 entry
        F1min = self.params.get('F1min', 10)
        F1max = self.params.get('F1max', 50)
        F10 = self.params.get('F10', 20)  # Initial number
        
        if len(self.firms1) < F1max:
            # Calculate market conditions change (simplified - use sales growth)
            if t > 1:
                current_sales = sum(f.sales for f in self.firms1)
                # Use a simple proxy for market conditions
                mc_change = min(max(np.random.uniform(x2inf, x2sup), x2inf), x2sup)
            else:
                mc_change = 0.0
            
            # Entry formula from C++ model (line 140-141 in fun_KS_capital.h)
            entry_rate = (1 - omicron) * np.random.uniform(x2inf, x2sup) + \
                         omicron * mc_change
            
            n_entry_base = max(0, int(round(len(self.firms1) * entry_rate)))
            
            # Apply stickiness shock (line 144 in C++)
            stickiness_adj = int(np.random.random() * stick * 
                               ((len(self.firms1) - self.exit_firms1) / F10 - 1) * F10)
            n_entry = max(0, n_entry_base - stickiness_adj)
            
            # Enforce min constraint
            if len(self.firms1) - self.exit_firms1 + n_entry < F1min:
                n_entry = F1min - len(self.firms1) + self.exit_firms1
            
            # Enforce max constraint
            if len(self.firms1) + n_entry > F1max:
                n_entry = F1max - len(self.firms1)
            
            # Create entrants
            for _ in range(max(0, n_entry)):
                # Entry with technology from incumbents (imitation)
                if self.firms1:
                    # Draw technology from best firms
                    best_firms = sorted(self.firms1, 
                                      key=lambda f: f.machine_productivity, 
                                      reverse=True)[:5]
                    template = np.random.choice(best_firms)
                    machine_prod = template.machine_productivity * (0.8 + 0.4 * np.random.random())
                else:
                    machine_prod = 1.0
                
                firm = Firm1(
                    firm_id=len(self.firms1) + 1000,  # High ID to avoid conflicts
                    params=self.params,
                    initial_net_worth=self.params.get('NW10', 100) * (0.5 + np.random.random()),
                    entrant=True,
                    entry_time=t
                )
                firm.machine_productivity = machine_prod
                self.firms1.append(firm)
                self.entry_firms1 += 1
        
        # Firm2 entry
        F2min = self.params.get('F2min', 50)
        F2max = self.params.get('F2max', 200)
        F20 = self.params.get('F20', 100)
        
        if len(self.firms2) < F2max:
            # Similar logic for Firm2
            if t > 1:
                mc_change = min(max(np.random.uniform(x2inf, x2sup), x2inf), x2sup)
            else:
                mc_change = 0.0
            
            entry_rate = (1 - omicron) * np.random.uniform(x2inf, x2sup) + \
                         omicron * mc_change
            
            n_entry_base = max(0, int(round(len(self.firms2) * entry_rate)))
            
            stickiness_adj = int(np.random.random() * stick * 
                               ((len(self.firms2) - self.exit_firms2) / F20 - 1) * F20)
            n_entry = max(0, n_entry_base - stickiness_adj)
            
            # Enforce constraints
            if len(self.firms2) - self.exit_firms2 + n_entry < F2min:
                n_entry = F2min - len(self.firms2) + self.exit_firms2
            
            if len(self.firms2) + n_entry > F2max:
                n_entry = F2max - len(self.firms2)
            
            # Create entrants
            for _ in range(max(0, n_entry)):
                # Entrants need initial capital
                m2 = self.params.get('m2', 1.0)
                initial_machines = int(5 + np.random.exponential(5))  # Small initial size
                
                firm = Firm2(
                    firm_id=len(self.firms2) + 1000,
                    params=self.params,
                    initial_net_worth=self.params.get('NW20', 100) * (0.5 + np.random.random()),
                    entrant=True,
                    entry_time=t
                )
                
                # Give entrant some initial capital (small vintage)
                if self.firms1:
                    supplier = np.random.choice(self.firms1)
                    from agents.vintage import Vintage
                    vintage = Vintage(
                        vintage_id=t * 10000 + firm.firm_id,
                        birth_time=t,
                        supplier_id=supplier.firm_id,
                        productivity=supplier.machine_productivity,
                        machines=initial_machines,
                        price=supplier.price
                    )
                    firm.vintages.append(vintage)
                    firm.capital_stock = initial_machines
                    firm.suppliers.append(supplier)
                    firm.main_supplier = supplier
                    supplier.clients.append(firm)
                
                self.firms2.append(firm)
                self.entry_firms2 += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get collected statistics from the simulation
        
        Returns:
            Dictionary of time series data for all tracked variables
        """
        return self.stats.get_data()
    
    def plot_results(self, variables: Optional[List[str]] = None):
        """
        Plot simulation results
        
        Args:
            variables: List of variable names to plot. If None, plots key aggregates.
        """
        from visualization.plots import plot_time_series, plot_distributions
        
        if variables is None:
            variables = ['GDP', 'unemployment_rate', 'inflation', 
                        'avg_productivity', 'num_firms1', 'num_firms2']
        
        plot_time_series(self.stats.get_data(), variables)
    
    def save_results(self, filename: str):
        """
        Save simulation results to file
        
        Args:
            filename: Output filename (CSV or JSON)
        """
        self.stats.save(filename)
    
    def __repr__(self):
        return (f"KSModel(t={self.t}, firms1={len(self.firms1)}, "
                f"firms2={len(self.firms2)}, workers={len(self.workers)}, "
                f"banks={len(self.banks)})")


if __name__ == "__main__":
    # Example usage
    model = KSModel(seed=42)
    model.run(time_steps=500)
    model.plot_results()
    model.save_results("results.csv")
