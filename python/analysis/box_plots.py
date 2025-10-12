"""
K+S Box Plots Analysis
Implements functionality from KS-box-plots.R

Creates box plot comparisons across experiments and Monte Carlo runs
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional
from .support_functions import load_simulation_results, comp_mc_stats


class BoxPlotAnalyzer:
    """
    Creates box plot analysis for K+S simulations
    Based on KS-box-plots.R (413 lines)
    """
    
    def __init__(self,
                 folder: str = "data",
                 base_name: str = "Sim",
                 n_exp: int = 1,
                 warm_up: int = 300):
        """
        Initialize box plot analyzer
        
        Args:
            folder: data files folder
            base_name: data files base name
            n_exp: number of experiments
            warm_up: initial periods to ignore
        """
        self.folder = folder
        self.base_name = base_name
        self.n_exp = n_exp
        self.warm_up = warm_up
        self.data = None
        
    def load_data(self, variables: List[str]):
        """Load simulation data"""
        self.data = load_simulation_results(
            folder=self.folder,
            base_name=self.base_name,
            variables=variables,
            n_exp=self.n_exp
        )
        
    def create_box_plots(self, 
                        variables: List[str],
                        save_path: Optional[str] = None):
        """
        Create box plots comparing experiments
        
        Args:
            variables: list of variables to plot
            save_path: path to save figure
        """
        if self.data is None:
            raise ValueError("Data not loaded")
            
        n_vars = len(variables)
        n_cols = 3
        n_rows = (n_vars + 2) // 3
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 4*n_rows))
        axes = axes.flatten() if n_vars > 1 else [axes]
        
        for idx, var_name in enumerate(variables):
            ax = axes[idx]
            
            # Prepare data for box plot
            box_data = []
            labels = []
            
            for exp_name, exp_data in self.data.items():
                # Get variable data after warm-up across all MC runs
                var_data = exp_data[self.warm_up:, idx, :].flatten()
                box_data.append(var_data)
                labels.append(exp_name)
                
            # Create box plot
            bp = ax.boxplot(box_data, labels=labels, patch_artist=True)
            
            # Customize appearance
            for patch in bp['boxes']:
                patch.set_facecolor('lightblue')
                patch.set_alpha(0.7)
                
            ax.set_title(var_name)
            ax.set_ylabel('Value')
            ax.grid(True, alpha=0.3, axis='y')
            
        # Hide unused subplots
        for idx in range(n_vars, len(axes)):
            axes[idx].set_visible(False)
            
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
            
    def create_violin_plots(self,
                           variables: List[str],
                           save_path: Optional[str] = None):
        """
        Create violin plots (alternative to box plots)
        
        Args:
            variables: list of variables to plot
            save_path: path to save figure
        """
        if self.data is None:
            raise ValueError("Data not loaded")
            
        # Prepare data in long format for seaborn
        plot_data = []
        
        for exp_name, exp_data in self.data.items():
            for idx, var_name in enumerate(variables):
                var_data = exp_data[self.warm_up:, idx, :].flatten()
                
                for val in var_data:
                    plot_data.append({
                        'Experiment': exp_name,
                        'Variable': var_name,
                        'Value': val
                    })
                    
        df = pd.DataFrame(plot_data)
        
        # Create violin plots
        n_vars = len(variables)
        fig, axes = plt.subplots(1, n_vars, figsize=(5*n_vars, 6))
        
        if n_vars == 1:
            axes = [axes]
            
        for idx, var_name in enumerate(variables):
            ax = axes[idx]
            var_df = df[df['Variable'] == var_name]
            
            sns.violinplot(data=var_df, x='Experiment', y='Value', ax=ax)
            ax.set_title(var_name)
            ax.set_xlabel('')
            
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()


def create_box_plots(folder: str = "data",
                    base_name: str = "Sim",
                    variables: Optional[List[str]] = None,
                    **kwargs):
    """
    Convenience function for box plot analysis
    
    Args:
        folder: data folder
        base_name: base name
        variables: variables to plot
        **kwargs: additional parameters
    """
    analyzer = BoxPlotAnalyzer(folder=folder, base_name=base_name, **kwargs)
    
    if variables is None:
        variables = ["dGDP", "U", "mu2avg", "HH2"]
        
    analyzer.load_data(variables)
    analyzer.create_box_plots(variables)
    
    return analyzer


__all__ = ['BoxPlotAnalyzer', 'create_box_plots']
