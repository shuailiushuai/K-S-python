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
        self._L1dRD = 0                   # R&D labor demand
        self._L1rd = 0                    # R&D labor employed
        self._JO1 = 0                     # Job openings
        self._p1avg = 0.0                 # Average machine price
        self._Pi1 = 0.0                   # Sector profits
        self._Tax1 = 0.0                  # Sector taxes
        self._W1 = 0.0                    # Wages paid
        self._S1 = 0.0                    # Sales revenue
        self._NW1 = 0.0                   # Sector net worth
        self._Deb1 = 0.0                  # Sector debt
        self._Div1 = 0.0                  # Sector dividends
        self._Eq1 = 0.0                   # Sector equity
        self._cEntry1 = 0.0               # Entry cost
        self._cExit1 = 0.0                # Exit credit
        self._MC1 = 0.0                   # Market conditions index
        self._entry1exit = 0              # Net entry (entry - exit)
        self._fires1 = 0                  # Workers fired
        self._hires1 = 0                  # Workers hired
        self._quits1 = 0                  # Workers quit
        self._retires1 = 0                # Workers retired
        
        # Firms list
        self.firms: List[Firm1] = []
    
    def compute_aggregates(self):
        """
        Compute sector-level aggregates from firm-level variables
        Implements aggregation equations from fun_KS_capital.h
        """
        # Reset aggregates
        self._D1 = 0.0
        self._Q1 = 0.0
        self._Q1e = 0.0
        self._L1d = 0
        self._L1dRD = 0
        self._Pi1 = 0.0
        self._Tax1 = 0.0
        self._W1 = 0.0
        self._S1 = 0.0
        self._NW1 = 0.0
        self._Deb1 = 0.0
        self._Div1 = 0.0
        self._Eq1 = 0.0
        
        n_firms = 0
        total_price = 0.0
        
        # Aggregate firm-level variables
        for firm in self.firms:
            self._D1 += getattr(firm, '_D1', 0.0)
            self._Q1 += getattr(firm, '_Q1', 0.0)
            self._Q1e += getattr(firm, '_Q1e', 0.0)
            self._L1d += getattr(firm, '_L1d', 0)
            self._L1dRD += getattr(firm, '_L1dRD', 0)
            self._Pi1 += getattr(firm, '_Pi1', 0.0)
            self._Tax1 += getattr(firm, '_Tax1', 0.0)
            self._W1 += getattr(firm, '_W1', 0.0)
            self._S1 += getattr(firm, '_S1', 0.0)
            self._NW1 += getattr(firm, '_NW1', 0.0)
            self._Deb1 += getattr(firm, '_Deb1', 0.0)
            self._Div1 += getattr(firm, '_Div1', 0.0)
            self._Eq1 += getattr(firm, '_Eq1', 0.0)
            
            total_price += getattr(firm, '_p1', 1.0)
            n_firms += 1
        
        # Compute average price
        self._p1avg = safe_divide(total_price, n_firms, 1.0)
        
        # Store aggregates
        self.write("D1", self._D1)
        self.write("Q1", self._Q1)
        self.write("Q1e", self._Q1e)
        self.write("L1d", self._L1d)
        self.write("L1dRD", self._L1dRD)
        self.write("Pi1", self._Pi1)
        self.write("Tax1", self._Tax1)
        self.write("W1", self._W1)
        self.write("S1", self._S1)
        self.write("NW1", self._NW1)
        self.write("Deb1", self._Deb1)
        self.write("Div1", self._Div1)
        self.write("Eq1", self._Eq1)
        self.write("p1avg", self._p1avg)
    
    def compute_MC1(self) -> float:
        """
        Market entry conditions index in capital-good sector
        MC1 = log(max(NW1_t-1, 0) + 1) - log(Deb1_t-1 + 1)
        """
        NW1_lag = self.read("NW1", 1)
        Deb1_lag = self.read("Deb1", 1)
        
        self._MC1 = math.log(max(NW1_lag, 0) + 1) - math.log(Deb1_lag + 1)
        self.write("MC1", self._MC1)
        return self._MC1
    
    def compute_wage_average(self, w2avg_fallback: float = 1.0) -> float:
        """
        Compute average wage in capital sector (w1avg equation from fun_KS_capital.h)
        Average wage paid by firms in capital-good sector
        
        Args:
            w2avg_fallback: Fallback wage if no workers in sector 1
        
        Returns:
            Average wage in sector 1
        """
        L1 = self._L1d  # Workers in sector 1
        
        if L1 == 0:
            # No workers - use sector 2 wage as proxy
            w1avg = w2avg_fallback
        else:
            w1avg = safe_divide(self._W1, L1, w2avg_fallback)
        
        # Only update if positive
        if w1avg > 0:
            self._w1avg = w1avg
            self.write("w1avg", w1avg)
        
        return self._w1avg if hasattr(self, '_w1avg') else w2avg_fallback
    
    def compute_min_tenure_skill(self, workers: List) -> float:
        """
        Compute minimum tenure skill in sector 1 (sT1min equation from fun_KS_capital.h)
        Minimum tenure skill of workers in capital-good sector
        
        Args:
            workers: List of all workers
        
        Returns:
            Minimum tenure skill
        """
        # Find workers employed in sector 1
        sector1_skills = []
        for worker in workers:
            # Check if worker is in capital sector (simplified - may need firm reference)
            if hasattr(worker, '_sT'):
                sector1_skills.append(worker._sT)
        
        if sector1_skills:
            sT1min = min(sector1_skills)
        else:
            sT1min = INISKILL  # Default if no workers
        
        self._sT1min = sT1min
        self.write("sT1min", sT1min)
        return sT1min


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
        self._Q2d = 0.0                   # Desired production
        self._Q2e = 0.0                   # Effective production
        self._S2 = 0.0                    # Sales
        self._N = 0.0                     # Inventories
        self._dNnom = 0.0                 # Change in inventories (nominal)
        self._L2d = 0                     # Labor demand
        self._L2 = 0                      # Actual labor employed
        self._JO2 = 0                     # Job openings
        self._Id = 0.0                    # Desired investment
        self._EI = 0.0                    # Expansion investment
        self._SI = 0.0                    # Substitution investment
        self._CI = 0.0                    # Canceled investment
        self._Inom = 0.0                  # Investment (nominal)
        self._Ireal = 0.0                 # Investment (real)
        self._K = 0.0                     # Capital stock
        self._Kd = 0.0                    # Desired capital
        self._Knom = 0                    # Number of machines
        self._p2avg = 0.0                 # Average goods price
        self._pC0 = 1.0                   # Initial price level
        self._CPI = 1.0                   # Consumer price index
        self._dCPI = 0.0                  # CPI inflation
        self._Pi2 = 0.0                   # Sector profits
        self._Tax2 = 0.0                  # Sector taxes
        self._W2 = 0.0                    # Wages paid
        self._Bon2 = 0.0                  # Bonuses paid
        self._NW2 = 0.0                   # Sector net worth
        self._Deb2 = 0.0                  # Sector debt
        self._Div2 = 0.0                  # Sector dividends
        self._Eq2 = 0.0                   # Sector equity
        self._cEntry2 = 0.0               # Entry cost
        self._cExit2 = 0.0                # Exit credit
        self._MC2 = 0.0                   # Market conditions index
        self._entry2exit = 0              # Net entry (entry - exit)
        self._fires2 = 0                  # Workers fired
        self._hires2 = 0                  # Workers hired
        self._quits2 = 0                  # Workers quit
        self._retires2 = 0                # Workers retired
        self._w2avg = 0.0                 # Average wage
        self._w2oAvg = 0.0                # Average wage offered
        self._A2 = 0.0                    # Average productivity
        
        # Firms list
        self.firms: List[Firm2] = []
    
    def compute_aggregates(self):
        """
        Compute sector-level aggregates from firm-level variables
        Implements aggregation equations from fun_KS_consumption.h
        """
        # Reset aggregates
        self._Q2 = 0.0
        self._Q2d = 0.0
        self._Q2e = 0.0
        self._D2e = 0.0
        self._D2d = 0.0
        self._S2 = 0.0
        self._N = 0.0
        self._L2d = 0
        self._L2 = 0
        self._EI = 0.0
        self._SI = 0.0
        self._CI = 0.0
        self._K = 0.0
        self._Kd = 0.0
        self._Knom = 0
        self._Pi2 = 0.0
        self._Tax2 = 0.0
        self._W2 = 0.0
        self._Bon2 = 0.0
        self._NW2 = 0.0
        self._Deb2 = 0.0
        self._Div2 = 0.0
        self._Eq2 = 0.0
        
        n_firms = 0
        total_price = 0.0
        total_wage = 0.0
        total_wage_offer = 0.0
        total_productivity = 0.0
        
        # Aggregate firm-level variables
        for firm in self.firms:
            self._Q2 += getattr(firm, '_Q2', 0.0)
            self._Q2d += getattr(firm, '_Q2d', 0.0)
            self._Q2e += getattr(firm, '_Q2e', 0.0)
            self._D2e += getattr(firm, '_D2e', 0.0)
            self._S2 += getattr(firm, '_S2', 0.0)
            self._N += getattr(firm, '_N', 0.0)
            self._L2d += getattr(firm, '_L2d', 0)
            self._L2 += getattr(firm, '_L2', 0)
            self._EI += getattr(firm, '_EI', 0.0)
            self._SI += getattr(firm, '_SI', 0.0)
            self._CI += getattr(firm, '_CI', 0.0)
            self._K += getattr(firm, '_K', 0.0)
            self._Kd += getattr(firm, '_Kd', 0.0)
            self._Knom += getattr(firm, '_Knom', 0)
            self._Pi2 += getattr(firm, '_Pi2', 0.0)
            self._Tax2 += getattr(firm, '_Tax2', 0.0)
            self._W2 += getattr(firm, '_W2', 0.0)
            self._Bon2 += getattr(firm, '_Bon2', 0.0)
            self._NW2 += getattr(firm, '_NW2', 0.0)
            self._Deb2 += getattr(firm, '_Deb2', 0.0)
            self._Div2 += getattr(firm, '_Div2', 0.0)
            self._Eq2 += getattr(firm, '_Eq2', 0.0)
            
            total_price += getattr(firm, '_p2', 1.0)
            total_wage += getattr(firm, '_w2avg', 0.0)
            total_wage_offer += getattr(firm, '_w2o', 0.0)
            total_productivity += getattr(firm, '_A2', INIPROD)
            n_firms += 1
        
        # Compute averages
        self._p2avg = safe_divide(total_price, n_firms, 1.0)
        self._w2avg = safe_divide(total_wage, n_firms, 1.0)
        self._w2oAvg = safe_divide(total_wage_offer, n_firms, 1.0)
        self._A2 = safe_divide(total_productivity, n_firms, INIPROD)
        
        # Compute desired demand aggregate
        self._D2d = self._D2e  # Simplification for now
        
        # Compute investment aggregates
        self._Id = self._EI + self._SI
        self._Inom = self._Id  # Nominal = desired for now
        
        # Store aggregates
        self.write("Q2", self._Q2)
        self.write("Q2d", self._Q2d)
        self.write("Q2e", self._Q2e)
        self.write("D2e", self._D2e)
        self.write("D2d", self._D2d)
        self.write("S2", self._S2)
        self.write("N", self._N)
        self.write("L2d", self._L2d)
        self.write("L2", self._L2)
        self.write("EI", self._EI)
        self.write("SI", self._SI)
        self.write("CI", self._CI)
        self.write("K", self._K)
        self.write("Kd", self._Kd)
        self.write("Knom", self._Knom)
        self.write("Pi2", self._Pi2)
        self.write("Tax2", self._Tax2)
        self.write("W2", self._W2)
        self.write("Bon2", self._Bon2)
        self.write("NW2", self._NW2)
        self.write("Deb2", self._Deb2)
        self.write("Div2", self._Div2)
        self.write("Eq2", self._Eq2)
        self.write("p2avg", self._p2avg)
        self.write("w2avg", self._w2avg)
        self.write("w2oAvg", self._w2oAvg)
        self.write("A2", self._A2)
    
    def compute_MC2(self) -> float:
        """
        Market entry conditions index in consumption-good sector
        MC2 = log(max(NW2_t-1, 0) + 1) - log(Deb2_t-1 + 1)
        """
        NW2_lag = self.read("NW2", 1)
        Deb2_lag = self.read("Deb2", 1)
        
        self._MC2 = math.log(max(NW2_lag, 0) + 1) - math.log(Deb2_lag + 1)
        self.write("MC2", self._MC2)
        return self._MC2
    
    def allocate_demand_to_firms(self, nominal_demand: float) -> float:
        """
        Allocate demand to firms based on market share and available supply
        Implements the full D2 allocation algorithm from fun_KS_consumption.h
        
        This algorithm cycles through firms allocating demand proportionally
        to market share until all demand is fulfilled or no more supply exists.
        It tracks unfilled demand (_l2) for each firm.
        
        Args:
            nominal_demand: Total nominal demand (Cd + G)
        
        Returns:
            Total real demand fulfilled (in units, not monetary)
        """
        k = len(self.firms)  # Number of firms
        
        if k == 0:
            return 0.0
        
        # Create temporary vectors for shares, prices, supply, and firm objects
        f2 = []  # Market shares
        p2 = []  # Prices
        sup2 = []  # Available supply (Q2e + inventory from last period)
        firm_refs = []  # Firm references
        
        # Initialize vectors and reset firm demand accumulators
        for firm in self.firms:
            # Get firm's available supply (current production + last period inventory)
            Q2e = getattr(firm, '_Q2e', 0.0)
            N_lag = firm.read('_N', 1)
            supply = Q2e + N_lag
            
            sup2.append(supply)
            f2.append(getattr(firm, '_f2', 0.0))  # Market share
            p2.append(getattr(firm, '_p2', 1.0))  # Price
            firm_refs.append(firm)
            
            # Reset demand fulfilled accumulator
            firm._D2 = 0.0
            # Assume no unsatisfied demand initially
            firm._l2 = 0.0
        
        # Cycle through firms until all demand is allocated or no more product to sell
        total_fulfilled = 0.0  # Fulfilled demand accumulator (in real units)
        remaining_demand = nominal_demand  # Remaining unallocated $ demand
        iteration = 0
        
        while remaining_demand > 0.01:  # Small threshold to avoid floating point issues
            prev_remaining = remaining_demand
            current_remaining = remaining_demand  # Copy for this iteration
            unallocated_shares = 0.0  # Shares yet unallocated
            
            # Process each firm
            for j in range(k):
                if f2[j] > 0:  # Firm has demand to supply
                    if sup2[j] > 0:  # Product to supply?
                        # Firm's $ demand allocation based on market share
                        # IMPORTANT: Use current_remaining (fixed at loop start), not remaining_demand
                        firm_demand_nominal = current_remaining * f2[j]
                        # Convert to real units
                        firm_demand_real = firm_demand_nominal / p2[j] if p2[j] > 0 else 0
                        
                        if firm_demand_real <= sup2[j]:  # Can supply all demanded?
                            # Supply all demanded
                            firm_refs[j]._D2 += firm_demand_real
                            
                            total_fulfilled += firm_demand_real
                            remaining_demand -= firm_demand_nominal
                            unallocated_shares += f2[j]
                            sup2[j] -= firm_demand_real  # Make supplied units unavailable
                        else:
                            # Cannot supply all demanded - supply all available
                            # Track unsatisfied demand on first iteration only
                            if iteration == 0:
                                firm_refs[j]._l2 = firm_demand_real - sup2[j]
                            
                            # Supply all available
                            firm_refs[j]._D2 += sup2[j]
                            
                            total_fulfilled += sup2[j]
                            remaining_demand -= sup2[j] * p2[j]
                            # Nothing else to supply from this firm
                            f2[j] = 0.0
                            sup2[j] = 0.0
                    else:
                        # No product to supply
                        f2[j] = 0.0
            
            # Rescale remaining firms' market shares
            if unallocated_shares > 0:
                for j in range(k):
                    f2[j] /= unallocated_shares
            else:
                # No more firms with supply
                break
            
            # Check if we made progress
            if abs(remaining_demand - prev_remaining) < 0.001:
                # No significant progress, exit to avoid infinite loop
                break
            
            iteration += 1
            # Safety check to prevent infinite loops
            if iteration > 1000:
                break
        
        return total_fulfilled


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
        self._BadDeb = 0.0                # Total bad debt
        self._BadDeb1 = 0.0               # Bad debt sector 1
        self._BadDeb2 = 0.0               # Bad debt sector 2
        self._Loans = 0.0                 # Total loans
        self._LoansCB = 0.0               # Loans from central bank
        self._Depo = 0.0                  # Total deposits
        self._Res = 0.0                   # Total reserves
        self._ExRes = 0.0                 # Excess reserves
        self._NWb = 0.0                   # Banking sector net worth
        
        # Banks list
        self.banks: List[Bank] = []
    
    def compute_aggregates(self):
        """
        Compute financial sector aggregates from bank-level variables
        Implements aggregation equations from fun_KS_financial.h
        """
        # Reset aggregates
        self._PiB = 0.0
        self._TaxB = 0.0
        self._DivB = 0.0
        self._BondsB = 0.0
        self._Cl = 0
        BadDeb = 0.0
        BadDeb1 = 0.0
        BadDeb2 = 0.0
        Loans = 0.0
        LoansCB = 0.0
        Depo = 0.0
        Res = 0.0
        ExRes = 0.0
        NWb = 0.0
        Gbail = 0.0
        
        # Aggregate bank-level variables
        for bank in self.banks:
            self._PiB += getattr(bank, '_PiB', 0.0)
            self._TaxB += getattr(bank, '_TaxB', 0.0)
            self._DivB += getattr(bank, '_DivB', 0.0)
            self._BondsB += getattr(bank, '_BondsB', 0.0)
            self._Cl += getattr(bank, '_Cl', 0)
            BadDeb1 += getattr(bank, '_BadDeb1', 0.0)
            BadDeb2 += getattr(bank, '_BadDeb2', 0.0)
            Loans += getattr(bank, '_Loans', 0.0)
            LoansCB += getattr(bank, '_LoansCB', 0.0)
            Depo += getattr(bank, '_Depo', 0.0)
            Res += getattr(bank, '_Res', 0.0)
            ExRes += getattr(bank, '_ExRes', 0.0)
            NWb += getattr(bank, '_NWb', 0.0)
            Gbail += getattr(bank, '_Gbail', 0.0)
        
        # Store aggregates
        self.write("BadDeb", BadDeb1 + BadDeb2)
        self.write("BadDeb1", BadDeb1)
        self.write("BadDeb2", BadDeb2)
        self.write("Loans", Loans)
        self.write("LoansCB", LoansCB)
        self.write("Depo", Depo)
        self.write("Res", Res)
        self.write("ExRes", ExRes)
        self.write("NWb", NWb)
        self.write("Gbail", Gbail)
        
        # Store as instance variables for easy access
        self._BadDeb = BadDeb1 + BadDeb2
        self._BadDeb1 = BadDeb1
        self._BadDeb2 = BadDeb2
        self._Loans = Loans
        self._LoansCB = LoansCB
        self._Depo = Depo
        self._Res = Res
        self._ExRes = ExRes
        self._NWb = NWb
        self._Gbail = Gbail
        
        # Central bank profits (simplified: interest on bonds held by CB)
        BondsCB = getattr(self, '_BondsCB', 0.0)
        rBonds = getattr(self, '_rBonds', 0.02)
        PiCB = BondsCB * rBonds
        self._PiCB = PiCB
        self.write("PiCB", PiCB)
    
    def compute_interest_rates(self):
        """
        Compute interest rate structure based on prime rate
        Implements equations from fun_KS_financial.h
        """
        r = self._r  # Prime rate
        
        # Interest rate structure
        self._rBonds = r + self._muBonds      # Bond rate
        self._rD = r + self._muD              # Deposit rate
        self._rDeb = r + self._muDeb          # Debt rate
        self._rRes = r + self._muRes          # Reserve rate
        
        # Store rates
        self.write("rBonds", self._rBonds)
        self.write("rD", self._rD)
        self.write("rDeb", self._rDeb)
        self.write("rRes", self._rRes)
    
    def compute_prime_rate(self, CPI: float, U: float) -> float:
        """
        Compute prime interest rate using Taylor rule
        r(t) = r* + phi_pi * (pi(t) - pi*) - phi_u * (u(t) - u*)
        
        Args:
            CPI: Consumer price index
            U: Unemployment rate
        
        Returns:
            Prime interest rate
        """
        # Taylor rule parameters (can be configured)
        r_star = getattr(self, '_rT', 0.03)    # Target rate
        pi_star = getattr(self, '_piT', 0.02)   # Target inflation
        u_star = getattr(self, '_uT', 0.05)     # Target unemployment
        phi_pi = getattr(self, '_phiPi', 1.5)   # Inflation response
        phi_u = getattr(self, '_phiU', 0.5)     # Unemployment response
        
        # Compute inflation rate
        CPI_lag = self.read("_CPI", 1)
        if CPI_lag > 0:
            pi = (CPI - CPI_lag) / CPI_lag
        else:
            pi = 0.0
        
        # Taylor rule
        r = r_star + phi_pi * (pi - pi_star) - phi_u * (U - u_star)
        
        # Bound interest rate (non-negative)
        r = max(r, 0.0)
        
        self._r = r
        self.write("r", r)
        return r
    
    def compute_bond_supply(self, Def: float) -> float:
        """
        Compute government bond supply
        
        Args:
            Def: Government deficit
        
        Returns:
            Bond supply
        """
        # Government finances deficit through bond issuance
        BS = max(Def, 0.0)  # Only positive deficit creates bond supply
        
        self.write("BS", BS)
        return BS


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
        
        # Initial equal market share for each firm
        initial_market_share = 1.0 / F20 if F20 > 0 else 0.0
        
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
            firm._f2 = initial_market_share  # CRITICAL: Initialize market share
            firm._N = 0.0  # Initial inventory
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
        
        CRITICAL SEQUENCING: Wages must be computed BEFORE consumption demand!
        
        Correct sequence based on C++ implementation:
        1. Regime change (if scheduled)
        2. Central bank updates interest rates (r, rDeb, rBonds)
        3. Consumption sector plans (D2e, Q2, L2d, Id)
        4. Capital sector plans (D1, Q1, L1d)
        5. Labor market matching (appl, JO1, JO2, L)
        6. Production and pricing (Q1e, Q2e, p1avg, p2avg)
        7. Wage computation (W, wAvg) - MUST BE BEFORE consumption demand
        8. Consumption and sales (G, Cd, D2d, D2, N, Sav)
        9. Financial operations (Pi1, Pi2, PiB, Tax1, Tax2, TaxB, NW1, NW2)
        10. Government operations (Tax, Def, Deb)
        11. Aggregates (GDPreal, GDPnom)
        12. Entry/exit (entryExit)
        """
        # Increment time
        self._t += 1
        
        # 0. Check for regime change
        self._check_regime_change()
        
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
        
        # 6. Compute wages (CRITICAL: must be before consumption demand)
        self._compute_wages()
        
        # 7. Government expenditure and consumption/sales
        self._consumption_and_sales()
        
        # 8. Financial operations: profits, taxes, cash flows
        self._financial_operations()
        
        # 9. Government operations: taxes, deficit, debt
        self._government_operations()
        
        # 10. Compute aggregate statistics
        self._compute_aggregates()
        
        # 11. Entry and exit
        self._entry_exit()
        
        # Update statistics collector
        self.statistics.compute_all_statistics(self)
        
        # Update lag values for next period
        self.update_lags()
    
    def _check_regime_change(self):
        """
        Check and apply regime change (regChg equation)
        Produces a labor market regime change at the time step defined in TregChg
        """
        if self._TregChg <= 0 or self._TregChg == 9999:
            return  # No regime change
        
        if self._t != self._TregChg:
            return  # Not time for regime change yet
        
        # Apply regime change parameters
        # Change flags and parameters to post-change values
        
        # Global parameters
        if hasattr(self, '_flagSearchModeChg'):
            self._flagSearchMode = self._flagSearchModeChg
        
        if hasattr(self, '_flagIndexMinWageChg'):
            self._flagIndexMinWage = self._flagIndexMinWageChg
        
        if hasattr(self, '_flagHireSeqChg'):
            self._flagHireSeq = self._flagHireSeqChg
        
        if hasattr(self, '_flagHireOrder1Chg'):
            self._flagHireOrder1 = self._flagHireOrder1Chg
        
        if hasattr(self, '_flagFireOrder1Chg'):
            self._flagFireOrder1 = self._flagFireOrder1Chg
        
        if hasattr(self, '_trChg'):
            self._tr = self._trChg
        
        # Financial sector parameters
        fin = self.financial_sector
        if hasattr(fin, '_LambdaChg'):
            fin._Lambda = fin._LambdaChg
        
        if hasattr(fin, '_muResChg'):
            fin._muRes = fin._muResChg
        
        if hasattr(fin, '_tauBchg'):
            fin._tauB = fin._tauBchg
        
        if hasattr(fin, '_rTchg'):
            fin._rT = fin._rTchg
        
        # Labor market parameters
        labor = self.labor_market
        if hasattr(labor, '_TsChg'):
            labor._Ts = labor._TsChg
        
        if hasattr(labor, '_phiChg'):
            labor._phi = labor._phiChg
        
        if hasattr(labor, '_omegaPosChg'):
            labor._omega = labor._omegaPosChg
        
        # Consumption sector parameters
        con_sector = self.consumption_sector
        if hasattr(con_sector, '_e0Chg'):
            con_sector._e0 = con_sector._e0Chg
        
        if hasattr(con_sector, '_mu20Chg'):
            con_sector._mu20 = con_sector._mu20Chg
        
        # Firm-specific parameters (apply to all firms)
        if hasattr(con_sector, '_flagHireOrder2Chg'):
            for firm in con_sector.firms:
                firm._flagHireOrder2 = con_sector._flagHireOrder2Chg
        
        if hasattr(con_sector, '_flagFireOrder2Chg'):
            for firm in con_sector.firms:
                firm._flagFireOrder2 = con_sector._flagFireOrder2Chg
        
        if hasattr(con_sector, '_flagFireRuleChg'):
            for firm in con_sector.firms:
                firm._flagFireRule = con_sector._flagFireRuleChg
    
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
            firm._L1 = workers_in_firm  # Update firm's worker count
            
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
            firm._L2 = workers_in_firm  # Update firm's worker count
            firm.write("_L2", workers_in_firm)  # Write to lag storage
            
            # Compute average wage for this firm's workers
            if workers_in_firm > 0:
                firm_worker_wages = [w._wReal for w in self.workers if w._employed == 2 and getattr(w, '_employer', None) == firm]
                firm._w2avg = sum(firm_worker_wages) / len(firm_worker_wages)
            else:
                firm._w2avg = self.labor_market._wAvg
            firm.write("_w2avg", firm._w2avg)  # Write to lag storage
            
            # Production based on workers and productivity
            firm._Q2e = workers_in_firm * firm._A2 * con_sector._m2 if firm._A2 > 0 else 0.0
            con_sector._Q2e += firm._Q2e
            
        prices2 = [f._p2 for f in con_sector.firms if f._p2 > 0]
        con_sector._p2avg = sum(prices2) / len(prices2) if prices2 else INIPROD
    
    def _compute_wages(self):
        """
        Compute total wages paid to workers (W equation)
        
        CRITICAL: This must be called BEFORE consumption demand calculation,
        since Cd depends on W (wages paid).
        
        Implements the W equation from fun_KS_labor.h
        """
        labor = self.labor_market
        
        # Compute average wage based on actual wages
        total_wages = sum(w._wReal for w in self.workers if w._employed > 0)
        employed = sum(1 for w in self.workers if w._employed > 0)
        
        if employed > 0:
            # Average wage across all employed workers
            labor._wAvg = total_wages / employed
            
            # Small wage growth each period: inflation + productivity
            # This provides dynamics to wage levels over time
            wage_growth = 1.0 + 0.01  # 1% baseline growth per period
            for worker in self.workers:
                if worker._employed > 0:
                    worker._wReal *= wage_growth
        
        # Total wages paid (W equation)
        # Scale up from actual workers to notional labor force
        labor._W = total_wages * labor._Lscale
    
    def _consumption_and_sales(self):
        """Match consumption demand with supply"""
        # Government expenditure
        self._compute_government_expenditure()
        
        # Compute desired consumption (Cd equation from fun_KS_country.h)
        self._compute_desired_consumption()
        
        # Full D2 demand allocation algorithm with unfilled demand tracking
        con_sector = self.consumption_sector
        total_demand_nominal = self._Cd + self._G  # Nominal demand
        
        # Allocate demand to firms using full D2 algorithm (from fun_KS_consumption.h)
        total_demand_fulfilled = con_sector.allocate_demand_to_firms(total_demand_nominal)
        
        # Compute sales revenue (_S2) for each firm AFTER allocation completes
        # This matches the C++ equation: _S2 = _p2 * _D2
        for firm in con_sector.firms:
            firm._S2 = firm._p2 * firm._D2
            firm.write("_S2", firm._S2)  # Write to lag storage for profit calculation
        
        # Actual consumption (in real terms)
        self._C = total_demand_fulfilled * con_sector._p2avg
        
        # Forced savings (Sav equation)
        self._Sav = max(0, total_demand_nominal - self._C)
        
        # Update accumulated savings (SavAcc equation)
        # Note: SavAcc is adjusted in Cd equation based on flagCons
        self._SavAcc += self._Sav
        
        # Update sector-level sales and inventories
        con_sector._S2 = sum(firm._S2 for firm in con_sector.firms)
        con_sector._D2 = total_demand_fulfilled
        
        # Inventories
        total_supply = sum(firm._Q2e + getattr(firm, '_N', 0) for firm in con_sector.firms)
        con_sector._N = max(0, total_supply - total_demand_fulfilled)
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
        """
        Financial operations: profits, taxes, dividends
        Includes aggregate financial statistics
        
        NOTE: Wages (W, wAvg) are now computed in _compute_wages() which is
        called before this method, so they are available here.
        """
        cap_sector = self.capital_sector
        con_sector = self.consumption_sector
        fin_sector = self.financial_sector
        labor = self.labor_market
        
        # Compute firm-level financial variables for consumption sector
        # This matches the C++ equation sequence: _W2 -> _i2 -> _iD2 -> _Pi2
        rDeb = fin_sector._rDeb if hasattr(fin_sector, '_rDeb') else 0.03
        rD = fin_sector._rD if hasattr(fin_sector, '_rD') else 0.01
        kConst = fin_sector._kConst if hasattr(fin_sector, '_kConst') else 0.5
        
        for firm in con_sector.firms:
            # Compute total wages (_W2)
            firm.compute_total_wages()
            
            # Compute interest on debt (_i2)
            firm.compute_interest_on_debt(rDeb, kConst)
            
            # Compute interest from deposits (_iD2)
            firm.compute_interest_from_deposits(rD)
            
            # Compute profits (_Pi2)
            firm.compute_profits()
        
        # Aggregate sector-level profits
        con_sector._Pi2 = sum(f._Pi2 for f in con_sector.firms)
        
        # Compute firm-level financial variables for capital sector
        # This matches the C++ equation sequence: _S1 -> _W1 -> _i1 -> _iD1 -> _Pi1
        for firm in cap_sector.firms:
            # Compute sales revenue (_S1)
            firm.compute_sales_revenue()
            
            # Compute total wages (_W1)
            firm.compute_total_wages()
            
            # Compute interest on debt (_i1)
            firm.compute_interest_on_debt(rDeb, kConst)
            
            # Compute interest from deposits (_iD1)
            firm.compute_interest_from_deposits(rD)
            
            # Compute profits (_Pi1)
            firm.compute_profits()
        
        # Aggregate sector-level profits
        cap_sector._Pi1 = sum(f._Pi1 for f in cap_sector.firms)
        
        # Compute financial sector profits and aggregates
        self._compute_financial_aggregates()
        
        # Compute firm-level taxes and handle cash flow
        # This matches C++ _Tax1 and _Tax2 equations
        tr = self._tr if self._flagTax else 0.0
        
        # Capital sector firms
        for firm in cap_sector.firms:
            firm.compute_tax_and_cash_flow(tr)
        
        # Consumption sector firms
        for firm in con_sector.firms:
            firm.compute_tax_and_cash_flow(tr)
        
        # Aggregate sector-level taxes
        cap_sector._Tax1 = sum(f._Tax1 for f in cap_sector.firms)
        con_sector._Tax2 = sum(f._Tax2 for f in con_sector.firms)
        fin_sector._TaxB = max(0, fin_sector._PiB * self._tr) if self._flagTax else 0
        
        self._Tax = cap_sector._Tax1 + con_sector._Tax2 + fin_sector._TaxB
        
        # Compute firm-level dividends (after taxes)
        # Use 0.5 (50%) payout rate as default
        d1 = 0.5  # Dividend payout rate for sector 1
        d2 = 0.5  # Dividend payout rate for sector 2
        
        for firm in cap_sector.firms:
            firm.compute_dividends(d1)
        
        for firm in con_sector.firms:
            firm.compute_dividends(d2)
        
        # Aggregate sector-level dividends
        cap_sector._Div1 = sum(f._Div1 for f in cap_sector.firms)
        con_sector._Div2 = sum(f._Div2 for f in con_sector.firms)
        fin_sector._DivB = max(0, fin_sector._PiB - fin_sector._TaxB) * 0.5
        
        self._Div = cap_sector._Div1 + con_sector._Div2 + fin_sector._DivB
        self._TaxDiv = self._Div * self._tr if self._flagTax >= 2 else 0
        
        # Net worth updates (now handled by cash_flow, but still aggregate for consistency)
        cap_sector._NW1 = sum(f._NW1 for f in cap_sector.firms)
        con_sector._NW2 = sum(f._NW2 for f in con_sector.firms)
    
    def _compute_financial_aggregates(self):
        """
        Compute financial sector aggregate variables
        Implements BadDeb, BadDeb1, BadDeb2, Depo, Loans, NWb, PiB, DivB, 
        Gbail, Cl, ExRes, BondsB, BondsCB equations
        """
        fin = self.financial_sector
        cap_sector = self.capital_sector
        con_sector = self.consumption_sector
        
        # BadDeb1 equation - bad debt from capital sector
        BadDeb1 = 0.0
        for firm in cap_sector.firms:
            if hasattr(firm, '_BadDeb1'):
                BadDeb1 += firm._BadDeb1
        
        # BadDeb2 equation - bad debt from consumption sector  
        BadDeb2 = 0.0
        for firm in con_sector.firms:
            if hasattr(firm, '_BadDeb2'):
                BadDeb2 += firm._BadDeb2
        
        # BadDeb equation - total bad debt
        fin._BadDeb1 = BadDeb1
        fin._BadDeb2 = BadDeb2
        fin._BadDeb = BadDeb1 + BadDeb2
        
        # Depo equation - total deposits
        # In C++, deposits are computed per bank from client firms
        # Here we compute total deposits directly from all firm net worths
        Depo = cap_sector._NW1 + con_sector._NW2
        # Add worker savings if available
        if hasattr(self, '_SavAcc'):
            Depo += self._SavAcc
        fin._Depo = Depo
        
        # Update bank deposits proportionally if banks exist
        if fin.banks:
            for bank in fin.banks:
                # Each bank gets equal share for simplicity
                # (In full implementation, would use market shares)
                bank._Depo = Depo / len(fin.banks)
                bank.write("_Depo", bank._Depo, 0)
        
        # Loans equation - total loans
        # Compute from firm debts
        Loans = cap_sector._Deb1 + con_sector._Deb2
        fin._Loans = Loans
        
        # Update bank loans proportionally if banks exist
        if fin.banks:
            for bank in fin.banks:
                bank._Loans = Loans / len(fin.banks)
                bank.write("_Loans", bank._Loans, 0)
        
        # NWb equation - total bank net worth
        NWb = 0.0
        for bank in fin.banks:
            if hasattr(bank, '_NWb'):
                NWb += bank._NWb
        fin._NWb = NWb
        
        # Cl equation - total clients
        Cl = 0
        for bank in fin.banks:
            if hasattr(bank, '_Cl'):
                Cl += bank._Cl
        fin._Cl = Cl
        
        # ExRes equation - excess reserves
        ExRes = 0.0
        for bank in fin.banks:
            if hasattr(bank, '_ExRes'):
                ExRes += bank._ExRes
        fin._ExRes = ExRes
        
        # BondsB equation - bonds held by banks
        BondsB = 0.0
        for bank in fin.banks:
            if hasattr(bank, '_BondsB'):
                BondsB += bank._BondsB
        fin._BondsB = BondsB
        
        # PiB equation - total bank profits
        PiB = 0.0
        for bank in fin.banks:
            if hasattr(bank, '_PiB'):
                PiB += bank._PiB
        fin._PiB = PiB
        
        # Gbail equation - government bailouts
        Gbail = 0.0
        for bank in fin.banks:
            if hasattr(bank, '_Gbail'):
                Gbail += bank._Gbail
        fin._Gbail = Gbail
        
        # BS equation - bond supply
        # Sovereign bond supply (new issues) from government
        Def = self._Def
        DepoG_lag = self.read_sector('_DepoG', fin, lag=1, default=0)
        BondsB_lag = self.read_sector('_BondsB', fin, lag=1, default=0)
        BondsCB_lag = self.read_sector('_BondsCB', fin, lag=1, default=0)
        thetaBonds = getattr(fin, '_thetaBonds', 10.0)
        
        bonds_maturing = (BondsB_lag + BondsCB_lag) / thetaBonds
        
        if Def + bonds_maturing < DepoG_lag:
            # No new bonds to supply
            fin._BS = 0
            fin._DepoG = DepoG_lag - Def - bonds_maturing
        else:
            # Issue just what is needed
            fin._BS = Def + bonds_maturing - DepoG_lag
            fin._DepoG = 0
        
        # BD equation - bond demand from banks (sum of _BD from banks)
        BD = 0.0
        for bank in fin.banks:
            if hasattr(bank, '_BD'):
                BD += bank._BD
        fin._BD = BD
        
        # BondsCB equation - bonds held by central bank (residual)
        # Central bank absorbs all outstanding bonds issued
        BondsCB_current = self.read_sector('_BondsCB', fin, lag=0, default=0)
        fin._BondsCB = max(0, BondsCB_current * (1 - 1/thetaBonds) + fin._BS - fin._BD)
        
        # PiCB equation - central bank profits
        # Interest on bonds held + reserves - interest on deposits
        rBonds = fin._rBonds
        rRes = fin._rRes
        PiCB = fin._BondsCB * rBonds - fin._DepoG * rRes
        fin._PiCB = PiCB
    
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
        
        # First, compute sector-level aggregations from firm-level data
        cap_sector.compute_aggregates()
        con_sector.compute_aggregates()
        
        # Compute market conditions indices
        cap_sector.compute_MC1()
        con_sector.compute_MC2()
        
        # Compute labor market aggregations (sAvg, wAvg, etc.)
        self._compute_labor_aggregates()
        
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
        
    def _compute_labor_aggregates(self):
        """
        Compute labor market aggregate statistics
        Implements sAvg, wAvg, wMinPol, sTmax, etc.
        """
        labor = self.labor_market
        
        # Compute wage aggregates (wAvg equation)
        wAvg, wMinPol, wU = labor.compute_wage_aggregates(self.workers)
        labor._wAvg = wAvg
        labor.write("wAvg", wAvg)
        
        # Compute skills aggregates (sAvg, sTavg, sVavg equations)
        sAvg, sTavg, sVavg = labor.compute_skills_aggregates(self.workers)
        labor._sAvg = sAvg
        labor._sTavg = sTavg
        labor._sVavg = sVavg
        
        labor.write("sAvg", sAvg)
        labor.write("sTavg", sTavg)
        labor.write("sVavg", sVavg)
        labor.write("sTmin", labor._sTmin)
        labor.write("sTmax", labor._sTmax)
        labor.write("sTsd", labor._sTsd)
        labor.write("sVsd", labor._sVsd)
        
        # Compute policy minimum wage (wMinPol equation)
        # Already computed by compute_wage_aggregates above
        labor.write("wMinPol", wMinPol)
    
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
        """
        Handle firm entry and exit (entryExit equation)
        Implements basic entry/exit dynamics from fun_KS_country.h
        """
        # Track entry/exit counts
        exits = 0
        entries = 0
        
        # Capital sector entry/exit
        exits += self._capital_sector_exit()
        entries += self._capital_sector_entry()
        
        # Consumption sector entry/exit
        exits += self._consumption_sector_exit()
        entries += self._consumption_sector_entry()
        
        # Recompute aggregates affected by entry/exit
        self._compute_entry_exit_costs()
        
        # Update financial sector credit scores
        # (pecking order for credit allocation)
        self._update_credit_scores()
        
        return exits + entries
    
    def _capital_sector_exit(self):
        """Exit process for capital sector firms"""
        cap_sector = self.capital_sector
        exits = 0
        
        # Identify firms to exit (negative net worth or market share too low)
        firms_to_exit = []
        for firm in cap_sector.firms:
            # Exit if negative net worth
            if firm._NW1 < 0:
                firms_to_exit.append(firm)
        
        # Remove exiting firms
        for firm in firms_to_exit:
            # Fire all workers
            for worker in self.workers:
                if worker._employer == firm:
                    worker._employed = 0
                    worker._employer = None
                    worker._Te = 0
            
            # Record exit cost/credit
            if hasattr(firm, '_NW1'):
                self._cExit += max(0, firm._NW1)  # Positive NW returned
            
            # Remove from firm list
            cap_sector.firms.remove(firm)
            exits += 1
        
        return exits
    
    def _capital_sector_entry(self):
        """Entry process for capital sector firms"""
        cap_sector = self.capital_sector
        entries = 0
        
        # Check if entry is needed (maintain minimum number)
        current_firms = len(cap_sector.firms)
        F1min = int(cap_sector._F1min)
        F1max = int(cap_sector._F1max)
        
        # Entry if below minimum and below maximum
        if current_firms < F1min and current_firms < F1max:
            # Create new firm
            new_id = max([f._ID1 for f in cap_sector.firms], default=0) + 1
            new_firm = Firm1(firm_id=new_id, parent=cap_sector)
            
            # Initialize with average characteristics
            if cap_sector.firms:
                avg_A = sum(f._Atau for f in cap_sector.firms) / len(cap_sector.firms)
                avg_B = sum(f._Btau for f in cap_sector.firms) / len(cap_sector.firms)
                new_firm._Atau = avg_A
                new_firm._Btau = avg_B
            else:
                new_firm._Atau = INIPROD
                new_firm._Btau = INIPROD
            
            # Initial values
            new_firm._p1 = new_firm._Btau * (1 + cap_sector._mu1)
            new_firm._NW1 = 10.0  # Initial equity
            
            # Record entry cost
            self._cEntry += new_firm._NW1
            
            cap_sector.firms.append(new_firm)
            entries += 1
        
        return entries
    
    def _consumption_sector_exit(self):
        """Exit process for consumption sector firms"""
        con_sector = self.consumption_sector
        exits = 0
        
        # Identify firms to exit
        firms_to_exit = []
        for firm in con_sector.firms:
            # Exit if negative net worth
            if firm._NW2 < 0:
                firms_to_exit.append(firm)
        
        # Remove exiting firms
        for firm in firms_to_exit:
            # Fire all workers
            for worker in self.workers:
                if worker._employer == firm:
                    worker._employed = 0
                    worker._employer = None
                    worker._Te = 0
            
            # Record exit cost/credit
            if hasattr(firm, '_NW2'):
                self._cExit += max(0, firm._NW2)
            
            # Remove from firm list
            con_sector.firms.remove(firm)
            exits += 1
        
        return exits
    
    def _consumption_sector_entry(self):
        """Entry process for consumption sector firms"""
        con_sector = self.consumption_sector
        entries = 0
        
        # Check if entry is needed
        current_firms = len(con_sector.firms)
        F2min = int(con_sector._F2min)
        F2max = int(con_sector._F2max)
        
        # Entry if below minimum and below maximum
        if current_firms < F2min and current_firms < F2max:
            # Create new firm
            new_id = max([f._ID2 for f in con_sector.firms], default=0) + 1
            new_firm = Firm2(firm_id=new_id, parent=con_sector)
            
            # Initialize with average characteristics
            if con_sector.firms:
                avg_A = sum(f._A2 for f in con_sector.firms) / len(con_sector.firms)
                new_firm._A2 = avg_A
            else:
                new_firm._A2 = INIPROD
            
            # Initial values
            new_firm._mu2 = con_sector._mu20
            new_firm._p2 = new_firm._A2 * (1 + new_firm._mu2)
            new_firm._NW2 = 10.0  # Initial equity
            
            # Record entry cost
            self._cEntry += new_firm._NW2
            
            con_sector.firms.append(new_firm)
            entries += 1
        
        return entries
    
    def _compute_entry_exit_costs(self):
        """
        Compute entry/exit costs and equity changes
        Implements cEntry, cExit, Eq equations
        """
        # cEntry and cExit are accumulated during entry/exit process
        # (already done in entry/exit methods above)
        
        # Recompute total equity (Eq equation)
        cap_sector = self.capital_sector
        con_sector = self.consumption_sector
        fin_sector = self.financial_sector
        
        cap_equity = sum(getattr(f, '_NW1', 0) for f in cap_sector.firms)
        con_equity = sum(getattr(f, '_NW2', 0) for f in con_sector.firms)
        bank_equity = sum(getattr(b, '_NWb', 0) for b in fin_sector.banks)
        
        self._Eq = cap_equity + con_equity + bank_equity
    
    def _update_credit_scores(self):
        """
        Update credit scores and pecking order
        Sets the credit allocation pecking order for firms
        """
        # This will be used by banks for credit allocation
        # For now, just store firm rankings by net worth to sales ratio
        cap_sector = self.capital_sector
        con_sector = self.consumption_sector
        
        # Rank capital sector firms
        for firm in cap_sector.firms:
            if hasattr(firm, '_S1') and firm._S1 > 0:
                firm._credit_score = safe_divide(firm._NW1, firm._S1)
            else:
                firm._credit_score = 0.0
        
        # Rank consumption sector firms
        for firm in con_sector.firms:
            if hasattr(firm, '_S2') and firm._S2 > 0:
                firm._credit_score = safe_divide(firm._NW2, firm._S2)
            else:
                firm._credit_score = 0.0
    
    def regulatory_change(self):
        """
        Execute regulatory regime change at specified time (regChg equation)
        
        If TregChg is reached, changes labor market and policy parameters
        from current values to "*Chg" variants.
        
        Implements EQUATION("regChg") from fun_KS_country.h
        """
        TregChg = int(self._TregChg)
        
        # Check if we're at regime change time
        if self._t != TregChg or TregChg <= 0:
            return False  # No change
        
        # Log regime change
        print(f"\n>>> Regime change at t={self._t}")
        
        # Global parameter changes
        if hasattr(self, '_flagSearchModeChg'):
            self._flagSearchMode = self._flagSearchModeChg
        if hasattr(self, '_flagIndexMinWageChg'):
            self._flagIndexMinWage = self._flagIndexMinWageChg
        if hasattr(self, '_flagHireSeqChg'):
            self._flagHireSeq = self._flagHireSeqChg
        if hasattr(self, '_flagHireOrder1Chg'):
            self._flagHireOrder1 = self._flagHireOrder1Chg
        if hasattr(self, '_flagFireOrder1Chg'):
            self._flagFireOrder1 = self._flagFireOrder1Chg
        if hasattr(self, '_trChg'):
            self._tr = self._trChg
        
        # Financial sector changes
        fin = self.financial_sector
        if hasattr(fin, '_LambdaChg'):
            fin._Lambda = fin._LambdaChg
        if hasattr(fin, '_muResChg'):
            fin._muRes = fin._muResChg
        if hasattr(fin, '_tauBchg'):
            fin._tauB = fin._tauBchg
        if hasattr(fin, '_rTchg'):
            fin._rT = fin._rTchg
        
        # Labor market changes
        labor = self.labor_market
        if hasattr(labor, '_TsChg'):
            labor._Ts = labor._TsChg
        if hasattr(labor, '_phiChg'):
            labor._phi = labor._phiChg
        if hasattr(labor, '_omegaPosChg'):
            labor._omega = labor._omegaPosChg
        
        # Consumption sector changes
        con = self.consumption_sector
        if hasattr(con, '_e0Chg'):
            con._e0 = con._e0Chg
        if hasattr(con, '_mu20Chg'):
            con._mu20 = con._mu20Chg
        
        # Firm-level changes (if flagAllFirmsChg is set)
        if hasattr(self, '_flagAllFirmsChg') and self._flagAllFirmsChg == 1:
            if hasattr(self, '_flagHireOrder2Chg'):
                self._flagHireOrder2 = self._flagHireOrder2Chg
            if hasattr(self, '_flagFireOrder2Chg'):
                self._flagFireOrder2 = self._flagFireOrder2Chg
            if hasattr(self, '_flagFireRuleChg'):
                self._flagFireRule = self._flagFireRuleChg
            if hasattr(self, '_flagWageOfferChg'):
                self._flagWageOffer = self._flagWageOfferChg
            if hasattr(self, '_flagIndexWageChg'):
                self._flagIndexWage = self._flagIndexWageChg
            if hasattr(con, '_bChg'):
                con._b = con._bChg
            
            # Mark all firms as post-change
            for firm in con.firms:
                if hasattr(firm, '_postChg'):
                    firm._postChg = 1
        
        return True  # Change executed
    
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
