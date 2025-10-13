"""
Worker Agent Class
Represents individual workers/consumers in the K+S model
"""

from typing import Optional, Dict, Any
from utils.data_structures import TimeSeriesData
from utils.core_utils import INISKILL, INIWAGE


class Worker:
    """
    Worker/Consumer agent in the K+S model
    Workers search for jobs, may learn skills, consume goods
    """
    
    def __init__(self, worker_id: int, config: Dict[str, Any]):
        # Identity
        self.id = worker_id
        self._ID = worker_id
        
        # Configuration parameters
        self.config = config
        self.Tc = config.get('Labor.Tc', 1)         # work contract term
        self.Tr = config.get('Labor.Tr', 0)         # work-life duration (retirement)
        
        # Employment status
        self._employed = 0              # 0=unemployed, 1=sector1, 2=sector2
        self._Te = 0                    # tenure (periods in current job)
        self._Tu = 0                    # unemployment duration
        self._age = 0                   # worker age
        
        # Skills
        self._sT = INISKILL             # tenure skills (learning-by-doing)
        self._sV = INISKILL             # vintage skills (learning-by-using)
        self._s = INISKILL              # compound skills
        
        # Wages
        self._w = INIWAGE               # current wage
        self._wR = INIWAGE              # real wage
        self._wReal = INIWAGE           # real wage (deflated)
        self._wRes = INIWAGE            # reservation wage
        self._wS = INIWAGE              # satisficing wage (job search threshold)
        self._wfull = INIWAGE           # full-time equivalent wage
        
        # Production and bonuses
        self._Q = 0.0                   # production in current period
        self._CQ = 0.0                  # cumulated production
        self._Bon = 0.0                 # bonus received
        self._TaxW = 0.0                # taxes paid on wages
        
        # Job search
        self._appl = 0                  # number of applications sent
        self._searchProb = 1.0          # probability of searching for job
        self._discouraged = 0           # discouraged worker flag
        
        # Pointers/links
        self.firm = None                # current employer (if employed)
        self.vintage = None             # current vintage working on (if sector 2)
        
        # History tracking
        self.history = {
            'w': TimeSeriesData('wage'),
            'employed': TimeSeriesData('employed'),
            'Te': TimeSeriesData('tenure'),
            's': TimeSeriesData('skills')
        }
        
    def is_employed(self) -> bool:
        """Check if worker is employed"""
        return self._employed > 0
    
    def update_tenure(self):
        """Update tenure counter"""
        if self.is_employed():
            self._Te += 1
            self._Tu = 0
        else:
            self._Te = 0
            self._Tu += 1
    
    def update_age(self):
        """Update worker age"""
        self._age += 1
    
    def should_retire(self) -> bool:
        """Check if worker should retire"""
        return self.Tr > 0 and self._age >= self.Tr
    
    def contract_ends(self) -> bool:
        """Check if work contract ends this period"""
        return self._Te >= self.Tc
    
    def update_skills_employed(self, tau_t: float, flag_worker_lbu: int):
        """
        Update skills when employed (learning-by-doing and learning-by-using)
        
        Args:
            tau_t: learning rate for tenure
            flag_worker_lbu: learning mode flag
        """
        if flag_worker_lbu in [2, 3]:  # Learning-by-tenure
            # Tenure skills increase with experience
            self._sT = self._sT * (1 + tau_t)
        
        # Compound skills (may depend on both tenure and vintage)
        if flag_worker_lbu == 0:
            self._s = INISKILL
        elif flag_worker_lbu == 1:  # Only vintage
            self._s = self._sV
        elif flag_worker_lbu == 2:  # Only tenure
            self._s = self._sT
        else:  # Both vintage and tenure
            self._s = (self._sV + self._sT) / 2
    
    def update_skills_unemployed(self, tau_u: float, sigma: float, 
                                  flag_worker_lbu: int, has_training: bool):
        """
        Update skills when unemployed (deterioration or training)
        
        Args:
            tau_u: skill deterioration rate
            sigma: public skill level
            flag_worker_lbu: learning mode flag
            has_training: whether worker receives government training
        """
        if has_training:
            # Government training helps maintain/improve skills
            tau_g = self.config.get('Labor.tauG', 0.0)
            if flag_worker_lbu in [2, 3]:  # Tenure skills
                self._sT = min(self._sT * (1 + tau_g), sigma)
        else:
            # Skills deteriorate without training
            if flag_worker_lbu in [2, 3]:  # Tenure skills
                self._sT = max(self._sT * (1 - tau_u), sigma)
        
        # Update compound skills
        if flag_worker_lbu == 0:
            self._s = INISKILL
        elif flag_worker_lbu == 1:  # Only vintage
            self._s = self._sV
        elif flag_worker_lbu == 2:  # Only tenure
            self._s = self._sT
        else:  # Both vintage and tenure
            self._s = (self._sV + self._sT) / 2
    
    def compute_reservation_wage(self, w_avg: float, epsilon: float,
                                  flag_search_mode: int) -> float:
        """
        Compute reservation wage for job search
        
        Args:
            w_avg: average wage in economy
            epsilon: minimum wage increment to change jobs
            flag_search_mode: job search mode
        
        Returns:
            Reservation wage
        """
        if not self.is_employed():
            # Unemployed: accept any reasonable offer
            self._wRes = w_avg * (1 - epsilon)
        else:
            if flag_search_mode == 0:  # Always search
                self._wRes = self._w * (1 + epsilon)
            elif flag_search_mode == 1:  # Only if unemployed
                self._wRes = float('inf')  # Won't search
            else:  # flag_search_mode == 2: Search if below average
                if self._w < w_avg:
                    self._wRes = self._w * (1 + epsilon)
                else:
                    self._wRes = float('inf')
        
        return self._wRes
    
    def compute_satisficing_wage(self, ts_chg: int, w_memory: list) -> float:
        """
        Compute satisficing wage based on wage memory
        
        Args:
            ts_chg: number of periods for wage memory
            w_memory: list of past wages
        
        Returns:
            Satisficing wage
        """
        if ts_chg == 0 or len(w_memory) == 0:
            self._wS = self._wRes
        else:
            # Average of recent wages
            relevant_wages = w_memory[:ts_chg]
            self._wS = sum(relevant_wages) / len(relevant_wages) if relevant_wages else self._wRes
        
        return self._wS
    
    def fire(self):
        """Fire worker from current job"""
        self._employed = 0
        self._Te = 0
        self.firm = None
        self.vintage = None
    
    def hire(self, sector: int, firm, wage: float):
        """
        Hire worker to a firm
        
        Args:
            sector: 1 for capital-good, 2 for consumption-good
            firm: Employer firm object
            wage: Offered wage
        """
        self._employed = sector
        self._Te = 0
        self._Tu = 0
        self._w = wage
        self._wR = wage
        self.firm = firm
        self._CQ = 0.0
    
    def produce(self, output: float):
        """Record production"""
        self._Q = output
        self._CQ += output
    
    def receive_bonus(self, bonus: float):
        """Receive profit-sharing bonus"""
        self._Bon = bonus
    
    def pay_taxes(self, tax_amount: float):
        """Pay taxes on wage/bonus"""
        self._TaxW = tax_amount
    
    def update_history(self):
        """Update historical values"""
        self.history['w'].append(self._w)
        self.history['employed'].append(float(self._employed))
        self.history['Te'].append(float(self._Te))
        self.history['s'].append(self._s)
    
    def __repr__(self):
        status = "Employed" if self.is_employed() else "Unemployed"
        return f"Worker(id={self.id}, {status}, wage={self._w:.2f}, skills={self._s:.2f})"
