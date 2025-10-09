"""
Government and Central Bank Agents

Government:
- Collects taxes
- Pays unemployment benefits
- Provides worker training
- Manages public debt
- Bails out banks and workers

Central Bank:
- Sets prime interest rate (Taylor rule)
- Takes compulsory reserves
- Bails out failed banks
"""

import numpy as np
from typing import List


class Government:
    """
    Government agent
    
    Manages fiscal policy, taxes, transfers, and public debt.
    """
    
    def __init__(self, params):
        """
        Initialize government
        
        Args:
            params: Parameters object
        """
        self.params = params
        
        # Fiscal variables
        self.tax_revenue = 0.0
        self.tax_firm1 = 0.0
        self.tax_firm2 = 0.0
        self.tax_bank = 0.0
        self.tax_worker = 0.0
        
        # Expenditure
        self.expenditure = 0.0
        self.unemployment_benefits = 0.0
        self.training_expenditure = 0.0
        self.bailout_banks = 0.0
        self.bailout_workers = 0.0
        self.fixed_expenditure = 0.0
        
        # Fiscal balance
        self.deficit = 0.0
        self.public_debt = 0.0
        
        # Tax rate
        self.tax_rate = params.get('tr', 0.1)
    
    def collect_tax(self, amount: float, source: str):
        """
        Collect tax from a source
        
        Args:
            amount: Tax amount
            source: Tax source ('firm1', 'firm2', 'bank', 'worker')
        """
        if source == 'firm1':
            self.tax_firm1 += amount
        elif source == 'firm2':
            self.tax_firm2 += amount
        elif source == 'bank':
            self.tax_bank += amount
        elif source == 'worker':
            self.tax_worker += amount
    
    def collect_taxes(self, t: int):
        """
        Calculate total tax revenue
        """
        self.tax_revenue = (self.tax_firm1 + self.tax_firm2 + 
                           self.tax_bank + self.tax_worker)
        
        # Reset for next period
        self.tax_firm1 = 0.0
        self.tax_firm2 = 0.0
        self.tax_bank = 0.0
        self.tax_worker = 0.0
    
    def determine_expenditure(self, t: int, workers: List, central_bank):
        """
        Determine government expenditure
        """
        flagGovExp = self.params.get('flagGovExp', 2)
        w0min = self.params.get('w0min', 1.0)
        phi = self.params.get('phi', 0.5)  # Unemployment benefit ratio
        
        # Count unemployed workers
        unemployed = sum(1 for w in workers if not w.employed)
        
        # Average wage
        employed = [w for w in workers if w.employed]
        if employed:
            wAvg = np.mean([w.wage for w in employed])
        else:
            wAvg = w0min
        
        # Minimum subsistence income
        subsistence = unemployed * w0min
        
        # Unemployment benefits
        if flagGovExp >= 2:
            self.unemployment_benefits = phi * wAvg * unemployed
        else:
            self.unemployment_benefits = subsistence
        
        # Training expenditure
        self.training_expenditure = self._determine_training_expenditure(t, workers, wAvg)
        
        # Fixed government expenditure
        if flagGovExp >= 1:
            gG = self.params.get('gG', 0.0)  # Growth rate of fixed expenditure
            if t == 1:
                self.fixed_expenditure = subsistence
            else:
                self.fixed_expenditure *= (1 + gG)
        else:
            self.fixed_expenditure = 0.0
        
        # Interest on public debt
        if self.public_debt > 0:
            rBonds = central_bank.interest_rate_bonds
            interest_payment = rBonds * self.public_debt
        else:
            interest_payment = 0.0
        
        # Total expenditure
        self.expenditure = (self.unemployment_benefits + 
                           self.training_expenditure +
                           self.fixed_expenditure +
                           interest_payment +
                           self.bailout_banks +
                           self.bailout_workers)
        
        # Reset bailouts
        self.bailout_banks = 0.0
        self.bailout_workers = 0.0
    
    def _determine_training_expenditure(self, t: int, workers: List, wAvg: float) -> float:
        """
        Calculate expenditure on worker training
        """
        Gamma = self.params.get('Gamma', 0.0)  # Share of unemployed trained
        GammaCost = self.params.get('GammaCost', 0.1)  # Cost per worker
        
        unemployed = sum(1 for w in workers if not w.employed)
        workers_trained = int(Gamma * unemployed)
        
        # Provide training to selected workers
        unemployed_workers = [w for w in workers if not w.employed]
        if len(unemployed_workers) > 0:
            trained = np.random.choice(unemployed_workers, 
                                      size=min(workers_trained, len(unemployed_workers)),
                                      replace=False)
            for worker in trained:
                worker.receive_training()
        
        return workers_trained * GammaCost * wAvg
    
    def update_public_debt(self, t: int):
        """
        Update public debt based on deficit
        """
        # Calculate deficit
        self.deficit = self.expenditure - self.tax_revenue
        
        # Update debt
        self.public_debt += self.deficit
        
        # Apply fiscal rules if needed
        self._apply_fiscal_rules(t)
    
    def _apply_fiscal_rules(self, t: int):
        """
        Apply fiscal rules to control debt
        """
        flagFiscalRule = self.params.get('flagFiscalRule', 0)
        
        if flagFiscalRule == 0:
            # No fiscal rule
            return
        
        Trule = self.params.get('Trule', 50)  # Time to start enforcing rules
        
        if t < Trule:
            return
        
        # Get GDP (simplified - should be from statistics)
        GDP = self.params.get('GDPnom', 1.0)
        
        # Check debt and deficit rules
        DebRule = self.params.get('DebRule', 0.9)  # Max debt/GDP
        DefPrule = self.params.get('DefPrule', 0.03)  # Max deficit/GDP
        
        debt_ratio = self.public_debt / GDP if GDP > 0 else 0
        deficit_ratio = self.deficit / GDP if GDP > 0 else 0
        
        # Apply adjustments if rules are violated
        if debt_ratio > DebRule or deficit_ratio > DefPrule:
            # Adjust tax rate or cut expenditure
            deltaDeb = self.params.get('deltaDeb', 0.1)
            
            if flagFiscalRule in [3, 4]:  # Debt rule active
                # Pay down debt
                debt_payment = deltaDeb * (self.public_debt - DebRule * GDP)
                self.public_debt -= max(0, debt_payment)
    
    def bailout_bank(self, bank) -> float:
        """
        Bailout a failed bank
        
        Returns:
            Bailout amount
        """
        PhiB = self.params.get('PhiB', 0.1)  # Fraction of average bank equity
        
        # Calculate bailout as fraction of average bank size
        # Simplified: fixed amount
        bailout = abs(bank.equity) + PhiB * 100  # Placeholder
        
        bank.receive_bailout(bailout)
        self.bailout_banks += bailout
        
        return bailout
    
    def bailout_workers(self, workers: List) -> float:
        """
        Bailout workers with negative savings
        
        Returns:
            Bailout amount
        """
        bailout_total = 0.0
        
        for worker in workers:
            if worker.forced_savings < 0:
                bailout = abs(worker.forced_savings)
                worker.forced_savings = 0.0
                bailout_total += bailout
        
        self.bailout_workers += bailout_total
        return bailout_total


