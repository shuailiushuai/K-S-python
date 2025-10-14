"""
Base Agent Class for K+S Model
Provides common functionality for all agents
"""

from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """Base class for all agents in the K+S model"""
    
    def __init__(self, agent_id: int, t: int = 0):
        """
        Initialize base agent
        
        Args:
            agent_id: Unique agent identifier
            t: Current time period
        """
        self.id = agent_id
        self.t_creation = t
        self.variables = {}  # Current period variables
        self.lagged_vars = {}  # Historical variables by period
        self.parameters = {}  # Agent-specific parameters
        self.hooks = {}  # References to related agents
        
    def get_var(self, name: str, lag: int = 0) -> Any:
        """
        Get variable value with optional lag
        
        Args:
            name: Variable name
            lag: Number of periods to lag (0 = current)
            
        Returns:
            Variable value or None if not found
        """
        if lag == 0:
            return self.variables.get(name)
        
        if name not in self.lagged_vars:
            return None
            
        # Get lagged value
        lags = sorted(self.lagged_vars[name].keys(), reverse=True)
        if lag <= len(lags):
            return self.lagged_vars[name].get(lags[lag - 1] if lag <= len(lags) else None)
        
        return None
    
    def set_var(self, name: str, value: Any):
        """
        Set variable value for current period
        
        Args:
            name: Variable name
            value: Variable value
        """
        self.variables[name] = value
    
    def update_lagged(self, t: int):
        """
        Update lagged variables at end of period
        
        Args:
            t: Current time period
        """
        for name, value in self.variables.items():
            if name not in self.lagged_vars:
                self.lagged_vars[name] = {}
            self.lagged_vars[name][t] = value
            
        # Keep only necessary history (e.g., last 10 periods)
        max_history = 10
        for name in self.lagged_vars:
            if len(self.lagged_vars[name]) > max_history:
                # Remove oldest
                oldest_t = min(self.lagged_vars[name].keys())
                del self.lagged_vars[name][oldest_t]
    
    def get_param(self, name: str, default: Any = None) -> Any:
        """
        Get parameter value
        
        Args:
            name: Parameter name
            default: Default value if not found
            
        Returns:
            Parameter value
        """
        return self.parameters.get(name, default)
    
    def set_param(self, name: str, value: Any):
        """
        Set parameter value
        
        Args:
            name: Parameter name
            value: Parameter value
        """
        self.parameters[name] = value
    
    def add_hook(self, name: str, agent: 'BaseAgent'):
        """
        Add reference to related agent
        
        Args:
            name: Hook name (e.g., 'bank', 'supplier')
            agent: Related agent object
        """
        self.hooks[name] = agent
    
    def get_hook(self, name: str) -> Optional['BaseAgent']:
        """
        Get related agent by hook name
        
        Args:
            name: Hook name
            
        Returns:
            Related agent or None
        """
        return self.hooks.get(name)
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]):
        """
        Initialize agent with configuration
        
        Args:
            config: Configuration dictionary
        """
        pass
    
    @abstractmethod
    def step(self, t: int):
        """
        Execute one time step
        
        Args:
            t: Current time period
        """
        pass
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, t={self.t_creation})"
