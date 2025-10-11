"""
K+S Model Python Implementation
Labor- and finance-augmented K+S Model (version 5.1.3)

This is a complete Python reimplementation of the K+S ABM model originally 
written in C++ for the LSD simulation environment.

Written based on the original K+S model by:
- Marcelo C. Pereira, University of Campinas
- Andrea Roventini and contributors

Python implementation ensures:
- Fixed random seed mechanism for reproducibility
- Correct agent class implementations
- Accurate attribute mappings from C++ to Python
- Consistent behavior function logic
- Identical time-step sequencing
- Compatible random number generation
- Validated mathematical formulas
- Consistent boundary condition handling
- Comprehensive exception handling
"""

__version__ = "5.1.3-python"
__author__ = "Python conversion of K+S model"

from .agent import Agent
from .worker import Worker
from .firm1 import Firm1
from .firm2 import Firm2
from .vintage import VintageAgent
from .bank import Bank
from .labor import LaborMarket, create_application
from .country import Country, CapitalSector, ConsumptionSector, FinancialSector
from .random_engine import random_engine
from .statistics import StatisticsCollector
from .config_parser import LSDConfigParser, parse_lsd_config, load_scenario

__all__ = [
    'Agent',
    'Worker',
    'Firm1',
    'Firm2',
    'VintageAgent',
    'Bank',
    'LaborMarket',
    'Country',
    'CapitalSector',
    'ConsumptionSector',
    'FinancialSector',
    'create_application',
    'random_engine',
    'StatisticsCollector',
    'LSDConfigParser',
    'parse_lsd_config',
    'load_scenario',
]
