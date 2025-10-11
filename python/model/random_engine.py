"""
Random Number Generation Engine
Implements mt19937_64 compatible random number generation matching the C++ implementation
"""

import numpy as np
from typing import Optional


class RandomEngine:
    """
    Random number generator compatible with C++ mt19937_64
    Ensures reproducible results across runs with fixed seeds
    """
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize random engine with optional seed"""
        self._rng = np.random.Generator(np.random.MT19937(seed))
        self._seed = seed
        
    def seed(self, seed: int):
        """Set/reset the random seed"""
        self._seed = seed
        self._rng = np.random.Generator(np.random.MT19937(seed))
    
    def uniform(self, low: float = 0.0, high: float = 1.0) -> float:
        """Generate uniform random number in [low, high)"""
        return self._rng.uniform(low, high)
    
    def uniform_int(self, low: int, high: int) -> int:
        """Generate uniform random integer in [low, high] (inclusive)"""
        return self._rng.integers(low, high + 1)
    
    def normal(self, mean: float = 0.0, std: float = 1.0) -> float:
        """Generate normal random number"""
        return self._rng.normal(mean, std)
    
    def exponential(self, scale: float = 1.0) -> float:
        """Generate exponential random number"""
        return self._rng.exponential(scale)
    
    def bernoulli(self, p: float) -> bool:
        """Generate Bernoulli random boolean with probability p"""
        return self._rng.uniform() < p
    
    def beta(self, alpha: float, beta: float) -> float:
        """Generate beta distribution random number"""
        return self._rng.beta(alpha, beta)
    
    def pareto(self, shape: float) -> float:
        """Generate Pareto distribution random number"""
        return self._rng.pareto(shape)
    
    def choice(self, a, size=None, replace=True, p=None):
        """Choose random sample from array"""
        return self._rng.choice(a, size=size, replace=replace, p=p)


# Global random engine instance (matches C++ global random_engine)
random_engine = RandomEngine()
