"""
Financial Market

Implements banking and credit allocation:
- Bank-firm relationships
- Credit demand and supply
- Credit rationing using pecking order
- Basel-like capital adequacy constraints
"""

import numpy as np
from typing import List


class FinancialMarket:
    """
    Financial market coordinating banks and firms
    """
    
    def __init__(self, params, banks: List, firms1: List, firms2: List):
        """
        Initialize financial market
        
        Args:
            params: Parameters object
            banks: List of Bank objects
            firms1: List of Firm1 objects
            firms2: List of Firm2 objects
        """
        self.params = params
        self.banks = banks
        self.firms1 = firms1
        self.firms2 = firms2
        
        # Market statistics
        self.total_credit_demand = 0.0
        self.total_credit_supply = 0.0
        self.total_credit_granted = 0.0
    
    def assign_banks_to_firms(self, firms1: List, firms2: List, banks: List):
        """
        Assign banks to firms using market share distribution
        """
        if len(banks) == 0:
            return
        
        alphaB = self.params.get('alphaB', 2.0)  # Pareto shape parameter
        
        # Calculate market shares for banks using bounded Pareto
        bank_shares = []
        for bank in banks:
            # Draw from bounded Pareto [2, (F1+F2)/2]
            max_clients = (len(firms1) + len(firms2)) / 2
            share = self._bounded_pareto(alphaB, 2, max_clients)
            bank_shares.append(share)
        
        # Normalize to market shares
        total = sum(bank_shares)
        bank_shares = [s / total for s in bank_shares]
        
        # Assign firms to banks
        all_firms = firms1 + firms2
        np.random.shuffle(all_firms)  # Random allocation
        
        # Assign firms proportionally to bank shares
        cumulative_shares = np.cumsum(bank_shares)
        
        for i, firm in enumerate(all_firms):
            # Select bank based on cumulative shares
            r = np.random.random()
            bank_idx = next((i for i, cs in enumerate(cumulative_shares) if r <= cs), len(banks)-1)
            
            bank = banks[bank_idx]
            firm.bank = bank
            
            if firm in firms1:
                bank.clients_firm1.append(firm)
            else:
                bank.clients_firm2.append(firm)
        
        # Set market share desired for each bank
        for bank, share in zip(banks, bank_shares):
            bank.market_share_desired = share
    
    def _bounded_pareto(self, alpha: float, min_val: float, max_val: float) -> float:
        """
        Draw from bounded Pareto distribution
        """
        u = np.random.random()
        if alpha == 1:
            return min_val * np.exp(u * np.log(max_val / min_val))
        else:
            return min_val * (1 - u + u * (min_val / max_val) ** (alpha - 1)) ** (1 / (1 - alpha))
    
    def update_interest_rates(self, prime_rate: float):
        """
        Update interest rate structure for all banks
        """
        for bank in self.banks:
            bank.update_interest_rates(prime_rate)
    
    def process_credit_requests(self, t: int):
        """
        Process credit requests from firms
        """
        # Firms determine credit needs
        self._determine_credit_demand(t)
        
        # Banks collect deposits
        for bank in self.banks:
            bank.collect_deposits(t)
        
        # Banks determine credit supply
        for bank in self.banks:
            bank.determine_credit_supply(t)
        
        # Allocate credit
        for bank in self.banks:
            all_clients = bank.clients_firm1 + bank.clients_firm2
            bank.allocate_credit(t, all_clients)
        
        # Calculate statistics
        self.total_credit_demand = sum(
            getattr(f, '_CD2', 0) for f in self.firms1 + self.firms2
        )
        self.total_credit_supply = sum(b.credit_supply for b in self.banks)
        self.total_credit_granted = sum(b.loans for b in self.banks)
    
    def _determine_credit_demand(self, t: int):
        """
        Firms determine their credit needs
        """
        # Firm1 credit demand (for production)
        for firm in self.firms1:
            # Project wage bill based on labor demand and average wage
            projected_wage_bill = firm.labor_demand * firm.avg_wage if firm.labor_demand > 0 else 0
            
            # Need credit for wage bill and R&D
            cash_needed = projected_wage_bill + firm.rd_expenditure
            available_cash = max(firm.net_worth, 0)  # Use net worth as available cash
            
            credit_demand = max(0, cash_needed - available_cash)
            
            # Check prudential limit
            max_debt = self._calculate_max_debt(firm, 1)
            credit_demand = min(credit_demand, max_debt - firm.debt)
            
            firm._CD1 = max(0, credit_demand)
        
        # Firm2 credit demand (for production and investment)
        for firm in self.firms2:
            # Project wage bill based on labor demand and average wage
            projected_wage_bill = firm.labor_demand * firm.avg_wage if firm.labor_demand > 0 else 0
            
            # Need credit for wage bill
            cash_needed = projected_wage_bill
            
            # Add investment cost
            if firm.investment_desired > 0:
                # Find average price from Firm1 suppliers
                if self.firms1:
                    avg_price = np.mean([f.price for f in self.firms1])
                    m2 = self.params.get('m2', 1.0)
                    investment_cost = (firm.investment_desired / m2) * avg_price
                    cash_needed += investment_cost
            
            available_cash = max(firm.net_worth, 0)  # Use net worth as available cash
            credit_demand = max(0, cash_needed - available_cash)
            
            # Check prudential limit
            max_debt = self._calculate_max_debt(firm, 2)
            credit_demand = min(credit_demand, max_debt - firm.debt)
            
            firm._CD2 = max(0, credit_demand)
    
    def _calculate_max_debt(self, firm, sector: int) -> float:
        """
        Calculate maximum prudential debt for firm
        """
        Lambda = self.params.get('Lambda', 10.0)
        Lambda0 = self.params.get('Lambda0', 1.0)
        
        # Maximum based on net worth and sales
        max_debt = Lambda * max(firm.net_worth, firm.sales)
        
        # Absolute floor
        if sector == 1:
            pK0 = self.params.get('pK0', 1.0)
        else:
            pK0 = 1.0  # Consumption goods
        
        PPI = 1.0  # Producer price index (simplified)
        floor = Lambda0 * PPI / pK0
        
        return max(max_debt, floor)
    
    def update_credit_scores(self, t: int):
        """
        Banks update credit scores/classes for clients
        """
        for bank in self.banks:
            bank.update_credit_scores(t)
    
    def handle_bankruptcies(self, t: int):
        """
        Handle firm bankruptcies and loan defaults
        """
        # Check for negative net worth
        for firm in self.firms1 + self.firms2:
            if firm.net_worth < 0 and firm.debt > 0:
                if firm.bank:
                    firm.bank.handle_default(firm, firm.debt)
                    firm.debt = 0.0
    
    def check_bank_bailouts(self, t: int, central_bank, government):
        """
        Check if any banks need bailout
        """
        for bank in self.banks:
            if bank.check_bailout():
                central_bank.bailout_banks([bank], government)
