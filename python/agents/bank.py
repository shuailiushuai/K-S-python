"""
Bank Agent Implementation
Translated from fun_KS_bank.h
"""

from typing import Dict, Any, List
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.base import BaseAgent


class Bank(BaseAgent):
    """
    Bank agent in financial sector
    Provides loans and manages deposits
    """
    
    def __init__(self, bank_id: int, t: int = 0):
        """Initialize Bank"""
        super().__init__(bank_id, t)
        
        # Bank variables
        self._Depo = 0.0  # Deposits
        self._Loans = 0.0  # Total loans
        self._NWb = 0.0  # Net worth
        self._Res = 0.0  # Required reserves
        self._ExRes = 0.0  # Excess reserves
        self._PiB = 0.0  # Profit
        self._DivB = 0.0  # Dividends
        self._TaxB = 0.0  # Taxes
        self._BondsB = 0.0  # Government bonds held
        self._BD = 0.0  # Bad debt
        self._Bda = 0.0  # Bad debt accumulation
        self._iB = 0.0  # Interest rate on loans
        self._iDb = 0.0  # Interest rate on deposits
        self._Cl = 0  # Number of clients
        self._fB = 0.0  # Market share
        
        # Client lists
        self.clients_firm1: List[BaseAgent] = []
        self.clients_firm2: List[BaseAgent] = []
        
    def initialize(self, config: Dict[str, Any]):
        """Initialize bank with configuration"""
        # Interest rate parameters
        self.set_param('muDeb', config.get('muDeb', 0.0))
        self.set_param('muD', config.get('muD', 1.0))
        self.set_param('muRes', config.get('muRes', 1.0))
        self.set_param('kConst', config.get('kConst', 0.0))
        
        # Capital adequacy
        self.set_param('tauB', config.get('tauB', 0.08))
        self.set_param('Lambda', config.get('Lambda', 2.0))
        
        # Initial values
        self._NWb = config.get('EqB0', 100.0)
        
    def step(self, t: int):
        """Execute one time step"""
        # 1. Update interest rates
        self.update_interest_rates(t)
        
        # 2. Evaluate loan requests
        self.process_loan_requests(t)
        
        # 3. Collect interest and manage defaults
        self.collect_interest(t)
        
        # 4. Update finances
        self.update_finances(t)
        
        # Update lagged variables
        self.update_lagged(t)
    
    def update_interest_rates(self, t: int):
        """Update bank interest rates"""
        # Get prime rate from central bank
        r = 0.01  # Simplified - should get from financial sector
        
        muDeb = self.get_param('muDeb', 0.0)
        muD = self.get_param('muD', 1.0)
        
        # Interest rate on loans (markup over prime)
        self._iB = r * (1 + muDeb)
        
        # Interest rate on deposits (markdown from prime)
        self._iDb = r * muD
    
    def process_loan_requests(self, t: int):
        """Process loan requests from firms"""
        # Calculate available credit
        tauB = self.get_param('tauB', 0.08)
        Lambda = self.get_param('Lambda', 2.0)
        
        # Maximum lending based on capital adequacy
        max_loans = self._NWb / tauB if tauB > 0 else float('inf')
        
        # Process requests (simplified)
        # In full model, would rank firms by creditworthiness
        
    def collect_interest(self, t: int):
        """Collect interest on loans and pay on deposits"""
        # Interest income from loans
        interest_income = self._Loans * self._iB
        
        # Interest paid on deposits
        interest_paid = self._Depo * self._iDb
        
        # Net interest income
        return interest_income - interest_paid
    
    def update_finances(self, t: int):
        """Update bank financial variables"""
        # Profit from interest margin
        self._PiB = self.collect_interest(t)
        
        # Deduct bad debt
        self._PiB -= self._BD
        
        # Taxes
        if self._PiB > 0:
            tr = 0.1
            self._TaxB = self._PiB * tr
        else:
            self._TaxB = 0.0
        
        # Dividends
        dB = self.get_param('dB', 0.0)
        self._DivB = max(0, dB * (self._PiB - self._TaxB))
        
        # Update net worth
        self._NWb = self._NWb + self._PiB - self._TaxB - self._DivB
    
    def grant_loan(self, firm: BaseAgent, amount: float) -> float:
        """
        Grant loan to firm
        
        Args:
            firm: Firm requesting loan
            amount: Loan amount requested
            
        Returns:
            Actual loan amount granted
        """
        # Check credit limit
        tauB = self.get_param('tauB', 0.08)
        max_loans = self._NWb / tauB if tauB > 0 else float('inf')
        available = max_loans - self._Loans
        
        granted = min(amount, available)
        self._Loans += granted
        
        return granted
    
    def repay_loan(self, amount: float):
        """Repay loan amount"""
        self._Loans = max(0, self._Loans - amount)
    
    def add_deposit(self, amount: float):
        """Add deposit"""
        self._Depo += amount
    
    def withdraw_deposit(self, amount: float) -> float:
        """Withdraw from deposit"""
        withdrawn = min(amount, self._Depo)
        self._Depo -= withdrawn
        return withdrawn
    
    def record_default(self, amount: float):
        """Record defaulted loan"""
        self._BD += amount
        self._Loans = max(0, self._Loans - amount)
        
        # Update bad debt accumulation
        if self._Loans + self._BondsB + self._Res + self._ExRes > 0:
            self._Bda = self._BD / (self._Loans + self._BondsB + self._Res + self._ExRes)
    
    def is_solvent(self) -> bool:
        """Check if bank is solvent"""
        return self._NWb > 0
    
    def add_client(self, firm: BaseAgent, sector: int):
        """
        Add client firm
        
        Args:
            firm: Client firm
            sector: Sector number (1 or 2)
        """
        if sector == 1:
            self.clients_firm1.append(firm)
        elif sector == 2:
            self.clients_firm2.append(firm)
        self._Cl = len(self.clients_firm1) + len(self.clients_firm2)
