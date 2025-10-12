"""
K+S Worker Analysis
Implements functionality from KS-workers.R

Analyzes worker-level dynamics including:
- Wage distribution
- Skill distribution  
- Employment transitions
- Worker mobility
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional
from .support_functions import load_simulation_results, comp_stats


class WorkerAnalyzer:
    """
    Analyzes worker dynamics in K+S simulations
    Based on KS-workers.R (554 lines)
    """
    
    # Worker-related variables
    WORKER_VARS = [
        "L", "Ls", "U", "Ue", "V",
        "wAvgReal", "wGini", "wLogSD",
        "wsAvg", "wsMax", "wsMin", "wsLogSD",
        "sTavg", "sVavg",
        "TeAvg", "Lent", "Lexit",
        "part", "w2realPreChg", "w2realPosChg"
    ]
    
    def __init__(self,
                 folder: str = "data",
                 base_name: str = "Sim",
                 n_exp: int = 1,
                 warm_up: int = 300):
        """
        Initialize worker analyzer
        
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
        
    def load_data(self, variables: Optional[List[str]] = None):
        """Load simulation data"""
        if variables is None:
            variables = self.WORKER_VARS
            
        self.data = load_simulation_results(
            folder=self.folder,
            base_name=self.base_name,
            variables=variables,
            n_exp=self.n_exp
        )
        
    def analyze_workers(self) -> pd.DataFrame:
        """
        Perform complete worker analysis
        
        Returns:
            DataFrame with worker statistics
        """
        if self.data is None:
            self.load_data()
            
        results = []
        
        for exp_name, exp_data in self.data.items():
            for idx, var_name in enumerate(self.WORKER_VARS):
                if idx >= exp_data.shape[1]:
                    break
                    
                var_data = exp_data[self.warm_up:, idx, :].flatten()
                stats = comp_stats(var_data)
                
                result = {
                    'Experiment': exp_name,
                    'Variable': var_name,
                    'Mean': stats['avg'],
                    'Std Dev': stats['sd'],
                    'JB Stat': stats['jb']['statistic'],
                    'JB p-value': stats['jb']['p_value']
                }
                results.append(result)
                
        return pd.DataFrame(results)
        
    def plot_wage_dynamics(self, save_path: Optional[str] = None):
        """
        Plot wage dynamics including distribution and inequality
        
        Args:
            save_path: path to save figure
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Plot average real wage
        ax = axes[0, 0]
        for exp_name, exp_data in self.data.items():
            var_idx = self.WORKER_VARS.index("wAvgReal")
            wage_data = np.mean(exp_data[:, var_idx, :], axis=1)
            ax.plot(wage_data, label=exp_name)
        ax.set_title("Average Real Wage")
        ax.set_xlabel("Time")
        ax.set_ylabel("Real Wage")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Plot wage inequality (Gini)
        ax = axes[0, 1]
        for exp_name, exp_data in self.data.items():
            var_idx = self.WORKER_VARS.index("wGini")
            gini_data = np.mean(exp_data[:, var_idx, :], axis=1)
            ax.plot(gini_data, label=exp_name)
        ax.set_title("Wage Inequality (Gini)")
        ax.set_xlabel("Time")
        ax.set_ylabel("Gini Coefficient")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Plot unemployment rate
        ax = axes[1, 0]
        for exp_name, exp_data in self.data.items():
            var_idx = self.WORKER_VARS.index("Ue")
            unemp_data = np.mean(exp_data[:, var_idx, :], axis=1)
            ax.plot(unemp_data, label=exp_name)
        ax.set_title("Unemployment Rate")
        ax.set_xlabel("Time")
        ax.set_ylabel("Unemployment Rate")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Plot labor market participation
        ax = axes[1, 1]
        for exp_name, exp_data in self.data.items():
            var_idx = self.WORKER_VARS.index("part")
            part_data = np.mean(exp_data[:, var_idx, :], axis=1)
            ax.plot(part_data, label=exp_name)
        ax.set_title("Labor Force Participation Rate")
        ax.set_xlabel("Time")
        ax.set_ylabel("Participation Rate")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
            
    def plot_skill_dynamics(self, save_path: Optional[str] = None):
        """
        Plot skill dynamics
        
        Args:
            save_path: path to save figure
        """
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Plot average tenure skills
        ax = axes[0]
        for exp_name, exp_data in self.data.items():
            var_idx = self.WORKER_VARS.index("sTavg")
            skill_data = np.mean(exp_data[:, var_idx, :], axis=1)
            ax.plot(skill_data, label=exp_name)
        ax.set_title("Average Tenure Skills")
        ax.set_xlabel("Time")
        ax.set_ylabel("Skills")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Plot average vintage skills
        ax = axes[1]
        for exp_name, exp_data in self.data.items():
            var_idx = self.WORKER_VARS.index("sVavg")
            skill_data = np.mean(exp_data[:, var_idx, :], axis=1)
            ax.plot(skill_data, label=exp_name)
        ax.set_title("Average Vintage Skills")
        ax.set_xlabel("Time")
        ax.set_ylabel("Skills")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
            
    def plot_labor_mobility(self, save_path: Optional[str] = None):
        """
        Plot labor mobility patterns
        
        Args:
            save_path: path to save figure
        """
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Plot entry and exit
        ax = axes[0]
        for exp_name, exp_data in self.data.items():
            entry_idx = self.WORKER_VARS.index("Lent")
            exit_idx = self.WORKER_VARS.index("Lexit")
            entry_data = np.mean(exp_data[:, entry_idx, :], axis=1)
            exit_data = np.mean(exp_data[:, exit_idx, :], axis=1)
            time = np.arange(len(entry_data))
            ax.plot(time, entry_data, label=f'{exp_name} (entry)', linestyle='-')
            ax.plot(time, exit_data, label=f'{exp_name} (exit)', linestyle='--')
        ax.set_title("Labor Force Entry and Exit")
        ax.set_xlabel("Time")
        ax.set_ylabel("Number of Workers")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Plot average tenure
        ax = axes[1]
        for exp_name, exp_data in self.data.items():
            var_idx = self.WORKER_VARS.index("TeAvg")
            tenure_data = np.mean(exp_data[:, var_idx, :], axis=1)
            ax.plot(tenure_data, label=exp_name)
        ax.set_title("Average Worker Tenure")
        ax.set_xlabel("Time")
        ax.set_ylabel("Tenure (periods)")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
            
    def create_wage_distribution_plot(self, 
                                     time_period: int,
                                     save_path: Optional[str] = None):
        """
        Plot wage distribution at a specific time period
        
        Args:
            time_period: time period to analyze
            save_path: path to save figure
        """
        fig, ax = plt.subplots(figsize=(10, 6))
        
        for exp_name, exp_data in self.data.items():
            # Get wage data at specific time across MC runs
            var_idx = self.WORKER_VARS.index("wAvgReal")
            if time_period < exp_data.shape[0]:
                wage_dist = exp_data[time_period, var_idx, :]
                ax.hist(wage_dist, bins=30, alpha=0.5, 
                       label=f'{exp_name} (t={time_period})',
                       density=True)
                
        ax.set_xlabel("Real Wage")
        ax.set_ylabel("Density")
        ax.set_title(f"Wage Distribution at t={time_period}")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()


def analyze_workers(folder: str = "data",
                   base_name: str = "Sim",
                   **kwargs) -> WorkerAnalyzer:
    """
    Convenience function for worker analysis
    
    Args:
        folder: data folder
        base_name: base name
        **kwargs: additional parameters
        
    Returns:
        WorkerAnalyzer instance
    """
    analyzer = WorkerAnalyzer(folder=folder, base_name=base_name, **kwargs)
    
    print("Analyzing Worker Dynamics...")
    analyzer.load_data()
    results = analyzer.analyze_workers()
    
    print(f"\nWorker Statistics:")
    print(results.head(10))
    
    return analyzer


__all__ = ['WorkerAnalyzer', 'analyze_workers']
