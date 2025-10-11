"""
Country Agent Implementation
Represents the top-level orchestrator for the K+S model
"""

from typing import List, Dict, Optional
from .agent import Agent
from .firm1 import Firm1
from .firm2 import Firm2
from .vintage import VintageAgent
from .worker import Worker
from .bank import Bank
from .labor import LaborMarket
from .statistics import StatisticsCollector
from .constants import *
from .random_engine import random_engine
from .support import safe_divide
import math


class CapitalSector(Agent):
    """
    Capital goods sector container
    Manages Firm1 agents producing capital goods (machines)
    """
    
    def __init__(self, parent: Agent):
        """Initialize Capital Sector"""
        super().__init__("Capital", parent)
        
        # Sector parameters
        self._F10 = 20                    # Initial number of firms
        self._F1min = 10                  # Minimum number of firms
        self._F1max = 100                 # Maximum number of firms
        self._m1 = 1.0                    # Machine output per period
        self._mu1 = 0.1                   # Mark-up
        self._nu = 0.04                   # R&D investment rate
        
        # Aggregate variables
        self._D1 = 0.0                    # Orders for machines
        self._Q1 = 0.0                    # Planned machine production
        self._Q1e = 0.0                   # Effective machine production
        self._L1d = 0                     # Labor demand
        self._JO1 = 0                     # Job openings
        self._p1avg = 0.0                 # Average machine price
        self._Pi1 = 0.0                   # Sector profits
        self._Tax1 = 0.0                  # Sector taxes
        self._NW1 = 0.0                   # Sector net worth
        self._Div1 = 0.0                  # Sector dividends
        self._Eq1 = 0.0                   # Sector equity
        self._cEntry1 = 0.0               # Entry cost
        self._cExit1 = 0.0                # Exit credit
        
        # Firms list
        self.firms: List[Firm1] = []


class ConsumptionSector(Agent):
    """
    Consumption goods sector container
    Manages Firm2 agents producing consumption goods
    """
    
    def __init__(self, parent: Agent):
        """Initialize Consumption Sector"""
        super().__init__("Consumption", parent)
        
        # Sector parameters
        self._F20 = 50                    # Initial number of firms
        self._F2min = 20                  # Minimum number of firms
        self._F2max = 200                 # Maximum number of firms
        self._m2 = 1.0                    # Machine output per period
        self._b = 3.0                     # Payback period
        self._mu20 = 0.2                  # Initial mark-up
        self._f2min = 0.001               # Exit market share threshold
        
        # Aggregate variables
        self._D2e = 0.0                   # Expected demand
        self._D2d = 0.0                   # Desired demand
        self._D2 = 0.0                    # Fulfilled demand
        self._Q2 = 0.0                    # Planned production
        self._Q2e = 0.0                   # Effective production
        self._S2 = 0.0                    # Sales
        self._N = 0.0                     # Inventories
        self._dNnom = 0.0                 # Change in inventories (nominal)
        self._L2d = 0                     # Labor demand
        self._JO2 = 0                     # Job openings
        self._Id = 0.0                    # Desired investment
        self._Inom = 0.0                  # Investment (nominal)
        self._Ireal = 0.0                 # Investment (real)
        self._p2avg = 0.0                 # Average goods price
        self._pC0 = 1.0                   # Initial price level
        self._Pi2 = 0.0                   # Sector profits
        self._Tax2 = 0.0                  # Sector taxes
        self._NW2 = 0.0                   # Sector net worth
        self._Div2 = 0.0                  # Sector dividends
        self._Eq2 = 0.0                   # Sector equity
        self._cEntry2 = 0.0               # Entry cost
        self._cExit2 = 0.0                # Exit credit
        
        # Firms list
        self.firms: List[Firm2] = []


class FinancialSector(Agent):
    """
    Financial sector container
    Manages Bank agents and central bank operations
    """
    
    def __init__(self, parent: Agent):
        """Initialize Financial Sector"""
        super().__init__("Financial", parent)
        
        # Sector parameters
        self._B = 5                       # Number of banks
        self._tauB = 0.08                 # Capital adequacy ratio (8%)
        self._rT = 0.03                   # Target interest rate
        self._muBonds = -0.01             # Bond rate spread
        self._muD = -0.01                 # Deposit rate spread
        self._muDeb = 0.02                # Debt rate spread
        self._muRes = -0.01               # Reserve rate spread
        
        # Interest rates
        self._r = 0.03                    # Prime interest rate
        self._rBonds = 0.02               # Bond interest rate
        self._rD = 0.02                   # Deposit interest rate
        self._rDeb = 0.05                 # Debt interest rate
        self._rRes = 0.02                 # Reserve interest rate
        
        # Aggregate variables
        self._PiB = 0.0                   # Banking sector profits
        self._TaxB = 0.0                  # Banking sector taxes
        self._DivB = 0.0                  # Banking sector dividends
        self._Gbail = 0.0                 # Government bailouts
        self._BondsB = 0.0                # Bonds held by banks
        self._BondsCB = 0.0               # Bonds held by central bank
        self._DepoG = 0.0                 # Government deposits
        self._PiCB = 0.0                  # Central bank profits
        self._Cl = 0                      # Total clients
        
        # Banks list
        self.banks: List[Bank] = []


