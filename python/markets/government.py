"""
Government and Central Bank Module
Implements fiscal policy, monetary policy, and public sector operations
"""

from typing import List, Dict, Any
import math


class Government:
    """
    Government fiscal operations for the K+S model
    Manages taxes, unemployment benefits, training, and public debt
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Government balance sheet
        self.public_debt = 0.0          # Deb
        self.deposits = 0.0              # DepoG
        self.deficit = 0.0               # Def
        self.primary_deficit = 0.0       # DefP
        
        # Flows
        self.tax_revenue = 0.0           # Tax
        self.expenditure = 0.0           # G
        self.training_cost = 0.0         # Gtrain
    
    def compute_expenditure(self, workers: List, labor_stats: Dict) -> float:
        """
        Compute government expenditure
        From fun_KS_country.h: G equation
        
        Args:
            workers: List of workers
            labor_stats: Labor market statistics (Ls, L, wAvg, etc.)
        
        Returns:
            Total government expenditure
        """
        flag_gov_exp = self.config.get('Country.flagGovExp', 2)
        flag_fiscal_rule = self.config.get('Country.flagFiscalRule', 0)
        
        # Unemployed workers
        unemployed = labor_stats.get('Ls', 0) - labor_stats.get('L', 0)
        
        # Base expenditure (unemployment benefits)
        if flag_gov_exp < 2:
            # Work-or-die + minimum income
            w0min = self.config.get('Labor.w0min', 1.0)
            base_exp = unemployed * w0min
        else:
            # Unemployment benefits
            wU = labor_stats.get('wU', 1.0)
            base_exp = unemployed * wU
        
        # Add worker training cost
        training = self.compute_training_cost(workers, labor_stats)
        self.training_cost = training
        base_exp += training
        
        # Additional expenditure based on growth
        if flag_gov_exp == 1:
            gG = self.config.get('Country.gG', 0.005)
            prev_training = labor_stats.get('Gtrain_prev', training)
            base_exp += (1 + gG) * (base_exp - prev_training)
        
        # Apply fiscal rule if applicable
        if self.deposits > 0:
            if flag_gov_exp == 3:
                # Spend accumulated surplus (limited to current deficit)
                prev_deficit = abs(min(self.deficit, 0))
                base_exp += min(self.deposits, prev_deficit)
        else:
            # Check fiscal rule constraints
            if flag_fiscal_rule > 0:
                base_exp = self._apply_fiscal_rule(base_exp, labor_stats)
        
        self.expenditure = base_exp
        return base_exp
    
    def compute_training_cost(self, workers: List, labor_stats: Dict) -> float:
        """
        Compute cost of training unemployed workers
        From fun_KS_labor.h: Gtrain equation
        """
        Ltrain = self._compute_workers_in_training(workers)
        GammaCost = self.config.get('Labor.GammaCost', 0.1)
        wAvg = labor_stats.get('wAvg', 1.0)
        
        return Ltrain * GammaCost * wAvg
    
    def _compute_workers_in_training(self, workers: List) -> int:
        """
        Compute number of workers in training
        From fun_KS_labor.h: Ltrain equation
        """
        Gamma = self.config.get('Labor.Gamma', 0)
        
        if Gamma <= 0:
            return 0
        
        # Count unemployed workers eligible for training
        eligible = 0
        for worker in workers:
            if worker._employed == 0:
                # Check if unemployment duration qualifies
                Tu = worker._Tu
                if Tu > 0 and Tu % Gamma == 0:  # Simplified eligibility
                    eligible += 1
        
        return eligible
    
    def _apply_fiscal_rule(self, base_exp: float, labor_stats: Dict) -> float:
        """
        Apply fiscal rule constraints to expenditure
        """
        Trule = self.config.get('Financial.Trule', 100)
        t = labor_stats.get('t', 0)
        
        if t < Trule:
            return base_exp  # No rule during warm-up
        
        DebRule = self.config.get('Financial.DebRule', 0.6)
        DefPrule = self.config.get('Financial.DefPrule', 0.03)
        
        prev_tax = labor_stats.get('Tax_prev', 0)
        prev_debt = self.public_debt
        prev_gdp = labor_stats.get('GDPnom_prev', 1.0)
        
        debt_to_gdp = prev_debt / prev_gdp if prev_gdp > 0 else 0
        
        flag_fiscal_rule = self.config.get('Country.flagFiscalRule', 0)
        
        # Check debt rule
        if flag_fiscal_rule > 2 and debt_to_gdp > DebRule:
            # Debt rule applies - must run surplus
            max_deficit = -0.01 * prev_gdp  # Small surplus required
        else:
            # Primary deficit rule
            max_deficit = DefPrule * prev_gdp
        
        # Limit expenditure
        max_exp = prev_tax + max_deficit
        
        return min(base_exp, max_exp)
    
    def collect_taxes(self, firms1: List, firms2: List, banks: List, 
                     workers: List) -> Dict[str, float]:
        """
        Collect taxes from all agents
        From fun_KS_country.h: Tax, TaxW, TaxDiv equations
        """
        tr = self.config.get('Country.tr', 0.1)
        tauT = self.config.get('Labor.tauT', 0.01)
        flag_tax = self.config.get('Country.flagTax', 0)
        
        # Wage taxes
        tax_wages = 0.0
        for worker in workers:
            if worker._employed > 0:
                wage_tax = worker._w * tauT
                worker._TaxW = wage_tax
                tax_wages += wage_tax
        
        # Firm and bank profit taxes
        tax_profits = 0.0
        
        if flag_tax > 0:
            # Tax on firms
            for firm in firms1:
                if hasattr(firm, '_Pi1') and firm._Pi1 > 0:
                    tax = firm._Pi1 * tr
                    firm._Tax1 = tax
                    tax_profits += tax
            
            for firm in firms2:
                if hasattr(firm, '_Pi2') and firm._Pi2 > 0:
                    tax = firm._Pi2 * tr
                    firm._Tax2 = tax
                    tax_profits += tax
            
            # Tax on banks
            for bank in banks:
                if hasattr(bank, '_PiB') and bank._PiB > 0:
                    tax = bank._PiB * tr
                    bank._TaxB = tax
                    tax_profits += tax
        
        # Dividend taxes (if applicable)
        tax_dividends = 0.0  # Simplified
        
        total_tax = tax_wages + tax_profits + tax_dividends
        self.tax_revenue = total_tax
        
        return {
            'total': total_tax,
            'wages': tax_wages,
            'profits': tax_profits,
            'dividends': tax_dividends
        }
    
    def update_public_debt(self, interest_rate: float):
        """
        Update public debt based on deficit and interest
        Deb(t) = Deb(t-1) + Def(t) + interest
        """
        self.deficit = self.expenditure - self.tax_revenue
        self.primary_deficit = self.deficit - (self.public_debt * interest_rate)
        
        # Update debt
        self.public_debt += self.deficit
        
        # Update deposits (if surplus)
        if self.deficit < 0:
            self.deposits += abs(self.deficit)
        else:
            # Use deposits to cover deficit if available
            if self.deposits > 0:
                coverage = min(self.deposits, self.deficit)
                self.deposits -= coverage


class CentralBank:
    """
    Central bank monetary policy operations
    Manages interest rates, reserves, and bank bailouts
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Policy variables
        self.prime_rate = config.get('Financial.rT', 0.01)
        self.target_inflation = config.get('Financial.piT', 0.0)
        self.target_unemployment = config.get('Financial.Ut', 0.015)
        
        # Central bank balance sheet
        self.reserves = 0.0
        self.loans_to_banks = 0.0
        self.profits = 0.0              # PiCB
    
    def update_prime_rate(self, inflation: float, unemployment: float, t: int):
        """
        Update prime interest rate using Taylor rule
        From fun_KS_financial.h: rT equation
        """
        Trule = self.config.get('Financial.Trule', 100)
        
        if t < Trule:
            # Keep initial rate during warm-up
            return self.prime_rate
        
        gammaPi = self.config.get('Financial.gammaPi', 0)
        gammaU = self.config.get('Financial.gammaU', 0)
        rAdj = self.config.get('Financial.rAdj', 0.0025)
        
        # Taylor rule: adjust based on inflation and unemployment gaps
        pi_gap = inflation - self.target_inflation
        u_gap = unemployment - self.target_unemployment
        
        adjustment = 0.0
        if gammaPi > 0:
            adjustment += gammaPi * pi_gap
        if gammaU > 0:
            adjustment -= gammaU * u_gap  # Negative because high U -> lower r
        
        # Smooth adjustment
        self.prime_rate += rAdj * adjustment
        
        # Keep rate non-negative
        self.prime_rate = max(self.prime_rate, 0.001)
        
        return self.prime_rate
    
    def compute_required_reserves(self, banks: List) -> float:
        """
        Compute required reserves for all banks
        """
        muRes = self.config.get('Financial.muRes', 1.0)
        
        total_required = 0.0
        for bank in banks:
            deposits = bank._Depo if hasattr(bank, '_Depo') else 0
            required = muRes * deposits
            bank._ResReq = required
            total_required += required
        
        return total_required
    
    def bailout_banks(self, banks: List) -> float:
        """
        Bailout insolvent banks
        From fun_KS_bank.h: bank bailout logic
        """
        PhiB = self.config.get('Financial.PhiB', 0.5)
        
        total_bailout = 0.0
        
        # Compute average bank size
        avg_size = sum(b._NWb for b in banks if hasattr(b, '_NWb')) / len(banks) if banks else 0
        
        for bank in banks:
            if hasattr(bank, '_NWb') and bank._NWb < 0:
                # Bank is insolvent, needs bailout
                bailout = PhiB * avg_size - bank._NWb
                bank._Gbail = bailout
                bank._NWb += bailout
                total_bailout += bailout
        
        return total_bailout
    
    def compute_profits(self, banks: List, government_debt: float) -> float:
        """
        Compute central bank profits
        """
        rRes = self.config.get('Financial.muRes', 0.01) * self.prime_rate
        rBonds = self.prime_rate + self.config.get('Financial.muBonds', 0)
        
        # Interest income from reserves and bonds
        interest_income = (self.reserves * rRes + 
                          government_debt * rBonds)
        
        # Interest expense on loans to banks
        interest_expense = self.loans_to_banks * self.prime_rate
        
        self.profits = interest_income - interest_expense
        
        return self.profits
