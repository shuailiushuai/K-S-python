"""
K+S Sector Analysis
Implements functionality from:
- KS-sector-1.R (576 lines) - Capital goods sector analysis
- KS-sector-2-MC.R (450 lines) - Consumption goods sector MC analysis  
- KS-sector-2-pool.R (540 lines) - Consumption goods sector pooled analysis

Analyzes firm-level and sector-level dynamics
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional, Tuple
from .support_functions import load_simulation_results, comp_stats


class SectorAnalyzer:
    """
    Analyzes sector-level dynamics in K+S simulations
    """
    
    def __init__(self,
                 folder: str = "data",
                 base_name: str = "Sim",
                 n_exp: int = 1,
                 warm_up: int = 300):
        """
        Initialize sector analyzer
        
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


class Sector1Analyzer(SectorAnalyzer):
    """
    Capital goods sector (Sector 1) analysis
    Based on KS-sector-1.R
    """
    
    # Variables specific to sector 1
    SECTOR1_VARS = [
        "F1", "L1", "Q1", "S1", "D1", "p1avg", "c1avg",
        "AtauAvg", "BtauAvg", "A1", "mu1avg", "NW1", "Deb1",
        "entry1", "exit1", "HH1", "age1avg", "s1avg"
    ]
    
    def analyze_sector1(self) -> pd.DataFrame:
        """
        Perform complete sector 1 analysis
        
        Returns:
            DataFrame with sector 1 statistics
        """
        if self.data is None:
            self.load_data(self.SECTOR1_VARS)
            
        results = []
        
        for exp_name, exp_data in self.data.items():
            # Compute statistics for each variable
            for idx, var_name in enumerate(self.SECTOR1_VARS):
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
        
    def plot_rd_innovation(self, save_path: Optional[str] = None):
        """
        Plot R&D and innovation dynamics
        
        Args:
            save_path: path to save figure
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Plot productivity evolution
        ax = axes[0, 0]
        for exp_name, exp_data in self.data.items():
            # AtauAvg - average productivity of machines supplied
            var_idx = self.SECTOR1_VARS.index("AtauAvg")
            prod_data = np.mean(exp_data[:, var_idx, :], axis=1)
            ax.plot(prod_data, label=exp_name)
        ax.set_title("Average Machine Productivity (Supplied)")
        ax.set_xlabel("Time")
        ax.set_ylabel("Productivity")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Plot innovation rate
        ax = axes[0, 1]
        for exp_name, exp_data in self.data.items():
            # BtauAvg - average productivity of machines produced
            var_idx = self.SECTOR1_VARS.index("BtauAvg")
            innov_data = np.mean(exp_data[:, var_idx, :], axis=1)
            ax.plot(innov_data, label=exp_name)
        ax.set_title("Average Machine Productivity (Produced)")
        ax.set_xlabel("Time")
        ax.set_ylabel("Productivity")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Plot market concentration
        ax = axes[1, 0]
        for exp_name, exp_data in self.data.items():
            var_idx = self.SECTOR1_VARS.index("HH1")
            hhi_data = np.mean(exp_data[:, var_idx, :], axis=1)
            ax.plot(hhi_data, label=exp_name)
        ax.set_title("Market Concentration (HHI)")
        ax.set_xlabel("Time")
        ax.set_ylabel("HHI")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Plot entry/exit dynamics
        ax = axes[1, 1]
        for exp_name, exp_data in self.data.items():
            entry_idx = self.SECTOR1_VARS.index("entry1")
            exit_idx = self.SECTOR1_VARS.index("exit1")
            entry_data = np.mean(exp_data[:, entry_idx, :], axis=1)
            exit_data = np.mean(exp_data[:, exit_idx, :], axis=1)
            time = np.arange(len(entry_data))
            ax.plot(time, entry_data, label=f'{exp_name} (entry)', linestyle='-')
            ax.plot(time, exit_data, label=f'{exp_name} (exit)', linestyle='--')
        ax.set_title("Entry and Exit")
        ax.set_xlabel("Time")
        ax.set_ylabel("Number of Firms")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()


class Sector2Analyzer(SectorAnalyzer):
    """
    Consumption goods sector (Sector 2) analysis
    Based on KS-sector-2-MC.R and KS-sector-2-pool.R
    """
    
    # Variables specific to sector 2
    SECTOR2_VARS = [
        "F2", "L2", "Q2", "S2", "D2", "p2avg", "c2avg",
        "A2", "mu2avg", "NW2", "Deb2", "Q2u",
        "entry2", "exit2", "HH2", "age2avg", "s2avg",
        "A2sd", "A2posChg", "A2preChg", "f2posChg"
    ]
    
    def analyze_sector2(self) -> pd.DataFrame:
        """
        Perform complete sector 2 analysis
        
        Returns:
            DataFrame with sector 2 statistics
        """
        if self.data is None:
            self.load_data(self.SECTOR2_VARS)
            
        results = []
        
        for exp_name, exp_data in self.data.items():
            for idx, var_name in enumerate(self.SECTOR2_VARS):
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
        
    def plot_sector2_dynamics(self, save_path: Optional[str] = None):
        """
        Plot sector 2 dynamics
        
        Args:
            save_path: path to save figure
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Plot productivity
        ax = axes[0, 0]
        for exp_name, exp_data in self.data.items():
            var_idx = self.SECTOR2_VARS.index("A2")
            prod_data = np.mean(exp_data[:, var_idx, :], axis=1)
            ax.plot(prod_data, label=exp_name)
        ax.set_title("Average Labor Productivity")
        ax.set_xlabel("Time")
        ax.set_ylabel("Productivity")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Plot capacity utilization
        ax = axes[0, 1]
        for exp_name, exp_data in self.data.items():
            var_idx = self.SECTOR2_VARS.index("Q2u")
            util_data = np.mean(exp_data[:, var_idx, :], axis=1)
            ax.plot(util_data, label=exp_name)
        ax.set_title("Capacity Utilization")
        ax.set_xlabel("Time")
        ax.set_ylabel("Utilization Rate")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Plot markup
        ax = axes[1, 0]
        for exp_name, exp_data in self.data.items():
            var_idx = self.SECTOR2_VARS.index("mu2avg")
            markup_data = np.mean(exp_data[:, var_idx, :], axis=1)
            ax.plot(markup_data, label=exp_name)
        ax.set_title("Average Markup")
        ax.set_xlabel("Time")
        ax.set_ylabel("Markup")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Plot concentration
        ax = axes[1, 1]
        for exp_name, exp_data in self.data.items():
            var_idx = self.SECTOR2_VARS.index("HH2")
            hhi_data = np.mean(exp_data[:, var_idx, :], axis=1)
            ax.plot(hhi_data, label=exp_name)
        ax.set_title("Market Concentration (HHI)")
        ax.set_xlabel("Time")
        ax.set_ylabel("HHI")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()


