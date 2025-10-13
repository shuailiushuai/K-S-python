"""
Core utility functions for the K+S model
Includes random number generation, moving averages, and other support functions
"""

import numpy as np
from typing import Optional, List
from scipy.stats import beta as beta_dist


class RandomEngine:
    """
    Random number generator with fixed seed for reproducibility
    Matches the mt19937_64 engine used in the C++ implementation
    """
    
    def __init__(self, seed: int = 1):
        self.rng = np.random.Generator(np.random.MT19937(seed))
        
    def uniform(self, low: float = 0.0, high: float = 1.0) -> float:
        """Generate uniform random number in [low, high)"""
        return self.rng.uniform(low, high)
    
    def uniform_int(self, low: int, high: int) -> int:
        """Generate uniform random integer in [low, high]"""
        return self.rng.integers(low, high + 1)
    
    def beta(self, alpha: float, beta: float) -> float:
        """Generate beta-distributed random number"""
        return self.rng.beta(alpha, beta)
    
    def normal(self, mean: float = 0.0, std: float = 1.0) -> float:
        """Generate normal-distributed random number"""
        return self.rng.normal(mean, std)
    
    def choice(self, options: List, weights: Optional[List[float]] = None):
        """Choose randomly from options with optional weights"""
        if weights is not None:
            weights = np.array(weights)
            weights = weights / weights.sum()  # normalize
        return self.rng.choice(options, p=weights)
    
    def shuffle(self, array: List):
        """Shuffle array in place"""
        self.rng.shuffle(array)
        return array
    
    def seed(self, seed: int):
        """Reset seed"""
        self.rng = np.random.Generator(np.random.MT19937(seed))


def mov_avg_bound(values: List[float], periods: int, limit: float = 0.0) -> float:
    """
    Calculate bounded moving-average growth rate
    If limit is zero, there is no bounding
    
    Args:
        values: List of historical values (most recent first)
        periods: Number of periods for moving average
        limit: Bound for growth rate (0 = no limit)
    
    Returns:
        Moving average growth rate
    """
    sum_g = 0.0
    count = 0
    
    for i in range(min(periods, len(values) - 1)):
        if i + 1 < len(values):
            prev = values[i + 1]
            if prev != 0:
                g = values[i] / prev - 1
            else:
                g = 0.0
            
            # Apply bounds if specified
            if limit > 0:
                g = max(min(g, limit), -limit)
            
            sum_g += g
            count += 1
    
    return sum_g / count if count > 0 else 0.0


def round_value(value: float, reference: float, tolerance: float) -> float:
    """Round values too close to a reference"""
    if abs(value - reference) > tolerance:
        return value
    else:
        return reference


def weighted_average(values: List[float], weights: List[float]) -> float:
    """Calculate weighted average"""
    if len(values) == 0 or len(weights) == 0:
        return 0.0
    
    total_weight = sum(weights)
    if total_weight == 0:
        return 0.0
    
    return sum(v * w for v, w in zip(values, weights)) / total_weight


def vintage_id(t0: int, id_suppl: int) -> int:
    """
    Pack vintage (machine technological generation) data
    VNT macro from C++ code
    """
    return 10000 * int(t0) + int(id_suppl)


def vintage_t0(id_vint: int) -> int:
    """Extract t0 from vintage ID"""
    return int(id_vint) // 10000


def vintage_supplier(id_vint: int) -> int:
    """Extract supplier ID from vintage ID"""
    t0 = vintage_t0(id_vint)
    return int(id_vint) - 10000 * t0


class MovingAverage:
    """Helper class to maintain moving averages"""
    
    def __init__(self, periods: int):
        self.periods = periods
        self.values = []
    
    def add(self, value: float):
        """Add new value to moving average"""
        self.values.insert(0, value)
        if len(self.values) > self.periods:
            self.values.pop()
    
    def average(self) -> float:
        """Get current moving average"""
        if len(self.values) == 0:
            return 0.0
        return sum(self.values) / len(self.values)
    
    def growth_rate(self, limit: float = 0.0) -> float:
        """Get moving average growth rate"""
        return mov_avg_bound(self.values, self.periods, limit)


# Initial notional definitions (from C++ code)
INIPROD = 1.0   # initial notional machine productivity
INIWAGE = 1.0   # initial notional wage
INISKILL = 1.0  # initial notional worker skills


# Global random engine instance
# Will be initialized with seed from configuration
random_engine: Optional[RandomEngine] = None


def init_random_engine(seed: int):
    """Initialize global random engine with seed"""
    global random_engine
    random_engine = RandomEngine(seed)
    return random_engine


def get_random_engine() -> RandomEngine:
    """Get global random engine instance"""
    global random_engine
    if random_engine is None:
        random_engine = RandomEngine(1)
    return random_engine
