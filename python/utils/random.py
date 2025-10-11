"""
Random number generation utilities for K+S model.

Matches the C++ mt19937_64 random engine used in the original model.
Ensures reproducibility through fixed seed mechanism.
"""

import numpy as np
from typing import Optional, List
from numpy.random import Generator, MT19937


class KSRandomGenerator:
    """
    Random number generator matching the C++ mt19937_64 engine.
    
    The original model uses C++11 mt19937_64 pseudo-random generator engine
    (see fun_KS.cpp line 33). This class replicates that behavior using NumPy's
    MT19937 generator for reproducibility.
    
    Attributes:
        seed: Random seed for reproducibility
        generator: NumPy random generator instance
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the random generator.
        
        Args:
            seed: Random seed for reproducibility. If None, uses system time.
                  Matches 'random_engine.seed(RND_SEED)' from fun_KS.cpp line 88
        """
        self.seed = seed if seed is not None else np.random.randint(0, 2**32 - 1)
        self.generator = Generator(MT19937(self.seed))
    
    def uniform(self, low: float = 0.0, high: float = 1.0) -> float:
        """
        Generate a uniform random number in [low, high).
        
        Args:
            low: Lower bound (inclusive)
            high: Upper bound (exclusive)
            
        Returns:
            Random float in [low, high)
        """
        return self.generator.uniform(low, high)
    
    def uniform_int(self, low: int, high: int) -> int:
        """
        Generate a uniform random integer in [low, high].
        
        Matches uniform_int() calls in C++ code (e.g., fun_KS_country.h line 491)
        
        Args:
            low: Lower bound (inclusive)
            high: Upper bound (inclusive)
            
        Returns:
            Random integer in [low, high]
        """
        return self.generator.integers(low, high + 1)
    
    def normal(self, mean: float = 0.0, std: float = 1.0) -> float:
        """
        Generate a normal (Gaussian) random number.
        
        Args:
            mean: Mean of the distribution
            std: Standard deviation
            
        Returns:
            Random float from normal distribution
        """
        return self.generator.normal(mean, std)
    
    def beta(self, alpha: float, beta: float) -> float:
        """
        Generate a random number from Beta distribution.
        
        Used for innovation and imitation in capital-good sector R&D
        (see fun_KS_firm1.h, parameters alpha1, beta1, alpha2, beta2)
        
        Args:
            alpha: Alpha parameter (> 0)
            beta: Beta parameter (> 0)
            
        Returns:
            Random float from Beta(alpha, beta) distribution
        """
        return self.generator.beta(alpha, beta)
    
    def pareto(self, shape: float, scale: float = 1.0) -> float:
        """
        Generate a random number from Pareto distribution.
        
        Used for bank size heterogeneity (see parameter alphaB in Financial sector)
        
        Args:
            shape: Shape parameter (alpha)
            scale: Scale parameter (xm)
            
        Returns:
            Random float from Pareto distribution
        """
        return (self.generator.pareto(shape) + 1) * scale
    
    def exponential(self, scale: float = 1.0) -> float:
        """
        Generate a random number from exponential distribution.
        
        Args:
            scale: Scale parameter (1/lambda)
            
        Returns:
            Random float from exponential distribution
        """
        return self.generator.exponential(scale)
    
    def choice(self, items: List, weights: Optional[List[float]] = None) -> any:
        """
        Random choice from a list, optionally weighted.
        
        Args:
            items: List of items to choose from
            weights: Optional probability weights
            
        Returns:
            Randomly selected item
        """
        if weights is not None:
            weights = np.array(weights)
            weights = weights / weights.sum()  # Normalize
        return self.generator.choice(items, p=weights)
    
    def shuffle(self, items: List) -> List:
        """
        Randomly shuffle a list in-place.
        
        Args:
            items: List to shuffle
            
        Returns:
            Shuffled list (same reference)
        """
        self.generator.shuffle(items)
        return items
    
    def bernoulli(self, p: float) -> bool:
        """
        Bernoulli trial (coin flip with probability p).
        
        Args:
            p: Probability of success
            
        Returns:
            True with probability p, False otherwise
        """
        return self.generator.uniform() < p
    
    def reset_seed(self, seed: int) -> None:
        """
        Reset the random generator with a new seed.
        
        Args:
            seed: New random seed
        """
        self.seed = seed
        self.generator = Generator(MT19937(seed))
    
    def get_state(self) -> dict:
        """
        Get the current state of the random generator.
        
        Useful for saving simulation state.
        
        Returns:
            Dictionary containing generator state
        """
        return {
            'seed': self.seed,
            'state': self.generator.bit_generator.state
        }
    
    def set_state(self, state: dict) -> None:
        """
        Set the state of the random generator.
        
        Useful for restoring simulation state.
        
        Args:
            state: State dictionary from get_state()
        """
        self.seed = state['seed']
        self.generator.bit_generator.state = state['state']


# Global random generator instance
# Matches 'mt19937_64 random_engine' from fun_KS.cpp line 33
_global_rng: Optional[KSRandomGenerator] = None


def get_rng() -> KSRandomGenerator:
    """
    Get the global random number generator.
    
    Returns:
        Global KSRandomGenerator instance
    """
    global _global_rng
    if _global_rng is None:
        _global_rng = KSRandomGenerator()
    return _global_rng


def set_rng_seed(seed: int) -> None:
    """
    Set the seed for the global random number generator.
    
    Args:
        seed: Random seed for reproducibility
    """
    global _global_rng
    _global_rng = KSRandomGenerator(seed)


def uniform(low: float = 0.0, high: float = 1.0) -> float:
    """Shortcut to global RNG uniform()."""
    return get_rng().uniform(low, high)


def uniform_int(low: int, high: int) -> int:
    """Shortcut to global RNG uniform_int()."""
    return get_rng().uniform_int(low, high)


def normal(mean: float = 0.0, std: float = 1.0) -> float:
    """Shortcut to global RNG normal()."""
    return get_rng().normal(mean, std)


def beta(alpha: float, beta_param: float) -> float:
    """Shortcut to global RNG beta()."""
    return get_rng().beta(alpha, beta_param)


def pareto(shape: float, scale: float = 1.0) -> float:
    """Shortcut to global RNG pareto()."""
    return get_rng().pareto(shape, scale)


def choice(items: List, weights: Optional[List[float]] = None) -> any:
    """Shortcut to global RNG choice()."""
    return get_rng().choice(items, weights)


def shuffle(items: List) -> List:
    """Shortcut to global RNG shuffle()."""
    return get_rng().shuffle(items)


def bernoulli(p: float) -> bool:
    """Shortcut to global RNG bernoulli()."""
    return get_rng().bernoulli(p)
