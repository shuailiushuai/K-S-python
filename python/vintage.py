"""
Vintage Capital Management
Manages capital vintages for Firm2 agents.
Based on fun_KS_vintage.h
"""

from typing import Dict, Any, Optional
from .agents import BaseAgent
from .config import *


class Vint(BaseAgent):
    """
    Capital vintage object.
    Represents a set of machines of the same vintage in a Firm2.
    """
    
    def __init__(self, agent_id: int, parent: BaseAgent):
        super().__init__(agent_id, "Vint", parent)
        
        # Vintage identification
        self.__IDvint = agent_id  # Vintage ID
        self.__tVint = 0          # Period of vintage creation
        
        # Machine characteristics
        self.__nVint = 0          # Number of machines in vintage
        self.__Avint = 0.0        # Labor productivity per machine
        self.__Bvint = 0.0        # Labor productivity when machine was built
        self.__pVint = 0.0        # Price paid for machines
        
        # Production
        self.__Qvint = 0.0        # Production from this vintage
        self.__AeVint = 0.0       # Effective productivity
        self.__toUseVint = 0.0    # Machines to use
        
        # Scrapping
        self.__RSvint = 0         # Machines to scrap
        
        # Labor allocation
        self.__dLdVint = 0        # Additional labor needed
    
    def compute_scrap_demand(self, params: Dict[str, Any], t: int, 
                            supplier_Atau: float, supplier_p1: float,
                            firm_w2avg: float, firm_postChg: bool) -> int:
        """
        Compute machines to scrap (__RSvint).
        Based on fun_KS_vintage.h __RSvint equation.
        
        Args:
            params: Model parameters
            t: Current time period
            supplier_Atau: Supplier's productivity
            supplier_p1: Supplier's price
            firm_w2avg: Firm's average wage
            firm_postChg: Post-change flag
            
        Returns:
            Number of machines to scrap (negative = must scrap)
        """
        eta = params.get('eta', 20)  # Technical lifetime
        
        # Check if vintage is out of technical life
        if self.__tVint < t - eta:
            return -self.__nVint  # Must scrap all
        
        # Unit cost advantage of new machines
        cost_old = firm_w2avg / self.__Avint
        cost_new = firm_w2avg / supplier_Atau
        cost_advantage = cost_old - cost_new
        
        if cost_advantage <= 0:
            return 0  # New machines not better
        
        # Payback period
        b = params.get('b', 3.0)
        bChg = params.get('bChg', 3.0)
        payback_threshold = bChg if firm_postChg else b
        
        m2 = params.get('m2', 1.0)
        
        # Payback period for replacement
        if cost_advantage > 0:
            payback = (supplier_p1 / m2) / cost_advantage
        else:
            payback = float('inf')
        
        # Scrap if payback period is acceptable
        if payback <= payback_threshold:
            return self.__nVint  # Scrap all in this vintage
        else:
            return 0  # Keep vintage
    
    def compute_labor_demand(self, params: Dict[str, Any], 
                           current_workers_skill: float,
                           last_worker_skill: float,
                           vintage_public_skill: float) -> int:
        """
        Compute additional labor needed (__dLdVint).
        Based on fun_KS_vintage.h __dLdVint equation.
        
        Args:
            params: Model parameters
            current_workers_skill: Sum of skills of current workers
            last_worker_skill: Skill of last hired worker
            vintage_public_skill: Public skill level for vintage
            
        Returns:
            Number of additional workers needed
        """
        Lscale = params.get('Lscale', 1.0)
        m2 = params.get('m2', 1.0)
        flag_worker_lbu = int(params.get('flagWorkerLBU', 0))
        
        # Vintage notional production per worker
        vintage_prod = self.__Avint * Lscale
        
        # Required capacity
        required_capacity = self.__toUseVint * m2
        
        if required_capacity == 0 and current_workers_skill == 0:
            return 0  # Nothing to do
        
        # Current workers capacity
        current_capacity = current_workers_skill * vintage_prod
        
        # Last worker capacity
        last_capacity = last_worker_skill * vintage_prod
        
        # Check if we should remove last worker (excess capacity)
        if current_capacity - last_capacity > required_capacity:
            # Would need to remove worker (return 0, removal handled elsewhere)
            return 0
        
        # Check if we need more workers
        if current_capacity < required_capacity:
            # Skill factor for new workers
            if flag_worker_lbu == 1 or flag_worker_lbu == 3:
                # Learning by vintage mode
                skill_factor = vintage_public_skill
            else:
                skill_factor = 1.0
            
            new_worker_capacity = skill_factor * vintage_prod
            
            if new_worker_capacity > 0:
                additional_workers = int(
                    ((required_capacity - current_capacity) / new_worker_capacity) + 0.5
                )
                return max(additional_workers, 0)
        
        return 0
    
    def compute_production(self, params: Dict[str, Any],
                         workers_total_skill: float,
                         n_workers: int) -> float:
        """
        Compute vintage production (__Qvint).
        Also updates __AeVint (effective productivity).
        Based on fun_KS_vintage.h __Qvint equation.
        
        Args:
            params: Model parameters
            workers_total_skill: Sum of all workers' skills
            n_workers: Number of workers
            
        Returns:
            Production from this vintage
        """
        Lscale = params.get('Lscale', 1.0)
        
        # Effective productivity (average skill times base productivity)
        if n_workers > 0:
            avg_skill = workers_total_skill / n_workers
            effective_prod = avg_skill * self.__Avint
        else:
            effective_prod = self.__Avint
        
        self.WRITE("__AeVint", effective_prod)
        
        # Production (workers * skills * productivity * scale)
        production = workers_total_skill * self.__Avint * Lscale
        
        # Cap by machine physical capacity
        m2 = params.get('m2', 1.0)
        max_production = self.__nVint * m2
        
        return min(production, max_production)


def create_vintage(parent: BaseAgent, t: int, n_machines: int,
                  productivity_A: float, productivity_B: float,
                  price: float, vintage_id: int) -> Vint:
    """
    Create a new vintage for a Firm2.
    
    Args:
        parent: Parent Firm2 agent
        t: Current time period
        n_machines: Number of machines
        productivity_A: Current productivity (Atau from supplier)
        productivity_B: Original productivity (Btau from supplier)
        price: Price per machine
        vintage_id: Unique vintage ID
        
    Returns:
        New Vint object
    """
    vintage = Vint(vintage_id, parent)
    vintage.__tVint = t
    vintage.__nVint = n_machines
    vintage.__Avint = productivity_A
    vintage.__Bvint = productivity_B
    vintage.__pVint = price
    vintage.__toUseVint = n_machines
    
    vintage.WRITE("__tVint", t)
    vintage.WRITE("__nVint", n_machines)
    vintage.WRITE("__Avint", productivity_A)
    vintage.WRITE("__Bvint", productivity_B)
    vintage.WRITE("__pVint", price)
    
    return vintage


def scrap_vintage(vintage: Vint, n_to_scrap: int):
    """
    Scrap machines from a vintage.
    
    Args:
        vintage: Vintage object
        n_to_scrap: Number of machines to scrap
    """
    current_n = vintage.__nVint
    new_n = max(0, current_n - n_to_scrap)
    vintage.__nVint = new_n
    vintage.WRITE("__nVint", new_n)
    
    if new_n == 0:
        # Vintage is empty, should be deleted
        return True
    return False
