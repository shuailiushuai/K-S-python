"""
Goods Market Module
Implements consumption goods allocation and market clearing
"""

from typing import List, Dict, Any


class GoodsMarket:
    """
    Consumption goods market for the K+S model
    Manages demand allocation based on market shares and available supply
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    def allocate_consumption_demand(self, firms2: List, total_demand: float) -> float:
        """
        Allocate consumption demand to firms based on market shares
        Implements iterative allocation with rationing
        
        From fun_KS_consumption.h: D2 equation
        
        Args:
            firms2: List of consumption-good firms
            total_demand: Total nominal consumption demand (Cd)
        
        Returns:
            Total demand fulfilled (in units, not monetary)
        """
        K = len(firms2)
        
        if K == 0 or total_demand <= 0:
            return 0.0
        
        # Create temporary vectors for shares, supply, and prices
        market_shares = []
        supply = []
        prices = []
        
        for firm in firms2:
            # Available supply = expected production + inventory
            avail_supply = firm._Q2e if hasattr(firm, '_Q2e') else 0
            if hasattr(firm, '_N') and len(firm.history['_N']) > 0:
                avail_supply += firm.history['_N'][-1]  # Previous period inventory
            
            supply.append(avail_supply)
            market_shares.append(firm._f2 if hasattr(firm, '_f2') else 0)
            prices.append(firm._p2 if hasattr(firm, '_p2') else 1.0)
            
            # Initialize demand fulfilled accumulator
            firm._D2 = 0
            firm._l2 = 0  # Unsatisfied demand
        
        # Allocate demand iteratively until exhausted or no more supply
        total_fulfilled = 0.0
        remaining_demand = total_demand
        iteration = 0
        
        while remaining_demand > 0.01:
            iter_demand = remaining_demand
            active_shares = 0.0
            
            # Try to allocate to each firm based on market share
            for j, firm in enumerate(firms2):
                if market_shares[j] > 0:
                    if supply[j] > 0:
                        # Firm's monetary demand allocation
                        firm_demand_monetary = remaining_demand * market_shares[j]
                        # Convert to units
                        firm_demand_units = firm_demand_monetary / prices[j]
                        
                        if firm_demand_units <= supply[j]:
                            # Can supply all demanded
                            firm._D2 += firm_demand_units
                            total_fulfilled += firm_demand_units
                            iter_demand -= firm_demand_monetary
                            active_shares += market_shares[j]
                            supply[j] -= firm_demand_units
                        else:
                            # Can only supply what's available
                            if iteration == 0:
                                # First iteration: track unsatisfied demand
                                firm._l2 = firm_demand_units - supply[j]
                            
                            firm._D2 += supply[j]
                            total_fulfilled += supply[j]
                            iter_demand -= supply[j] * prices[j]
                            # Firm exhausted
                            market_shares[j] = 0
                            supply[j] = 0
                    else:
                        # No more supply
                        market_shares[j] = 0
            
            # Rescale remaining market shares
            if active_shares > 0:
                for j in range(K):
                    market_shares[j] /= active_shares
            else:
                # No more firms can supply
                break
            
            remaining_demand = iter_demand
            iteration += 1
            
            # Safety check to avoid infinite loops
            if iteration > 100:
                break
        
        return total_fulfilled
    
    def compute_consumption_demand(self, workers: List, government_exp: float,
                                   past_bonus: float, past_dividends: float,
                                   tax_wages: float, tax_dividends: float,
                                   savings_acc: float) -> float:
        """
        Compute total consumption demand from workers
        
        From fun_KS_country.h: Cd equation
        
        Args:
            workers: List of workers
            government_exp: Government transfers (G)
            past_bonus: Bonuses from previous period
            past_dividends: Dividends from previous period
            tax_wages: Wage taxes this period
            tax_dividends: Dividend taxes this period
            savings_acc: Accumulated forced savings
        
        Returns:
            Total nominal consumption demand
        """
        # Workers' net income after taxes
        # Current wages + government benefits + past bonuses/dividends - taxes
        total_wages = sum(w._w for w in workers if w._employed > 0)
        
        consumption = (total_wages + government_exp + past_bonus + past_dividends 
                      - tax_wages - tax_dividends)
        
        # Handle accumulated forced savings
        flag_cons = self.config.get('Country.flagCons', 1)
        
        if flag_cons == 0:
            # Ignore past savings
            pass
        elif flag_cons == 1:
            # Spend all savings
            consumption += savings_acc
            savings_acc = 0
        else:  # flag_cons == 2
            # Slow spend of savings
            Crec = self.config.get('Country.Crec', 0.2)
            max_recovery = consumption * Crec
            
            if savings_acc <= max_recovery:
                consumption += savings_acc
                savings_acc = 0
            else:
                consumption += max_recovery
                savings_acc -= max_recovery
        
        return consumption, savings_acc
    
    def update_inventories(self, firms2: List):
        """
        Update firm inventories after sales
        N(t) = N(t-1) + Q2 - D2
        """
        for firm in firms2:
            prev_inventory = firm._N if hasattr(firm, '_N') else 0
            production = firm._Q2 if hasattr(firm, '_Q2') else 0
            sales = firm._D2 if hasattr(firm, '_D2') else 0
            
            firm._N = max(prev_inventory + production - sales, 0)
    
    def compute_sales_revenue(self, firms2: List):
        """
        Compute sales revenue for each firm
        S2 = D2 * p2
        """
        for firm in firms2:
            demand = firm._D2 if hasattr(firm, '_D2') else 0
            price = firm._p2 if hasattr(firm, '_p2') else 1.0
            firm._S2 = demand * price