class CentralBank:
    """
    Central Bank agent
    
    Sets monetary policy and bails out banks.
    """
    
    def __init__(self, params):
        """
        Initialize central bank
        
        Args:
            params: Parameters object
        """
        self.params = params
        
        # Interest rates
        self.prime_rate = params.get('rT', 0.03)  # Target prime rate
        self.interest_rate_bonds = params.get('rT', 0.03)
        
        # Taylor rule parameters
        self.pi_target = params.get('piT', 0.02)  # Inflation target
        self.u_target = params.get('Ut', 0.05)  # Unemployment target
        self.gamma_pi = params.get('gammaPi', 1.5)  # Inflation sensitivity
        self.gamma_u = params.get('gammaU', 0.5)  # Unemployment sensitivity
    
    def update_interest_rate(self, stats, t: int):
        """
        Update prime interest rate using Taylor rule
        """
        if t < 2:
            return  # Need data from previous period
        
        # Get inflation and unemployment from statistics
        inflation = stats.get_last('inflation', 0.0)
        unemployment = stats.get_last('unemployment_rate', 0.0)
        
        # Taylor rule
        pi_gap = inflation - self.pi_target
        u_gap = unemployment - self.u_target
        
        # Interest rate adjustment
        rAdj = self.params.get('rAdj', 0.001)  # Minimum adjustment step
        
        delta_r = self.gamma_pi * pi_gap - self.gamma_u * u_gap
        
        # Apply adjustment with minimum step
        if abs(delta_r) > rAdj:
            self.prime_rate += np.sign(delta_r) * rAdj
        
        # Ensure non-negative
        self.prime_rate = max(0.001, self.prime_rate)
        
        # Update bonds rate
        muBonds = self.params.get('muBonds', 0.5)
        self.interest_rate_bonds = self.prime_rate * (1 - muBonds)
    
    def bailout_banks(self, banks: List, government):
        """
        Bailout failed banks
        """
        for bank in banks:
            if bank.check_bailout():
                government.bailout_bank(bank)
    
    def __repr__(self):
        return f"CentralBank(r={self.prime_rate:.4f})"
