"""
Type definitions and constants for the K+S model.

This module defines common types, enums, and constants used throughout the model,
matching the C++ definitions in fun_KS_class.h
"""

from typing import Dict, List, Tuple, Optional, Union, Any
from enum import Enum, IntEnum
from dataclasses import dataclass
import numpy as np


# ==================== CONSTANTS ====================

# Initial notional values (from fun_KS_class.h lines 87-89)
INIPROD: float = 1.0  # Initial notional machine productivity
INIWAGE: float = 1.0  # Initial notional wage
INISKILL: float = 1.0  # Initial notional worker skills


# ==================== ENUMERATIONS ====================

class HookType(IntEnum):
    """Dynamic hook types for agent relationships."""
    BANK = 0  # From Firm1/Firm2 to Bank
    BCLIENT = 1  # From Firm1/Firm2 to Cli1/Cli2 (in Bank)
    SUPPL = 2  # From Firm2 to Broch (in Firm2)
    TOPVINT = 3  # From Firm2 to Vint (in Firm2)
    FWRK = 0  # From Worker to Wkr1/Wrkr2 (in Capital/Firm2)
    VWRK = 1  # From Worker to WrkV (in Vint in Firm2)


class ConsumptionMode(IntEnum):
    """Consumption composition modes (flagCons)."""
    IGNORE_PAST = 0  # C = Q2 + N (ignore unfilled past demand)
    RECOVER_ALL = 1  # C = Q2 + N + Cpast (recover all at once)
    RECOVER_LIMITED = 2  # C = Q2 + N + min(Cpast, Crec) (limited recovery)


class GovExpenditureMode(IntEnum):
    """Government expenditure modes (flagGovExp)."""
    MINIMUM_ONLY = 0  # Minimum subsistence income plus interest/bail-outs
    FIXED_GROWTH = 1  # 0 plus growing fixed expenditure
    UNEMPLOYMENT_BENEFIT = 2  # 1 plus unemployment benefit
    SPEND_SURPLUS = 3  # 2 plus spend surplus if no debt


class TaxMode(IntEnum):
    """Taxation modes (flagTax)."""
    PROFIT_ONLY = 0  # Taxes on firm profit only
    PROFIT_AND_WAGE = 1  # Taxes on profit and worker wage/bonus


class CreditRuleMode(IntEnum):
    """Bank credit supply rule modes (flagCreditRule)."""
    NO_LIMIT = 0  # No bank-level credit limit
    DEPOSITS_MULTIPLIER = 1  # Deposits multiplier, no capital adequacy
    BASEL_CAPITAL_ADEQUACY = 2  # Basel-like capital adequacy with bail-out


class FiscalRuleMode(IntEnum):
    """Government fiscal rule modes (flagFiscalRule)."""
    NO_RULE = 0  # No fiscal rule
    BALANCED_BUDGET = 1  # Balanced budget with max deficit/GDP
    SOFT_BALANCED = 2  # Soft balanced budget (only if GDP growing)
    BALANCED_WITH_DEBT = 3  # Balanced budget with max debt and deficit
    SOFT_BALANCED_WITH_DEBT = 4  # Soft balanced with debt (only if GDP growing)


class ExpectationMode(IntEnum):
    """Firm expectation modes in consumption-good sector (flagExpect)."""
    MYOPIC_1 = 0  # Myopic expectations with 1-period memory
    MYOPIC_4 = 1  # Myopic expectations with up to 4-period memory
    ACCELERATING_GD = 2  # Accelerating GD expectations
    ADAPTIVE_1ST = 3  # 1st order adaptive expectations
    EXTRAPOLATIVE = 4  # Extrapolative-accelerating expectations


class JobSearchMode(IntEnum):
    """Job search modes (flagSearchMode)."""
    ALWAYS = 0  # Always search
    UNEMPLOYED_ONLY = 1  # Search only if unemployed
    BELOW_AVERAGE_WAGE = 2  # Search if unemployed or wage below average


class SearchDiscouragementMode(IntEnum):
    """Job search discouragement modes (flagSearchDisc)."""
    ALWAYS_SEARCH = 0  # Always search
    GLOBAL_PROBABILITY = 1  # Global search probability (aggregate unemployment)
    INDIVIDUAL_PROBABILITY = 2  # Individual search probability


class HiringOrder(IntEnum):
    """Hiring/firing order modes (flagHireOrder1, flagHireOrder2, flagFireOrder1, flagFireOrder2)."""
    RANDOM = 0  # Random order
    HIGHER_WAGE_FIRST = 1  # Higher wage workers first
    LOWER_WAGE_FIRST = 2  # Lower wage workers first
    HIGHER_SKILLS_FIRST = 3  # Higher skills workers first
    LOWER_SKILLS_FIRST = 4  # Lower skills workers first
    HIGHER_PAYBACK_FIRST = 5  # Higher payback period workers first
    LOWER_PAYBACK_FIRST = 6  # Lower payback period workers first
    OLD_HIRED_FIRST = 7  # Old hired workers first
    RECENT_HIRED_FIRST = 8  # Recent hired workers first


