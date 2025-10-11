"""
Labor Market Module
Implements labor market search and matching mechanisms
"""

from typing import List, Tuple, Optional
from .agent import Agent
from .worker import Worker
from .data_structures import Application, WageOffer
from .support import safe_divide
from .random_engine import random_engine
from .constants import INISKILL, INIPROD
import math


class LaborMarket(Agent):
    """
    Labor Market agent class
    
    Manages:
    - Worker job applications
    - Firm job openings
    - Search and matching
    - Hiring and firing
    - Wage offers
    - Unemployment tracking
    """
    
    def __init__(self, parent: Agent):
        """
        Initialize Labor Market
        
        Args:
            parent: Parent Country object
        """
        super().__init__("Labor", parent)
        
        # Labor force statistics
        self._Ls = 0                      # Labor supply (workforce size)
        self._L = 0                       # Employed workers
        self._Ue = 0.0                    # Unemployment rate (effective)
        self._U = 0.0                     # Unemployment rate (including discouraged)
        self._Us = 0.0                    # Short-term unemployment rate
        
        # Wage statistics
        self._wAvg = 0.0                  # Average wage
        self._w0min = 0.5                 # Minimum wage
        self._wCent = 1.0                 # Centralized wage (if applicable)
        
        # Skills statistics
        self._sAvg = 1.0                  # Average skills
        self._sTavg = 1.0                 # Average tenure skills
        self._sVavg = 1.0                 # Average vintage skills
        
        # Training
        self._Ltrain = 0                  # Workers in training
        self._Gtrain = 0.0                # Government training expenditure
        
        # Wage policy
        self._wMinPol = 0.5               # Policy minimum wage
        self._wCent = 1.0                 # Centralized wage (if used)
        self._wU = 0.0                    # Unemployment benefit
        self._psi1 = 1.0                  # Inflation adjustment parameter
        self._psi2 = 0.5                  # Productivity adjustment parameter
        self._psi3 = -0.3                 # Unemployment adjustment parameter
        
        # Additional statistics
        self._sTmax = 1.0                 # Maximum tenure skills
        self._sTmin = 1.0                 # Minimum tenure skills
        self._sTsd = 0.0                  # Std dev of tenure skills
        self._sVsd = 0.0                  # Std dev of vintage skills
        self._TeAvg = 0.0                 # Average tenure in current job
        self._dUeB = 0.0                  # Bounded unemployment rate change
        
        # Applications and offers
        self._applications_sector1 = []  # Sector 1 applications
        self._applications_sector2 = []  # Sector 2 applications by firm
        self._wage_offers = []            # List of wage offers
        
    def collect_applications(self, workers: List[Worker]) -> Tuple[int, int]:
        """
        Collect job applications from all workers
        
        Args:
            workers: List of worker agents
        
        Returns:
            Tuple of (total_applications, unemployed_count)
        """
        self._applications_sector1 = []
        self._applications_sector2 = {}
        
        total_apps = 0
        unemployed = 0
        
        for worker in workers:
            # Check employment status
            if worker.read("_employed", 0) == 0:
                unemployed += 1
            
            # Get worker's applications (simplified - in full model, workers apply)
            # This would be called during worker's apply_for_jobs() method
            
        return total_apps, unemployed
    
    def match_sector1(self, firms: List, applications: List[Application], 
                      hiring_mode: int = 0) -> List[Tuple]:
        """
        Match workers to Firm1 positions
        
        Args:
            firms: List of Firm1 objects
            applications: List of worker applications
            hiring_mode: Mode for ranking applicants (0=wage, 1=skills, 2=tenure)
        
        Returns:
            List of (firm, worker, wage) matches
        """
        matches = []
        
        if not applications or not firms:
            return matches
        
        # Rank applications based on hiring mode
        if hiring_mode == 0:
            # Hire by lowest wage request
            applications_sorted = sorted(applications, key=lambda a: a.w)
        elif hiring_mode == 1:
            # Hire by highest skills
            applications_sorted = sorted(applications, key=lambda a: a.s, reverse=True)
        elif hiring_mode == 2:
            # Hire by longest tenure
            applications_sorted = sorted(applications, key=lambda a: a.Te, reverse=True)
        else:
            # Combined: best wage-skill ratio
            applications_sorted = sorted(applications, key=lambda a: a.ws)
        
        # Process each firm's hiring needs
        for firm in firms:
            L1d = firm.read("_L1d", 0)  # Desired labor
            L1 = firm.read("_L1", 1)     # Current labor
            
            vacancies = max(0, L1d - L1)
            
            if vacancies == 0:
                continue
            
            # Get firm's wage offer
            w1avg = firm.parent.read("w1avg", 1) if firm.parent else 1.0
            
            # Hire workers
            hired = 0
            for app in applications_sorted[:]:
                if hired >= vacancies:
                    break
                
                # Check if worker acceptable (wage request not too high)
                if app.w <= w1avg * 1.2:  # Accept up to 20% above average
                    matches.append((firm, app.wrk, w1avg))
                    applications_sorted.remove(app)
                    hired += 1
        
        return matches
    
    def match_sector2(self, firms: List, applications_by_firm: dict,
                      hiring_mode: int = 0, firing_mode: int = 0) -> List[Tuple]:
        """
        Match workers to Firm2 positions with hiring and firing
        
        Args:
            firms: List of Firm2 objects
            applications_by_firm: Dictionary of {firm: [applications]}
            hiring_mode: Mode for ranking applicants
            firing_mode: Mode for firing workers (0=LIFO, 1=FIFO, 2=lowest_prod, etc.)
        
        Returns:
            List of (firm, worker, wage, action) where action='hire' or 'fire'
        """
        matches = []
        
        for firm in firms:
            L2d = firm.read("_L2d", 0)  # Desired labor
            L2 = firm.read("_L2", 1)     # Current labor
            
            # Get applications for this firm
            applications = applications_by_firm.get(firm, [])
            
            if L2d > L2:
                # Need to hire
                vacancies = L2d - L2
                
                # Rank applications
                if hiring_mode == 0:
                    apps_sorted = sorted(applications, key=lambda a: a.w)
                elif hiring_mode == 1:
                    apps_sorted = sorted(applications, key=lambda a: a.s, reverse=True)
                elif hiring_mode == 2:
                    apps_sorted = sorted(applications, key=lambda a: a.Te, reverse=True)
                else:
                    apps_sorted = sorted(applications, key=lambda a: a.ws)
                
                # Get wage offer
                w2o = firm.read("_w2o", 0)
                
                # Hire workers
                for app in apps_sorted[:vacancies]:
                    matches.append((firm, app.wrk, w2o, 'hire'))
            
            elif L2d < L2:
                # Need to fire
                to_fire = L2 - L2d
                
                # Get current workers (simplified - in full model, track worker objects)
                # Fire based on firing mode
                # This is placeholder logic - full implementation needs worker tracking
                
                # For now, just record that firing is needed
                pass
        
        return matches
    
    def execute_matches(self, matches: List[Tuple]):
        """
        Execute hiring matches
        
        Args:
            matches: List of (firm, worker, wage[, action]) tuples
        """
        for match in matches:
            firm = match[0]
            worker = match[1]
            wage = match[2]
            action = match[3] if len(match) > 3 else 'hire'
            
            if action == 'hire':
                # Update worker
                worker.write("_employed", 1 if firm.name == "Firm1" else 2)
                worker.write("_w", wage)
                worker.write("_Te", 0)
                worker.write("_Tu", 0)
                
                # Update firm
                current_L = firm.read("_L1" if firm.name == "Firm1" else "_L2", 1)
                firm.write("_L1" if firm.name == "Firm1" else "_L2", current_L + 1)
                
                # Set hooks for tracking
                worker.set_hook(FIRM_HOOK_IDX, firm)  # Worker → Firm
    
    def compute_unemployment_rate(self, workers: List[Worker]) -> Tuple[float, float, float]:
        """
        Compute various unemployment measures
        
        Args:
            workers: List of worker agents
        
        Returns:
            Tuple of (effective_U, total_U, short_term_U)
        """
        total_workers = len(workers)
        unemployed = 0
        discouraged = 0
        short_term_unemployed = 0
        
        for worker in workers:
            employed = worker.read("_employed", 0)
            
            if employed == 0:
                unemployed += 1
                
                # Check if discouraged
                if worker.read("_discouraged", 0):
                    discouraged += 1
                
                # Check unemployment duration
                Tu = worker.read("_Tu", 0)
                if Tu <= 1:
                    short_term_unemployed += 1
        
        # Effective unemployment (not counting discouraged)
        Ue = safe_divide(unemployed - discouraged, total_workers, 0)
        
        # Total unemployment (including discouraged)
        U = safe_divide(unemployed, total_workers, 0)
        
        # Short-term unemployment
        Us = safe_divide(short_term_unemployed, total_workers, 0)
        
        self.write("_Ue", Ue)
        self.write("_U", U)
        self.write("_Us", Us)
        
        self._Ue = Ue
        self._U = U
        self._Us = Us
        
        return Ue, U, Us
    
    def compute_average_wage(self, workers: List[Worker]) -> float:
        """
        Compute average wage across all employed workers
        
        Args:
            workers: List of worker agents
        
        Returns:
            Average wage
        """
        total_wage = 0.0
        employed_count = 0
        
        for worker in workers:
            if worker.read("_employed", 0) > 0:
                total_wage += worker.read("_w", 0)
                employed_count += 1
        
        wAvg = safe_divide(total_wage, employed_count, self._w0min)
        
        self.write("_wAvg", wAvg)
        self._wAvg = wAvg
        return wAvg
    
    def compute_average_skills(self, workers: List[Worker]) -> Tuple[float, float, float]:
        """
        Compute average skills across workers
        
        Args:
            workers: List of worker agents
        
        Returns:
            Tuple of (avg_total_skills, avg_tenure_skills, avg_vintage_skills)
        """
        total_s = 0.0
        total_sT = 0.0
        total_sV = 0.0
        count = 0
        
        for worker in workers:
            total_s += worker.read("_s", 0)
            total_sT += worker.read("_sT", 0)
            total_sV += worker.read("_sV", 0)
            count += 1
        
        sAvg = safe_divide(total_s, count, 1.0)
        sTavg = safe_divide(total_sT, count, 1.0)
        sVavg = safe_divide(total_sV, count, 1.0)
        
        self.write("_sAvg", sAvg)
        self.write("_sTavg", sTavg)
        self.write("_sVavg", sVavg)
        
        self._sAvg = sAvg
        self._sTavg = sTavg
        self._sVavg = sVavg
        
        return sAvg, sTavg, sVavg
    
    def train_unemployed(self, workers: List[Worker], params: dict) -> int:
        """
        Provide training to unemployed workers
        
        Args:
            workers: List of worker agents
            params: Dictionary with:
                - Gamma: Share of unemployed receiving training
                - tauG: Training learning rate
                - sigma: Public skill level target
        
        Returns:
            Number of workers trained
        """
        Gamma = params.get('Gamma', 0.5)
        tauG = params.get('tauG', 0.05)
        sigma = params.get('sigma', 0.5)
        
        # Find unemployed workers
        unemployed = [w for w in workers if w.read("_employed", 0) == 0]
        
        # Train a fraction of them
        num_to_train = int(len(unemployed) * Gamma)
        
        trained = 0
        for worker in unemployed[:num_to_train]:
            # Improve tenure skills toward public level
            sT_current = worker.read("_sT", 0)
            sTavg = self.read("_sTavg", 0)
            
            sT_new = sT_current + tauG * (sTavg - sT_current)
            worker.write("_sT", sT_new)
            
            trained += 1
        
        self.write("_Ltrain", trained)
        self._Ltrain = trained
        
        return trained
    
    def compute_job_openings_sector1(self, firms: List) -> int:
        """
        Compute total job openings in sector 1
        
        Args:
            firms: List of Firm1 objects
        
        Returns:
            Total job openings
        """
        total_openings = 0
        
        for firm in firms:
            L1d = firm.read("_L1d", 0)
            L1 = firm.read("_L1", 1)
            openings = max(0, L1d - L1)
            total_openings += openings
        
        return total_openings
    
    def compute_job_openings_sector2(self, firms: List) -> int:
        """
        Compute total job openings in sector 2
        
        Args:
            firms: List of Firm2 objects
        
        Returns:
            Total job openings
        """
        total_openings = 0
        
        for firm in firms:
            L2d = firm.read("_L2d", 0)
            L2 = firm.read("_L2", 1)
            openings = max(0, L2d - L2)
            total_openings += openings
        
        return total_openings
    
    def compute_wage_aggregates(self, workers: List[Worker]) -> Tuple[float, float, float]:
        """
        Compute wage-related aggregate statistics
        
        Implements equations: wAvg, wMinPol, wU
        
        Args:
            workers: List of all workers
        
        Returns:
            Tuple of (wAvg, wMinPol, wU)
        """
        # wAvg equation: Average wage of employed workers
        total_wage = 0.0
        employed_count = 0
        
        for worker in workers:
            if worker.read("_employed", 0):
                total_wage += worker.read("_w", 0)
                employed_count += 1
        
        if employed_count > 0:
            self._wAvg = total_wage / employed_count
        # else keep previous value
        
        # wMinPol equation: Policy minimum wage (indexed if enabled)
        country = self.parent
        flagIndexMinWage = getattr(country, '_flagIndexMinWage', 0)
        w0min = self._w0min
        
        if flagIndexMinWage != 0:
            # Get adjustment factors
            dCPIb_lag = country.read('_inflation', lag=1, default=0)  # Inflation
            dAb_lag = country.read('_dAb', lag=1, default=0)  # Productivity growth
            dUeB_lag = self.read('_dUeB', lag=1, default=0)  # Unemployment change
            
            # Adjust minimum wage
            adjustment = (self._psi1 * dCPIb_lag + 
                         self._psi2 * dAb_lag + 
                         self._psi3 * dUeB_lag) * flagIndexMinWage
            
            self._wMinPol *= (1 + adjustment)
        
        # Floor at absolute minimum
        self._wMinPol = max(self._wMinPol, w0min)
        
        # wU equation: Unemployment benefit
        phi = getattr(country, '_phi', 0.5)  # Benefit replacement rate
        wAvg_lag = self.read('_wAvg', lag=1, default=self._wAvg)
        self._wU = phi * wAvg_lag
        
        return self._wAvg, self._wMinPol, self._wU
    
    def compute_skills_aggregates(self, workers: List[Worker]) -> Tuple[float, float, float]:
        """
        Compute skills-related aggregate statistics
        
        Implements equation: sAvg (and related: sTavg, sTmax, sTmin, sTsd, sVavg, sVsd)
        
        Args:
            workers: List of all workers
        
        Returns:
            Tuple of (sAvg, sTavg, sVavg)
        """
        country = self.parent
        flagWorkerLBU = getattr(country, '_flagWorkerLBU', 1)
        
        if flagWorkerLBU == 0:
            # No worker-level learning
            self._sAvg = INISKILL
            self._sTavg = INISKILL
            self._sVavg = INISKILL
            self._sTmax = INISKILL
            self._sTmin = INISKILL
            self._sTsd = 0.0
            self._sVsd = 0.0
            return INISKILL, INISKILL, INISKILL
        
        # Accumulators
        sum_s = 0.0
        sum_sT = 0.0
        sum_sT_sq = 0.0
        sum_sV = 0.0
        sum_sV_sq = 0.0
        sT_max = 0.0
        sT_min = float('inf')
        count = 0
        
        for worker in workers:
            s = worker.read("_s", 0)
            sum_s += s
            count += 1
            
            if flagWorkerLBU >= 2:  # Tenure skills active
                sT = worker.read("_sT", 0)
                sum_sT += sT
                sum_sT_sq += sT ** 2
                sT_max = max(sT_max, sT)
                sT_min = min(sT_min, sT)
            
            if flagWorkerLBU == 1 or flagWorkerLBU == 3:  # Vintage skills active
                sV = worker.read("_sV", 0)
                sum_sV += sV
                sum_sV_sq += sV ** 2
        
        if count > 0:
            self._sAvg = sum_s / count
            
            if flagWorkerLBU >= 2:
                self._sTavg = sum_sT / count
                variance_sT = max((sum_sT_sq / count) - (self._sTavg ** 2), 0)
                self._sTsd = math.sqrt(variance_sT)
                self._sTmax = sT_max if sT_max > 0 else INISKILL
                self._sTmin = sT_min if sT_min < float('inf') else INISKILL
            else:
                self._sTavg = INISKILL
                self._sTsd = 0.0
                self._sTmax = INISKILL
                self._sTmin = INISKILL
            
            if flagWorkerLBU == 1 or flagWorkerLBU == 3:
                self._sVavg = sum_sV / count
                variance_sV = max((sum_sV_sq / count) - (self._sVavg ** 2), 0)
                self._sVsd = math.sqrt(variance_sV)
            else:
                self._sVavg = INISKILL
                self._sVsd = 0.0
        
        return self._sAvg, self._sTavg, self._sVavg
    
    def compute_bounded_unemployment_change(self, mLim: float, mPer: int) -> float:
        """
        Compute bounded rate of change in unemployment (dUeB equation)
        
        Uses moving average to smooth and bound the change
        
        Args:
            mLim: Limit for growth rate
            mPer: Number of periods for moving average
        
        Returns:
            Bounded unemployment rate change
        """
        # Get recent unemployment rates
        Ue_current = self._Ue
        Ue_values = [Ue_current]
        
        for lag in range(1, min(mPer, self._t) + 1):
            Ue_lag = self.read('_Ue', lag=lag, default=Ue_current)
            Ue_values.append(Ue_lag)
        
        if len(Ue_values) < 2:
            self._dUeB = 0.0
            return 0.0
        
        # Compute moving average of rate of change
        changes = []
        for i in range(len(Ue_values) - 1):
            if Ue_values[i+1] > 0:
                change = (Ue_values[i] - Ue_values[i+1]) / Ue_values[i+1]
                # Bound individual changes
                change = max(min(change, mLim), -mLim)
                changes.append(change)
        
        if changes:
            self._dUeB = sum(changes) / len(changes)
        else:
            self._dUeB = 0.0
        
        return self._dUeB


# Hook index for firm reference (placeholder)
FIRM_HOOK_IDX = 0


def create_application(worker: Worker) -> Application:
    """
    Create an application from a worker
    
    Args:
        worker: Worker object
    
    Returns:
        Application object
    """
    app = Application()
    app.wrk = worker
    app.w = worker.read("_wR", 0)      # Wage request
    app.s = worker.read("_s", 0)       # Skills
    app.ws = safe_divide(app.w, app.s, float('inf'))  # Wage-skill ratio
    app.Te = worker.read("_Te", 1)     # Employment tenure
    
    return app