def analyze_sector_1(folder: str = "data",
                    base_name: str = "Sim",
                    **kwargs) -> Sector1Analyzer:
    """
    Convenience function for sector 1 analysis
    """
    analyzer = Sector1Analyzer(folder=folder, base_name=base_name, **kwargs)
    print("Analyzing Capital Goods Sector (Sector 1)...")
    results = analyzer.analyze_sector1()
    print(f"\nSector 1 Statistics:")
    print(results.head(10))
    return analyzer


def analyze_sector_2_mc(folder: str = "data",
                       base_name: str = "Sim",
                       **kwargs) -> Sector2Analyzer:
    """
    Convenience function for sector 2 Monte Carlo analysis
    """
    analyzer = Sector2Analyzer(folder=folder, base_name=base_name, **kwargs)
    print("Analyzing Consumption Goods Sector (Sector 2)...")
    results = analyzer.analyze_sector2()
    print(f"\nSector 2 Statistics:")
    print(results.head(10))
    return analyzer


def analyze_sector_2_pool(folder: str = "data",
                          base_name: str = "Sim",
                          **kwargs) -> Sector2Analyzer:
    """
    Convenience function for sector 2 pooled analysis
    (Same as MC analysis but with pooled data across experiments)
    """
    return analyze_sector_2_mc(folder, base_name, **kwargs)


__all__ = [
    'SectorAnalyzer',
    'Sector1Analyzer', 
    'Sector2Analyzer',
    'analyze_sector_1',
    'analyze_sector_2_mc',
    'analyze_sector_2_pool'
]
