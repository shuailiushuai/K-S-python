"""
Worker Agent

Workers in the K+S model:
- Search for jobs across firms
- Accumulate skills through learning-by-doing
- Consume goods with their income
- Can be unemployed and receive benefits
"""

import numpy as np
from typing import Optional, List


class Worker:
    """
    Worker agent
    
    Workers search for jobs, work for firms, accumulate skills,
    and consume goods.
    """
    
    def __init__(self, worker_id: int, params, age: int = 1, 
                 reservation_wage: float = 1.0, contract_term: int = 1):
        """
        Initialize a worker
        
        Args:
            worker_id: Unique identifier
            params: Parameters object
            age: Initial age
            reservation_wage: Minimum acceptable wage
            contract_term: Length of work contract
        """
        self.worker_id = worker_id
        self.params = params
        self.age = age
        self.contract_term = contract_term
        
        # Employment status
        self.employed = False
        self.employer = None  # Firm object (Firm1 or Firm2)
        self.employer_sector = None  # 1 or 2
        self.tenure = 0  # Time with current employer
        self.unemployment_duration = 0
        
        # Wages and income
        self.wage = reservation_wage
        self.reservation_wage = reservation_wage
        self.wage_history = [reservation_wage] * 8  # Last 8 periods
        self.income = 0.0
        self.bonus = 0.0
        self.unemployment_benefit = 0.0
        
        # Skills
        self.skills_vintage = 1.0  # Learning-by-using vintage
        self.skills_tenure = 1.0  # Learning-by-doing tenure
        self.skills_total = 1.0  # Combined skills
        
        # Consumption
        self.consumption_desired = 0.0
        self.consumption_actual = 0.0
        self.savings = 0.0
        self.forced_savings = 0.0  # Unspent consumption
        
        # Job search
        self.applications = []  # List of firms applied to
        self.offers = []  # List of job offers received
        self.search_prob = 1.0  # Probability of searching
        
        # Training
        self.in_training = False
    
    def update_age(self, t: int):
        """Update worker age and check retirement"""
        self.age += 1
        
        Tr = self.params.get('Tr', 0)  # Retirement age
        if Tr > 0 and self.age > Tr:
            # Worker retires (to be replaced by new worker)
            return True  # Should retire
        
        return False
    
    def update_skills(self, t: int):
        """
        Update worker skills based on employment and learning
        """
        flagWorkerLBU = self.params.get('flagWorkerLBU', 0)
        flagWorkerSkProd = self.params.get('flagWorkerSkProd', 0)
        
        if self.employed:
            # Learning-by-doing for employed workers
            tauT = self.params.get('tauT', 0.01)  # Tenure learning rate
            sigma = self.params.get('sigma', 0.5)  # Public vintage skills
            
            # Tenure skills increase with experience
            if flagWorkerLBU in [2, 3]:  # Tenure skills active
                self.skills_tenure *= (1 + tauT)
            
            # Vintage skills depend on machine vintage used
            if flagWorkerLBU in [1, 3]:  # Vintage skills active
                if self.employer and hasattr(self.employer, 'vintages'):
                    # Get average vintage productivity
                    if len(self.employer.vintages) > 0:
                        avg_vintage_prod = sum(v.productivity for v in self.employer.vintages) / len(self.employer.vintages)
                        self.skills_vintage = sigma + (1 - sigma) * avg_vintage_prod
            
            self.tenure += 1
        
        else:
            # Skills deterioration for unemployed
            tauU = self.params.get('tauU', 0.01)  # Skills decay rate
            
            if not self.in_training:
                # Skills deteriorate
                self.skills_tenure *= (1 - tauU)
                self.skills_vintage *= (1 - tauU)
            else:
                # Training preserves or improves skills
                tauG = self.params.get('tauG', 0.005)
                self.skills_tenure *= (1 + tauG)
            
            self.unemployment_duration += 1
        
        # Calculate total skills based on mode
        if flagWorkerSkProd == 0:
            self.skills_total = 1.0  # Skills don't affect productivity
        elif flagWorkerSkProd == 1:
            self.skills_total = self.skills_vintage
        elif flagWorkerSkProd == 2:
            self.skills_total = self.skills_tenure
        else:  # flagWorkerSkProd == 3
            self.skills_total = (self.skills_vintage + self.skills_tenure) / 2
    
    def apply_for_jobs(self, t: int, labor_market):
        """
        Submit job applications to firms
        """
        self.applications = []
        
        # Check if worker searches for job
        if not self._should_search(t):
            return
        
        # Determine number of applications
        if self.employed:
            omega = self.params.get('omega', 1.0)
        else:
            omega = self.params.get('omegaU', 3.0)
        
        # Account for search discouragement
        omega = omega * self.search_prob
        
        # Draw actual number of applications
        n_applications = max(1, int(np.random.poisson(omega)))
        
        # Submit applications through labor market
        firms = labor_market.select_firms_for_application(self, n_applications)
        
        for firm in firms:
            labor_market.submit_application(self, firm)
            self.applications.append(firm)
    
    def _should_search(self, t: int) -> bool:
        """
        Determine if worker should search for jobs
        """
        flagSearchMode = self.params.get('flagSearchMode', 0)
        
        if flagSearchMode == 0:
            # Always search
            return True
        elif flagSearchMode == 1:
            # Search only if unemployed
            return not self.employed
        elif flagSearchMode == 2:
            # Search if unemployed or wage below average
            if not self.employed:
                return True
            # Compare to average wage
            wAvg = self.params.get('wAvg', 1.0)  # Will be updated by labor market
            return self.wage < wAvg
        
        return True
    
    def receive_job_offer(self, firm, wage_offer: float):
        """
        Receive a job offer from a firm
        """
        self.offers.append({
            'firm': firm,
            'wage': wage_offer,
            'sector': 1 if hasattr(firm, 'machine_productivity') else 2
        })
    
    def select_best_offer(self):
        """
        Select best job offer (highest wage)
        """
        if not self.offers:
            return None
        
        # Select offer with highest wage
        best_offer = max(self.offers, key=lambda x: x['wage'])
        
        # Check if better than current job
        epsilon = self.params.get('epsilon', 0.01)  # Minimum wage increment
        
        if self.employed:
            # Only switch if wage significantly better
            if best_offer['wage'] > self.wage * (1 + epsilon):
                return best_offer
            else:
                return None
        else:
            # Unemployed: accept if above reservation wage
            if best_offer['wage'] >= self.reservation_wage:
                return best_offer
        
        return None
    
    def accept_job(self, offer: dict):
        """
        Accept a job offer
        """
        # Quit current job if employed
        if self.employed and self.employer:
            self.employer.workers.remove(self)
        
        # Accept new job
        self.employer = offer['firm']
        self.employer_sector = offer['sector']
        self.wage = offer['wage']
        self.employed = True
        self.tenure = 0
        self.unemployment_duration = 0
        
        # Add to firm's worker list
        self.employer.workers.append(self)
        
        # Reset offers
        self.offers = []
    
    def update_reservation_wage(self, t: int):
        """
        Update reservation wage based on wage history
        """
        Ts = self.params.get('Ts', 4)  # Wage memory periods
        
        if Ts == 0 or len(self.wage_history) == 0:
            # No memory
            return
        
        # Average of recent wages
        recent_wages = self.wage_history[-Ts:]
        self.reservation_wage = np.mean([w for w in recent_wages if w > 0])
    
    def determine_consumption(self, t: int):
        """
        Determine desired consumption based on income
        """
        # Calculate total income
        if self.employed:
            self.income = self.wage + self.bonus
            self.unemployment_benefit = 0.0
        else:
            # Receive unemployment benefit
            phi = self.params.get('phi', 0.5)  # Benefit ratio
            wAvg = self.params.get('wAvg', 1.0)
            self.unemployment_benefit = phi * wAvg
            self.income = self.unemployment_benefit
        
        # Handle forced savings based on flagCons
        flagCons = self.params.get('flagCons', 0)
        
        if flagCons == 0:
            # Ignore unfilled past demand - consume only current income
            self.consumption_desired = self.income
        elif flagCons == 1:
            # Spend all accumulated savings at once
            self.consumption_desired = self.income + self.forced_savings
        elif flagCons == 2:
            # Recover past consumption with limit
            Crec = self.params.get('Crec', 0.5)  # Max recovery rate
            recovery = min(self.forced_savings, Crec * self.income)
            self.consumption_desired = self.income + recovery
        else:
            # Default: ignore past savings
            self.consumption_desired = self.income
        
        # Reset bonus
        self.bonus = 0.0
    
    def consume(self, consumption_actual: float):
        """
        Record actual consumption (after goods market clearing)
        """
        self.consumption_actual = consumption_actual
        
        # Update forced savings (unspent income)
        if consumption_actual < self.consumption_desired:
            self.forced_savings += (self.consumption_desired - consumption_actual)
        else:
            self.forced_savings = 0.0
        
        # Update savings
        self.savings = self.forced_savings
    
    def update_wage_history(self):
        """
        Update wage history for reservation wage calculation
        """
        self.wage_history.append(self.wage)
        if len(self.wage_history) > 8:
            self.wage_history.pop(0)
    
    def receive_training(self):
        """
        Receive government-provided training
        """
        self.in_training = True
    
    def __repr__(self):
        status = "employed" if self.employed else "unemployed"
        return (f"Worker(id={self.worker_id}, {status}, "
                f"w={self.wage:.2f}, s={self.skills_total:.2f})")
