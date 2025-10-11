"""
Support functions for the K+S model.

Matches pure C support functions from fun_KS_support.h
"""

from typing import List, Optional, Callable
import numpy as np


def mov_avg_bound(
    values: List[float], 
    lim: float = 0.0, 
    per: int = 4
) -> float:
    """
    Calculate bounded, moving-average growth rate of a variable.
    
    Matches C++ function from fun_KS_support.h lines 21-41
    
    If lim is zero, there is no bounding.
    
    Args:
        values: List of historical values (most recent first)
        lim: Limit for bounding growth rates (0 = no bounding)
        per: Number of periods for moving average
        
    Returns:
        Moving average growth rate
        
    Example:
        # Calculate bounded 4-period moving average growth
        >>> values = [105, 100, 95, 90, 85]  # Most recent first
        >>> mov_avg_bound(values, lim=0.1, per=4)
    """
    if len(values) < 2:
        return 0.0
    
    sum_g = 0.0
    i = 0
    
    for i in range(min(per, len(values) - 1)):
        prev = values[i + 1]
        curr = values[i]
        
        if prev != 0:
            g = curr / prev - 1
        else:
            g = 0.0
        
        # Apply bounds if lim > 0
        if lim > 0:
            g = max(min(g, lim), -lim)
        
        sum_g += g
    
    # Return average (i is the count of actual periods used)
    return sum_g / (i + 1) if i >= 0 else 0.0


def check_error(
    condition: bool,
    err_msg: str,
    err_count: int,
    err_counter: List[int]
) -> None:
    """
    Append error messages and increment error counter.
    
    Matches C++ function from fun_KS_support.h lines 46-57
    
    Args:
        condition: If True, error is recorded
        err_msg: Error message to log
        err_count: Current count for this error type
        err_counter: List containing single error counter (passed by reference)
    """
    if not condition:
        return
    
    if err_count == 0:
        print(f" {err_msg}")
    else:
        print(f" {err_msg}({err_count})")
    
    err_counter[0] += 1


def rank_desc_nw_to_s(e1: 'FirmRank', e2: 'FirmRank') -> bool:
    """
    Comparison function for sorting firms by net-wealth-to-sales ratio (descending).
    
    Matches C++ function from fun_KS_support.h lines 64-67
    Used in bank credit pecking order (equations 'cScores', '_cScores')
    
    Args:
        e1: First firm rank
        e2: Second firm rank
        
    Returns:
        True if e1 should come before e2 in descending order
    """
    return e1.NWtoS > e2.NWtoS


def update_debt(
    firm: any,
    sector: int,
    deb_var: float,
    cs_var: float,
    cd_var: float,
    cd_c_var: float
) -> None:
    """
    Update firm debt variables.
    
    Matches C++ function from fun_KS_support.h lines 96-138
    Called in equations '_Q1', '_Tax1', '_Q2', '_EI', '_SI', '_Tax2'
    
    Args:
        firm: Firm object to update
        sector: Sector number (1 or 2)
        deb_var: Current debt value
        cs_var: Credit supplied value
        cd_var: Credit demanded value
        cd_c_var: Credit demanded constrained value
    """
    # Update debt variable
    new_debt = deb_var - cs_var + cd_c_var
    
    if sector == 1:
        firm._Deb1 = max(new_debt, 0.0)
    else:
        firm._Deb2 = max(new_debt, 0.0)


def cash_flow(
    firm: any,
    profit: float,
    tax: float
) -> None:
    """
    Manage the period cash flow for a firm.
    
    Matches C++ function from fun_KS_support.h lines 179-214
    Called in equations '_Tax1', '_Tax2'
    
    Args:
        firm: Firm object
        profit: Gross profit before tax
        tax: Tax amount
    """
    # After-tax profit
    net_profit = profit - tax
    
    # Update net worth
    if hasattr(firm, '_NW1'):
        firm._NW1 += net_profit
    elif hasattr(firm, '_NW2'):
        firm._NW2 += net_profit


def entry_firm(
    sector: any,
    firm_type: str,
    params: dict
) -> any:
    """
    Create and initialize a new entrant firm.
    
    Matches C++ functions for firm entry from fun_KS_support.h
    Used in 'entry1exit' and 'entry2exit' equations
    
    Args:
        sector: Sector object (Capital or Consumption)
        firm_type: Type of firm ('Firm1' or 'Firm2')
        params: Dictionary of parameters for initialization
        
    Returns:
        New firm object
    """
    # This is a placeholder - actual implementation depends on firm classes
    pass


