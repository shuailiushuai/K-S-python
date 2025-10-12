"""
Statistical Analysis Module for K+S Model
Implements all R-based statistical analysis in Python

This module provides comprehensive statistical analysis capabilities
for K+S model simulation results, including:
- Aggregate statistics
- Time series plots  
- Box plots
- Sector-specific analysis
- Worker analysis
- Sensitivity analysis

Based on the original R scripts:
- KS-aggregates.R
- KS-time-plots.R
- KS-box-plots.R
- KS-sector-1.R
- KS-sector-2-MC.R
- KS-sector-2-pool.R
- KS-workers.R
- KS-elementary-effects-SA.R
- KS-kriging-sobol-SA.R
"""

from .support_functions import *
from .aggregates import *
from .time_plots import *
from .box_plots import *
from .sector_analysis import *
from .worker_analysis import *
from .sensitivity_analysis import *

__all__ = [
    'load_simulation_results',
    'compute_statistics',
    'plot_time_series',
    'plot_box_plots',
    'analyze_sector_1',
    'analyze_sector_2_mc',
    'analyze_sector_2_pool',
    'analyze_workers',
    'elementary_effects_sa',
    'kriging_sobol_sa'
]
