"""
Firm2 (Consumption Goods Sector) Agent Implementation  
Translated from fun_KS_firm2.h
"""

from typing import Dict, Any, List, Optional
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.base import BaseAgent
from utils.random_gen import get_random_generator
from utils.support import VintageData


class Vintage:
    """Machine vintage in consumption goods firm"""
    
    def __init__(self, vint_id: int, productivity: float, price: float, 
                 supplier_id: int, t0: int):
        """Initialize vintage"""
        self.id = vint_id
        self.productivity = productivity  # __Avint
        self.price = price  # __pVint
        self.supplier_id = supplier_id
        self.t0 = t0  # Creation time
        self.n_machines = 0  # __nVint
        self.to_scrap = 0  # __RSvint
        self.workers = []  # Workers using this vintage
        
    def calculate_production(self, workers: int) -> float:
        """Calculate production from this vintage"""
        return workers * self.productivity


class Firm2(BaseAgent):
    """
    Consumption goods firm agent
    Produces consumption goods using machines and labor
    """
    
    def __init__(self, firm_id: int, t: int = 0):
        """Initialize Firm2"""
        super().__init__(firm_id, t)
        
        # Firm variables
        self._Q2 = 0.0  # Actual production
        self._Q2e = 0.0  # Expected demand
        self._Q2d = 0.0  # Desired production
        self._D2 = 0.0  # Demand fulfilled
        self._S2 = 0.0  # Sales revenue
        self._p2 = 1.0  # Price
        self._c2 = 1.0  # Unit cost
        self._mu2 = 0.2  # Markup rate
        self._N = 0.0  # Inventories
        self._K = 0  # Capital stock (machines)
        self._Kd = 0  # Desired capital
        self._L2 = 0  # Actual workers
        self._L2d = 0  # Desired workers
        self._W2 = 0.0  # Total wages
        self._A2 = 1.0  # Average productivity
        self._f2 = 0.0  # Market share
        self._NW2 = 0.0  # Net worth
        self._Deb2 = 0.0  # Debt
        self._Pi2 = 0.0  # Profit
        self._Div2 = 0.0  # Dividends
        self._Tax2 = 0.0  # Taxes
        self._l2 = 0.0  # Unfilled demand ratio
        self._EI = 0.0  # Expansion investment
        self._SI = 0.0  # Substitution investment
        
        # Vintages
        self.vintages: List[Vintage] = []
        
    def initialize(self, config: Dict[str, Any]):
        """Initialize firm with configuration"""
        # Production parameters
        self.set_param('m2', config.get('m2', 1.0))
        self.set_param('u', config.get('u', 0.75))
        self.set_param('iota', config.get('iota', 0.1))
        self.set_param('b', config.get('b', 3.0))
        self.set_param('eta', config.get('eta', 20))
        
        # Pricing parameters
        self.set_param('mu20', config.get('mu20', 0.2))
        self.set_param('upsilon', config.get('upsilon', 0.04))
        self.set_param('omega1', config.get('omega1', 1.0))
        self.set_param('omega2', config.get('omega2', 1.0))
        self.set_param('omega3', config.get('omega3', 0.0))
        
        # Expectation parameters
        self.set_param('e0', config.get('e0', 1.0))
        self.set_param('e1', config.get('e1', 0.5))
        self.set_param('chi', config.get('chi', 1.0))
        self.set_param('d2', config.get('d2', 0.5))
        
        # Initial values
        self._mu2 = self.get_param('mu20')
        self._NW2 = config.get('NW20', 100.0)
        
    def step(self, t: int):
        """Execute one time step"""
        # 1. Form expectations
        self.form_expectations(t)
        
        # 2. Plan production and investment
        self.plan_production(t)
        self.plan_investment(t)
        
        # 3. Produce
        self.produce(t)
        
        # 4. Update price and finances
        self.update_price(t)
        self.update_finances(t)
        
        # Update lagged variables
        self.update_lagged(t)
    
    def form_expectations(self, t: int):
        """Form demand expectations"""
        e0 = self.get_param('e0', 1.0)
        e1 = self.get_param('e1', 0.5)
        
        # Get past demand
        d_past = self.get_var('_D2', 1) or self._D2
        
        # Simple adaptive expectations
        self._Q2e = e0 * (e1 * self._D2 + (1 - e1) * d_past)
        
    def plan_production(self, t: int):
        """Plan production based on expectations"""
        iota = self.get_param('iota', 0.1)
        
        # Desired production including inventories
        self._Q2d = self._Q2e * (1 + iota)
        
        # Labor demand
        if self._A2 > 0:
            self._L2d = int(self._Q2d / self._A2)
        else:
            self._L2d = 0
    
    def plan_investment(self, t: int):
        """Plan investment in new machines"""
        u = self.get_param('u', 0.75)
        m2 = self.get_param('m2', 1.0)
        
        # Desired capital
        if self._A2 > 0 and u > 0:
            self._Kd = int(self._Q2d / (self._A2 * u * m2))
        else:
            self._Kd = 0
        
        # Expansion investment
        self._EI = max(0, self._Kd - self._K)
        
        # Substitution investment (scrap old machines)
        self._SI = self.calculate_scrapping(t)
    
    def calculate_scrapping(self, t: int) -> int:
        """Calculate machines to scrap"""
        b = self.get_param('b', 3.0)
        eta = self.get_param('eta', 20)
        scrap = 0
        
        for vintage in self.vintages:
            # Scrap if too old
            if t - vintage.t0 > eta:
                scrap += vintage.n_machines
            # Or if payback period exceeded
            # Simplified logic here
        
        return scrap
    
    def produce(self, t: int):
        """Produce consumption goods"""
        # Production based on workers and capital
        self._Q2 = 0.0
        
        for vintage in self.vintages:
            # Allocate workers to vintages
            workers_on_vintage = len(vintage.workers)
            self._Q2 += vintage.calculate_production(workers_on_vintage)
        
        # Update inventories
        self._N = max(0, self._N + self._Q2 - self._D2)
    
    def update_price(self, t: int):
        """Update price using markup rule"""
        upsilon = self.get_param('upsilon', 0.04)
        
        # Adjust markup based on market share change
        f2_past = self.get_var('_f2', 1) or self._f2
        if f2_past > 0:
            delta_f = (self._f2 - f2_past) / f2_past
            self._mu2 = self._mu2 * (1 + upsilon * delta_f)
        
        # Update price
        self._p2 = (1 + self._mu2) * self._c2
    
    def update_finances(self, t: int):
        """Update financial variables"""
        # Sales revenue
        self._S2 = self._D2 * self._p2
        
        # Unit cost
        if self._Q2 > 0:
            self._c2 = self._W2 / self._Q2
        
        # Gross profit
        self._Pi2 = self._S2 - self._W2
        
        # Taxes
        if self._Pi2 > 0:
            tr = 0.1
            self._Tax2 = self._Pi2 * tr
        else:
            self._Tax2 = 0.0
        
        # Dividends
        d2 = self.get_param('d2', 0.5)
        self._Div2 = max(0, d2 * (self._Pi2 - self._Tax2))
        
        # Net worth
        self._NW2 = self._NW2 + self._Pi2 - self._Tax2 - self._Div2
    
    def add_vintage(self, productivity: float, price: float, 
                    supplier_id: int, t: int, n_machines: int):
        """Add new vintage to capital stock"""
        vint_id = len(self.vintages)
        vintage = Vintage(vint_id, productivity, price, supplier_id, t)
        vintage.n_machines = n_machines
        self.vintages.append(vintage)
        self._K += n_machines
        
        # Update average productivity
        self.update_average_productivity()
    
    def update_average_productivity(self):
        """Update average capital productivity"""
        if not self.vintages or self._K == 0:
            self._A2 = 1.0
            return
            
        total_prod = sum(v.productivity * v.n_machines for v in self.vintages)
        self._A2 = total_prod / self._K
    
    def calculate_competitiveness(self) -> float:
        """Calculate firm competitiveness"""
        omega1 = self.get_param('omega1', 1.0)
        omega2 = self.get_param('omega2', 1.0)
        omega3 = self.get_param('omega3', 0.0)
        
        # Normalized competitiveness
        comp = -omega1 * self._p2 + omega2 * (1 - self._l2) + omega3
        return comp
