"""
Bank Agent Class
Represents banks in the financial sector
"""

from typing import List, Dict, Any, Optional
from utils.data_structures import TimeSeriesData, FirmRank


class Bank:
    """
    Bank agent in the K+S model
    Banks collect deposits, provide loans, manage credit limits
    """
    
    def __init__(self, bank_id: int, config: Dict[str, Any]):
        # Identity
        self.id = bank_id
        self._IDb = bank_id
        
        # Configuration
        self.config = config
        
        # Market share
        self._fB = 0.0                  # market share
        self._fD = 0.0                  # deposit market share
        
        # Assets and liabilities
        self._NWb = 0.0                 # net worth (equity)
        self._Depo = 0.0                # total deposits
        self._Loans = 0.0               # total loans
        self._Res = 0.0                 # reserves at central bank
        self._ExRes = 0.0               # excess reserves
        self._BondsB = 0.0              # government bonds held
        self._LoansCB = 0.0             # loans from central bank
        
        # Credit management
        self._TC = 0.0                  # total credit supply capacity
        self._TC1free = 0.0             # available credit for sector 1
        self._TC2free = 0.0             # available credit for sector 2
        self._BadDeb1 = 0.0             # bad debt from sector 1
        self._BadDeb2 = 0.0             # bad debt from sector 2
        
        # Financial results
        self._PiB = 0.0                 # bank profits
        self._DivB = 0.0                # dividends paid
        self._TaxB = 0.0                # taxes paid
        self._Gbail = 0.0               # government bail-out received
        
        # Interest rates
        self._iB = 0.0                  # average interest rate on loans
        self._iDb = 0.0                 # interest rate on deposits
        
        # Credit allocation
        self._CD1b = 0.0                # credit demand from sector 1
        self._CD2b = 0.0                # credit demand from sector 2
        self._BD = 0.0                  # bad debt
        self._Bda = 0.0                 # deposits adjustment
        self._Cl = 0.0                  # credit limit indicator
        
        # Client lists
        self.clients_sector1 = []       # Firm1 clients
        self.clients_sector2 = []       # Firm2 clients
        self.client_scores = []         # Credit scores for pecking order
        
        # History
        self.history = {
            'NWb': TimeSeriesData('net_worth'),
            'Loans': TimeSeriesData('loans'),
            'Depo': TimeSeriesData('deposits'),
            'PiB': TimeSeriesData('profits')
        }
    
    def compute_credit_supply(self, lambda_param: float, lambda0: float,
                             tau_b: float, flag_credit_rule: int) -> float:
        """
        Compute total credit supply capacity
        
        Args:
            lambda_param: credit multiple
            lambda0: minimum credit floor
            tau_b: capital adequacy ratio
            flag_credit_rule: credit rule flag
        
        Returns:
            Total credit supply capacity
        """
        if flag_credit_rule == 0:
            # No bank-level credit limit
            self._TC = float('inf')
            self._TC1free = float('inf')
            self._TC2free = float('inf')
        elif flag_credit_rule == 1:
            # Deposit multiplier
            self._TC = max(lambda_param * self._Depo, lambda0)
            self._TC1free = self._TC / 2  # Split equally
            self._TC2free = self._TC / 2
        else:  # flag_credit_rule == 2
            # Basel-like capital adequacy
            if tau_b > 0 and tau_b < 1:
                max_loans = self._NWb / tau_b
                self._TC = max(max_loans - self._Loans, 0.0)
            else:
                self._TC = max(lambda_param * self._Depo, lambda0)
            
            # Allocate to sectors proportionally
            total_loans = self._Loans
            if total_loans > 0:
                loans1 = sum(c.debt for c in self.clients_sector1)
                loans2 = sum(c.debt for c in self.clients_sector2)
                if loans1 + loans2 > 0:
                    self._TC1free = self._TC * loans1 / (loans1 + loans2)
                    self._TC2free = self._TC * loans2 / (loans1 + loans2)
                else:
                    self._TC1free = self._TC / 2
                    self._TC2free = self._TC / 2
            else:
                self._TC1free = self._TC / 2
                self._TC2free = self._TC / 2
        
        return self._TC
    
    def rank_clients(self, sector: int) -> List[FirmRank]:
        """
        Rank clients by net-wealth-to-sales ratio (pecking order)
        
        Args:
            sector: 1 or 2 for capital/consumption sector
        
        Returns:
            Sorted list of FirmRank objects
        """
        clients = self.clients_sector1 if sector == 1 else self.clients_sector2
        rankings = []
        
        for client in clients:
            if hasattr(client, '_S1' if sector == 1 else '_S2'):
                sales = getattr(client, '_S1' if sector == 1 else '_S2', 1.0)
                nw = getattr(client, '_NW1' if sector == 1 else '_NW2', 0.0)
                
                if sales > 0:
                    nw_to_s = nw / sales
                else:
                    nw_to_s = 0.0
                
                rankings.append(FirmRank(nw_to_s=nw_to_s, firm=client))
        
        # Sort in descending order of NW/S ratio
        rankings.sort(key=lambda x: x.nw_to_s, reverse=True)
        return rankings
    
    def allocate_credit(self, sector: int, requested_credit: Dict[Any, float]) -> Dict[Any, float]:
        """
        Allocate credit to firms according to pecking order
        
        Args:
            sector: 1 or 2
            requested_credit: Dict mapping firm to requested credit amount
        
        Returns:
            Dict mapping firm to allocated credit amount
        """
        rankings = self.rank_clients(sector)
        available = self._TC1free if sector == 1 else self._TC2free
        allocated = {}
        
        for rank in rankings:
            firm = rank.firm
            if firm in requested_credit:
                request = requested_credit[firm]
                if request <= available:
                    allocated[firm] = request
                    available -= request
                elif available > 0:
                    allocated[firm] = available
                    available = 0.0
                else:
                    allocated[firm] = 0.0
        
        # Update available credit
        if sector == 1:
            self._TC1free = available
        else:
            self._TC2free = available
        
        return allocated
    
    def grant_loan(self, amount: float, sector: int):
        """Grant a loan"""
        self._Loans += amount
        if sector == 1:
            self._TC1free = max(0, self._TC1free - amount)
        else:
            self._TC2free = max(0, self._TC2free - amount)
    
    def repay_loan(self, amount: float):
        """Repay a loan"""
        self._Loans = max(0, self._Loans - amount)
    
    def accept_deposit(self, amount: float):
        """Accept a deposit"""
        self._Depo += amount
    
    def withdraw_deposit(self, amount: float):
        """Withdraw from deposits"""
        self._Depo = max(0, self._Depo - amount)
    
    def write_off_bad_debt(self, amount: float, sector: int):
        """Write off bad debt"""
        if sector == 1:
            self._BadDeb1 += amount
        else:
            self._BadDeb2 += amount
        self._BD += amount
        self._NWb -= amount  # Reduce net worth
    
    def compute_profits(self, r_deb: float, r_d: float, r_bonds: float) -> float:
        """
        Compute bank profits
        
        Args:
            r_deb: interest rate on loans
            r_d: interest rate on deposits
            r_bonds: interest rate on bonds
        
        Returns:
            Bank profits
        """
        # Interest income from loans
        interest_income = self._Loans * r_deb
        
        # Interest income from bonds
        bond_income = self._BondsB * r_bonds
        
        # Interest paid on deposits
        interest_expense = self._Depo * r_d
        
        # Net interest income
        net_interest = interest_income + bond_income - interest_expense
        
        # Subtract bad debt losses
        self._PiB = net_interest - self._BD
        
        return self._PiB
    
    def pay_dividends(self, dividend_rate: float):
        """Pay dividends on profits"""
        if self._PiB > 0:
            self._DivB = self._PiB * dividend_rate
            self._NWb += self._PiB - self._DivB - self._TaxB
        else:
            self._DivB = 0.0
            self._NWb += self._PiB  # Losses reduce net worth
    
    def needs_bailout(self) -> bool:
        """Check if bank needs government bailout"""
        return self._NWb < 0
    
    def receive_bailout(self, amount: float):
        """Receive government bailout"""
        self._Gbail = amount
        self._NWb += amount
    
    def update_history(self):
        """Update historical values"""
        self.history['NWb'].append(self._NWb)
        self.history['Loans'].append(self._Loans)
        self.history['Depo'].append(self._Depo)
        self.history['PiB'].append(self._PiB)
    
    def __repr__(self):
        return f"Bank(id={self.id}, NW={self._NWb:.0f}, Loans={self._Loans:.0f}, Deposits={self._Depo:.0f})"
