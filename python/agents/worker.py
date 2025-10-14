"""
Worker Agent Implementation
Translated from fun_KS_worker.h
"""

from typing import Optional, Dict, Any
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.base import BaseAgent
from utils.support import INISKILL, Application


class Worker(BaseAgent):
    """
    Worker agent in the K+S model
    Represents a worker/consumer in the economy
    """
    
    def __init__(self, worker_id: int, t: int = 0):
        """
        Initialize worker
        
        Args:
            worker_id: Unique worker identifier
            t: Current time period
        """
        super().__init__(worker_id, t)
        
        # Worker state variables
        self._age = 1  # Working age
        self._employed = 0  # Employment status (0=unemployed, 1=sector1, 2=sector2)
        self._w = 0.0  # Current wage
        self._wR = 0.0  # Requested wage
        self._wRes = 0.0  # Reservation wage
        self._s = INISKILL  # Compounded skills
        self._sV = INISKILL  # Vintage (machine) skills
        self._sT = INISKILL  # Tenure skills
        self._Te = 0  # Employment tenure
        self._Tu = 0  # Unemployment duration
        self._Tc = 0  # Current contract duration
        self._Q = 0.0  # Production output
        self._Bon = 0.0  # Bonus payment
        self._TaxW = 0.0  # Taxes paid
        self._discouraged = 0  # Discouraged worker flag
        self._searchProb = 1.0  # Job search probability
        self._appl = 0  # Number of applications
        self._CQ = 0.0  # Consumption quantity
        self._dQb = 0.0  # Consumption budget
        self._wReal = 0.0  # Real wage
        self._wS = 0.0  # Wage structure
        
    def initialize(self, config: Dict[str, Any]):
        """
        Initialize worker with configuration
        
        Args:
            config: Configuration parameters
        """
        self.set_param('w0min', config.get('w0min', 1.0))
        self.set_param('Lscale', config.get('Lscale', 1))
        self.set_param('Tc', config.get('Tc', 12))
        self.set_param('Tr', config.get('Tr', 0))
        self.set_param('Ts', config.get('Ts', 4))
        self.set_param('epsilon', config.get('epsilon', 0.02))
        self.set_param('sigma', config.get('sigma', 0.1))
        self.set_param('tauT', config.get('tauT', 0.01))
        self.set_param('tauU', config.get('tauU', 0.01))
        self.set_param('tauG', config.get('tauG', 0.5))
        
        self._w = self.get_param('w0min')
        self._wR = self._w
        
    def step(self, t: int):
        """
        Execute one time step for worker
        
        Args:
            t: Current time period
        """
        # Update age
        self.update_age()
        
        # Update skills based on employment status
        self.update_skills(t)
        
        # Calculate requested wage
        self.calculate_wage_request(t)
        
        # Apply for jobs if conditions met
        self.apply_for_jobs(t)
        
        # Update lagged variables
        self.update_lagged(t)
    
    def update_age(self):
        """Update worker age and handle retirement"""
        tr = self.get_param('Tr', 0)
        if tr == 0 or self._age < tr:
            self._age += 1
        else:
            self._age = 1  # "Reborn" after retirement
            self._employed = 0
            self._Te = 0
            self._Tu = 0
            self._sT = INISKILL
            self._sV = INISKILL
    
    def update_skills(self, t: int):
        """
        Update worker skills based on employment and learning
        
        Args:
            t: Current time period
        """
        # Update vintage skills (_sV)
        self._update_vintage_skills(t)
        
        # Update tenure skills (_sT)
        self._update_tenure_skills(t)
        
        # Compute compounded skills (_s)
        self._compute_compounded_skills()
    
    def _update_vintage_skills(self, t: int):
        """Update vintage (machine) skills"""
        if self._age == 1:
            # New worker gets minimum skills
            self._sV = INISKILL
            return
            
        if self._employed == 0:
            # Unemployed: skills deteriorate
            tauU = self.get_param('tauU', 0.01)
            self._sV = max(self._sV * (1 - tauU), INISKILL)
        elif self._employed == 2:
            # Employed in sector 2: learn from vintage
            tauT = self.get_param('tauT', 0.01)
            # Get vintage productivity from hook
            vintage_hook = self.get_hook('vintage')
            if vintage_hook:
                vintage_prod = vintage_hook.get_var('productivity', 0)
                sigma = self.get_param('sigma', 0.1)
                self._sV = min(self._sV * (1 + tauT), vintage_prod * sigma)
        # Else sector 1: preserve skills
    
    def _update_tenure_skills(self, t: int):
        """Update tenure skills"""
        if self._age == 1:
            self._sT = INISKILL
            return
            
        if self._employed == 0:
            # Unemployed: skills deteriorate
            tauU = self.get_param('tauU', 0.01)
            self._sT = max(self._sT * (1 - tauU), INISKILL)
        else:
            # Employed: learn by doing
            tauT = self.get_param('tauT', 0.01)
            self._sT = self._sT * (1 + tauT)
    
    def _compute_compounded_skills(self):
        """Compute final compounded skills"""
        # This depends on flagWorkerSkProd parameter
        # For now, use both vintage and tenure
        self._s = (self._sV + self._sT) / 2.0
    
    def calculate_wage_request(self, t: int):
        """
        Calculate wage request for job applications
        
        Args:
            t: Current time period
        """
        if self._employed:
            # Employed: request based on current wage and inflation
            self._wR = self._w * 1.0  # Simplified
        else:
            # Unemployed: request based on reservation wage
            w0min = self.get_param('w0min', 1.0)
            self._wRes = max(w0min, self._w * 0.9)
            self._wR = self._wRes
    
    def apply_for_jobs(self, t: int):
        """
        Apply for jobs in both sectors
        
        Args:
            t: Current time period
        """
        # Determine number of applications based on employment status
        if self._employed == 0:
            # Unemployed: apply to more firms
            num_appl = self.get_param('omegaU', 5)
        else:
            # Employed: apply to fewer firms
            num_appl = self.get_param('omega', 2)
        
        self._appl = int(num_appl * self._searchProb)
    
    def calculate_production(self) -> float:
        """
        Calculate production output based on skills and vintage
        
        Returns:
            Production output
        """
        vintage_hook = self.get_hook('vintage')
        if vintage_hook and self._employed == 2:
            vintage_prod = vintage_hook.get_var('productivity', 0)
            self._Q = self._s * vintage_prod
        else:
            self._Q = 0.0
        
        return self._Q
    
    def receive_wage(self, wage: float):
        """
        Receive wage payment
        
        Args:
            wage: Wage amount
        """
        self._w = wage
        self._Te += 1 if self._employed else 0
        self._Tu = 0 if self._employed else self._Tu + 1
    
    def receive_bonus(self, bonus: float):
        """
        Receive bonus payment
        
        Args:
            bonus: Bonus amount
        """
        self._Bon = bonus
    
    def pay_taxes(self, tax_rate: float):
        """
        Pay taxes on income
        
        Args:
            tax_rate: Tax rate
        """
        self._TaxW = (self._w + self._Bon) * tax_rate
    
    def consume(self, budget: float, price: float) -> float:
        """
        Consume goods given budget and price
        
        Args:
            budget: Consumption budget
            price: Good price
            
        Returns:
            Consumption quantity
        """
        self._dQb = budget
        if price > 0:
            self._CQ = budget / price
        else:
            self._CQ = 0.0
        return self._CQ
    
    def get_employment_status(self) -> int:
        """Get employment status (0=unemployed, 1=sector1, 2=sector2)"""
        return self._employed
    
    def set_employment_status(self, status: int):
        """Set employment status"""
        self._employed = status
        if status == 0:
            self._Te = 0
        else:
            self._Tu = 0
    
    def get_skills(self) -> float:
        """Get worker skills"""
        return self._s
    
    def get_wage(self) -> float:
        """Get current wage"""
        return self._w
    
    def get_wage_request(self) -> float:
        """Get requested wage"""
        return self._wR
