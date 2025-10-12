"""
K+S Aggregates Analysis
Implements functionality from KS-aggregates.R

Analyzes aggregate economic statistics across Monte Carlo runs
including GDP, employment, productivity, inflation, etc.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional, Tuple
from .support_functions import (
    load_simulation_results,
    comp_mc_stats,
    comp_stats,
    bootstrap_ci,
    format_number
)


# Default variables for aggregate analysis (from KS-aggregates.R)
LOG_VARS = [
    "Creal", "GDPreal", "GDPnom", "G", "Gbail", "Tax", "Deb", "Def",
    "DefP", "dN", "Ireal", "EI", "A", "A1", "A2", "S1", "S2", "Deb1",
    "Deb2", "NWb", "NW1", "NW2", "W1", "W2", "wAvgReal", "BadDeb",
    "TC", "Loans", "CD", "CS", "A2preChg", "A2posChg", "Bon2",
    "Gtrain", "w2realPreChg", "w2realPosChg"
]

AGGR_VARS = LOG_VARS + [
    "dGDP", "dCPI", "dA", "dw", "CPI", "Q2u",
    "F1", "F2", "entry1", "entry2", "entry1exit",
    "entry2exit", "exit1", "exit2", "exit1fail",
    "exit2fail", "imi", "inn", "HH1", "HH2",
    "mu2avg", "U", "V", "r", "Bda", "Bfail",
    "DebGDP", "DefGDP", "DefPgdp", "A2sdPreChg",
    "A2sdPosChg", "Lent", "Lexit", "TeAvg", "Ue",
    "f2posChg", "part", "q2avg", "q2preChg",
    "q2posChg", "sTavg", "sVavg", "wGini", "wLogSD"
]


class AggregateAnalyzer:
    """
    Analyzes aggregate statistics from K+S simulations
    Based on KS-aggregates.R
    """
    
    def __init__(self, 
                 folder: str = "data",
                 base_name: str = "Sim",
                 n_exp: int = 1,
                 ini_drop: int = 0,
                 n_keep: int = -1,
                 mc_stat: str = "mean",
                 ci_level: float = 0.95,
                 boot_r: int = 999,
                 boot_ci: Optional[str] = None):
        """
        Initialize aggregate analyzer
        
        Args:
            folder: data files folder
            base_name: data files base name  
            n_exp: number of experiments
            ini_drop: initial time steps to drop
            n_keep: number of time steps to keep (-1=all)
            mc_stat: Monte Carlo statistic ("mean" or "median")
            ci_level: confidence level
            boot_r: bootstrap replicates
            boot_ci: bootstrap CI method (None, "basic", "bca")
        """
        self.folder = folder
        self.base_name = base_name
        self.n_exp = n_exp
        self.ini_drop = ini_drop
        self.n_keep = n_keep
        self.mc_stat = mc_stat
        self.ci_level = ci_level
        self.boot_r = boot_r
        self.boot_ci_method = boot_ci
        
        self.data = None
        self.mc_stats = None
        self.stats_summary = None
        
    def load_data(self, variables: Optional[List[str]] = None):
        """
        Load simulation data for analysis
        
        Args:
            variables: list of variables to load (default: AGGR_VARS)
        """
        if variables is None:
            variables = AGGR_VARS
            
        print(f"Loading data from {self.folder}/{self.base_name}...")
        print(f"Variables: {len(variables)}")
        print(f"Experiments: {self.n_exp}")
        
        self.data = load_simulation_results(
            folder=self.folder,
            base_name=self.base_name,
            variables=variables,
            n_exp=self.n_exp,
            ini_drop=self.ini_drop,
            n_keep=self.n_keep
        )
        
        print(f"Loaded {len(self.data)} experiment(s)")
        
    def compute_mc_statistics(self):
        """
        Compute Monte Carlo statistics across runs
        """
        if self.data is None:
            raise ValueError("Data not loaded. Call load_data() first.")
            
        self.mc_stats = {}
        
        for exp_name, exp_data in self.data.items():
            print(f"Computing MC statistics for {exp_name}...")
            
            # exp_data shape: (time_steps, n_vars, mc_runs)
            mc_stat = comp_mc_stats(exp_data, stat_type=self.mc_stat)
            
            self.mc_stats[exp_name] = mc_stat
            
            print(f"  Shape: {exp_data.shape}")
            print(f"  Time steps: {exp_data.shape[0]}")
            print(f"  Variables: {exp_data.shape[1]}")
            print(f"  MC runs: {exp_data.shape[2]}")
            
    def compute_summary_statistics(self, 
                                   warm_up: int = 300,
                                   variables: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Compute summary statistics for key variables
        
        Args:
            warm_up: initial periods to ignore for statistics
            variables: variables to analyze (default: all)
            
        Returns:
            DataFrame with summary statistics
        """
        if self.mc_stats is None:
            raise ValueError("MC statistics not computed. Call compute_mc_statistics() first.")
            
        if variables is None:
            variables = AGGR_VARS[:20]  # Use subset for summary
            
        summaries = []
        
        for exp_name, mc_stat in self.mc_stats.items():
            central = mc_stat['central'][warm_up:, :]
            
            for i, var_name in enumerate(variables):
                if i >= central.shape[1]:
                    break
                    
                var_data = central[:, i]
                stats = comp_stats(var_data)
                
                summary = {
                    'Experiment': exp_name,
                    'Variable': var_name,
                    'Mean': stats['avg'],
                    'Std Dev': stats['sd'],
                    'JB Stat': stats['jb']['statistic'],
                    'JB p-value': stats['jb']['p_value'],
                    'AC(1)': stats['ac']['lag1'],
                    'AC(2)': stats['ac']['lag2']
                }
                
                summaries.append(summary)
                
        self.stats_summary = pd.DataFrame(summaries)
        return self.stats_summary
        
    def plot_time_series(self, 
                        variables: List[str],
                        save_path: Optional[str] = None,
                        figsize: Tuple[int, int] = (12, 8)):
        """
        Plot time series for selected variables
        
        Args:
            variables: list of variables to plot
            save_path: path to save figure
            figsize: figure size
        """
        if self.mc_stats is None:
            raise ValueError("MC statistics not computed.")
            
        n_vars = len(variables)
        n_cols = 2
        n_rows = (n_vars + 1) // 2
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
        axes = axes.flatten() if n_vars > 1 else [axes]
        
        for exp_name, mc_stat in self.mc_stats.items():
            central = mc_stat['central']
            ci_low = mc_stat['central'] - 1.96 * mc_stat['sd']
            ci_high = mc_stat['central'] + 1.96 * mc_stat['sd']
            
            for idx, var_name in enumerate(variables):
                ax = axes[idx]
                
                # Find variable index
                var_idx = None
                for i, v in enumerate(AGGR_VARS):
                    if v == var_name:
                        var_idx = i
                        break
                        
                if var_idx is None or var_idx >= central.shape[1]:
                    continue
                    
                time_steps = np.arange(central.shape[0])
                
                # Plot central tendency
                ax.plot(time_steps, central[:, var_idx], 
                       label=f'{exp_name} ({self.mc_stat})',
                       linewidth=2)
                
                # Plot confidence interval
                ax.fill_between(time_steps, 
                               ci_low[:, var_idx],
                               ci_high[:, var_idx],
                               alpha=0.2)
                
                ax.set_title(var_name)
                ax.set_xlabel('Time')
                ax.grid(True, alpha=0.3)
                ax.legend()
                
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Saved plot to {save_path}")
        else:
            plt.show()
            
    def compare_experiments(self, 
                           variable: str,
                           warm_up: int = 300) -> pd.DataFrame:
        """
        Compare a variable across experiments
        
        Args:
            variable: variable name to compare
            warm_up: initial periods to ignore
            
        Returns:
            DataFrame with comparison statistics
        """
        if self.mc_stats is None:
            raise ValueError("MC statistics not computed.")
            
        comparisons = []
        
        # Find variable index
        var_idx = None
        for i, v in enumerate(AGGR_VARS):
            if v == variable:
                var_idx = i
                break
                
        if var_idx is None:
            raise ValueError(f"Variable {variable} not found")
            
        for exp_name, mc_stat in self.mc_stats.items():
            central = mc_stat['central'][warm_up:, var_idx]
            
            stats = comp_stats(central)
            
            comparison = {
                'Experiment': exp_name,
                'Variable': variable,
                'Mean': stats['avg'],
                'Std Dev': stats['sd'],
                'Min': np.min(central),
                'Max': np.max(central)
            }
            
            comparisons.append(comparison)
            
        return pd.DataFrame(comparisons)
        
    def export_results(self, output_file: str):
        """
        Export analysis results to file
        
        Args:
            output_file: output file path (.csv or .xlsx)
        """
        if self.stats_summary is None:
            self.compute_summary_statistics()
            
        if output_file.endswith('.csv'):
            self.stats_summary.to_csv(output_file, index=False)
        elif output_file.endswith('.xlsx'):
            self.stats_summary.to_excel(output_file, index=False)
        else:
            raise ValueError("Output file must be .csv or .xlsx")
            
        print(f"Results exported to {output_file}")


def analyze_aggregates(folder: str = "data",
                      base_name: str = "Sim",
                      n_exp: int = 1,
                      **kwargs) -> AggregateAnalyzer:
    """
    Convenience function to run complete aggregate analysis
    
    Args:
        folder: data folder
        base_name: base name of configuration files
        n_exp: number of experiments
        **kwargs: additional parameters for AggregateAnalyzer
        
    Returns:
        Configured AggregateAnalyzer instance
    """
    analyzer = AggregateAnalyzer(
        folder=folder,
        base_name=base_name,
        n_exp=n_exp,
        **kwargs
    )
    
    print("=" * 60)
    print("K+S Aggregate Analysis")
    print("=" * 60)
    
    analyzer.load_data()
    analyzer.compute_mc_statistics()
    summary = analyzer.compute_summary_statistics()
    
    print("\nSummary Statistics (first 10 variables):")
    print(summary.head(10))
    
    return analyzer


__all__ = [
    'AggregateAnalyzer',
    'analyze_aggregates',
    'AGGR_VARS',
    'LOG_VARS'
]
