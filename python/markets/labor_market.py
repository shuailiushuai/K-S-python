"""
Labor Market

Implements decentralized job search and matching between workers and firms.
- Workers submit applications to multiple firms
- Firms post vacancies and make wage offers
- Matching occurs based on preferences (wages, skills)
- No market clearing guaranteed
"""

import numpy as np
from typing import List, Dict
from collections import defaultdict


class LaborMarket:
    """
    Labor market with decentralized search-and-match
    """
    
    def __init__(self, params, workers: List, firms1: List, firms2: List):
        """
        Initialize labor market
        
        Args:
            params: Parameters object
            workers: List of Worker objects
            firms1: List of Firm1 objects
            firms2: List of Firm2 objects
        """
        self.params = params
        self.workers = workers
        self.firms1 = firms1
        self.firms2 = firms2
        
        # Application queues for each firm
        self.applications_firm1 = defaultdict(list)  # firm -> list of applications
        self.applications_firm2 = defaultdict(list)
        
        # Wage offers from firms
        self.wage_offers = []  # List of (firm, wage, n_workers) tuples
        
        # Statistics
        self.total_applications = 0
        self.vacancies_firm1 = 0
        self.vacancies_firm2 = 0
        self.matches = 0
    
    def select_firms_for_application(self, worker, n_applications: int) -> List:
        """
        Select firms for worker to apply to
        
        Workers have higher probability of applying to larger firms.
        
        Args:
            worker: Worker object
            n_applications: Number of applications to make
            
        Returns:
            List of selected firms
        """
        all_firms = self.firms1 + self.firms2
        
        if len(all_firms) == 0:
            return []
        
        # Probability proportional to firm size (number of workers)
        firm_sizes = np.array([len(f.workers) + 1 for f in all_firms])  # +1 to avoid zero
        probabilities = firm_sizes / firm_sizes.sum()
        
        # Sample firms without replacement
        n_select = min(n_applications, len(all_firms))
        selected_indices = np.random.choice(
            len(all_firms), 
            size=n_select, 
            replace=False,
            p=probabilities
        )
        
        return [all_firms[i] for i in selected_indices]
    
    def submit_application(self, worker, firm):
        """
        Worker submits application to firm
        """
        application = {
            'worker': worker,
            'wage_requested': worker.reservation_wage,
            'skills': worker.skills_total,
            'tenure': worker.tenure
        }
        
        # Add to appropriate queue
        if firm in self.firms1:
            self.applications_firm1[firm].append(application)
        else:
            self.applications_firm2[firm].append(application)
        
        self.total_applications += 1
    
    def firms_post_vacancies(self, t: int):
        """
        Firms determine vacancies and prepare wage offers
        """
        self.vacancies_firm1 = 0
        self.vacancies_firm2 = 0
        self.wage_offers = []
        
        # Firm1 vacancies
        for firm in self.firms1:
            vacancies = max(0, firm.labor_demand - len(firm.workers))
            
            if vacancies > 0:
                self.vacancies_firm1 += vacancies
                
                # Determine wage offer
                wage_offer = self._determine_wage_offer(firm, t, sector=1)
                
                self.wage_offers.append({
                    'firm': firm,
                    'wage': wage_offer,
                    'vacancies': vacancies,
                    'sector': 1
                })
        
        # Firm2 vacancies
        for firm in self.firms2:
            vacancies = max(0, firm.labor_demand - len(firm.workers))
            
            if vacancies > 0:
                self.vacancies_firm2 += vacancies
                
                wage_offer = self._determine_wage_offer(firm, t, sector=2)
                
                self.wage_offers.append({
                    'firm': firm,
                    'wage': wage_offer,
                    'vacancies': vacancies,
                    'sector': 2
                })
    
    def _determine_wage_offer(self, firm, t: int, sector: int) -> float:
        """
        Firm determines wage offer based on applications received
        """
        flagWageOffer = self.params.get('flagWageOffer', 0)
        flagWagePremium = self.params.get('flagWagePremium', 1)
        
        # Get applications for this firm
        if sector == 1:
            applications = self.applications_firm1.get(firm, [])
        else:
            applications = self.applications_firm2.get(firm, [])
        
        # Base wage (current average wage in firm)
        if len(firm.workers) > 0:
            base_wage = np.mean([w.wage for w in firm.workers])
        else:
            base_wage = self.params.get('w0min', 1.0)
        
        # Calculate wage offer
        if flagWageOffer == 0:
            # Don't consider requested wages, use premium
            wage_offer = self._apply_wage_premium(base_wage, firm, sector, flagWagePremium)
        
        else:  # flagWageOffer == 1
            # Consider requested wages from applications
            if applications:
                requested_wages = [app['wage_requested'] for app in applications]
                min_requested = min(requested_wages)
                
                # Offer lowest acceptable wage (but at least base wage)
                wage_offer = max(min_requested, base_wage)
            else:
                # No applications, offer premium
                wage_offer = self._apply_wage_premium(base_wage, firm, sector, flagWagePremium)
        
        # Apply wage cap
        wCap = self.params.get('wCap', 0.0)
        if wCap > 0:
            wage_offer = min(wage_offer, base_wage * (1 + wCap))
        
        return wage_offer
    
    def _apply_wage_premium(self, base_wage: float, firm, sector: int, 
                           flag_premium: int) -> float:
        """
        Apply wage premium/indexation mechanism
        """
        if flag_premium == 0:
            # No premium
            return base_wage
        
        elif flag_premium == 1:
            # Wage indexation (WP1)
            return self._wage_indexation(base_wage, firm, sector)
        
        else:  # flag_premium == 2
            # Endogenous premium (WP2)
            return self._wage_endogenous(base_wage, firm, sector)
    
    def _wage_indexation(self, base_wage: float, firm, sector: int) -> float:
        """
        Wage indexation mechanism
        """
        psi1 = self.params.get('psi1', 0.5)  # Inflation pass-through
        psi2 = self.params.get('psi2', 0.5)  # Productivity elasticity
        psi3 = self.params.get('psi3', 0.0)  # Unemployment elasticity
        psi4 = self.params.get('psi4', 0.0)  # Firm productivity elasticity
        psi5 = self.params.get('psi5', 0.0)  # Vacancy elasticity
        
        # Get macroeconomic variables (from params, updated by model)
        inflation = self.params.get('inflation', 0.02)
        productivity_growth = self.params.get('productivity_growth', 0.01)
        unemployment_rate = self.params.get('unemployment_rate', 0.05)
        
        # Calculate wage adjustment
        wage_adjustment = (psi1 * inflation + 
                          psi2 * productivity_growth -
                          psi3 * unemployment_rate)
        
        return base_wage * (1 + wage_adjustment)
    
    def _wage_endogenous(self, base_wage: float, firm, sector: int) -> float:
        """
        Endogenous wage premium based on firm conditions
        """
        # Simplified: offer premium if firm is profitable
        if firm.profit > 0:
            premium = 0.05  # 5% premium
            return base_wage * (1 + premium)
        else:
            return base_wage
    
    def match_workers_to_jobs(self, t: int):
        """
        Match workers to jobs through decentralized process
        """
        self.matches = 0
        
        # Order wage offers (can be randomized or by wage level)
        flagHireSeq = self.params.get('flagHireSeq', 0)
        ordered_offers = self._order_wage_offers(self.wage_offers, flagHireSeq)
        
        # Process each firm's hiring
        for offer in ordered_offers:
            firm = offer['firm']
            wage = offer['wage']
            vacancies = int(offer['vacancies'])
            sector = offer['sector']
            
            # Get and order applications for this firm
            if sector == 1:
                applications = self.applications_firm1.get(firm, [])
                flagHireOrder = self.params.get('flagHireOrder1', 0)
            else:
                applications = self.applications_firm2.get(firm, [])
                flagHireOrder = self.params.get('flagHireOrder2', 0)
            
            # Order applications
            ordered_apps = self._order_applications(applications, flagHireOrder)
            
            # Make offers to workers in order
            hired = 0
            for app in ordered_apps:
                if hired >= vacancies:
                    break
                
                worker = app['worker']
                
                # Worker receives offer
                worker.receive_job_offer(firm, wage)
                hired += 1
        
        # Workers select best offer
        for worker in self.workers:
            best_offer = worker.select_best_offer()
            
            if best_offer is not None:
                worker.accept_job(best_offer)
                self.matches += 1
        
        # Update firm actual labor
        for firm in self.firms1 + self.firms2:
            firm.labor_actual = len(firm.workers)
            if firm.labor_actual > 0:
                firm.avg_wage = np.mean([w.wage for w in firm.workers])
                firm.wage_bill = sum(w.wage for w in firm.workers)
            else:
                firm.wage_bill = 0.0
        
        # Clear application queues
        self.applications_firm1.clear()
        self.applications_firm2.clear()
    
    def _order_wage_offers(self, offers: List[Dict], flag_hire_seq: int) -> List[Dict]:
        """
        Order wage offers for hiring sequence
        """
        if flag_hire_seq == 0:
            # Random order
            offers_copy = offers.copy()
            np.random.shuffle(offers_copy)
            return offers_copy
        
        elif flag_hire_seq == 1:
            # Higher wages first
            return sorted(offers, key=lambda x: x['wage'], reverse=True)
        
        elif flag_hire_seq == 2:
            # Firms without workers first, then random
            with_workers = [o for o in offers if len(o['firm'].workers) > 0]
            without_workers = [o for o in offers if len(o['firm'].workers) == 0]
            np.random.shuffle(with_workers)
            return without_workers + with_workers
        
        else:  # flag_hire_seq == 3
            # Firms without workers first, then higher wages
            with_workers = sorted([o for o in offers if len(o['firm'].workers) > 0],
                                key=lambda x: x['wage'], reverse=True)
            without_workers = sorted([o for o in offers if len(o['firm'].workers) == 0],
                                   key=lambda x: x['wage'], reverse=True)
            return without_workers + with_workers
    
    def _order_applications(self, applications: List[Dict], flag_hire_order: int) -> List[Dict]:
        """
        Order applications for hiring decisions
        """
        if len(applications) == 0:
            return []
        
        if flag_hire_order == 0:
            # Random order
            apps_copy = applications.copy()
            np.random.shuffle(apps_copy)
            return apps_copy
        
        elif flag_hire_order == 1:
            # Higher wage requests first
            return sorted(applications, key=lambda x: x['wage_requested'], reverse=True)
        
        elif flag_hire_order == 2:
            # Lower wage requests first
            return sorted(applications, key=lambda x: x['wage_requested'])
        
        elif flag_hire_order == 3:
            # Higher skills first
            return sorted(applications, key=lambda x: x['skills'], reverse=True)
        
        elif flag_hire_order == 4:
            # Lower skills first
            return sorted(applications, key=lambda x: x['skills'])
        
        elif flag_hire_order == 5:
            # Higher payback (wage/skills) first
            return sorted(applications, 
                        key=lambda x: x['wage_requested']/x['skills'] if x['skills'] > 0 else np.inf,
                        reverse=True)
        
        elif flag_hire_order == 6:
            # Lower payback first
            return sorted(applications,
                        key=lambda x: x['wage_requested']/x['skills'] if x['skills'] > 0 else np.inf)
        
        elif flag_hire_order == 7:
            # Old hires (higher tenure) first
            return sorted(applications, key=lambda x: x['tenure'], reverse=True)
        
        else:  # flag_hire_order == 8
            # Recent hires (lower tenure) first
            return sorted(applications, key=lambda x: x['tenure'])
    
    def handle_firing(self, t: int):
        """
        Handle firing decisions by firms
        """
        # Firm2 firing based on rules
        for firm in self.firms2:
            self._firm2_firing(firm, t)
        
        # Firm1 firing (simplified)
        for firm in self.firms1:
            self._firm1_firing(firm, t)
    
    def _firm2_firing(self, firm, t: int):
        """
        Handle Firm2 firing based on flagFireRule
        
        The firing logic should be more conservative to avoid excessive unemployment.
        """
        flagFireRule = self.params.get('flagFireRule', 4)
        theta = self.params.get('theta', 0.0)  # Hiring slack
        
        if flagFireRule == 0:
            # Never fire (except retirement)
            return
        
        elif flagFireRule == 1:
            # Work sharing (reduce hours, no firing)
            return
        
        elif flagFireRule == 2:
            # Fire only if downsizing significantly
            if firm.labor_demand < len(firm.workers) * 0.8:
                n_fire = len(firm.workers) - int(firm.labor_demand * (1 + theta))
                self._fire_workers(firm, max(0, n_fire), 2)
        
        elif flagFireRule == 3:
            # Fire if losses
            if firm.profit < 0:
                n_fire = max(1, int(0.1 * len(firm.workers)))  # Fire 10%
                self._fire_workers(firm, n_fire, 2)
        
        elif flagFireRule == 4:
            # Fire to match labor demand with slack (theta)
            # This is the standard firing rule from the C++ model
            if len(firm.workers) > 0:
                # Allow slack in hiring: firms keep theta % extra workers
                target_workers = firm.labor_demand * (1 + theta)
                if len(firm.workers) > target_workers:
                    # Fire excess workers beyond the slack
                    n_fire = int(len(firm.workers) - target_workers)
                    self._fire_workers(firm, max(0, n_fire), 2)
        
        else:  # flagFireRule == 5
            # Fire when contract ends
            Tc = self.params.get('Tc', 1)
            workers_to_fire = [w for w in firm.workers if w.tenure >= Tc]
            if workers_to_fire:
                for worker in workers_to_fire:
                    worker.employed = False
                    worker.employer = None
                    worker.tenure = 0
                    firm.workers.remove(worker)
    
    def _firm1_firing(self, firm, t: int):
        """
        Handle Firm1 firing with slack parameter
        """
        theta = self.params.get('theta', 0.0)  # Hiring slack
        
        # Fire only if current workers exceed demand + slack
        if len(firm.workers) > 0:
            target_workers = firm.labor_demand * (1 + theta)
            if len(firm.workers) > target_workers:
                n_fire = int(len(firm.workers) - target_workers)
                self._fire_workers(firm, max(0, n_fire), 1)
    
    def _fire_workers(self, firm, n_fire: int, sector: int):
        """
        Fire workers from firm based on firing order
        """
        if n_fire <= 0 or len(firm.workers) == 0:
            return
        
        # Get firing order flag
        if sector == 1:
            flagFireOrder = self.params.get('flagFireOrder1', 0)
        else:
            flagFireOrder = self.params.get('flagFireOrder2', 0)
        
        # Order workers for firing
        workers_ordered = self._order_workers_for_firing(firm.workers, flagFireOrder)
        
        # Fire first n_fire workers
        n_fire = min(n_fire, len(workers_ordered))
        for i in range(n_fire):
            worker = workers_ordered[i]
            worker.employed = False
            worker.employer = None
            worker.tenure = 0
            firm.workers.remove(worker)
    
    def _order_workers_for_firing(self, workers: List, flag_fire_order: int) -> List:
        """
        Order workers for firing decisions (same logic as hiring order)
        """
        if flag_fire_order == 0:
            # Random
            workers_copy = workers.copy()
            np.random.shuffle(workers_copy)
            return workers_copy
        
        elif flag_fire_order == 1:
            # Higher wage first
            return sorted(workers, key=lambda w: w.wage, reverse=True)
        
        elif flag_fire_order == 2:
            # Lower wage first
            return sorted(workers, key=lambda w: w.wage)
        
        elif flag_fire_order == 3:
            # Higher skills first
            return sorted(workers, key=lambda w: w.skills_total, reverse=True)
        
        elif flag_fire_order == 4:
            # Lower skills first
            return sorted(workers, key=lambda w: w.skills_total)
        
        elif flag_fire_order == 7:
            # Old hires first
            return sorted(workers, key=lambda w: w.tenure, reverse=True)
        
        else:  # flag_fire_order == 8
            # Recent hires first
            return sorted(workers, key=lambda w: w.tenure)
