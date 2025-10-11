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
        self._Deb2max = 0.0               # Maximum debt sector 2
        self._HCavg = 0.0                 # Average capacity utilization
        self._NCavg = 0.0                 # Average number of clients
        
        # Sector 2 specific statistics
        self._CD2 = 0.0                   # Change in demand sector 2
        self._CD2c = 0.0                  # Change in real demand sector 2
        self._CS2 = 0.0                   # Demand per capita sector 2
        self._A2sd = 0.0                  # Std dev productivity sector 2
        self._A2posChg = 0.0              # Positive A changes sector 2
        self._A2preChg = 0.0              # Negative A changes sector 2
        self._mu2avg = 0.0                # Average mark-up sector 2
        self._age1avg = 0.0               # Average age sector 1
        self._age2avg = 0.0               # Average age sector 2
        self._s1avg = 0.0                 # Average skill sector 1
        self._s2avg = 0.0                 # Average skill sector 2
        self._HH1 = 0.0                   # HHI sector 1
        self._HH2 = 0.0                   # HHI sector 2
        self._HP1 = 0.0                   # HHI percent sector 1
        self._HP2 = 0.0                   # HHI percent sector 2
        
        # Labor mobility statistics
        self._L1ent = 0                   # Entrants sector 1
        self._L1exit = 0                  # Exits sector 1
        self._L2ent = 0                   # Entrants sector 2
        self._L2exit = 0                  # Exits sector 2
        self._Lent = 0                    # Total entrants
        self._Lexit = 0                   # Total exits
        self._L1v = 0                     # Vacancies sector 1
        self._L2v = 0                     # Vacancies sector 2
        self._V = 0                       # Total vacancies
        
        # Investment and savings
        self._EId = 0.0                   # Expansion investment demand
        self._SId = 0.0                   # Substitution investment demand
        self._RS2 = 0.0                   # Desired machine orders sector 2
        self._RD = 0.0                    # R&D expenditure sector 1
        
        # Wage and income statistics
        self._dN = 0.0                    # Change in inventories (nominal)
        self._dw = 0.0                    # Wage growth rate
        self._wAvgReal = 0.0              # Real average wage
        self._TuAvg = 0.0                 # Average unemployment duration
        
        # Firm counts
        self._B2payers = 0                # Firms paying bonuses sector 2
        self._noWrk2 = 0                  # Firms without workers sector 2
        self._part = 0.0                  # Participation rate
        
        # Quality and technology
        self._q2posChg = 0                # Positive quality changes sector 2
        self._q2preChg = 0                # Negative quality changes sector 2
        self._w2realPosChg = 0            # Positive real wage changes sector 2
        self._w2realPreChg = 0            # Negative real wage changes sector 2
        self._nBrochAvg = 0.0             # Average brochures sent
        self._w2oMin = 0.0                # Minimum wage offer sector 2
        self._w2avgLarg = 0.0             # Average wage large firms sector 2
        self._L2larg = 0                  # Employment large firms sector 2
    
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
    
    def compute_sector2_statistics(self, country):
        """
        Compute sector 2 (consumption) specific statistics
        
        Args:
            country: Country object
        """
        con_sector = country.consumption_sector
        labor = country.labor_market
        
        if not con_sector.firms:
            return
        
        # Demand changes sector 2
        D2 = con_sector._D2 if hasattr(con_sector, '_D2') else 0.0
        D2_prev = self.read_from(con_sector, '_D2', lag=1)
        if D2_prev:
            self._CD2 = D2 - D2_prev
        else:
            self._CD2 = 0.0
        
        # Real demand change sector 2
        if D2_prev and D2_prev > 0:
            self._CD2c = (D2 - D2_prev) / D2_prev
        else:
            self._CD2c = 0.0
        
        # Per capita demand sector 2
        self._CS2 = safe_divide(D2, labor._Ls) if labor._Ls > 0 else 0.0
        
        # Productivity statistics sector 2
        A2_values = [f._A2 for f in con_sector.firms if hasattr(f, '_A2') and f._A2 > 0]
        if A2_values:
            n = len(A2_values)
            avg = sum(A2_values) / n
            variance = sum((x - avg)**2 for x in A2_values) / n if n > 1 else 0.0
            self._A2sd = math.sqrt(variance)
        else:
            self._A2sd = 0.0
        
        # Count productivity changes
        pos_changes = 0
        neg_changes = 0
        for firm in con_sector.firms:
            if hasattr(firm, '_A2'):
                A2_old = self.read_from(firm, '_A2', lag=1)
                if A2_old and A2_old > 0:
                    change = (firm._A2 - A2_old) / A2_old
                    if change > 0:
                        pos_changes += 1
                    elif change < 0:
                        neg_changes += 1
        
        self._A2posChg = pos_changes
        self._A2preChg = neg_changes
        
        # Average mark-up sector 2
        mu2_values = [f._mu2 for f in con_sector.firms if hasattr(f, '_mu2')]
        self._mu2avg = sum(mu2_values) / len(mu2_values) if mu2_values else 0.0
        
        # Average ages
        age2_values = [f._t2ent for f in con_sector.firms if hasattr(f, '_t2ent')]
        t = country._t if hasattr(country, '_t') else 0
        ages = [t - entry_time for entry_time in age2_values]
        self._age2avg = sum(ages) / len(ages) if ages else 0.0
        
        # Average skills sector 2
        s2_values = []
        for firm in con_sector.firms:
            if hasattr(firm, '_workers'):
                for worker in firm._workers:
                    if hasattr(worker, '_s'):
                        s2_values.append(worker._s)
        self._s2avg = sum(s2_values) / len(s2_values) if s2_values else 0.0
        
        # Herfindahl index sector 2
        total_sales = sum(f._S2 for f in con_sector.firms if hasattr(f, '_S2'))
        if total_sales > 0:
            shares = [safe_divide(f._S2, total_sales) for f in con_sector.firms if hasattr(f, '_S2')]
            self._HH2 = sum(s**2 for s in shares)
            self._HP2 = self._HH2 * 100
        else:
            self._HH2 = 0.0
            self._HP2 = 0.0
        
        # Maximum debt sector 2
        Deb2_values = [f._Deb2 for f in con_sector.firms if hasattr(f, '_Deb2')]
        self._Deb2max = max(Deb2_values) if Deb2_values else 0.0
        
        # Count bonus payers
        self._B2payers = sum(1 for f in con_sector.firms if hasattr(f, '_Bon2') and f._Bon2 > 0)
        
        # Count firms without workers
        self._noWrk2 = sum(1 for f in con_sector.firms if hasattr(f, '_L2') and f._L2 == 0)
        
        # Quality changes
        q2_pos = 0
        q2_neg = 0
        for firm in con_sector.firms:
            if hasattr(firm, '_q2'):
                q2_old = self.read_from(firm, '_q2', lag=1)
                if q2_old and q2_old > 0:
                    if firm._q2 > q2_old:
                        q2_pos += 1
                    elif firm._q2 < q2_old:
                        q2_neg += 1
        
        self._q2posChg = q2_pos
        self._q2preChg = q2_neg
        
        # Average number of clients
        NC_values = [f._NC for f in con_sector.firms if hasattr(f, '_NC')]
        self._NCavg = sum(NC_values) / len(NC_values) if NC_values else 0.0
    
    def compute_sector1_statistics(self, country):
        """
        Compute sector 1 (capital goods) specific statistics
        
        Args:
            country: Country object
        """
        cap_sector = country.capital_sector
        
        if not cap_sector.firms:
            return
        
        # Average ages sector 1
        age1_values = [f._t1ent for f in cap_sector.firms if hasattr(f, '_t1ent')]
        t = country._t if hasattr(country, '_t') else 0
        ages = [t - entry_time for entry_time in age1_values]
        self._age1avg = sum(ages) / len(ages) if ages else 0.0
        
        # Average skills sector 1
        s1_values = []
        for firm in cap_sector.firms:
            if hasattr(firm, '_workers'):
                for worker in firm._workers:
                    if hasattr(worker, '_s'):
                        s1_values.append(worker._s)
        self._s1avg = sum(s1_values) / len(s1_values) if s1_values else 0.0
        
        # Herfindahl index sector 1
        total_sales = sum(f._S1 for f in cap_sector.firms if hasattr(f, '_S1'))
        if total_sales > 0:
            shares = [safe_divide(f._S1, total_sales) for f in cap_sector.firms if hasattr(f, '_S1')]
            self._HH1 = sum(s**2 for s in shares)
            self._HP1 = self._HH1 * 100
        else:
            self._HH1 = 0.0
            self._HP1 = 0.0
        
        # Average brochures sent
        broch_values = [f._nBroch for f in cap_sector.firms if hasattr(f, '_nBroch')]
        self._nBrochAvg = sum(broch_values) / len(broch_values) if broch_values else 0.0
    
    def compute_labor_mobility_statistics(self, country):
        """
        Compute labor mobility statistics (entry/exit between sectors)
        
        Args:
            country: Country object
        """
        cap_sector = country.capital_sector
        con_sector = country.consumption_sector
        labor = country.labor_market
        
        # These would be tracked during labor market operations
        # For now, approximate from sector changes
        L1 = cap_sector._L1 if hasattr(cap_sector, '_L1') else 0
        L2 = con_sector._L2 if hasattr(con_sector, '_L2') else 0
        L1_prev = self.read_from(cap_sector, '_L1', lag=1)
        L2_prev = self.read_from(con_sector, '_L2', lag=1)
        
        # Entries and exits (simplified approximation)
        if L1_prev is not None:
            delta_L1 = L1 - L1_prev
            self._L1ent = max(delta_L1, 0)
            self._L1exit = max(-delta_L1, 0)
        else:
            self._L1ent = 0
            self._L1exit = 0
        
        if L2_prev is not None:
            delta_L2 = L2 - L2_prev
            self._L2ent = max(delta_L2, 0)
            self._L2exit = max(-delta_L2, 0)
        else:
            self._L2ent = 0
            self._L2exit = 0
        
        self._Lent = self._L1ent + self._L2ent
        self._Lexit = self._L1exit + self._L2exit
        
        # Vacancies
        L1d = cap_sector._L1d if hasattr(cap_sector, '_L1d') else 0
        L2d = con_sector._L2d if hasattr(con_sector, '_L2d') else 0
        self._L1v = max(L1d - L1, 0)
        self._L2v = max(L2d - L2, 0)
        self._V = self._L1v + self._L2v
    
    def compute_investment_statistics(self, country):
        """
        Compute investment-related statistics
        
        Args:
            country: Country object
        """
        con_sector = country.consumption_sector
        
        # Expansion and substitution investment
        EI_total = sum(f._EI for f in con_sector.firms if hasattr(f, '_EI'))
        SI_total = sum(f._SI for f in con_sector.firms if hasattr(f, '_SI'))
        
        self._EId = EI_total
        self._SId = SI_total
        
        # Desired machine orders (substitution + expansion)
        self._RS2 = SI_total + EI_total
        
        # R&D expenditure
        cap_sector = country.capital_sector
        RD_total = sum(f._RD for f in cap_sector.firms if hasattr(f, '_RD'))
        self._RD = RD_total
    
    def compute_wage_statistics(self, country):
        """
        Compute wage-related statistics
        
        Args:
            country: Country object
        """
        labor = country.labor_market
        con_sector = country.consumption_sector
        
        # Change in inventories (nominal)
        dN_nom = con_sector._dNnom if hasattr(con_sector, '_dNnom') else 0.0
        self._dN = dN_nom
        
        # Wage growth rate
        wAvg = labor._wAvg
        wAvg_prev = self.read_from(labor, '_wAvg', lag=1)
        if wAvg_prev and wAvg_prev > 0:
            self._dw = (wAvg - wAvg_prev) / wAvg_prev
        else:
            self._dw = 0.0
        
        # Real average wage
        CPI = con_sector._p2avg if hasattr(con_sector, '_p2avg') else 1.0
        self._wAvgReal = safe_divide(wAvg, CPI)
        
        # Average unemployment duration
        # This requires tracking unemployment spells - simplified version
        if hasattr(labor, '_TuAvg'):
            self._TuAvg = labor._TuAvg
        else:
            self._TuAvg = 0.0
        
        # Participation rate
        Ls = labor._Ls
        Lscale = country._Lscale if hasattr(country, '_Lscale') else 1
        total_population = Ls * Lscale
        # Assume working-age population is proportional to total
        # This is a simplification; real model might track this separately
        self._part = 1.0  # Simplified: assume 100% participation
        
        # Sector 2 wage statistics
        if con_sector.firms:
            # Minimum wage offer
            w2o_values = [f._w2o for f in con_sector.firms if hasattr(f, '_w2o') and f._w2o > 0]
            self._w2oMin = min(w2o_values) if w2o_values else 0.0
            
            # Large firms (top quartile by size)
            firms_by_size = sorted(con_sector.firms, 
                                 key=lambda f: getattr(f, '_L2', 0), 
                                 reverse=True)
            n_large = max(1, len(firms_by_size) // 4)
            large_firms = firms_by_size[:n_large]
            
            # Average wage in large firms
            w2_large = [f._w2 for f in large_firms if hasattr(f, '_w2')]
            self._w2avgLarg = sum(w2_large) / len(w2_large) if w2_large else 0.0
            
            # Employment in large firms
            self._L2larg = sum(f._L2 for f in large_firms if hasattr(f, '_L2'))
            
            # Real wage changes in sector 2
            w2_real_pos = 0
            w2_real_neg = 0
            for firm in con_sector.firms:
                if hasattr(firm, '_w2'):
                    w2_real = safe_divide(firm._w2, CPI)
                    w2_real_prev = self.read_from(firm, '_w2', lag=1)
                    if w2_real_prev:
                        w2_real_prev_adj = safe_divide(w2_real_prev, 
                                                       self.read('_pC', lag=1) or CPI)
                        if w2_real > w2_real_prev_adj:
                            w2_real_pos += 1
                        elif w2_real < w2_real_prev_adj:
                            w2_real_neg += 1
            
            self._w2realPosChg = w2_real_pos
            self._w2realPreChg = w2_real_neg
    
    def compute_all_statistics(self, country):
        """
        Compute all statistics for current period
        
        Args:
            country: Country object
        """
        self.compute_macro_aggregates(country)
        self.compute_sectoral_statistics(country)
        self.compute_financial_statistics(country)
        self.compute_sector1_statistics(country)
        self.compute_sector2_statistics(country)
        self.compute_labor_mobility_statistics(country)
        self.compute_investment_statistics(country)
        self.compute_wage_statistics(country)
    
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