class FiringRule(IntEnum):
    """Firing rule operations (flagFireRule)."""
    NEVER_FIRE = 0  # Never fires (Japanese mode)
    NEVER_WITH_SHARING = 1  # Never fires with sharing (German mode)
    DOWNSIZING_ONLY = 2  # Only fire if firm downsizing (French mode)
    LOSSES_ONLY = 3  # Only fire if firm at losses (Italian mode)
    PAYBACK_ACHIEVED = 4  # Fire if sufficient payback achieved (American mode)
    CONTRACT_END = 5  # Always fire when contract ends (Brazilian mode)


class WageOfferMode(IntEnum):
    """Wage offer modes (flagWageOffer)."""
    WAGE_PREMIUM = 0  # Propose wage premium (ignore requested wages)
    LOWEST_POSSIBLE = 1  # Propose lowest possible wage based on requests


class WageIndexMode(IntEnum):
    """Wage indexation modes (flagIndexWage)."""
    NO_ADJUSTMENT = 0  # No wage adjustment during employment
    PERIODIC_ADJUSTMENT = 1  # Periodic wage adjustment
    CURRENT_OFFER_REPLICATION = 2  # Current wage offer replication (sector 2 only)


class WorkerLearningMode(IntEnum):
    """Worker-level learning modes (flagWorkerLBU)."""
    NO_LEARNING = 0  # No worker-level learning
    LEARNING_BY_VINTAGE = 1  # Worker-level learning-by-using-vintage
    LEARNING_BY_TENURE = 2  # Worker-level learning-by-tenure
    BOTH = 3  # Both vintage and tenure learning


# ==================== DATA STRUCTURES ====================

@dataclass
class Vintage:
    """
    Represents a machine vintage (technological generation).
    
    Matches C++ struct from fun_KS_class.h lines 18-23
    """
    sVp: float  # Public skills for vintage
    sVavg: float  # Average skills for vintage
    sVavgLag: float  # Lagged average skills
    workers: int  # Current workers using this vintage


@dataclass
class FirmRank:
    """
    Element of pecking order rank for bank credit allocation.
    
    Matches C++ struct from fun_KS_class.h lines 25-29
    """
    NWtoS: float  # Net-wealth-to-sales ratio
    firm_id: int  # ID of the firm
    firm: Any  # Reference to firm object (will be actual Firm instance)


@dataclass
class WageOffer:
    """
    Element of wage offer list for labor market.
    
    Matches C++ struct from fun_KS_class.h lines 31-36
    """
    offer: float  # Wage offer value
    workers: int  # Number of workers in firm
    firm_id: int  # ID of the firm
    firm: Any  # Reference to firm object


@dataclass
class Application:
    """
    Element of job application list.
    
    Matches C++ struct from fun_KS_class.h lines 38-43
    """
    w: float  # Wage attribute
    s: float  # Skill attribute
    ws: float  # Combined wage-skill attribute
    Te: int  # Employment duration
    worker_id: int  # ID of the worker
    worker: Any  # Reference to worker object


# ==================== UTILITY FUNCTIONS ====================

def pack_vintage_id(t0: int, id_suppl: int) -> int:
    """
    Pack vintage (machine technological generation) ID from time and supplier.
    
    Matches C++ macro VNT from fun_KS_class.h lines 150-151
    
    Args:
        t0: Time period of vintage creation
        id_suppl: Supplier firm ID
        
    Returns:
        Packed vintage ID
    """
    return 10000 * int(t0) + int(id_suppl)


def unpack_vintage_time(id_vint: int) -> int:
    """
    Extract time period from vintage ID.
    
    Matches C++ macro T0 from fun_KS_class.h lines 152-153
    
    Args:
        id_vint: Packed vintage ID
        
    Returns:
        Time period of vintage creation
    """
    return int(np.trunc(id_vint) / 10000)


def unpack_vintage_supplier(id_vint: int) -> int:
    """
    Extract supplier ID from vintage ID.
    
    Matches C++ macro SUP from fun_KS_class.h lines 154-155
    
    Args:
        id_vint: Packed vintage ID
        
    Returns:
        Supplier firm ID
    """
    t0 = unpack_vintage_time(id_vint)
    return int(np.trunc(id_vint) - 10000 * t0)


def round_near_reference(value: float, reference: float, tolerance: float) -> float:
    """
    Round values too close to a reference value.
    
    Matches C++ macro ROUND from fun_KS_class.h line 147
    
    Args:
        value: Value to check
        reference: Reference value
        tolerance: Tolerance for rounding
        
    Returns:
        Original value or reference if within tolerance
    """
    return value if abs(value - reference) > tolerance else reference
