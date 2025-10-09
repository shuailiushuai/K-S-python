"""
Visualization Functions

Plotting functions for model results.
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Optional
import seaborn as sns


def plot_time_series(data: Dict[str, List], variables: Optional[List[str]] = None,
                     save_path: Optional[str] = None):
    """
    Plot time series of selected variables
    
    Args:
        data: Dictionary of time series data
        variables: List of variable names to plot
        save_path: Path to save figure (optional)
    """
    if variables is None:
        variables = ['GDP_real', 'unemployment_rate', 'inflation', 
                    'num_firms1', 'num_firms2']
    
    # Filter available variables
    available_vars = [v for v in variables if v in data and len(data[v]) > 0]
    
    if not available_vars:
        print("No data available for plotting")
        return
    
    n_vars = len(available_vars)
    fig, axes = plt.subplots(n_vars, 1, figsize=(12, 3*n_vars))
    
    if n_vars == 1:
        axes = [axes]
    
    time = data.get('time', range(len(data[available_vars[0]])))
    
    for i, var in enumerate(available_vars):
        axes[i].plot(time, data[var], linewidth=1.5)
        axes[i].set_xlabel('Time')
        axes[i].set_ylabel(var.replace('_', ' ').title())
        axes[i].grid(True, alpha=0.3)
        axes[i].set_title(f'{var.replace("_", " ").title()} over Time')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Figure saved to {save_path}")
    else:
        plt.show()


def plot_distributions(data: Dict[str, Dict], time_step: int,
                       save_path: Optional[str] = None):
    """
    Plot distributions at a specific time step
    
    Args:
        data: Dictionary containing distribution data
        time_step: Time step to plot
        save_path: Path to save figure (optional)
    """
    distributions = {}
    
    if 'firm_sizes' in data and time_step in data['firm_sizes']:
        distributions['Firm Sizes'] = data['firm_sizes'][time_step]
    
    if 'wage_distribution' in data and time_step in data['wage_distribution']:
        distributions['Wages'] = data['wage_distribution'][time_step]
    
    if 'productivity_distribution' in data and time_step in data['productivity_distribution']:
        distributions['Productivity'] = data['productivity_distribution'][time_step]
    
    if not distributions:
        print(f"No distribution data available for time step {time_step}")
        return
    
    n_dists = len(distributions)
    fig, axes = plt.subplots(1, n_dists, figsize=(6*n_dists, 4))
    
    if n_dists == 1:
        axes = [axes]
    
    for i, (name, dist_data) in enumerate(distributions.items()):
        if dist_data:
            axes[i].hist(dist_data, bins=30, alpha=0.7, edgecolor='black')
            axes[i].set_xlabel(name)
            axes[i].set_ylabel('Frequency')
            axes[i].set_title(f'{name} Distribution (t={time_step})')
            axes[i].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Figure saved to {save_path}")
    else:
        plt.show()


def plot_aggregate_summary(data: Dict[str, List], save_path: Optional[str] = None):
    """
    Plot summary of key aggregate variables
    
    Args:
        data: Dictionary of time series data
        save_path: Path to save figure (optional)
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    time = data.get('time', range(len(data['GDP_real'])))
    
    # GDP
    axes[0, 0].plot(time, data['GDP_real'], label='Real GDP', linewidth=1.5)
    axes[0, 0].set_xlabel('Time')
    axes[0, 0].set_ylabel('GDP')
    axes[0, 0].set_title('Real GDP')
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].legend()
    
    # Unemployment
    axes[0, 1].plot(time, [u*100 for u in data['unemployment_rate']], 
                   color='red', linewidth=1.5)
    axes[0, 1].set_xlabel('Time')
    axes[0, 1].set_ylabel('Unemployment Rate (%)')
    axes[0, 1].set_title('Unemployment Rate')
    axes[0, 1].grid(True, alpha=0.3)
    
    # Inflation
    axes[1, 0].plot(time, [i*100 for i in data['inflation']], 
                   color='green', linewidth=1.5)
    axes[1, 0].set_xlabel('Time')
    axes[1, 0].set_ylabel('Inflation Rate (%)')
    axes[1, 0].set_title('Inflation Rate')
    axes[1, 0].grid(True, alpha=0.3)
    
    # Number of firms
    axes[1, 1].plot(time, data['num_firms1'], label='Capital Firms', linewidth=1.5)
    axes[1, 1].plot(time, data['num_firms2'], label='Consumption Firms', linewidth=1.5)
    axes[1, 1].set_xlabel('Time')
    axes[1, 1].set_ylabel('Number of Firms')
    axes[1, 1].set_title('Firm Population')
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].legend()
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Figure saved to {save_path}")
    else:
        plt.show()
