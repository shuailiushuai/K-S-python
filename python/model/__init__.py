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
