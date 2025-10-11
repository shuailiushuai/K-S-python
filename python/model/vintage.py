"""
Vintage Agent Implementation
Represents a machine vintage (technological generation) in a Firm2
"""

from typing import Optional, List
from .agent import Agent
from .constants import *
from .support import safe_divide
import math


class VintageAgent(Agent):
    """
    Vintage agent class
    
    Represents a specific technological generation of machines in a Firm2.
    Machines in a vintage share the same productivity characteristics.
    Workers are assigned to vintages and learn vintage-specific skills.
    """
    
    def __init__(self, vintage_id: int, parent: Agent):
        """
        Initialize Vintage agent
        
        Args:
            vintage_id: Unique vintage ID
            parent: Parent Firm2 object
        """
        super().__init__("Vint", parent)
        
        # Vintage identification
        self._IDvint = vintage_id        # Vintage ID
        self._tVint = 0                  # Vintage creation time
        
        # Technology characteristics
        self._Avint = INIPROD            # Labor productivity (A)
        self._nVint = 0                  # Number of machines
        
        # Production and utilization
        self._Qvint = 0.0                # Production from this vintage
        self._toUseVint = 0.0            # Machines to use
        self._RSvint = 0                 # Machines to scrap
        self._dLdVint = 0                # Additional labor required
        
        # Worker tracking
        self._LdVint = 0                 # Labor in vintage
        
    def compute_scrapping(self, params: dict) -> int:
        """
        Compute number of machines to scrap in this vintage
        
        Machines are scrapped if:
        1. Out of technical life (age > eta), or
        2. New machines are more economical (payback period)
        
        Args:
            params: Dictionary with:
                - eta: Technical machine lifetime
                - b or bChg: Payback period
                - m2: Machine modularity
                - w2avg: Average wage in sector 2
                - supplier: Supplier firm object
                - postChg: Post regime change flag
                - current_time: Current simulation time
        
        Returns:
            Number of machines to scrap (positive=economical, negative=must scrap)
        """
        current_time = params['current_time']
        eta = params['eta']
        
        # Out of technical life?
        if self._tVint < current_time - eta:
            # Scrap all if not in use
            self.write("__RSvint", -self._nVint)
            return -self._nVint
        
        # Get supplier information
        supplier = params.get('supplier')
        if supplier is None:
            self.write("__RSvint", 0)
            return 0
        
        # Unit cost advantage of new machines
        w2avg = params['w2avg']
        Atau_new = supplier.read("_Atau")
        cost_old = safe_divide(w2avg, self._Avint, 0)
        cost_new = safe_divide(w2avg, Atau_new, 0)
        cost_advantage = cost_old - cost_new
        
        # Payback period (regime dependent)
        b = params.get('bChg') if params.get('postChg', False) else params.get('b', 10)
        
        # If new machine not better or payback too long, don't scrap
        if cost_advantage <= 0:
            self.write("__RSvint", 0)
            return 0
        
        p1 = supplier.read("_p1")
        m2 = params['m2']
        payback = safe_divide(p1, m2 * cost_advantage, float('inf'))
        
        if payback > b:
            self.write("__RSvint", 0)
            return 0
        
        # Scrap if can be replaced
        self.write("__RSvint", self._nVint)
        return self._nVint
    
    def compute_labor_required(self, params: dict) -> int:
        """
        Compute additional labor required for vintage utilization
        
        Takes into account:
        - Machine capacity requirements
        - Current worker skills
        - Learning-by-using effects
        
        Args:
            params: Dictionary with:
                - m2: Machine modularity
                - Lscale: Labor scaling factor
                - flagWorkerLBU: Learning-by-using mode
                - vintProd: Vintage productivity map
                - current_workers: List of worker objects assigned to vintage
        
        Returns:
            Number of additional workers needed
        """
        m2 = params['m2']
        Lscale = params['Lscale']
        flagWorkerLBU = params.get('flagWorkerLBU', 0)
        
        # Vintage notional production
        notional_prod = self._Avint * Lscale
        
        # Required machine capacity
        required_capacity = self._toUseVint * m2
        
        # Calculate current worker capacity
        current_workers = params.get('current_workers', [])
        total_skills = 0.0
        last_worker_skill = 0.0
        
        for worker in current_workers:
            skill = worker.read("_s")
            total_skills += skill
            last_worker_skill = skill
        
        if required_capacity == 0 and len(current_workers) == 0:
            self.write("__dLdVint", 0)
            return 0
        
        last_worker_capacity = last_worker_skill * notional_prod
        all_workers_capacity = total_skills * notional_prod
        
        # Check if last worker is in excess
        if all_workers_capacity - last_worker_capacity > required_capacity:
            # Last worker should be removed (handled by caller)
            self.write("__dLdVint", 0)
            return 0
        
        # Check if need to hire more workers
        if all_workers_capacity < required_capacity:
            # Get skill factor for new workers
            if flagWorkerLBU != 0 and flagWorkerLBU != 2:
                # Learning by vintage mode - use public skills
                vintProd = params.get('vintProd', {})
                vintage_data = vintProd.get(self._IDvint)
                sVp = vintage_data.sVp if vintage_data else 1.0
            else:
                sVp = 1.0
            
            new_worker_capacity = sVp * notional_prod
            additional_workers = math.ceil(safe_divide(required_capacity - all_workers_capacity, 
                                                       new_worker_capacity, 0))
            
            self.write("__dLdVint", additional_workers)
            return additional_workers
        
        self.write("__dLdVint", 0)
        return 0
    
    def compute_production(self, m2: float, Lscale: float) -> float:
        """
        Compute production from this vintage
        
        Args:
            m2: Machine modularity
            Lscale: Labor scaling factor
        
        Returns:
            Production quantity
        """
        # Production based on machines used and their capacity
        Qvint = self._toUseVint * self._Avint * m2 * Lscale
        
        self.write("__Qvint", Qvint)
        self._Qvint = Qvint
        return Qvint
    
    def initialize(self, vintage_id: int, creation_time: int, 
                   productivity: float, num_machines: int):
        """
        Initialize vintage with parameters
        
        Args:
            vintage_id: Vintage identifier
            creation_time: Time vintage was created
            productivity: Labor productivity (A)
            num_machines: Number of machines
        """
        self._IDvint = vintage_id
        self._tVint = creation_time
        self._Avint = productivity
        self._nVint = num_machines
        
        self.write("_IDvint", vintage_id)
        self.write("_tVint", creation_time)
        self.write("_Avint", productivity)
        self.write("_nVint", num_machines)
