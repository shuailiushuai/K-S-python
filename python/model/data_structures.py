"""
Data Structures and Classes
Defines the core data structures used in the K+S model
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Set
from enum import Enum


@dataclass
class Vintage:
    """
    Element of map of vintages (machine technological generation)
    """
    sVp: float = 0.0          # Public skills for vintage
    sVavg: float = 0.0        # Average skills for vintage
    sVavgLag: float = 0.0     # Lagged average skills for vintage
    workers: int = 0          # Current workers using this vintage


@dataclass
class FirmRank:
    """
    Element of pecking order rank for credit allocation
    """
    NWtoS: float = 0.0        # Net-wealth-to-sales ratio
    firm: Optional[object] = None  # Pointer to firm object


@dataclass
class WageOffer:
    """
    Element of wage offer list
    """
    offer: float = 0.0        # Wage offer value
    workers: int = 0          # Number of workers in firm
    firm: Optional[object] = None  # Pointer to firm object


@dataclass
class Application:
    """
    Element of job application list
    """
    w: float = 0.0            # Wage attribute for ordering
    s: float = 0.0            # Skills attribute for ordering
    ws: float = 0.0           # Combined wage-skills attribute
    Te: int = 0               # Employment tenure
    wrk: Optional[object] = None  # Pointer to worker object


@dataclass
class CountryExtension:
    """
    Extension data for Country object
    Contains static global pointers and collections for fast access
    """
    # Container pointers
    finSec: Optional[object] = None   # Financial sector
    capSec: Optional[object] = None   # Capital sector
    conSec: Optional[object] = None   # Consumption sector
    labSup: Optional[object] = None   # Labor supply
    macSta: Optional[object] = None   # Macro statistics
    secSta: Optional[object] = None   # Sector statistics
    labSta: Optional[object] = None   # Labor statistics
    
    # Speed-up vectors and maps
    bankWgtd: List[float] = field(default_factory=list)  # Bank market share cumulative weights
    firm2wgtd: List[float] = field(default_factory=list)  # Firm2 market share cumulative weights
    bankPtr: List[object] = field(default_factory=list)   # Pointers to banks
    firm2ptr: List[object] = field(default_factory=list)  # Pointers to firms in sector 2
    firm2map: Dict[int, object] = field(default_factory=dict)  # ID to pointer map for sector 2
    vintProd: Dict[int, Vintage] = field(default_factory=dict)  # Vintage productivities and skills
    
    # Lists for applications and offers
    firm2wo: List[WageOffer] = field(default_factory=list)     # List of wage offers
    firm1appl: List[Application] = field(default_factory=list) # Sector 1 job applications


@dataclass
class Firm2Extension:
    """
    Extension data for Firm2 object
    """
    appl: List[Application] = field(default_factory=list)  # Firm job applications


class AgentType(Enum):
    """Enumeration of agent types in the model"""
    COUNTRY = "Country"
    FINANCIAL = "Financial"
    BANK = "Bank"
    CAPITAL = "Capital"
    FIRM1 = "Firm1"
    CONSUMPTION = "Consumption"
    FIRM2 = "Firm2"
    VINTAGE = "Vint"
    LABOR = "Labor"
    WORKER = "Worker"
    STATISTICS = "Statistics"
