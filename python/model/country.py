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
        
        # Create sectors
        self.capital_sector = CapitalSector(self)
        self.consumption_sector = ConsumptionSector(self)
        self.financial_sector = FinancialSector(self)
        self.labor_market = LaborMarket(self)
        
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
        Follows the equation sequencing from the C++ model
        """
        # Increment time
        self._t += 1
        
        # 1. Central bank updates interest rates
        self._update_interest_rates()
        
        # 2. Consumption firms: expectations, production, labor demand, investment
        self._consumption_planning()
        
        # 3. Capital firms: R&D, orders, production, labor demand
        self._capital_planning()
        
        # 4. Labor market: applications, matching, hiring
        self._labor_market_matching()
        
        # 5. Production and pricing
        self._production_and_pricing()
        
        # 6. Consumption and sales
        self._consumption_and_sales()
        
        # 7. Financial operations: profits, taxes, cash flows
        self._financial_operations()
        
        # 8. Government operations
        self._government_operations()
        
        # 9. Aggregate statistics
        self._compute_aggregates()
        
        # 10. Entry and exit
        self._entry_exit()
        
        # Update lag values for next period
        self.update_lags()
    
    def _update_interest_rates(self):
        """Update interest rate structure"""
        fin = self.financial_sector
        
        # Simple fixed rate for now (can be enhanced with Taylor rule)
        fin._r = fin._rT
        fin._rBonds = fin._r * (1 + fin._muBonds)
        fin._rD = fin._r * (1 + fin._muD)
        fin._rDeb = fin._r * (1 + fin._muDeb)
        fin._rRes = fin._r * (1 + fin._muRes)
    
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
        
        # Desired consumption from workers (using actual wages)
        labor = self.labor_market
        total_wages = sum(w._wReal for w in self.workers if w._employed > 0)
        self._Cd = total_wages if total_wages > 0 else 0.0
        
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
        
        # Forced savings
        self._Sav = max(0, self._Cd - self._C)
        self._SavAcc += self._Sav
        
        # Inventories
        con_sector._N = max(0, supply - self._C)
    
    def _financial_operations(self):
        """Financial operations: profits, taxes, dividends"""
        cap_sector = self.capital_sector
        con_sector = self.consumption_sector
        fin_sector = self.financial_sector
        
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
        """Government fiscal operations"""
        # Primary deficit
        self._DefP = self._G - self._Tax
        
        # Total deficit (including interest)
        interest_payment = self._Deb * self.financial_sector._rBonds
        self._Def = self._DefP + interest_payment
        
        # Update debt
        self._Deb += self._Def
    
    def _compute_aggregates(self):
        """Compute aggregate macroeconomic variables"""
        con_sector = self.consumption_sector
        
        # Real GDP (C + I in real terms)
        self._Creal = con_sector._Q2e * con_sector._pC0
        self._GDPreal = max(self._Creal + con_sector._Ireal, 1.0)
        
        # Nominal GDP
        self._GDPnom = max(self._C + con_sector._Inom + con_sector._dNnom, 1.0)
        
        # Overall productivity
        labor = self.labor_market
        self._A = safe_divide(self._GDPreal, labor._L) if labor._L > 0 else self._A
        
        # GDP growth
        if self._t > 1:
            gdp_prev = self.read('_GDPreal', lag=1)
            if gdp_prev and gdp_prev > 0:
                self._dGDP = math.log(self._GDPreal) - math.log(gdp_prev)
        
        # Debt ratios
        self._DebGDP = safe_divide(self._Deb, self._GDPnom)
        self._DefPgdp = safe_divide(self._DefP, self._GDPnom)
    
    def _compute_government_expenditure(self):
        """Compute government expenditure"""
        labor = self.labor_market
        
        # Unemployment benefits
        unemployed = labor._Ls - labor._L
        
        if self._flagGovExp < 2:
            # Minimum income
            self._G = unemployed * labor._w0min
        else:
            # Unemployment benefits
            wU = labor._wAvg * 0.5  # 50% of average wage
            self._G = unemployed * wU
        
        # Add training costs
        self._G += labor._Gtrain if hasattr(labor, '_Gtrain') else 0
        
        # Growth adjustment
        if self._flagGovExp == 1:
            prev_G = self.read('_G', lag=1)
            if prev_G:
                self._G = prev_G * (1 + self._gG)
    
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
            
            # Store results
            results['t'].append(self._t)
            results['GDPreal'].append(self._GDPreal)
            results['GDPnom'].append(self._GDPnom)
            results['Unemployment'].append(self.labor_market._Ue)
            results['Inflation'].append(0.0)  # TBD
            results['Debt'].append(self._Deb)
            results['Deficit'].append(self._Def)
        
        return results
