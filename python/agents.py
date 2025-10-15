"""
Base Agent Classes and Data Structures
Defines the core agent types and data structures used in the K+S model.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import math

@dataclass
class Vintage:
    """Element of map of vintages (from fun_KS_class.h)"""
    sVp: float = 0.0          # public skills for vintage
    sVavg: float = 0.0        # average skills for vintage
    sVavgLag: float = 0.0     # lagged average skills for vintage
    workers: int = 0          # current workers using this vintage


@dataclass
class FirmRank:
    """Element of pecking order rank"""
    NWtoS: float = 0.0        # net-wealth-to-sales ratio
    firm: Optional[Any] = None  # pointer to firm


@dataclass
class WageOffer:
    """Element of wage offer list"""
    offer: float = 0.0        # wage offer value
    workers: int = 0          # workers in firm
    firm: Optional[Any] = None  # pointer to firm


@dataclass
class Application:
    """Element of application list"""
    w: float = 0.0            # wage
    s: float = 0.0            # skills
    ws: float = 0.0           # wage-skill ratio
    Te: int = 0               # employment tenure
    wrk: Optional[Any] = None # pointer to worker


class BaseAgent:
    """
    Base agent class with variable storage and hooks.
    Mimics LSD object behavior with variable storage and dynamic hooks.
    """
    
    def __init__(self, agent_id: int, agent_type: str, parent=None):
        """
        Initialize base agent.
        
        Args:
            agent_id: Unique identifier for this agent
            agent_type: Type name of the agent (e.g., 'Firm1', 'Worker')
            parent: Parent agent in hierarchy
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.parent = parent
        
        # Variable storage (current and lagged values)
        self.vars: Dict[str, List[float]] = defaultdict(lambda: [0.0])
        
        # Dynamic hooks (pointers to other agents)
        self.hooks: List[Optional[Any]] = [None] * 10  # Max hooks
        
        # Extensions for specialized data
        self.extensions: Dict[str, Any] = {}
        
        # Children agents
        self.children: Dict[str, List[Any]] = defaultdict(list)
        
    def V(self, var_name: str) -> float:
        """Get current value of variable"""
        return self.vars[var_name][0]
    
    def VL(self, var_name: str, lag: int = 1) -> float:
        """Get lagged value of variable"""
        if lag >= len(self.vars[var_name]):
            return 0.0
        return self.vars[var_name][lag]
    
    def WRITE(self, var_name: str, value: float) -> float:
        """Write current value of variable"""
        self.vars[var_name][0] = value
        return value
    
    def INCR(self, var_name: str, increment: float) -> float:
        """Increment variable value"""
        self.vars[var_name][0] += increment
        return self.vars[var_name][0]
    
    def update_lags(self):
        """Update lagged values (called at end of time step)"""
        for var_name in self.vars:
            self.vars[var_name].insert(0, self.vars[var_name][0])
            # Keep only necessary lags (max 10)
            if len(self.vars[var_name]) > 10:
                self.vars[var_name] = self.vars[var_name][:10]
    
    def HOOK(self, hook_id: int) -> Optional[Any]:
        """Get hook pointer"""
        if 0 <= hook_id < len(self.hooks):
            return self.hooks[hook_id]
        return None
    
    def WRITE_HOOK(self, hook_id: int, target: Any):
        """Set hook pointer"""
        if 0 <= hook_id < len(self.hooks):
            self.hooks[hook_id] = target
    
    def add_child(self, child_type: str, child: Any):
        """Add child agent"""
        self.children[child_type].append(child)
    
    def get_children(self, child_type: str) -> List[Any]:
        """Get children of specified type"""
        return self.children.get(child_type, [])
    
    def count_children(self, child_type: str) -> int:
        """Count children of specified type"""
        return len(self.children.get(child_type, []))
    
    def delete_child(self, child_type: str, child: Any):
        """Remove child agent"""
        if child_type in self.children and child in self.children[child_type]:
            self.children[child_type].remove(child)
    

class CountryExtension:
    """Extension to Country object (from fun_KS_class.h)"""
    
    def __init__(self):
        # Static global pointers to individual containers
        self.finSec = None
        self.capSec = None
        self.conSec = None
        self.labSup = None
        self.macSta = None
        self.secSta = None
        self.labSta = None
        
        # Country speed-up vectors & maps
        self.bankWgtd: List[float] = []      # m.s. cum. weights in banking
        self.firm2wgtd: List[float] = []     # m.s. cum. weights in sector 2
        self.bankPtr: List[Any] = []         # pointers to banks
        self.firm2ptr: List[Any] = []        # pointers to firms in sector 2
        self.firm2map: Dict[int, Any] = {}   # ID to pointer map for sector 2
        self.vintProd: Dict[int, Vintage] = {}  # vintage productivities & skills
        
        # Country lists
        self.firm2wo: List[WageOffer] = []   # list of wage offers
        self.firm1appl: List[Application] = []  # sector 1 job applications
        self.firm2appl: List[Application] = []  # sector 2 job applications


class Firm2Extension:
    """Extension to Firm2 object"""
    
    def __init__(self):
        self.appl: List[Application] = []    # firm job applications


def mov_avg_bound(values: List[float], lim: float = 0.0, per: int = 1) -> float:
    """
    Calculate the bounded, moving-average growth rate.
    
    Args:
        values: List of historical values (most recent first)
        lim: Bound limit (0 = no bounding)
        per: Number of periods for moving average
    
    Returns:
        Moving average growth rate
    """
    sum_g = 0.0
    count = 0
    
    for i in range(per):
        if i + 1 >= len(values):
            break
        
        prev = values[i + 1]
        if prev != 0:
            g = values[i] / prev - 1
        else:
            g = 0.0
        
        if lim > 0:
            g = max(min(g, lim), -lim)
        
        sum_g += g
        count += 1
    
    return sum_g / count if count > 0 else 0.0
