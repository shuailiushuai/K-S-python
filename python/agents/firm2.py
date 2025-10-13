"""
Firm2 (Consumption-Good Firm) Agent Class
Produces consumption goods using machines and labor
"""

from typing import List, Dict, Any, Optional
from utils.data_structures import TimeSeriesData, Firm2Extension
from utils.core_utils import INIPROD, get_random_engine


class Vintage:
    """Represents a vintage of machines in a firm's capital stock"""
    
    def __init__(self, vintage_id: int, productivity: float, price: float, 
                 n_machines: int, build_time: int):
        self.__IDvint = vintage_id
        self.__Avint = productivity
        self.__AeVint = productivity  # Effective productivity
        self.__nVint = n_machines
        self.__pVint = price
        self.__tVint = build_time
        self.__RSvint = 0  # Machines to scrap
        self.workers = []  # Workers using this vintage


class Firm2:
    """
    Consumption-good firm agent
    Combines capital and labor to produce consumption goods
    """
    
    def __init__(self, firm_id: int, config: Dict[str, Any]):
        # Identity
        self.id = firm_id
        self._ID2 = firm_id
        self._t2ent = 0
        self._postChg = False  # Pre/post regime change type
        
        # Configuration
        self.config = config
        
        # Market position
        self._f2 = 0.0  # Market share
        self._E = 0.0  # Competitiveness
        self._life2cycle = 0  # Life cycle stage
        
        # Technology and production
        self._A2 = INIPROD  # Average productivity
        self._A2p = INIPROD  # Planned productivity
        self._Q2 = 0.0  # Production
        self._Q2e = 0.0  # Effective production
        self._Q2u = 0.0  # Utilized production
        self._Q2d = 0.0  # Desired production
        
        # Capital stock
        self._K = 0.0  # Capital stock
        self._Kd = 0.0  # Desired capital
        self._EI = 0.0  # Expansion investment
        self._SI = 0.0  # Substitution investment
        self._CI = 0.0  # Canceled investment
        self._RSold = 0.0  # Scrapped capital
        
        # Demand and sales
        self._D2 = 0.0  # Demand
        self._D2e = 0.0  # Expected demand
        self._D2d = 0.0  # Desired demand
        self._S2 = 0.0  # Sales
        self._N = 0.0  # Inventories
        self._l2 = 0.0  # Unfilled demand
        
        # Pricing
        self._p2 = 1.0  # Price
        self._c2 = 1.0  # Unit cost
        self._c2e = 1.0  # Expected unit cost
        self._mu2 = 0.2  # Markup
        self._q2 = 1.0  # Quality
        
        # Labor
        self._L2 = 0  # Total workers
        self._L2d = 0  # Desired workers
        self._L2rd = 0  # Workers to hire/fire
        self._w2avg = 1.0  # Average wage
        self._w2o = 1.0  # Wage offer
        self._w2realAvg = 1.0  # Real average wage
        self._s2avg = 1.0  # Average skills
        self._sT2min = 1.0  # Minimum tenure skills
        
        # Financial
        self._NW2 = 0.0  # Net worth
        self._NW2p = 0.0  # Provisions
        self._Deb2 = 0.0  # Debt
        self._Eq2 = 0.0  # Equity
        self._Pi2 = 0.0  # Profits
        self._Div2 = 0.0  # Dividends
        self._Tax2 = 0.0  # Taxes
        self._Bon2 = 0.0  # Bonuses
        
        # Credit
        self._CD2 = 0.0
        self._CD2c = 0.0
        self._CS2 = 0.0
        self._CS2a = 0.0
        self._Deb2max = 0.0
        
        # Suppliers and orders
        self.supplier = None  # Current machine supplier
        self.suppliers = []  # Known suppliers
        self.machine_orders = {}  # Orders by supplier
        
        # Banking
        self.bank = None
        self._bank2 = 0
        
        # Workers and vintages
        self.workers = []
        self.vintages: List[Vintage] = []
        
        # Extensions
        self.ext = Firm2Extension()
        
        # Innovation
        self._qc2 = 0
        
        # History
        self.history = {
            'f2': TimeSeriesData('market_share'),
            'A2': TimeSeriesData('productivity'),
            'p2': TimeSeriesData('price'),
            'Pi2': TimeSeriesData('profits'),
            'D2': TimeSeriesData('demand')
        }
    
    def compute_expected_demand(self, flag_expect: int) -> float:
        """Compute expected demand based on past demand"""
        if flag_expect == 0:  # Myopic 1-period
            self._D2e = self.history['D2'].get(1) or 0.0
        elif flag_expect == 1:  # Myopic multi-period
            periods = [self.history['D2'].get(i) for i in range(1, 5)]
            valid = [d for d in periods if d is not None]
            self._D2e = sum(valid) / len(valid) if valid else 0.0
        else:
            # Simplified adaptive expectations
            lag1 = self.history['D2'].get(1) or 0.0
            self._D2e = lag1
        
        # Add animal spirits
        e0 = self.config.get(f'Consumption.e0{"Chg" if self._postChg else ""}', 1.0)
        potential_demand = self._K * self.config.get('Consumption.u', 0.8)
        self._D2e = (1 - e0) * self._D2e + e0 * potential_demand
        
        return self._D2e
    
    def compute_desired_production(self, iota: float) -> float:
        """Compute desired production including inventory target"""
        target_inventories = iota * self._D2e
        self._Q2d = self._D2e + target_inventories - self._N
        return max(self._Q2d, 0.0)
    
    def compute_desired_capital(self, m2: float, u: float) -> float:
        """Compute desired capital stock"""
        if self._A2 > 0:
            self._Kd = (self._Q2d / (self._A2 * u)) * m2
        else:
            self._Kd = self._K
        return self._Kd
    
    def plan_investment(self, eta: float, b: float) -> tuple:
        """
        Plan expansion and substitution investment
        
        Returns:
            (expansion_investment, substitution_investment)
        """
        # Expansion investment
        if self._Kd > self._K:
            self._EI = self._Kd - self._K
        else:
            self._EI = 0.0
        
        # Substitution investment (scrap old machines)
        self._SI = 0.0
        total_scrap = 0.0
        
        for vint in self.vintages:
            age = -vint.__tVint  # Age of vintage
            # Scrap if older than eta or payback period exceeded
            if age >= eta or (self.supplier and vint.__Avint / self.supplier._Btau < b):
                machines_to_scrap = vint.__nVint
                total_scrap += machines_to_scrap
                vint.__RSvint = -machines_to_scrap
        
        self._SI = total_scrap
        
        return self._EI, self._SI
    
    def produce(self, m2: float) -> float:
        """Produce consumption goods"""
        total_output = 0.0
        
        for vint in self.vintages:
            workers_in_vint = len(vint.workers)
            output = workers_in_vint * vint.__AeVint * m2
            total_output += output
        
        self._Q2 = total_output
        self._Q2e = total_output
        return self._Q2
    
    def compute_competitiveness(self, omega1: float, omega2: float, omega3: float) -> float:
        """Compute competitiveness index"""
        # Normalize components
        self._E = -omega1 * self._p2 - omega2 * (self._l2 / max(self._D2, 1)) + omega3 * self._q2
        return self._E
    
    def update_market_share(self, all_firms: List['Firm2'], chi: float):
        """Update market share using replicator dynamics"""
        # Average competitiveness
        if all_firms:
            e_avg = sum(f._E for f in all_firms) / len(all_firms)
        else:
            e_avg = self._E
        
        # Replicator dynamics
        if e_avg != 0:
            growth = chi * (self._E - e_avg) / abs(e_avg)
        else:
            growth = 0.0
        
        self._f2 = self._f2 * (1 + growth)
        self._f2 = max(0.0, min(1.0, self._f2))
    
    def compute_price(self, upsilon: float) -> float:
        """Update price based on markup"""
        # Adjust markup based on market share change
        f2_lag = self.history['f2'].get(1) or self._f2
        if f2_lag > 0:
            ms_change = (self._f2 - f2_lag) / f2_lag
            self._mu2 = self._mu2 * (1 + upsilon * ms_change)
        
        # Price based on unit cost and markup
        self._p2 = (1 + self._mu2) * self._c2
        return self._p2
    
    def compute_sales(self) -> float:
        """Compute sales"""
        available = self._Q2 + self._N
        self._S2 = min(self._D2, available)
        self._l2 = max(0.0, self._D2 - available)
        self._N = available - self._S2
        return self._S2
    
    def compute_profits(self) -> float:
        """Compute profits"""
        revenue = self._S2 * self._p2
        wage_bill = sum(w._w for w in self.workers)
        interest = self._Deb2 * self.config.get('Financial.rDeb', 0.02)
        
        self._Pi2 = revenue - wage_bill - interest
        return self._Pi2
    
    def should_exit(self, f2_min: float) -> bool:
        """Check if firm should exit"""
        return self._f2 < f2_min or self._NW2 < 0
    
    def update_history(self):
        """Update historical values"""
        self.history['f2'].append(self._f2)
        self.history['A2'].append(self._A2)
        self.history['p2'].append(self._p2)
        self.history['Pi2'].append(self._Pi2)
        self.history['D2'].append(self._D2)
    
    def __repr__(self):
        return f"Firm2(id={self.id}, f2={self._f2:.3f}, A={self._A2:.2f}, p={self._p2:.2f})"
