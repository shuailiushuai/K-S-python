"""
Random Number Generator with Fixed Seed
Provides consistent random number generation across runs for reproducibility
"""

import numpy as np
from typing import Optional


class RandomGenerator:
    """
    Random number generator with fixed seed for reproducibility
    Uses NumPy's MT19937 generator to match C++11 mt19937_64
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize random generator
        
        Args:
            seed: Random seed for reproducibility. If None, uses default seed.
        """
        self.seed = seed if seed is not None else 1
        self.rng = np.random.Generator(np.random.MT19937(self.seed))
        
    def set_seed(self, seed: int):
        """Reset random generator with new seed"""
        self.seed = seed
        self.rng = np.random.Generator(np.random.MT19937(seed))
        
    def uniform(self, low: float = 0.0, high: float = 1.0) -> float:
        """Generate uniform random number in [low, high)"""
        return self.rng.uniform(low, high)
    
    def normal(self, mean: float = 0.0, std: float = 1.0) -> float:
        """Generate normal (Gaussian) random number"""
        return self.rng.normal(mean, std)
    
    def beta(self, alpha: float, beta: float) -> float:
        """Generate Beta distribution random number"""
        return self.rng.beta(alpha, beta)
    
    def choice(self, choices: list, weights: Optional[list] = None):
        """Choose random element from list with optional weights"""
        if weights is None:
            return self.rng.choice(choices)
        return self.rng.choice(choices, p=np.array(weights) / np.sum(weights))
    
    def shuffle(self, array: list) -> list:
        """Shuffle array in place and return it"""
        arr = np.array(array)
        self.rng.shuffle(arr)
        return arr.tolist()
    
    def poisson(self, lam: float) -> int:
        """Generate Poisson distributed random integer"""
        return self.rng.poisson(lam)
    
    def exponential(self, scale: float = 1.0) -> float:
        """Generate exponential distributed random number"""
        return self.rng.exponential(scale)
    
    def integer(self, low: int, high: int) -> int:
        """Generate random integer in [low, high]"""
        return self.rng.integers(low, high + 1)


# Global random generator instance
_random_generator = RandomGenerator()


def get_random_generator() -> RandomGenerator:
    """Get global random generator instance"""
    return _random_generator


def set_seed(seed: int):
    """Set seed for global random generator"""
    _random_generator.set_seed(seed)
