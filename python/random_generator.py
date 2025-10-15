"""
Random Number Generation
Provides consistent random number generation using numpy's mt19937 generator
to match the C++ implementation's mt19937_64 random engine.
"""

import numpy as np
from typing import Optional

class RandomEngine:
    """
    Random number generator matching C++ mt19937_64 behavior.
    Uses numpy's MT19937 generator for consistency with the C++ model.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize random engine with optional seed.
        
        Args:
            seed: Random seed for reproducibility (default: None)
        """
        self._seed = seed
        self._generator = np.random.Generator(np.random.MT19937(seed))
        
    def seed(self, seed: int):
        """Set the random seed"""
        self._seed = seed
        self._generator = np.random.Generator(np.random.MT19937(seed))
        
    def uniform(self, low: float = 0.0, high: float = 1.0) -> float:
        """Generate uniform random number in [low, high)"""
        return self._generator.uniform(low, high)
    
    def normal(self, mean: float = 0.0, std: float = 1.0) -> float:
        """Generate normal random number"""
        return self._generator.normal(mean, std)
    
    def beta(self, alpha: float, beta: float) -> float:
        """Generate beta random number"""
        return self._generator.beta(alpha, beta)
    
    def pareto(self, alpha: float) -> float:
        """Generate Pareto random number"""
        return self._generator.pareto(alpha)
    
    def poisson(self, lam: float) -> int:
        """Generate Poisson random number"""
        return int(self._generator.poisson(lam))
    
    def choice(self, arr, size=None, replace=True, p=None):
        """Random choice from array"""
        return self._generator.choice(arr, size=size, replace=replace, p=p)
    
    def integers(self, low: int, high: int = None) -> int:
        """Generate random integer in [low, high)"""
        if high is None:
            high = low
            low = 0
        return self._generator.integers(low, high)
    
    def shuffle(self, arr):
        """Shuffle array in place"""
        self._generator.shuffle(arr)
        return arr
    
    def bernoulli(self, p: float) -> bool:
        """Generate Bernoulli random variable"""
        return self._generator.uniform() < p

# Global random engine instance (matches C++ global random_engine)
random_engine = RandomEngine()
