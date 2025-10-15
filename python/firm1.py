"""
Capital Sector (Firm1) Agent Implementation
Implements capital-good firms with R&D, innovation, and machine production.
Based on fun_KS_firm1.h and fun_KS_capital.h
"""

from typing import List, Optional, Dict
from .agents import BaseAgent
from .config import FIRM1HK, BANK, BCLIENT, INIPROD, INIWAGE
from .random_generator import random_engine
import math


class Firm1(BaseAgent):
    """
    Capital-good firm (Firm1) agent class.
    Produces heterogeneous machine-tools through R&D and innovation.
    """
    
    def __init__(self, agent_id: int, parent=None):
        super().__init__(agent_id, "Firm1", parent)
        
        # Initialize hooks
        self.hooks = [None] * FIRM1HK
        
        # Firm1-specific variables
        self._ID1 = agent_id
        self._Atau = INIPROD        # Labor productivity of vintage (A coefficient)
        self._Btau = INIPROD        # Machine productivity coefficient (B)
        self._c1 = 0.0              # Unit cost
        self._p1 = 0.0              # Unit price
        self._f1 = 0.0              # Market share
        self._mu1 = 0.0             # Mark-up
        self._D1 = 0.0              # Orders/demand
        self._Q1 = 0.0              # Planned production
        self._Q1e = 0.0             # Effective production
        self._S1 = 0.0              # Sales
        self._L1 = 0.0              # Employed labor
        self._L1d = 0.0             # Desired labor
        self._L1rd = 0.0            # R&D labor
        self._w1 = 0.0              # Average wage
        self._NW1 = 0.0             # Net worth
        self._Deb1 = 0.0            # Debt
        self._Pi1 = 0.0             # Profits
        self._CS1a = 0.0            # Available credit
        self._CD1 = 0.0             # Desired credit
        self._CD1c = 0.0            # Credit constraint
        self._RD = 0.0              # R&D expenditure
        self._inn = False           # Innovation success flag
        self._imi = False           # Imitation success flag
        
        # Technology tracking
        self._tInn = 0              # Time of last innovation
        self._tImi = 0              # Time of last imitation
        
    def compute_productivity(self, params: dict, t: int) -> tuple:
        """
        Compute new vintage productivity (_Atau equation).
        Handles both innovation and imitation R&D.
        
        Args:
            params: Dictionary with model parameters
            t: Current time period
            
        Returns:
            Tuple of (Atau, Btau) - productivity coefficients
        """
        # Current productivity
        Atau_current = self._Atau
        Btau_current = self._Btau
        
        # Parameters
        alpha1 = params['alpha1']
        beta1 = params['beta1']
        alpha2 = params['alpha2']
        beta2 = params['beta2']
        xi = params['xi']
        x1inf = params['x1inf']
        x1sup = params['x1sup']
        zeta1 = params['zeta1']
        zeta2 = params['zeta2']
        nu = params['nu']
        m1 = params['m1']
        m2 = params['m2']
        b = params['b']
        
        # R&D allocation between innovation and imitation
        RD_total = self._RD
        RD_inn = xi * RD_total
        RD_imi = (1 - xi) * RD_total
        
        # Innovation attempt
        Ainn = Atau_current
        Binn = Btau_current
        inn_success = False
        
        if RD_inn > 0:
            # Innovation success probability
            prob_inn = 1.0 - math.exp(-zeta1 * RD_inn)
            
            if random_engine.bernoulli(prob_inn):
                # Innovation successful
                inn_success = True
                
                # Draw innovation magnitude
                x_inn = random_engine.uniform(x1inf, x1sup)
                
                # Update productivity with Beta distribution randomness
                Ainn = Atau_current * (1 + x_inn) * random_engine.beta(alpha1, beta1)
                Binn = Btau_current * (1 + x_inn) * random_engine.beta(alpha1, beta1)
        
        # Imitation attempt
        Aimi = Atau_current
        Bimi = Btau_current
        imi_success = False
        
        if RD_imi > 0:
            # Find best competitor for imitation
            sector = self.parent
            best_A = Atau_current
            best_B = Btau_current
            best_c = self._c1
            best_p = self._p1
            
            for competitor in sector.get_children("Firm1"):
                if competitor != self and competitor._f1 > 0:
                    comp_A = competitor._Atau
                    comp_B = competitor._Btau
                    
                    # Check if competitor is better (lower cost or higher productivity)
                    if comp_A > best_A or comp_B > best_B:
                        best_A = comp_A
                        best_B = comp_B
                        best_c = competitor._c1
                        best_p = competitor._p1
            
            # Imitation success probability
            prob_imi = 1.0 - math.exp(-zeta2 * RD_imi)
            
            if random_engine.bernoulli(prob_imi) and (best_A > Atau_current or best_B > Btau_current):
                # Imitation successful
                imi_success = True
                
                # Imitate with some randomness
                Aimi = best_A * random_engine.beta(alpha2, beta2)
                Bimi = best_B * random_engine.beta(alpha2, beta2)
        
        # Select best technology (innovation or imitation)
        if inn_success or imi_success:
            # Compute unit costs for comparison
            w1 = self._w1
            
            if inn_success:
                c_inn = w1 / (Binn * m1) if Binn > 0 else float('inf')
            else:
                c_inn = float('inf')
            
            if imi_success:
                c_imi = w1 / (Bimi * m1) if Bimi > 0 else float('inf')
            else:
                c_imi = float('inf')
            
            # Choose technology with lower cost
            if c_inn < c_imi and c_inn < self._c1:
                self._Atau = Ainn
                self._Btau = Binn
                self._inn = True
                self._tInn = t
            elif c_imi < self._c1:
                self._Atau = Aimi
                self._Btau = Bimi
                self._imi = True
                self._tImi = t
        
        self.WRITE("_Atau", self._Atau)
        self.WRITE("_Btau", self._Btau)
        self.WRITE("_inn", 1.0 if self._inn else 0.0)
        self.WRITE("_imi", 1.0 if self._imi else 0.0)
        
        return self._Atau, self._Btau
    
    def compute_unit_cost(self, w1: float, m1: float) -> float:
        """
        Compute unit cost (_c1 equation).
        
        Args:
            w1: Wage in capital sector
            m1: Worker output per period
            
        Returns:
            Unit cost
        """
        self._c1 = w1 / (self._Btau * m1) if self._Btau > 0 else 0.0
        self.WRITE("_c1", self._c1)
        return self._c1
    
    def compute_price(self, mu1: float) -> float:
        """
        Compute price (_p1 equation).
        
        Args:
            mu1: Mark-up rate
            
        Returns:
            Unit price
        """
        self._mu1 = mu1
        self._p1 = (1 + mu1) * self._c1
        self.WRITE("_p1", self._p1)
        return self._p1
    
    def compute_demand(self) -> float:
        """
        Aggregate orders from clients (_D1 equation).
        
        Returns:
            Total demand
        """
        # Sum orders from all clients (in brochures)
        D1 = 0.0
        for cli in self.get_children("Cli"):
            D1 += cli.V("_Qo")  # Ordered quantity
        
        self._D1 = D1
        self.WRITE("_D1", D1)
        return D1
    
    def compute_production(self, L1rdMax: float) -> tuple:
        """
        Compute production plan and labor demand (_Q1, _L1d equations).
        
        Args:
            L1rdMax: Maximum R&D labor share
            
        Returns:
            Tuple of (Q1, L1d, L1rd)
        """
        # Desired production equals demand
        Q1_desired = self._D1
        
        # R&D expenditure (fraction of past revenue)
        S1_lag = self.VL("_S1", 1)
        nu = self.parent.V("nu") if self.parent else 0.1
        RD = nu * S1_lag
        self._RD = RD
        
        # R&D labor demand
        w1 = self._w1
        L1rd = RD / w1 if w1 > 0 else 0.0
        
        # Production labor demand
        m1 = self.parent.V("m1") if self.parent else 1.0
        L1prod = Q1_desired / (self._Btau * m1) if self._Btau > 0 else 0.0
        
        # Total labor demand
        L1d_total = L1prod + L1rd
        
        # Check R&D labor constraint
        if L1d_total > 0 and L1rd / L1d_total > L1rdMax:
            # Scale down R&D
            L1rd = L1rdMax * L1d_total
            RD = L1rd * w1
            self._RD = RD
        
        self._L1rd = L1rd
        self._L1d = L1d_total
        self._Q1 = Q1_desired
        
        self.WRITE("_Q1", Q1_desired)
        self.WRITE("_L1d", L1d_total)
        self.WRITE("_L1rd", L1rd)
        self.WRITE("_RD", RD)
        
        return Q1_desired, L1d_total, L1rd
    
    def compute_effective_production(self, L1: float) -> float:
        """
        Compute actual production based on hired labor (_Q1e equation).
        
        Args:
            L1: Actually hired labor
            
        Returns:
            Effective production
        """
        # Adjust for R&D labor
        L1_prod = max(0.0, L1 - self._L1rd)
        
        m1 = self.parent.V("m1") if self.parent else 1.0
        Q1e = L1_prod * self._Btau * m1
        
        self._Q1e = Q1e
        self._L1 = L1
        self.WRITE("_Q1e", Q1e)
        self.WRITE("_L1", L1)
        
        return Q1e
    
    def compute_sales(self) -> float:
        """
        Compute sales revenue (_S1 equation).
        
        Returns:
            Sales revenue
        """
        S1 = min(self._Q1e, self._D1) * self._p1
        self._S1 = S1
        self.WRITE("_S1", S1)
        return S1
    
    def compute_profits(self) -> float:
        """
        Compute profits (_Pi1 equation).
        
        Returns:
            Profits
        """
        # Revenue
        revenue = self._S1
        
        # Costs
        labor_cost = self._L1 * self._w1
        interest = self.V("_rDeb") * self._Deb1
        
        # Profits
        Pi1 = revenue - labor_cost - interest
        self._Pi1 = Pi1
        self.WRITE("_Pi1", Pi1)
        
        return Pi1
    
    def update_market_share(self, total_sales: float, n1: int) -> float:
        """
        Update market share (_f1 equation).
        
        Args:
            total_sales: Total sector sales
            n1: Number of periods for evaluation
            
        Returns:
            Market share
        """
        # Average sales over n1 periods
        sales_sum = 0.0
        for lag in range(n1):
            sales_sum += self.VL("_S1", lag)
        
        avg_sales = sales_sum / n1
        
        # Market share
        f1 = avg_sales / total_sales if total_sales > 0 else 0.0
        self._f1 = f1
        self.WRITE("_f1", f1)
        
        return f1
