"""
Worker Agent Implementation for K+S Model.

Matches fun_KS_worker.h from the original C++ implementation.
Represents individual workers/consumers in the labor market.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
import numpy as np

from ..types import INISKILL, INIWAGE


@dataclass
class WorkerState:
    """
    State variables for a worker agent.
    Matches variables from fun_KS_worker.h
    """
    # Identity
    ID: int  # Worker unique ID (_ID)
    
    # Employment status
    employed: int = 0  # 0=unemployed, 1=employed in sector 1, 2=employed in sector 2 (_employed)
    employer: Optional[Any] = None  # Reference to current employer firm
    employer_vintage: Optional[Any] = None  # Reference to vintage if employed (_vwrk hook)
    
    # Contract and tenure
    Tc: int = 1  # Work contract term in periods (_Tc)
    Te: int = 0  # Employment duration with current employer (_Te)
    age: int = 1  # Worker working age (_age)
    retirement_age: int = 0  # Age at which worker retires (Tr parameter)
    
    # Wages and income
    w: float = INIWAGE  # Current wage (_w)
    w_history: List[float] = field(default_factory=list)  # Wage history for requested wage calc
    wRes: float = INIWAGE  # Reservation wage (_wRes)
    bonus: float = 0.0  # Bonus received from profitable firm
    
    # Skills
    sV: float = INISKILL  # Vintage (machine operation) skills (_sV)
    sT: float = INISKILL  # Tenure (on-the-job) skills (_sT)
    s: float = INISKILL  # Compound skills (combination of sV and sT) (_s)
    
    # Job search
    num_applications: int = 0  # Number of job applications in period (_appl)
    search_prob: float = 1.0  # Probability of searching for job (_searchProb)
    discouraged: bool = False  # Whether worker is discouraged from searching (_discouraged)
    
    # Production
    Q: float = 0.0  # Production with current skills and vintage (_Q)


class Worker:
    """
    Worker/Consumer Agent.
    
    Represents individual workers in the K+S model labor market.
    Workers search for jobs, accumulate skills through learning, receive wages,
    and consume goods.
    
    Matches equations from fun_KS_worker.h
    """
    
    def __init__(
        self,
        worker_id: int,
        initial_params: Dict[str, Any]
    ):
        """
        Initialize a worker agent.
        
        Args:
            worker_id: Unique worker ID
            initial_params: Dictionary of initialization parameters
        """
        self.state = WorkerState(ID=worker_id)
        self.params = initial_params
        
        # Initialize from parameters
        self.state.Tc = initial_params.get('Tc', 1)
        self.state.retirement_age = initial_params.get('Tr', 0)
        self.state.wRes = initial_params.get('w0min', INIWAGE)
        self.state.age = initial_params.get('initial_age', 1)
        
        # Initialize wage history
        self.state.w_history = [self.state.w] * 8
    
    def compute_age(self, t: int) -> int:
        """
        Worker working age - accumulates age and makes worker reborn after retirement.
        
        Matches equation '_age' from fun_KS_worker.h lines 26-38
        
        Args:
            t: Current time period
            
        Returns:
            New age
        """
        Tr = self.state.retirement_age
        
        if Tr == 0 or self.state.age < Tr:
            # Simply gets older
            new_age = self.state.age + 1
        else:
            # Retirement - worker is "reborn" with age 1
            new_age = 1
            # Reset skills and employment when reborn
            self.state.employed = 0
            self.state.employer = None
            self.state.Te = 0
            self.state.sT = INISKILL
            self.state.sV = self.params.get('sigma', INISKILL)
        
        self.state.age = new_age
        return new_age
    
    def compute_production(self) -> float:
        """
        Production with current worker skills and vintage.
        
        Matches equation '_Q' from fun_KS_worker.h lines 18-23
        
        Returns:
            Production output
        """
        if self.state.employer_vintage is not None:
            # Worker is allocated to a vintage
            vintage_productivity = self.state.employer_vintage.A  # __Avint
            production = self.state.s * vintage_productivity
        else:
            # Unallocated, unemployed, or in sector 1
            production = 0.0
        
        self.state.Q = production
        return production
    
    def compute_applications(
        self,
        labor_market: Any,
        t: int
    ) -> int:
        """
        Number of job applications for firms in the period.
        Insert candidate in corresponding sector 1 and 2 firms' queues.
        
        Matches equation '_appl' from fun_KS_worker.h lines 41-147
        
        Args:
            labor_market: Reference to labor market object
            t: Current time period
            
        Returns:
            Number of applications made
        """
        employed = self.state.employed
        
        # Determine if worker is in post-change type firm
        post_change_firm = False
        if employed == 2 and self.state.employer is not None:
            post_change_firm = self.state.employer.state.postChg
        
        # Select correct parameters
        if employed and not post_change_firm:
            omega = self.params.get('omegaPreChg', self.params.get('omega', 1))
        else:
            omega = self.params.get('omega', 1) if employed else self.params.get('omegaU', 1)
        
        if omega == 0:
            self.state.discouraged = False
            self.state.num_applications = 0
            return 0
        
        # Determine if worker searches based on search mode
        search_mode = self.params.get('flagSearchMode', 0)
        search_prob = self.compute_search_probability(labor_market)
        
        if search_mode == 0:  # Always search
            effective_applications = search_prob * omega
        elif search_mode == 1:  # Search only if unemployed
            effective_applications = search_prob * omega if not employed else 0
        elif search_mode == 2:  # Search if wage below average
            avg_wage = labor_market.get_average_wage_sector2()
            if self.state.w < avg_wage:
                effective_applications = search_prob * omega
            else:
                effective_applications = 0
        else:
            effective_applications = 0
        
        # Handle fractional applications as probability
        if 0 < effective_applications < 1:
            num_apps = 1 if np.random.random() < effective_applications else 0
        else:
            num_apps = int(np.ceil(effective_applications))
        
        if num_apps == 0:
            self.state.discouraged = True
            self.state.num_applications = 0
            return 0
        
        self.state.discouraged = False
        self.state.num_applications = num_apps
        
        # Actually submit applications to firms (handled by labor market)
        return num_apps
    
    def compute_search_probability(self, labor_market: Any) -> float:
        """
        Individual probability of searching for job in period.
        
        Matches equation '_searchProb' from fun_KS_worker.h lines 150-173
        
        Args:
            labor_market: Reference to labor market object
            
        Returns:
            Search probability
        """
        search_disc_mode = self.params.get('flagSearchDisc', 0)
        
        if search_disc_mode == 0:
            # Always search
            prob = 1.0
        elif search_disc_mode == 1:
            # Global discouragement based on aggregate unemployment
            kappa = self.params.get('kappa', 1.0)
            Ue = labor_market.get_unemployment_rate()
            prob = labor_market.global_search_prob  # Computed at market level
        elif search_disc_mode == 2:
            # Individual discouragement based on personal unemployment
            lambda_param = self.params.get('lambda', 1.0)
            if self.state.employed:
                prob = 1.0
            else:
                # Probability decreases with unemployment duration
                unemp_duration = t - self.state.Te if self.state.Te > 0 else 1
                prob = lambda_param * np.exp(-lambda_param * unemp_duration)
        else:
            prob = 1.0
        
        self.state.search_prob = prob
        return prob
    
    def compute_skills(self, t: int) -> float:
        """
        Update worker skills based on learning mode.
        
        Matches equations '_s', '_sT', '_sV' from fun_KS_worker.h
        
        Args:
            t: Current time period
            
        Returns:
            Compound skills
        """
        learning_mode = self.params.get('flagWorkerLBU', 0)
        
        if learning_mode == 0:
            # No worker-level learning
            self.state.s = INISKILL
            return self.state.s
        
        # Store previous values for compound calculation
        prev_sT = self.state.sT
        prev_sV = self.state.sV
        
        # Update tenure skills if employed
        if self.state.employed:
            tau_T = self.params.get('tauT', 0.0)
            self.state.sT = prev_sT * (1 + tau_T)
            self.state.Te += 1
        else:
            # Skills deteriorate if unemployed
            tau_U = self.params.get('tauU', 0.0)
            self.state.sT = prev_sT * (1 - tau_U)
            self.state.Te = 0
        
        # Update vintage skills (if relevant)
        if learning_mode in [1, 3]:  # Learning-by-vintage
            if self.state.employer_vintage is not None:
                # Skills update based on vintage
                self.state.sV = self.state.employer_vintage.sVavg
        
        # Compute compound skills based on mode
        if learning_mode == 1:  # Vintage only
            self.state.s = prev_sV
        elif learning_mode == 2:  # Tenure only
            self.state.s = self.state.sT
        elif learning_mode == 3:  # Both
            self.state.s = (prev_sV + self.state.sT) / 2
        else:
            self.state.s = INISKILL
        
        return self.state.s
    
    def compute_requested_wage(self, t: int) -> float:
        """
        Compute wage requested by worker when applying for jobs.
        
        Matches equation '_wReq' from fun_KS_worker.h
        
        Args:
            t: Current time period
            
        Returns:
            Requested wage
        """
        Ts = self.params.get('Ts', 0)
        epsilon = self.params.get('epsilon', 0.01)
        
        if Ts == 0:
            # No memory - use reservation wage
            return self.state.wRes
        
        # Use average of recent wages
        recent_wages = self.state.w_history[:min(Ts, len(self.state.w_history))]
        avg_wage = np.mean(recent_wages) if recent_wages else self.state.wRes
        
        # Request slightly more than past average (epsilon increment)
        requested = avg_wage * (1 + epsilon)
        
        return max(requested, self.state.wRes)
    
    def update_wage(self, new_wage: float, t: int) -> None:
        """
        Update worker's wage.
        
        Args:
            new_wage: New wage value
            t: Current time period
        """
        self.state.w = new_wage
        
        # Update wage history
        self.state.w_history.insert(0, new_wage)
        if len(self.state.w_history) > 8:
            self.state.w_history = self.state.w_history[:8]
    
    def accept_job_offer(
        self,
        firm: Any,
        wage_offer: float,
        sector: int,
        t: int
    ) -> bool:
        """
        Worker accepts a job offer.
        
        Args:
            firm: Employer firm object
            wage_offer: Offered wage
            sector: Sector number (1 or 2)
            t: Current time period
            
        Returns:
            True if offer accepted
        """
        # Check if offer is better than current situation
        if self.state.employed and wage_offer <= self.state.w:
            return False
        
        # Check minimum increment to change jobs
        if self.state.employed:
            epsilon = self.params.get('epsilon', 0.01)
            if wage_offer < self.state.w * (1 + epsilon):
                return False
        
        # Accept the offer
        if self.state.employer is not None:
            # Quit current job
            self.quit_job(t)
        
        self.state.employed = sector
        self.state.employer = firm
        self.state.Te = 0
        self.update_wage(wage_offer, t)
        
        return True
    
    def quit_job(self, t: int) -> None:
        """
        Worker quits current job.
        
        Args:
            t: Current time period
        """
        if self.state.employer is not None:
            # Remove from employer's worker list (handled by employer)
            pass
        
        self.state.employed = 0
        self.state.employer = None
        self.state.employer_vintage = None
        self.state.Te = 0
    
    def get_fired(self, t: int) -> None:
        """
        Worker gets fired.
        
        Args:
            t: Current time period
        """
        self.quit_job(t)
    
    def receive_bonus(self, bonus: float) -> None:
        """
        Worker receives profit-sharing bonus.
        
        Args:
            bonus: Bonus amount
        """
        self.state.bonus = bonus
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Export worker state as dictionary.
        
        Returns:
            Dictionary of worker state variables
        """
        return {
            'ID': self.state.ID,
            'employed': self.state.employed,
            'age': self.state.age,
            'Te': self.state.Te,
            'w': self.state.w,
            'wRes': self.state.wRes,
            'bonus': self.state.bonus,
            'sV': self.state.sV,
            'sT': self.state.sT,
            's': self.state.s,
            'Q': self.state.Q,
            'num_applications': self.state.num_applications,
            'discouraged': self.state.discouraged,
        }
