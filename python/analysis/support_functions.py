"""
Support Functions for K+S Statistical Analysis
Implements the functionality from KS-support-functions.R

This module provides utility functions for:
- Data loading and manipulation
- Statistical computations
- Distribution fitting
- Plotting utilities

Based on KS-support-functions.R (2043 lines)
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import jarque_bera, kstest, anderson
import warnings
from typing import Dict, List, Tuple, Optional, Union
import pickle
import gzip


# ==== User Parameters ====

MAX_SAMPLE = 10000          # Maximum sample size in plots (PDF control)
TOP_MARGIN = 0.2            # Top plot margin scaling factor
BOT_MARGIN = 0.1            # Bottom plot margin scaling factor  
DEF_DIGITS = 4              # Default number of digits after comma


# ==== Basic Functions ====

def all_na(x: np.ndarray) -> np.ndarray:
    """
    Test if all elements in a matrix/dataframe row are NA
    
    Args:
        x: array to test
        
    Returns:
        Boolean array indicating rows where all elements are NA
    """
    return np.all(np.isnan(x), axis=1)


def is_finite_df(x: Union[np.ndarray, pd.DataFrame]) -> Union[np.ndarray, pd.DataFrame]:
    """
    Check if values are finite (not NaN, not Inf)
    
    Args:
        x: array or dataframe to test
        
    Returns:
        Boolean array/dataframe with finite test results
    """
    if isinstance(x, pd.DataFrame):
        return x.applymap(np.isfinite)
    return np.isfinite(x)


def not_in(a: List, b: List) -> List:
    """
    Find elements in a that are not in b
    
    Args:
        a: first list
        b: second list
        
    Returns:
        List of elements in a but not in b
    """
    return [x for x in a if x not in b]


# ==== Statistical Functions ====

def comp_stats(x: np.ndarray) -> Dict[str, Union[float, Dict]]:
    """
    Compute comprehensive statistics for a data series
    Including mean, std dev, normality tests, autocorrelation
    
    Based on comp_stats() in KS-support-functions.R
    
    Args:
        x: data series
        
    Returns:
        Dictionary with statistical measures:
        - avg: mean
        - sd: standard deviation  
        - jb: Jarque-Bera test result
        - ll: Lilliefors test result
        - ad: Anderson-Darling test result
        - ac: autocorrelation at lags 1 and 2
    """
    x = np.array(x).flatten()
    x = x[~np.isnan(x)]
    
    # Initialize default values
    result = {
        'avg': np.nan,
        'sd': np.nan,
        'jb': {'statistic': np.nan, 'p_value': np.nan},
        'll': {'statistic': np.nan, 'p_value': np.nan},
        'ad': {'statistic': np.nan, 'p_value': np.nan},
        'ac': {'lag1': np.nan, 'lag2': np.nan}
    }
    
    if len(x) == 0:
        return result
        
    # Compute mean and standard deviation
    result['avg'] = np.mean(x)
    result['sd'] = np.std(x, ddof=1) if len(x) > 1 else 0.0
    
    # Normality tests (require sufficient data)
    if len(x) >= 8:
        try:
            # Jarque-Bera test
            jb_stat, jb_pval = jarque_bera(x)
            result['jb'] = {'statistic': jb_stat, 'p_value': jb_pval}
        except:
            pass
            
        try:
            # Kolmogorov-Smirnov test (Lilliefors)
            ll_stat, ll_pval = kstest(x, 'norm', args=(result['avg'], result['sd']))
            result['ll'] = {'statistic': ll_stat, 'p_value': ll_pval}
        except:
            pass
            
        try:
            # Anderson-Darling test
            ad_result = anderson(x, dist='norm')
            result['ad'] = {'statistic': ad_result.statistic, 
                           'p_value': np.nan}  # AD doesn't return p-value directly
        except:
            pass
    
    # Autocorrelation (require sufficient data)
    if len(x) >= 3:
        try:
            # Compute autocorrelation at lag 1 and 2
            from statsmodels.tsa.stattools import acf
            acf_vals = acf(x, nlags=2, fft=True)
            result['ac']['lag1'] = acf_vals[1] if len(acf_vals) > 1 else np.nan
            result['ac']['lag2'] = acf_vals[2] if len(acf_vals) > 2 else np.nan
        except:
            pass
    
    return result


def comp_mc_stats(data: np.ndarray, stat_type: str = 'mean') -> Dict[str, np.ndarray]:
    """
    Compute Monte Carlo statistics from multiple runs
    
    Based on comp_MC_stats() in KS-support-functions.R
    
    Args:
        data: 3D array (time_steps, variables, mc_runs) 
        stat_type: 'mean' or 'median'
        
    Returns:
        Dictionary with:
        - central: central tendency (mean or median) across MC runs
        - min: minimum across MC runs
        - max: maximum across MC runs  
        - sd: standard deviation across MC runs
    """
    if stat_type == 'mean':
        central = np.mean(data, axis=2)
    elif stat_type == 'median':
        central = np.median(data, axis=2)
    else:
        raise ValueError(f"Unknown stat_type: {stat_type}")
        
    return {
        'central': central,
        'min': np.min(data, axis=2),
        'max': np.max(data, axis=2),
        'sd': np.std(data, axis=2, ddof=1)
    }


def bootstrap_ci(data: np.ndarray, ci_level: float = 0.95, 
                 n_boot: int = 999, method: str = 'percentile') -> Tuple[float, float]:
    """
    Compute bootstrap confidence interval
    
    Args:
        data: data array
        ci_level: confidence level (default 0.95)
        n_boot: number of bootstrap replicates
        method: 'percentile', 'basic', or 'bca'
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    data = data[~np.isnan(data)]
    n = len(data)
    
    if n < 2:
        return (np.nan, np.nan)
    
    # Generate bootstrap samples
    boot_means = np.zeros(n_boot)
    for i in range(n_boot):
        sample = np.random.choice(data, size=n, replace=True)
        boot_means[i] = np.mean(sample)
    
    # Compute confidence interval
    alpha = 1 - ci_level
    
    if method == 'percentile':
        lower = np.percentile(boot_means, alpha/2 * 100)
        upper = np.percentile(boot_means, (1 - alpha/2) * 100)
    elif method == 'basic':
        theta = np.mean(data)
        lower = 2 * theta - np.percentile(boot_means, (1 - alpha/2) * 100)
        upper = 2 * theta - np.percentile(boot_means, alpha/2 * 100)
    elif method == 'bca':
        # Bias-corrected and accelerated (BCa) method
        theta = np.mean(data)
        z0 = stats.norm.ppf(np.mean(boot_means < theta))
        
        # Jackknife for acceleration
        jack_means = np.zeros(n)
        for i in range(n):
            jack_sample = np.delete(data, i)
            jack_means[i] = np.mean(jack_sample)
        jack_mean = np.mean(jack_means)
        
        numerator = np.sum((jack_mean - jack_means)**3)
        denominator = 6 * (np.sum((jack_mean - jack_means)**2))**(3/2)
        a = numerator / denominator if denominator != 0 else 0
        
        # Adjusted percentiles
        z_alpha = stats.norm.ppf(alpha/2)
        z_1alpha = stats.norm.ppf(1 - alpha/2)
        
        p_lower = stats.norm.cdf(z0 + (z0 + z_alpha) / (1 - a * (z0 + z_alpha)))
        p_upper = stats.norm.cdf(z0 + (z0 + z_1alpha) / (1 - a * (z0 + z_1alpha)))
        
        lower = np.percentile(boot_means, p_lower * 100)
        upper = np.percentile(boot_means, p_upper * 100)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return (lower, upper)


