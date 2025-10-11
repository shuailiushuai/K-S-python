"""
Bank Agent Implementation
Represents banks in the financial sector
"""

from typing import Optional, List, Tuple
from .agent import Agent
from .constants import *
from .random_engine import random_engine
from .support import safe_divide
from .data_structures import FirmRank
import math


class Bank(Agent):
    """
    Bank agent class
    
    Banks:
    - Accept deposits from firms and government
    - Supply credit to firms
    - Set interest rates
    - Follow capital adequacy rules (Basel-like)
    - Can experience bankruptcy and bailout
    """
    
    def __init__(self, bank_id: int, parent: Agent):
        """
        Initialize Bank agent
        
        Args:
            bank_id: Unique bank ID
            parent: Parent Financial sector object
        """
        super().__init__("Bank", parent)
        
        # Bank identification
        self._IDb = bank_id
        
        # Assets
        self._Loans = 0.0                 # Total loans outstanding
        self._Res = 0.0                   # Reserves held
        self._ExRes = 0.0                 # Excess reserves
        self._BondsB = 0.0                # Government bonds held
        
        # Liabilities
        self._Depo = 0.0                  # Total deposits
        self._LoansCB = 0.0               # Loans from central bank
        
        # Equity and performance
        self._NWb = 0.0                   # Net worth (equity)
        self._PiB = 0.0                   # Profits
        self._BadDeb1 = 0.0               # Bad debt from sector 1
        self._BadDeb2 = 0.0               # Bad debt from sector 2
        self._DivB = 0.0                  # Dividends paid
        self._TaxB = 0.0                  # Taxes paid
        
        # Credit supply
        self._TC = 0.0                    # Total credit available
        self._TC1free = 0.0               # Free credit for sector 1
        self._TC2free = 0.0               # Free credit for sector 2
        
        # Clients and market
        self._Cl = 0                      # Number of clients
        self._fB = 0.0                    # Market share
        
        # Interest rates
        self._iB = 0.0                    # Interest rate on loans
        self._iDb = 0.0                   # Interest rate on deposits
        
        # Debt allocation tracking
        self._CD1b = 0.0                  # Credit demand sector 1
        self._CD2b = 0.0                  # Credit demand sector 2
        self._Bda = 0.0                   # Bank debt available
        
    def compute_total_credit(self, params: dict) -> float:
        """
        Compute total credit supply available
        
        Based on:
        1. Capital adequacy rules (Basel-like)
        2. Deposits
        3. Central bank loans
        
        Args:
            params: Dictionary with:
                - alpha: Capital adequacy ratio
                - betaB: Leverage ratio
                - lambda_val: Reserve requirement ratio
        
        Returns:
            Total credit available
        """
        alpha = params.get('alpha', 0.08)     # Capital adequacy ratio
        betaB = params.get('betaB', 0.9)      # Leverage ratio
        lambda_val = params.get('lambda', 0.05)  # Reserve requirement
        
        NWb = self.read("_NWb", 1)
        Depo = self.read("_Depo", 1)
        
        # Capital adequacy constraint
        TC_capital = NWb / alpha if alpha > 0 else 0
        
        # Leverage constraint
        TC_leverage = betaB * (NWb + Depo)
        
        # Take minimum of constraints
        TC = min(TC_capital, TC_leverage)
        
        # Subtract required reserves
        required_reserves = lambda_val * Depo
        TC = max(0, TC - required_reserves)
        
        self.write("_TC", TC)
        self._TC = TC
        return TC
    
    def allocate_credit_sector1(self, firms: List, sector_demand: float) -> Tuple[float, List]:
        """
        Allocate credit to sector 1 firms
        
        Uses pecking order based on net worth to sales ratio
        
        Args:
            firms: List of Firm1 objects requesting credit
            sector_demand: Total credit demand from sector 1
        
        Returns:
            Tuple of (allocated_credit, allocation_list)
        """
        if not firms or sector_demand <= 0:
            self.write("_TC1free", self._TC)
            return 0.0, []
        
        # Create pecking order ranking
        pecking_order = []
        for firm in firms:
            NW1 = firm.read("_NW1", 1)
            S1 = firm.read("_S1", 1)
            
            # Firms with higher NW/S ratio get priority
            nw_to_s = safe_divide(NW1, S1, 0)
            
            pecking_order.append(FirmRank(NWtoS=nw_to_s, firm=firm))
        
        # Sort by ratio (descending - higher is better)
        pecking_order.sort(key=lambda x: x.NWtoS, reverse=True)
        
        # Allocate credit in order
        TC1_available = self.read("_TC1free", 0)
        if TC1_available == 0:
            TC1_available = self._TC
        
        allocated_credit = 0.0
        allocations = []
        
        for rank in pecking_order:
            firm = rank.firm
            credit_demand = firm.read("_Deb1max", 0) - firm.read("_Deb1", 1)
            
            if credit_demand <= 0:
                continue
            
            # Allocate as much as possible
            credit_granted = min(credit_demand, TC1_available - allocated_credit)
            
            if credit_granted > 0:
                allocations.append((firm, credit_granted))
                allocated_credit += credit_granted
            
            if allocated_credit >= TC1_available:
                break
        
        # Update free credit
        TC1_free = TC1_available - allocated_credit
        self.write("_TC1free", TC1_free)
        self._TC1free = TC1_free
        
        self.write("_CD1b", min(sector_demand, allocated_credit))
        self._CD1b = min(sector_demand, allocated_credit)
        
        return allocated_credit, allocations
    
    def allocate_credit_sector2(self, firms: List, sector_demand: float) -> Tuple[float, List]:
        """
        Allocate credit to sector 2 firms
        
        Uses pecking order based on net worth to sales ratio
        
        Args:
            firms: List of Firm2 objects requesting credit
            sector_demand: Total credit demand from sector 2
        
        Returns:
            Tuple of (allocated_credit, allocation_list)
        """
        if not firms or sector_demand <= 0:
            self.write("_TC2free", self._TC1free)
            return 0.0, []
        
        # Create pecking order ranking
        pecking_order = []
        for firm in firms:
            NW2 = firm.read("_NW2", 1)
            S2 = firm.read("_S2", 1)
            
            # Firms with higher NW/S ratio get priority
            nw_to_s = safe_divide(NW2, S2, 0)
            
            pecking_order.append(FirmRank(NWtoS=nw_to_s, firm=firm))
        
        # Sort by ratio (descending)
        pecking_order.sort(key=lambda x: x.NWtoS, reverse=True)
        
        # Allocate credit in order
        TC2_available = self.read("_TC1free", 0)
        allocated_credit = 0.0
        allocations = []
        
        for rank in pecking_order:
            firm = rank.firm
            credit_demand = firm.read("_Deb2max", 0) - firm.read("_Deb2", 1)
            
            if credit_demand <= 0:
                continue
            
            # Allocate as much as possible
            credit_granted = min(credit_demand, TC2_available - allocated_credit)
            
            if credit_granted > 0:
                allocations.append((firm, credit_granted))
                allocated_credit += credit_granted
            
            if allocated_credit >= TC2_available:
                break
        
        # Update free credit
        TC2_free = TC2_available - allocated_credit
        self.write("_TC2free", TC2_free)
        self._TC2free = TC2_free
        
        self.write("_CD2b", min(sector_demand, allocated_credit))
        self._CD2b = min(sector_demand, allocated_credit)
        
        return allocated_credit, allocations
    
    def compute_interest_rate(self, r: float, spread: float) -> float:
        """
        Compute interest rate on loans
        
        Args:
            r: Base interest rate (central bank rate)
            spread: Bank spread over base rate
        
        Returns:
            Interest rate on loans
        """
        iB = r + spread
        
        self.write("_iB", iB)
        self._iB = iB
        return iB
    
    def compute_deposit_rate(self, r: float, spread_deposit: float) -> float:
        """
        Compute interest rate on deposits
        
        Args:
            r: Base interest rate
            spread_deposit: Deposit rate spread (typically negative)
        
        Returns:
            Interest rate on deposits
        """
        iDb = max(0, r + spread_deposit)
        
        self.write("_iDb", iDb)
        self._iDb = iDb
        return iDb
    
    def compute_profits(self) -> float:
        """
        Compute bank profits
        
        Profits come from:
        - Interest on loans
        - Interest on bonds
        Minus:
        - Interest on deposits
        - Interest on central bank loans
        - Bad debts
        
        Returns:
            Gross profits
        """
        # Interest income
        Loans = self.read("_Loans", 1)
        iB = self.read("_iB", 1)
        interest_income = Loans * iB
        
        # Bond income
        BondsB = self.read("_BondsB", 1)
        iBonds = self.parent.read("iBonds", 1) if self.parent else 0.02
        bond_income = BondsB * iBonds
        
        # Interest expenses
        Depo = self.read("_Depo", 1)
        iDb = self.read("_iDb", 1)
        deposit_expense = Depo * iDb
        
        LoansCB = self.read("_LoansCB", 1)
        r = self.parent.read("r", 1) if self.parent else 0.03
        cb_expense = LoansCB * r
        
        # Bad debts
        BadDeb1 = self.read("_BadDeb1", 0)
        BadDeb2 = self.read("_BadDeb2", 0)
        
        # Total profits
        PiB = interest_income + bond_income - deposit_expense - cb_expense - BadDeb1 - BadDeb2
        
        self.write("_PiB", PiB)
        self._PiB = PiB
        return PiB
    
    def update_balance_sheet(self):
        """
        Update bank balance sheet components
        """
        # Assets
        Loans = self.read("_Loans", 0)
        Res = self.read("_Res", 0)
        BondsB = self.read("_BondsB", 0)
        total_assets = Loans + Res + BondsB
        
        # Liabilities
        Depo = self.read("_Depo", 0)
        LoansCB = self.read("_LoansCB", 0)
        total_liabilities = Depo + LoansCB
        
        # Net worth (equity)
        NWb = total_assets - total_liabilities
        
        self.write("_NWb", NWb)
        self._NWb = NWb
    
    def compute_reserves(self, lambda_val: float) -> Tuple[float, float]:
        """
        Compute required and excess reserves
        
        Args:
            lambda_val: Reserve requirement ratio
        
        Returns:
            Tuple of (total_reserves, excess_reserves)
        """
        Depo = self.read("_Depo", 0)
        required_reserves = lambda_val * Depo
        
        # Assume bank holds required reserves plus some buffer
        Res = required_reserves * 1.1  # 10% buffer
        ExRes = Res - required_reserves
        
        self.write("_Res", Res)
        self.write("_ExRes", ExRes)
        self._Res = Res
        self._ExRes = ExRes
        
        return Res, ExRes
    
    def compute_market_share(self) -> float:
        """
        Compute bank market share based on number of clients
        
        Returns:
            Market share
        """
        Cl = self.read("_Cl", 0)
        
        # Sum all banks' clients
        total_clients = 0
        for bank in self.parent.get_children("Bank"):
            total_clients += bank.read("_Cl", 0)
        
        fB = safe_divide(Cl, total_clients, 0.0)
        
        self.write("_fB", fB)
        self._fB = fB
        return fB
    
    def check_bankruptcy(self) -> bool:
        """
        Check if bank is bankrupt (negative net worth)
        
        Returns:
            True if bankrupt
        """
        return self._NWb < 0
    
    def initialize(self, params: dict):
        """
        Initialize bank with parameters
        
        Args:
            params: Dictionary with initialization values
        """
        self._IDb = params.get('bank_id', 0)
        self._NWb = params.get('NWb', 10.0)
        self._Depo = params.get('Depo', 50.0)
        self._Loans = params.get('Loans', 40.0)
        self._Cl = params.get('Cl', 10)
        
        # Write initial values
        self.write("_IDb", self._IDb)
        self.write("_NWb", self._NWb)
        self.write("_Depo", self._Depo)
        self.write("_Loans", self._Loans)
        self.write("_Cl", self._Cl)
        
        # Initialize reserves
        self.compute_reserves(params.get('lambda', 0.05))
