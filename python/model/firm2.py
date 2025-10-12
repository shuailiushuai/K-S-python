"""
Firm2 Agent Implementation (Consumption Goods Sector)
Represents consumption goods producers
"""

from typing import Optional, List, Tuple
from .agent import Agent
from .vintage import VintageAgent
from .constants import *
from .random_engine import random_engine
from .support import safe_divide, moving_average
import math


class Firm2(Agent):
    """
    Firm2 agent class (Consumption Goods Sector)
    
    Consumption goods firms:
    - Form demand expectations (multiple modes)
    - Plan production with vintage capital
    - Invest in new machines
    - Hire and fire workers
    - Set wages and prices
    - Compete in the consumption market
    """
    
    def __init__(self, firm_id: int, parent: Agent):
        """
        Initialize Firm2 agent
        
        Args:
            firm_id: Unique firm ID
            parent: Parent Consumption sector object
        """
        super().__init__("Firm2", parent)
        
        # Firm attributes
        self._ID2 = firm_id
        self._t2ent = 0                   # Entry time
        self._life2cycle = 0              # Life cycle stage
        self._postChg = False             # Post regime change flag
        
        # Production and capacity
        self._Q2 = 0.0                    # Planned production
        self._Q2d = 0.0                   # Desired production
        self._Q2e = 0.0                   # Effective production
        self._A2 = INIPROD                # Average labor productivity
        self._D2 = 0.0                    # Demand (expected sales)
        self._D2e = 0.0                   # Effective demand
        self._N = 0                       # Stock of inventories
        
        # Capital
        self._K = 0.0                     # Capital stock (machines × price)
        self._Kd = 0.0                    # Desired capital
        self._EI = 0.0                    # Expansion investment
        self._SI = 0.0                    # Substitution investment
        self._CI = 0.0                    # Canceled investment
        self._Knom = 0                    # Number of machines
        
        # Labor
        self._L2 = 0                      # Actual workers
        self._L2d = 0                     # Desired workers
        self._w2avg = 0.0                 # Average wage
        self._w2o = 0.0                   # Offered wage
        
        # Costs and pricing
        self._c2 = 0.0                    # Unit cost
        self._c2e = 0.0                   # Effective unit cost
        self._p2 = 0.0                    # Price
        self._mu2 = 0.0                   # Mark-up
        
        # Financial
        self._NW2 = 0.0                   # Net worth
        self._Deb2 = 0.0                  # Debt stock
        self._S2 = 0.0                    # Sales revenue
        self._Pi2 = 0.0                   # Gross profits
        self._Tax2 = 0.0                  # Taxes paid
        self._Div2 = 0.0                  # Dividends paid
        self._Bon2 = 0.0                  # Worker bonus
        self._W2 = 0.0                    # Total wages paid
        self._i2 = 0.0                    # Interest paid on debt
        self._iD2 = 0.0                   # Interest from deposits
        
        # Market
        self._f2 = 0.0                    # Market share
        self._age2 = 0                    # Firm age
        self._l2 = 0.0                    # Unfilled demand
        
        # Supplier management
        self._supplier = None             # Current supplier (Firm1)
        self._Atau = INIPROD              # Supplier technology (A)
        self._Btau = INIPROD              # Supplier technology (B)
        
        # Initialize hooks
        self.add_hooks(FIRM2HK)
        
        # Extension for job applications
        from .data_structures import Firm2Extension
        self._extension = Firm2Extension()
    
    def compute_demand_expectation(self, mode: int, params: dict) -> float:
        """
        Compute demand expectation for next period (_D2e equation)
        
        Exactly matches fun_KS_firm2.h _D2e equation logic
        
        Multiple expectation modes (flagExpect):
        0: Myopic with 1-period memory
        1: Myopic with up to 4-period memory
        2: Accelerating GD expectations
        3: 1st order adaptive expectations
        4: Extrapolative-accelerating expectations
        
        Args:
            mode: Expectation formation mode (0-4)
            params: Dictionary with expectation parameters:
                - e0: Animal spirits parameter
                - e1, e2, e3, e4: Weights for mode 1
                - e5: Acceleration parameter for mode 2
                - e6: Adaptation parameter for mode 3
                - e7, e8: Parameters for mode 4
                - iota: Desired inventory adjustment
        
        Returns:
            Expected demand
        """
        # Entrant firms use myopic-optimistic expectations
        if self._life2cycle < 3:
            D2d_lag1 = self.read("_D2d", 1)
            D2e_current = self.read("_D2e")
            D2e = max(D2d_lag1, D2e_current)
            self.write("_D2e", D2e)
            self._D2e = D2e
            return D2e
        
        # Get parameters
        e0 = params.get('e0', 0.0)  # Animal spirits parameter
        
        # Determine number of required data periods
        if mode == 0 or mode > 4:
            j = 1
        elif mode == 1:
            j = 4
        else:
            j = 2
        
        # Compute mix between fulfilled and potential demand (orders)
        v = {}
        for i in range(1, j + 1):
            D2_lag = self.read("_D2", i)  # Fulfilled demand
            D2d_lag = self.read("_D2d", i)  # Desired demand
            v[i] = max((1 - e0) * D2_lag + e0 * D2d_lag, D2_lag)
        
        # Apply expectation mode
        if mode == 0:
            # Myopic expectations with 1-period memory
            D2e = v[1]
            
        elif mode == 1:
            # Myopic expectations with up to 4-period memory
            e1 = params.get('e1', 1.0)
            e2 = params.get('e2', 0.0)
            e3 = params.get('e3', 0.0)
            e4 = params.get('e4', 0.0)
            
            v_sum = 0.0
            w_sum = 0.0
            weights = [e1, e2, e3, e4]
            
            for i in range(1, 5):
                if v.get(i, 0) > 0:  # Consider only periods with demand
                    v_sum += weights[i-1] * v[i]
                    w_sum += weights[i-1]
            
            D2e = v_sum / w_sum if w_sum > 0 else 0
            
        elif mode == 2:
            # Accelerating GD expectations
            e5 = params.get('e5', 0.1)
            v1 = v.get(1, 0)
            v2 = max(v.get(2, 1), 1)  # Floor to positive only
            D2e = (1 + e5 * (v1 - v2) / v2) * v1
            
        elif mode == 3:
            # 1st order adaptive expectations
            e6 = params.get('e6', 0.5)
            v1 = v.get(1, 0)
            v2 = v.get(2, 0)
            D2e_current = self.read("_D2e")
            D2e = D2e_current + e6 * (v1 - v2)
            
        else:  # mode == 4
            # Extrapolative-accelerating expectations
            e7 = params.get('e7', 0.1)
            e8 = params.get('e8', 0.5)
            v1 = v.get(1, 0)
            v2 = max(v.get(2, 1), 1)  # Floor to positive only
            
            # Need dGDP from grandparent (Country)
            try:
                grandparent = self.parent.parent  # Country
                dGDP_lag1 = grandparent.read("dGDP", 1)
            except:
                dGDP_lag1 = 0.0
            
            D2e = (1 + e7 * (v1 - v2) / v2 + e8 * dGDP_lag1) * v1
        
        D2e = max(0, D2e)  # Cannot be negative
        
        self.write("_D2e", D2e)
        self._D2e = D2e
        return D2e
    
    def compute_desired_production(self, u: float) -> float:
        """
        Compute desired production level
        
        Args:
            u: Desired utilization rate
        
        Returns:
            Desired production quantity
        """
        D2e = self.read("_D2e")
        N = self.read("_N", 1)  # Current inventories
        
        # Desired production = expected demand - inventories + target inventories
        Q2d = D2e - N + u * D2e
        Q2d = max(0, Q2d)
        
        self.write("_Q2d", Q2d)
        self._Q2d = Q2d
        return Q2d
    
    def compute_labor_productivity(self) -> float:
        """
        Compute average labor productivity across all vintages
        
        Returns:
            Average productivity
        """
        total_workers = 0
        weighted_prod = 0.0
        
        for vintage in self.get_children("Vint"):
            L_vint = vintage.read("_LdVint", 0)
            A_vint = vintage.read("_Avint", 0)
            
            weighted_prod += L_vint * A_vint
            total_workers += L_vint
        
        A2 = safe_divide(weighted_prod, total_workers, INIPROD)
        
        self.write("_A2", A2)
        self._A2 = A2
        return A2
    
    def compute_desired_capital(self, m2: float) -> float:
        """
        Compute desired capital stock
        
        Args:
            m2: Machine modularity (workers per machine)
        
        Returns:
            Desired capital value
        """
        Q2d = self.read("_Q2d")
        A2 = self.read("_A2")
        
        # Desired number of machines
        Knom_d = math.ceil(safe_divide(Q2d, A2 * m2, 0))
        
        # Get average machine price
        # (In full implementation, this would use supplier price)
        p1avg = self.parent.read("p1avg", 1) if self.parent else 1.5
        
        Kd = Knom_d * p1avg
        
        self.write("_Kd", Kd)
        self._Kd = Kd
        return Kd
    
    def compute_investment_plan(self, params: dict) -> Tuple[float, float, float]:
        """
        Compute investment in new machines
        
        Firms invest for:
        1. Expansion: increase capacity
        2. Substitution: replace old/inefficient machines
        
        Args:
            params: Dictionary with:
                - eta: Technical machine lifetime
                - m2: Machine modularity
                - current_time: Current simulation time
        
        Returns:
            Tuple of (expansion_investment, substitution_investment, total_orders)
        """
        K = self.read("_K", 1)
        Kd = self.read("_Kd")
        
        # Expansion investment
        EI = max(0, Kd - K)
        
        # Substitution investment: replace scrapped machines
        SI = 0.0
        for vintage in self.get_children("Vint"):
            RS_vint = vintage.read("__RSvint", 0)
            if RS_vint > 0:  # Machines to scrap
                # Get supplier price
                supplier = self.read("_supplier")
                if supplier:
                    p1 = supplier.read("_p1")
                    m2 = params['m2']
                    SI += RS_vint * p1 / m2
        
        self.write("_EI", EI)
        self.write("_SI", SI)
        self._EI = EI
        self._SI = SI
        
        return EI, SI, EI + SI
    
    def compute_markup(self, upsilon: float, f2min: float) -> float:
        """
        Compute firm's mark-up (_mu2 equation)
        
        Exactly matches fun_KS_firm2.h _mu2 equation (lines 546-558)
        
        Mark-up adjusts based on market share changes:
        - Increasing market share → increase mark-up
        - Decreasing market share → decrease mark-up
        - Just-entered firms keep initial mark-up
        
        Args:
            upsilon: Mark-up adjustment parameter
            f2min: Minimum market share threshold
        
        Returns:
            Updated mark-up
        """
        # Get past market shares
        f2_lag1 = self.read("_f2", 1)
        f2_lag2 = self.read("_f2", 2)
        mu2_current = self.read("_mu2")
        
        # Just entered firms keep initial mark-up
        if f2_lag1 < f2min or f2_lag2 < f2min:
            mu2 = mu2_current
        else:
            # Adjust based on market share trend
            if f2_lag2 > 0:
                mu2 = mu2_current * (1 + upsilon * (f2_lag1 / f2_lag2 - 1))
            else:
                mu2 = mu2_current
        
        # Ensure non-negative
        mu2 = max(0, mu2)
        
        self.write("_mu2", mu2)
        self._mu2 = mu2
        return mu2
    
    def compute_labor_demand(self, m2: float) -> int:
        """
        Compute desired labor force
        
        Args:
            m2: Machine modularity
        
        Returns:
            Desired number of workers
        """
        Q2d = self.read("_Q2d")
        A2 = self.read("_A2")
        
        L2d = math.ceil(safe_divide(Q2d, A2, 0))
        
        self.write("_L2d", L2d)
        self._L2d = L2d
        return L2d
    
    def compute_wage_offer(self, params: dict) -> float:
        """
        Compute wage offer for new hires
        
        Wages may include:
        - Base wage (sector average or firm-specific)
        - Premium based on firm performance
        - Regime-specific adjustments
        
        Args:
            params: Dictionary with:
                - flagWageMode: Wage setting mode
                - wCent: Centralized wage (if applicable)
                - Various premium parameters
        
        Returns:
            Wage offer
        """
        flagWageMode = params.get('flagWageMode', 0)
        
        if flagWageMode == 0:
            # Homogeneous wages: use central wage
            w2o = params.get('wCent', 1.0)
        else:
            # Heterogeneous wages: use average wage with potential premium
            w2avg_lag = self.read("_w2avg", 1)
            
            # Add premium based on profitability (simplified)
            Pi2_lag = self.read("_Pi2", 1)
            S2_lag = self.read("_S2", 1)
            
            if S2_lag > 0 and Pi2_lag > 0:
                profit_margin = Pi2_lag / S2_lag
                premium = min(0.1, profit_margin * 0.5)  # Max 10% premium
            else:
                premium = 0
            
            w2o = w2avg_lag * (1 + premium)
        
        w2o = max(w2o, params.get('w0min', 0.5))  # Minimum wage floor
        
        self.write("_w2o", w2o)
        self._w2o = w2o
        return w2o
    
    def compute_price(self, params: dict) -> float:
        """
        Compute product price
        
        Price is based on:
        - Unit cost
        - Mark-up (may be adjusted based on competition)
        
        Args:
            params: Dictionary with:
                - mu20: Initial mark-up
                - omega1: Mark-up adjustment parameter
                - Various competition parameters
        
        Returns:
            Price
        """
        c2 = self.read("_c2")
        
        # Get current mark-up (simplified - in full model, mark-up adjusts)
        mu2 = self.read("_mu2", 1) if self.read("_mu2", 1) > 0 else params.get('mu20', 0.2)
        
        p2 = (1 + mu2) * c2
        p2 = max(p2, c2)  # Price must cover costs
        
        self.write("_p2", p2)
        self._p2 = p2
        return p2
    
    def compute_unit_cost(self, w2avg: float) -> float:
        """
        Compute unit production cost
        
        Args:
            w2avg: Average wage
        
        Returns:
            Unit cost
        """
        A2 = self.read("_A2")
        c2 = safe_divide(w2avg, A2, 1.0)
        
        self.write("_c2", c2)
        self._c2 = c2
        return c2
    
    def compute_effective_unit_cost(self) -> float:
        """
        Compute effective average unit cost (_c2e equation)
        
        Effective average unit cost of firm in consumption-good sector.
        Use expected cost if firm is not producing.
        
        Returns:
            Effective unit cost
        """
        Q2e = self.read("_Q2e")
        W2 = self.read("_W2")
        c2 = self.read("_c2")
        
        # If producing, compute actual unit cost; otherwise use expected
        c2e = safe_divide(W2, Q2e, c2)
        
        self.write("_c2e", c2e)
        self._c2e = c2e
        return c2e
    
    def compute_interest_from_deposits(self, rD: float) -> float:
        """
        Compute interest received from deposits (_iD2 equation)
        
        Interest received from deposits by firm in consumption-good sector
        
        Args:
            rD: Deposit interest rate
        
        Returns:
            Interest from deposits
        """
        NW2_lag = self.read("_NW2", 1)
        iD2 = NW2_lag * rD
        
        self.write("_iD2", iD2)
        self._iD2 = iD2 if hasattr(self, '_iD2') else 0.0
        if not hasattr(self, '_iD2'):
            self._iD2 = iD2
        else:
            self._iD2 = iD2
        return iD2
    
    def compute_market_share(self, n2: int) -> float:
        """
        Compute market share
        
        Args:
            n2: Number of periods for evaluation
        
        Returns:
            Market share
        """
        # Sum sales over last n2 periods
        sales_sum = sum(self.read("_S2", lag) for lag in range(1, n2 + 1))
        
        # Sum of all firms' sales
        total_sales = 0.0
        for firm in self.parent.get_children("Firm2"):
            firm_sales = sum(firm.read("_S2", lag) for lag in range(1, n2 + 1))
            total_sales += firm_sales
        
        # Market share
        f2 = safe_divide(sales_sum, total_sales, 0.0)
        
        self.write("_f2", f2)
        self._f2 = f2
        return f2
    
    def select_supplier(self, firm1_list: List) -> Optional[object]:
        """
        Select machine supplier from available Firm1 agents
        
        Selection based on competitiveness measure combining
        price and productivity
        
        Args:
            firm1_list: List of available Firm1 suppliers
        
        Returns:
            Selected supplier or None
        """
        if not firm1_list:
            return None
        
        # Evaluate each supplier
        best_supplier = None
        best_score = float('inf')
        
        for supplier in firm1_list:
            p1 = supplier.read("_p1")
            Atau = supplier.read("_Atau")
            
            # Competitiveness score: unit cost to client
            # Lower is better
            score = safe_divide(p1, Atau, float('inf'))
            
            if score < best_score:
                best_score = score
                best_supplier = supplier
        
        if best_supplier:
            self._supplier = best_supplier
            self._Atau = best_supplier.read("_Atau")
            self._Btau = best_supplier.read("_Btau")
            self.write("_supplier", best_supplier)
            self.write("_Atau", self._Atau)
            self.write("_Btau", self._Btau)
        
        return best_supplier
    
    def check_exit_conditions(self) -> bool:
        """
        Check if firm should exit market
        
        Returns:
            True if firm should exit
        """
        # Exit if market share too low or negative net worth
        f2min = self.parent.get_param("f2min", 0.001) if self.parent else 0.001
        
        if self._f2 < f2min or self._NW2 < 0:
            return True
        
        return False
    
    def compute_total_wages(self) -> float:
        """
        Compute total wages paid by firm (_W2 equation)
        
        Total wages paid by firm in sector 2
        Sum of all wages paid to employed workers
        
        Returns:
            Total wages paid
        """
        # In a full implementation, this would sum wages from all Wrk2 worker objects
        # For now, use approximation: _L2 * _w2avg
        L2 = self.read("_L2")
        w2avg = self.read("_w2avg")
        
        W2 = L2 * w2avg
        
        self.write("_W2", W2)
        self._W2 = W2
        return W2
    
    def compute_interest_on_debt(self, rDeb: float, kConst: float) -> float:
        """
        Compute interest paid on debt (_i2 equation)
        
        Interest paid by firm in consumption-good sector
        Based on lagged debt, interest rate, and credit class premium
        
        Args:
            rDeb: Base debt interest rate
            kConst: Credit class premium constant
        
        Returns:
            Interest paid on debt
        """
        Deb2_lag = self.read("_Deb2", 1)
        try:
            qc2_lag = self.read("_qc2", 1)
        except:
            qc2_lag = 1.0
        
        # Interest = debt * (base rate + credit class premium)
        i2 = Deb2_lag * rDeb * (1 + (qc2_lag - 1) * kConst)
        
        self.write("_i2", i2)
        self._i2 = i2 if hasattr(self, '_i2') else 0.0
        if not hasattr(self, '_i2'):
            self._i2 = i2
        else:
            self._i2 = i2
        return i2
    
    def compute_profits(self) -> float:
        """
        Compute profits before taxes (_Pi2 equation)
        
        Profit of firm (before taxes) in consumption-good sector
        Formula: _Pi2 = _S2 + _iD2 - _W2 - _i2
        
        Returns:
            Profits before taxes
        """
        S2 = self.read("_S2")
        try:
            iD2 = self.read("_iD2")
        except:
            iD2 = 0.0
        W2 = self.read("_W2")
        try:
            i2 = self.read("_i2")
        except:
            i2 = 0.0
        
        Pi2 = S2 + iD2 - W2 - i2
        
        self.write("_Pi2", Pi2)
        self._Pi2 = Pi2
        return Pi2
    
    def initialize(self, params: dict):
        """
        Initialize firm with parameters
        
        Args:
            params: Dictionary with initialization values
        """
        self._t2ent = params.get('entry_time', 0)
        self._life2cycle = params.get('life_cycle', 0)
        self._A2 = params.get('A2', INIPROD)
        self._NW2 = params.get('NW2', 10.0)
        self._mu2 = params.get('mu2', 0.2)
        
        # Write initial values
        self.write("_t2ent", self._t2ent)
        self.write("_life2cycle", self._life2cycle)
        self.write("_A2", self._A2)
        self.write("_NW2", self._NW2)
        self.write("_mu2", self._mu2)
