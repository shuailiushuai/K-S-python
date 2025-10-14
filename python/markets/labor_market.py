"""
Labor Market Module
Implements job search, matching, hiring, and firing mechanisms
"""

from typing import List, Dict, Any, Tuple
import math
from utils.data_structures import WageOffer, Application
from utils.core_utils import get_random_engine


class LaborMarket:
    """
    Labor market coordination for the K+S model
    Manages job applications, wage offers, and worker-firm matching
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.applications_sector1: List[Application] = []
        self.wage_offers_sector2: List[WageOffer] = []
        
    def worker_applications(self, workers: List, firms1: List, firms2: List, 
                           country_ext) -> int:
        """
        Workers post applications to firms based on search strategy
        Returns total number of applications
        
        From fun_KS_labor.h: appl equation
        """
        Lscale = self.config.get('Labor.Lscale', 1)
        search_prob = self._compute_search_probability(workers)
        
        # Clear previous applications
        self.applications_sector1.clear()
        self.wage_offers_sector2.clear()
        for firm in firms2:
            if hasattr(firm, 'applications'):
                firm.applications.clear()
            else:
                firm.applications = []
        
        total_applications = 0
        
        for worker in workers:
            worker._appl = 0  # Reset application flag
            
            # Check if worker should search
            if not self._should_search(worker, search_prob):
                continue
            
            # Determine search mode
            flag_search_mode = self._get_flag_search_mode(worker)
            search_mode = self.config.get(f'Country.flagSearchMode{"Chg" if flag_search_mode else ""}', 1)
            
            if search_mode == 0:
                # Apply to random firms
                self._apply_random(worker, firms1, firms2)
            elif search_mode == 1:
                # Apply to firms offering best wages
                self._apply_best_wage(worker, firms1, firms2, country_ext)
            elif search_mode == 2:
                # Apply to firms with most workers
                self._apply_most_workers(worker, firms1, firms2)
            else:
                # Apply to best wage/worker ratio
                self._apply_best_ratio(worker, firms1, firms2, country_ext)
            
            worker._appl = 1
            total_applications += 1
        
        return total_applications * Lscale
    
    def _compute_search_probability(self, workers: List) -> float:
        """
        Compute global search probability with discouragement
        From fun_KS_labor.h: searchProb equation
        """
        flag_disc = self.config.get('Country.flagSearchDisc', 0)
        
        if flag_disc == 1:
            kappa = self.config.get('Labor.kappa', 1.0)
            # Compute unemployment rate
            unemployed = sum(1 for w in workers if w._employed == 0)
            Ue = unemployed / len(workers) if workers else 0.0
            
            # Global discouragement function
            prob = kappa * math.exp(-kappa * Ue)
            return prob
        else:
            return 1.0  # Always search
    
    def _should_search(self, worker, global_prob: float) -> bool:
        """Check if worker should search for a job"""
        # Employed workers don't search (unless enabled)
        if worker._employed > 0:
            return False
        
        # Apply global search probability
        if get_random_engine().uniform() > global_prob:
            return False
        
        # Individual discouragement based on unemployment duration
        Tu = worker._Tu
        kappa = self.config.get('Labor.kappa', 1.0)
        individual_prob = math.exp(-kappa * Tu / 10.0)  # Simplified
        
        return get_random_engine().uniform() < individual_prob
    
    def _get_flag_search_mode(self, worker) -> bool:
        """Determine if post-change search mode applies to worker"""
        if not hasattr(worker, '_postChg'):
            return False
        return worker._postChg
    
    def _apply_random(self, worker, firms1: List, firms2: List):
        """Apply to random subset of firms"""
        n1 = self.config.get('Capital.n1', 4)
        n2 = self.config.get('Consumption.n2', 1)
        
        # Apply to random firms in sector 1
        if len(firms1) > 0:
            num_apps = min(n1, len(firms1))
            selected_firms = get_random_engine().sample(firms1, num_apps)
            for firm in selected_firms:
                app = Application(
                    w=worker._wRes,  # Reservation wage
                    s=worker._s,     # Skills
                    ws=worker._s * worker._wRes,  # Combined metric
                    Te=worker._Te,
                    wrk=worker
                )
                self.applications_sector1.append(app)
        
        # Apply to random firms in sector 2
        if len(firms2) > 0:
            num_apps = min(n2, len(firms2))
            selected_firms = get_random_engine().sample(firms2, num_apps)
            for firm in selected_firms:
                app = Application(
                    w=worker._wRes,
                    s=worker._s,
                    ws=worker._s * worker._wRes,
                    Te=worker._Te,
                    wrk=worker
                )
                firm.applications.append(app)
    
    def _apply_best_wage(self, worker, firms1: List, firms2: List, country_ext):
        """Apply to firms offering best wages"""
        n1 = self.config.get('Capital.n1', 4)
        n2 = self.config.get('Consumption.n2', 1)
        
        # Sample and select best wage offers in sector 1
        if len(firms1) > 0:
            sample_size = min(n1 * 3, len(firms1))  # Sample more, select best
            sampled = get_random_engine().sample(firms1, sample_size)
            # Sort by wage offer
            sampled.sort(key=lambda f: f._w1o if hasattr(f, '_w1o') else 0, reverse=True)
            selected = sampled[:n1]
            
            for firm in selected:
                app = Application(
                    w=worker._wRes,
                    s=worker._s,
                    ws=worker._s * worker._wRes,
                    Te=worker._Te,
                    wrk=worker
                )
                self.applications_sector1.append(app)
        
        # Sector 2: use wage offer list from country extension
        if len(self.wage_offers_sector2) > 0:
            # Sort by wage offer (already sorted in creation)
            selected = self.wage_offers_sector2[:min(n2, len(self.wage_offers_sector2))]
            for offer in selected:
                app = Application(
                    w=worker._wRes,
                    s=worker._s,
                    ws=worker._s * worker._wRes,
                    Te=worker._Te,
                    wrk=worker
                )
                offer.firm.applications.append(app)
    
    def _apply_most_workers(self, worker, firms1: List, firms2: List):
        """Apply to firms with most workers"""
        n1 = self.config.get('Capital.n1', 4)
        n2 = self.config.get('Consumption.n2', 1)
        
        # Sort firms by number of workers
        if len(firms1) > 0:
            sorted_firms = sorted(firms1, key=lambda f: f._L1 if hasattr(f, '_L1') else 0, reverse=True)
            selected = sorted_firms[:n1]
            for firm in selected:
                app = Application(
                    w=worker._wRes,
                    s=worker._s,
                    ws=worker._s * worker._wRes,
                    Te=worker._Te,
                    wrk=worker
                )
                self.applications_sector1.append(app)
        
        if len(firms2) > 0:
            sorted_firms = sorted(firms2, key=lambda f: f._L2 if hasattr(f, '_L2') else 0, reverse=True)
            selected = sorted_firms[:n2]
            for firm in selected:
                app = Application(
                    w=worker._wRes,
                    s=worker._s,
                    ws=worker._s * worker._wRes,
                    Te=worker._Te,
                    wrk=worker
                )
                firm.applications.append(app)
    
    def _apply_best_ratio(self, worker, firms1: List, firms2: List, country_ext):
        """Apply to firms with best wage/worker ratio"""
        n1 = self.config.get('Capital.n1', 4)
        n2 = self.config.get('Consumption.n2', 1)
        
        # Compute ratio: wage / (workers + 1)
        if len(firms1) > 0:
            firms_with_ratio = []
            for firm in firms1:
                wage = firm._w1o if hasattr(firm, '_w1o') else 1.0
                workers = firm._L1 if hasattr(firm, '_L1') else 1
                ratio = wage / max(workers + 1, 1)
                firms_with_ratio.append((ratio, firm))
            
            firms_with_ratio.sort(reverse=True)
            selected = [f[1] for f in firms_with_ratio[:n1]]
            
            for firm in selected:
                app = Application(
                    w=worker._wRes,
                    s=worker._s,
                    ws=worker._s * worker._wRes,
                    Te=worker._Te,
                    wrk=worker
                )
                self.applications_sector1.append(app)
        
        # Similar for sector 2
        if len(firms2) > 0:
            firms_with_ratio = []
            for firm in firms2:
                wage = firm._w2o if hasattr(firm, '_w2o') else 1.0
                workers = firm._L2 if hasattr(firm, '_L2') else 1
                ratio = wage / max(workers + 1, 1)
                firms_with_ratio.append((ratio, firm))
            
            firms_with_ratio.sort(reverse=True)
            selected = [f[1] for f in firms_with_ratio[:n2]]
            
            for firm in selected:
                app = Application(
                    w=worker._wRes,
                    s=worker._s,
                    ws=worker._s * worker._wRes,
                    Te=worker._Te,
                    wrk=worker
                )
                firm.applications.append(app)
    
    def compute_job_openings_sector1(self, firms1: List, total_labor: int, 
                                     L2d: float) -> float:
        """
        Compute open job positions in sector 1
        From fun_KS_capital.h: JO1 equation
        """
        Lscale = self.config.get('Labor.Lscale', 1)
        L1shortMax = self.config.get('Capital.L1shortMax', 1.0)
        
        # Sum up R&D and production labor demand
        L1dRD = sum(f._L1rd for f in firms1 if hasattr(f, '_L1rd'))
        L1d = sum(f._L1d for f in firms1 if hasattr(f, '_L1d'))
        
        # Limit demands to available labor
        L1dRD = min(L1dRD, total_labor)
        L1d = min(L1d, total_labor)
        
        # Production labor after R&D
        L1d_prod = L1d - L1dRD
        
        # Handle shortage proportionally
        if (L1d_prod + L2d) > (total_labor - L1dRD):
            L1d_prod *= max((total_labor - L1dRD) / (L1d_prod + L2d), 1 - L1shortMax)
        
        # Current workers in sector 1
        current_workers = sum(1 for f in firms1 for _ in range(int(getattr(f, '_L1', 0))))
        
        # Open positions (scaled and rounded up)
        JO1 = max(math.ceil(L1dRD + L1d_prod - current_workers), 0)
        
        return JO1
    
    def compute_job_openings_sector2(self, firms2: List) -> float:
        """
        Compute open job positions in sector 2
        Each firm computes its own _JO2
        """
        total_JO2 = 0
        for firm in firms2:
            if hasattr(firm, '_JO2'):
                total_JO2 += firm._JO2
        return total_JO2
    
    def create_wage_offers_sector2(self, firms2: List, country_ext):
        """
        Create and sort wage offer list for sector 2
        From fun_KS_consumption.h: used in hires2
        """
        self.wage_offers_sector2.clear()
        
        for firm in firms2:
            if not hasattr(firm, '_JO2') or firm._JO2 <= 0:
                continue
            
            offer = WageOffer(
                offer=firm._w2o if hasattr(firm, '_w2o') else 1.0,
                workers=int(firm._L2) if hasattr(firm, '_L2') else 0,
                firm=firm
            )
            self.wage_offers_sector2.append(offer)
        
        # Store in country extension
        country_ext.firm2wo = self.wage_offers_sector2
    
    def hire_workers_sector1(self, firms1: List) -> int:
        """
        Process hiring in capital-good sector
        From fun_KS_capital.h: hires1 equation (simplified, full version in C++)
        """
        Lscale = self.config.get('Labor.Lscale', 1)
        flag_hire_order = self.config.get('Country.flagHireOrder1', 0)
        
        # Sort applications based on hiring strategy
        self._sort_applications(self.applications_sector1, flag_hire_order)
        
        # Distribute applications to firms (simplified - in full version, 
        # applications go directly to firms)
        total_hired = 0
        
        for firm in firms1:
            if not hasattr(firm, '_JO1') or firm._JO1 <= 0:
                continue
            
            firm._hires1 = 0
            positions = math.ceil(firm._JO1 / Lscale)
            
            # Find applications for this firm
            firm_applications = [app for app in self.applications_sector1 
                               if app.wrk._employed == 0]
            
            hired = 0
            for app in firm_applications[:positions]:
                if self._hire_worker(app.wrk, 1, firm, firm._w1o):
                    hired += 1
                if hired >= positions:
                    break
            
            firm._hires1 = hired * Lscale
            total_hired += hired
        
        return total_hired * Lscale
    
    def hire_workers_sector2(self, firms2: List, country_ext) -> int:
        """
        Process hiring in consumption-good sector
        From fun_KS_consumption.h: hires2 equation
        """
        Lscale = self.config.get('Labor.Lscale', 1)
        flag_heter_wage = self.config.get('Country.flagHeterWage', 0)
        
        # Sort wage offers
        flag_hire_seq = self.config.get('Country.flagHireSeq', 0) if flag_heter_wage else 0
        self._order_offers(flag_hire_seq, self.wage_offers_sector2)
        
        total_hired = 0
        
        for offer in self.wage_offers_sector2:
            firm = offer.firm
            applications = firm.applications if hasattr(firm, 'applications') else []
            
            # Sort firm's applications
            flag_hire_order = self.config.get('Country.flagHireOrder2', 0)
            self._sort_applications(applications, flag_hire_order)
            
            # Hire from ordered applications
            positions = math.ceil(firm._JO2 / Lscale)
            hired = 0
            min_wage_worker = None
            min_wage = float('inf')
            
            for app in applications:
                if positions - hired <= 0:
                    break
                
                # Check if not already hired and wage acceptable
                if not (app.wrk._employed > 0 and app.wrk._Te == 0):
                    if app.w <= offer.offer * 1.01:  # Small tolerance
                        if self._hire_worker(app.wrk, 2, firm, offer.offer):
                            hired += 1
                    elif app.w < min_wage:
                        min_wage = app.w
                        min_wage_worker = app.wrk
            
            # Try to hire at least one worker at any wage
            if positions - hired > 0 and hired == 0 and min_wage_worker:
                if self._hire_worker(min_wage_worker, 2, firm, min_wage):
                    hired += 1
            
            firm._hires2 = hired * Lscale
            total_hired += hired
            
            # Clear applications
            firm.applications.clear()
        
        return total_hired * Lscale
    
    def _hire_worker(self, worker, sector: int, firm, wage: float) -> bool:
        """
        Hire a worker to a firm
        Updates worker status and firm worker list
        """
        worker._employed = sector
        worker._w = wage
        worker._Te = 0  # Reset tenure
        
        # Add to firm's worker list (simplified)
        if sector == 1:
            if not hasattr(firm, 'workers'):
                firm.workers = []
            firm.workers.append(worker)
            worker.employer = firm
        else:  # sector == 2
            if not hasattr(firm, 'workers'):
                firm.workers = []
            firm.workers.append(worker)
            worker.employer = firm
        
        return True
    
    def _sort_applications(self, applications: List[Application], order_mode: int):
        """
        Sort applications according to hiring strategy
        0: random, 1: best skills, 2: lowest wage, 3: best skills/wage ratio
        """
        if order_mode == 0:
            # Random order
            get_random_engine().shuffle(applications)
        elif order_mode == 1:
            # Best skills first
            applications.sort(key=lambda a: a.s, reverse=True)
        elif order_mode == 2:
            # Lowest wage first
            applications.sort(key=lambda a: a.w)
        else:  # mode == 3
            # Best skills/wage ratio
            applications.sort(key=lambda a: a.s / a.w if a.w > 0 else 0, reverse=True)
    
    def _order_offers(self, order_mode: int, offers: List[WageOffer]):
        """
        Order wage offers according to sequence strategy
        0: random, 1: highest wage, 2: most workers, 3: best wage/worker ratio
        """
        if order_mode == 0:
            get_random_engine().shuffle(offers)
        elif order_mode == 1:
            offers.sort(key=lambda o: o.offer, reverse=True)
        elif order_mode == 2:
            offers.sort(key=lambda o: o.workers, reverse=True)
        else:  # mode == 3
            offers.sort(key=lambda o: o.offer / max(o.workers, 1), reverse=True)
    
    def fire_workers_sector1(self, firms1: List) -> int:
        """
        Process firing in sector 1 according to firing rules
        """
        flag_fire_rule = self.config.get('Country.flagFireRule', 2)
        flag_fire_order = self.config.get('Country.flagFireOrder1', 0)
        Lscale = self.config.get('Labor.Lscale', 1)
        
        total_fired = 0
        
        for firm in firms1:
            if not hasattr(firm, 'workers') or not firm.workers:
                continue
            
            current_workers = len(firm.workers)
            desired_workers = int(firm._L1d / Lscale) if hasattr(firm, '_L1d') else current_workers
            
            if current_workers <= desired_workers:
                continue
            
            to_fire = current_workers - desired_workers
            
            # Sort workers for firing
            workers_sorted = self._sort_workers_for_firing(firm.workers, flag_fire_order)
            
            # Fire workers
            for i in range(min(to_fire, len(workers_sorted))):
                worker = workers_sorted[i]
                self._fire_worker(worker, firm)
                total_fired += 1
        
        return total_fired * Lscale
    
    def fire_workers_sector2(self, firms2: List) -> int:
        """Process firing in sector 2"""
        flag_fire_rule = self.config.get('Country.flagFireRule', 2)
        flag_fire_order = self.config.get('Country.flagFireOrder2', 0)
        Lscale = self.config.get('Labor.Lscale', 1)
        
        total_fired = 0
        
        for firm in firms2:
            if not hasattr(firm, 'workers') or not firm.workers:
                continue
            
            current_workers = len(firm.workers)
            desired_workers = int(firm._L2d / Lscale) if hasattr(firm, '_L2d') else current_workers
            
            if current_workers <= desired_workers:
                continue
            
            to_fire = current_workers - desired_workers
            
            workers_sorted = self._sort_workers_for_firing(firm.workers, flag_fire_order)
            
            for i in range(min(to_fire, len(workers_sorted))):
                worker = workers_sorted[i]
                self._fire_worker(worker, firm)
                total_fired += 1
        
        return total_fired * Lscale
    
    def _sort_workers_for_firing(self, workers: List, order_mode: int) -> List:
        """
        Sort workers for firing
        0: random, 1: lowest skills, 2: highest wage, 3: worst skills/wage
        """
        workers_copy = workers.copy()
        
        if order_mode == 0:
            get_random_engine().shuffle(workers_copy)
        elif order_mode == 1:
            workers_copy.sort(key=lambda w: w._s)
        elif order_mode == 2:
            workers_copy.sort(key=lambda w: w._w, reverse=True)
        else:  # mode == 3
            workers_copy.sort(key=lambda w: w._s / w._w if w._w > 0 else 0)
        
        return workers_copy
    
    def _fire_worker(self, worker, firm):
        """Fire a worker from a firm"""
        worker._employed = 0
        worker._Te = 0
        worker._Tu = 0  # Reset unemployment duration
        
        if hasattr(firm, 'workers') and worker in firm.workers:
            firm.workers.remove(worker)
        
        worker.employer = None
