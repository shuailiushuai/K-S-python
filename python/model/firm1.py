"""
Firm1 Agent Implementation (Capital Goods Sector)
Represents capital goods producers with R&D and innovation capabilities
"""

from typing import Optional, List, Tuple
from .agent import Agent
from .constants import *
from .random_engine import random_engine
from .support import beta_draw, euclidean_distance, safe_divide
import math


class Firm1(Agent):
    """
    Firm1 agent class (Capital Goods Sector)
    
    Capital goods firms:
    - Perform R&D (innovation and imitation)
    - Produce heterogeneous machines with different productivities
    - Compete through technological innovation
    - Set prices with fixed mark-up over labor costs
    - Distribute brochures to potential clients
    - Hire workers for production and R&D
    - Manage finance (debt, deposits, dividends)
    """
    
    def __init__(self, firm_id: int, parent: Agent):
        """
        Initialize Firm1 agent
        
        Args:
            firm_id: Unique firm ID
            parent: Parent Capital sector object
        """
        super().__init__("Firm1", parent)
        
        # Firm attributes
        self._ID = firm_id
        self._t1ent = 0                   # Entry time
        self._life1cycle = 0              # Life cycle stage
        
        # Technology attributes
        self._Atau = INIPROD              # Final productivity (A)
        self._Btau = INIPROD              # Production productivity (B)
        
        # Production and demand
        self._D1 = 0.0                    # Demand (orders)
        self._Q1 = 0.0                    # Planned production
        self._Q1e = 0.0                   # Effective production
        self._L1 = 0                      # Actual workers
        self._L1d = 0                     # Desired workers
        self._L1rd = 0                    # R&D workers
        
        # Costs and pricing
        self._c1 = 0.0                    # Unit cost
        self._p1 = 0.0                    # Price
        self._RD = 0.0                    # R&D expenditure
        
        # Financial
        self._NW1 = 0.0                   # Net worth
        self._Deb1 = 0.0                  # Debt stock
        self._S1 = 0.0                    # Sales revenue
        self._Pi1 = 0.0                   # Gross profits
        self._Tax1 = 0.0                  # Taxes paid
        self._Div1 = 0.0                  # Dividends paid
        self._W1 = 0.0                    # Total wages paid
        self._i1 = 0.0                    # Interest paid on debt
        self._iD1 = 0.0                   # Interest from deposits
        
        # Market
        self._f1 = 0.0                    # Market share
        self._HC = 0                      # Historical clients count
        self._BC = 0                      # Buying clients count
        
        # Initialize hooks for bank and client references
        self.add_hooks(FIRM1HK)
    
    def compute_innovation_imitation(self, params: dict) -> Tuple[float, float]:
        """
        Compute R&D results: innovation and imitation
        
        This is the core of the K+S model's endogenous technical change.
        Firms invest in R&D to:
        1. Innovate: Create new technologies (Beta distribution)
        2. Imitate: Copy technologies from competitors (distance-based)
        
        Args:
            params: Dictionary with parameters:
                - xi: Share of R&D for innovation
                - zeta1: Innovation success elasticity
                - zeta2: Imitation success elasticity
                - alpha1, beta1: Beta distribution parameters for innovation
                - alpha2, beta2: Beta distribution parameters for imitation
                - x1inf, x1sup: Innovation productivity change bounds
                - m1: Worker output (modularity)
                - mu1: Mark-up
                - w1avg: Average wage in sector 1
                - w2avg: Average wage in sector 2
                - Ls0, Ls: Initial and current labor supply
        
        Returns:
            Tuple of (new_Atau, new_Btau) - updated productivities
        """
        # Get current technology
        Atau = self.read("_Atau", 1)  # Use previous period's value
        Btau = self.read("_Btau", 1)  # Production productivity from previous period
        
        # R&D effort (normalized by labor supply)
        L1rdN = self.read("_L1rd", 1) * params['Ls0'] / params['Ls']
        
        # Current technology costs
        pTau = self.read("_p1", 1)  # Current price
        cTau = params['w2avg'] / Atau  # Current operating cost
        
        # Initialize: assume innovation/imitation failure
        Ainn = Binn = Atau
        pInn = cInn = float('inf')
        Aimi = Bimi = Atau
        pImi = cImi = float('inf')
        
        # === INNOVATION PROCESS ===
        
        # Innovation success probability (exponential function)
        prob_innovation = 1 - math.exp(-params['zeta1'] * params['xi'] * L1rdN)
        
        if random_engine.bernoulli(prob_innovation):
            # Innovation succeeded!
            
            # Draw productivity improvement from Beta distribution
            # scaled to [x1inf, x1sup] range
            x_draw = beta_draw(params['alpha1'], params['beta1'], 
                              params['x1inf'], params['x1sup'])
            
            # New final productivity (A)
            Ainn = Atau * (1 + x_draw)
            
            # New production productivity (B) 
            Binn = Btau * (1 + x_draw)
            
            # Calculate costs of new innovative machine
            pInn = (1 + params['mu1']) * params['w1avg'] / (Binn * params['m1'])
            cInn = params['w2avg'] / Ainn
        
        # === IMITATION PROCESS ===
        
        # Imitation success probability
        prob_imitation = 1 - math.exp(-params['zeta2'] * (1 - params['xi']) * L1rdN)
        
        if random_engine.bernoulli(prob_imitation):
            # Imitation succeeded!
            
            # Get all other firms in sector 1 for imitation
            competitors = [f for f in self.parent.get_children("Firm1") if f != self]
            
            if len(competitors) > 0:
                # Calculate euclidean distance in technology space
                # Imitation probability inversely proportional to distance
                
                distances = []
                inverse_distances = []
                
                for comp in competitors:
                    # Get competitor's technology
                    A_comp = comp.read("_Atau", 1)
                    B_comp = comp.read("_Btau", 1)
                    
                    # Calculate price and cost of competitor
                    p_comp = (1 + params['mu1']) * params['w1avg'] / (B_comp * params['m1'])
                    c_comp = params['w2avg'] / A_comp
                    
                    # Euclidean distance in normalized (price, cost) space
                    # Normalization by sector averages
                    dist = euclidean_distance(
                        pTau / params['p1avg'], cTau / params['c2avg'],
                        p_comp / params['p1avg'], c_comp / params['c2avg']
                    )
                    
                    distances.append(dist)
                    # Inverse distance (closer firms more likely to be imitated)
                    inverse_distances.append(1.0 / dist if dist > 0 else 0.0)
                
                # Sum of inverse distances for normalization
                total_inv_dist = sum(inverse_distances)
                
                if total_inv_dist > 0:
                    # Create cumulative probability distribution
                    cum_prob = []
                    cum_sum = 0.0
                    for inv_dist in inverse_distances:
                        cum_sum += inv_dist / total_inv_dist
                        cum_prob.append(cum_sum)
                    
                    # Select firm to imitate based on distance
                    r = random_engine.uniform()
                    selected_idx = 0
                    for i, prob in enumerate(cum_prob):
                        if r <= prob:
                            selected_idx = i
                            break
                    
                    # Get imitated technology
                    imitated_firm = competitors[selected_idx]
                    Aimi = imitated_firm.read("_Atau", 1)
                    Bimi = imitated_firm.read("_Btau", 1)
                    
                    # Calculate costs of imitated technology
                    pImi = (1 + params['mu1']) * params['w1avg'] / (Bimi * params['m1'])
                    cImi = params['w2avg'] / Aimi
        
        # === TECHNOLOGY SELECTION ===
        
        # Select best technology among:
        # 1. Current technology
        # 2. Innovative technology (if successful)
        # 3. Imitated technology (if successful)
        
        # Selection criterion: minimize unit cost for client
        # Unit cost = machine price + payback period * operating cost
        b = params.get('b', 10)  # Payback period
        
        cost_current = pTau + b * cTau
        cost_innovation = pInn + b * cInn
        cost_imitation = pImi + b * cImi
        
        if cost_innovation < cost_current and cost_innovation < cost_imitation:
            # Adopt innovative technology
            new_Atau = Ainn
            new_Btau = Binn
        elif cost_imitation < cost_current and cost_imitation < cost_innovation:
            # Adopt imitated technology
            new_Atau = Aimi
            new_Btau = Bimi
        else:
            # Keep current technology
            new_Atau = Atau
            new_Btau = Btau
        
        # Update technology
        self.write("_Atau", new_Atau)
        self.write("_Btau", new_Btau)
        
        return new_Atau, new_Btau
    
    def compute_rd_expenditure(self, nu: float) -> float:
        """
        Compute R&D expenditure
        
        Args:
            nu: R&D share of sales
        
        Returns:
            R&D expenditure
        """
        S1_lag = self.read("_S1", 1)  # Sales in previous period
        
        if S1_lag > 0:
            rd = nu * S1_lag
        else:
            # No sales: keep current expenditure or fraction of available cash
            rd = min(self.read("_RD", 0), nu * self.read("_NW1", 1))
        
        # Always hire at least one worker
        w1avg = self.parent.read("w1avg", 1)
        rd = max(rd, w1avg)
        
        self.write("_RD", rd)
        self._RD = rd
        return rd
    
    def compute_sales_revenue(self) -> float:
        """
        Compute sales revenue (_S1 equation)
        
        Sales of firm in capital-good sector
        Formula: _S1 = _p1 * _Q1e
        
        Returns:
            Sales revenue
        """
        p1 = self.read("_p1")
        Q1e = self.read("_Q1e")
        S1 = p1 * Q1e
        
        self.write("_S1", S1)
        self._S1 = S1
        return S1
    
    def compute_total_wages(self) -> float:
        """
        Compute total wages paid (_W1 equation)
        
        Total wages paid by firm in capital-good sector
        Uses approximation: _W1 = _L1 * w1avg
        
        Returns:
            Total wages paid
        """
        L1 = self.read("_L1")
        try:
            w1avg = self.parent.read("w1avg")
        except:
            w1avg = INIWAGE
        
        W1 = L1 * w1avg
        
        self.write("_W1", W1)
        self._W1 = W1
        return W1
    
    def compute_interest_on_debt(self, rDeb: float, kConst: float) -> float:
        """
        Compute interest paid on debt (_i1 equation)
        
        Interest paid by firm in capital-good sector
        Formula: _i1 = _Deb1(lag) * rDeb * (1 + (qc1(lag) - 1) * kConst)
        
        Args:
            rDeb: Base debt interest rate
            kConst: Credit class premium constant
        
        Returns:
            Interest paid on debt
        """
        Deb1_lag = self.read("_Deb1", 1)
        try:
            qc1_lag = self.read("_qc1", 1)
        except:
            qc1_lag = 1.0
        
        i1 = Deb1_lag * rDeb * (1 + (qc1_lag - 1) * kConst)
        
        self.write("_i1", i1)
        self._i1 = i1 if hasattr(self, '_i1') else 0.0
        if not hasattr(self, '_i1'):
            self._i1 = i1
        else:
            self._i1 = i1
        return i1
    
    def compute_interest_from_deposits(self, rD: float) -> float:
        """
        Compute interest received from deposits (_iD1 equation)
        
        Interest received from deposits by firm in capital-good sector
        Formula: _iD1 = _NW1(lag) * rD
        
        Args:
            rD: Deposit interest rate
        
        Returns:
            Interest from deposits
        """
        NW1_lag = self.read("_NW1", 1)
        iD1 = NW1_lag * rD
        
        self.write("_iD1", iD1)
        self._iD1 = iD1 if hasattr(self, '_iD1') else 0.0
        if not hasattr(self, '_iD1'):
            self._iD1 = iD1
        else:
            self._iD1 = iD1
        return iD1
    
    def compute_profits(self) -> float:
        """
        Compute profits before taxes (_Pi1 equation)
        
        Profit (before taxes) of firm in capital-good sector
        Formula: _Pi1 = _S1 + _iD1 - _W1 - _i1
        
        Returns:
            Profits before taxes
        """
        S1 = self.read("_S1")
        try:
            iD1 = self.read("_iD1")
        except:
            iD1 = 0.0
        W1 = self.read("_W1")
        try:
            i1 = self.read("_i1")
        except:
            i1 = 0.0
        
        Pi1 = S1 + iD1 - W1 - i1
        
        self.write("_Pi1", Pi1)
        self._Pi1 = Pi1
        return Pi1
    
    def compute_price(self, mu1: float) -> float:
        """
        Compute machine price
        
        Args:
            mu1: Mark-up in capital goods sector
        
        Returns:
            Price
        """
        c1 = self.read("_c1")
        p1 = (1 + mu1) * c1
        
        self.write("_p1", p1)
        self._p1 = p1
        return p1
    
    def compute_labor_demand(self, m1: float) -> int:
        """
        Compute labor demand for production and R&D
        
        Args:
            m1: Worker output (machines per period)
        
        Returns:
            Total labor demand
        """
        # R&D labor
        L1dRD = self.compute_rd_labor_demand()
        
        # Production labor
        Q1 = self.read("_Q1")
        Btau = self.read("_Btau")
        
        L1dProd = math.ceil(Q1 / (Btau * m1)) if Btau * m1 > 0 else 0
        
        # Total labor demand
        L1d = L1dRD + L1dProd
        
        self.write("_L1d", L1d)
        self._L1d = L1d
        return L1d
    
    def compute_rd_labor_demand(self) -> int:
        """
        Compute R&D labor demand
        
        Returns:
            R&D workers needed
        """
        RD = self.read("_RD")
        w1avg = self.parent.read("w1avg", 1)
        
        L1dRD = math.ceil(RD / w1avg) if w1avg > 0 else 1
        
        # Apply maximum R&D share constraint
        L1rdMax = self.parent.get_param("L1rdMax", 0.5)
        L1 = self.read("_L1", 1)
        
        if L1 > 0:
            L1dRD = min(L1dRD, math.floor(L1rdMax * L1))
        
        self.write("_L1dRD", L1dRD)
        return L1dRD
    
    def compute_market_share(self, n1: int) -> float:
        """
        Compute market share
        
        Args:
            n1: Number of periods for evaluation
        
        Returns:
            Market share
        """
        # Sum sales over last n1 periods
        sales_sum = sum(self.read("_S1", lag) for lag in range(1, n1 + 1))
        
        # Sum of all firms' sales
        total_sales = 0.0
        for firm in self.parent.get_children("Firm1"):
            firm_sales = sum(firm.read("_S1", lag) for lag in range(1, n1 + 1))
            total_sales += firm_sales
        
        # Market share
        f1 = safe_divide(sales_sum, total_sales, 0.0)
        
        self.write("_f1", f1)
        self._f1 = f1
        return f1
    
    def distribute_brochures(self, gamma: float) -> int:
        """
        Distribute brochures to potential clients
        
        New and existing clients receive information about this firm's machines
        
        Args:
            gamma: Share of new clients to target
        
        Returns:
            Number of new clients reached
        """
        # This is a placeholder - full implementation requires
        # interaction with Firm2 agents and client management
        return 0
    
    def check_exit_conditions(self) -> bool:
        """
        Check if firm should exit market
        
        Returns:
            True if firm should exit
        """
        # Exit if market share too low or negative net worth
        f1min = self.parent.get_param("f1min", 0.001)
        
        if self._f1 < f1min or self._NW1 < 0:
            return True
        
        return False
