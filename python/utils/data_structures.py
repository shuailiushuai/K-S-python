"""
Data structures used in the K+S model
Corresponds to structs defined in fun_KS_class.h
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class Vintage:
    """Element of map of vintages (machine technological generation)"""
    s_v_p: float = 1.0              # public skills for vintage
    s_v_avg: float = 1.0            # average skills for vintage
    s_v_avg_lag: float = 1.0        # lagged average skills for vintage
    workers: int = 0                # current workers using this vintage


@dataclass
class FirmRank:
    """Element of pecking order rank for credit allocation"""
    nw_to_s: float = 0.0            # net-wealth-to-sales ratio
    firm: Any = None                # pointer to firm object


@dataclass
class WageOffer:
    """Element of wage offer list"""
    offer: float = 0.0              # wage offer value
    workers: int = 0                # number of workers in firm
    firm: Any = None                # pointer to firm object
    
    def __lt__(self, other):
        """For sorting by offer"""
        return self.offer < other.offer


@dataclass
class Application:
    """Element of job application list"""
    w: float = 0.0                  # wage request/offer
    s: float = 1.0                  # skills
    ws: float = 0.0                 # wage/skill ratio (payback)
    te: int = 0                     # tenure
    worker: Any = None              # pointer to worker object
    
    def __lt__(self, other):
        """For sorting applications"""
        return self.w < other.w


@dataclass
class CountryExtension:
    """Extensions to Country object for performance optimization"""
    # Speed-up vectors & maps
    bank_wgtd: List[float] = field(default_factory=list)       # market share cum. weights in banking
    firm2_wgtd: List[float] = field(default_factory=list)      # market share cum. weights in sector 2
    bank_ptr: List[Any] = field(default_factory=list)          # pointers to banks
    firm2_ptr: List[Any] = field(default_factory=list)         # pointers to firms in sector 2
    firm2_map: Dict[int, Any] = field(default_factory=dict)    # ID to pointer map for sector 2
    vint_prod: Dict[int, Vintage] = field(default_factory=dict) # vintage productivities & skills
    
    # Lists for job market
    firm2_wo: List[WageOffer] = field(default_factory=list)    # list of wage offers (sector 2)
    firm1_appl: List[Application] = field(default_factory=list) # sector 1 job applications


@dataclass
class Firm2Extension:
    """Extensions to Firm2 (consumption-good firm) object"""
    appl: List[Application] = field(default_factory=list)  # firm job applications


class LazyVariable:
    """
    Lazy-evaluated variable that caches its computed value
    Mimics LSD variable behavior
    """
    
    def __init__(self, compute_func=None, initial_value=None):
        self.compute_func = compute_func
        self._value = initial_value
        self._computed_t = -1
        self._history = []  # Store historical values
        
    def get(self, t: int, recalc: bool = False):
        """Get value at time t"""
        if recalc or self._computed_t != t:
            if self.compute_func:
                self._value = self.compute_func()
            self._computed_t = t
        return self._value
    
    def set(self, value, t: int = -1):
        """Set value"""
        self._value = value
        if t >= 0:
            self._computed_t = t
    
    def lag(self, periods: int = 1) -> Optional[float]:
        """Get lagged value"""
        if len(self._history) >= periods:
            return self._history[periods - 1]
        return None
    
    def update_history(self, t: int):
        """Update historical values at end of period"""
        if self._computed_t == t:
            self._history.insert(0, self._value)
            # Keep reasonable history length
            if len(self._history) > 20:
                self._history.pop()


class TimeSeriesData:
    """Store time series data for a variable"""
    
    def __init__(self, name: str):
        self.name = name
        self.data = []
        
    def append(self, value: float):
        """Add new value"""
        self.data.append(value)
    
    def get(self, lag: int = 0) -> Optional[float]:
        """Get value with lag (0 = current, 1 = previous, etc.)"""
        idx = len(self.data) - 1 - lag
        if 0 <= idx < len(self.data):
            return self.data[idx]
        return None
    
    def get_last_n(self, n: int) -> List[float]:
        """Get last n values"""
        return self.data[-n:] if len(self.data) >= n else self.data[:]
    
    def clear(self):
        """Clear all data"""
        self.data = []


# Comparison functions for sorting
def rank_desc_nw_to_s(e1: FirmRank, e2: FirmRank) -> bool:
    """Comparison for descending net-wealth-to-sales ratio"""
    return e1.nw_to_s > e2.nw_to_s


def wo_asc_wrk(e1: WageOffer, e2: WageOffer) -> bool:
    """Comparison for ascending number of workers"""
    return e1.workers < e2.workers


def wo_desc_off(e1: WageOffer, e2: WageOffer) -> bool:
    """Comparison for descending wage offer"""
    return e1.offer > e2.offer


def appl_asc_w(e1: Application, e2: Application) -> bool:
    """Comparison for ascending wage"""
    return e1.w < e2.w


def appl_desc_w(e1: Application, e2: Application) -> bool:
    """Comparison for descending wage"""
    return e1.w > e2.w


def appl_asc_s(e1: Application, e2: Application) -> bool:
    """Comparison for ascending skills"""
    return e1.s < e2.s


def appl_desc_s(e1: Application, e2: Application) -> bool:
    """Comparison for descending skills"""
    return e1.s > e2.s


def appl_asc_ws(e1: Application, e2: Application) -> bool:
    """Comparison for ascending wage/skill ratio"""
    return e1.ws < e2.ws


def appl_desc_ws(e1: Application, e2: Application) -> bool:
    """Comparison for descending wage/skill ratio"""
    return e1.ws > e2.ws


def appl_asc_te(e1: Application, e2: Application) -> bool:
    """Comparison for ascending tenure"""
    return e1.te < e2.te


def appl_desc_te(e1: Application, e2: Application) -> bool:
    """Comparison for descending tenure"""
    return e1.te > e2.te
