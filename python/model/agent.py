"""
Base Agent Class
Provides the foundation for all agents in the K+S model
"""

from typing import Any, Dict, List, Optional, Tuple
import math


class Agent:
    """
    Base class for all agents in the K+S model
    
    Implements core functionality for:
    - Variable storage and retrieval (current and lagged values)
    - Parameter management
    - Parent-child relationships
    - Hook management for inter-agent references
    """
    
    def __init__(self, agent_type: str, parent: Optional['Agent'] = None):
        """
        Initialize agent
        
        Args:
            agent_type: Type of agent (Country, Bank, Firm1, etc.)
            parent: Parent agent in hierarchy
        """
        self.agent_type = agent_type
        self.parent = parent
        self.children: List[Agent] = []
        
        # Variable storage: name -> list of values (index 0 = current, 1 = t-1, etc.)
        self._variables: Dict[str, List[float]] = {}
        
        # Parameters: name -> value
        self._parameters: Dict[str, float] = {}
        
        # Hooks: dynamic references to other agents
        self._hooks: List[Optional[Agent]] = []
        
        # Extensions: additional data structures
        self._extension: Any = None
        
        # Tracking
        self._last_update: Dict[str, int] = {}  # Track when variable was last computed
        self._current_time: int = 0
        
    def add_child(self, child: 'Agent'):
        """Add child agent"""
        self.children.append(child)
        child.parent = self
        
    def get_children(self, agent_type: Optional[str] = None) -> List['Agent']:
        """Get all children, optionally filtered by type"""
        if agent_type is None:
            return self.children
        return [c for c in self.children if c.agent_type == agent_type]
    
    def find_parent(self, agent_type: str) -> Optional['Agent']:
        """Find parent of specified type by traversing up hierarchy"""
        current = self.parent
        while current is not None:
            if current.agent_type == agent_type:
                return current
            current = current.parent
        return None
    
    # Variable management
    def write(self, var_name: str, value: float, lag: int = 0):
        """
        Write variable value at specified lag
        
        Args:
            var_name: Variable name
            value: Value to write
            lag: Lag index (0=current, 1=t-1, etc., or -1 for initialization)
        """
        if var_name not in self._variables:
            self._variables[var_name] = []
        
        # Handle initialization with lag -1 (creates lag 1 position directly)
        if lag == -1:
            lag = 1
        
        # Extend list if needed
        while len(self._variables[var_name]) <= lag:
            self._variables[var_name].append(0.0)
        
        self._variables[var_name][lag] = value
        
        if lag == 0:
            self._last_update[var_name] = self._current_time
    
    def read(self, var_name: str, lag: int = 0, default: float = 0.0) -> float:
        """
        Read variable value at specified lag
        
        Args:
            var_name: Variable name
            lag: Lag index (0=current, 1=t-1, etc.)
            default: Default value if not found
            
        Returns:
            Variable value
        """
        if var_name not in self._variables:
            return default
        
        if lag >= len(self._variables[var_name]):
            return default
            
        return self._variables[var_name][lag]
    
    def update_lags(self):
        """
        Update lagged values for all variables
        Called at the end of each time step
        """
        for var_name, values in self._variables.items():
            if len(values) > 0:
                # Shift values: current becomes lag 1, etc.
                self._variables[var_name] = [values[0]] + values
    
    # Parameter management
    def set_param(self, param_name: str, value: float):
        """Set parameter value"""
        self._parameters[param_name] = value
    
    def get_param(self, param_name: str, default: float = 0.0) -> float:
        """Get parameter value"""
        return self._parameters.get(param_name, default)
    
    # Hook management (for inter-agent references)
    def add_hooks(self, num_hooks: int):
        """Initialize hooks array"""
        self._hooks = [None] * num_hooks
    
    def set_hook(self, index: int, agent: Optional['Agent']):
        """Set hook at index to point to agent"""
        if index < len(self._hooks):
            self._hooks[index] = agent
    
    def get_hook(self, index: int) -> Optional['Agent']:
        """Get agent referenced by hook at index"""
        if index < len(self._hooks):
            return self._hooks[index]
        return None
    
    # Extension management
    def set_extension(self, extension: Any):
        """Set extension data structure"""
        self._extension = extension
    
    def get_extension(self) -> Any:
        """Get extension data structure"""
        return self._extension
    
    # Time management
    def set_time(self, t: int):
        """Set current time step"""
        self._current_time = t
        for child in self.children:
            child.set_time(t)
    
    def get_time(self) -> int:
        """Get current time step"""
        return self._current_time
    
    # Utility methods
    def search(self, agent_type: str) -> Optional['Agent']:
        """Search for first child of specified type"""
        for child in self.children:
            if child.agent_type == agent_type:
                return child
        return None
    
    def search_all(self, agent_type: str) -> List['Agent']:
        """Search for all children of specified type"""
        return self.get_children(agent_type)
    
    def count(self, agent_type: str) -> int:
        """Count children of specified type"""
        return len(self.get_children(agent_type))
    
    def __repr__(self) -> str:
        return f"{self.agent_type}(children={len(self.children)})"
