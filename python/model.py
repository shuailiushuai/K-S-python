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
from .firm2 import Firm2
from .vintage import Vint, create_vintage
from . import statistics as stats_module


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
        L10 = self.params.get('L10', 10)  # Initial workers per firm
        
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
            firm.WRITE("_w1", INIWAGE)
            
            # Initial labor
            firm._L1 = L10
            firm._L1d = L10
            firm.WRITE("_L1", L10)
            firm.WRITE("_L1d", L10)
            
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
        K0 = self.params.get('K0', 10.0)  # Initial capital per firm
        L20 = self.params.get('L20', 5)  # Initial workers per firm
        
        ext = self.extensions['country']
        
        for i in range(F20):
            firm = Firm2(i + 1, self.consumption_sector)
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
            firm.WRITE("_mu2", mu20)
            
            # Initial market share (uniform)
            firm._f2 = 1.0 / F20
            firm.WRITE("_f2", firm._f2)
            
            # Initial capital stock
            firm._K = K0
            firm.WRITE("_K", K0)
            
            # Initial labor
            firm._L2 = L20
            firm._L2d = L20
            firm.WRITE("_L2", L20)
            firm.WRITE("_L2d", L20)
            
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
        self.WRITE("Inflation", 0.0)
        self.WRITE("priceIndex", 1.0)
        
        # Initialize sector statistics
        self.stats.WRITE("HH1", 0.0)
        self.stats.WRITE("HH2", 0.0)
        self.stats.WRITE("AtauAvg", INIPROD)
        self.stats.WRITE("BtauAvg", INIPROD)
    
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
        
        # 10. Compute statistics
        self._compute_statistics()
        
        # 11. Update all lagged variables
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
        # Update all Firm2 agents expectations and plans
        for firm in self.consumption_sector.get_children("Firm2"):
            # Compute expected demand
            D2e = firm.compute_expected_demand(self.params, self.t)
            firm.WRITE("_D2e", D2e)
            
            # Compute desired capital
            Kd = firm.compute_desired_capital(self.params)
            firm.WRITE("_Kd", Kd)
            
            # Compute investment plans
            SI = firm.compute_investment_plans(self.params)
            firm.WRITE("_SI", SI)
            
            # Compute maximum debt
            Deb2max = firm.compute_max_debt(self.params)
            firm.WRITE("_Deb2max", Deb2max)
    
    def _capital_sector_planning(self):
        """Capital sector R&D and production planning"""
        # Update all Firm1 agents
        for firm in self.capital_sector.get_children("Firm1"):
            firm.compute_productivity(self.params, self.t)
            firm.compute_unit_cost(firm._w1, self.params.get('m1', 1.0))
            firm.compute_price(self.params.get('mu1', 0.25))
    
    def _labor_market(self):
        """Labor market matching"""
        # Compute unemployment and employment statistics
        self.compute_unemployment()
        
        # Workers search for jobs
        self._workers_apply_for_jobs()
        
        # Firms post vacancies and wages
        self._firms_post_vacancies()
        
        # Match workers to firms
        self._match_workers_to_firms()
    
    def compute_unemployment(self):
        """
        Compute unemployment rate and related statistics.
        Based on fun_KS_labor.h Ue equation.
        """
        Lscale = self.params.get('Lscale', 1.0)
        
        # Count employed and unemployed workers
        employed = 0
        unemployed = 0
        short_term_unemployed = 0
        
        for worker in self.labor_supply.get_children("Worker"):
            if worker.V("_employed") > 0:
                employed += 1
            else:
                unemployed += 1
                # Check if short-term (unemployed < 1 period)
                Tu = worker.V("_Tu") if hasattr(worker, '_Tu') else 0
                if Tu < 1:
                    short_term_unemployed += 1
        
        total = employed + unemployed
        if total > 0:
            Ue = unemployed / total  # Unemployment rate
            Us = short_term_unemployed / total  # Short-term unemployment
        else:
            Ue = 0.0
            Us = 0.0
        
        self.labor_supply.WRITE("Ue", Ue)
        self.labor_supply.WRITE("Us", Us)
        self.labor_supply.WRITE("L", employed * Lscale)
        
        return Ue
    
    def _workers_apply_for_jobs(self):
        """Workers send job applications"""
        omega = self.params.get('omega', 3)  # Applications per worker
        
        for worker in self.labor_supply.get_children("Worker"):
            # Unemployed workers apply
            if worker.V("_employed") == 0:
                # Send omega applications (Poisson distributed)
                n_appl = random_engine.poisson(omega)
                worker.WRITE("_appl", n_appl)
                
                # Apply to random firms (simplified - would use proper selection)
                # This would be implemented fully with application queues
    
    def _firms_post_vacancies(self):
        """Firms post wage offers and vacancies"""
        # Firm1 vacancies
        for firm in self.capital_sector.get_children("Firm1"):
            L1d = firm.V("_L1d")
            L1 = firm.V("_L1")
            JO1 = max(0, L1d - L1)
            firm.WRITE("_JO1", JO1)
        
        # Firm2 vacancies
        for firm in self.consumption_sector.get_children("Firm2"):
            L2d = firm.V("_L2d")
            L2 = firm.V("_L2")
            JO2 = max(0, L2d - L2)
            firm.WRITE("_JO2", JO2)
    
    def _match_workers_to_firms(self):
        """Match worker applications to firm vacancies"""
        # Simplified matching - full implementation would use
        # the application queues and worker ranking
        pass
    
    def _production(self):
        """Production based on hired labor"""
        # Capital sector production
        for firm in self.capital_sector.get_children("Firm1"):
            # Simplified production
            L1 = firm.V("_L1")
            Btau = firm.V("_Btau")
            m1 = self.params.get('m1', 1.0)
            
            # Production = labor * productivity * modularity
            Q1 = L1 * Btau * m1
            firm.WRITE("_Q1", Q1)
            
            # Sales equal production (no inventories in capital sector)
            firm.WRITE("_S1", Q1)
            
            # Wage bill
            w1 = firm.V("_w1")
            W1 = L1 * w1
            firm.WRITE("_W1", W1)
        
        # Consumption sector production
        for firm in self.consumption_sector.get_children("Firm2"):
            # Simplified production (without vintages for now)
            L2 = firm.V("_L2")
            K = firm.V("_K")
            m2 = self.params.get('m2', 1.0)
            
            # Production constrained by capital
            if K > 0:
                # Effective productivity (simplified)
                A2e = INIPROD * 0.8  # Placeholder
                Q2e = min(L2 * A2e, K * m2)
            else:
                Q2e = 0.0
            
            firm.WRITE("_Q2e", Q2e)
            
            # Wage bill (simplified - constant wage)
            L2d = firm.V("_L2d")
            if L2d > 0:
                w2avg = INIWAGE
                W2 = L2 * w2avg
            else:
                W2 = 0.0
            
            firm.WRITE("_W2", W2)
            firm.WRITE("_w2avg", INIWAGE)
    
    def _price_setting(self):
        """Firms set prices"""
        # Capital sector pricing
        for firm in self.capital_sector.get_children("Firm1"):
            mu1 = self.params.get('mu1', 0.25)
            firm.compute_price(mu1)
        
        # Consumption sector pricing
        for firm in self.consumption_sector.get_children("Firm2"):
            # Update markup
            mu2 = firm.compute_markup(self.params)
            firm.WRITE("_mu2", mu2)
            
            # Update cost (if production happened)
            if firm.V("_Q2e") > 0:
                c2 = firm.compute_unit_cost(self.params)
                firm.WRITE("_c2", c2)
            
            # Set price
            p2 = firm.compute_price()
            firm.WRITE("_p2", p2)
    
    def _demand_and_sales(self):
        """Match demand and supply"""
        # Compute desired consumption
        Cd = self.compute_desired_consumption()
        self.WRITE("Cd", Cd)
        
        # Compute government expenditure
        G = self.compute_government_expenditure()
        self.WRITE("G", G)
        
        # Allocate consumption demand to firms
        self._allocate_consumption_demand(Cd)
        
        # Compute sales for all firms
        for firm in self.consumption_sector.get_children("Firm2"):
            # Simplified sales computation
            D2d = firm.V("_D2d")  # Demand allocated to firm
            N = firm.VL("_N", 1)   # Previous inventories
            Q2e = firm.V("_Q2e")   # Production
            
            # Sales = min(demand, available = inventories + production)
            available = N + Q2e
            S2 = min(D2d, available)
            
            # Update inventories
            N_new = available - S2
            
            firm.WRITE("_S2", S2)
            firm.WRITE("_N", N_new)
            firm.WRITE("_D2", S2)  # Realized demand
    
    def compute_desired_consumption(self) -> float:
        """
        Compute nominal desired consumption (Cd).
        Based on fun_KS_country.h Cd equation.
        """
        # Workers' net income after taxes
        W = self.labor_supply.V("W") if hasattr(self.labor_supply, 'V') else 0.0
        G = self.V("G")
        Bon_lag1 = self.labor_supply.VL("Bon", 1) if hasattr(self.labor_supply, 'VL') else 0.0
        TaxW = self.labor_supply.V("TaxW") if hasattr(self.labor_supply, 'V') else 0.0
        Div_lag1 = self.VL("Div", 1)
        TaxDiv = self.V("TaxDiv")
        
        # Disposable income
        Yd = W + G + Bon_lag1 - TaxW + Div_lag1 - TaxDiv
        
        # Consumption propensity (simplified - would check flagCons)
        flag_cons = int(self.params.get('flagCons', 0))
        
        if flag_cons == 0:  # All income consumed
            Cd = Yd
        else:  # With savings
            savings_rate = self.params.get('savingsRate', 0.1)
            Cd = Yd * (1 - savings_rate)
        
        return max(Cd, 0.0)
    
    def compute_government_expenditure(self) -> float:
        """
        Compute government expenditure (G).
        Based on fun_KS_country.h G equation.
        """
        # Unemployment benefits
        Ls0 = self.params.get('Ls0', 1000)
        Lscale = self.params.get('Lscale', 1.0)
        phi = self.params.get('phi', 0.5)  # Benefit rate
        
        # Count unemployed workers
        n_unemployed = 0
        for worker in self.labor_supply.get_children("Worker"):
            if worker.V("_employed") == 0:
                n_unemployed += 1
        
        # Average wage (simplified)
        w_avg = INIWAGE  # Would compute from employed workers
        
        # Unemployment benefits
        benefits = n_unemployed * Lscale * phi * w_avg
        
        # Fixed government consumption (grows at rate gG)
        gG = self.params.get('gG', 0.0)
        G_lag1 = self.VL("G", 1)
        G_fixed = G_lag1 * (1 + gG) if G_lag1 > 0 else 0.0
        
        return benefits + G_fixed
    
    def _allocate_consumption_demand(self, Cd: float):
        """Allocate consumption demand to firms based on competitiveness"""
        # Compute competitiveness for all firms
        total_E = 0.0
        for firm in self.consumption_sector.get_children("Firm2"):
            E = firm.compute_competitiveness(self.params)
            firm.WRITE("_E", E)
            total_E += E
        
        # Allocate demand proportionally to competitiveness
        for firm in self.consumption_sector.get_children("Firm2"):
            if total_E > 0:
                E = firm.V("_E")
                firm_demand = Cd * (E / total_E)
            else:
                # Equal allocation if no competitiveness
                n_firms = self.consumption_sector.count_children("Firm2")
                firm_demand = Cd / n_firms if n_firms > 0 else 0.0
            
            firm.WRITE("_D2d", firm_demand)
    
    def _profits_and_finance(self):
        """Compute profits, taxes, and update finances"""
        # Compute GDP
        GDPnom = self.compute_gdp_nominal()
        GDPreal = self.compute_gdp_real()
        self.WRITE("GDPnom", GDPnom)
        self.WRITE("GDPreal", GDPreal)
        
        # Compute total taxes
        Tax = self.compute_total_tax()
        self.WRITE("Tax", Tax)
        
        # Compute government deficit
        G = self.V("G")
        Def = G - Tax
        self.WRITE("Def", Def)
        
        # Update public debt
        Deb_lag1 = self.VL("Deb", 1)
        r = self.financial_sector.V("r")
        Deb = Deb_lag1 * (1 + r) + Def
        self.WRITE("Deb", Deb)
        
        # Compute firm profits and distribute
        self._compute_firm_profits()
        
        # Compute total dividends
        Div = self.compute_total_dividends()
        self.WRITE("Div", Div)
    
    def compute_gdp_nominal(self) -> float:
        """
        Compute nominal GDP (GDPnom).
        Based on fun_KS_country.h GDPnom equation.
        """
        # GDP = Consumption + Investment + Government
        C = sum(firm.V("_S2") * firm.V("_p2") 
                for firm in self.consumption_sector.get_children("Firm2"))
        
        I = sum(firm.V("_EI") 
                for firm in self.consumption_sector.get_children("Firm2"))
        
        G = self.V("G")
        
        return C + I + G
    
    def compute_gdp_real(self) -> float:
        """
        Compute real GDP (GDPreal).
        Based on fun_KS_country.h GDPreal equation.
        """
        # Real GDP = sum of value added at constant prices
        # Simplified: use quantities
        Q1 = sum(firm.V("_Q1") for firm in self.capital_sector.get_children("Firm1"))
        Q2 = sum(firm.V("_Q2e") for firm in self.consumption_sector.get_children("Firm2"))
        
        return Q1 + Q2
    
    def compute_total_tax(self) -> float:
        """
        Compute total tax revenue (Tax).
        Based on fun_KS_country.h Tax equation.
        """
        tr = self.params.get('tr', 0.2)  # Tax rate
        
        # Taxes from firms
        Tax1 = 0.0
        for firm in self.capital_sector.get_children("Firm1"):
            Pi1 = firm.V("_Pi1")
            if Pi1 > 0:
                Tax1 += tr * Pi1
        
        Tax2 = 0.0
        for firm in self.consumption_sector.get_children("Firm2"):
            Pi2 = firm.V("_Pi2")
            if Pi2 > 0:
                Tax2 += tr * Pi2
        
        # Taxes from workers (simplified)
        TaxW = 0.0
        
        return Tax1 + Tax2 + TaxW
    
    def _compute_firm_profits(self):
        """Compute profits for all firms"""
        # Capital sector
        for firm in self.capital_sector.get_children("Firm1"):
            # Revenues - Costs
            S1 = firm.V("_S1")
            p1 = firm.V("_p1")
            W1 = firm.V("_W1")
            
            Pi1 = S1 * p1 - W1
            firm.WRITE("_Pi1", Pi1)
        
        # Consumption sector
        for firm in self.consumption_sector.get_children("Firm2"):
            # Revenues - Costs
            S2 = firm.V("_S2")
            p2 = firm.V("_p2")
            W2 = firm.V("_W2")
            
            Pi2 = S2 * p2 - W2
            firm.WRITE("_Pi2", Pi2)
            
            # Compute bonuses
            Bon2 = firm.compute_bonuses(self.params)
            firm.WRITE("_Bon2", Bon2)
            
            # Compute dividends
            Div2 = firm.compute_dividends(self.params)
            firm.WRITE("_Div2", Div2)
    
    def compute_total_dividends(self) -> float:
        """Compute total dividends distributed"""
        Div1 = sum(firm.V("_Div1") if firm.V("_Div1") > 0 else 0.0
                   for firm in self.capital_sector.get_children("Firm1"))
        Div2 = sum(firm.V("_Div2") 
                   for firm in self.consumption_sector.get_children("Firm2"))
        
        return Div1 + Div2
    
    def _entry_exit(self):
        """Handle firm entry and exit"""
        # Count firms needing exit (negative net worth)
        exit1 = sum(1 for firm in self.capital_sector.get_children("Firm1")
                   if firm.V("_NW1") < 0)
        exit2 = sum(1 for firm in self.consumption_sector.get_children("Firm2")
                   if firm.V("_NW2") < 0)
        
        self.WRITE("cExit", exit1 + exit2)
        
        # Entry based on market conditions (simplified)
        # Full implementation would use entry rules
        self.WRITE("cEntry", 0)
    
    def _compute_statistics(self):
        """Compute all statistics"""
        # Sectoral statistics
        sector1_stats = stats_module.compute_sectoral_statistics(
            self.capital_sector, "Firm1")
        sector2_stats = stats_module.compute_sectoral_statistics(
            self.consumption_sector, "Firm2")
        
        # Write sectoral stats
        for key, value in sector1_stats.items():
            self.stats.WRITE(key, value)
        for key, value in sector2_stats.items():
            self.stats.WRITE(key, value)
        
        # Labor statistics
        labor_stats = stats_module.compute_labor_statistics(self.labor_supply)
        for key, value in labor_stats.items():
            self.labor_supply.WRITE(key, value)
        
        # Financial statistics
        fin_stats = stats_module.compute_financial_statistics(self.financial_sector)
        for key, value in fin_stats.items():
            self.financial_sector.WRITE(key, value)
        
        # Credit statistics
        credit_stats = stats_module.compute_credit_statistics(
            self.capital_sector, self.consumption_sector)
        for key, value in credit_stats.items():
            self.stats.WRITE(key, value)
        
        # Productivity statistics
        prod_stats = stats_module.compute_productivity_statistics(self.capital_sector)
        for key, value in prod_stats.items():
            self.stats.WRITE(key, value)
        
        # Price index and inflation
        price_index = stats_module.compute_price_index(self.consumption_sector)
        self.WRITE("priceIndex", price_index)
        
        price_index_lag = self.VL("priceIndex", 1)
        inflation = stats_module.compute_inflation(price_index, price_index_lag)
        self.WRITE("Inflation", inflation)
        
        # GDP growth
        GDP_current = self.V("GDPreal")
        GDP_lag = self.VL("GDPreal", 1)
        GDP_growth = stats_module.compute_growth_rate(GDP_current, GDP_lag)
        self.WRITE("GDPgrowth", GDP_growth)
    
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
            'GDPgrowth': [],
            'Unemployment': [],
            'Inflation': [],
            'Consumption': [],
            'Investment': [],
            'Government': [],
            'Wages': [],
            'Profits': [],
            'Debt': [],
            'Tax': [],
            'HH1': [],  # Capital sector concentration
            'HH2': [],  # Consumption sector concentration
            'AtauAvg': [],  # Average productivity
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
            self.results['GDPgrowth'].append(self.country.V("GDPgrowth"))
            self.results['Unemployment'].append(self.country.labor_supply.V("Ue"))
            self.results['Inflation'].append(self.country.V("Inflation"))
            self.results['Consumption'].append(self.country.V("Cd"))
            self.results['Government'].append(self.country.V("G"))
            self.results['Debt'].append(self.country.V("Deb"))
            self.results['Tax'].append(self.country.V("Tax"))
            
            # Sectoral statistics
            if hasattr(self.country, 'stats'):
                self.results['HH1'].append(self.country.stats.V("HH1"))
                self.results['HH2'].append(self.country.stats.V("HH2"))
                self.results['AtauAvg'].append(self.country.stats.V("AtauAvg"))
            
            if (t + 1) % 100 == 0:
                print(f"  Period {t + 1}/{self.T_max} completed")
        
        print("Simulation completed!")
        return self.results
    
    def get_results(self) -> Dict[str, List[float]]:
        """Get simulation results"""
        return self.results
