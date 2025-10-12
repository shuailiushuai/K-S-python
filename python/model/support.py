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


# Financial management functions (fun_KS_support.h:97-221)

def update_debt(firm, desired: float, loan: float) -> float:
    """
    Update firm debt accounting
    
    Implements the C++ update_debt() function from fun_KS_support.h
    Manages:
    - Credit demand tracking (_CD1/_CD2)
    - Credit constraint tracking (_CD1c/_CD2c)
    - Credit supply tracking (_CS1/_CS2)
    - Debt stock updates (_Deb1/_Deb2)
    - Bank available credit adjustments (_TC1free/_TC2free)
    
    Args:
        firm: Firm agent (Firm1 or Firm2)
        desired: Desired credit amount
        loan: Actual loan amount granted
        
    Returns:
        Updated debt stock
    """
    # Determine sector (0=Firm1, 1=Firm2)
    sec = 0 if firm.agent_type == "Firm1" else 1
    
    # Variable name arrays
    _CDvar = ["_CD1", "_CD2"]
    _CDcVar = ["_CD1c", "_CD2c"]
    _CSvar = ["_CS1", "_CS2"]
    _DebVar = ["_Deb1", "_Deb2"]
    _TCfreeVar = ["_TC1free", "_TC2free"]
    
    # Track credit demand and constraints (only for new loans, not repayment)
    if desired > 0:
        # Increment desired credit
        current_cd = firm.read(_CDvar[sec], 0)
        firm.write(_CDvar[sec], current_cd + desired, 0)
        
        # Increment credit constraint
        current_cdc = firm.read(_CDcVar[sec], 0)
        firm.write(_CDcVar[sec], current_cdc + (desired - loan), 0)
        
        # Increment supplied credit
        current_cs = firm.read(_CSvar[sec], 0)
        firm.write(_CSvar[sec], current_cs + loan, 0)
    
    # Get current debt
    Deb = firm.read(_DebVar[sec], 0)
    
    # Take new loan or repay debt
    if loan != 0:
        # Write-off small debt
        if Deb + loan < 0.001:
            Deb = 0.0
            firm.write(_DebVar[sec], 0.0, 0)
        else:
            Deb = Deb + loan
            firm.write(_DebVar[sec], Deb, 0)
        
        # Update bank's available credit
        bank = firm.get_hook(0)  # BANK hook (index 0)
        if bank is not None:
            TCfree = bank.read(_TCfreeVar[sec], 0)
            if TCfree > -0.1:
                bank.write(_TCfreeVar[sec], max(TCfree - loan, 0.0), 0)
    
    return Deb


def update_depo(firm, depo: float, incr: bool) -> float:
    """
    Update firm deposits (net worth)
    
    Implements the C++ update_depo() function from fun_KS_support.h
    Manages firm net worth (_NW1/_NW2) which represents bank deposits
    
    Args:
        firm: Firm agent (Firm1 or Firm2)
        depo: Deposit change (if incr=True) or new value (if incr=False)
        incr: If True, increment by depo; if False, set to depo
        
    Returns:
        Updated net worth (deposits)
    """
    # Determine sector (0=Firm1, 1=Firm2)
    sec = 0 if firm.agent_type == "Firm1" else 1
    
    # Variable name arrays
    _NWvar = ["_NW1", "_NW2"]
    
    # Update net worth (deposits)
    if incr:
        NW = firm.read(_NWvar[sec], 0)
        if depo != 0:
            NW = NW + depo
            firm.write(_NWvar[sec], NW, 0)
    else:
        NW = depo
        firm.write(_NWvar[sec], NW, 0)
    
    return NW


def cash_flow(firm, profit: float, tax: float) -> float:
    """
    Manage firm cash flow and financial operations
    
    Implements the complete C++ cash_flow() function from fun_KS_support.h:169-221
    
    This function handles the complete financial cycle for a firm:
    1. Calculates free cash flow after taxes, bonuses, and dividends
    2. If losses (negative cash flow):
       a. Draw from deposits if available
       b. If deposits insufficient, take loans
       c. If credit unavailable, mark for bankruptcy (negative NW)
    3. If profits (positive cash flow):
       a. Repay debt if any (up to desired repayment rate)
       b. Keep remainder in deposits
    
    This is called from _Tax1 and _Tax2 equations in the C++ model
    
    Args:
        firm: Firm agent (Firm1 or Firm2)
        profit: Gross profit before taxes
        tax: Tax amount to pay
        
    Returns:
        Free cash flow after all transactions
    """
    # Determine sector (0=Firm1, 1=Firm2, 2=other)
    sec = 0 if firm.agent_type == "Firm1" else (1 if firm.agent_type == "Firm2" else 2)
    
    # Get financial sector for parameters
    country = firm.find_parent("Country")
    if country is None:
        return profit - tax
    
    fin = None
    for child in country.children:
        if child.agent_type == "Financial":
            fin = child
            break
    
    if fin is None:
        return profit - tax
    
    # Variable name arrays
    _CIvar = ["", "_CI"]
    _CSaVar = ["_CS1a", "_CS2a"]
    _DivVar = ["_Div1", "_Div2"]
    _NWpVar = ["_NW1p", "_NW2p"]
    _DebVar = ["_Deb1", "_Deb2"]
    
    # Calculate free cash flow
    bonus = firm.read("_Bon2", 1) if sec == 1 else 0.0  # Worker bonus (only Firm2)
    dividends = firm.read(_DivVar[sec], 1)  # Shareholder dividends
    cashFree = profit - tax - bonus - dividends  # Final free cash flow
    
    # Ensure canceled investment reimbursed (Firm2 only)
    if sec > 0:
        firm.read(_CIvar[sec], 0)  # Just access to ensure it's computed
    
    # Get current deposits (with production cost provision for productive firms)
    provision = firm.read(_NWpVar[sec], 0) if sec < 2 else 0.0
    depo = update_depo(firm, provision, True)  # Current bank deposits
    
    # Handle negative cash flow (losses)
    if cashFree < 0:
        if depo >= -cashFree:
            # Deposits cover losses
            update_depo(firm, cashFree, True)
        else:
            # Need to borrow
            credAvb = firm.read(_CSaVar[sec], 0)  # Available credit
            credDes = -cashFree - depo  # Desired credit
            
            # Finance all in any case (even if credit unavailable)
            update_debt(firm, credDes, credDes)
            
            if credAvb >= credDes:
                # Could finance losses - keep going with zero deposits
                update_depo(firm, 0.0, False)
            else:
                # Credit unavailable - let negative NW (bankruptcy signal)
                update_depo(firm, -1e-6, False)
    
    # Handle positive cash flow (profits)
    else:
        # Calculate desired debt repayment
        current_debt = firm.read(_DebVar[sec], 0)
        deltaB = fin.read("deltaB", 0)
        repayDes = current_debt * deltaB
        
        if repayDes > 0:
            # Something to repay
            if cashFree > repayDes:
                # Can repay desired and more
                update_debt(firm, 0.0, -repayDes)
                update_depo(firm, cashFree - repayDes, True)
            else:
                # Repay what is possible
                update_debt(firm, 0.0, -cashFree)
        else:
            # No debt or no repayment needed - just keep all cash
            update_depo(firm, cashFree, True)
    
    return cashFree
