"""
Worker Agent Implementation
Represents individual workers/consumers in the K+S model
"""

from typing import Optional
from .agent import Agent
from .constants import *
from .random_engine import random_engine
import math


class Worker(Agent):
    """
    Worker agent class
    
    Workers:
    - Search for jobs in the labor market
    - Possess skills that evolve through learning-by-doing and learning-by-using
    - Receive wages and consume goods
    - Can be unemployed and receive benefits
    - Age and retire according to work-life duration
    """
    
    def __init__(self, worker_id: int, parent: Agent):
        """
        Initialize worker agent
        
        Args:
            worker_id: Unique worker ID
            parent: Parent Labor object
        """
        super().__init__("Worker", parent)
        
        # Worker attributes
        self._id = worker_id
        self._age_val = 0                 # Worker age
        self._employed = 0                # Employment status: 0=unemployed, 1=sector1, 2=sector2
        self._Tc = 0                      # Work contract term
        self._Te = 0                      # Employment tenure in current firm
        self._Tu = 0                      # Periods unemployed
        self._w = 0.0                     # Current wage
        self._wReal = 0.0                 # Real wage (w/CPI)
        self._wRes = 0.0                  # Reservation wage
        self._wR = 0.0                    # Requested wage
        self._s = INISKILL                # Compound skills
        self._sT = INISKILL               # Tenure skills
        self._sV = INISKILL               # Vintage skills
        self._Q = 0.0                     # Production with current skills/vintage
        self._CQ = 1.0                    # Vintage capacity
        self._searchProb = 1.0            # Probability of searching for job
        self._discouraged = 0             # Discouragement status
        
        # Initialize hooks for firm references
        self.add_hooks(WORKERHK)
    
    def initialize(self, age: int, tc: int, w_res: float, sv0: float):
        """
        Initialize worker attributes
        
        Args:
            age: Initial age
            tc: Work contract term
            w_res: Reservation wage
            sv0: Initial vintage skills
        """
        self._age_val = age
        self._Tc = tc
        self._wRes = w_res
        self._sV = sv0
        
        # Initialize variables
        self.write("_age", age)
        self.write("_Tc", tc)
        self.write("_wRes", w_res)
        self.write("_employed", 0)
        self.write("_sT", INISKILL, -1)
        self.write("_sV", sv0, -1)
        self.write("_w", 0.0)
        self.write("_Te", 0)
        self.write("_Tu", 0)
    
    def compute_age(self, tr: int) -> int:
        """
        Update worker age
        Worker ages and "reborns" after retirement
        
        Args:
            tr: Retirement age (0 = no retirement)
            
        Returns:
            New age
        """
        current_age = self.read("_age")
        
        if tr == 0 or current_age < tr:
            new_age = current_age + 1  # Simply gets older
        else:
            new_age = 1  # Reborn at age 1
        
        self.write("_age", new_age)
        self._age_val = new_age
        return new_age
    
    def compute_skills(self, flag_worker_lbu: int, flag_worker_sk_prod: int,
                      flag_learn1: int, gamma: float, tau_g: float, 
                      tau_u: float, tau_t: float, sigma: float) -> float:
        """
        Compute worker compound skills
        
        Skills combine vintage learning-by-using and tenure learning-by-doing
        based on configuration flags
        
        Args:
            flag_worker_lbu: Worker learning mode (0-3)
            flag_worker_sk_prod: Skills effect on productivity (0-3)
            flag_learn1: Learning mode in sector 1
            gamma: Training coverage rate
            tau_g: Training learning factor
            tau_u: Unemployment skills deterioration rate
            tau_t: Tenure learning factor
            sigma: Learning-by-doing public skill level
            
        Returns:
            Compound skills
        """
        # First update tenure skills (_sT)
        self._update_tenure_skills(flag_worker_lbu, flag_learn1, gamma, 
                                   tau_g, tau_u, tau_t)
        
        # Then update vintage skills (_sV)
        self._update_vintage_skills(flag_worker_lbu, sigma)
        
        # Compute compound skills based on mode
        if flag_worker_sk_prod == 0:
            # Skills don't affect productivity
            s = INISKILL
        elif flag_worker_sk_prod == 1:
            # Only vintage skills count
            s = self._sV
        elif flag_worker_sk_prod == 2:
            # Only tenure skills count (normalized)
            st_avg = self.parent.read("sTavg", 1)
            s = self._sT / st_avg if st_avg > 0 else INISKILL
        else:  # flag_worker_sk_prod == 3
            # Both skills count
            st_avg = self.parent.read("sTavg", 1)
            s = self._sV * self._sT / st_avg if st_avg > 0 else INISKILL
        
        self._s = s
        self.write("_s", s)
        return s
    
    def _update_tenure_skills(self, flag_worker_lbu: int, flag_learn1: int,
                             gamma: float, tau_g: float, tau_u: float, 
                             tau_t: float):
        """Update tenure skills based on employment status and learning"""
        if flag_worker_lbu <= 1:  # No learning-by-tenure mode
            self._sT = INISKILL
            self.write("_sT", INISKILL)
            return
        
        if self._age_val == 1:  # Just born
            st_min = self.parent.read("sTmin", 1)
            self._sT = st_min
            self.write("_sT", st_min)
            return
        
        current_st = self.read("_sT", 0)
        
        if self._employed == 0:  # Not employed
            if random_engine.uniform() < gamma:  # Under training
                new_st = current_st * (1 + tau_g)
            else:  # Skills deteriorate
                new_st = current_st / (1 + tau_u)
        
        elif self._employed == 1:  # Sector 1
            if flag_learn1 == 0:
                new_st = current_st  # Keep skills
            elif flag_learn1 == 1:
                new_st = current_st / (1 + tau_u)  # Decrease as unemployed
            elif flag_learn1 == 2:
                new_st = current_st * (1 + tau_t)  # Increase skills
            else:  # flag_learn1 == 3
                # Get minimum skills in sector 1
                cap_sec = self.find_parent("Country").search("Capital")
                new_st = cap_sec.read("sT1min", 1)
        
        else:  # self._employed == 2, Sector 2
            if self._Te == 0:  # Just hired
                # Get firm minimum skills
                firm = self.get_hook(FWRK).parent if self.get_hook(FWRK) else None
                if firm:
                    new_st = firm.read("_sT2min", 1)
                else:
                    new_st = current_st
            else:  # Already working
                new_st = current_st * (1 + tau_t)
        
        # Apply minimum skills floor
        st_min = self.parent.read("sTmin", 1)
        new_st = max(new_st, st_min)
        
        self._sT = new_st
        self.write("_sT", new_st)
    
    def _update_vintage_skills(self, flag_worker_lbu: int, sigma: float):
        """Update vintage skills based on learning-by-using"""
        if flag_worker_lbu == 0 or flag_worker_lbu == 2:
            # No learning-by-vintage mode
            self._sV = INISKILL
            self.write("_sV", INISKILL)
            return
        
        # Check if unemployed or in sector 1
        if self.get_hook(FWRK) is None or self._age_val == 1:
            self._sV = sigma  # Public skills
            self.write("_sV", sigma)
            return
        
        # Learning-by-using formula for sector 2 workers
        current_sv = self.read("_sV", 0)
        q_lag = self.read("_Q", 1)
        cq_lag = self.read("_CQ", 1)
        
        if cq_lag > 0:
            learning = sigma * (q_lag / cq_lag) * current_sv * (1 - current_sv)
            new_sv = current_sv + learning
        else:
            new_sv = current_sv
        
        # Cap vintage skills to [0, INISKILL]
        new_sv = max(0.0, min(INISKILL, new_sv))
        
        self._sV = new_sv
        self.write("_sV", new_sv)
    
    def compute_search_probability(self, flag_search_disc: int, 
                                  search_prob: float, lambda_val: float) -> float:
        """
        Compute probability of searching for job
        
        Args:
            flag_search_disc: Search discouragement mode
            search_prob: Global search probability
            lambda_val: Individual discouragement intensity
            
        Returns:
            Search probability
        """
        if flag_search_disc == 0:
            # Always search
            prob = 1.0
        elif flag_search_disc == 1:
            # Global search probability
            prob = search_prob
        else:  # flag_search_disc == 2
            # Individual search probability based on unemployment duration
            tu = self.read("_Tu")
            prob = lambda_val * math.exp(-lambda_val * tu)
        
        prob = min(prob, 1.0)
        self._searchProb = prob
        self.write("_searchProb", prob)
        return prob
    
    def compute_wage(self, flag_index_wage: int, flag_heter_wage: int) -> float:
        """
        Compute effective wage received
        Adjusts employed workers' wages according to indexation rules
        
        Args:
            flag_index_wage: Wage indexation mode
            flag_heter_wage: Heterogeneous wage mode
            
        Returns:
            Effective wage
        """
        # This is a simplified version - full implementation needs more context
        # from firm and economy-wide variables
        
        if self._employed == 0:
            self._w = 0.0
        else:
            # Keep current wage for now (full indexation logic requires more context)
            self._w = self.read("_w", 0)
        
        self.write("_w", self._w)
        return self._w
    
    def compute_real_wage(self, CPI: float) -> float:
        """
        Compute real wage (_wReal equation)
        
        Real wage is nominal wage deflated by Consumer Price Index
        
        Args:
            CPI: Consumer Price Index
            
        Returns:
            Real wage
        """
        w = self.read("_w")
        wReal = w / CPI if CPI > 0 else w
        
        self._wReal = wReal
        self.write("_wReal", wReal)
        return wReal
    
    def apply_for_jobs(self, omega: float, omega_u: float, 
                      flag_search_mode: int) -> int:
        """
        Submit job applications to firms
        
        Args:
            omega: Number of firms employed workers apply to
            omega_u: Number of firms unemployed workers apply to
            flag_search_mode: Search mode (0=always, 1=unemployed only, 2=low wage)
            
        Returns:
            Number of applications submitted
        """
        # Determine number of applications based on employment status
        if self._employed:
            max_appl = omega
        else:
            max_appl = omega_u
        
        if max_appl == 0:
            self._discouraged = 0
            self.write("_discouraged", 0)
            return 0
        
        # Apply search mode
        search_prob = self._searchProb
        effective_appl = search_prob * max_appl
        
        if flag_search_mode == 1 and self._employed:
            # Search only if unemployed
            effective_appl = 0
        elif flag_search_mode == 2 and self._employed:
            # Search if wage below average
            w2o_avg = self.parent.parent.search("Consumption").read("w2oAvg", 1)
            if self.read("_w", 1) >= w2o_avg:
                effective_appl = 0
        
        # Handle fractional number of applications
        if 0 < effective_appl < 1:
            num_appl = 1 if random_engine.uniform() < effective_appl else 0
        else:
            num_appl = int(effective_appl)
        
        if not self._employed and num_appl <= 0:
            self._discouraged = 1
        else:
            self._discouraged = 0
        
        self.write("_discouraged", self._discouraged)
        return num_appl
    
    def retire_and_update(self):
        """Update employment status and handle retirement"""
        self._Te = self.read("_Te") + 1 if self._employed else 0
        self._Tu = self.read("_Tu") + 1 if not self._employed else 0
        
        self.write("_Te", self._Te)
        self.write("_Tu", self._Tu)
