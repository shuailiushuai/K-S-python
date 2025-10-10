"""
Consumption-Good Firm (Firm2) Agent

Firms in the consumption-good sector:
- Form adaptive demand expectations
- Produce consumption goods using machines and labor
- Manage vintage capital stock
- Set variable markups based on competitiveness
- Compete via price, quality, and delivery
"""

import numpy as np
from typing import Dict, List, Optional
from agents.vintage import Vintage


class Firm2:
    """
    Consumption-good firm agent (Firm2)
    
    These firms produce consumption goods using machines bought from
    capital-good firms and labor from the labor market.
    """
    
    def __init__(self, firm_id: int, params, initial_net_worth: float,
                 entrant: bool = False, entry_time: int = 0):
        """
        Initialize a consumption-good firm
        
        Args:
            firm_id: Unique identifier
            params: Parameters object
            initial_net_worth: Initial net worth
            entrant: Whether this is an entrant
            entry_time: Entry time step
        """
        self.firm_id = firm_id
        self.params = params
        self.entrant = entrant
        self.entry_time = entry_time
        self.post_change = False
        self.life_cycle = 0  # Firm age
        
        # Financial variables
        self.net_worth = initial_net_worth
        self.debt = 0.0
        self.deposits = 0.0
        self.profit = 0.0
        self.revenue = 0.0
        self.sales = 0.0
        self.free_cash_flow = 0.0
        
        # Production variables
        self.output = 0.0
        self.output_planned = 0.0
        self.output_desired = 0.0
        self.price = 1.0
        self.markup = params.get('mu20', 0.35)  # Initial markup
        self.unit_cost = 0.0
        self.inventories = 0.0
        
        # Capital stock (vintages)
        self.vintages: List[Vintage] = []
        self.capital_stock = 0.0  # Number of machines
        self.capital_desired = 0.0
        self.investment_desired = 0.0
        self.expansion_investment = 0.0
        self.replacement_investment = 0.0
        
        # Market variables
        self.market_share = 1.0 / params.get('F20', 100)
        self.demand_expected = 0.0
        self.demand_fulfilled = 0.0
        self.demand_unfilled = 0.0
        self.competitiveness = 1.0
        
        # Quality
        self.quality = 1.0
        
        # Labor variables
        self.labor_demand = 0.0
        self.labor_actual = 0.0
        self.workers = []
        self.wage_bill = 0.0
        self.avg_wage = params.get('w0min', 1.0)
        self.avg_skills = 1.0
        
        # Suppliers (Firm1)
        self.suppliers = []  # List of Firm1 suppliers
        self.main_supplier = None
        self.pending_orders = []  # List of pending machine orders
        
        # Bank relationship
        self.bank = None
        self.bank_client_obj = None
        
        # Historical data for expectations
        self.demand_history = []
        self.fulfilled_history = []
    
    def form_expectations(self, t: int):
        """
        Form adaptive demand expectations
        """
        # For entrants in first periods or t=1, use recent history or initial values
        if self.life_cycle < 3:
            if len(self.demand_history) > 0:
                self.demand_expected = max(self.demand_history[-1], self.demand_fulfilled)
            else:
                # Use initial demand if available, otherwise use a small default
                if hasattr(self, 'demand_expected') and self.demand_expected > 0:
                    # Keep existing initial demand
                    pass
                else:
                    self.demand_expected = self.params.get('initial_demand', 10)
            return
        
        # At t=1, if we have initial state but no history, keep initial expectations
        if t == 1 and len(self.demand_history) == 0:
            if hasattr(self, 'demand_expected') and self.demand_expected > 0:
                # Keep initialization values for first step
                return
            else:
                self.demand_expected = self.output_desired if self.output_desired > 0 else 10
                return
        
        # Get expectation mode
        flag_expect = self.params.get('flagExpect', 0)
        e0 = self.params.get('e0', 0.5)  # Animal spirits
        
        # Compute mix of fulfilled and potential demand
        if len(self.demand_history) == 0:
            # Fallback for no history
            if hasattr(self, 'demand_expected') and self.demand_expected > 0:
                return  # Keep existing
            else:
                self.demand_expected = self.params.get('initial_demand', 10)
                return
        
        # Get recent demand (fulfilled and orders)
        recent_demands = []
        for i in range(min(4, len(self.demand_history))):
            d_fulfilled = self.fulfilled_history[-(i+1)] if len(self.fulfilled_history) > i else 0
            d_orders = self.demand_history[-(i+1)] if len(self.demand_history) > i else 0
            d_mix = (1 - e0) * d_fulfilled + e0 * d_orders
            d_mix = max(d_mix, d_fulfilled)  # At least fulfilled demand
            recent_demands.append(d_mix)
        
        if flag_expect == 0:
            # Myopic with 1-period memory
            self.demand_expected = recent_demands[0] if recent_demands else 0
        
        elif flag_expect == 1:
            # Myopic with up to 4-period memory
            e1 = self.params.get('e1', 0.4)
            e2 = self.params.get('e2', 0.3)
            e3 = self.params.get('e3', 0.2)
            e4 = self.params.get('e4', 0.1)
            weights = [e1, e2, e3, e4]
            
            total_weight = 0
            weighted_sum = 0
            for i, d in enumerate(recent_demands[:4]):
                if d > 0:
                    weighted_sum += weights[i] * d
                    total_weight += weights[i]
            
            self.demand_expected = weighted_sum / total_weight if total_weight > 0 else 0
        
        elif flag_expect == 2:
            # Accelerating expectations
            if len(recent_demands) >= 2:
                growth = (recent_demands[0] / recent_demands[1] - 1) if recent_demands[1] > 0 else 0
                e5 = self.params.get('e5', 0.5)
                self.demand_expected = recent_demands[0] * (1 + e5 * growth)
            else:
                self.demand_expected = recent_demands[0] if recent_demands else 0
        
        else:
            # Default to myopic
            self.demand_expected = recent_demands[0] if recent_demands else 0
    
    def plan_production(self, t: int):
        """
        Plan production based on expected demand
        """
        iota = self.params.get('iota', 0.1)  # Desired inventory ratio
        u = self.params.get('u', 0.75)  # Planned capacity utilization
        
        # Desired output = expected demand + desired inventories - current inventories
        desired_inventories = iota * self.demand_expected
        self.output_desired = self.demand_expected + desired_inventories - self.inventories
        self.output_desired = max(0, self.output_desired)
        
        # Planned output considers capacity
        available_capacity = self._calculate_capacity()
        self.output_planned = min(self.output_desired, available_capacity * u)
    
    def _calculate_capacity(self) -> float:
        """Calculate total production capacity from capital stock"""
        m2 = self.params.get('m2', 1.0)  # Machine productivity
        
        # Capacity from all vintages
        capacity = 0.0
        for vintage in self.vintages:
            capacity += vintage.machines * m2 * vintage.productivity
        
        return capacity
    
    def _calculate_productivity(self) -> float:
        """Calculate average productivity of capital stock"""
        if not self.vintages:
            return 1.0
        
        total_prod = sum(v.machines * v.productivity for v in self.vintages)
        total_machines = sum(v.machines for v in self.vintages)
        
        return total_prod / total_machines if total_machines > 0 else 1.0
    
    def determine_labor_demand(self, t: int):
        """
        Determine labor demand for planned production
        """
        theta = self.params.get('theta', 0.0)  # Extra capacity when hiring
        
        # Labor needed for planned production
        productivity = self._calculate_productivity()
        if productivity > 0:
            L_needed = self.output_planned / productivity
        else:
            L_needed = self.output_planned  # Fallback
        
        # Add slack for potential growth
        self.labor_demand = L_needed * (1 + theta)
    
    def determine_investment_demand(self, t: int):
        """
        Determine desired investment in new machines
        """
        # Check if expansion investment is needed
        kappaMin = self.params.get('kappaMin', 0.0)
        kappaMax = self.params.get('kappaMax', 0.2)
        
        current_capacity = self._calculate_capacity()
        required_capacity = self.output_desired
        
        # Expansion investment
        if required_capacity > current_capacity * (1 + kappaMin):
            expansion_gap = required_capacity - current_capacity
            m2 = self.params.get('m2', 1.0)
            # Machines needed (will have productivity from best supplier)
            self.expansion_investment = expansion_gap / m2
        else:
            self.expansion_investment = 0.0
        
        # Replacement investment (replace old machines)
        eta = self.params.get('eta', 20)  # Technical lifetime
        b = self.params.get('b', 20)  # Payback period
        self.replacement_investment = self._determine_replacement(t, eta, b)
        
        self.investment_desired = self.expansion_investment + self.replacement_investment
    
    def _determine_replacement(self, t: int, eta: float, b: float) -> float:
        """
        Determine which machines to replace based on technical lifetime and payback rule
        
        Args:
            t: Current time
            eta: Technical lifetime of machines
            b: Payback period for replacement
        """
        machines_to_replace = 0.0
        
        # Check each vintage
        for vintage in self.vintages:
            age = t - vintage.birth_time
            
            # First: check if machine exceeded technical lifetime
            if age >= eta:
                machines_to_replace += vintage.machines
                continue
            
            # Second: check economic payback
            # If a new machine from supplier is more productive and pays back in < b periods
            # then replace this vintage (simplified check)
            # For now, we just use the age-based rule
            # TODO: Implement full payback calculation comparing with supplier technology
        
        return machines_to_replace
    
    def produce(self, t: int):
        """
        Produce with actual labor hired
        """
        # Adjust output to actual labor
        if self.labor_demand > 0:
            labor_ratio = self.labor_actual / self.labor_demand
        else:
            labor_ratio = 1.0
        
        self.output = self.output_planned * min(1.0, labor_ratio)
        
        # Update inventories
        self.inventories += self.output
    
    def set_price(self, t: int):
        """
        Set price using variable markup rule
        """
        upsilon = self.params.get('upsilon', 0.02)  # Markup sensitivity
        
        # Calculate unit cost
        productivity = self._calculate_productivity()
        if self.output > 0 and productivity > 0:
            self.unit_cost = self.wage_bill / (self.output * productivity)
        else:
            self.unit_cost = self.avg_wage / max(productivity, 0.1)
        
        # Adjust markup based on market share dynamics
        # If market share growing, increase markup; if shrinking, decrease
        if t > 1 and hasattr(self, 'prev_market_share'):
            if self.market_share > self.prev_market_share:
                self.markup = min(1.0, self.markup * (1 + upsilon))
            elif self.market_share < self.prev_market_share:
                self.markup = max(0.01, self.markup * (1 - upsilon))
        
        self.prev_market_share = self.market_share
        
        # Set price
        self.price = (1 + self.markup) * self.unit_cost
    
    def calculate_profit(self, t: int):
        """
        Calculate profit for the period
        """
        # Revenue from sales
        self.revenue = self.sales * self.price
        
        # Costs: wages + interest on debt
        if self.bank:
            r_debt = self.bank.interest_rate_debt
            interest = r_debt * self.debt
        else:
            interest = 0.0
        
        total_costs = self.wage_bill + interest
        
        # Profit
        self.profit = self.revenue - total_costs
        
        # Free cash flow for bonuses
        self.free_cash_flow = max(0, self.profit)
    
    def pay_bonuses(self, t: int):
        """
        Pay bonuses to workers if firm is profitable
        """
        psi6 = self.params.get('psi6', 0.0)  # Bonus share
        
        # Check if firm is above average profitability
        # Simplified: pay bonuses if profit > 0
        if self.profit > 0 and len(self.workers) > 0:
            bonus_pool = psi6 * self.free_cash_flow
            bonus_per_worker = bonus_pool / len(self.workers)
            
            for worker in self.workers:
                worker.bonus = bonus_per_worker
    
    def pay_taxes(self, t: int, government):
        """
        Pay taxes to government
        """
        tr = self.params.get('tr', 0.1)
        
        if self.profit > 0:
            tax = tr * self.profit
            self.profit -= tax
            government.collect_tax(tax, 'firm2')
    
    def update_net_worth(self, t: int):
        """
        Update net worth
        """
        d2 = self.params.get('d2', 0.5)  # Dividend rate
        
        # Pay bonuses first
        self.pay_bonuses(t)
        
        # Pay dividends
        dividends = max(0, d2 * self.profit)
        
        # Retained earnings
        retained = self.profit - dividends
        
        # Update net worth
        self.net_worth += retained
        
        # Increment life cycle
        self.life_cycle += 1
    
    def calculate_competitiveness(self, t: int, avg_price: float, avg_quality: float):
        """
        Calculate firm competitiveness for market share dynamics
        """
        omega1 = self.params.get('omega1', 1.0)  # Price weight
        omega2 = self.params.get('omega2', 1.0)  # Unfilled demand weight
        omega3 = self.params.get('omega3', 0.0)  # Quality weight
        
        # Normalize competitiveness factors
        price_comp = avg_price / self.price if self.price > 0 else 0
        
        unfilled_ratio = self.demand_unfilled / self.demand_fulfilled if self.demand_fulfilled > 0 else 0
        unfilled_comp = 1 - unfilled_ratio
        
        quality_comp = self.quality / avg_quality if avg_quality > 0 else 1
        
        # Combined competitiveness
        self.competitiveness = (omega1 * price_comp + 
                               omega2 * unfilled_comp + 
                               omega3 * quality_comp)
    
    def exit(self, labor_market, financial_market):
        """
        Handle firm exit
        """
        # Fire all workers
        for worker in self.workers:
            worker.employed = False
            worker.employer = None
        
        # Default on loans
        if self.bank and self.debt > 0:
            self.bank.handle_default(self, self.debt)
    
    def __repr__(self):
        return (f"Firm2(id={self.firm_id}, p={self.price:.2f}, "
                f"ms={self.market_share:.4f}, NW={self.net_worth:.1f})")
