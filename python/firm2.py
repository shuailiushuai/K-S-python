"""
Firm2 (Consumption-Good Sector) Agent Implementation
Implements consumer-good producing firms with capital vintages.
Based on fun_KS_firm2.h and fun_KS_consumption.h
"""

from typing import Dict, Any, Optional, List
from .agents import BaseAgent, Vintage
from .config import *
from .random_generator import random_engine


class Firm2(BaseAgent):
    """
    Consumption-good firm agent.
    Produces consumer goods using capital (machines) and labor.
    """
    
    def __init__(self, agent_id: int, parent: BaseAgent):
        super().__init__(agent_id, "Firm2", parent)
        
        # Firm attributes
        self._ID2 = agent_id
        self._life2cycle = 0
        
        # Net worth and finance
        self._NW2 = 0.0
        self._Deb2 = 0.0
        self._Deb2max = 0.0
        self._CD2 = 0.0   # Credit demand
        self._CD2c = 0.0  # Credit constraint flag
        self._CS2 = 0.0   # Credit supplied
        
        # Production and capital
        self._K = 0.0     # Capital stock (number of machines)
        self._Kd = 0.0    # Desired capital
        self._Q2 = 0.0    # Planned production
        self._Q2d = 0.0   # Desired production capacity
        self._Q2e = 0.0   # Effective production
        self._q2 = 0.0    # Unit production
        
        # Demand and sales
        self._D2e = 0.0   # Expected demand
        self._D2d = 0.0   # Potential demand (orders)
        self._D2 = 0.0    # Realized demand
        self._S2 = 0.0    # Sales
        self._N = 0.0     # Inventories
        
        # Costs and prices
        self._c2 = 0.0    # Unit cost
        self._p2 = 0.0    # Price
        self._mu2 = 0.0   # Markup
        
        # Market shares
        self._f2 = 0.0    # Market share
        self._E = 0.0     # Competitiveness
        
        # Labor
        self._L2 = 0.0    # Current labor
        self._L2d = 0.0   # Desired labor
        self._w2avg = 0.0 # Average wage
        self._W2 = 0.0    # Wage bill
        
        # Investment
        self._EI = 0.0    # Investment expenditure
        self._EId = 0.0   # Desired investment expenditure
        self._SI = 0.0    # Investment plans
        
        # Profits and distributions
        self._Pi2 = 0.0   # Profits
        self._Tax2 = 0.0  # Taxes
        self._Bon2 = 0.0  # Bonuses
        self._Div2 = 0.0  # Dividends
        
        # Flags
        self._postChg = False  # Post regime change flag
    
    def compute_expected_demand(self, params: Dict[str, Any], t: int) -> float:
        """
        Compute adaptive demand expectation (_D2e).
        Based on fun_KS_firm2.h _D2e equation.
        """
        if self._life2cycle < 3:  # Entrant firm
            # Myopic-optimistic expectations
            D2d_lag1 = self.VL("_D2d", 1)
            current = self.V("_D2e")
            return max(D2d_lag1, current)
        
        flag_expect = int(params.get('flagExpect', 0))
        
        # Compute mix between fulfilled and potential demand
        e0 = params.get('e0', 0.5)  # Animal spirits
        
        if flag_expect == 0:  # Myopic 1-period
            j = 1
        elif flag_expect == 1:  # Myopic 4-period
            j = 4
        else:  # Accelerator
            j = 2
        
        # Mix fulfilled and potential demand
        demands = []
        for i in range(1, j + 1):
            D2_lag = self.VL("_D2", i)
            D2d_lag = self.VL("_D2d", i)
            demand = max((1 - e0) * D2_lag + e0 * D2d_lag, D2_lag)
            demands.append(demand)
        
        if flag_expect == 0:  # Myopic 1-period
            expected = demands[0] if demands else 0.0
        elif flag_expect == 1:  # Myopic 4-period weighted
            e1 = params.get('e1', 0.25)
            e2 = params.get('e2', 0.25)
            e3 = params.get('e3', 0.25)
            e4 = params.get('e4', 0.25)
            weights = [e1, e2, e3, e4]
            
            total_weight = 0.0
            weighted_sum = 0.0
            for i, demand in enumerate(demands):
                if demand > 0:
                    weighted_sum += weights[i] * demand
                    total_weight += weights[i]
            
            expected = weighted_sum / total_weight if total_weight > 0 else 0.0
        else:  # Accelerator mode (simplified)
            if len(demands) >= 2:
                expected = demands[0] + (demands[0] - demands[1])
            else:
                expected = demands[0] if demands else 0.0
        
        return expected
    
    def compute_markup(self, params: Dict[str, Any]) -> float:
        """
        Compute variable markup (_mu2).
        Based on fun_KS_firm2.h _mu2 equation.
        """
        f1_lag1 = self.VL("_f2", 1)
        f1_lag2 = self.VL("_f2", 2)
        f2min = params.get('f2min', 0.01)
        
        # Just entered firms keep their markup
        if f1_lag1 < f2min or f1_lag2 < f2min:
            return self.V("_mu2")
        
        upsilon = params.get('upsilon', 0.02)
        
        # Adjust markup based on market share changes
        if f1_lag1 > f1_lag2:  # Gaining share
            new_mu = self._mu2 * (1 + upsilon)
        elif f1_lag1 < f1_lag2:  # Losing share
            new_mu = self._mu2 / (1 + upsilon)
        else:  # Stable share
            new_mu = self._mu2
        
        return new_mu
    
    def compute_desired_capital(self, params: Dict[str, Any]) -> float:
        """
        Compute desired capital stock (_Kd).
        Based on fun_KS_firm2.h _Kd equation.
        """
        # Ensure expected demand is computed
        D2e = self.V("_D2e")
        m2 = params.get('m2', 1.0)  # Machine output
        u = params.get('u', 0.8)    # Desired utilization
        iota = params.get('iota', 0.1)  # Inventories target
        N_lag1 = self.VL("_N", 1)  # Previous inventories
        
        if D2e <= 0:
            return self.VL("_K", 1)
        
        # Desired capital allowing for inventories adjustment
        Kd = (D2e * (1 + iota) - N_lag1) / (m2 * u)
        
        return max(Kd, 0.0)
    
    def compute_investment_plans(self, params: Dict[str, Any]) -> float:
        """
        Compute investment plans (_SI).
        Based on fun_KS_firm2.h _SI equation.
        """
        K_lag1 = self.VL("_K", 1)
        Kd = self.V("_Kd")
        
        # Expansion investment
        EI = max(Kd - K_lag1, 0.0)
        
        # Replacement investment (simplified - would need vintage tracking)
        # For now, assume a fixed depreciation rate
        delta = params.get('delta', 0.05)
        RS = delta * K_lag1
        
        # Total investment
        SI = EI + RS
        
        return SI
    
    def compute_max_debt(self, params: Dict[str, Any]) -> float:
        """
        Compute maximum prudential debt (_Deb2max).
        Also updates _CD2, _CD2c, _CS2.
        Based on fun_KS_firm2.h _Deb2max equation.
        """
        Lambda = params.get('Lambda', 2.0)
        Lambda0 = params.get('Lambda0', 5.0)
        
        NW2_lag1 = self.VL("_NW2", 1)
        S2_lag1 = self.VL("_S2", 1)
        W2_lag1 = self.VL("_W2", 1)
        
        # Maximum debt based on net worth and margin
        max_debt1 = Lambda * max(NW2_lag1, S2_lag1 - W2_lag1)
        
        # Absolute floor (simplified - would need PPI)
        pK0 = params.get('pK0', 1.0)
        max_debt2 = Lambda0 * 1.0 / pK0  # Using 1.0 as PPI placeholder
        
        max_debt = max(max_debt1, max_debt2)
        
        # Reset credit variables
        self.WRITE("_CD2", 0.0)
        self.WRITE("_CD2c", 0.0)
        self.WRITE("_CS2", 0.0)
        
        return max_debt
    
    def compute_bonuses(self, params: Dict[str, Any]) -> float:
        """
        Compute bonuses to workers (_Bon2).
        Based on fun_KS_firm2.h _Bon2 equation.
        """
        Pi2 = self.V("_Pi2")
        Tax2 = self.V("_Tax2")
        net_profit = Pi2 - Tax2
        
        K_lag1 = self.VL("_K", 1)
        L2 = self.V("_L2")
        
        if net_profit <= 0 or K_lag1 <= 0 or L2 <= 0:
            return 0.0
        
        # Check if profitability exceeds average (simplified)
        # Would need parent's Pi2rateAvg
        psi6 = params.get('psi6', 0.1)
        
        # Simplified: pay bonus if profitable
        return psi6 * net_profit
    
    def compute_dividends(self, params: Dict[str, Any]) -> float:
        """
        Compute dividends (_Div2).
        Based on fun_KS_firm2.h _Div2 equation.
        """
        d2 = params.get('d2', 0.5)
        Pi2 = self.V("_Pi2")
        Tax2 = self.V("_Tax2")
        Bon2 = self.V("_Bon2")
        
        dividends = d2 * (Pi2 - Tax2 - Bon2)
        return max(dividends, 0.0)
    
    def compute_competitiveness(self, params: Dict[str, Any]) -> float:
        """
        Compute competitiveness index (_E).
        Based on fun_KS_consumption.h _E equation.
        """
        omega1 = params.get('omega1', 1.0)  # Price weight
        omega2 = params.get('omega2', 0.0)  # Delivery time weight
        
        # Simplified competitiveness (price-based)
        # Full version would include delivery times
        p2 = self.V("_p2")
        
        if p2 <= 0:
            return 0.0
        
        # Competitiveness is inverse of price (normalized)
        E = 1.0 / p2
        
        return E
    
    def compute_market_share(self, params: Dict[str, Any], total_E: float) -> float:
        """
        Compute market share (_f2).
        Based on replicator dynamics.
        """
        if total_E <= 0:
            # Equal shares if no competitiveness computed
            parent = self.parent
            n_firms = parent.count_children("Firm2")
            return 1.0 / n_firms if n_firms > 0 else 0.0
        
        chi = params.get('chi', 1.0)
        E = self.V("_E")
        f2_lag1 = self.VL("_f2", 1)
        
        # Replicator dynamics
        f2 = f2_lag1 * (1 + chi * (E / total_E - 1))
        
        # Ensure market shares sum to 1 (normalization done at sector level)
        return max(f2, 0.0)
    
    def compute_unit_cost(self, params: Dict[str, Any]) -> float:
        """
        Compute unit cost (_c2).
        Based on fun_KS_firm2.h _c2 equation.
        """
        Q2e = self.V("_Q2e")
        W2 = self.V("_W2")
        
        if Q2e <= 0:
            # Use lagged cost
            return self.VL("_c2", 1)
        
        # Unit labor cost
        c2 = W2 / Q2e
        
        return c2
    
    def compute_price(self) -> float:
        """
        Compute price (_p2).
        """
        mu2 = self.V("_mu2")
        c2 = self.V("_c2")
        
        return (1 + mu2) * c2
    
    def allocate_workers_to_vintages(self, params: Dict[str, Any], 
                                     workers: List[BaseAgent], 
                                     vintages: List[BaseAgent],
                                     Lscale: float) -> int:
        """
        Allocate workers to vintages, prioritizing newer vintages.
        Based on _alloc2 equation in fun_KS_firm2.h
        
        Args:
            params: Model parameters
            workers: List of Wrk2 worker bridge objects
            vintages: List of vintage objects (ordered newest first)
            Lscale: Labor scaling factor
            
        Returns:
            Number of workers allocated (unscaled)
        """
        if not vintages:
            return 0
        
        flagWorkerLBU = params.get('flagWorkerLBU', 0)
        vint_learn = (flagWorkerLBU != 0 and flagWorkerLBU != 2)
        
        # Start with newest vintage (TOPVINT = first in list)
        allocations = 0
        
        # Phase 1: Allocate unallocated workers to top vintages
        # Go from newest to oldest
        vint_idx = 0
        current_vint = vintages[vint_idx] if vint_idx < len(vintages) else None
        
        if current_vint:
            labor_needed = current_vint.V("__dLdVint")
            
            for worker_bridge in workers:
                worker = worker_bridge.get_hook("worker")
                if not worker:
                    continue
                
                # Check if worker is unallocated (no vintage bridge)
                if worker.get_hook("VWRK") is None:
                    # Find vintage with open positions
                    while labor_needed == 0 and vint_idx < len(vintages) - 1:
                        vint_idx += 1
                        current_vint = vintages[vint_idx]
                        if current_vint.V("__toUseVint") == 0:
                            # No more vintages in use
                            break
                        labor_needed = current_vint.V("__dLdVint")
                    
                    if labor_needed > 0 and current_vint:
                        # Move worker to this vintage
                        self.move_worker_to_vintage(worker, current_vint, vint_learn, params)
                        allocations += 1
                        labor_needed -= 1
        
        # Phase 2: Try to move workers from older to newer vintages
        # to better utilize newer technology
        for old_vint_idx, old_vint in enumerate(vintages):
            # Get workers in this vintage (WrkV bridge objects)
            old_vint_workers = old_vint.get_children("WrkV")
            
            for worker_bridge in old_vint_workers:
                worker = worker_bridge.get_hook("worker")
                if not worker:
                    continue
                
                # Find newer vintage with open positions
                vint_idx = 0
                current_vint = vintages[vint_idx] if vint_idx < len(vintages) else None
                
                if current_vint:
                    labor_needed = current_vint.V("__dLdVint")
                    
                    # Find vintage with open positions (newer than current)
                    while labor_needed == 0 and vint_idx < old_vint_idx:
                        vint_idx += 1
                        if vint_idx >= old_vint_idx:
                            break
                        current_vint = vintages[vint_idx]
                        labor_needed = current_vint.V("__dLdVint")
                    
                    if labor_needed > 0 and vint_idx < old_vint_idx:
                        # Remove from old vintage
                        worker.set_hook("VWRK", None)
                        
                        # Move to new vintage
                        self.move_worker_to_vintage(worker, current_vint, vint_learn, params)
                        allocations += 1
        
        return allocations
    
    def move_worker_to_vintage(self, worker: BaseAgent, vintage: BaseAgent, 
                               vint_learn: bool, params: Dict[str, Any]):
        """
        Move a worker to a vintage.
        Based on move_worker() in fun_KS_support.h
        
        Args:
            worker: Worker agent
            vintage: Vintage agent
            vint_learn: Whether learning-by-vintage is active
            params: Model parameters
        """
        # Determine vintage skills
        if vint_learn:
            # Learning by vintage - get public skills for this vintage
            IDv = vintage.V("__IDvint")
            # Get from country extension
            country_ext = worker.grandparent.extensions.get('country')
            if country_ext and IDv in country_ext.vintProd:
                sV = country_ext.vintProd[IDv].sVp
            else:
                sV = INISKILL
        else:
            sV = INISKILL
        
        # Create worker-vintage bridge object
        wrkV = BaseAgent(worker.V("_ID"), "WrkV", vintage)
        vintage.add_child("WrkV", wrkV)
        wrkV.set_hook("worker", worker)  # Save pointer to worker
        worker.set_hook("VWRK", wrkV)     # Register vintage in worker
        
        # Set worker skills and reset cumulated production
        worker.WRITE("_sV", sV)
        worker.WRITE("_CQ", 0)
