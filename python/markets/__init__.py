"""
Market and Sector Container Classes
Translated from fun_KS_capital.h, fun_KS_consumption.h, fun_KS_labor.h, fun_KS_financial.h
"""

from typing import List, Dict, Any, Optional
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents import Worker, Firm1, Firm2, Bank
from utils.random_gen import get_random_generator
from utils.support import WageOffer, Application


class LaborMarket:
    """
    Labor market container
    Manages workers and job search/matching
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize labor market"""
        self.workers: List[Worker] = []
        self.config = config
        
        # Labor market variables
        self.Ls = 0  # Labor supply
        self.L = 0  # Employment
        self.U = 0  # Unemployment
        self.Ue = 0.0  # Unemployment rate
        self.W = 0.0  # Total wages
        self.wAvg = 1.0  # Average wage
        self.wCent = 1.0  # Centralized wage
        self.wMinPol = 1.0  # Minimum wage policy
        self.sAvg = 1.0  # Average skills
        
        # Job applications
        self.applications_sector1: List[Application] = []
        self.applications_sector2: Dict[int, List[Application]] = {}
        
    def initialize(self, config: Dict[str, Any]):
        """Initialize labor market"""
        Ls0 = int(config.get('Ls0', 1000))
        Lscale = int(config.get('Lscale', 1))
        w0min = config.get('w0min', 1.0)
        
        # Create workers
        for i in range(Ls0 // Lscale):
            worker = Worker(i, 0)
            worker.initialize(config)
            self.workers.append(worker)
        
        self.Ls = Ls0
        self.wMinPol = w0min
        self.wCent = w0min
    
    def step(self, t: int):
        """Execute one time step"""
        # Update workers
        for worker in self.workers:
            worker.step(t)
        
        # Update aggregate variables
        self.update_aggregates(t)
        
        # Grow labor force
        self.grow_labor_force(t)
    
    def update_aggregates(self, t: int):
        """Update aggregate labor market variables"""
        employed = sum(1 for w in self.workers if w.get_employment_status() > 0)
        self.L = employed * self.config.get('Lscale', 1)
        self.U = self.Ls - self.L
        self.Ue = self.U / self.Ls if self.Ls > 0 else 0.0
        
        # Average wage
        total_wage = sum(w.get_wage() for w in self.workers if w.get_employment_status() > 0)
        self.wAvg = total_wage / employed if employed > 0 else self.wMinPol
        
        # Total wages
        self.W = total_wage * self.config.get('Lscale', 1)
        
        # Average skills
        self.sAvg = sum(w.get_skills() for w in self.workers) / len(self.workers)
    
    def grow_labor_force(self, t: int):
        """Grow labor force according to delta parameter"""
        delta = self.config.get('delta', 0.0)
        Lscale = self.config.get('Lscale', 1)
        
        if delta > 0:
            new_workers = int(self.Ls * delta / Lscale)
            for i in range(new_workers):
                worker_id = len(self.workers)
                worker = Worker(worker_id, t)
                worker.initialize(self.config)
                self.workers.append(worker)
            
            self.Ls = len(self.workers) * Lscale
    
    def collect_applications(self, t: int):
        """Collect job applications from workers"""
        self.applications_sector1 = []
        self.applications_sector2 = {}
        
        # For now, simplified application collection
        # In full model, workers create Application objects
    
    def match_workers(self, firms1: List[Firm1], firms2: List[Firm2], t: int):
        """Match workers to firms"""
        # Simplified matching algorithm
        # In full model, implements search and matching process
        pass


class CapitalGoodsSector:
    """
    Capital goods sector container
    Manages Firm1 agents
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize capital goods sector"""
        self.firms: List[Firm1] = []
        self.config = config
        
        # Sector variables
        self.F1 = 0  # Number of firms
        self.Q1 = 0.0  # Total production
        self.D1 = 0.0  # Total demand
        self.L1 = 0  # Total employment
        self.L1d = 0  # Total desired employment
        self.A1 = 1.0  # Average productivity
        self.p1avg = 1.0  # Average price
        
    def initialize(self, config: Dict[str, Any]):
        """Initialize sector"""
        F10 = int(config.get('F10', 50))
        
        # Create firms
        for i in range(F10):
            firm = Firm1(i, 0)
            firm.initialize(config)
            self.firms.append(firm)
        
        self.F1 = F10
    
    def step(self, t: int):
        """Execute one time step"""
        # Update firms
        for firm in self.firms:
            firm.step(t)
        
        # Update aggregates
        self.update_aggregates(t)
        
        # Handle entry/exit
        self.handle_entry_exit(t)
    
    def update_aggregates(self, t: int):
        """Update sector aggregates"""
        self.F1 = len(self.firms)
        self.Q1 = sum(f._Q1 for f in self.firms)
        self.D1 = sum(f._D1 for f in self.firms)
        self.L1 = sum(f._L1 for f in self.firms)
        self.L1d = sum(f._L1d for f in self.firms)
        
        if self.F1 > 0:
            self.A1 = sum(f._Atau for f in self.firms) / self.F1
            self.p1avg = sum(f._p1 for f in self.firms) / self.F1
    
    def handle_entry_exit(self, t: int):
        """Handle firm entry and exit"""
        # Exit firms with negative net worth
        self.firms = [f for f in self.firms if f._NW1 > 0]
        
        # Entry logic (simplified)
        # In full model, entry depends on market conditions


class ConsumptionGoodsSector:
    """
    Consumption goods sector container
    Manages Firm2 agents
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize consumption goods sector"""
        self.firms: List[Firm2] = []
        self.config = config
        
        # Sector variables
        self.F2 = 0  # Number of firms
        self.Q2 = 0.0  # Total production
        self.D2 = 0.0  # Total demand
        self.L2 = 0  # Total employment
        self.L2d = 0  # Total desired employment
        self.A2 = 1.0  # Average productivity
        self.p2avg = 1.0  # Average price
        
    def initialize(self, config: Dict[str, Any]):
        """Initialize sector"""
        F20 = int(config.get('F20', 200))
        
        # Create firms
        for i in range(F20):
            firm = Firm2(i, 0)
            firm.initialize(config)
            self.firms.append(firm)
        
        self.F2 = F20
    
    def step(self, t: int):
        """Execute one time step"""
        # Update firms
        for firm in self.firms:
            firm.step(t)
        
        # Update aggregates
        self.update_aggregates(t)
        
        # Handle entry/exit
        self.handle_entry_exit(t)
    
    def update_aggregates(self, t: int):
        """Update sector aggregates"""
        self.F2 = len(self.firms)
        self.Q2 = sum(f._Q2 for f in self.firms)
        self.D2 = sum(f._D2 for f in self.firms)
        self.L2 = sum(f._L2 for f in self.firms)
        self.L2d = sum(f._L2d for f in self.firms)
        
        if self.F2 > 0:
            self.A2 = sum(f._A2 for f in self.firms) / self.F2
            self.p2avg = sum(f._p2 for f in self.firms) / self.F2
    
    def handle_entry_exit(self, t: int):
        """Handle firm entry and exit"""
        # Exit firms with negative net worth
        self.firms = [f for f in self.firms if f._NW2 > 0]
        
        # Entry logic (simplified)
        # In full model, entry depends on market conditions
    
    def allocate_demand(self, total_demand: float, t: int):
        """
        Allocate demand among firms based on competitiveness
        
        Args:
            total_demand: Total nominal demand
            t: Current time period
        """
        if not self.firms:
            return
        
        # Calculate competitiveness for each firm
        competitiveness = [(f.calculate_competitiveness(), f) for f in self.firms]
        
        # Calculate market shares using replicator dynamics
        chi = self.config.get('chi', 1.0)
        comp_vals = [c[0] for c in competitiveness]
        mean_comp = sum(comp_vals) / len(comp_vals) if comp_vals else 0
        
        # Update market shares
        total_share = 0.0
        for comp, firm in competitiveness:
            # Replicator dynamics
            delta_f = chi * firm._f2 * (comp - mean_comp)
            firm._f2 = max(0.001, firm._f2 + delta_f)
            total_share += firm._f2
        
        # Normalize shares
        if total_share > 0:
            for firm in self.firms:
                firm._f2 /= total_share
        
        # Allocate demand
        for firm in self.firms:
            firm_demand = total_demand * firm._f2 / firm._p2
            firm._D2 = min(firm_demand, firm._Q2 + firm._N)


class FinancialSector:
    """
    Financial sector container
    Manages banks and central bank
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize financial sector"""
        self.banks: List[Bank] = []
        self.config = config
        
        # Central bank variables
        self.r = 0.01  # Prime rate
        self.rDeb = 0.01  # Loan rate
        self.rD = 0.01  # Deposit rate
        self.rBonds = 0.01  # Bond rate
        
        # Sector variables
        self.Loans = 0.0  # Total loans
        self.Depo = 0.0  # Total deposits
        self.NWb = 0.0  # Total bank net worth
        self.PiB = 0.0  # Total bank profit
        
    def initialize(self, config: Dict[str, Any]):
        """Initialize financial sector"""
        B = int(config.get('B', 1))
        
        # Create banks
        for i in range(B):
            bank = Bank(i, 0)
            bank.initialize(config)
            self.banks.append(bank)
    
    def step(self, t: int):
        """Execute one time step"""
        # Update central bank interest rate
        self.update_prime_rate(t)
        
        # Update banks
        for bank in self.banks:
            bank.step(t)
        
        # Update aggregates
        self.update_aggregates(t)
        
        # Handle bank failures
        self.handle_bank_failures(t)
    
    def update_prime_rate(self, t: int):
        """Update central bank prime rate"""
        # Simplified - in full model uses Taylor rule
        rT = self.config.get('rT', 0.01)
        self.r = rT
        
        # Update related rates
        muDeb = self.config.get('muDeb', 0.0)
        muD = self.config.get('muD', 1.0)
        
        self.rDeb = self.r * (1 + muDeb)
        self.rD = self.r * muD
    
    def update_aggregates(self, t: int):
        """Update sector aggregates"""
        self.Loans = sum(b._Loans for b in self.banks)
        self.Depo = sum(b._Depo for b in self.banks)
        self.NWb = sum(b._NWb for b in self.banks)
        self.PiB = sum(b._PiB for b in self.banks)
    
    def handle_bank_failures(self, t: int):
        """Handle insolvent banks"""
        # Bail out insolvent banks
        for bank in self.banks:
            if not bank.is_solvent():
                # Government bailout
                PhiB = self.config.get('PhiB', 0.5)
                avg_nw = self.NWb / len(self.banks) if self.banks else 0
                bank._NWb = PhiB * avg_nw