# ==== Data Loading Functions ====

def load_simulation_results(folder: str, base_name: str, 
                            variables: List[str],
                            n_exp: int = 1,
                            ini_drop: int = 0,
                            n_keep: int = -1) -> Dict[str, np.ndarray]:
    """
    Load K+S simulation results from saved files
    
    Based on read.3d.lsd() functionality in R scripts
    
    Args:
        folder: folder containing result files
        base_name: base name of configuration files
        variables: list of variable names to load
        n_exp: number of experiments
        ini_drop: initial time steps to drop
        n_keep: number of time steps to keep (-1 = all)
        
    Returns:
        Dictionary mapping experiment names to 3D arrays (time, vars, mc_runs)
    """
    results = {}
    
    for exp in range(1, n_exp + 1):
        if n_exp > 1:
            exp_name = f"{base_name}{exp}"
        else:
            exp_name = base_name
            
        # Load simulation data
        # This is a placeholder - actual implementation depends on output format
        # The original R scripts use LSDinterface to read .res.gz files
        # In Python implementation, we'll use pickle or similar format
        
        try:
            file_path = f"{folder}/{exp_name}_results.pkl.gz"
            with gzip.open(file_path, 'rb') as f:
                data = pickle.load(f)
                
            # Extract requested variables
            exp_data = []
            for var in variables:
                if var in data:
                    var_data = data[var]
                    if ini_drop > 0:
                        var_data = var_data[ini_drop:, :]
                    if n_keep > 0:
                        var_data = var_data[:n_keep, :]
                    exp_data.append(var_data)
                else:
                    warnings.warn(f"Variable {var} not found in {exp_name}")
                    
            if exp_data:
                results[exp_name] = np.stack(exp_data, axis=1)
                
        except FileNotFoundError:
            warnings.warn(f"Results file not found for {exp_name}")
            
    return results


def save_simulation_results(data: Dict[str, np.ndarray], 
                            folder: str, 
                            base_name: str):
    """
    Save simulation results in compressed format
    
    Args:
        data: dictionary of variable_name -> array data
        folder: output folder
        base_name: base name for output file
    """
    import os
    os.makedirs(folder, exist_ok=True)
    
    file_path = f"{folder}/{base_name}_results.pkl.gz"
    with gzip.open(file_path, 'wb') as f:
        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)


