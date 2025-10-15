"""
Worker Agent Implementation
Implements worker/consumer agents with skills, employment, and job search behavior.
Based on fun_KS_worker.h
"""

from typing import Optional, List
from .agents import BaseAgent
from .config import WORKERHK, FWRK, VWRK, INISKILL
import math


class Worker(BaseAgent):
    """
    Worker/Consumer agent class.
    Handles employment, skills, wage requests, and job applications.
    """
    
    def __init__(self, agent_id: int, parent=None):
        super().__init__(agent_id, "Worker", parent)
        
        # Initialize hooks for Worker
        self.hooks = [None] * WORKERHK
        
        # Worker-specific variables (initialized in equations)
        self._employed = 0          # Employment status: 0=unemployed, 1=sector1, 2=sector2
        self._employer = None       # Current employer firm
        self._s = INISKILL         # Compound skills
        self._sV = INISKILL        # Vintage (learning-by-using) skills
        self._sT = INISKILL        # Tenure (learning-by-doing) skills
        self._w = 0.0              # Actual wage
        self._wR = 0.0             # Requested wage
        self._appl = 0             # Number of applications sent
        self._discouraged = False  # Job search discouragement flag
        self._Te = 0               # Employment tenure (periods)
        self._Tc = 0               # Contract remaining periods
        self._Tp = 0               # Protection remaining periods
        self._vintage_id = 0       # ID of vintage currently working with
        
    def compute_skills(self, flagWorkerSkProd: int) -> float:
        """
        Compute worker compound skills (_s equation).
        
        Args:
            flagWorkerSkProd: Flag for how skills affect productivity
            
        Returns:
            Compound skill level
        """
        if flagWorkerSkProd == 0:
            # Skills don't affect productivity
            s = INISKILL
        elif flagWorkerSkProd == 1:
            # Only vintage skills count
            s = self._sV
        elif flagWorkerSkProd == 2:
            # Only tenure skills count
            s = self._sT
        else:  # flagWorkerSkProd == 3
            # Both vintage & tenure skills count (average)
            s = (self._sV + self._sT) / 2.0
        
        self.WRITE("_s", s)
        return s
    
    def update_vintage_skills(self, sVp: float, sigma: float) -> float:
        """
        Update vintage skills (_sV equation).
        
        Args:
            sVp: Public skill level for the vintage
            sigma: Learning-by-doing parameter
            
        Returns:
            Updated vintage skills
        """
        if self._employed > 0 and sVp > 0:
            # Worker is employed and uses a vintage
            sV_new = self._sV + sigma * (sVp - self._sV)
            self._sV = max(sV_new, INISKILL)
        elif self._employed == 0:
            # Unemployed workers lose skills
            self._sV = INISKILL
        
        self.WRITE("_sV", self._sV)
        return self._sV
    
    def update_tenure_skills(self, tauT: float, tauU: float) -> float:
        """
        Update tenure skills (_sT equation).
        
        Args:
            tauT: Tenure learning factor for employed
            tauU: Skills deterioration rate for unemployed
            
        Returns:
            Updated tenure skills
        """
        if self._employed > 0:
            # Employed workers learn
            self._sT = self._sT * (1.0 + tauT)
        else:
            # Unemployed workers lose skills
            self._sT = max(self._sT * (1.0 - tauU), INISKILL)
        
        self.WRITE("_sT", self._sT)
        return self._sT
    
    def compute_wage_request(self, params: dict, t: int) -> float:
        """
        Compute wage request (_wR equation).
        
        Args:
            params: Dictionary with model parameters (Ts, psi1-5, inflation, etc.)
            t: Current time period
            
        Returns:
            Requested wage
        """
        Ts = params['Ts']
        psi1 = params['psi1']
        psi2 = params['psi2']
        psi3 = params['psi3']
        psi4 = params['psi4']
        piT = params['piT']      # Expected inflation
        dCPIb = params['dCPIb']   # Current inflation
        dAb = params['dAb']       # General productivity variation
        dUeB = params['dUeB']     # Unemployment variation
        epsilon = params['epsilon']  # Minimum wage increment to change jobs
        
        # Get employment status
        h = self._employed
        
        if h == 1:
            # Worker in sector 1
            dA = params.get('dA1b', 0.0)  # Sector 1 productivity variation
            k = 4  # Placeholder for employer life cycle status
        elif h == 2:
            # Worker in sector 2
            k = params.get('life2cycle', 0)  # Employer status
            if k == 0:  # Handle entrants
                dA = dAb
            else:
                dA = params.get('dA2', 0.0)  # Firm-level productivity
        else:
            # Unemployed
            dA = 0.0
            k = 0
        
        # Compute wage adjustment factors
        if h == 0:
            # Unemployed - use general trends
            prod_adj = psi2 * dAb
        elif params.get('flagHeterWage', 0) == 0:
            # Homogeneous wage indexation
            prod_adj = psi2 * dAb
        elif params.get('flagHeterWage', 0) == 1:
            # Firm-level heterogeneity
            prod_adj = psi4 * dA
        else:  # flagHeterWage == 2
            # Worker-level heterogeneity
            if self._s > INISKILL:
                prod_adj = psi4 * (self._s / self.VL("_s", 1) - 1.0)
            else:
                prod_adj = 0.0
        
        # Base wage from memory
        if Ts == 0 or self._Te == 0:
            w_base = self._w
        else:
            # Average over Ts periods
            w_sum = 0.0
            for lag in range(min(Ts, self._Te)):
                w_sum += self.VL("_w", lag + 1)
            w_base = w_sum / min(Ts, self._Te)
        
        # Compute requested wage
        inflation_adj = psi1 * max(dCPIb, piT)
        unemployment_adj = psi3 * dUeB
        
        wR = w_base * (1.0 + inflation_adj + prod_adj + unemployment_adj)
        
        # Minimum increment if changing jobs
        if h > 0 and params.get('searching', False):
            wR = max(wR, self._w * (1.0 + epsilon))
        
        self._wR = max(wR, params.get('w0min', 0.0))
        self.WRITE("_wR", self._wR)
        return self._wR
    
    def send_applications(self, firms: List, omega: int, random_engine) -> int:
        """
        Send job applications (_appl equation).
        
        Args:
            firms: List of firms to potentially apply to
            omega: Average number of applications to send
            random_engine: Random number generator
            
        Returns:
            Number of applications sent
        """
        if self._discouraged:
            return 0
        
        # Determine number of applications (Poisson distribution)
        n_appl = max(1, random_engine.poisson(omega))
        n_appl = min(n_appl, len(firms))
        
        # Select random firms to apply to
        target_firms = random_engine.choice(firms, size=n_appl, replace=False)
        
        # Create application data
        from .agents import Application
        for firm in target_firms:
            app = Application(
                w=self._wR,
                s=self._s,
                ws=self._wR / self._s if self._s > 0 else float('inf'),
                Te=self._Te,
                wrk=self
            )
            # Add application to firm's queue (handled by firm)
            if hasattr(firm, 'extensions') and 'appl' in firm.extensions:
                firm.extensions['appl'].appl.append(app)
        
        self._appl = n_appl
        self.WRITE("_appl", n_appl)
        return n_appl
    
    def check_discouragement(self, flagSearchDisc: int, Ue: float, lambda_: float, kappa: float, random_engine) -> bool:
        """
        Check if worker is discouraged from job search.
        
        Args:
            flagSearchDisc: Discouragement mode
            Ue: Unemployment rate
            lambda_: Individual discouragement intensity
            kappa: Overall discouragement intensity
            random_engine: Random number generator
            
        Returns:
            True if discouraged, False otherwise
        """
        if flagSearchDisc == 0:
            # Always search
            self._discouraged = False
        elif flagSearchDisc == 1:
            # Global search probability
            prob = 1.0 / (1.0 + kappa * Ue)
            self._discouraged = not random_engine.bernoulli(prob)
        else:  # flagSearchDisc == 2
            # Individual search probability
            u_periods = max(0, self.V("_u_periods"))  # Unemployment duration
            prob = 1.0 / (1.0 + lambda_ * u_periods)
            self._discouraged = not random_engine.bernoulli(prob)
        
        self.WRITE("_discouraged", 1.0 if self._discouraged else 0.0)
        return self._discouraged
    
    def retire_or_new_contract(self, Tr: int, Tc: int, t: int) -> bool:
        """
        Check retirement or renew contract.
        
        Args:
            Tr: Retirement period limit
            Tc: Contract term length
            t: Current time period
            
        Returns:
            True if worker retires, False otherwise
        """
        # Check retirement
        if Tr > 0 and self._Te >= Tr:
            return True
        
        # Decrease contract period
        if self._Tc > 0:
            self._Tc -= 1
            self.WRITE("_Tc", self._Tc)
        
        # Decrease protection period
        if self._Tp > 0:
            self._Tp -= 1
            self.WRITE("_Tp", self._Tp)
        
        return False
    
    def hire(self, firm, wage: float, vintage_id: int, sector: int, Tc: int, Tp: int):
        """
        Hire worker to a firm.
        
        Args:
            firm: Hiring firm
            wage: Offered wage
            vintage_id: Vintage ID (for sector 2)
            sector: Sector number (1 or 2)
            Tc: Contract term
            Tp: Protection period
        """
        self._employed = sector
        self._employer = firm
        self._w = wage
        self._vintage_id = vintage_id if sector == 2 else 0
        self._Tc = Tc
        self._Tp = Tp
        self._Te = 0
        
        self.WRITE("_employed", sector)
        self.WRITE("_w", wage)
        self.WRITE("_Tc", Tc)
        self.WRITE("_Tp", Tp)
        self.WRITE("_Te", 0)
    
    def fire(self):
        """Fire worker (terminate employment)"""
        self._employed = 0
        self._employer = None
        self._w = 0.0
        self._vintage_id = 0
        
        self.WRITE("_employed", 0)
        self.WRITE("_w", 0.0)
