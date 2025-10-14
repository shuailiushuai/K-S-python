"""
Firm1 (Capital-Good Firm) Agent Class
Produces machines/capital goods, invests in R&D for innovation
"""

from typing import List, Dict, Any, Optional
from utils.data_structures import TimeSeriesData
from utils.core_utils import get_random_engine, INIPROD


class Firm1:
    """
    Capital-good firm agent
    Produces machines through R&D, innovation and imitation
    """
    
    def __init__(self, firm_id: int, config: Dict[str, Any]):
        # Identity
        self.id = firm_id
        self._ID1 = firm_id
        
        # Configuration
        self.config = config
        
        # Market position
        self._f1 = 0.0                  # market share
        self._t1ent = 0                 # entry time
        
        # Technology
        self._Atau = INIPROD            # labor productivity (process innovation)
        self._Btau = INIPROD            # machine productivity (product innovation)
        
        # Production
        self._Q1 = 0.0                  # production (machines)
        self._Q1e = 0.0                 # effective production
        self._D1 = 0.0                  # demand
        self._S1 = 0.0                  # sales
        self._N1 = 0.0                  # inventories
        
        # Pricing and costs
        self._p1 = 1.0                  # price
        self._c1 = 1.0                  # unit cost
        self._w1avg = 1.0               # average wage
        
        # R&D
        self._RD = 0.0                  # R&D expenditure
        self._L1rd = 0                  # workers in R&D
        self._L1 = 0                    # total workers
        
        # Financial
        self._NW1 = 0.0                 # net worth (deposits)
        self._Deb1 = 0.0                # debt
        self._Eq1 = 0.0                 # equity
        self._Pi1 = 0.0                 # profits
        self._Div1 = 0.0                # dividends
        self._Tax1 = 0.0                # taxes
        self._Bon1 = 0.0                # bonuses paid to workers
        
        # Credit
        self._CD1 = 0.0                 # credit demanded
        self._CD1c = 0.0                # credit constrained amount
        self._CS1 = 0.0                 # credit supplied
        self._CS1a = 0.0                # available credit
        self._Deb1max = 0.0             # maximum debt limit
        
        # Client management
        self._NC = 0                    # number of clients (Firm2s)
        self.clients = []               # List of client firms
        self.brochures_sent = []        # Brochures sent to potential clients
        
        # Banking
        self.bank = None                # Associated bank
        self._bank1 = 0                 # Bank ID
        
        # Innovation tracking
        self._qc1 = 0                   # quality class (for stats)
        self._innov = False             # Innovation flag
        self._imit = False              # Imitation flag
        
        # Workers
        self.workers = []               # List of employed workers
        
        # History
        self.history = {
            'f1': TimeSeriesData('market_share'),
            'Atau': TimeSeriesData('productivity'),
            'p1': TimeSeriesData('price'),
            'Pi1': TimeSeriesData('profits')
        }
    
    def compute_rd_investment(self, nu: float) -> float:
        """
        Compute R&D investment
        
        Args:
            nu: Share of revenue for R&D
        
        Returns:
            R&D expenditure
        """
        revenue = self.history['f1'].get(1) * self._S1 if self.history['f1'].get(1) else 0
        self._RD = nu * revenue
        return self._RD
    
    def innovate(self, alpha1: float, beta1: float, xi: float, 
                 x1_inf: float, x1_sup: float, zeta1: float) -> bool:
        """
        Attempt innovation (process and product)
        
        Args:
            alpha1, beta1: Beta distribution parameters
            xi: Share of R&D in innovation
            x1_inf, x1_sup: Productivity change bounds
            zeta1: R&D elasticity
        
        Returns:
            True if innovation succeeded
        """
        rng = get_random_engine()
        
        # Innovation probability based on R&D
        if self._RD > 0:
            inn_prob = 1 - (1 - xi) ** (self._RD ** zeta1)
        else:
            inn_prob = 0.0
        
        if rng.uniform() < inn_prob:
            # Draw innovation magnitude from Beta distribution
            x = rng.beta(alpha1, beta1)
            # Scale to range [x1_inf, x1_sup]
            x_scaled = x1_inf + x * (x1_sup - x1_inf)
            
            # Update productivity
            self._Atau = self._Atau * (1 + x_scaled)
            self._Btau = self._Btau * (1 + x_scaled)
            
            self._innov = True
            return True
        
        self._innov = False
        return False
    
    def imitate(self, alpha2: float, beta2: float, xi: float,
                competitors: List['Firm1'], zeta2: float) -> bool:
        """
        Attempt imitation from competitors
        
        Args:
            alpha2, beta2: Beta distribution parameters
            xi: Share of R&D in innovation
            competitors: List of competitor firms
            zeta2: R&D elasticity for imitation
        
        Returns:
            True if imitation succeeded
        """
        if not competitors:
            return False
        
        rng = get_random_engine()
        
        # Imitation probability based on R&D
        if self._RD > 0:
            imit_prob = 1 - (1 - (1 - xi)) ** (self._RD ** zeta2)
        else:
            imit_prob = 0.0
        
        if rng.uniform() < imit_prob:
            # Find best competitor
            best_competitor = max(competitors, key=lambda f: f._Btau)
            
            # Draw imitation success from Beta distribution
            x = rng.beta(alpha2, beta2)
            
            # Move towards best competitor
            self._Atau = (1 - x) * self._Atau + x * best_competitor._Atau
            self._Btau = (1 - x) * self._Btau + x * best_competitor._Btau
            
            self._imit = True
            return True
        
        self._imit = False
        return False
    
    def compute_price(self, mu1: float) -> float:
        """
        Compute price using markup pricing
        
        Args:
            mu1: Markup rate
        
        Returns:
            Price
        """
        # Unit cost
        self._c1 = self._w1avg / (self._Btau * self.config.get('Capital.m1', 0.1))
        
        # Price with markup
        self._p1 = (1 + mu1) * self._c1
        
        return self._p1
    
    def update_market_share(self, all_firms: List['Firm1'], n1: int):
        """
        Update market share based on recent sales
        
        Args:
            all_firms: List of all firms in sector
            n1: Number of periods for market share calculation
        """
        # Get recent sales
        my_sales = sum(self.history['f1'].get_last_n(n1))
        total_sales = sum(sum(f.history['f1'].get_last_n(n1)) for f in all_firms)
        
        if total_sales > 0:
            self._f1 = my_sales / total_sales
        else:
            self._f1 = 1.0 / len(all_firms) if all_firms else 0.0
    
    def compute_demand(self) -> float:
        """Compute demand from clients"""
        self._D1 = sum(client.machine_orders.get(self, 0.0) for client in self.clients)
        return self._D1
    
    def plan_production(self) -> float:
        """
        Plan production based on orders and financing constraints
        This determines Q1 (planned production) from D1 (orders)
        considering available cash and credit
        
        Returns:
            Planned production Q1
        """
        # Get financing parameters
        D1 = self._D1  # Orders
        CS1a = getattr(self, '_CS1a', 0.0)  # Available credit supply
        NW1_prev = getattr(self, '_NW1', 0.0)  # Net worth (cash available)
        c1 = self._c1  # Unit cost
        p1 = self._p1  # Unit price
        RD = self._RD  # R&D costs to pay
        
        # Cash needed to fulfill orders and R&D
        cash_needed = D1 * (c1 - p1) + RD
        
        # Check financing
        if cash_needed <= 0 or cash_needed <= NW1_prev:
            # Can self-finance
            self._Q1 = D1
            cash_after = NW1_prev - cash_needed
            credit_needed = 0.0
        elif cash_needed <= NW1_prev + CS1a:
            # Can finance with available credit
            self._Q1 = D1
            cash_after = 0.0
            credit_needed = cash_needed - NW1_prev
        else:
            # Credit constrained - produce what we can afford
            import math
            self._Q1 = min(max(math.floor((NW1_prev + CS1a - RD) / c1), 0), D1)
            
            if self._Q1 == 0:
                if RD <= NW1_prev:
                    cash_after = NW1_prev - RD
                    credit_needed = 0.0
                else:
                    cash_after = 0.0
                    credit_needed = RD
            else:
                actual_cost = self._Q1 * c1 + RD
                if actual_cost <= NW1_prev:
                    cash_after = NW1_prev - actual_cost
                    credit_needed = 0.0
                else:
                    cash_after = 0.0
                    credit_needed = actual_cost - NW1_prev
        
        # Store provision for production
        self._NW1p = NW1_prev - cash_after + credit_needed
        
        return self._Q1
    
    def produce(self, m1: float) -> float:
        """
        Produce machines based on workers actually hired
        This calculates Q1e (effective production), not Q1 (planned production)
        
        Args:
            m1: Worker output scale
        
        Returns:
            Effective production quantity (Q1e)
        """
        # Calculate potential production from workers
        num_workers = len(self.workers) if hasattr(self, 'workers') else 0
        Q1p = num_workers * self._Btau * m1 if num_workers > 0 and self._Btau > 0 else 0.0
        
        # Effective production is minimum of planned and potential
        self._Q1e = min(self._Q1, Q1p) if hasattr(self, '_Q1') else Q1p
        return self._Q1e
    
    def compute_sales(self) -> float:
        """Compute sales (min of demand and available supply)"""
        # Use effective production Q1e, not planned Q1
        available = self._Q1e + self._N1  # Production + inventories
        self._S1 = min(self._D1, available)
        self._N1 = available - self._S1  # Update inventories
        return self._S1
    
    def compute_profits(self) -> float:
        """Compute profits"""
        revenue = self._S1 * self._p1
        wage_bill = sum(w._w for w in self.workers)
        rd_cost = self._RD
        interest = self._Deb1 * self.config.get('Financial.rDeb', 0.02)
        
        self._Pi1 = revenue - wage_bill - rd_cost - interest
        return self._Pi1
    
    def request_credit(self, amount: float):
        """Request credit from bank"""
        self._CD1 += amount
        if self.bank:
            self.bank._CD1b += amount
    
    def receive_credit(self, amount: float):
        """Receive credit from bank"""
        self._CS1 = amount
        self._Deb1 += amount
        self._NW1 += amount
    
    def repay_debt(self, amount: float):
        """Repay debt to bank"""
        amount = min(amount, self._Deb1)
        self._Deb1 -= amount
        self._NW1 -= amount
        if self.bank:
            self.bank.repay_loan(amount)
    
    def exit_market(self):
        """Firm exits market"""
        # Notify clients
        for client in self.clients:
            if hasattr(client, 'suppliers'):
                client.suppliers.remove(self)
        
        # Write off debt
        if self.bank and self._Deb1 > 0:
            self.bank.write_off_bad_debt(self._Deb1, sector=1)
        
        # Fire all workers
        for worker in self.workers:
            worker.fire()
    
    def update_history(self):
        """Update historical values"""
        self.history['f1'].append(self._f1)
        self.history['Atau'].append(self._Atau)
        self.history['p1'].append(self._p1)
        self.history['Pi1'].append(self._Pi1)
    
    def __repr__(self):
        return f"Firm1(id={self.id}, f1={self._f1:.3f}, A={self._Atau:.2f}, p={self._p1:.2f})"
