"""
Capital-Good Firm (Firm1) Agent

Firms in the capital-good sector:
- Perform R&D (innovation and imitation)
- Produce heterogeneous machine tools
- Compete via technological innovation
- Serve consumption-good firms as clients
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from scipy.stats import beta as beta_dist


class Firm1:
    """
    Capital-good firm agent (Firm1)
    
    These firms engage in R&D to develop new machine technologies,
    produce machines, and sell them to consumption-good firms.
    """
    
    def __init__(self, firm_id: int, params, initial_net_worth: float, 
                 entrant: bool = False, entry_time: int = 0):
        """
        Initialize a capital-good firm
        
        Args:
            firm_id: Unique identifier for the firm
            params: Parameters object with model configuration
            initial_net_worth: Initial net worth
            entrant: Whether this is an entrant firm
            entry_time: Time step when firm entered (0 for initial firms)
        """
        self.firm_id = firm_id
        self.params = params
        self.entrant = entrant
        self.entry_time = entry_time
        self.post_change = False  # Whether firm is post-regime-change type
        
        # Financial variables
        self.net_worth = initial_net_worth
        self.debt = 0.0
        self.deposits = 0.0
        self.profit = 0.0
        self.revenue = 0.0
        self.sales = 0.0
        
        # Production variables
        self.labor_productivity_output = params.get('m1', 1.0)  # B_tau (production productivity)
        self.machine_productivity = 1.0  # A_tau (final machine productivity)
        self.output = 0.0
        self.price = 1.0
        self.unit_cost = 0.0
        
        # Market variables
        self.market_share = 1.0 / params.get('F10', 20)  # Initial equal shares
        self.clients = []  # List of Firm2 clients
        self.orders = 0.0
        self.sales_history = []  # Track past sales for R&D calculation
        
        # Labor variables
        self.labor_demand = 0.0
        self.labor_actual = 0.0
        self.workers = []  # List of Worker objects
        self.wage_bill = 0.0
        self.avg_wage = params.get('w0min', 1.0)
        self.rd_labor_demand = 0.0  # R&D labor DEMAND (before allocation)
        self.rd_workers = 0  # R&D workers ALLOCATED (after sector allocation)
        self.production_workers = 0  # Production workers ALLOCATED (after sector allocation)
        
        # R&D variables
        self.rd_expenditure = 0.0
        self.innovation_success = False
        self.imitation_success = False
        
        # Bank relationship
        self.bank = None
        self.bank_client_obj = None
        
        # Competitiveness (for market dynamics)
        self.competitiveness = 1.0
    
    def do_rd(self, t: int) -> Tuple[float, float]:
        """
        Perform R&D: innovation and imitation
        
        Returns:
            Tuple of (new_machine_productivity, new_production_productivity)
        """
        # Get R&D parameters
        nu = self.params.get('nu', 0.04)  # Share of revenue for R&D
        xi = self.params.get('xi', 0.5)  # Share of R&D for innovation
        zeta1 = self.params.get('zeta1', 0.3)  # Innovation success elasticity
        zeta2 = self.params.get('zeta2', 0.3)  # Imitation success elasticity
        
        # R&D expenditure as share of past revenue
        self.rd_expenditure = nu * self.revenue
        
        # Normalize R&D workers by labor force (for comparability)
        Ls0 = self.params.get('Ls0', 1000)
        Ls_current = self.labor_actual  # Will be updated by labor market
        if Ls_current > 0:
            L1rdN = self.rd_workers * Ls0 / max(Ls_current, 1)
        else:
            L1rdN = 0
        
        # Current technology
        A_tau = self.machine_productivity
        B_tau = self.labor_productivity_output
        
        # Try innovation
        prob_innovation = 1 - np.exp(-zeta1 * xi * L1rdN)
        self.innovation_success = np.random.random() < prob_innovation
        
        A_inn = A_tau
        B_inn = B_tau
        
        if self.innovation_success:
            # Draw innovation from beta distribution
            x1inf = self.params.get('x1inf', -0.15)
            x1sup = self.params.get('x1sup', 0.15)
            alpha1 = self.params.get('alpha1', 3.0)
            beta1 = self.params.get('beta1', 3.0)
            
            draw = beta_dist.rvs(alpha1, beta1)
            improvement = x1inf + draw * (x1sup - x1inf)
            
            A_inn = A_tau * (1 + improvement)
            B_inn = B_tau * (1 + improvement)
        
        # Try imitation
        prob_imitation = 1 - np.exp(-zeta2 * (1 - xi) * L1rdN)
        self.imitation_success = np.random.random() < prob_imitation
        
        A_imi = A_tau
        B_imi = B_tau
        
        if self.imitation_success and len(self.params.get('all_firms1', [])) > 1:
            # Find firms to imitate based on technology distance
            # This requires access to other firms - simplified here
            # In full implementation, this would calculate Euclidean distance
            # For now, use a simplified version
            A_imi = A_tau * 1.05  # Placeholder
            B_imi = B_tau * 1.05
        
        # Select best technology
        # Compare based on machine quality and price
        w1avg = self.avg_wage
        w2avg = self.params.get('w2avg', 1.0)
        m1 = self.params.get('m1', 1.0)
        mu1 = self.params.get('mu1', 0.04)
        
        # Calculate costs and prices for each option
        p_current = (1 + mu1) * w1avg / B_tau / m1
        c_current = w2avg / A_tau
        
        p_inn = (1 + mu1) * w1avg / B_inn / m1 if B_inn > 0 else np.inf
        c_inn = w2avg / A_inn if A_inn > 0 else np.inf
        
        p_imi = (1 + mu1) * w1avg / B_imi / m1 if B_imi > 0 else np.inf
        c_imi = w2avg / A_imi if A_imi > 0 else np.inf
        
        # Choose technology with best combination (lower price and cost)
        options = [
            (A_tau, B_tau, p_current, c_current),
            (A_inn, B_inn, p_inn, c_inn),
            (A_imi, B_imi, p_imi, c_imi)
        ]
        
        # Simple selection: prefer lower operating cost for customers
        best_option = min(options, key=lambda x: x[3])
        
        new_A = best_option[0]
        new_B = best_option[1]
        
        return new_A, new_B
    
    def plan_production(self, t: int):
        """
        Plan production based on received orders
        """
        # Production equals orders (machines are produced on demand)
        self.output = self.orders
    
    def determine_labor_demand(self, t: int):
        """
        Determine labor demand for production and R&D
        
        Following C++ model (fun_KS_firm1.h):
        - _L1d = _L1dRD + ceil(_Q1 / (_Btau * m1))
        - _L1dRD = ceil(_RD / w1avg[t-1])
        - _RD = nu * _S1[t-1] (R&D based on PAST sales, not current)
        """
        m1 = self.params.get('m1', 1.0)
        nu = self.params.get('nu', 0.04)  # R&D share of sales
        
        # Production workers needed (based on current orders)
        if self.labor_productivity_output > 0:
            L_prod = self.output / (self.labor_productivity_output * m1)
        else:
            L_prod = 0
        
        # R&D workers based on PAST sales (C++ uses VL("_S1", 1))
        # This ensures Firm1 maintains R&D workforce even when orders are zero
        if hasattr(self, 'sales_history') and len(self.sales_history) > 0:
            past_sales = self.sales_history[-1]
        else:
            # Use past revenue as proxy (initially set to positive value)
            past_sales = self.revenue
        
        if past_sales > 0:
            # R&D expenditure = nu * past_sales
            rd_expenditure = nu * past_sales
            # R&D workers = RD / avg_wage
            L_rd = rd_expenditure / self.avg_wage if self.avg_wage > 0 else 0
        else:
            L_rd = 0
        
        # Total labor demand
        self.labor_demand = L_prod + L_rd
        
        # Store R&D labor DEMAND (not allocation - that's done by sector later)
        self.rd_labor_demand = L_rd
    
    def produce(self, t: int):
        """
        Produce machines with actual labor hired
        
        Following C++ model (_Q1e equation, fun_KS_firm1.h lines 411-440):
        - Use R&D and production workers allocated by sector-level L1rd equation
        - Adjust output based on available production workers
        - Ensure output is never negative
        
        NOTE: rd_workers and production_workers are now set by the sector-level
        labor allocation in labor_market.allocate_sector1_rd_labor()
        """
        m1 = self.params.get('m1', 1.0)
        
        # Use the sector-allocated production workers
        # These are set by allocate_sector1_rd_labor() after hiring
        if not hasattr(self, 'production_workers'):
            # Fallback if sector allocation hasn't run yet (shouldn't happen)
            L1rdMax = self.params.get('L1rdMax', 0.2)
            max_rd = min(self.labor_actual, self.labor_actual * L1rdMax, 
                        getattr(self, 'rd_workers', 0))
            self.rd_workers = max(0, max_rd)
            self.production_workers = max(0, self.labor_actual - self.rd_workers)
        
        # Calculate what can be produced with allocated production workers
        max_output = self.production_workers * self.labor_productivity_output * m1
        
        # Actual output is minimum of planned and producible
        # C++ uses max(output, 0) at line 440 to ensure non-negative
        self.output = max(0, min(self.output, max_output))
        
        # Update machine productivity from R&D (using allocated rd_workers)
        if t > 1:  # After initialization
            new_A, new_B = self.do_rd(t)
            self.machine_productivity = new_A
            self.labor_productivity_output = new_B
    
    def set_price(self, t: int):
        """
        Set machine price using cost-plus markup
        """
        mu1 = self.params.get('mu1', 0.04)  # Markup
        m1 = self.params.get('m1', 1.0)
        
        # Calculate unit cost
        if self.output > 0:
            self.unit_cost = self.wage_bill / self.output
        else:
            self.unit_cost = self.avg_wage / m1
        
        # Set price with markup
        self.price = (1 + mu1) * self.unit_cost
    
    def calculate_profit(self, t: int):
        """
        Calculate profit for the period
        """
        # Revenue from sales
        self.revenue = self.sales * self.price
        
        # Track sales history for R&D calculation (C++ uses VL("_S1", 1))
        self.sales_history.append(self.sales)
        if len(self.sales_history) > 4:  # Keep only recent history
            self.sales_history.pop(0)
        
        # Costs
        total_costs = self.wage_bill + self.rd_expenditure
        
        # Interest on debt
        if self.bank:
            r_debt = self.bank.interest_rate_debt
            interest = r_debt * self.debt
        else:
            interest = 0.0
        
        # Profit
        self.profit = self.revenue - total_costs - interest
    
    def pay_taxes(self, t: int, government):
        """
        Pay taxes to government
        """
        tr = self.params.get('tr', 0.1)  # Tax rate
        
        if self.profit > 0:
            tax = tr * self.profit
            self.profit -= tax
            government.collect_tax(tax, 'firm1')
    
    def update_net_worth(self, t: int):
        """
        Update net worth based on profit and financial flows
        """
        # Pay dividends
        d1 = self.params.get('d1', 0.5)  # Dividend rate
        dividends = max(0, d1 * self.profit)
        
        # Retained earnings
        retained = self.profit - dividends
        
        # Update net worth
        self.net_worth += retained
        
        # Update debt (simplified - new loans minus repayments)
        # Full implementation would interact with financial market
    
    def exit(self, labor_market, financial_market):
        """
        Handle firm exit: fire workers, default on loans
        """
        # Fire all workers
        for worker in self.workers:
            worker.employed = False
            worker.employer = None
        
        # Default on bank loans
        if self.bank and self.debt > 0:
            self.bank.handle_default(self, self.debt)
        
        # Remove from client lists
        # This would be handled by the capital market in full implementation
    
    def __repr__(self):
        return (f"Firm1(id={self.firm_id}, A={self.machine_productivity:.3f}, "
                f"NW={self.net_worth:.1f}, L={len(self.workers)})")
