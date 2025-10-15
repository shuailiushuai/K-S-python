"""
Main K+S Model Simulation
Coordinates the complete ABM simulation with proper time stepping and initialization.
Based on fun_KS.cpp
"""

from typing import Dict, List, Optional, Any
import numpy as np
from .random_generator import random_engine, RandomEngine
from .agents import BaseAgent, CountryExtension, Firm2Extension
from .config import *
from .worker import Worker
from .bank import Bank
from .firm1 import Firm1


class Country(BaseAgent):
    """
    Country agent - top level container.
    Coordinates all sectors and agents.
    """
    
    def __init__(self, agent_id: int, params: Dict[str, Any]):
        super().__init__(agent_id, "Country", None)
        
        # Store parameters
        self.params = params
        
        # Create country extension
        self.extensions['country'] = CountryExtension()
        
        # Simulation time
        self.t = 0
        
        # Initialize sectors (will be populated in init_country)
        self.financial_sector = None
        self.capital_sector = None
        self.consumption_sector = None
        self.labor_supply = None
        self.stats = None
        
    def init_country(self, random_seed: Optional[int] = None):
        """
        Initialize country (initCountry equation).
        Sets up all sectors, firms, banks, and workers.
        
        Args:
            random_seed: Seed for random number generator
        """
        if random_seed is not None:
            random_engine.seed(random_seed)
        
        # Create sector containers
        self.financial_sector = BaseAgent(0, "Financial", self)
        self.capital_sector = BaseAgent(0, "Capital", self)
        self.consumption_sector = BaseAgent(0, "Consumption", self)
        self.labor_supply = BaseAgent(0, "Labor", self)
        self.stats = BaseAgent(0, "Stats", self)
        
        # Add to children
        self.add_child("Financial", self.financial_sector)
        self.add_child("Capital", self.capital_sector)
        self.add_child("Consumption", self.consumption_sector)
        self.add_child("Labor", self.labor_supply)
        self.add_child("Stats", self.stats)
        
        # Store in country extension for fast access
        ext = self.extensions['country']
        ext.finSec = self.financial_sector
        ext.capSec = self.capital_sector
        ext.conSec = self.consumption_sector
        ext.labSup = self.labor_supply
        ext.macSta = self.stats
        
        # Initialize financial sector (banks)
        self._init_financial_sector()
        
        # Initialize capital sector (Firm1)
        self._init_capital_sector()
        
        # Initialize consumption sector (Firm2)
        self._init_consumption_sector()
        
        # Initialize labor supply (workers)
        self._init_labor_supply()
        
        # Initialize statistics
        self._init_statistics()
        
        print(f"Country initialized with:")
        print(f"  Banks: {len(ext.bankPtr)}")
        print(f"  Capital firms: {self.capital_sector.count_children('Firm1')}")
        print(f"  Consumption firms: {self.consumption_sector.count_children('Firm2')}")
        print(f"  Workers: {self.labor_supply.count_children('Worker')}")
    
    def _init_financial_sector(self):
        """Initialize financial sector with banks"""
        B = int(self.params.get('B', 10))  # Number of banks
        EqB0 = self.params.get('EqB0', 1.0)
        alphaB = self.params.get('alphaB', 2.0)
        
        ext = self.extensions['country']
        
        # Create banks with heterogeneous sizes (Pareto distribution)
        sizes = [random_engine.pareto(alphaB) + 1.0 for _ in range(B)]
        total_size = sum(sizes)
        
        for i in range(B):
            bank = Bank(i + 1, self.financial_sector)
            bank._IDb = i + 1
            
            # Initial equity proportional to relative size
            bank._NWb = EqB0 * (sizes[i] / total_size)
            bank.WRITE("_NWb", bank._NWb)
            
            self.financial_sector.add_child("Bank", bank)
            ext.bankPtr.append(bank)
        
        # Compute initial market share weights
        ext.bankWgtd = [sizes[i] / total_size for i in range(B)]
        for i in range(1, B):
            ext.bankWgtd[i] += ext.bankWgtd[i-1]  # Cumulative
    
    def _init_capital_sector(self):
        """Initialize capital sector with Firm1 agents"""
        F10 = int(self.params.get('F10', 20))  # Initial number of firms
        NW10 = self.params.get('NW10', 1.0)
        mu1 = self.params.get('mu1', 0.25)
        
        for i in range(F10):
            firm = Firm1(i + 1, self.capital_sector)
            firm._ID1 = i + 1
            
            # Initial net worth
            firm._NW1 = NW10 * random_engine.uniform(0.8, 1.2)
            firm.WRITE("_NW1", firm._NW1)
            
            # Initial productivity (drawn from distribution)
            alpha2 = self.params.get('alpha2', 2.0)
            beta2 = self.params.get('beta2', 2.0)
            firm._Atau = INIPROD * random_engine.beta(alpha2, beta2)
            firm._Btau = INIPROD * random_engine.beta(alpha2, beta2)
            firm.WRITE("_Atau", firm._Atau)
            firm.WRITE("_Btau", firm._Btau)
            
            # Initial cost and price
            m1 = self.params.get('m1', 1.0)
            firm._w1 = INIWAGE
            firm._c1 = INIWAGE / (firm._Btau * m1)
            firm._p1 = (1 + mu1) * firm._c1
            firm._mu1 = mu1
            firm.WRITE("_c1", firm._c1)
            firm.WRITE("_p1", firm._p1)
            
            # Initial market share (uniform)
            firm._f1 = 1.0 / F10
            firm.WRITE("_f1", firm._f1)
            
            # Assign to bank
            bank_id = random_engine.integers(0, len(self.extensions['country'].bankPtr))
            bank = self.extensions['country'].bankPtr[bank_id]
            firm.WRITE_HOOK(BANK, bank)
            
            self.capital_sector.add_child("Firm1", firm)
    
    def _init_consumption_sector(self):
        """Initialize consumption sector with Firm2 agents"""
        F20 = int(self.params.get('F20', 100))  # Initial number of firms
        NW20 = self.params.get('NW20', 1.0)
        mu20 = self.params.get('mu20', 0.25)
        
        ext = self.extensions['country']
        
        for i in range(F20):
            firm = BaseAgent(i + 1, "Firm2", self.consumption_sector)
            firm._ID2 = i + 1
            
            # Add Firm2 extension
            firm.extensions['firm2'] = Firm2Extension()
            
            # Initial net worth
            firm._NW2 = NW20 * random_engine.uniform(0.8, 1.2)
            firm.WRITE("_NW2", firm._NW2)
            
            # Initial cost and price
            firm._c2 = INIWAGE / INIPROD
            firm._p2 = (1 + mu20) * firm._c2
            firm._mu2 = mu20
            firm.WRITE("_c2", firm._c2)
            firm.WRITE("_p2", firm._p2)
            
            # Initial market share (uniform)
            firm._f2 = 1.0 / F20
            firm.WRITE("_f2", firm._f2)
            
            # Assign to bank
            bank_id = random_engine.integers(0, len(ext.bankPtr))
            bank = ext.bankPtr[bank_id]
            firm.WRITE_HOOK(BANK, bank)
            
            self.consumption_sector.add_child("Firm2", firm)
            ext.firm2ptr.append(firm)
            ext.firm2map[i + 1] = firm
        
        # Compute initial market share weights (for client selection)
        ext.firm2wgtd = [1.0 / F20 for _ in range(F20)]
        for i in range(1, F20):
            ext.firm2wgtd[i] += ext.firm2wgtd[i-1]  # Cumulative
    
    def _init_labor_supply(self):
        """Initialize labor supply with workers"""
        Ls0 = int(self.params.get('Ls0', 1000))  # Initial workers
        Lscale = self.params.get('Lscale', 1.0)  # Scale factor
        
        # Number of worker objects (each represents Lscale actual workers)
        n_workers = int(Ls0 / Lscale)
        
        for i in range(n_workers):
            worker = Worker(i + 1, self.labor_supply)
            
            # Initial skills
            worker._s = INISKILL
            worker._sV = INISKILL
            worker._sT = INISKILL
            worker.WRITE("_s", INISKILL)
            worker.WRITE("_sV", INISKILL)
            worker.WRITE("_sT", INISKILL)
            
            # Initially unemployed
            worker._employed = 0
            worker._w = 0.0
            worker._wR = INIWAGE
            worker.WRITE("_employed", 0)
            worker.WRITE("_w", 0.0)
            worker.WRITE("_wR", INIWAGE)
            
            self.labor_supply.add_child("Worker", worker)
    
    def _init_statistics(self):
        """Initialize statistics tracking"""
        # Initialize macro variables
        self.WRITE("GDPreal", 0.0)
        self.WRITE("GDPnom", 0.0)
        self.WRITE("Cd", 0.0)
        self.WRITE("G", 0.0)
        self.WRITE("Tax", 0.0)
        self.WRITE("Deb", 0.0)
        self.WRITE("Def", 0.0)
    
    def time_step(self):
        """
        Execute one time step (timeStep equation).
        Ensures proper computation order of all variables.
        """
        self.t += 1
        
        # 1. Central bank updates interest rates
        self._update_interest_rates()
        
        # 2. Consumption firms define expectations and plans
        self._consumption_sector_planning()
        
        # 3. Capital firms do R&D and receive orders
        self._capital_sector_planning()
        
        # 4. Labor market: workers apply, firms hire
        self._labor_market()
        
        # 5. Production is adjusted to actual labor
        self._production()
        
        # 6. Prices are set
        self._price_setting()
        
        # 7. Government and consumption demand
        self._demand_and_sales()
        
        # 8. Profits, taxes, and cash flows
        self._profits_and_finance()
        
        # 9. Entry and exit
        self._entry_exit()
        
        # 10. Update all lagged variables
        self._update_lags()
        
        return self.t
    
    def _update_interest_rates(self):
        """Update interest rate structure"""
        # Taylor rule or fixed rate
        rT = self.params.get('rT', 0.02)
        muD = self.params.get('muD', 0.5)
        muDeb = self.params.get('muDeb', 2.0)
        muRes = self.params.get('muRes', 0.8)
        
        r = rT
        rD = r * (1 - muD)
        rDeb = r * (1 + muDeb)
        rRes = r * (1 - muRes)
        
        self.financial_sector.WRITE("r", r)
        self.financial_sector.WRITE("rD", rD)
        self.financial_sector.WRITE("rDeb", rDeb)
        self.financial_sector.WRITE("rRes", rRes)
    
    def _consumption_sector_planning(self):
        """Consumption sector planning"""
        # Simplified - actual implementation has complex expectation formation
        pass
    
    def _capital_sector_planning(self):
        """Capital sector R&D and production planning"""
        # Update all Firm1 agents
        for firm in self.capital_sector.get_children("Firm1"):
            firm.compute_productivity(self.params, self.t)
            firm.compute_unit_cost(firm._w1, self.params.get('m1', 1.0))
            firm.compute_price(self.params.get('mu1', 0.25))
    
    def _labor_market(self):
        """Labor market matching"""
        # Simplified - actual implementation has complex search and matching
        pass
    
    def _production(self):
        """Production based on hired labor"""
        pass
    
    def _price_setting(self):
        """Firms set prices"""
        pass
    
    def _demand_and_sales(self):
        """Match demand and supply"""
        pass
    
    def _profits_and_finance(self):
        """Compute profits, taxes, and update finances"""
        pass
    
    def _entry_exit(self):
        """Handle firm entry and exit"""
        pass
    
    def _update_lags(self):
        """Update all lagged variables"""
        # Update lags for all agents recursively
        self.update_lags()
        for sector_name in ["Financial", "Capital", "Consumption", "Labor"]:
            sector = self.children.get(sector_name, [[]])[0]
            if sector:
                sector.update_lags()
                for child_type in sector.children:
                    for agent in sector.children[child_type]:
                        agent.update_lags()