class Country(Agent):
    """
    Country agent class - Top-level orchestrator
    
    Manages:
    - Initialization of all agents
    - Time-step sequencing
    - Government operations
    - Aggregate statistics
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize Country
        
        Args:
            config: Configuration dictionary (optional)
        """
        super().__init__("Country", None)  # Country is root, no parent
        
        # Time tracking
        self._t = 0                       # Current time period
        
        # Model flags
        self._flagCons = 2                # Consumption mode (0-2)
        self._flagGovExp = 2              # Government expenditure mode
        self._flagFiscalRule = 0          # Fiscal rule mode
        self._flagTax = 1                 # Tax mode (0=none, 1=basic, 2=full)
        self._flagWorkerLBU = 1           # Worker learning mode
        self._flagWorkerSkProd = 3        # Skills affect productivity mode
        self._TregChg = 9999              # Regime change time (disabled)
        
        # Government parameters
        self._gG = 0.01                   # Government spending growth rate
        self._Crec = 0.5                  # Savings recovery rate
        self._tr = 0.2                    # Tax rate
        self._mLim = 0.05                 # Productivity growth limit
        self._mPer = 4                    # Productivity moving average periods
        
        # Government variables
        self._G = 0.0                     # Government expenditure
        self._Tax = 0.0                   # Total tax revenue
        self._TaxDiv = 0.0                # Dividend tax
        self._Def = 0.0                   # Government deficit
        self._DefP = 0.0                  # Primary deficit
        self._Deb = 0.0                   # Government debt
        self._SavAcc = 0.0                # Accumulated savings
        self._Cd = 0.0                    # Desired consumption
        self._C = 0.0                     # Actual consumption
        self._Sav = 0.0                   # Forced savings
        self._Div = 0.0                   # Total dividends
        self._Eq = 0.0                    # Total equity
        self._cEntry = 0.0                # Entry cost
        self._cExit = 0.0                 # Exit credit
        
        # Macroeconomic variables
        self._GDPreal = 0.0               # Real GDP
        self._GDPnom = 0.0                # Nominal GDP
        self._Creal = 0.0                 # Real consumption
        self._A = INIPROD                 # Overall productivity
        self._dAb = 0.0                   # Productivity growth (bounded)
        self._dGDP = 0.0                  # GDP growth rate
        self._DebGDP = 0.0                # Debt to GDP ratio
        self._DefPgdp = 0.0               # Primary deficit to GDP ratio
        self._inflation = 0.0             # Inflation rate
        
        # Create sectors
        self.capital_sector = CapitalSector(self)
        self.consumption_sector = ConsumptionSector(self)
        self.financial_sector = FinancialSector(self)
        self.labor_market = LaborMarket(self)
        
        # Statistics collector
        self.statistics = StatisticsCollector(self)
        
        # Workers list (managed at country level)
        self.workers: List[Worker] = []
        
        # Apply configuration if provided
        if config:
            self.apply_config(config)
    
    def apply_config(self, config: Dict):
        """
        Apply configuration parameters
        
        Args:
            config: Configuration dictionary
        """
        # Apply country-level parameters
        for key, value in config.get('country', {}).items():
            attr = f"_{key}"
            if hasattr(self, attr):
                setattr(self, attr, value)
        
        # Apply sector parameters
        for sector_name in ['capital', 'consumption', 'financial', 'labor']:
            sector_key = f"{sector_name}_sector"
            if hasattr(self, sector_key):
                sector = getattr(self, sector_key)
                for key, value in config.get(sector_name, {}).items():
                    attr = f"_{key}"
                    if hasattr(sector, attr):
                        setattr(sector, attr, value)
    
    def initialize(self):
        """
        Initialize all agents and structures
        Must be called before simulation
        """
        # Check if already initialized
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        # Set initial time
        self._t = 0
        
        # Initialize random engine
        seed = 42  # Default seed, can be configured
        random_engine.seed(seed)
        
        # Initialize sectors
        self._initialize_capital_sector()
        self._initialize_consumption_sector()
        self._initialize_financial_sector()
        self._initialize_labor_market()
        
        # Set initial government state
        self._initialize_government()
        
        # Compute initial aggregates
        self._compute_initial_aggregates()
        
        # Mark as initialized
        self._initialized = True
    
    def _initialize_capital_sector(self):
        """Initialize capital goods firms"""
        sector = self.capital_sector
        F10 = int(sector._F10)
        
        # Create initial firms
        for i in range(F10):
            firm = Firm1(firm_id=i+1, parent=sector)
            # Initialize with default values
            firm._Atau = INIPROD
            firm._Btau = INIPROD
            firm._p1 = INIPROD * 1.1  # Initial price
            firm._NW1 = 10.0  # Initial net worth
            firm._Q1 = 0.0  # Production
            firm._Q1e = 0.0  # Effective production
            firm._L1d = 0  # Labor demand
            firm._JO1 = 0  # Job openings
            sector.firms.append(firm)
    
    def _initialize_consumption_sector(self):
        """Initialize consumption goods firms"""
        sector = self.consumption_sector
        F20 = int(sector._F20)
        
        # Create initial firms
        for i in range(F20):
            firm = Firm2(firm_id=i+1, parent=sector)
            # Initialize with default values
            firm._A2 = INIPROD
            firm._mu2 = sector._mu20
            firm._p2 = INIPROD * 1.2  # Initial price
            firm._NW2 = 10.0  # Initial net worth
            firm._D2e = 0.0  # Expected demand
            firm._Q2d = 0.0  # Desired production
            firm._Q2e = 0.0  # Effective production
            firm._S2 = 0.0  # Sales
            firm._L2d = 0  # Labor demand
            firm._JO2 = 0  # Job openings
            sector.firms.append(firm)
    
    def _initialize_financial_sector(self):
        """Initialize banks"""
        sector = self.financial_sector
        B = int(sector._B)
        
        # Create initial banks
        for i in range(B):
            bank = Bank(bank_id=i+1, parent=sector)
            # Initialize with default values
            bank._NWb = 15.0  # Initial bank net worth
            bank._Depo = 80.0  # Initial deposits
            sector.banks.append(bank)
    
    def _initialize_labor_market(self):
        """Initialize workers"""
        labor = self.labor_market
        Ls0 = 1000  # Initial labor supply (notional)
        Lscale = 10  # Labor scaling factor
        
        labor._Ls = Ls0  # Notional labor supply
        labor._Lscale = Lscale
        labor._w0min = 0.5  # Minimum wage
        labor._wAvg = INIWAGE
        
        # Create actual worker agents (scaled down)
        num_workers = Ls0 // Lscale
        for i in range(num_workers):
            worker = Worker(worker_id=i+1, parent=labor)
            worker._age = 25  # Initial age
            worker._Tc = 12  # Contract term
            worker._wRes = INIWAGE  # Reservation wage
            worker._wReal = INIWAGE  # Initial wage
            worker._employed = 0  # Initially unemployed
            worker._employer = None  # No employer
            worker._Te = 0  # Tenure
            worker._sV = INISKILL
            worker._sT = INISKILL
            self.workers.append(worker)
    
    def _initialize_government(self):
        """Initialize government state"""
        # Set initial government expenditure
        Ls0 = self.labor_market._Ls
        self._G = self._gG * Ls0
        
        # Initialize debt and deficit at zero
        self._Deb = 0.0
        self._Def = 0.0
        self._DefP = 0.0
        self._SavAcc = 0.0
    
    def _compute_initial_aggregates(self):
        """Compute initial aggregate statistics"""
        # Simple initial values
        self._GDPreal = 1000.0
        self._GDPnom = 1000.0
        self._A = INIPROD
        self._dAb = 0.0
        self._dGDP = 0.0
    
    def time_step(self):
        """
        Execute one complete time step
        Follows the equation sequencing from fun_KS.cpp::timeStep
        
        Exact sequence:
        1. Central bank updates interest rates (r, rDeb, rBonds)
        2. Consumption sector plans (D2e, Q2, L2d, Id)
        3. Capital sector plans (D1, Q1, L1d)
        4. Labor market matching (appl, JO1, JO2, L)
        5. Production and pricing (Q1e, Q2e, p1avg, p2avg)
        6. Consumption and sales (G, D2d, D2, N, Sav)
        7. Financial operations (Pi1, Pi2, PiB, Tax1, Tax2, TaxB, NW1, NW2)
        8. Government operations (Tax, Def, Deb)
        9. Aggregates (GDPreal, GDPnom)
        10. Entry/exit (entryExit)
        """
        # Increment time
        self._t += 1
        
        # 1. Central bank updates interest rates
        self._update_interest_rates()
        
        # 2. Consumption firms: expectations, production, labor demand, investment
        self._consumption_planning()
        
        # 3. Capital firms: R&D, orders, production, labor demand
        self._capital_planning()
        
        # 4. Labor market: applications, job openings, matching, hiring
        self._labor_market_matching()
        
        # 5. Production and pricing
        self._production_and_pricing()
        
        # 6. Government expenditure and consumption/sales
        self._consumption_and_sales()
        
        # 7. Financial operations: profits, taxes, cash flows
        self._financial_operations()
        
        # 8. Government operations: taxes, deficit, debt
        self._government_operations()
        
        # 9. Compute aggregate statistics
        self._compute_aggregates()
        
        # 10. Entry and exit
        self._entry_exit()
        
        # Update statistics collector
        self.statistics.compute_all_statistics(self)
        
        # Update lag values for next period
        self.update_lags()
    
    def _update_interest_rates(self):
        """
        Update interest rate structure
        Implements r, rBonds, rD, rDeb, rRes equations from fun_KS_financial.h
        """
        fin = self.financial_sector
        con_sector = self.consumption_sector
        labor = self.labor_market
        
        # Central bank prime rate (r equation - Taylor rule)
        r_current = fin._r
        rAdj = getattr(fin, '_rAdj', 0.0025)  # Rate adjustment step
        
        # Taylor rule
        piT = getattr(fin, '_piT', 0.02)  # Target inflation
        Ut = getattr(fin, '_Ut', 0.05)  # Target unemployment
        gammaPi = getattr(fin, '_gammaPi', 1.5)  # Inflation weight
        gammaU = getattr(fin, '_gammaU', 0.5)  # Unemployment weight
        rT = fin._rT  # Target rate
        
        # Get inflation and unemployment from previous period
        dCPIb_lag = self.read('_inflation', lag=1, default=0)  # Bounded inflation
        Ue_lag = labor._Ue  # Current unemployment rate
        
        # Taylor rule formula
        r_taylor = rT + gammaPi * (dCPIb_lag - piT) + gammaU * (Ut - Ue_lag)
        
        # Smooth rate adjustment
        if abs(r_taylor - r_current) > 2 * rAdj:
            # Big adjustment
            fin._r = r_current + (2 * rAdj if r_taylor > r_current else -2 * rAdj)
        elif abs(r_taylor - r_current) > rAdj:
            # Small adjustment
            fin._r = r_current + (rAdj if r_taylor > r_current else -rAdj)
        else:
            fin._r = r_taylor
        
        fin._r = max(fin._r, 0)  # Non-negative
        
        # Bond interest rate (rBonds equation)
        rBonds_current = getattr(fin, '_rBonds', fin._r)
        muBonds = fin._muBonds  # Bond rate spread
        rhoBonds = getattr(fin, '_rhoBonds', 0.0)  # Debt feedback
        
        # Base bond rate
        rBonds_base = (1 - muBonds) * fin._r
        
        # Positive feedback on excessive public debt
        DebGDP = self._DebGDP if hasattr(self, '_DebGDP') else 0
        if DebGDP > 0:
            rBonds_base *= (1 + rhoBonds * DebGDP)
        
        # Smooth adjustment
        if abs(rBonds_base - rBonds_current) > 2 * rAdj:
            fin._rBonds = rBonds_current + (2 * rAdj if rBonds_base > rBonds_current else -2 * rAdj)
        elif abs(rBonds_base - rBonds_current) > rAdj:
            fin._rBonds = rBonds_current + (rAdj if rBonds_base > rBonds_current else -rAdj)
        else:
            fin._rBonds = rBonds_base
        
        fin._rBonds = max(fin._rBonds, 0)
        
        # Deposit interest rate (rD equation)
        fin._rD = (1 - fin._muD) * fin._r
        
        # Debt interest rate (rDeb equation)
        # Lower-bounded by expected inflation
        fin._rDeb = max((1 + fin._muDeb) * fin._r, piT)
        
        # Reserve interest rate (rRes equation)
        fin._rRes = (1 - fin._muRes) * fin._r
    
    def _consumption_planning(self):
        """Consumption sector planning phase"""
        sector = self.consumption_sector
        
        # Aggregate variables
        sector._D2e = 0.0
        sector._Q2 = 0.0
        sector._L2d = 0
        sector._Id = 0.0
        
        # Estimate total demand based on labor market
        labor = self.labor_market
        # Use potential labor force for initial demand estimation
        potential_wages = labor._Ls * labor._wAvg
        actual_wages = labor._L * labor._wAvg if labor._L > 0 else 0
        # Start with potential, move toward actual
        total_demand = max(potential_wages * 0.5 + actual_wages * 0.5, labor._Ls * labor._w0min)
        
        # Each firm plans (simplified for now)
        for firm in sector.firms:
            # Simple expectation: share of total demand
            market_share = 1.0 / len(sector.firms) if sector.firms else 1.0
            firm._D2e = max(total_demand * market_share, 10.0)
            firm._Q2d = firm._D2e / max(firm._p2, 0.1)  # Convert to quantity
            
            # Labor demand based on productivity
            labor_needed = int(firm._Q2d / max(firm._A2, 0.1))
            firm._L2d = max(labor_needed, 1)
            
            # Aggregate
            sector._D2e += firm._D2e
            sector._Q2 += firm._Q2d
            sector._L2d += firm._L2d
            sector._Id += 0.0  # Investment planning TBD
    
    def _capital_planning(self):
        """Capital sector planning phase"""
        sector = self.capital_sector
        
        # Aggregate variables
        sector._D1 = 0.0
        sector._Q1 = 0.0
        sector._L1d = 0
        
        # Firms do R&D (simplified innovation)
        for firm in sector.firms:
            # Simple R&D: small chance of productivity improvement each period
            if random_engine.uniform() < 0.1:  # 10% chance per period
                improvement = 1.0 + random_engine.uniform() * 0.05  # 0-5% improvement
                firm._Atau *= improvement
                firm._Btau *= improvement
                # Update price based on new productivity (lower cost)
                firm._p1 = firm._Btau * (1 + sector._mu1)
        
        # Machine demand from consumption sector (simplified for now)
        sector._D1 = max(self.consumption_sector._Id, len(self.consumption_sector.firms) * 0.1)
        
        # Each firm plans
        for firm in sector.firms:
            # Simple production planning
            firm._Q1 = max(sector._D1 / len(sector.firms) if sector.firms else 0, 0.5)
            # Labor demand based on production and productivity
            firm._L1d = max(int(firm._Q1 / max(firm._Btau, 0.1)), 1)
            
            # Aggregate
            sector._Q1 += firm._Q1
            sector._L1d += firm._L1d
    
    def _labor_market_matching(self):
        """Labor market search and match"""
        labor = self.labor_market
        cap_sector = self.capital_sector
        con_sector = self.consumption_sector
        
        # Count currently employed workers in each sector
        employed_sector1 = sum(1 for w in self.workers if w._employed == 1)
        employed_sector2 = sum(1 for w in self.workers if w._employed == 2)
        
        # Calculate job openings needed
        cap_sector._JO1 = max(0, cap_sector._L1d - employed_sector1)
        con_sector._JO2 = max(0, con_sector._L2d - employed_sector2)
        
        # Distribute job openings across firms (simplified)
        if cap_sector.firms:
            openings_per_firm1 = cap_sector._JO1 // len(cap_sector.firms)
            for firm in cap_sector.firms:
                firm._JO1 = openings_per_firm1
        
        if con_sector.firms:
            openings_per_firm2 = con_sector._JO2 // len(con_sector.firms)
            for firm in con_sector.firms:
                firm._JO2 = openings_per_firm2
        
        # Workers search for jobs (simple random matching for now)
        unemployed_workers = [w for w in self.workers if w._employed == 0]
        
        # Match unemployed workers to sector 1 openings
        hired_count1 = 0
        for worker in unemployed_workers[:cap_sector._JO1]:
            if cap_sector.firms:
                # Assign to a random firm with openings
                firm_idx = hired_count1 % len(cap_sector.firms)
                firm = cap_sector.firms[firm_idx]
                worker._employed = 1
                worker._employer = firm
                worker._Te = 0  # Reset tenure
                worker._wReal = labor._wAvg  # Set wage
                hired_count1 += 1
        
        # Match remaining unemployed to sector 2 openings
        unemployed_workers = [w for w in self.workers if w._employed == 0]
        hired_count2 = 0
        for worker in unemployed_workers[:con_sector._JO2]:
            if con_sector.firms:
                # Assign to a random firm with openings
                firm_idx = hired_count2 % len(con_sector.firms)
                firm = con_sector.firms[firm_idx]
                worker._employed = 2
                worker._employer = firm
                worker._Te = 0  # Reset tenure
                worker._wReal = labor._wAvg  # Set wage
                hired_count2 += 1
        
        # Update employment statistics
        # Scale up actual employed workers to notional labor force
        actual_employed = sum(1 for w in self.workers if w._employed > 0)
        labor._L = actual_employed * labor._Lscale
        
        # Unemployment rate based on notional labor force
        labor._Ue = safe_divide(labor._Ls - labor._L, labor._Ls)
    
    def _production_and_pricing(self):
        """Production execution and price setting"""
        cap_sector = self.capital_sector
        con_sector = self.consumption_sector
        
        # Update worker skills based on employment
        for worker in self.workers:
            if worker._employed > 0:
                # Worker is employed - skills improve with tenure
                worker._Te += 1
                # Simple learning: skills improve slightly each period employed
                worker._sT = min(worker._sT * 1.01, 2.0)  # Cap at 2x initial
            else:
                # Unemployed - skills deteriorate
                worker._sT = max(worker._sT * 0.99, 0.5)  # Floor at 0.5x initial
        
        # Capital sector production based on actual employment
        cap_sector._Q1e = 0.0
        for firm in cap_sector.firms:
            # Count workers in this firm
            workers_in_firm = sum(1 for w in self.workers if w._employed == 1 and getattr(w, '_employer', None) == firm)
            # Production based on workers and productivity
            firm._Q1e = workers_in_firm * firm._Btau * cap_sector._m1 if firm._Btau > 0 else 0.0
            cap_sector._Q1e += firm._Q1e
            
        prices1 = [f._p1 for f in cap_sector.firms if f._p1 > 0]
        cap_sector._p1avg = sum(prices1) / len(prices1) if prices1 else INIPROD
        
        # Consumption sector production based on actual employment
        con_sector._Q2e = 0.0
        for firm in con_sector.firms:
            # Count workers in this firm
            workers_in_firm = sum(1 for w in self.workers if w._employed == 2 and getattr(w, '_employer', None) == firm)
            # Production based on workers and productivity
            firm._Q2e = workers_in_firm * firm._A2 * con_sector._m2 if firm._A2 > 0 else 0.0
            con_sector._Q2e += firm._Q2e
            
        prices2 = [f._p2 for f in con_sector.firms if f._p2 > 0]
        con_sector._p2avg = sum(prices2) / len(prices2) if prices2 else INIPROD
    
    def _consumption_and_sales(self):
        """Match consumption demand with supply"""
        # Government expenditure
        self._compute_government_expenditure()
        
        # Compute desired consumption (Cd equation from fun_KS_country.h)
        self._compute_desired_consumption()
        
        # Match with supply
        con_sector = self.consumption_sector
        supply = con_sector._Q2e * con_sector._p2avg
        self._C = min(self._Cd + self._G, supply) if supply > 0 else 0.0
        con_sector._S2 = self._C
        
        # Update firm sales (distribute proportionally)
        if con_sector.firms and con_sector._Q2e > 0:
            for firm in con_sector.firms:
                firm_share = firm._Q2e / con_sector._Q2e if con_sector._Q2e > 0 else 0
                firm._S2 = self._C * firm_share
        
        # Forced savings (Sav equation)
        self._Sav = max(0, self._Cd + self._G - self._C)
        
        # Update accumulated savings (SavAcc equation)
        # Note: SavAcc is adjusted in Cd equation based on flagCons
        self._SavAcc += self._Sav
        
        # Inventories
        con_sector._N = max(0, supply - self._C)
        con_sector._dNnom = con_sector._N - self.read_sector('_N', con_sector, lag=1) if self._t > 1 else 0
    
    def _compute_desired_consumption(self):
        """
        Compute desired consumption (Cd equation from fun_KS_country.h)
        Nominal (monetary terms) desired aggregated consumption
        """
        labor = self.labor_market
        
        # Workers' net income after taxes
        # Wages + unemployment benefits + past bonuses/dividends - taxes
        W = labor._W if hasattr(labor, '_W') else 0  # Total wages
        G = self._G  # Unemployment benefits
        Bon_lag = self.read_sector('_Bon', labor, lag=1) if self._t > 1 else 0
        TaxW = labor._TaxW if hasattr(labor, '_TaxW') else 0
        Div_lag = self.read('_Div', lag=1) if self._t > 1 else 0
        TaxDiv = self._TaxDiv if hasattr(self, '_TaxDiv') else 0
        
        Cd = W + G + Bon_lag - TaxW + Div_lag - TaxDiv
        
        # Handle accumulated forced savings from the past
        if self._flagCons == 0:
            # Ignore unfilled past demand
            pass
        elif self._flagCons == 1:
            # Spend all savings
            Cd += self._SavAcc
            self._SavAcc = 0
        else:  # flagCons == 2 (default)
            # Slow spend of unfulfilled past consumption
            # Recover up to a limit of current consumption
            SavAcc = self._SavAcc
            Crec_limit = Cd * self._Crec  # Max recovery limit
            
            if SavAcc <= Crec_limit:
                # Fit in limit: use all savings
                Cd += SavAcc
                self._SavAcc = 0
            else:
                # No: spend the limit
                Cd += Crec_limit
                self._SavAcc -= Crec_limit
        
        self._Cd = max(Cd, 0)
    
    def _financial_operations(self):
        """Financial operations: profits, taxes, dividends"""
        cap_sector = self.capital_sector
        con_sector = self.consumption_sector
        fin_sector = self.financial_sector
        labor = self.labor_market
        
        # Update average wage based on actual wages
        total_wages = sum(w._wReal for w in self.workers if w._employed > 0)
        employed = sum(1 for w in self.workers if w._employed > 0)
        if employed > 0:
            labor._wAvg = total_wages / employed
            # Wage growth: small inflation + productivity gains
            wage_growth = 1.0 + 0.01  # 1% baseline growth
            for worker in self.workers:
                if worker._employed > 0:
                    worker._wReal *= wage_growth
        
        # Simplified profit calculation
        cap_sector._Pi1 = cap_sector._Q1e * cap_sector._p1avg * 0.1  # 10% margin
        con_sector._Pi2 = con_sector._S2 * 0.1
        fin_sector._PiB = 0.0  # Banks TBD
        
        # Taxes
        cap_sector._Tax1 = max(0, cap_sector._Pi1 * self._tr) if self._flagTax else 0
        con_sector._Tax2 = max(0, con_sector._Pi2 * self._tr) if self._flagTax else 0
        fin_sector._TaxB = max(0, fin_sector._PiB * self._tr) if self._flagTax else 0
        
        self._Tax = cap_sector._Tax1 + con_sector._Tax2 + fin_sector._TaxB
        
        # Dividends
        cap_sector._Div1 = max(0, cap_sector._Pi1 - cap_sector._Tax1) * 0.5
        con_sector._Div2 = max(0, con_sector._Pi2 - con_sector._Tax2) * 0.5
        fin_sector._DivB = max(0, fin_sector._PiB - fin_sector._TaxB) * 0.5
        
        self._Div = cap_sector._Div1 + con_sector._Div2 + fin_sector._DivB
        self._TaxDiv = self._Div * self._tr if self._flagTax >= 2 else 0
        
        # Net worth updates (simplified)
        cap_sector._NW1 = sum(f._NW1 for f in cap_sector.firms)
        con_sector._NW2 = sum(f._NW2 for f in con_sector.firms)
    
    def _government_operations(self):
        """
        Government fiscal operations
        Implements Tax, TaxDiv, Def, DefP, Deb equations from fun_KS_country.h
        """
        fin = self.financial_sector
        
        # Total tax revenue (Tax equation)
        cap_sector = self.capital_sector
        con_sector = self.consumption_sector
        self._Tax = cap_sector._Tax1 + con_sector._Tax2 + fin._TaxB
        
        # Dividend tax (TaxDiv equation)
        if self._flagTax >= 2:
            self._TaxDiv = self._Div * self._tr
        else:
            self._TaxDiv = 0.0
        
        # Add dividend tax to total tax
        self._Tax += self._TaxDiv
        
        # Primary deficit (DefP equation)
        # Government expenditure minus tax revenue
        self._DefP = self._G - self._Tax
        
        # Total deficit (Def equation)
        # Primary deficit plus interest payments on public debt
        rBonds = fin._rBonds if hasattr(fin, '_rBonds') else fin._r
        interest_payment = self._Deb * rBonds
        self._Def = self._DefP + interest_payment
        
        # Update public debt (Deb equation)
        # Debt increases by deficit amount
        self._Deb += self._Def
    
    def read_sector(self, attr: str, sector, lag: int = 0, default=0):
        """
        Read lagged value from a sector object
        
        Args:
            attr: Attribute name (with or without leading _)
            sector: Sector object
            lag: Number of periods back
            default: Default value if not available
            
        Returns:
            Value or default
        """
        if not attr.startswith('_'):
            attr = f'_{attr}'
        
        if lag == 0:
            return getattr(sector, attr, default)
        elif hasattr(sector, '_lags') and attr in sector._lags:
            if lag <= len(sector._lags[attr]):
                return sector._lags[attr][-lag]
        return default
    
    def _compute_aggregates(self):
        """
        Compute aggregate macroeconomic variables
        Implements GDPreal, GDPnom, A, dAb, dGDP, Creal equations
        """
        con_sector = self.consumption_sector
        cap_sector = self.capital_sector
        labor = self.labor_market
        
        # Real consumption (Creal equation)
        # Actual consumption in quantity terms using base price
        pC0 = con_sector._pC0  # Base price level
        self._Creal = safe_divide(self._C, con_sector._p2avg) * pC0 if con_sector._p2avg > 0 else 0
        
        # Real investment
        # Investment in capital goods
        Ireal = con_sector._Ireal if hasattr(con_sector, '_Ireal') else 0.0
        
        # Real GDP (GDPreal equation)
        # GDP = C + I + ΔN (in real terms)
        dNreal = 0.0
        if self._t > 1:
            N_current = con_sector._N
            N_lag = self.read_sector('_N', con_sector, lag=1, default=0)
            # Convert to real terms
            dNreal = safe_divide(N_current - N_lag, con_sector._p2avg) * pC0 if con_sector._p2avg > 0 else 0
        
        self._GDPreal = max(self._Creal + Ireal + dNreal, 1.0)
        
        # Nominal GDP (GDPnom equation)
        # GDP in current prices
        Inom = con_sector._Inom if hasattr(con_sector, '_Inom') else 0.0
        dNnom = con_sector._dNnom if hasattr(con_sector, '_dNnom') else 0.0
        self._GDPnom = max(self._C + Inom + dNnom, 1.0)
        
        # Overall productivity (A equation)
        # GDP per worker
        if labor._L > 0:
            self._A = safe_divide(self._GDPreal, labor._L)
        else:
            # Keep previous value if no workers
            self._A = self.read('_A', lag=1, default=INIPROD)
        
        # Productivity growth (dAb equation - bounded)
        if self._t > 1:
            A_lag = self.read('_A', lag=1, default=INIPROD)
            if A_lag > 0:
                dA = (self._A - A_lag) / A_lag
                # Bound by mLim
                mLim = self._mLim if self._mLim > 0 else float('inf')
                self._dAb = max(min(dA, mLim), -mLim)
            else:
                self._dAb = 0.0
        else:
            self._dAb = 0.0
        
        # GDP growth rate (dGDP equation - bounded)
        if self._t > 1:
            GDPreal_lag = self.read('_GDPreal', lag=1, default=1.0)
            if GDPreal_lag > 0:
                dGDP = (self._GDPreal - GDPreal_lag) / GDPreal_lag
                # Bound by mLim
                mLim = self._mLim if self._mLim > 0 else float('inf')
                self._dGDP = max(min(dGDP, mLim), -mLim)
            else:
                self._dGDP = 0.0
        else:
            self._dGDP = 0.0
        
        # Inflation (price level change)
        if self._t > 1:
            prev_price = self.read_sector('_p2avg', con_sector, lag=1, default=pC0)
            if prev_price > 0:
                self._inflation = (con_sector._p2avg - prev_price) / prev_price
            else:
                self._inflation = 0.0
        else:
            self._inflation = 0.0
        
        # Debt ratios (DebGDP, DefPgdp equations)
        self._DebGDP = safe_divide(self._Deb, self._GDPnom)
        self._DefPgdp = safe_divide(self._DefP, self._GDPnom)
        
        # Total dividends (Div equation)
        self._Div = cap_sector._Div1 + con_sector._Div2 + self.financial_sector._DivB
        
        # Total equity (Eq equation)
        # Sum of firm equities minus bad debt
        cap_equity = sum(getattr(f, '_NW1', 0) for f in cap_sector.firms)
        con_equity = sum(getattr(f, '_NW2', 0) for f in con_sector.firms)
        bank_equity = sum(getattr(b, '_NWb', 0) for b in self.financial_sector.banks)
        self._Eq = cap_equity + con_equity + bank_equity
    
    def _compute_government_expenditure(self):
        """
        Compute government expenditure (G equation from fun_KS_country.h)
        Government expenditure (exogenous demand)
        """
        labor = self.labor_market
        fin = self.financial_sector
        
        i = int(self._flagGovExp)  # Type of govt. expenditure
        j = int(self._flagFiscalRule)  # Fiscal rule to apply
        
        # Unemployed workers
        unemployed = labor._Ls - labor._L
        
        # Accumulated surplus at central bank
        DepoG_lag = self.read_sector('_DepoG', fin, lag=1) if self._t > 1 else 0
        
        # Base expenditure
        if i < 2:  # Work-or-die + minimum income
            G = unemployed * labor._w0min
        else:  # Pay unemployment benefit
            wU = labor._wU if hasattr(labor, '_wU') else labor._wAvg * 0.5
            G = unemployed * wU
        
        # Add worker training cost
        Gtrain = labor._Gtrain if hasattr(labor, '_Gtrain') else 0
        G += Gtrain
        
        # Growth adjustment
        if i == 1:
            G_lag = self.read('_G', lag=1) if self._t > 1 else G
            Gtrain_lag = self.read_sector('_Gtrain', labor, lag=1) if self._t > 1 else 0
            G += (1 + self._gG) * (G_lag - Gtrain_lag)
        
        # Use accumulated surplus if available
        if DepoG_lag > 0:
            if i == 3:  # Spend accumulated surplus
                Def_lag = self.read('_Def', lag=1) if self._t > 1 else 0
                G += min(DepoG_lag, max(0, -Def_lag))
        else:
            # Apply fiscal rule if conditions met
            Trule = getattr(fin, '_Trule', 10)
            if ((j == 1 or j == 3 or (j > 0 and self.read('_dGDP', lag=1, default=0) > 0)) 
                and self._t >= Trule):
                
                DebRule = getattr(fin, '_DebRule', 0.6)
                DefPrule = getattr(fin, '_DefPrule', 0.03)
                Tax_lag = self.read('_Tax', lag=1, default=0)
                Deb_lag = self.read('_Deb', lag=1, default=0)
                GDPnom_lag = self.read('_GDPnom', lag=1, default=1)
                
                # Debt rule applies?
                if j > 2 and safe_divide(Deb_lag, GDPnom_lag) > DebRule:
                    deltaDeb = getattr(fin, '_deltaDeb', 0.1)
                    target_deficit = -(Deb_lag - DebRule * GDPnom_lag) * deltaDeb
                    G = max(G, Tax_lag + target_deficit)
                elif j == 1 or j == 3:
                    # Primary deficit rule
                    G = max(G, Tax_lag - DefPrule * GDPnom_lag)
        
        self._G = max(G, 0)
    
    def _entry_exit(self):
        """Handle firm entry and exit"""
        # Simplified: no entry/exit in this basic version
        # Will be implemented in enhanced version
        pass
    
    def simulate(self, periods: int) -> Dict:
        """
        Run simulation for specified number of periods
        
        Args:
            periods: Number of time steps to simulate
            
        Returns:
            Dictionary of time series data
        """
        # Initialize if not done
        if not hasattr(self, '_initialized') or not self._initialized:
            self.initialize()
        
        # Storage for results
        results = {
            't': [],
            'GDPreal': [],
            'GDPnom': [],
            'Unemployment': [],
            'Inflation': [],
            'Debt': [],
            'Deficit': []
        }
        
        # Run simulation
        for t in range(periods):
            self.time_step()
            
            # Store results from statistics collector
            stats = self.statistics
            results['t'].append(self._t)
            results['GDPreal'].append(stats._GDPreal)
            results['GDPnom'].append(stats._GDPnom)
            results['Unemployment'].append(stats._Ue)  # Unemployment rate %
            results['Inflation'].append(stats._inflation * 100)  # Convert to %
            results['Debt'].append(self._Deb)
            results['Deficit'].append(self._Def)
        
        # Add scalar values for compatibility
        results['L'] = stats._L
        results['U'] = stats._Ue
        results['A'] = stats._A
        results['inflation'] = stats._inflation * 100
        
        return results
