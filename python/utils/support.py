"""
Support functions for K+S model
Translated from fun_KS_support.h
"""

import math
from typing import Optional, List, Dict, Any


def mov_avg_bound(values: List[float], lim: float = 0.0, per: int = 4) -> float:
    """
    Calculate bounded moving-average growth rate of variable
    If lim is zero, there is no bounding
    
    Args:
        values: List of historical values (most recent first)
        lim: Bound limit (0 = no bounding)
        per: Number of periods for moving average
        
    Returns:
        Moving average growth rate
    """
    sum_g = 0.0
    count = 0
    
    for i in range(min(per, len(values) - 1)):
        if i + 1 < len(values):
            prev = values[i + 1]
            if prev != 0:
                g = values[i] / prev - 1
                
                # Apply bounds if specified
                if lim > 0:
                    g = max(min(g, lim), -lim)
                
                sum_g += g
                count += 1
    
    return sum_g / count if count > 0 else 0.0


def round_value(v: float, ref: float, tol: float) -> float:
    """
    Round values too close to a reference
    
    Args:
        v: Value to round
        ref: Reference value
        tol: Tolerance
        
    Returns:
        Rounded value or original if not close enough
    """
    return ref if abs(v - ref) <= tol else v


def check_error(cond: bool, err_msg: str, err_count: int, err_counter: List[int]) -> None:
    """
    Append error messages and increment error counter
    
    Args:
        cond: Condition to check
        err_msg: Error message
        err_count: Current error count for this type
        err_counter: List with single element - total error counter
    """
    if not cond:
        return
        
    if err_count == 0:
        print(f" {err_msg}")
    else:
        print(f" {err_msg}({err_count})")
    
    err_counter[0] += 1


class VintageData:
    """Data structure for vintage (machine generation) information"""
    
    def __init__(self, t0: int, id_suppl: int, productivity: float, price: float):
        """
        Initialize vintage data
        
        Args:
            t0: Time period of creation
            id_suppl: Supplier firm ID
            productivity: Machine productivity
            price: Machine price
        """
        self.t0 = t0
        self.id_suppl = id_suppl
        self.productivity = productivity
        self.price = price
        self.sVp = 1.0  # Public skills for vintage
        self.sVavg = 1.0  # Average skills for vintage
        self.sVavgLag = 1.0  # Lagged average skills
        self.workers = 0  # Current workers using this vintage
        
    def pack_vintage_id(self) -> int:
        """
        Pack vintage data into ID
        Format: t0 * 1000000 + id_suppl
        """
        return self.t0 * 1000000 + self.id_suppl
    
    @staticmethod
    def unpack_vintage_id(vint_id: int) -> tuple:
        """
        Unpack vintage ID to (t0, id_suppl)
        
        Args:
            vint_id: Packed vintage ID
            
        Returns:
            Tuple of (t0, id_suppl)
        """
        id_suppl = vint_id % 1000000
        t0 = vint_id // 1000000
        return t0, id_suppl


class FirmRank:
    """Element of pecking order rank"""
    
    def __init__(self, nw_to_s: float, firm: Any):
        """
        Initialize firm rank
        
        Args:
            nw_to_s: Net-wealth-to-sales ratio
            firm: Pointer to firm object
        """
        self.NWtoS = nw_to_s
        self.firm = firm


class WageOffer:
    """Element of wage offer list"""
    
    def __init__(self, offer: float, workers: int, firm: Any):
        """
        Initialize wage offer
        
        Args:
            offer: Wage offer value
            workers: Number of workers in firm
            firm: Pointer to firm object
        """
        self.offer = offer
        self.workers = workers
        self.firm = firm


class Application:
    """Element of job application list"""
    
    def __init__(self, worker: Any, wage: float = 0.0, skills: float = 0.0, 
                 tenure: int = 0):
        """
        Initialize job application
        
        Args:
            worker: Pointer to worker object
            wage: Requested wage
            skills: Worker skills
            tenure: Work tenure
        """
        self.wrk = worker
        self.w = wage
        self.s = skills
        self.ws = wage + skills  # Combined ordering attribute
        self.Te = tenure


# Initial notional values
INIPROD = 1.0  # Initial notional machine productivity
INIWAGE = 1.0  # Initial notional wage
INISKILL = 1.0  # Initial notional worker skills
