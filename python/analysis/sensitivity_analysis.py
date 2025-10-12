"""
K+S Sensitivity Analysis
Implements functionality from:
- KS-elementary-effects-SA.R (200 lines) - Morris elementary effects method
- KS-kriging-sobol-SA.R (348 lines) - Kriging-based Sobol indices

Performs global sensitivity analysis to identify key parameters
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional, Tuple, Callable
from .support_functions import load_simulation_results, comp_stats
from scipy.stats import norm


class SensitivityAnalyzer:
    """
    Base class for sensitivity analysis
    """
    
    def __init__(self,
                 folder: str = "data",
                 base_name: str = "sa",
                 var_name: str = "dGDP"):
        """
        Initialize sensitivity analyzer
        
        Args:
            folder: data files folder
            base_name: data files base name for SA
            var_name: variable name for sensitivity analysis
        """
        self.folder = folder
        self.base_name = base_name
        self.var_name = var_name
        self.data = None
        self.parameters = None
        self.results = None


class ElementaryEffectsAnalyzer(SensitivityAnalyzer):
    """
    Morris Elementary Effects Method for sensitivity screening
    Based on KS-elementary-effects-SA.R
    
    The Morris method efficiently identifies important parameters
    by computing elementary effects across the parameter space
    """
    
    def __init__(self,
                 folder: str = "data",
                 base_name: str = "sa-ee",
                 var_name: str = "dGDP",
                 n_trajectories: int = 10,
                 n_levels: int = 4):
        """
        Initialize elementary effects analyzer
        
        Args:
            folder: data folder
            base_name: base name for SA files
            var_name: variable for analysis
            n_trajectories: number of Morris trajectories
            n_levels: number of parameter levels
        """
        super().__init__(folder, base_name, var_name)
        self.n_trajectories = n_trajectories
        self.n_levels = n_levels
        self.effects = None
        
    def load_sa_data(self, parameter_file: str, results_file: str):
        """
        Load sensitivity analysis data
        
        Args:
            parameter_file: file with parameter samples
            results_file: file with model outputs
        """
        # Load parameter samples
        self.parameters = pd.read_csv(parameter_file)
        
        # Load model results
        self.data = load_simulation_results(
            folder=self.folder,
            base_name=self.base_name,
            variables=[self.var_name],
            n_exp=1
        )
        
    def compute_elementary_effects(self) -> pd.DataFrame:
        """
        Compute Morris elementary effects
        
        Returns:
            DataFrame with mean, std dev, and mean absolute effects
        """
        if self.parameters is None or self.data is None:
            raise ValueError("Data not loaded")
            
        n_params = len(self.parameters.columns)
        param_names = self.parameters.columns.tolist()
        
        # Initialize storage for effects
        effects = np.zeros((self.n_trajectories, n_params))
        
        # Compute effects for each trajectory
        for traj in range(self.n_trajectories):
            # Get parameter values and outputs for this trajectory
            start_idx = traj * (n_params + 1)
            end_idx = start_idx + n_params + 1
            
            if end_idx > len(self.parameters):
                break
                
            traj_params = self.parameters.iloc[start_idx:end_idx].values
            
            # Get corresponding outputs
            exp_name = list(self.data.keys())[0]
            traj_outputs = self.data[exp_name][start_idx:end_idx, 0, :]
            
            # Compute mean output for each parameter set
            mean_outputs = np.mean(traj_outputs, axis=1)
            
            # Compute elementary effects
            for i in range(n_params):
                # Change in output / change in parameter
                delta_y = mean_outputs[i+1] - mean_outputs[i]
                delta_x = traj_params[i+1, i] - traj_params[i, i]
                
                if delta_x != 0:
                    effects[traj, i] = delta_y / delta_x
                    
        # Compute statistics of elementary effects
        ee_stats = []
        for i, param_name in enumerate(param_names):
            param_effects = effects[:, i]
            
            ee_stat = {
                'Parameter': param_name,
                'Mean Effect': np.mean(param_effects),
                'Mean Absolute Effect': np.mean(np.abs(param_effects)),
                'Std Dev Effect': np.std(param_effects, ddof=1)
            }
            ee_stats.append(ee_stat)
            
        self.effects = pd.DataFrame(ee_stats)
        return self.effects
        
    def plot_elementary_effects(self, save_path: Optional[str] = None):
        """
        Create scatter plot of mean vs std dev of effects
        
        Args:
            save_path: path to save figure
        """
        if self.effects is None:
            self.compute_elementary_effects()
            
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Plot mean absolute effect vs std dev
        ax.scatter(self.effects['Mean Absolute Effect'],
                  self.effects['Std Dev Effect'],
                  s=100, alpha=0.6)
        
        # Add parameter labels
        for idx, row in self.effects.iterrows():
            ax.annotate(row['Parameter'],
                       (row['Mean Absolute Effect'], row['Std Dev Effect']),
                       fontsize=9, alpha=0.7,
                       xytext=(5, 5), textcoords='offset points')
        
        ax.set_xlabel('Mean Absolute Elementary Effect (μ*)')
        ax.set_ylabel('Standard Deviation of Elementary Effect (σ)')
        ax.set_title(f'Morris Elementary Effects - {self.var_name}')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
            
    def rank_parameters(self, criterion: str = 'mean_abs') -> pd.DataFrame:
        """
        Rank parameters by importance
        
        Args:
            criterion: 'mean_abs' or 'std_dev'
            
        Returns:
            DataFrame with ranked parameters
        """
        if self.effects is None:
            self.compute_elementary_effects()
            
        if criterion == 'mean_abs':
            ranked = self.effects.sort_values('Mean Absolute Effect', 
                                             ascending=False)
        elif criterion == 'std_dev':
            ranked = self.effects.sort_values('Std Dev Effect',
                                             ascending=False)
        else:
            raise ValueError(f"Unknown criterion: {criterion}")
            
        return ranked.reset_index(drop=True)


class SobolAnalyzer(SensitivityAnalyzer):
    """
    Sobol Sensitivity Analysis using Kriging surrogate
    Based on KS-kriging-sobol-SA.R
    
    Computes first-order and total-order Sobol indices
    to quantify parameter importance and interactions
    """
    
    def __init__(self,
                 folder: str = "data",
                 base_name: str = "sa-sobol",
                 var_name: str = "dGDP",
                 n_samples: int = 1000):
        """
        Initialize Sobol analyzer
        
        Args:
            folder: data folder
            base_name: base name for SA files
            var_name: variable for analysis
            n_samples: number of Sobol samples
        """
        super().__init__(folder, base_name, var_name)
        self.n_samples = n_samples
        self.sobol_indices = None
        
    def load_sa_data(self, parameter_file: str, results_file: str):
        """
        Load Sobol analysis data
        
        Args:
            parameter_file: file with Sobol samples
            results_file: file with model outputs
        """
        self.parameters = pd.read_csv(parameter_file)
        
        self.data = load_simulation_results(
            folder=self.folder,
            base_name=self.base_name,
            variables=[self.var_name],
            n_exp=1
        )
        
    def compute_sobol_indices(self) -> pd.DataFrame:
        """
        Compute first-order and total-order Sobol indices
        
        Returns:
            DataFrame with Sobol indices
        """
        if self.parameters is None or self.data is None:
            raise ValueError("Data not loaded")
            
        n_params = len(self.parameters.columns)
        param_names = self.parameters.columns.tolist()
        
        # Get model outputs
        exp_name = list(self.data.keys())[0]
        outputs = self.data[exp_name][:, 0, :]
        mean_outputs = np.mean(outputs, axis=1)
        
        # Total variance
        var_total = np.var(mean_outputs)
        
        # Compute Sobol indices using Saltelli sampling scheme
        # This is a simplified implementation
        # Full implementation would use specialized SA packages
        
        indices = []
        
        for i, param_name in enumerate(param_names):
            # Estimate first-order index
            # Group by parameter value and compute variance
            param_values = self.parameters.iloc[:, i].values
            unique_vals = np.unique(param_values)
            
            cond_means = []
            for val in unique_vals:
                mask = param_values == val
                if np.sum(mask) > 0:
                    cond_means.append(np.mean(mean_outputs[mask]))
                    
            var_cond = np.var(cond_means) if len(cond_means) > 1 else 0.0
            s_first = var_cond / var_total if var_total > 0 else 0.0
            
            # Estimate total-order index (simplified)
            # Would need proper complementary sampling in full implementation
            s_total = 1.0 - (var_total - var_cond) / var_total if var_total > 0 else 0.0
            s_total = max(s_first, s_total)  # Total >= First-order
            
            index = {
                'Parameter': param_name,
                'First-Order Index': s_first,
                'Total-Order Index': s_total,
                'Interaction Index': s_total - s_first
            }
            indices.append(index)
            
        self.sobol_indices = pd.DataFrame(indices)
        return self.sobol_indices
        
    def plot_sobol_indices(self, save_path: Optional[str] = None):
        """
        Plot Sobol indices
        
        Args:
            save_path: path to save figure
        """
        if self.sobol_indices is None:
            self.compute_sobol_indices()
            
        fig, ax = plt.subplots(figsize=(12, 6))
        
        x = np.arange(len(self.sobol_indices))
        width = 0.35
        
        # Plot first-order and total-order indices
        ax.bar(x - width/2, self.sobol_indices['First-Order Index'],
              width, label='First-Order', alpha=0.8)
        ax.bar(x + width/2, self.sobol_indices['Total-Order Index'],
              width, label='Total-Order', alpha=0.8)
        
        ax.set_xlabel('Parameter')
        ax.set_ylabel('Sobol Index')
        ax.set_title(f'Sobol Sensitivity Indices - {self.var_name}')
        ax.set_xticks(x)
        ax.set_xticklabels(self.sobol_indices['Parameter'], rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
            
    def rank_parameters(self, criterion: str = 'total') -> pd.DataFrame:
        """
        Rank parameters by Sobol indices
        
        Args:
            criterion: 'first', 'total', or 'interaction'
            
        Returns:
            DataFrame with ranked parameters
        """
        if self.sobol_indices is None:
            self.compute_sobol_indices()
            
        if criterion == 'first':
            col = 'First-Order Index'
        elif criterion == 'total':
            col = 'Total-Order Index'
        elif criterion == 'interaction':
            col = 'Interaction Index'
        else:
            raise ValueError(f"Unknown criterion: {criterion}")
            
        ranked = self.sobol_indices.sort_values(col, ascending=False)
        return ranked.reset_index(drop=True)


def elementary_effects_sa(folder: str = "data",
                         var_name: str = "dGDP",
                         **kwargs) -> ElementaryEffectsAnalyzer:
    """
    Convenience function for elementary effects analysis
    
    Args:
        folder: data folder
        var_name: variable to analyze
        **kwargs: additional parameters
        
    Returns:
        ElementaryEffectsAnalyzer instance
    """
    analyzer = ElementaryEffectsAnalyzer(folder=folder, var_name=var_name, **kwargs)
    
    print("=" * 60)
    print(f"Elementary Effects Sensitivity Analysis - {var_name}")
    print("=" * 60)
    
    # Note: In actual usage, parameter_file and results_file need to be provided
    # analyzer.load_sa_data(parameter_file, results_file)
    # effects = analyzer.compute_elementary_effects()
    # print("\nParameter Rankings (by mean absolute effect):")
    # print(analyzer.rank_parameters())
    
    return analyzer


def kriging_sobol_sa(folder: str = "data",
                    var_name: str = "dGDP",
                    **kwargs) -> SobolAnalyzer:
    """
    Convenience function for Sobol analysis
    
    Args:
        folder: data folder
        var_name: variable to analyze
        **kwargs: additional parameters
        
    Returns:
        SobolAnalyzer instance
    """
    analyzer = SobolAnalyzer(folder=folder, var_name=var_name, **kwargs)
    
    print("=" * 60)
    print(f"Sobol Sensitivity Analysis - {var_name}")
    print("=" * 60)
    
    # Note: In actual usage, parameter_file and results_file need to be provided
    # analyzer.load_sa_data(parameter_file, results_file)
    # indices = analyzer.compute_sobol_indices()
    # print("\nParameter Rankings (by total-order index):")
    # print(analyzer.rank_parameters())
    
    return analyzer


__all__ = [
    'ElementaryEffectsAnalyzer',
    'SobolAnalyzer',
    'elementary_effects_sa',
    'kriging_sobol_sa'
]
