"""
Support Functions
Utility functions matching the C++ fun_KS_support.h implementations
"""

import math
from typing import List, Optional, Tuple
from .random_engine import random_engine


def round_value(v: float, ref: float, tol: float) -> float:
    """Round values too close to a reference"""
    return v if abs(v - ref) > tol else ref


def pack_vintage(t0: int, id_suppl: int) -> int:
    """
    Pack vintage (machine technological generation) data
    Combines time period and supplier ID into single integer
    """
    return t0 * 1000000 + id_suppl


def unpack_vintage(vnt: int) -> Tuple[int, int]:
    """
    Unpack vintage data
    Returns (time period, supplier ID)
    """
    t0 = vnt // 1000000
    id_suppl = vnt % 1000000
    return t0, id_suppl


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division with default value if denominator is zero"""
    return numerator / denominator if abs(denominator) > 1e-10 else default


def moving_average(values: List[float], periods: int) -> float:
    """
    Calculate moving average over specified number of periods
    
    Args:
        values: List of values (most recent first)
        periods: Number of periods to average
        
    Returns:
        Moving average
    """
    if not values or periods <= 0:
        return 0.0
    
    n = min(len(values), periods)
    return sum(values[:n]) / n


def growth_rate(current: float, previous: float, cap: Optional[float] = None) -> float:
    """
    Calculate growth rate with optional cap
    
    Args:
        current: Current value
        previous: Previous value
        cap: Optional absolute cap on growth rate
        
    Returns:
        Growth rate
    """
    if abs(previous) < 1e-10:
        return 0.0
    
    g = (current - previous) / previous
    
    if cap is not None and cap > 0:
        g = max(min(g, cap), -cap)
    
    return g


def logistic(x: float, center: float = 0.0, steepness: float = 1.0) -> float:
    """
    Logistic function
    
    Args:
        x: Input value
        center: Center point
        steepness: Steepness parameter
        
    Returns:
        Logistic function value in [0, 1]
    """
    return 1.0 / (1.0 + math.exp(-steepness * (x - center)))


def pareto_random(shape: float, scale: float = 1.0) -> float:
    """
    Generate Pareto distribution random number
    
    Args:
        shape: Shape parameter (alpha)
        scale: Scale parameter (minimum value)
        
    Returns:
        Random value from Pareto distribution
    """
    return scale * (random_engine.pareto(shape) + 1.0)


def beta_draw(alpha: float, beta: float, lower: float, upper: float) -> float:
    """
    Draw from Beta distribution scaled to [lower, upper]
    
    Args:
        alpha: Alpha parameter
        beta: Beta parameter
        lower: Lower bound
        upper: Upper bound
        
    Returns:
        Random value in [lower, upper]
    """
    x = random_engine.beta(alpha, beta)
    return lower + x * (upper - lower)


def select_random_weighted(weights: List[float]) -> int:
    """
    Select random index based on cumulative weights
    
    Args:
        weights: List of cumulative weights (must be normalized to sum to 1)
        
    Returns:
        Selected index
    """
    if not weights:
        return -1
    
    r = random_engine.uniform()
    
    for i, w in enumerate(weights):
        if r <= w:
            return i
    
    return len(weights) - 1


def normalize_weights(values: List[float]) -> List[float]:
    """
    Normalize values to create cumulative weights summing to 1
    
    Args:
        values: List of non-negative values
        
    Returns:
        List of cumulative weights
    """
    total = sum(values)
    if total <= 0:
        # Equal weights if all zero
        n = len(values)
        return [i / n for i in range(1, n + 1)]
    
    cumulative = []
    cum_sum = 0.0
    for v in values:
        cum_sum += v / total
        cumulative.append(cum_sum)
    
    # Ensure last element is exactly 1.0
    if cumulative:
        cumulative[-1] = 1.0
    
    return cumulative


def euclidean_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculate Euclidean distance in 2D space"""
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def cap_value(value: float, min_val: Optional[float] = None, 
              max_val: Optional[float] = None) -> float:
    """
    Cap value to specified range
    
    Args:
        value: Value to cap
        min_val: Minimum value (None for no minimum)
        max_val: Maximum value (None for no maximum)
        
    Returns:
        Capped value
    """
    if min_val is not None:
        value = max(value, min_val)
    if max_val is not None:
        value = min(value, max_val)
    return value


def herfindahl_index(market_shares: List[float]) -> float:
    """
    Calculate Herfindahl-Hirschman Index (market concentration)
    
    Args:
        market_shares: List of market shares (as fractions)
        
    Returns:
        HHI value
    """
    return sum(share ** 2 for share in market_shares)


def gini_coefficient(values: List[float]) -> float:
    """
    Calculate Gini coefficient (inequality measure)
    
    Args:
        values: List of values
        
    Returns:
        Gini coefficient in [0, 1]
    """
    if not values or all(v == 0 for v in values):
        return 0.0
    
    sorted_values = sorted([v for v in values if v >= 0])
    n = len(sorted_values)
    
    if n == 0:
        return 0.0
    
    cumsum = 0.0
    for i, v in enumerate(sorted_values):
        cumsum += (2 * (i + 1) - n - 1) * v
    
    mean_val = sum(sorted_values) / n
    if mean_val == 0:
        return 0.0
        
    return cumsum / (n * n * mean_val)
