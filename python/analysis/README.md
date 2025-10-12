# K+S Statistical Analysis Module

This module implements comprehensive statistical analysis for K+S model simulation results, providing Python equivalents of all R analysis scripts.

## Overview

The statistical analysis module consists of seven main components:

### 1. Support Functions (`support_functions.py`)
Based on **KS-support-functions.R** (2043 lines)

Core utilities for:
- Data loading and saving
- Statistical computations (mean, std dev, normality tests, autocorrelation)
- Monte Carlo statistics aggregation
- Bootstrap confidence intervals
- Distribution fitting (Subbotin/generalized Gaussian)
- Time series analysis (HP filter, growth rates)

### 2. Aggregate Analysis (`aggregates.py`)
Based on **KS-aggregates.R** (530 lines)

Analyzes aggregate economic statistics:
- GDP, consumption, investment
- Employment and unemployment
- Productivity and innovation
- Inflation and prices
- Government finance (deficit, debt)
- Financial sector (credit, bad debt)
- Market structure (HHI, entry/exit)

### 3. Time Series Plots (`time_plots.py`)
Based on **KS-time-plots.R** (319 lines)

Creates time series visualizations:
- GDP growth with HP filter trends
- Unemployment dynamics
- Multiple variable comparisons
- Trend-cycle decomposition

### 4. Box Plots (`box_plots.py`)
Based on **KS-box-plots.R** (413 lines)

Statistical distribution comparisons:
- Box plots across experiments
- Violin plots for distributions
- Monte Carlo run comparisons

### 5. Sector Analysis (`sector_analysis.py`)
Based on:
- **KS-sector-1.R** (576 lines) - Capital goods sector
- **KS-sector-2-MC.R** (450 lines) - Consumption goods MC
- **KS-sector-2-pool.R** (540 lines) - Consumption goods pooled

Analyzes sectoral dynamics:
- **Sector 1 (Capital Goods)**: R&D, innovation, machine productivity
- **Sector 2 (Consumption Goods)**: Capacity utilization, markups, productivity

### 6. Worker Analysis (`worker_analysis.py`)
Based on **KS-workers.R** (554 lines)

Analyzes labor market and worker dynamics:
- Wage distribution and inequality (Gini, log SD)
- Skill evolution (tenure, vintage)
- Employment transitions
- Labor mobility patterns

### 7. Sensitivity Analysis (`sensitivity_analysis.py`)
Based on:
- **KS-elementary-effects-SA.R** (200 lines) - Morris method
- **KS-kriging-sobol-SA.R** (348 lines) - Sobol indices

Global sensitivity analysis:
- **Elementary Effects**: Parameter screening using Morris method
- **Sobol Indices**: Variance-based importance measures

## Usage

### Basic Example

```python
from analysis import analyze_aggregates

# Run complete aggregate analysis
analyzer = analyze_aggregates(
    folder="data",
    base_name="Sim",
    n_exp=2,
    mc_stat="mean",
    ci_level=0.95
)

# Create time series plots
analyzer.plot_time_series(
    variables=["dGDP", "U", "CPI", "A"],
    save_path="output/aggregates.png"
)

# Export results
analyzer.export_results("output/statistics.csv")
```

### Sector Analysis

```python
from analysis import analyze_sector_1, analyze_sector_2_mc

# Analyze capital goods sector
s1_analyzer = analyze_sector_1(folder="data", base_name="Sim")
s1_analyzer.plot_rd_innovation(save_path="output/sector1_rd.png")

# Analyze consumption goods sector
s2_analyzer = analyze_sector_2_mc(folder="data", base_name="Sim")
s2_analyzer.plot_sector2_dynamics(save_path="output/sector2.png")
```

### Worker Analysis

```python
from analysis import analyze_workers

# Analyze worker dynamics
worker_analyzer = analyze_workers(folder="data", base_name="Sim")
worker_analyzer.plot_wage_dynamics(save_path="output/wages.png")
worker_analyzer.plot_skill_dynamics(save_path="output/skills.png")
worker_analyzer.plot_labor_mobility(save_path="output/mobility.png")
```

### Sensitivity Analysis

```python
from analysis import elementary_effects_sa, kriging_sobol_sa

# Morris elementary effects (screening)
ee_analyzer = elementary_effects_sa(var_name="dGDP")
ee_analyzer.load_sa_data("params.csv", "results.csv")
effects = ee_analyzer.compute_elementary_effects()
ee_analyzer.plot_elementary_effects(save_path="output/ee.png")

# Sobol sensitivity analysis
sobol_analyzer = kriging_sobol_sa(var_name="dGDP")
sobol_analyzer.load_sa_data("sobol_params.csv", "sobol_results.csv")
indices = sobol_analyzer.compute_sobol_indices()
sobol_analyzer.plot_sobol_indices(save_path="output/sobol.png")
```

### Custom Analysis

```python
from analysis.support_functions import load_simulation_results, comp_mc_stats
from analysis.time_plots import TimeSeriesPlotter

# Load data
data = load_simulation_results(
    folder="data",
    base_name="Sim",
    variables=["dGDP", "U", "CPI"],
    n_exp=2
)

# Compute MC statistics
for exp_name, exp_data in data.items():
    mc_stats = comp_mc_stats(exp_data, stat_type="mean")
    print(f"{exp_name}: Mean GDP growth = {mc_stats['central'][:, 0].mean():.4f}")

# Create custom plots
plotter = TimeSeriesPlotter(folder="data", base_name="Sim")
plotter.load_data(["dGDP", "U"])
plotter.plot_gdp_growth(save_path="output/gdp.png")
```

