"""
Bank Agent

Banks in the K+S model:
- Collect deposits from firms and workers
- Provide loans to firms
- Subject to capital adequacy constraints (Basel-like rules)
- Use pecking order for credit allocation based on firm financial health
"""

import numpy as np
from typing import List, Dict


class Bank:
    """
    Bank agent
    
    Banks intermediate between depositors and borrowers,
    subject to regulatory constraints.
    """
    
    def __init__(self, bank_id: int, params, initial_equity: float):
        """
        Initialize a bank
        
        Args:
            bank_id: Unique identifier
            params: Parameters object
            initial_equity: Initial bank equity
        """
        self.bank_id = bank_id
        self.params = params
        
        # Financial variables
        self.equity = initial_equity
        self.deposits = 0.0
        self.reserves = 0.0
        self.loans = 0.0
        self.bad_debt = 0.0
        self.profit = 0.0
        
        # Interest rates
        self.interest_rate_deposits = 0.01
        self.interest_rate_debt = 0.05
        self.interest_rate_reserves = 0.02
        
        # Clients
        self.clients_firm1 = []  # List of Firm1 clients
        self.clients_firm2 = []  # List of Firm2 clients
        self.market_share_desired = 0.0
        
        # Credit allocation
        self.credit_supply = 0.0
        self.credit_demand = 0.0
    
    def update_interest_rates(self, prime_rate: float):
        """
        Update interest rate structure based on central bank prime rate
        """
        muD = self.params.get('muD', 0.5)  # Deposit markdown
        muDeb = self.params.get('muDeb', 0.5)  # Debt markup
        muRes = self.params.get('muRes', 0.9)  # Reserves markdown
        
        self.interest_rate_deposits = prime_rate * (1 - muD)
        self.interest_rate_debt = prime_rate * (1 + muDeb)
        self.interest_rate_reserves = prime_rate * (1 - muRes)
    
    def collect_deposits(self, t: int):
        """
        Collect deposits from firms and workers
        """
        # Deposits = fraction of worker savings + positive firm net worth
        fD = self.market_share_desired  # Market share
        
        # Worker deposits (through savings account)
        worker_savings = self.params.get('total_worker_savings', 0.0)
        
        # Firm deposits (positive net worth)
        firm_deposits = 0.0
        for firm in self.clients_firm1 + self.clients_firm2:
            if firm.net_worth > 0:
                firm_deposits += firm.net_worth
        
        self.deposits = fD * worker_savings + firm_deposits
        
        # Reserves as fraction of deposits
        reserve_requirement = 0.0  # Simplified (can add reserve requirements)
        self.reserves = reserve_requirement * self.deposits
    
    def determine_credit_supply(self, t: int):
        """
        Determine total credit supply based on capital adequacy
        """
        flagCreditRule = self.params.get('flagCreditRule', 2)
        
        if flagCreditRule == 0:
            # No bank-level credit limit
            self.credit_supply = np.inf
        
        elif flagCreditRule == 1:
            # Deposits multiplier
            Lambda = self.params.get('Lambda', 10.0)
            self.credit_supply = Lambda * self.deposits
        
        else:  # flagCreditRule == 2
            # Basel-like capital adequacy
            tauB = self.params.get('tauB', 0.08)  # Minimum capital ratio
            
            # Maximum loans based on capital
            max_loans = self.equity / tauB
            
            # Available new credit
            self.credit_supply = max(0, max_loans - self.loans)
    
    def allocate_credit(self, t: int, firms: List):
        """
        Allocate credit to firms using pecking order
        
        Firms are ranked by their net-worth-to-sales ratio,
        and credit is allocated in order until supply is exhausted.
        """
        # Rank firms by financial health (NW/Sales ratio)
        firm_scores = []
        for firm in firms:
            if firm.sales > 0:
                score = firm.net_worth / firm.sales
            else:
                score = firm.net_worth  # Use net worth if no sales
            
            firm_scores.append({
                'firm': firm,
                'score': score,
                'credit_demand': getattr(firm, '_CD2', 0) if hasattr(firm, '_CD2') else 0
            })
        
        # Sort by score (descending - best firms first)
        firm_scores.sort(key=lambda x: x['score'], reverse=True)
        
        # Allocate credit in pecking order
        remaining_credit = self.credit_supply
        
        for item in firm_scores:
            firm = item['firm']
            demand = item['credit_demand']
            
            if demand > 0:
                # Grant credit up to demand or remaining supply
                credit_granted = min(demand, remaining_credit)
                
                # Update firm loan
                firm.debt += credit_granted
                firm.deposits += credit_granted
                
                # Update bank
                self.loans += credit_granted
                remaining_credit -= credit_granted
                
                # Mark if firm was credit constrained
                if credit_granted < demand:
                    if hasattr(firm, '_CD2c'):
                        firm._CD2c = demand - credit_granted
    
    def update_credit_scores(self, t: int):
        """
        Update credit class scores for clients (4 classes)
        """
        # Combine all clients
        all_clients = self.clients_firm1 + self.clients_firm2
        
        if len(all_clients) == 0:
            return
        
        # Rank by NW/Sales ratio
        scores = []
        for firm in all_clients:
            if firm.sales > 0:
                nw_to_sales = firm.net_worth / firm.sales
            else:
                nw_to_sales = firm.net_worth
            
            scores.append({
                'firm': firm,
                'score': nw_to_sales
            })
        
        # Sort by score
        scores.sort(key=lambda x: x['score'], reverse=True)
        
        # Assign credit classes (1=best, 4=worst)
        n = len(scores)
        for i, item in enumerate(scores):
            if i < n * 0.25:
                credit_class = 1
            elif i < n * 0.5:
                credit_class = 2
            elif i < n * 0.75:
                credit_class = 3
            else:
                credit_class = 4
            
            # Store in firm (with sector suffix)
            if item['firm'] in self.clients_firm1:
                item['firm'].credit_class = credit_class
            else:
                item['firm'].credit_class = credit_class
    
    def handle_default(self, firm, debt_amount: float):
        """
        Handle firm default on loans
        """
        self.bad_debt += debt_amount
        self.loans -= debt_amount
        
        # Write off against equity
        self.equity -= debt_amount
    
    def calculate_profit(self, t: int):
        """
        Calculate bank profit
        """
        # Interest income from loans
        interest_income = self.interest_rate_debt * self.loans
        
        # Interest paid on deposits
        interest_expense_deposits = self.interest_rate_deposits * self.deposits
        
        # Interest income from reserves
        interest_income_reserves = self.interest_rate_reserves * self.reserves
        
        # Net interest income
        net_interest = (interest_income + interest_income_reserves - 
                       interest_expense_deposits)
        
        # Subtract bad debt losses
        self.profit = net_interest - self.bad_debt
        
        # Reset bad debt for next period
        self.bad_debt = 0.0
    
    def pay_taxes(self, t: int, government):
        """
        Pay taxes on profit
        """
        tr = self.params.get('tr', 0.1)
        
        if self.profit > 0:
            tax = tr * self.profit
            self.profit -= tax
            government.collect_tax(tax, 'bank')
    
    def pay_dividends(self, t: int):
        """
        Pay dividends and update equity
        """
        dB = self.params.get('dB', 0.5)  # Dividend rate
        
        if self.profit > 0:
            dividends = dB * self.profit
            retained = self.profit - dividends
            
            # Update equity
            self.equity += retained
    
    def check_bailout(self) -> bool:
        """
        Check if bank needs bailout (negative equity)
        """
        return self.equity < 0
    
    def receive_bailout(self, bailout_amount: float):
        """
        Receive bailout from central bank
        """
        self.equity += bailout_amount
    
    def __repr__(self):
        return (f"Bank(id={self.bank_id}, equity={self.equity:.1f}, "
                f"loans={self.loans:.1f}, clients={len(self.clients_firm1 + self.clients_firm2)})")
