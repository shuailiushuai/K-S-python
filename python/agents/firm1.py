"""
Firm1 (Capital Goods Sector) Agent Implementation
Translated from fun_KS_firm1.h
"""

from typing import Dict, Any, List
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.base import BaseAgent
from utils.random_gen import get_random_generator
from utils.support import INIPROD


class Firm1(BaseAgent):
    """
    Capital goods firm agent
    Produces machines through R&D and innovation/imitation
    """
    
    def __init__(self, firm_id: int, t: int = 0):
        """
        Initialize Firm1
        
        Args:
            firm_id: Unique firm identifier
            t: Current time period
        """
        super().__init__(firm_id, t)
        
        # Firm variables
        self._Atau = INIPROD  # Machine productivity (technology)
        self._Btau = INIPROD  # Competitiveness of machine
        self._p1 = 1.0  # Machine price
        self._Q1 = 0.0  # Production quantity
        self._Q1e = 0.0  # Expected production
        self._D1 = 0.0  # Demand for machines
        self._S1 = 0.0  # Sales revenue
        self._W1 = 0.0  # Total wages
        self._L1 = 0  # Number of workers
        self._L1d = 0  # Desired workers
        self._L1rd = 0  # R&D workers
        self._RD = 0.0  # R&D expenditure
        self._inn = 0  # Innovation success
        self._imi = 0  # Imitation success
        self._NW1 = 0.0  # Net worth
        self._Deb1 = 0.0  # Debt
        self._Pi1 = 0.0  # Profit
        self._Div1 = 0.0  # Dividends
        self._Tax1 = 0.0  # Taxes
        self._f1 = 0.0  # Market share
        self._c1 = 0.0  # Unit cost
        self._NC = 0  # Number of clients
        self._HC = 0  # Number of new clients (hires)
        self._BC = 0  # Number of lost clients (breaks)
        
    def initialize(self, config: Dict[str, Any]):
        """Initialize firm with configuration"""
        # Technology parameters
        self.set_param('alpha1', config.get('alpha1', 3.0))
        self.set_param('beta1', config.get('beta1', 3.0))
        self.set_param('alpha2', config.get('alpha2', 3.0))
        self.set_param('beta2', config.get('beta2', 3.0))
        self.set_param('x1inf', config.get('x1inf', -0.15))
        self.set_param('x1sup', config.get('x1sup', 0.15))
        self.set_param('xi', config.get('xi', 0.5))
        self.set_param('zeta1', config.get('zeta1', 1.0))
        self.set_param('zeta2', config.get('zeta2', 1.0))
        
        # Production parameters
        self.set_param('m1', config.get('m1', 1.0))
        self.set_param('mu1', config.get('mu1', 0.04))
        self.set_param('nu', config.get('nu', 0.02))
        self.set_param('gamma', config.get('gamma', 0.1))
        self.set_param('d1', config.get('d1', 0.5))
        
        # Initial values
        self._Atau = INIPROD
        self._p1 = (1 + self.get_param('mu1')) / self.get_param('m1')
        self._NW1 = config.get('NW10', 100.0)
    
    def step(self, t: int):
        """Execute one time step"""
        # 1. R&D activities
        self.conduct_rd(t)
        
        # 2. Receive orders
        self.process_orders(t)
        
        # 3. Calculate production
        self.calculate_production(t)
        
        # 4. Update finances
        self.update_finances(t)
        
        # Update lagged variables
        self.update_lagged(t)
    
    def conduct_rd(self, t: int):
        """
        Conduct R&D for innovation and imitation
        
        Args:
            t: Current time period
        """
        rng = get_random_generator()
        
        # R&D expenditure
        nu = self.get_param('nu', 0.02)
        self._RD = nu * self._S1
        
        # Split between innovation and imitation
        xi = self.get_param('xi', 0.5)
        rd_inn = xi * self._RD
        rd_imi = (1 - xi) * self._RD
        
        # Innovation attempt
        alpha1 = self.get_param('alpha1')
        beta1 = self.get_param('beta1')
        zeta1 = self.get_param('zeta1')
        
        inn_prob = 1 - (1 + rd_inn) ** (-zeta1)
        if rng.uniform() < inn_prob:
            # Successful innovation
            x1inf = self.get_param('x1inf')
            x1sup = self.get_param('x1sup')
            delta_a = rng.beta(alpha1, beta1) * (x1sup - x1inf) + x1inf
            new_a = self._Atau * (1 + delta_a)
            
            if new_a > self._Atau:
                self._Atau = new_a
                self._inn = 1
            else:
                self._inn = 0
        else:
            self._inn = 0
        
        # Imitation attempt
        alpha2 = self.get_param('alpha2')
        beta2 = self.get_param('beta2')
        zeta2 = self.get_param('zeta2')
        
        imi_prob = 1 - (1 + rd_imi) ** (-zeta2)
        if rng.uniform() < imi_prob:
            # Try to imitate best competitor
            # For now, simplified: improve by small amount
            delta_a = rng.beta(alpha2, beta2) * 0.05
            self._Atau = self._Atau * (1 + delta_a)
            self._imi = 1
        else:
            self._imi = 0
    
    def process_orders(self, t: int):
        """Process orders from consumption goods firms"""
        # Orders received from clients
        # This is set by market mechanism
        pass
    
    def calculate_production(self, t: int):
        """Calculate production quantity"""
        m1 = self.get_param('m1', 1.0)
        
        # Production based on workers
        self._Q1 = self._L1 * m1
        self._Q1e = min(self._Q1, self._D1)
    
    def update_finances(self, t: int):
        """Update financial variables"""
        # Sales revenue
        self._S1 = self._Q1e * self._p1
        
        # Unit cost
        m1 = self.get_param('m1', 1.0)
        w1avg = self.get_var('w1avg', 0) or 1.0
        self._c1 = w1avg / m1
        
        # Gross profit
        self._Pi1 = self._S1 - self._W1 - self._RD
        
        # Taxes
        if self._Pi1 > 0:
            tr = 0.1  # Tax rate
            self._Tax1 = self._Pi1 * tr
        else:
            self._Tax1 = 0.0
        
        # Dividends
        d1 = self.get_param('d1', 0.5)
        self._Div1 = max(0, d1 * (self._Pi1 - self._Tax1))
        
        # Net worth
        self._NW1 = self._NW1 + self._Pi1 - self._Tax1 - self._Div1
        
        # Price update (markup rule)
        mu1 = self.get_param('mu1')
        self._p1 = (1 + mu1) * self._c1
    
    def hire_workers(self, available: int) -> int:
        """
        Hire workers based on demand
        
        Args:
            available: Number of available workers
            
        Returns:
            Number of workers hired
        """
        need = max(0, self._L1d - self._L1)
        hired = min(need, available)
        self._L1 += hired
        return hired
    
    def fire_workers(self, num: int):
        """Fire workers"""
        self._L1 = max(0, self._L1 - num)
    
    def get_machine_specs(self) -> Dict[str, float]:
        """Get machine specifications"""
        return {
            'productivity': self._Atau,
            'price': self._p1,
            'supplier_id': self.id
        }