class KSModel:
    """
    Complete K+S ABM Model.
    Main simulation controller.
    """
    
    def __init__(self, params: Dict[str, Any], random_seed: Optional[int] = None):
        """
        Initialize K+S model.
        
        Args:
            params: Model parameters dictionary
            random_seed: Random seed for reproducibility
        """
        self.params = params
        self.random_seed = random_seed
        
        # Create country
        self.country = Country(1, params)
        
        # Initialize
        self.country.init_country(random_seed)
        
        # Simulation state
        self.t = 0
        self.T_max = params.get('T_max', 1000)
        
        # Results storage
        self.results = {
            'GDPreal': [],
            'GDPnom': [],
            'Unemployment': [],
            'Inflation': [],
            'time': []
        }
    
    def run(self, T_max: Optional[int] = None):
        """
        Run simulation for T_max periods.
        
        Args:
            T_max: Number of time periods (default: from params)
        """
        if T_max is not None:
            self.T_max = T_max
        
        print(f"Running K+S model for {self.T_max} periods...")
        
        for t in range(self.T_max):
            self.country.time_step()
            
            # Store results
            self.results['time'].append(t)
            self.results['GDPreal'].append(self.country.V("GDPreal"))
            self.results['GDPnom'].append(self.country.V("GDPnom"))
            
            if (t + 1) % 100 == 0:
                print(f"  Period {t + 1}/{self.T_max} completed")
        
        print("Simulation completed!")
        return self.results
    
    def get_results(self) -> Dict[str, List[float]]:
        """Get simulation results"""
        return self.results