def exit_firm(firm: any, sector: any) -> None:
    """
    Handle firm exit from the market.
    
    Matches C++ functions for firm exit from fun_KS_support.h
    Used in 'entry1exit' and 'entry2exit' equations
    
    Args:
        firm: Firm object to exit
        sector: Sector object (Capital or Consumption)
    """
    # This is a placeholder - actual implementation depends on firm classes
    pass


def compute_market_share(
    firm_sales: float,
    total_sales: float,
    previous_share: float,
    n_periods: int = 1
) -> float:
    """
    Compute market share using moving average.
    
    Args:
        firm_sales: Current firm sales
        total_sales: Total market sales
        previous_share: Previous market share
        n_periods: Number of periods for averaging
        
    Returns:
        Updated market share
    """
    if total_sales <= 0:
        return previous_share
    
    current_share = firm_sales / total_sales
    
    if n_periods == 1:
        return current_share
    else:
        # Exponential moving average
        alpha = 2.0 / (n_periods + 1)
        return alpha * current_share + (1 - alpha) * previous_share


def compute_competitiveness(
    price: float,
    unfilled_demand: float,
    quality: float,
    omega1: float,
    omega2: float,
    omega3: float,
    avg_price: float,
    avg_unfilled: float,
    avg_quality: float
) -> float:
    """
    Compute firm competitiveness in consumption-good sector.
    
    Used in market share dynamics (replicator dynamics)
    
    Args:
        price: Firm's price
        unfilled_demand: Firm's unfilled demand
        quality: Firm's product quality
        omega1: Weight of price competitiveness
        omega2: Weight of unfilled demand competitiveness
        omega3: Weight of quality competitiveness
        avg_price: Market average price
        avg_unfilled: Market average unfilled demand
        avg_quality: Market average quality
        
    Returns:
        Firm competitiveness index
    """
    # Normalize components
    price_comp = (avg_price / price) if price > 0 else 1.0
    unfilled_comp = (avg_unfilled / unfilled_demand) if unfilled_demand > 0 else 1.0
    quality_comp = (quality / avg_quality) if avg_quality > 0 else 1.0
    
    # Weighted competitiveness
    total_weight = omega1 + omega2 + omega3
    if total_weight == 0:
        return 1.0
    
    competitiveness = (
        omega1 * price_comp +
        omega2 * unfilled_comp +
        omega3 * quality_comp
    ) / total_weight
    
    return competitiveness


def apply_replicator_dynamics(
    market_shares: np.ndarray,
    competitiveness: np.ndarray,
    chi: float
) -> np.ndarray:
    """
    Apply replicator dynamics to update market shares.
    
    Used in consumption-good sector market dynamics
    
    Args:
        market_shares: Current market shares (array)
        competitiveness: Firm competitiveness indices (array)
        chi: Selectivity coefficient
        
    Returns:
        Updated market shares (normalized)
    """
    if len(market_shares) == 0:
        return market_shares
    
    # Average competitiveness
    avg_comp = np.average(competitiveness, weights=market_shares)
    
    # Update shares
    new_shares = market_shares * (1 + chi * (competitiveness - avg_comp))
    
    # Ensure non-negative
    new_shares = np.maximum(new_shares, 0)
    
    # Normalize
    total = new_shares.sum()
    if total > 0:
        new_shares = new_shares / total
    else:
        new_shares = np.ones_like(new_shares) / len(new_shares)
    
    return new_shares


def compute_herfindahl_index(market_shares: np.ndarray) -> float:
    """
    Compute Herfindahl-Hirschman Index (HHI) of market concentration.
    
    Args:
        market_shares: Array of market shares
        
    Returns:
        HHI value (between 0 and 1)
    """
    return np.sum(market_shares ** 2)


def select_supplier(
    suppliers: List[any],
    selection_weights: List[float],
    rng: any
) -> any:
    """
    Select a supplier based on weights (e.g., market share, past relationship).
    
    Args:
        suppliers: List of supplier objects
        selection_weights: Weights for selection
        rng: Random number generator
        
    Returns:
        Selected supplier
    """
    if not suppliers:
        return None
    
    if len(suppliers) == 1:
        return suppliers[0]
    
    # Normalize weights
    weights = np.array(selection_weights)
    weights = weights / weights.sum()
    
    return rng.choice(suppliers, weights=weights.tolist())
