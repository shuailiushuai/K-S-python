"""
Random Number Utilities

Provides consistent random number generation across the model.
"""

import numpy as np
import random


def set_seed(seed: int):
    """
    Set random seed for reproducibility
    
    Args:
        seed: Random seed value
    """
    np.random.seed(seed)
    random.seed(seed)
