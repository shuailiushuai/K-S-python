"""
Goods Market

Implements consumption goods trading with:
- Demand from workers (consumption)
- Supply from Firm2 (production + inventories)
- Competitiveness-based market share dynamics (replicator dynamics)
- Rationing if supply < demand
"""

import numpy as np
from typing import List


class GoodsMarket:
    """
    Consumption goods market
    """
    
    def __init__(self, params, workers: List, firms2: List):
        """
        Initialize goods market
        
        Args:
            params: Parameters object
            workers: List of Worker objects
            firms2: List of Firm2 objects
        """
        self.params = params
        self.workers = workers
        self.firms2 = firms2
        
        # Market statistics
        self.total_demand = 0.0
        self.total_supply = 0.0
        self.total_sales = 0.0
    
    def match_demand_supply(self, t: int):
        """
        Match consumption demand with supply
        
        Implements replicator dynamics for market share evolution.
        """
        # Calculate total demand from workers
        self.total_demand = sum(w.consumption_desired for w in self.workers)
        
        # Calculate total supply (current output + past inventories)
        # Following C++ model: sup2[j] = _Q2e + _N[t-1]
        self.total_supply = sum(f.output + f.inventories for f in self.firms2)
        
        # Update firm competitiveness
        self._update_competitiveness(t)
        
        # Allocate demand to firms based on market shares
        if self.total_supply > 0:
            self._allocate_demand_to_firms(t)
        
        # Update market shares using replicator dynamics
        self._update_market_shares(t)
        
        # Distribute goods to workers
        self._distribute_to_workers()
    
    def _update_competitiveness(self, t: int):
        """
        Calculate competitiveness for each firm
        """
        if len(self.firms2) == 0:
            return
        
        # Calculate average price and quality
        avg_price = np.mean([f.price for f in self.firms2 if f.price > 0])
        avg_quality = np.mean([f.quality for f in self.firms2])
        
        # Update each firm's competitiveness
        for firm in self.firms2:
            firm.calculate_competitiveness(t, avg_price, avg_quality)
    
    def _allocate_demand_to_firms(self, t: int):
        """
        Allocate demand to firms based on market shares
        """
        # Reset firm demands
        for firm in self.firms2:
            firm.demand_fulfilled = 0.0
            firm.demand_unfilled = 0.0
        
        # Allocate demand proportional to market share
        for firm in self.firms2:
            firm_demand = firm.market_share * self.total_demand
            
            # Fulfill demand from current output + inventories (C++ logic)
            available = firm.output + firm.inventories
            fulfilled = min(firm_demand, available)
            
            firm.demand_fulfilled = fulfilled
            firm.demand_unfilled = firm_demand - fulfilled
            
            # Update inventories: add current output, subtract sales
            firm.inventories += firm.output - fulfilled
            firm.sales = fulfilled
            
            # Record in history
            firm.demand_history.append(firm_demand)
            firm.fulfilled_history.append(fulfilled)
            
            # Keep only recent history
            if len(firm.demand_history) > 8:
                firm.demand_history.pop(0)
                firm.fulfilled_history.pop(0)
        
        # Total sales
        self.total_sales = sum(f.sales for f in self.firms2)
    
    def _update_market_shares(self, t: int):
        """
        Update market shares using replicator dynamics
        """
        if len(self.firms2) == 0:
            return
        
        chi = self.params.get('chi', 1.0)  # Selectivity parameter
        
        # Calculate total competitiveness
        total_comp = sum(f.competitiveness for f in self.firms2)
        
        if total_comp == 0:
            # Equal shares if no differentiation
            for firm in self.firms2:
                firm.market_share = 1.0 / len(self.firms2)
            return
        
        # Replicator dynamics
        for firm in self.firms2:
            # Market share growth rate
            avg_comp = total_comp / len(self.firms2)
            
            if avg_comp > 0:
                growth = chi * (firm.competitiveness / avg_comp - 1)
            else:
                growth = 0
            
            # Update market share
            new_share = firm.market_share * (1 + growth)
            firm.market_share = max(0.0, new_share)
        
        # Normalize to sum to 1
        total_share = sum(f.market_share for f in self.firms2)
        if total_share > 0:
            for firm in self.firms2:
                firm.market_share /= total_share
    
    def _distribute_to_workers(self):
        """
        Distribute consumed goods to workers
        """
        # Simple proportional rationing if supply < demand
        if self.total_demand > 0:
            fulfillment_ratio = min(1.0, self.total_sales / self.total_demand)
        else:
            fulfillment_ratio = 1.0
        
        for worker in self.workers:
            consumption_actual = worker.consumption_desired * fulfillment_ratio
            worker.consume(consumption_actual)
