"""
Statistics Module for K+S Model
Implements all statistical equations from fun_KS_stats.h
"""

from typing import Dict, List, Optional
from .agent import Agent
from .support import safe_divide
import math


class StatisticsCollector(Agent):
    """
    Statistics collector for K+S model
    Computes aggregate and sectoral statistics
    Based on fun_KS_stats.h
    """
    
    def __init__(self, parent: Agent):
        """Initialize statistics collector"""
        super().__init__("Stats", parent)
        
        # Macroeconomic aggregates
        self._A = 0.0                     # Overall productivity
        self._dA = 0.0                    # Productivity growth rate
        self._dAb = 0.0                   # Bounded productivity growth
        self._C = 0.0                     # Real consumption
        self._CD = 0.0                    # Change in nominal consumption
        self._CDc = 0.0                   # Change in real consumption
        self._CS = 0.0                    # Consumption per capita
        self._Creal = 0.0                 # Real consumption aggregate
        self._Def = 0.0                   # Government deficit
        self._DefGDP = 0.0                # Deficit to GDP ratio
        self._DefP = 0.0                  # Primary deficit
        self._GDI = 0.0                   # Gross domestic income
        self._GDPdefl = 0.0               # GDP deflator
        self._GDPnom = 0.0                # Nominal GDP
        self._GDPreal = 0.0               # Real GDP
        self._dGDP = 0.0                  # GDP growth rate
        
        # Price indices
        self._pC = 0.0                    # Consumption price index
        self._pC0 = 1.0                   # Initial price level
        self._inflation = 0.0             # Inflation rate
        
        # Labor market statistics
        self._L = 0                       # Total employment
        self._Ls = 0                      # Labor supply
        self._U = 0                       # Unemployment
        self._Ue = 0.0                    # Unemployment rate
        
        # Sectoral statistics
        self._F1 = 0                      # Number of firms sector 1
        self._F2 = 0                      # Number of firms sector 2
        self._CD1 = 0.0                   # Change in demand sector 1
        self._CD1c = 0.0                  # Change in real demand sector 1
        self._CS1 = 0.0                   # Demand per capita sector 1
        
        # Financial statistics
        self._BadDeb = 0.0                # Bad debt total
        self._BadDebAcc = 0.0             # Accumulated bad debt
        self._BadDeb1 = 0.0               # Bad debt sector 1
        self._BadDeb2 = 0.0               # Bad debt sector 2
        self._Bda = 0.0                   # Bad debt rate
        self._Bfail = 0                   # Bank failures
        self._HHb = 0.0                   # Banking sector Herfindahl
        self._HPb = 0.0                   # Banking sector HHI (pct)
        self._TC = 0.0                    # Total credit
        
        # Productivity statistics
        self._AtauAvg = 0.0               # Average machine productivity A
        self._BtauAvg = 0.0               # Average machine productivity B
        
        # Capacity statistics
        self._Deb1max = 0.0               # Maximum debt sector 1
        self._HCavg = 0.0                 # Average capacity utilization
    
    def compute_macro_aggregates(self, country):
        """
        Compute macroeconomic aggregate statistics
        
        Args:
            country: Country object with all sectors
        """
        labor = country.labor_market
        cap_sector = country.capital_sector
        con_sector = country.consumption_sector
        fin_sector = country.financial_sector
        
        # Labor market
        self._L = labor._L
        self._Ls = labor._Ls
        self._U = self._Ls - self._L
        self._Ue = safe_divide(self._U, self._Ls) if self._Ls > 0 else 0.0
        
        # Number of firms
        self._F1 = len(cap_sector.firms)
        self._F2 = len(con_sector.firms)
        
        # GDP components (real terms)
        self._Creal = con_sector._Q2e  # Real production of consumption goods
        Ireal = con_sector._Ireal if hasattr(con_sector, '_Ireal') else 0.0
        self._GDPreal = max(self._Creal + Ireal, 1.0)
        
        # GDP components (nominal terms)
        C_nom = country._C  # Nominal consumption
        I_nom = con_sector._Inom if hasattr(con_sector, '_Inom') else 0.0
        dN_nom = con_sector._dNnom if hasattr(con_sector, '_dNnom') else 0.0
        self._GDPnom = max(C_nom + I_nom + dN_nom, 1.0)
        
        # Overall productivity
        if self._L > 0:
            self._A = safe_divide(self._GDPreal, self._L)
        else:
            self._A = country._A  # Keep previous value
        
        # GDP growth rate
        GDPreal_prev = self.read('_GDPreal', lag=1)
        if GDPreal_prev and GDPreal_prev > 0:
            self._dGDP = (self._GDPreal - GDPreal_prev) / GDPreal_prev
        else:
            self._dGDP = 0.0
        
        # Bounded GDP growth (for moving averages)
        mLim = country._mLim if country._mLim > 0 else float('inf')
        self._dGDP = max(min(self._dGDP, mLim), -mLim)
        
        # Productivity growth
        A_prev = self.read('_A', lag=1)
        if A_prev and A_prev > 0:
            self._dA = (self._A - A_prev) / A_prev
            self._dAb = max(min(self._dA, mLim), -mLim)
        else:
            self._dA = 0.0
            self._dAb = 0.0
        
        # Price indices
        self._pC = con_sector._p2avg if con_sector._p2avg > 0 else self._pC0
        pC_prev = self.read('_pC', lag=1)
        if pC_prev and pC_prev > 0:
            self._inflation = (self._pC - pC_prev) / pC_prev
        else:
            self._inflation = 0.0
        
        # GDP deflator
        self._GDPdefl = safe_divide(self._GDPnom, self._GDPreal)
        
        # Gross domestic income (should equal GDP in equilibrium)
        W = labor._W if hasattr(labor, '_W') else self._L * labor._wAvg
        Pi1 = cap_sector._Pi1 if hasattr(cap_sector, '_Pi1') else 0.0
        Pi2 = con_sector._Pi2 if hasattr(con_sector, '_Pi2') else 0.0
        PiB = fin_sector._PiB if hasattr(fin_sector, '_PiB') else 0.0
        self._GDI = W + Pi1 + Pi2 + PiB
        
        # Fiscal statistics
        self._Def = country._Def
        self._DefP = country._DefP
        self._DefGDP = safe_divide(self._Def, self._GDPnom)
        
        # Per capita statistics
        self._CS = safe_divide(self._Creal, self._Ls) if self._Ls > 0 else 0.0
        
        # Changes in consumption
        C_prev = self.read('_C', lag=1)
        if C_prev:
            self._CD = country._C - C_prev
        else:
            self._CD = 0.0
        
        Creal_prev = self.read('_Creal', lag=1)
        if Creal_prev and Creal_prev > 0:
            self._CDc = (self._Creal - Creal_prev) / Creal_prev
        else:
            self._CDc = 0.0
    
    def compute_sectoral_statistics(self, country):
        """
        Compute sectoral statistics
        
        Args:
            country: Country object with all sectors
        """
        cap_sector = country.capital_sector
        con_sector = country.consumption_sector
        
        # Capital sector averages
        if cap_sector.firms:
            # Average productivities
            Atau_sum = sum(f._Atau for f in cap_sector.firms if hasattr(f, '_Atau'))
            Btau_sum = sum(f._Btau for f in cap_sector.firms if hasattr(f, '_Btau'))
            self._AtauAvg = Atau_sum / len(cap_sector.firms)
            self._BtauAvg = Btau_sum / len(cap_sector.firms)
            
            # Maximum debt
            Deb1_values = [f._Deb1 for f in cap_sector.firms if hasattr(f, '_Deb1')]
            self._Deb1max = max(Deb1_values) if Deb1_values else 0.0
        else:
            self._AtauAvg = 0.0
            self._BtauAvg = 0.0
            self._Deb1max = 0.0
        
        # Consumption sector statistics
        if con_sector.firms:
            # Average capacity utilization
            utilizations = []
            for firm in con_sector.firms:
                if hasattr(firm, '_K') and firm._K > 0:
                    # Utilization = actual production / capacity
                    capacity = firm._K
                    production = firm._Q2e if hasattr(firm, '_Q2e') else 0.0
                    utilization = safe_divide(production, capacity)
                    utilizations.append(utilization)
            
            self._HCavg = sum(utilizations) / len(utilizations) if utilizations else 0.0
        else:
            self._HCavg = 0.0
        
        # Sector 1 demand changes
        D1 = cap_sector._D1 if hasattr(cap_sector, '_D1') else 0.0
        D1_prev = self.read_from(cap_sector, '_D1', lag=1)
        if D1_prev:
            self._CD1 = D1 - D1_prev
        else:
            self._CD1 = 0.0
        
        # Real demand change
        if D1_prev and D1_prev > 0:
            self._CD1c = (D1 - D1_prev) / D1_prev
        else:
            self._CD1c = 0.0
        
        # Per capita demand sector 1
        self._CS1 = safe_divide(D1, country.labor_market._Ls)
    
    def compute_financial_statistics(self, country):
        """
        Compute financial sector statistics
        
        Args:
            country: Country object with all sectors
        """
        fin_sector = country.financial_sector
        cap_sector = country.capital_sector
        con_sector = country.consumption_sector
        
        # Bad debt accumulation
        BadDeb1_new = 0.0
        BadDeb2_new = 0.0
        
        # Collect bad debt from firms
        for firm in cap_sector.firms:
            if hasattr(firm, '_BadDeb1'):
                BadDeb1_new += firm._BadDeb1
        
        for firm in con_sector.firms:
            if hasattr(firm, '_BadDeb2'):
                BadDeb2_new += firm._BadDeb2
        
        self._BadDeb1 = BadDeb1_new
        self._BadDeb2 = BadDeb2_new
        self._BadDeb = self._BadDeb1 + self._BadDeb2
        
        # Accumulated bad debt
        BadDebAcc_prev = self.read('_BadDebAcc', lag=1)
        if BadDebAcc_prev:
            self._BadDebAcc = BadDebAcc_prev + self._BadDeb
        else:
            self._BadDebAcc = self._BadDeb
        
        # Total credit
        Loans1 = sum(f._Deb1 for f in cap_sector.firms if hasattr(f, '_Deb1'))
        Loans2 = sum(f._Deb2 for f in con_sector.firms if hasattr(f, '_Deb2'))
        self._TC = Loans1 + Loans2
        
        # Bad debt rate
        self._Bda = safe_divide(self._BadDeb, self._TC) if self._TC > 0 else 0.0
        
        # Bank concentration (Herfindahl index)
        if fin_sector.banks and self._TC > 0:
            bank_shares = []
            for bank in fin_sector.banks:
                bank_loans = bank._Loans if hasattr(bank, '_Loans') else 0.0
                share = safe_divide(bank_loans, self._TC)
                bank_shares.append(share)
            
            # HHI = sum of squared market shares
            self._HHb = sum(s**2 for s in bank_shares)
            self._HPb = self._HHb * 100  # Percentage
        else:
            self._HHb = 0.0
            self._HPb = 0.0
        
        # Bank failures
        self._Bfail = getattr(fin_sector, '_Bfail', 0)
    
    def compute_all_statistics(self, country):
        """
        Compute all statistics for current period
        
        Args:
            country: Country object
        """
        self.compute_macro_aggregates(country)
        self.compute_sectoral_statistics(country)
        self.compute_financial_statistics(country)
    
    def read_from(self, obj, attr: str, lag: int = 0) -> Optional[float]:
        """
        Read lagged value from another object
        
        Args:
            obj: Object to read from
            attr: Attribute name
            lag: Number of periods back (0 = current)
            
        Returns:
            Value or None if not available
        """
        if hasattr(obj, attr):
            if lag == 0:
                return getattr(obj, attr)
            elif hasattr(obj, '_lags') and attr in obj._lags:
                if lag <= len(obj._lags[attr]):
                    return obj._lags[attr][-lag] if lag <= len(obj._lags[attr]) else None
        return None