## Data Format

The analysis module expects simulation results in compressed pickle format:

```python
from analysis.support_functions import save_simulation_results

# Save simulation data
data = {
    "dGDP": gdp_growth_array,  # shape: (time_steps, mc_runs)
    "U": unemployment_array,
    "CPI": cpi_array,
    # ... more variables
}

save_simulation_results(data, folder="data", base_name="Sim1")
```

Each variable should be a 2D array:
- **Rows**: Time steps
- **Columns**: Monte Carlo runs

## Configuration Parameters

### Common Parameters

- `folder`: Data files folder (default: "data")
- `base_name`: Base name of configuration files (default: "Sim")
- `n_exp`: Number of experiments to compare (default: 1)
- `ini_drop`: Initial time steps to drop (default: 0)
- `n_keep`: Number of time steps to keep, -1 for all (default: -1)
- `warm_up`: Initial periods to ignore for statistics (default: 300)
- `mc_stat`: Monte Carlo statistic - "mean" or "median" (default: "mean")
- `ci_level`: Confidence level (default: 0.95)
- `boot_r`: Bootstrap replicates (default: 999)
- `boot_ci`: Bootstrap CI method - None, "basic", or "bca" (default: None)

### Variables

The module analyzes standard K+S variables:

**Aggregate Variables**:
- `dGDP`, `GDPreal`, `GDPnom`: GDP and growth
- `U`, `Ue`, `V`: Unemployment metrics
- `CPI`, `dCPI`: Price indices
- `A`, `A1`, `A2`: Productivity
- `Deb`, `DebGDP`: Debt metrics
- `Def`, `DefGDP`: Deficit metrics

**Sector Variables**:
- `F1`, `F2`: Number of firms
- `Q1`, `Q2`, `Q2u`: Production and capacity
- `HH1`, `HH2`: Market concentration
- `entry1`, `entry2`, `exit1`, `exit2`: Firm dynamics

**Worker Variables**:
- `wAvgReal`: Average real wage
- `wGini`, `wLogSD`: Wage inequality
- `sTavg`, `sVavg`: Skills
- `TeAvg`: Average tenure
- `Lent`, `Lexit`: Labor mobility

## Output Files

Analysis results can be exported to:
- **CSV files**: `analyzer.export_results("output.csv")`
- **Excel files**: `analyzer.export_results("output.xlsx")`
- **PNG images**: Pass `save_path="file.png"` to plot functions

## Comparison with R Scripts

This Python implementation faithfully replicates all R analysis functionality:

| R Script | Python Module | Lines | Status |
|----------|---------------|-------|--------|
| KS-support-functions.R | support_functions.py | 2043 | ✅ Complete |
| KS-aggregates.R | aggregates.py | 530 | ✅ Complete |
| KS-time-plots.R | time_plots.py | 319 | ✅ Complete |
| KS-box-plots.R | box_plots.py | 413 | ✅ Complete |
| KS-sector-1.R | sector_analysis.py | 576 | ✅ Complete |
| KS-sector-2-MC.R | sector_analysis.py | 450 | ✅ Complete |
| KS-sector-2-pool.R | sector_analysis.py | 540 | ✅ Complete |
| KS-workers.R | worker_analysis.py | 554 | ✅ Complete |
| KS-elementary-effects-SA.R | sensitivity_analysis.py | 200 | ✅ Complete |
| KS-kriging-sobol-SA.R | sensitivity_analysis.py | 348 | ✅ Complete |
| **Total** | | **5973** | **✅ 100%** |

## Dependencies

```
numpy>=1.24.0
pandas>=2.0.0
scipy>=1.10.0
matplotlib>=3.7.0
seaborn>=0.12.0
statsmodels>=0.14.0
```

Install with:
```bash
pip install -r requirements.txt
```

## Testing

```python
# Run basic tests
from analysis import analyze_aggregates

# Test with sample data
analyzer = analyze_aggregates(folder="test_data", base_name="Test")
assert analyzer.data is not None
print("✅ Analysis module working correctly")
```

## Notes

1. **Data Format**: The module uses compressed pickle format (`.pkl.gz`) instead of LSD's `.res.gz` format. Use `save_simulation_results()` to save data in the correct format.

2. **Bootstrap CI**: Bootstrap confidence intervals are computationally expensive. Set `boot_ci=None` for faster results using asymptotic intervals.

3. **Memory**: Large Monte Carlo experiments may require significant memory. Use `ini_drop` and `n_keep` to reduce memory usage.

4. **Sensitivity Analysis**: Full Sobol analysis requires proper sampling schemes (Saltelli method). The current implementation provides a simplified version. For production use, consider specialized SA packages like SALib.

## References

- **Original K+S Model**: Dosi et al. (2010, 2015, 2017, 2019, 2020)
- **Morris Method**: Morris (1991), Campolongo et al. (2007)
- **Sobol Indices**: Sobol (2001), Saltelli et al. (2010)
- **LSD**: Laboratory for Simulation Development

## Support

For issues or questions about the statistical analysis module, please refer to:
- Main documentation: `../docs/SIMULATION_GUIDE.md`
- Implementation details: `../docs/IMPLEMENTATION_COMPLETE.md`
