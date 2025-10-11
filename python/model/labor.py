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
