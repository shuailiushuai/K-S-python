"""
Example: Skill Mismatch Analysis
示例：技能失配分析

This example demonstrates comprehensive skill mismatch analysis 
for the K+S model, including:
1. Individual and aggregate mismatch indicators
2. Temporal dynamics and cyclical patterns
3. Distribution characteristics
4. Relationships with macro variables
5. Micro mechanisms
6. Visualization tools

本示例演示K+S模型的全面技能失配分析，包括：
1. 个体和总体失配指标
2. 时间动态和周期模式
3. 分布特征
4. 与宏观变量的关系
5. 微观机制
6. 可视化工具
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from analysis.skill_mismatch_analysis import SkillMismatchAnalyzer


def example_basic_mismatch_indicators():
    """
    Example 1: Basic Skill Mismatch Indicators
    示例1：基本技能失配指标
    """
    print("\n" + "="*70)
    print("Example 1: Basic Skill Mismatch Indicators")
    print("示例1：基本技能失配指标")
    print("="*70)
    
    # Create analyzer
    analyzer = SkillMismatchAnalyzer()
    
    # Simulate worker skills and job requirements
    np.random.seed(42)
    n_workers = 1000
    
    # Worker skills: normal distribution with mean 1.2, std 0.3
    worker_skills = np.random.normal(1.2, 0.3, n_workers)
    worker_skills = np.clip(worker_skills, 0.5, 2.5)  # Bound skills
    
    # Job requirements: normal distribution with mean 1.0, std 0.2
    job_requirements = np.random.normal(1.0, 0.2, n_workers)
    job_requirements = np.clip(job_requirements, 0.5, 2.0)
    
    # Compute mismatch indicators
    print("\n1.1 Individual-level mismatch:")
    individual_mismatch = analyzer.compute_individual_mismatch(worker_skills, job_requirements)
    print(f"   Mean mismatch: {np.mean(individual_mismatch):.4f}")
    print(f"   Mismatch std dev: {np.std(individual_mismatch):.4f}")
    
    print("\n1.2 Aggregate mismatch indicators:")
    mismatch_idx = analyzer.compute_mismatch_index(worker_skills, job_requirements)
    for key, value in mismatch_idx.items():
        print(f"   {key}: {value:.4f}")
    
    print("\n1.3 Absolute and relative mismatch:")
    abs_mismatch = analyzer.compute_absolute_mismatch(worker_skills, job_requirements)
    rel_mismatch = analyzer.compute_relative_mismatch(worker_skills, job_requirements)
    print(f"   Absolute mismatch: {abs_mismatch:.4f}")
    print(f"   Relative mismatch: {rel_mismatch:.4f}")
    
    return analyzer, worker_skills, job_requirements, individual_mismatch


def example_sector_comparison():
    """
    Example 2: Sector-level Mismatch Comparison
    示例2：部门层面失配比较
    """
    print("\n" + "="*70)
    print("Example 2: Sector-level Mismatch Comparison")
    print("示例2：部门层面失配比较")
    print("="*70)
    
    analyzer = SkillMismatchAnalyzer()
    
    # Simulate sector data
    np.random.seed(42)
    n_workers_s1 = 400
    n_workers_s2 = 600
    
    # Sector 1: Capital goods (higher skills)
    sector1_skills = np.random.normal(1.4, 0.25, n_workers_s1)
    sector1_prod = 1.3
    
    # Sector 2: Consumption goods (lower skills)
    sector2_skills = np.random.normal(1.1, 0.35, n_workers_s2)
    sector2_prod = 1.0
    
    # Compute sector mismatch
    print("\n2.1 Sector comparison:")
    sector_mismatch = analyzer.compute_sector_mismatch(
        sector1_skills, sector2_skills, sector1_prod, sector2_prod
    )
    for key, value in sector_mismatch.items():
        print(f"   {key}: {value:.4f}")
    
    # Compare distributions
    print("\n2.2 Distribution comparison:")
    mismatch1 = sector1_skills - sector1_prod
    mismatch2 = sector2_skills - sector2_prod
    
    dist_comparison = analyzer.compare_sector_mismatch_distributions(mismatch1, mismatch2)
    print(f"   Sector 1 mean mismatch: {dist_comparison['sector1_mean']:.4f}")
    print(f"   Sector 2 mean mismatch: {dist_comparison['sector2_mean']:.4f}")
    print(f"   Mean difference: {dist_comparison['mean_difference']:.4f}")
    print(f"   Distributions differ significantly: {dist_comparison['distributions_differ']}")
    
    return analyzer, sector1_skills, sector2_skills


def example_temporal_dynamics():
    """
    Example 3: Temporal Dynamics of Skill Mismatch
    示例3：技能失配的时间动态
    """
    print("\n" + "="*70)
    print("Example 3: Temporal Dynamics of Skill Mismatch")
    print("示例3：技能失配的时间动态")
    print("="*70)
    
    analyzer = SkillMismatchAnalyzer()
    
    # Simulate time series (500 periods)
    np.random.seed(42)
    T = 500
    
    # Skill evolution: increasing trend with noise
    time_series_skills = 1.0 + 0.002 * np.arange(T) + 0.05 * np.random.randn(T)
    
    # Productivity evolution: slower increase with technological shocks
    time_series_prod = 1.0 + 0.0015 * np.arange(T) + 0.03 * np.random.randn(T)
    
    # Add policy shock at t=200
    time_series_prod[200:] += 0.1  # Productivity jump
    
    # Analyze dynamics
    print("\n3.1 Mismatch dynamics analysis:")
    dynamics = analyzer.analyze_mismatch_dynamics(time_series_skills, time_series_prod)
    print(f"   Average mismatch: {dynamics['mismatch'].mean():.4f}")
    print(f"   Mismatch trend: {dynamics['mismatch'].iloc[-1] - dynamics['mismatch'].iloc[0]:.4f}")
    print(f"   Average skill growth: {dynamics['skill_growth'].mean():.4f}")
    print(f"   Average productivity growth: {dynamics['prod_growth'].mean():.4f}")
    
    # Detect cycles
    print("\n3.2 Cyclical patterns:")
    mismatch_series = (time_series_skills - time_series_prod)
    cycles = analyzer.detect_mismatch_cycles(mismatch_series, window=20)
    print(f"   Number of cycles detected: {cycles['n_cycles']}")
    print(f"   Average cycle length: {cycles['avg_cycle_length']:.2f} periods")
    print(f"   Average amplitude: {cycles['avg_amplitude']:.4f}")
    
    # Analyze shock impact
    print("\n3.3 Policy shock impact (t=200):")
    shock_impact = analyzer.analyze_shock_impact(mismatch_series, shock_time=200,
                                                 window_before=50, window_after=50)
    print(f"   Pre-shock mismatch: {shock_impact['pre_mean']:.4f}")
    print(f"   Post-shock mismatch: {shock_impact['post_mean']:.4f}")
    print(f"   Change: {shock_impact['change']:.4f} ({shock_impact['pct_change']:.2f}%)")
    print(f"   Statistically significant: {shock_impact['significant']}")
    
    return analyzer, time_series_skills, time_series_prod, mismatch_series


def example_distribution_analysis():
    """
    Example 4: Distribution Analysis
    示例4：分布特征分析
    """
    print("\n" + "="*70)
    print("Example 4: Distribution Analysis")
    print("示例4：分布特征分析")
    print("="*70)
    
    analyzer = SkillMismatchAnalyzer()
    
    # Simulate mismatch distribution
    np.random.seed(42)
    n = 1000
    
    # Mixed distribution: some over-skilled, some under-skilled
    mismatch_values = np.concatenate([
        np.random.normal(0.3, 0.15, int(n*0.4)),   # Over-skilled
        np.random.normal(-0.1, 0.1, int(n*0.3)),   # Under-skilled
        np.random.normal(0.0, 0.05, int(n*0.3))    # Well-matched
    ])
    
    # Analyze distribution
    print("\n4.1 Distribution characteristics:")
    dist_stats = analyzer.analyze_mismatch_distribution(mismatch_values)
    print(f"   Mean: {dist_stats['mean']:.4f}")
    print(f"   Median: {dist_stats['median']:.4f}")
    print(f"   Std dev: {dist_stats['std']:.4f}")
    print(f"   Skewness: {dist_stats['skewness']:.4f}")
    print(f"   Kurtosis: {dist_stats['kurtosis']:.4f}")
    print(f"   Best fit distribution: {dist_stats['best_fit']}")
    
    # Inequality analysis
    print("\n4.2 Mismatch inequality:")
    abs_mismatch_values = np.abs(mismatch_values)
    inequality = analyzer.compute_mismatch_inequality(abs_mismatch_values)
    print(f"   Gini coefficient: {inequality['gini']:.4f}")
    print(f"   Theil index: {inequality['theil']:.4f}")
    print(f"   CV: {inequality['cv']:.4f}")
    print(f"   P90/P10 ratio: {inequality['p90_p10_ratio']:.4f}")
    print(f"   Top 10% share: {inequality['top10_share']:.4f}")
    
    return analyzer, mismatch_values


def example_macro_relationships():
    """
    Example 5: Relationships with Macro Variables
    示例5：与宏观变量的关系
    """
    print("\n" + "="*70)
    print("Example 5: Relationships with Macro Variables")
    print("示例5：与宏观变量的关系")
    print("="*70)
    
    analyzer = SkillMismatchAnalyzer()
    
    # Simulate time series
    np.random.seed(42)
    T = 300
    
    # Mismatch series with trend
    mismatch_series = 0.2 + 0.001 * np.arange(T) + 0.05 * np.random.randn(T)
    
    # Unemployment: positively correlated with mismatch
    unemployment_series = 0.05 + 0.3 * mismatch_series + 0.02 * np.random.randn(T)
    unemployment_series = np.clip(unemployment_series, 0.01, 0.20)
    
    # Productivity: negatively correlated with mismatch
    productivity_series = 1.5 - 0.5 * mismatch_series + 0.1 * np.random.randn(T)
    productivity_series = np.clip(productivity_series, 1.0, 2.0)
    
    # Wages: slightly negative correlation
    wage_series = 1.0 - 0.2 * mismatch_series + 0.05 * np.random.randn(T)
    wage_series = np.clip(wage_series, 0.8, 1.5)
    
    # GDP growth
    gdp_growth_series = 0.03 - 0.1 * mismatch_series + 0.02 * np.random.randn(T)
    
    # Analyze relationships
    print("\n5.1 Mismatch and Unemployment:")
    unemp_rel = analyzer.analyze_mismatch_unemployment_relationship(
        mismatch_series, unemployment_series
    )
    print(f"   Correlation: {unemp_rel['correlation']:.4f} (p={unemp_rel['p_correlation']:.4f})")
    print(f"   Regression slope: {unemp_rel['regression_slope']:.4f}")
    print(f"   R²: {unemp_rel['r_squared']:.4f}")
    print(f"   Optimal lag: {unemp_rel['optimal_lag']} periods")
    
    print("\n5.2 Mismatch and Productivity:")
    prod_rel = analyzer.analyze_mismatch_productivity_relationship(
        mismatch_series, productivity_series
    )
    print(f"   Correlation: {prod_rel['correlation']:.4f} (p={prod_rel['p_correlation']:.4f})")
    print(f"   Linear slope: {prod_rel['linear_slope']:.4f}")
    print(f"   R²: {prod_rel['r_squared']:.4f}")
    
    print("\n5.3 Mismatch and Wages:")
    wage_rel = analyzer.analyze_mismatch_wage_relationship(
        mismatch_series, wage_series
    )
    print(f"   Overall correlation: {wage_rel['correlation_all']:.4f}")
    print(f"   Regression slope: {wage_rel['regression_slope']:.4f}")
    
    print("\n5.4 Mismatch and Economic Growth:")
    growth_rel = analyzer.analyze_mismatch_growth_relationship(
        mismatch_series, gdp_growth_series
    )
    print(f"   Correlation: {growth_rel['correlation']:.4f}")
    print(f"   Regression slope: {growth_rel['regression_slope']:.4f}")
    print(f"   R²: {growth_rel['r_squared']:.4f}")
    
    return analyzer, mismatch_series, unemployment_series, productivity_series


def example_micro_mechanisms():
    """
    Example 6: Micro Mechanisms Analysis
    示例6：微观机制分析
    """
    print("\n" + "="*70)
    print("Example 6: Micro Mechanisms Analysis")
    print("示例6：微观机制分析")
    print("="*70)
    
    analyzer = SkillMismatchAnalyzer()
    
    # Simulate hiring process
    np.random.seed(42)
    n_applicants = 200
    n_hired = 50
    job_requirement = 1.2
    
    # Applicant skills
    applicant_skills = np.random.normal(1.1, 0.3, n_applicants)
    applicant_skills = np.clip(applicant_skills, 0.5, 2.0)
    
    # Hired workers (firms prefer higher skills)
    hired_indices = np.argsort(applicant_skills)[-n_hired:]
    hired_skills = applicant_skills[hired_indices]
    
    # Analyze hiring bias
    print("\n6.1 Hiring bias analysis:")
    hiring_bias = analyzer.analyze_hiring_bias(
        hired_skills, applicant_skills, job_requirement
    )
    print(f"   Mean hired skill: {hiring_bias['mean_hired_skill']:.4f}")
    print(f"   Mean applicant skill: {hiring_bias['mean_applicant_skill']:.4f}")
    print(f"   Selectivity: {hiring_bias['selectivity']:.4f}")
    print(f"   Over-qualification preference: {hiring_bias['over_qualification_preference']:.4f}")
    print(f"   Hiring rate: {hiring_bias['hiring_rate']:.2%}")
    
    # Skill evolution
    print("\n6.2 Skill evolution and mismatch:")
    initial_skills = np.random.normal(1.0, 0.2, 100)
    final_skills = initial_skills * 1.15 + np.random.normal(0, 0.05, 100)
    productivity_growth = 0.10
    
    skill_evol = analyzer.analyze_skill_evolution_mismatch(
        initial_skills, final_skills, productivity_growth
    )
    print(f"   Skill growth rate: {skill_evol['skill_growth_rate']:.4f}")
    print(f"   Productivity growth rate: {skill_evol['productivity_growth_rate']:.4f}")
    print(f"   Growth rate gap: {skill_evol['growth_rate_gap']:.4f}")
    print(f"   Dispersion change: {skill_evol['dispersion_change']:.4f}")
    
    # Labor mobility
    print("\n6.3 Labor mobility effects:")
    n_movers = 50
    pre_move_mismatch = np.random.normal(0.3, 0.15, n_movers)
    # After mobility, some improve, some worsen
    improvement = np.random.choice([-1, 1], size=n_movers, p=[0.3, 0.7])
    post_move_mismatch = pre_move_mismatch + improvement * np.random.uniform(0, 0.2, n_movers)
    
    mobility_effect = analyzer.analyze_mobility_mismatch_reduction(
        pre_move_mismatch, post_move_mismatch
    )
    print(f"   % Improved: {mobility_effect['pct_improved']:.2f}%")
    print(f"   % Worsened: {mobility_effect['pct_worsened']:.2f}%")
    print(f"   Net improvement: {mobility_effect['net_improvement']:.2f}%")
    print(f"   Abs. mismatch change: {mobility_effect['abs_mismatch_change']:.4f}")
    
    return analyzer


def example_visualizations():
    """
    Example 7: Visualization Tools
    示例7：可视化工具
    """
    print("\n" + "="*70)
    print("Example 7: Visualization Tools")
    print("示例7：可视化工具")
    print("="*70)
    
    analyzer = SkillMismatchAnalyzer()
    
    # Generate data for visualizations
    np.random.seed(42)
    T = 300
    
    # Temporal dynamics data
    print("\n7.1 Plotting mismatch dynamics...")
    time_points = np.arange(T)
    mismatch_series = 0.2 + 0.001 * time_points + 0.05 * np.random.randn(T)
    
    # Add cyclical component
    cyclical = 0.05 * np.sin(2 * np.pi * time_points / 50)
    mismatch_series += cyclical
    
    # Components
    components = {
        'Structural': 0.2 + 0.001 * time_points,
        'Cyclical': cyclical,
        'Stochastic': 0.05 * np.random.randn(T)
    }
    
    analyzer.plot_mismatch_dynamics(
        time_points, mismatch_series, components,
        shock_time=200,
        title="Skill Mismatch Temporal Dynamics",
        save_path="/tmp/mismatch_dynamics.png"
    )
    print("   Saved: /tmp/mismatch_dynamics.png")
    
    # Distribution comparison
    print("\n7.2 Plotting distribution comparison...")
    mismatch_dict = {
        'Fordist': np.random.normal(0.15, 0.08, 500),
        'Competitive': np.random.normal(0.25, 0.12, 500),
        'Baseline': np.random.normal(0.20, 0.10, 500)
    }
    
    analyzer.plot_mismatch_distribution_comparison(
        mismatch_dict,
        title="Skill Mismatch Distribution Comparison Across Regimes",
        save_path="/tmp/mismatch_distribution_comparison.png"
    )
    print("   Saved: /tmp/mismatch_distribution_comparison.png")
    
    # Heatmap
    print("\n7.3 Plotting mismatch heatmap...")
    n_points = 200
    skill_levels = np.random.uniform(0.8, 1.8, n_points)
    requirement_levels = np.random.uniform(0.8, 1.6, n_points)
    
    # Value represents frequency or density
    values = np.exp(-((skill_levels - requirement_levels)**2) / 0.2)
    
    analyzer.plot_mismatch_heatmap(
        skill_levels, requirement_levels, values,
        title="Skill-Requirement Match Density",
        save_path="/tmp/mismatch_heatmap.png"
    )
    print("   Saved: /tmp/mismatch_heatmap.png")
    
    print("\n7.4 All visualizations created successfully!")
    return analyzer


def run_comprehensive_example():
    """
    Run all examples in sequence
    运行所有示例
    """
    print("\n" + "="*70)
    print("K+S Model - Comprehensive Skill Mismatch Analysis Examples")
    print("K+S模型 - 全面技能失配分析示例")
    print("="*70)
    print("\nThis script demonstrates six categories of skill mismatch analysis:")
    print("本脚本演示六类技能失配分析：")
    print("1. Basic mismatch indicators (基本失配指标)")
    print("2. Sector comparison (部门比较)")
    print("3. Temporal dynamics (时间动态)")
    print("4. Distribution analysis (分布分析)")
    print("5. Macro relationships (宏观关系)")
    print("6. Micro mechanisms (微观机制)")
    print("7. Visualizations (可视化)")
    
    # Run all examples
    example_basic_mismatch_indicators()
    example_sector_comparison()
    example_temporal_dynamics()
    example_distribution_analysis()
    example_macro_relationships()
    example_micro_mechanisms()
    example_visualizations()
    
    print("\n" + "="*70)
    print("All examples completed successfully!")
    print("所有示例运行成功!")
    print("="*70)
    print("\nVisualization files saved to /tmp/:")
    print("  - mismatch_dynamics.png")
    print("  - mismatch_distribution_comparison.png")
    print("  - mismatch_heatmap.png")
    print("\nFor actual simulation data analysis, load your K+S simulation results")
    print("and use the SkillMismatchAnalyzer with appropriate data.")
    print("\n要分析实际仿真数据，请加载K+S仿真结果")
    print("并使用SkillMismatchAnalyzer处理相应数据。")


if __name__ == "__main__":
    run_comprehensive_example()