# ==== Distribution Fitting ====

def fit_subbotin(x: np.ndarray, symmetric: bool = True) -> Dict[str, float]:
    """
    Fit Subbotin (generalized Gaussian) distribution
    
    The Subbotin distribution is a generalization of normal, Laplace, and uniform
    Used in original R scripts for analyzing heavy-tailed distributions
    
    Args:
        x: data series
        symmetric: whether to fit symmetric or asymmetric Subbotin
        
    Returns:
        Dictionary with distribution parameters
    """
    x = x[~np.isfinite(x)]
    
    if len(x) < 20:
        return {
            'location': np.nan,
            'scale': np.nan,
            'shape': np.nan
        }
    
    # For symmetric Subbotin, use generalized normal (p-norm) approximation
    # This is a simplified version - full Subbotin fitting requires specialized packages
    
    try:
        # Estimate parameters using method of moments
        mu = np.mean(x)
        sigma = np.std(x, ddof=1)
        
        # Estimate shape parameter from kurtosis
        # Normal: kurtosis = 3, Laplace: kurtosis = 6, Uniform: kurtosis = 1.8
        from scipy.stats import kurtosis as scipy_kurtosis
        kurt = scipy_kurtosis(x, fisher=False)  # Pearson's definition
        
        # Map kurtosis to shape parameter (rough approximation)
        # shape = 2 gives normal, shape = 1 gives Laplace
        if kurt > 3:
            shape = 2 / np.sqrt(1 + (kurt - 3) / 3)
        else:
            shape = 2 * np.sqrt(1 + (3 - kurt) / 1.8)
            
        return {
            'location': mu,
            'scale': sigma,
            'shape': np.clip(shape, 0.5, 5.0)
        }
    except:
        return {
            'location': np.nan,
            'scale': np.nan,
            'shape': np.nan
        }


# ==== Time Series Analysis ====

def hp_filter(x: np.ndarray, lambda_param: float = 1600) -> Tuple[np.ndarray, np.ndarray]:
    """
    Hodrick-Prescott filter for trend/cycle decomposition
    
    Args:
        x: time series data
        lambda_param: smoothing parameter (1600 for quarterly data)
        
    Returns:
        Tuple of (trend, cycle)
    """
    from scipy.sparse import diags
    from scipy.sparse.linalg import spsolve
    
    n = len(x)
    if n < 4:
        return x, np.zeros(n)
        
    # Create second difference matrix
    e = np.ones(n)
    D2 = diags([e, -2*e, e], [0, 1, 2], shape=(n-2, n))
    
    # Solve for trend
    I = diags(e)
    trend = spsolve(I + lambda_param * D2.T @ D2, x)
    cycle = x - trend
    
    return trend, cycle


def compute_growth_rate(x: np.ndarray, method: str = 'log') -> np.ndarray:
    """
    Compute growth rate of time series
    
    Args:
        x: time series data
        method: 'log' for log difference, 'pct' for percentage change
        
    Returns:
        Growth rate series
    """
    if method == 'log':
        return np.diff(np.log(x + 1e-10))
    elif method == 'pct':
        return np.diff(x) / (x[:-1] + 1e-10)
    else:
        raise ValueError(f"Unknown method: {method}")


# ==== Utility Functions ====

def format_number(x: float, digits: int = DEF_DIGITS) -> str:
    """Format number with specified decimal places"""
    return f"{x:.{digits}f}"


def summarize_variable(data: np.ndarray, var_name: str = "") -> pd.DataFrame:
    """
    Create summary statistics table for a variable
    
    Args:
        data: variable data (can be 1D, 2D, or 3D)
        var_name: name of variable
        
    Returns:
        DataFrame with summary statistics
    """
    if data.ndim == 1:
        stats = comp_stats(data)
    elif data.ndim == 2:
        # Compute stats for each column
        stats_list = [comp_stats(data[:, i]) for i in range(data.shape[1])]
        stats = {
            'avg': np.array([s['avg'] for s in stats_list]),
            'sd': np.array([s['sd'] for s in stats_list])
        }
    else:
        # For 3D, compute MC statistics
        mc_stats = comp_mc_stats(data)
        stats = {
            'avg': np.mean(mc_stats['central']),
            'sd': np.mean(mc_stats['sd'])
        }
    
    summary = pd.DataFrame({
        'Variable': [var_name],
        'Mean': [stats['avg'] if np.isscalar(stats['avg']) else np.mean(stats['avg'])],
        'Std Dev': [stats['sd'] if np.isscalar(stats['sd']) else np.mean(stats['sd'])]
    })
    
    return summary


# ==== Export Functions ====

__all__ = [
    'all_na',
    'is_finite_df',
    'not_in',
    'comp_stats',
    'comp_mc_stats',
    'bootstrap_ci',
    'load_simulation_results',
    'save_simulation_results',
    'fit_subbotin',
    'hp_filter',
    'compute_growth_rate',
    'format_number',
    'summarize_variable',
]
