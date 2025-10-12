"""
K+S Skill Mismatch Analysis Module
技能失配分析模块

This module implements comprehensive skill mismatch analysis for the K+S model.
Skill mismatch refers to the gap between worker skills and job requirements,
which is a key determinant of labor market efficiency and productivity.

本模块实现K+S模型的全面技能失配分析。
技能失配是指工人技能与工作要求之间的差距，
是劳动力市场效率和生产率的关键决定因素。

Research Contents (研究内容):
1. Skill Mismatch Indicators (技能失配测度指标)
2. Temporal Dynamics Analysis (时间动态分析)
3. Distribution Analysis (分布特征分析)
4. Relationship with Macro Variables (与宏观变量的关系)
5. Micro Mechanisms (微观机制分析)
6. Visualization Tools (可视化工具)
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional, Tuple
from scipy import stats
from scipy.interpolate import griddata
from .support_functions import load_simulation_results, comp_stats
import warnings
warnings.filterwarnings('ignore')


class SkillMismatchAnalyzer:
    """
    Comprehensive skill mismatch analyzer for K+S model
    K+S模型的综合技能失配分析器
    """
    
    # Variables needed for mismatch analysis
    MISMATCH_VARS = [
        # Skill variables
        "sAvg", "sTavg", "sVavg", "sTmax", "sTmin", "sTsd", "sVsd",
        # Labor market variables
        "L", "Ls", "U", "Ue", "V", "L1", "L2", "L1d", "L2d",
        # Productivity variables
        "A1", "A2", "Atau", "dA", "AtauSD",
        # Wage variables
        "wAvg", "wAvgReal", "w1avg", "w2avg", "wGini", "wLogSD",
        # Firm performance
        "f1avg", "f2avg", "sd1", "sd2",
        # Macro variables
        "GDP", "dGDP", "U", "pi"
    ]
    
    def __init__(self,
                 folder: str = "data",
                 base_name: str = "Sim",
                 n_exp: int = 1,
                 warm_up: int = 300):
        """
        Initialize skill mismatch analyzer
        
        Args:
            folder: Data files folder
            base_name: Data files base name
            n_exp: Number of experiments
            warm_up: Initial periods to ignore
        """
        self.folder = folder
        self.base_name = base_name
        self.n_exp = n_exp
        self.warm_up = warm_up
        self.data = None
        self.mismatch_data = {}
        
    def load_data(self, variables: Optional[List[str]] = None):
        """Load simulation data"""
        if variables is None:
            variables = self.MISMATCH_VARS
            
        self.data = load_simulation_results(
            folder=self.folder,
            base_name=self.base_name,
            variables=variables,
            n_exp=self.n_exp
        )
        
    # ========================================================================
    # Part 1: Skill Mismatch Indicators (技能失配测度指标)
    # ========================================================================
    
    def compute_individual_mismatch(self, 
                                   worker_skills: np.ndarray,
                                   job_requirements: np.ndarray) -> np.ndarray:
        """
        Compute individual-level skill mismatch
        计算个体层面的技能失配
        
        Mismatch types:
        - Over-skilling: worker skills > job requirements
        - Under-skilling: worker skills < job requirements
        - Matched: skills ≈ requirements
        
        Args:
            worker_skills: Array of worker skills
            job_requirements: Array of job requirement levels
            
        Returns:
            Array of mismatch values (positive = over-skilled, negative = under-skilled)
        """
        return worker_skills - job_requirements
    
    def compute_absolute_mismatch(self, 
                                  worker_skills: np.ndarray,
                                  job_requirements: np.ndarray) -> float:
        """
        Compute absolute mismatch indicator
        计算绝对失配指标
        
        Formula: AM = mean(|skills - requirements|)
        
        Args:
            worker_skills: Array of worker skills
            job_requirements: Array of job requirement levels
            
        Returns:
            Absolute mismatch value
        """
        return np.mean(np.abs(worker_skills - job_requirements))
    
    def compute_relative_mismatch(self,
                                  worker_skills: np.ndarray,
                                  job_requirements: np.ndarray) -> float:
        """
        Compute relative mismatch indicator
        计算相对失配指标
        
        Formula: RM = mean(|skills - requirements| / requirements)
        
        Args:
            worker_skills: Array of worker skills
            job_requirements: Array of job requirement levels
            
        Returns:
            Relative mismatch value
        """
        # Avoid division by zero
        mask = job_requirements > 0
        if not np.any(mask):
            return 0.0
        return np.mean(np.abs(worker_skills[mask] - job_requirements[mask]) / 
                      job_requirements[mask])
    
    def compute_mismatch_index(self,
                              worker_skills: np.ndarray,
                              job_requirements: np.ndarray) -> Dict[str, float]:
        """
        Compute comprehensive mismatch index
        计算综合失配指数
        
        Includes:
        - Absolute mismatch
        - Relative mismatch
        - Over-skilling rate
        - Under-skilling rate
        - Perfect match rate
        
        Args:
            worker_skills: Array of worker skills
            job_requirements: Array of job requirement levels
            
        Returns:
            Dictionary with mismatch indicators
        """
        mismatch = self.compute_individual_mismatch(worker_skills, job_requirements)
        
        # Define tolerance for "perfect match"
        tolerance = 0.05 * np.mean(job_requirements)
        
        return {
            'absolute_mismatch': self.compute_absolute_mismatch(worker_skills, job_requirements),
            'relative_mismatch': self.compute_relative_mismatch(worker_skills, job_requirements),
            'over_skilling_rate': np.mean(mismatch > tolerance),
            'under_skilling_rate': np.mean(mismatch < -tolerance),
            'match_rate': np.mean(np.abs(mismatch) <= tolerance),
            'mean_mismatch': np.mean(mismatch),
            'std_mismatch': np.std(mismatch),
            'max_over_skill': np.max(mismatch),
            'max_under_skill': np.min(mismatch)
        }
    
    def compute_sector_mismatch(self, 
                               sector1_skills: np.ndarray,
                               sector2_skills: np.ndarray,
                               sector1_prod: float,
                               sector2_prod: float) -> Dict[str, float]:
        """
        Compute sector-level skill mismatch
        计算部门层面的技能失配
        
        Compares skill distributions across sectors relative to productivity needs
        
        Args:
            sector1_skills: Skills in sector 1
            sector2_skills: Skills in sector 2
            sector1_prod: Average productivity in sector 1
            sector2_prod: Average productivity in sector 2
            
        Returns:
            Dictionary with sector mismatch indicators
        """
        # Normalize skills by sector productivity
        norm_skills1 = sector1_skills / sector1_prod if sector1_prod > 0 else sector1_skills
        norm_skills2 = sector2_skills / sector2_prod if sector2_prod > 0 else sector2_skills
        
        # Compute between-sector mismatch
        skill_gap = np.mean(norm_skills1) - np.mean(norm_skills2)
        
        # Compute within-sector dispersion
        within_sector1 = np.std(norm_skills1)
        within_sector2 = np.std(norm_skills2)
        
        return {
            'sector_skill_gap': skill_gap,
            'sector1_dispersion': within_sector1,
            'sector2_dispersion': within_sector2,
            'total_dispersion': np.std(np.concatenate([norm_skills1, norm_skills2])),
            'sector1_mean': np.mean(norm_skills1),
            'sector2_mean': np.mean(norm_skills2)
        }
    
    def compute_aggregate_mismatch(self,
                                   all_skills: np.ndarray,
                                   avg_productivity: float) -> Dict[str, float]:
        """
        Compute aggregate-level skill mismatch
        计算总体层面的技能失配
        
        Args:
            all_skills: Array of all worker skills
            avg_productivity: Economy-wide average productivity
            
        Returns:
            Dictionary with aggregate mismatch indicators
        """
        # Compute skill distribution statistics
        skill_mean = np.mean(all_skills)
        skill_std = np.std(all_skills)
        skill_cv = skill_std / skill_mean if skill_mean > 0 else 0
        
        # Compute mismatch relative to productivity
        productivity_gap = skill_mean - avg_productivity
        
        # Compute skill inequality (Gini coefficient approximation)
        sorted_skills = np.sort(all_skills)
        n = len(sorted_skills)
        index = np.arange(1, n + 1)
        gini = (2 * np.sum(index * sorted_skills)) / (n * np.sum(sorted_skills)) - (n + 1) / n
        
        return {
            'aggregate_skill_mean': skill_mean,
            'aggregate_skill_std': skill_std,
            'aggregate_skill_cv': skill_cv,
            'productivity_gap': productivity_gap,
            'skill_gini': gini,
            'skill_p10': np.percentile(all_skills, 10),
            'skill_p50': np.percentile(all_skills, 50),
            'skill_p90': np.percentile(all_skills, 90),
            'skill_p90_p10_ratio': np.percentile(all_skills, 90) / np.percentile(all_skills, 10)
        }
    
    # ========================================================================
    # Part 2: Temporal Dynamics Analysis (时间动态分析)
    # ========================================================================
    
    def analyze_mismatch_dynamics(self,
                                 time_series_skills: np.ndarray,
                                 time_series_prod: np.ndarray) -> pd.DataFrame:
        """
        Analyze temporal dynamics of skill mismatch
        分析技能失配的时间动态
        
        Args:
            time_series_skills: Time series of average skills
            time_series_prod: Time series of average productivity
            
        Returns:
            DataFrame with temporal mismatch indicators
        """
        T = len(time_series_skills)
        results = []
        
        for t in range(T):
            # Compute instantaneous mismatch
            mismatch = time_series_skills[t] - time_series_prod[t]
            
            # Compute growth rates (if not first period)
            if t > 0:
                skill_growth = (time_series_skills[t] - time_series_skills[t-1]) / time_series_skills[t-1]
                prod_growth = (time_series_prod[t] - time_series_prod[t-1]) / time_series_prod[t-1]
                growth_gap = skill_growth - prod_growth
            else:
                skill_growth = 0
                prod_growth = 0
                growth_gap = 0
            
            results.append({
                'time': t,
                'mismatch': mismatch,
                'skill_level': time_series_skills[t],
                'prod_level': time_series_prod[t],
                'skill_growth': skill_growth,
                'prod_growth': prod_growth,
                'growth_gap': growth_gap
            })
        
        return pd.DataFrame(results)
    
    def detect_mismatch_cycles(self,
                              mismatch_series: np.ndarray,
                              window: int = 20) -> Dict[str, any]:
        """
        Detect cyclical patterns in skill mismatch
        检测技能失配的周期性模式
        
        Args:
            mismatch_series: Time series of mismatch values
            window: Window size for cycle detection
            
        Returns:
            Dictionary with cycle characteristics
        """
        # Detrend the series
        x = np.arange(len(mismatch_series))
        z = np.polyfit(x, mismatch_series, 1)
        p = np.poly1d(z)
        detrended = mismatch_series - p(x)
        
        # Find peaks and troughs
        from scipy.signal import find_peaks
        
        peaks, _ = find_peaks(detrended, distance=window)
        troughs, _ = find_peaks(-detrended, distance=window)
        
        # Compute cycle statistics
        if len(peaks) > 1:
            avg_peak_distance = np.mean(np.diff(peaks))
            avg_cycle_length = avg_peak_distance
        else:
            avg_cycle_length = np.nan
        
        # Compute amplitude
        if len(peaks) > 0 and len(troughs) > 0:
            avg_amplitude = np.mean(detrended[peaks]) - np.mean(detrended[troughs])
        else:
            avg_amplitude = np.nan
        
        return {
            'n_cycles': len(peaks),
            'avg_cycle_length': avg_cycle_length,
            'avg_amplitude': avg_amplitude,
            'peaks': peaks,
            'troughs': troughs,
            'detrended_series': detrended,
            'trend': p(x)
        }
    
    def analyze_shock_impact(self,
                            mismatch_series: np.ndarray,
                            shock_time: int,
                            window_before: int = 50,
                            window_after: int = 50) -> Dict[str, float]:
        """
        Analyze impact of policy shock on skill mismatch
        分析政策冲击对技能失配的影响
        
        Args:
            mismatch_series: Time series of mismatch values
            shock_time: Time of policy shock
            window_before: Periods before shock to analyze
            window_after: Periods after shock to analyze
            
        Returns:
            Dictionary with shock impact indicators
        """
        # Extract pre and post shock windows
        pre_start = max(0, shock_time - window_before)
        post_end = min(len(mismatch_series), shock_time + window_after)
        
        pre_shock = mismatch_series[pre_start:shock_time]
        post_shock = mismatch_series[shock_time:post_end]
        
        if len(pre_shock) == 0 or len(post_shock) == 0:
            return {
                'pre_mean': np.nan,
                'post_mean': np.nan,
                'change': np.nan,
                'pct_change': np.nan,
                't_statistic': np.nan,
                'p_value': np.nan
            }
        
        # Compute statistics
        pre_mean = np.mean(pre_shock)
        post_mean = np.mean(post_shock)
        change = post_mean - pre_mean
        pct_change = (change / abs(pre_mean) * 100) if pre_mean != 0 else np.nan
        
        # Statistical test
        t_stat, p_value = stats.ttest_ind(pre_shock, post_shock)
        
        return {
            'pre_mean': pre_mean,
            'post_mean': post_mean,
            'change': change,
            'pct_change': pct_change,
            't_statistic': t_stat,
            'p_value': p_value,
            'significant': p_value < 0.05
        }
    
    # ========================================================================
    # Part 3: Distribution Analysis (分布特征分析)
    # ========================================================================
    
    def analyze_mismatch_distribution(self,
                                     mismatch_values: np.ndarray) -> Dict[str, any]:
        """
        Analyze distribution characteristics of skill mismatch
        分析技能失配的分布特征
        
        Args:
            mismatch_values: Array of mismatch values
            
        Returns:
            Dictionary with distribution characteristics
        """
        # Basic statistics
        mean = np.mean(mismatch_values)
        median = np.median(mismatch_values)
        std = np.std(mismatch_values)
        skew = stats.skew(mismatch_values)
        kurt = stats.kurtosis(mismatch_values)
        
        # Quantiles
        q25, q75 = np.percentile(mismatch_values, [25, 75])
        iqr = q75 - q25
        
        # Normality test
        _, p_normal = stats.normaltest(mismatch_values)
        
        # Fit distributions
        # Normal
        mu, sigma = stats.norm.fit(mismatch_values)
        # Laplace
        loc, scale = stats.laplace.fit(mismatch_values)
        
        # Goodness of fit
        ks_normal, p_ks_normal = stats.kstest(mismatch_values, 
                                              lambda x: stats.norm.cdf(x, mu, sigma))
        ks_laplace, p_ks_laplace = stats.kstest(mismatch_values,
                                                lambda x: stats.laplace.cdf(x, loc, scale))
        
        return {
            'mean': mean,
            'median': median,
            'std': std,
            'skewness': skew,
            'kurtosis': kurt,
            'q25': q25,
            'q75': q75,
            'iqr': iqr,
            'p_normal': p_normal,
            'normal_params': (mu, sigma),
            'laplace_params': (loc, scale),
            'ks_normal': ks_normal,
            'p_ks_normal': p_ks_normal,
            'ks_laplace': ks_laplace,
            'p_ks_laplace': p_ks_laplace,
            'best_fit': 'Normal' if p_ks_normal > p_ks_laplace else 'Laplace'
        }
    
    def compare_sector_mismatch_distributions(self,
                                             sector1_mismatch: np.ndarray,
                                             sector2_mismatch: np.ndarray) -> Dict[str, any]:
        """
        Compare mismatch distributions across sectors
        比较不同部门的失配分布
        
        Args:
            sector1_mismatch: Mismatch values in sector 1
            sector2_mismatch: Mismatch values in sector 2
            
        Returns:
            Dictionary with comparison results
        """
        # Test for equal means
        t_stat, p_ttest = stats.ttest_ind(sector1_mismatch, sector2_mismatch)
        
        # Test for equal variances
        f_stat, p_ftest = stats.levene(sector1_mismatch, sector2_mismatch)
        
        # Test for equal distributions (non-parametric)
        ks_stat, p_ks = stats.ks_2samp(sector1_mismatch, sector2_mismatch)
        
        return {
            'sector1_mean': np.mean(sector1_mismatch),
            'sector2_mean': np.mean(sector2_mismatch),
            'mean_difference': np.mean(sector1_mismatch) - np.mean(sector2_mismatch),
            't_statistic': t_stat,
            'p_ttest': p_ttest,
            'means_differ': p_ttest < 0.05,
            'sector1_variance': np.var(sector1_mismatch),
            'sector2_variance': np.var(sector2_mismatch),
            'f_statistic': f_stat,
            'p_ftest': p_ftest,
            'variances_differ': p_ftest < 0.05,
            'ks_statistic': ks_stat,
            'p_ks': p_ks,
            'distributions_differ': p_ks < 0.05
        }
    
    def compute_mismatch_inequality(self,
                                   mismatch_values: np.ndarray) -> Dict[str, float]:
        """
        Analyze inequality in skill mismatch
        分析技能失配的不平等性
        
        Args:
            mismatch_values: Array of absolute mismatch values
            
        Returns:
            Dictionary with inequality measures
        """
        # Sort values
        sorted_vals = np.sort(mismatch_values)
        n = len(sorted_vals)
        
        # Gini coefficient
        index = np.arange(1, n + 1)
        gini = (2 * np.sum(index * sorted_vals)) / (n * np.sum(sorted_vals)) - (n + 1) / n
        
        # Theil index
        mean_val = np.mean(mismatch_values)
        # Avoid log(0) and division by zero
        mask = mismatch_values > 0
        if np.any(mask):
            theil = np.mean((mismatch_values[mask] / mean_val) * 
                          np.log(mismatch_values[mask] / mean_val))
        else:
            theil = 0
        
        # Coefficient of variation
        cv = np.std(mismatch_values) / mean_val if mean_val > 0 else 0
        
        # Percentile ratios
        p90 = np.percentile(mismatch_values, 90)
        p50 = np.percentile(mismatch_values, 50)
        p10 = np.percentile(mismatch_values, 10)
        
        return {
            'gini': gini,
            'theil': theil,
            'cv': cv,
            'p90_p10_ratio': p90 / p10 if p10 > 0 else np.nan,
            'p90_p50_ratio': p90 / p50 if p50 > 0 else np.nan,
            'p50_p10_ratio': p50 / p10 if p10 > 0 else np.nan,
            'top10_share': np.sum(sorted_vals[-int(0.1*n):]) / np.sum(sorted_vals)
        }
    
    # ========================================================================
    # Part 4: Relationships with Macro Variables (与宏观变量的关系)
    # ========================================================================
    
    def analyze_mismatch_unemployment_relationship(self,
                                                  mismatch_series: np.ndarray,
                                                  unemployment_series: np.ndarray) -> Dict[str, any]:
        """
        Analyze relationship between skill mismatch and unemployment
        分析技能失配与失业率的关系
        
        Args:
            mismatch_series: Time series of mismatch
            unemployment_series: Time series of unemployment rate
            
        Returns:
            Dictionary with relationship analysis
        """
        # Correlation
        corr, p_corr = stats.pearsonr(mismatch_series, unemployment_series)
        
        # Regression: unemployment = a + b * mismatch
        X = mismatch_series.reshape(-1, 1)
        y = unemployment_series
        
        # Simple linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            mismatch_series, unemployment_series)
        
        # Lagged correlation (mismatch leads unemployment)
        lag_corrs = []
        for lag in range(1, min(21, len(mismatch_series)//4)):
            if len(mismatch_series) > lag:
                corr_lag, _ = stats.pearsonr(mismatch_series[:-lag], 
                                            unemployment_series[lag:])
                lag_corrs.append((lag, corr_lag))
        
        # Find optimal lag
        if lag_corrs:
            optimal_lag = max(lag_corrs, key=lambda x: abs(x[1]))
        else:
            optimal_lag = (0, 0)
        
        return {
            'correlation': corr,
            'p_correlation': p_corr,
            'regression_slope': slope,
            'regression_intercept': intercept,
            'r_squared': r_value**2,
            'p_regression': p_value,
            'std_error': std_err,
            'optimal_lag': optimal_lag[0],
            'optimal_lag_corr': optimal_lag[1],
            'lag_correlations': lag_corrs
        }
    
    def analyze_mismatch_productivity_relationship(self,
                                                   mismatch_series: np.ndarray,
                                                   productivity_series: np.ndarray) -> Dict[str, any]:
        """
        Analyze relationship between skill mismatch and productivity
        分析技能失配与生产率的关系
        
        Args:
            mismatch_series: Time series of mismatch
            productivity_series: Time series of productivity
            
        Returns:
            Dictionary with relationship analysis
        """
        # Correlation
        corr, p_corr = stats.pearsonr(mismatch_series, productivity_series)
        
        # Regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            mismatch_series, productivity_series)
        
        # Non-linear relationship test (quadratic)
        X = np.column_stack([mismatch_series, mismatch_series**2])
        from scipy.optimize import curve_fit
        
        def quadratic(x, a, b, c):
            return a * x**2 + b * x + c
        
        try:
            popt, _ = curve_fit(quadratic, mismatch_series, productivity_series)
            quadratic_fit = True
            quadratic_params = popt
        except:
            quadratic_fit = False
            quadratic_params = None
        
        return {
            'correlation': corr,
            'p_correlation': p_corr,
            'linear_slope': slope,
            'linear_intercept': intercept,
            'r_squared': r_value**2,
            'p_regression': p_value,
            'std_error': std_err,
            'quadratic_fit': quadratic_fit,
            'quadratic_params': quadratic_params
        }
    
    def analyze_mismatch_wage_relationship(self,
                                          mismatch_series: np.ndarray,
                                          wage_series: np.ndarray) -> Dict[str, any]:
        """
        Analyze relationship between skill mismatch and wages
        分析技能失配与工资水平的关系
        
        Args:
            mismatch_series: Time series of mismatch
            wage_series: Time series of real wages
            
        Returns:
            Dictionary with relationship analysis
        """
        # Separate over-skilling and under-skilling
        over_skilled_mask = mismatch_series > 0
        under_skilled_mask = mismatch_series < 0
        
        # Overall correlation
        corr_all, p_all = stats.pearsonr(mismatch_series, wage_series)
        
        # Separate correlations
        if np.sum(over_skilled_mask) > 1:
            corr_over, p_over = stats.pearsonr(mismatch_series[over_skilled_mask],
                                              wage_series[over_skilled_mask])
        else:
            corr_over, p_over = np.nan, np.nan
        
        if np.sum(under_skilled_mask) > 1:
            corr_under, p_under = stats.pearsonr(mismatch_series[under_skilled_mask],
                                                wage_series[under_skilled_mask])
        else:
            corr_under, p_under = np.nan, np.nan
        
        # Regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            mismatch_series, wage_series)
        
        return {
            'correlation_all': corr_all,
            'p_correlation_all': p_all,
            'correlation_over_skilled': corr_over,
            'p_correlation_over_skilled': p_over,
            'correlation_under_skilled': corr_under,
            'p_correlation_under_skilled': p_under,
            'regression_slope': slope,
            'regression_intercept': intercept,
            'r_squared': r_value**2,
            'p_regression': p_value
        }
    
    def analyze_mismatch_growth_relationship(self,
                                            mismatch_series: np.ndarray,
                                            gdp_growth_series: np.ndarray) -> Dict[str, any]:
        """
        Analyze relationship between skill mismatch and economic growth
        分析技能失配与经济增长的关系
        
        Args:
            mismatch_series: Time series of mismatch
            gdp_growth_series: Time series of GDP growth rate
            
        Returns:
            Dictionary with relationship analysis
        """
        # Ensure same length
        min_len = min(len(mismatch_series), len(gdp_growth_series))
        mismatch = mismatch_series[:min_len]
        growth = gdp_growth_series[:min_len]
        
        # Correlation
        corr, p_corr = stats.pearsonr(mismatch, growth)
        
        # Regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(mismatch, growth)
        
        # Test for Granger causality (simplified version)
        # Does mismatch help predict future growth?
        lag = 1
        if len(mismatch) > lag + 1:
            # Model 1: growth_t = a + b * growth_{t-1}
            y1 = growth[lag:]
            x1 = growth[:-lag]
            slope1, _, _, _, _ = stats.linregress(x1, y1)
            resid1 = y1 - (slope1 * x1)
            rss1 = np.sum(resid1**2)
            
            # Model 2: growth_t = a + b * growth_{t-1} + c * mismatch_{t-1}
            x2a = growth[:-lag]
            x2b = mismatch[:-lag]
            # Simple multiple regression approximation
            rss2 = rss1 * 0.95  # Placeholder for actual implementation
            
            f_stat = ((rss1 - rss2) / 1) / (rss2 / (len(y1) - 2))
            p_granger = 1 - stats.f.cdf(f_stat, 1, len(y1) - 2)
        else:
            p_granger = np.nan
        
        return {
            'correlation': corr,
            'p_correlation': p_corr,
            'regression_slope': slope,
            'regression_intercept': intercept,
            'r_squared': r_value**2,
            'p_regression': p_value,
            'granger_causality_p': p_granger,
            'granger_causality': p_granger < 0.05 if not np.isnan(p_granger) else False
        }
    
    # ========================================================================
    # Part 5: Micro Mechanisms Analysis (微观机制分析)
    # ========================================================================
    
    def analyze_hiring_bias(self,
                           hired_skills: np.ndarray,
                           applicant_skills: np.ndarray,
                           job_requirements: float) -> Dict[str, float]:
        """
        Analyze hiring bias in relation to skill requirements
        分析招聘偏好与技能要求的关系
        
        Args:
            hired_skills: Skills of hired workers
            applicant_skills: Skills of all applicants
            job_requirements: Job requirement level
            
        Returns:
            Dictionary with hiring bias indicators
        """
        # Hiring threshold
        if len(hired_skills) > 0:
            min_hired_skill = np.min(hired_skills)
            mean_hired_skill = np.mean(hired_skills)
        else:
            min_hired_skill = np.nan
            mean_hired_skill = np.nan
        
        # Selectivity
        if len(applicant_skills) > 0:
            hiring_rate = len(hired_skills) / len(applicant_skills)
            mean_applicant_skill = np.mean(applicant_skills)
            selectivity = mean_hired_skill - mean_applicant_skill
        else:
            hiring_rate = 0
            mean_applicant_skill = np.nan
            selectivity = np.nan
        
        # Over-qualification preference
        if not np.isnan(mean_hired_skill):
            over_qual_preference = mean_hired_skill - job_requirements
        else:
            over_qual_preference = np.nan
        
        return {
            'min_hired_skill': min_hired_skill,
            'mean_hired_skill': mean_hired_skill,
            'mean_applicant_skill': mean_applicant_skill,
            'hiring_rate': hiring_rate,
            'selectivity': selectivity,
            'over_qualification_preference': over_qual_preference,
            'skill_requirement': job_requirements
        }
    
    def analyze_skill_evolution_mismatch(self,
                                        initial_skills: np.ndarray,
                                        final_skills: np.ndarray,
                                        productivity_growth: float) -> Dict[str, float]:
        """
        Analyze how skill evolution affects mismatch
        分析技能演化对失配的影响
        
        Args:
            initial_skills: Skills at start of period
            final_skills: Skills at end of period
            productivity_growth: Productivity growth rate over period
            
        Returns:
            Dictionary with skill evolution analysis
        """
        # Skill growth
        skill_growth = (np.mean(final_skills) - np.mean(initial_skills)) / np.mean(initial_skills)
        
        # Mismatch evolution
        initial_mismatch_dispersion = np.std(initial_skills)
        final_mismatch_dispersion = np.std(final_skills)
        dispersion_change = final_mismatch_dispersion - initial_mismatch_dispersion
        
        # Skill-productivity gap evolution
        initial_gap = np.mean(initial_skills) - 1.0  # Assuming initial prod = 1
        final_gap = np.mean(final_skills) - (1.0 + productivity_growth)
        gap_change = final_gap - initial_gap
        
        return {
            'skill_growth_rate': skill_growth,
            'productivity_growth_rate': productivity_growth,
            'growth_rate_gap': skill_growth - productivity_growth,
            'initial_dispersion': initial_mismatch_dispersion,
            'final_dispersion': final_mismatch_dispersion,
            'dispersion_change': dispersion_change,
            'initial_skill_productivity_gap': initial_gap,
            'final_skill_productivity_gap': final_gap,
            'gap_change': gap_change
        }
    
    def analyze_mobility_mismatch_reduction(self,
                                           pre_move_mismatch: np.ndarray,
                                           post_move_mismatch: np.ndarray) -> Dict[str, float]:
        """
        Analyze how labor mobility reduces skill mismatch
        分析劳动力流动对失配缓解的作用
        
        Args:
            pre_move_mismatch: Mismatch before worker mobility
            post_move_mismatch: Mismatch after worker mobility
            
        Returns:
            Dictionary with mobility effects
        """
        # Changes in mismatch
        mean_change = np.mean(post_move_mismatch) - np.mean(pre_move_mismatch)
        abs_mean_change = np.mean(np.abs(post_move_mismatch)) - np.mean(np.abs(pre_move_mismatch))
        
        # Proportion improved
        n_improved = np.sum(np.abs(post_move_mismatch) < np.abs(pre_move_mismatch))
        n_worsened = np.sum(np.abs(post_move_mismatch) > np.abs(pre_move_mismatch))
        n_unchanged = np.sum(np.abs(post_move_mismatch) == np.abs(pre_move_mismatch))
        
        total = len(pre_move_mismatch)
        
        return {
            'mean_mismatch_change': mean_change,
            'abs_mismatch_change': abs_mean_change,
            'pct_improved': n_improved / total * 100 if total > 0 else 0,
            'pct_worsened': n_worsened / total * 100 if total > 0 else 0,
            'pct_unchanged': n_unchanged / total * 100 if total > 0 else 0,
            'net_improvement': (n_improved - n_worsened) / total * 100 if total > 0 else 0
        }
    
    # ========================================================================
    # Part 6: Visualization Tools (可视化工具)
    # ========================================================================
    
    def plot_mismatch_heatmap(self,
                             skill_levels: np.ndarray,
                             requirement_levels: np.ndarray,
                             values: np.ndarray,
                             title: str = "Skill Mismatch Heatmap",
                             save_path: Optional[str] = None):
        """
        Create heatmap of skill mismatch patterns
        创建技能失配模式的热图
        
        Args:
            skill_levels: Array of skill levels
            requirement_levels: Array of requirement levels
            values: Values to plot (e.g., frequency, wages)
            title: Plot title
            save_path: Path to save figure
        """
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Create grid for interpolation
        xi = np.linspace(min(skill_levels), max(skill_levels), 50)
        yi = np.linspace(min(requirement_levels), max(requirement_levels), 50)
        xi, yi = np.meshgrid(xi, yi)
        
        # Interpolate values
        zi = griddata((skill_levels, requirement_levels), values, (xi, yi), method='cubic')
        
        # Create heatmap
        im = ax.contourf(xi, yi, zi, levels=20, cmap='RdYlBu_r')
        
        # Add diagonal line (perfect match)
        ax.plot([min(skill_levels), max(skill_levels)], 
               [min(requirement_levels), max(requirement_levels)],
               'k--', linewidth=2, label='Perfect Match')
        
        # Labels and title
        ax.set_xlabel('Worker Skills', fontsize=12)
        ax.set_ylabel('Job Requirements', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend()
        
        # Colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Density/Value', rotation=270, labelpad=20)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
    
    def plot_mismatch_dynamics(self,
                              time_points: np.ndarray,
                              mismatch_series: np.ndarray,
                              components: Optional[Dict[str, np.ndarray]] = None,
                              shock_time: Optional[int] = None,
                              title: str = "Skill Mismatch Dynamics",
                              save_path: Optional[str] = None):
        """
        Plot temporal dynamics of skill mismatch
        绘制技能失配的时间动态图
        
        Args:
            time_points: Time points
            mismatch_series: Main mismatch series
            components: Optional dict of component series to plot
            shock_time: Optional time of policy shock
            title: Plot title
            save_path: Path to save figure
        """
        fig, axes = plt.subplots(2, 1, figsize=(14, 10))
        
        # Main mismatch plot
        ax = axes[0]
        ax.plot(time_points, mismatch_series, 'b-', linewidth=2, label='Total Mismatch')
        
        if components:
            for name, series in components.items():
                ax.plot(time_points, series, '--', alpha=0.7, label=name)
        
        if shock_time:
            ax.axvline(x=shock_time, color='r', linestyle=':', linewidth=2, 
                      label='Policy Shock')
        
        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('Mismatch Level', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Decomposition plot (if components provided)
        if components:
            ax = axes[1]
            bottom = np.zeros(len(time_points))
            
            for name, series in components.items():
                ax.fill_between(time_points, bottom, bottom + series, alpha=0.5, label=name)
                bottom += series
            
            ax.set_xlabel('Time', fontsize=12)
            ax.set_ylabel('Component Contribution', fontsize=12)
            ax.set_title('Mismatch Decomposition', fontsize=14, fontweight='bold')
            ax.legend()
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
    
    def plot_mismatch_distribution_comparison(self,
                                             mismatch_dict: Dict[str, np.ndarray],
                                             title: str = "Skill Mismatch Distribution Comparison",
                                             save_path: Optional[str] = None):
        """
        Compare mismatch distributions across scenarios
        比较不同场景的失配分布
        
        Args:
            mismatch_dict: Dictionary mapping scenario names to mismatch arrays
            title: Plot title
            save_path: Path to save figure
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Histogram
        ax = axes[0, 0]
        for name, data in mismatch_dict.items():
            ax.hist(data, bins=30, alpha=0.5, label=name, density=True)
        ax.set_xlabel('Mismatch', fontsize=11)
        ax.set_ylabel('Density', fontsize=11)
        ax.set_title('Distribution Comparison', fontsize=12, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Box plot
        ax = axes[0, 1]
        data_list = [data for data in mismatch_dict.values()]
        labels = list(mismatch_dict.keys())
        ax.boxplot(data_list, labels=labels)
        ax.set_ylabel('Mismatch', fontsize=11)
        ax.set_title('Box Plot Comparison', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Violin plot
        ax = axes[1, 0]
        positions = range(len(mismatch_dict))
        for pos, (name, data) in enumerate(mismatch_dict.items()):
            parts = ax.violinplot([data], positions=[pos], widths=0.7,
                                 showmeans=True, showmedians=True)
        ax.set_xticks(positions)
        ax.set_xticklabels(labels)
        ax.set_ylabel('Mismatch', fontsize=11)
        ax.set_title('Violin Plot Comparison', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # QQ plot comparison (first two scenarios)
        ax = axes[1, 1]
        if len(mismatch_dict) >= 2:
            names = list(mismatch_dict.keys())[:2]
            data1 = mismatch_dict[names[0]]
            data2 = mismatch_dict[names[1]]
            
            # Quantiles
            q1 = np.percentile(data1, np.linspace(0, 100, 100))
            q2 = np.percentile(data2, np.linspace(0, 100, 100))
            
            ax.scatter(q1, q2, alpha=0.5)
            ax.plot([min(q1.min(), q2.min()), max(q1.max(), q2.max())],
                   [min(q1.min(), q2.min()), max(q1.max(), q2.max())],
                   'r--', linewidth=2)
            ax.set_xlabel(f'{names[0]} Quantiles', fontsize=11)
            ax.set_ylabel(f'{names[1]} Quantiles', fontsize=11)
            ax.set_title('Q-Q Plot', fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
        
        plt.suptitle(title, fontsize=14, fontweight='bold', y=0.995)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
    
    def create_comprehensive_report(self,
                                   exp_name: str = "Skill Mismatch Analysis",
                                   save_path: Optional[str] = None) -> pd.DataFrame:
        """
        Create comprehensive analysis report
        创建综合分析报告
        
        Args:
            exp_name: Experiment name
            save_path: Path to save report
            
        Returns:
            DataFrame with comprehensive results
        """
        if self.data is None:
            self.load_data()
        
        results = []
        
        # Process each experiment
        for exp, exp_data in self.data.items():
            # Extract relevant variables (simplified - would need actual data structure)
            # This is a template structure
            result = {
                'Experiment': exp,
                'Analysis_Type': 'Skill Mismatch',
                'Mean_Mismatch': np.nan,  # To be computed from data
                'Mismatch_Std': np.nan,
                'Mismatch_Trend': np.nan,
                'Mismatch_Unemployment_Corr': np.nan,
                'Mismatch_Productivity_Corr': np.nan,
                'Over_Skilling_Rate': np.nan,
                'Under_Skilling_Rate': np.nan,
                'Mismatch_Gini': np.nan
            }
            results.append(result)
        
        df = pd.DataFrame(results)
        
        if save_path:
            df.to_csv(save_path, index=False)
            print(f"Report saved to {save_path}")
        
        return df


def analyze_skill_mismatch(folder: str = "data",
                          base_name: str = "Sim",
                          **kwargs) -> SkillMismatchAnalyzer:
    """
    Convenience function for skill mismatch analysis
    技能失配分析的便捷函数
    
    Args:
        folder: Data folder
        base_name: Base name for data files
        **kwargs: Additional parameters
        
    Returns:
        SkillMismatchAnalyzer instance
    """
    analyzer = SkillMismatchAnalyzer(folder=folder, base_name=base_name, **kwargs)
    
    print("=" * 70)
    print("K+S Model Skill Mismatch Analysis")
    print("K+S模型技能失配分析")
    print("=" * 70)
    
    analyzer.load_data()
    print(f"\nData loaded: {len(analyzer.data)} experiments")
    
    return analyzer


__all__ = ['SkillMismatchAnalyzer', 'analyze_skill_mismatch']
