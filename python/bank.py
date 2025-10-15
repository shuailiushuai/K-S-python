"""
Bank Agent Implementation
Implements bank agents with credit supply, deposits, and Basel-like capital adequacy.
Based on fun_KS_bank.h
"""

from typing import List, Optional
from .agents import BaseAgent, FirmRank
from .config import INIPROD
import math


class Bank(BaseAgent):
    """
    Bank agent class.
    Handles deposits, loans, reserves, and capital adequacy.
    """
    
    def __init__(self, agent_id: int, parent=None):
        super().__init__(agent_id, "Bank", parent)
        
        # Bank-specific variables
        self._IDb = agent_id          # Bank ID
        self._Depo = 0.0              # Total deposits
        self._Loans = 0.0             # Total loans
        self._Res = 0.0               # Required reserves
        self._ExRes = 0.0             # Excess reserves
        self._BondsB = 0.0            # Government bonds held
        self._NWb = 0.0               # Net worth
        self._BadDeb1 = 0.0           # Bad debt from sector 1
        self._BadDeb2 = 0.0           # Bad debt from sector 2
        self._TC1 = 0.0               # Total credit to sector 1
        self._TC2 = 0.0               # Total credit to sector 2
        self._TC1free = 0.0           # Available credit sector 1
        self._TC2free = 0.0           # Available credit sector 2
        self._r = 0.0                 # Prime interest rate
        self._rD = 0.0                # Deposit interest rate
        self._rRes = 0.0              # Reserves interest rate
        self._rDeb = 0.0              # Debt interest rate
        
        # Client lists (simplified - actual implementation uses children)
        self.clients_sector1 = []
        self.clients_sector2 = []
        
    def compute_bad_debt_fragility(self) -> float:
        """
        Compute financial fragility (_Bda equation).
        Ratio of bad debt to total assets.
        
        Returns:
            Financial fragility ratio
        """
        bad_debt = max(0.0, self.VL("_BadDeb1", 1) + self.VL("_BadDeb2", 1))
        assets = (self.VL("_Loans", 1) + self.VL("_BondsB", 1) + 
                 self.VL("_Res", 1) + self.VL("_ExRes", 1))
        
        Bda = bad_debt / assets if assets > 0 else 0.0
        self.WRITE("_Bda", Bda)
        return Bda
    
    def compute_deposits(self, rD: float) -> float:
        """
        Compute deposits and interest paid (_Depo, _IntPaid equations).
        
        Args:
            rD: Deposit interest rate
            
        Returns:
            Total deposits
        """
        # Sum deposits from all clients
        deposits = 0.0
        
        # Sector 1 clients
        for cli in self.get_children("Cli1"):
            firm = cli.HOOK(0)  # Hook back to firm
            if firm:
                deposits += max(0.0, firm.VL("_NW1", 1))
        
        # Sector 2 clients
        for cli in self.get_children("Cli2"):
            firm = cli.HOOK(0)
            if firm:
                deposits += max(0.0, firm.VL("_NW2", 1))
        
        self._Depo = deposits
        self.WRITE("_Depo", deposits)
        
        # Interest paid on deposits
        int_paid = rD * deposits
        self.WRITE("_IntPaid", int_paid)
        
        return deposits
    
    def compute_credit_scores(self):
        """
        Define credit class for bank's clients (_cScores equation).
        Ranks clients by net-worth-to-sales ratio.
        """
        rank1 = []
        rank2 = []
        
        # Rank sector 1 clients
        for cli in self.get_children("Cli1"):
            firm = cli.HOOK(0)
            if firm:
                NW = firm.VL("_NW1", 1)
                S = firm.VL("_S1", 1)
                NWtoS = NW / S if S > 0 else 0.0
                rank1.append(FirmRank(NWtoS=NWtoS, firm=firm))
        
        # Rank sector 2 clients
        for cli in self.get_children("Cli2"):
            firm = cli.HOOK(0)
            if firm:
                NW = firm.VL("_NW2", 1)
                S = firm.VL("_S2", 1)
                NWtoS = NW / S if S > 0 else 0.0
                rank2.append(FirmRank(NWtoS=NWtoS, firm=firm))
        
        # Sort by NWtoS ratio (descending)
        rank1.sort(key=lambda x: x.NWtoS, reverse=True)
        rank2.sort(key=lambda x: x.NWtoS, reverse=True)
        
        # Assign credit classes (position in ranking)
        for i, rank in enumerate(rank1):
            if rank.firm:
                rank.firm.WRITE("_cClass", i + 1)
        
        for i, rank in enumerate(rank2):
            if rank.firm:
                rank.firm.WRITE("_cClass", i + 1)
    
    def compute_credit_supply(self, Lambda: float, flagCreditRule: int, 
                             tauB: float, kConst: float) -> tuple:
        """
        Compute available credit supply (TC1, TC2 equations).
        
        Args:
            Lambda: Credit multiple
            flagCreditRule: Credit rule type
            tauB: Capital adequacy ratio
            kConst: Credit class interest ramping
            
        Returns:
            Tuple of (TC1, TC2) - total credit for each sector
        """
        if flagCreditRule == 0:
            # No bank-level credit limit
            TC1 = float('inf')
            TC2 = float('inf')
            self._TC1free = -1.0  # Signal unlimited credit
            self._TC2free = -1.0
        else:
            # Compute credit based on deposits and capital adequacy
            if flagCreditRule == 1:
                # Simple deposit multiplier
                TC_total = Lambda * self._Depo
            else:  # flagCreditRule == 2
                # Basel-like capital adequacy
                assets = self._Loans + self._BondsB
                TC_total = assets + self._NWb / tauB - self._BondsB
                TC_total = max(0.0, TC_total)
            
            # Allocate between sectors (proportional to current loans)
            loans1 = sum(cli.HOOK(0).V("_Deb1") for cli in self.get_children("Cli1") 
                        if cli.HOOK(0))
            loans2 = sum(cli.HOOK(0).V("_Deb2") for cli in self.get_children("Cli2") 
                        if cli.HOOK(0))
            total_loans = loans1 + loans2
            
            if total_loans > 0:
                TC1 = TC_total * loans1 / total_loans
                TC2 = TC_total * loans2 / total_loans
            else:
                TC1 = TC_total / 2
                TC2 = TC_total / 2
            
            self._TC1free = TC1
            self._TC2free = TC2
        
        self._TC1 = TC1
        self._TC2 = TC2
        self.WRITE("_TC1", TC1)
        self.WRITE("_TC2", TC2)
        
        return TC1, TC2
    
    def compute_profits(self, rD: float, rDeb: float, rRes: float, 
                       rBonds: float) -> float:
        """
        Compute bank profits (_PiB equation).
        
        Args:
            rD: Deposit interest rate
            rDeb: Debt interest rate
            rRes: Reserves interest rate
            rBonds: Bonds interest rate
            
        Returns:
            Bank profits
        """
        # Interest income from loans
        int_income = rDeb * self._Loans
        
        # Interest income from reserves and bonds
        int_income += rRes * (self._Res + self._ExRes)
        int_income += rBonds * self._BondsB
        
        # Interest paid on deposits
        int_expense = rD * self._Depo
        
        # Bad debt losses
        bad_debt = self._BadDeb1 + self._BadDeb2
        
        # Profits
        PiB = int_income - int_expense - bad_debt
        
        self.WRITE("_PiB", PiB)
        return PiB
    
    def compute_net_worth(self, dB: float) -> float:
        """
        Compute bank net worth (_NWb equation).
        
        Args:
            dB: Dividend rate
            
        Returns:
            Updated net worth
        """
        PiB = self.V("_PiB")
        TaxB = self.V("_TaxB")
        
        # Retained profits after tax and dividends
        retained = PiB - TaxB
        dividends = dB * max(0.0, retained)
        retained -= dividends
        
        # Update net worth
        self._NWb += retained
        self.WRITE("_NWb", self._NWb)
        self.WRITE("_DivB", dividends)
        
        return self._NWb
    
    def check_bailout(self, PhiB: float, avg_bank_size: float) -> float:
        """
        Check if bank needs bailout and compute required capital injection.
        
        Args:
            PhiB: Fraction of average bank size for bailout
            avg_bank_size: Average bank assets
            
        Returns:
            Bailout amount (0 if no bailout needed)
        """
        if self._NWb < 0:
            # Bank failed - needs bailout
            bailout = PhiB * avg_bank_size - self._NWb
            self._NWb = PhiB * avg_bank_size
            self.WRITE("_NWb", self._NWb)
            return bailout
        
        return 0.0
    
    def compute_reserves(self, muRes: float, theta_reserves: float) -> tuple:
        """
        Compute required and excess reserves.
        
        Args:
            muRes: Reserve requirement ratio
            theta_reserves: Excess reserve target ratio
            
        Returns:
            Tuple of (required_reserves, excess_reserves)
        """
        # Required reserves
        required = muRes * self._Depo
        
        # Excess reserves (for liquidity management)
        target_excess = theta_reserves * self._Depo
        excess = max(0.0, self._Depo - self._Loans - required - target_excess)
        
        self._Res = required
        self._ExRes = excess
        self.WRITE("_Res", required)
        self.WRITE("_ExRes", excess)
        
        return required, excess
