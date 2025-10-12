"""
K+S Time Series Plots
Implements functionality from KS-time-plots.R

Creates time series visualizations for key economic variables
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional, Tuple
from .support_functions import load_simulation_results, comp_mc_stats, hp_filter


class TimeSeriesPlotter:
    """
    Creates time series plots for K+S simulations
    Based on KS-time-plots.R (319 lines)
    """
    
    def __init__(self, 
                 folder: str = "data",
                 base_name: str = "Sim",
                 n_exp: int = 1,
                 warm_up_plot: int = 100):
        """
        Initialize time series plotter
        
        Args:
            folder: data files folder
            base_name: data files base name
            n_exp: number of experiments
            warm_up_plot: initial periods to ignore in plots
        """
        self.folder = folder
        self.base_name = base_name
        self.n_exp = n_exp
        self.warm_up_plot = warm_up_plot
        self.data = None
        
    def load_data(self, variables: List[str]):
        """Load simulation data"""
        self.data = load_simulation_results(
            folder=self.folder,
            base_name=self.base_name,
            variables=variables,
            n_exp=self.n_exp
        )
        
    def plot_gdp_growth(self, save_path: Optional[str] = None):
        """Plot GDP growth rate with trend"""
        if self.data is None:
            raise ValueError("Data not loaded")
            
        fig, ax = plt.subplots(figsize=(12, 6))
        
        for exp_name, exp_data in self.data.items():
            # Assuming dGDP is in the data
            mc_stats = comp_mc_stats(exp_data)
            gdp_growth = mc_stats['central'][self.warm_up_plot:, :]
            
            time = np.arange(len(gdp_growth))
            
            # Plot with trend
            trend, cycle = hp_filter(np.mean(gdp_growth, axis=1))
            
            ax.plot(time, np.mean(gdp_growth, axis=1), 
                   label=f'{exp_name} (actual)', alpha=0.7)
            ax.plot(time, trend, label=f'{exp_name} (trend)', 
                   linewidth=2, linestyle='--')
            
        ax.set_xlabel('Time')
        ax.set_ylabel('GDP Growth Rate')
        ax.set_title('GDP Growth Rate with HP Filter Trend')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
            
    def plot_unemployment(self, save_path: Optional[str] = None):
        """Plot unemployment rate"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        for exp_name, exp_data in self.data.items():
            mc_stats = comp_mc_stats(exp_data)
            unemployment = mc_stats['central'][self.warm_up_plot:, :]
            
            time = np.arange(len(unemployment))
            mean_u = np.mean(unemployment, axis=1)
            std_u = np.std(unemployment, axis=1)
            
            ax.plot(time, mean_u, label=f'{exp_name}')
            ax.fill_between(time, mean_u - std_u, mean_u + std_u, alpha=0.2)
            
        ax.set_xlabel('Time')
        ax.set_ylabel('Unemployment Rate')
        ax.set_title('Unemployment Rate over Time')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
            
    def plot_multiple_variables(self, 
                               variables: List[str],
                               save_path: Optional[str] = None):
        """
        Plot multiple variables in subplots
        
        Args:
            variables: list of variable names
            save_path: path to save figure
        """
        n_vars = len(variables)
        n_cols = 2
        n_rows = (n_vars + 1) // 2
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(14, 4*n_rows))
        axes = axes.flatten() if n_vars > 1 else [axes]
        
        for idx, var_name in enumerate(variables):
            ax = axes[idx]
            
            for exp_name, exp_data in self.data.items():
                mc_stats = comp_mc_stats(exp_data)
                var_data = mc_stats['central'][self.warm_up_plot:, idx]
                
                time = np.arange(len(var_data))
                ax.plot(time, var_data, label=exp_name)
                
            ax.set_title(var_name)
            ax.set_xlabel('Time')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()


def plot_time_series(folder: str = "data",
                    base_name: str = "Sim",
                    variables: Optional[List[str]] = None,
                    **kwargs):
    """
    Convenience function for time series plotting
    
    Args:
        folder: data folder
        base_name: base name
        variables: variables to plot
        **kwargs: additional parameters
    """
    plotter = TimeSeriesPlotter(folder=folder, base_name=base_name, **kwargs)
    
    if variables is None:
        variables = ["dGDP", "U", "CPI", "A"]
        
    plotter.load_data(variables)
    plotter.plot_multiple_variables(variables)
    
    return plotter


__all__ = ['TimeSeriesPlotter', 'plot_time_series']
