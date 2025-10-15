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
    
    def compute_pecking_order(self) -> int:
        """
        Compute pecking order ranking for credit allocation.
        Based on _qc equation in fun_KS_bank.h
        
        Returns:
            Number of clients ranked
        """
        rank1 = []
        rank2 = []
        
        # Rank sector 1 clients by NW/S ratio
        for cli in self.get_children("Cli1"):
            firm = cli.get_hook("firm")
            if firm:
                NW1 = firm.VL("_NW1", 1)
                S1 = firm.VL("_S1", 1)
                
                # Compute net-worth-to-sales ratio
                if NW1 > 0 and S1 > 0:
                    NWtoS = NW1 / S1
                else:
                    NWtoS = 0.0
                
                rank1.append(FirmRank(NWtoS=NWtoS, firm=firm))
        
        # Rank sector 2 clients by NW/S ratio
        for cli in self.get_children("Cli2"):
            firm = cli.get_hook("firm")
            if firm:
                NW2 = firm.VL("_NW2", 1)
                S2 = firm.VL("_S2", 1)
                
                # Compute net-worth-to-sales ratio
                if NW2 > 0 and S2 > 0:
                    NWtoS = NW2 / S2
                else:
                    NWtoS = 0.0
                
                rank2.append(FirmRank(NWtoS=NWtoS, firm=firm))
        
        # Sort in descending order (higher ratios first)
        rank1.sort(key=lambda r: r.NWtoS, reverse=True)
        rank2.sort(key=lambda r: r.NWtoS, reverse=True)
        
        # Assign credit quality classes (1=best, 4=worst)
        i = len(rank1)
        for h, cli in enumerate(rank1):
            if h < i * 0.25:
                qc = 1
            elif h < i * 0.5:
                qc = 2
            elif h < i * 0.75:
                qc = 3
            else:
                qc = 4
            
            cli.firm.WRITE("_qc1", qc)
        
        j = len(rank2)
        for h, cli in enumerate(rank2):
            if h < j * 0.25:
                qc = 1
            elif h < j * 0.5:
                qc = 2
            elif h < j * 0.75:
                qc = 3
            else:
                qc = 4
            
            cli.firm.WRITE("_qc2", qc)
        
        return i + j
    
    def compute_total_credit_supply(self, params: dict) -> float:
        """
        Compute total credit supply available to firms.
        Based on _TC equation in fun_KS_bank.h
        
        Args:
            params: Model parameters
            
        Returns:
            Total credit available (-1 means unlimited)
        """
        flagCreditRule = params.get('flagCreditRule', 0)
        
        if flagCreditRule == 1:
            # Deposits multiplier rule
            tauB = params.get('tauB', 0.1)
            Depo = self.V("_Depo")
            TC = Depo / tauB if tauB > 0 else 0.0
        elif flagCreditRule == 2:
            # Basel-like credit rule with fragility
            tauB = params.get('tauB', 0.1)
            betaB = params.get('betaB', 1.0)
            mPerB = params.get('mPerB', 4)
            
            # Moving average of fragility
            Bda_avg = 0.0
            count = 0
            try:
                for i in range(mPerB):
                    val = self.VL("_Bda", i)
                    Bda_avg += val
                    count += 1
            except:
                # No history available
                pass
            
            if count > 0:
                Bda_avg /= count
            else:
                Bda_avg = self.V("_Bda") if hasattr(self, '_Bda') else 0.0
            
            # Capital adequacy adjusted for fragility
            NWb = self.V("_NWb")
            TC = NWb / (tauB * (1 + betaB * Bda_avg)) if tauB > 0 else 0.0
        else:
            # No credit limit
            TC = -1.0
        
        self.WRITE("_TC", TC)
        return TC
    
    def allocate_credit_by_sector(self, params: dict) -> tuple:
        """
        Allocate credit between sectors.
        Based on _TC1free and _TC2free equations.
        
        Args:
            params: Model parameters
            
        Returns:
            Tuple of (TC1free, TC2free)
        """
        flagCreditRule = params.get('flagCreditRule', 0)
        
        if flagCreditRule == 0:
            # No credit limit
            return -1.0, -1.0
        
        # Get credit demand from both sectors
        CD1b = self.VL("_CD1b", 1)
        CD2b = self.VL("_CD2b", 1)
        
        # Allocate proportionally to demand
        if CD1b + CD2b > 0:
            share1 = CD1b / (CD1b + CD2b)
            share2 = CD2b / (CD1b + CD2b)
        else:
            # No demand - split 50/50
            share1 = 0.5
            share2 = 0.5
        
        # Free credit to lend
        TC = self.V("_TC")
        Loans = self.VL("_Loans", 1)
        free_credit = max(0.0, TC - Loans)
        
        TC1free = share1 * free_credit
        TC2free = share2 * free_credit
        
        self.WRITE("_TC1free", TC1free)
        self.WRITE("_TC2free", TC2free)
        
        return TC1free, TC2free
