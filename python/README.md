# K+S Model Python Implementation

## Overview

This is a complete Python replication of the Labor- and Finance-Augmented K+S (Keynes+Schumpeter) Agent-Based Model originally implemented in C++/LSD.

The K+S model is a general disequilibrium, stock-and-flow consistent, agent-based macroeconomic model featuring heterogeneous agents (workers, firms, banks) with bounded rationality.

## Model Version

Python implementation of K+S Model version 5.1.3

Original C++ version by Marcelo C. Pereira, University of Campinas

## Architecture

The model uses **pure Python** (not Mesa) for maximum control over:
- Precise computational ordering (critical for stock-flow consistency)
- Complex agent dependencies and interactions
- Custom scheduling and time-stepping logic

### Directory Structure

```
python/
├── ks_model/           # Core model implementation
│   ├── agents/         # Agent classes (Firm1, Firm2, Bank, Worker)
│   ├── sectors/        # Sector containers (Capital, Consumption, Financial, Labor)
│   ├── country.py      # Country-level coordination
│   ├── government.py   # Government and fiscal policy
│   ├── scheduler.py    # Time-stepping and equation ordering
│   └── model.py        # Main model class
├── config/             # Configuration loading and parameters
│   ├── loader.py       # .lsd file parser
│   └── scenarios/      # Pre-configured scenarios
├── analysis/           # Data analysis (Python equivalent of R scripts)
│   ├── aggregates.py   # Macro-level analysis
│   ├── sectors.py      # Firm-level analysis
│   └── workers.py      # Worker-level analysis
├── utils/              # Support utilities
│   ├── random.py       # Random number generation
│   ├── statistics.py   # Statistical functions
│   └── helpers.py      # General utilities
├── tests/              # Unit and integration tests
└── examples/           # Example usage scripts

```

## Key Features

- **Stock-Flow Consistency**: All financial flows properly tracked
- **Heterogeneous Agents**: Different behaviors and characteristics
- **Bounded Rationality**: Agents use adaptive, rule-based decisions
- **Endogenous Innovation**: R&D-driven technological progress
- **Credit Market**: Bank lending with Basel-like regulations
- **Labor Market**: Search-and-match with skill dynamics
- **Multiple Regimes**: Support for institutional shocks

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```python
from ks_model import KSModel

# Load configuration
model = KSModel("config/scenarios/No_skills-Fix_entry-No_fin.lsd")

# Run simulation
model.run(periods=500)

# Export results
model.export_results("output/simulation_results.csv")

# Analyze
from analysis import MacroAnalysis
analysis = MacroAnalysis(model.data)
analysis.plot_time_series()
```

## Configuration Files

The following scenarios are supported (matching original LSD configurations):

1. **Cent_wage-Benchmark_v1.lsd**: Centralized wage, minimal financial market
2. **Cent_wage-Baseline_v2.lsd**: Centralized wage, full financial market
3. **No_skills-Fix_entry-No_fin.lsd**: No skills, fixed entry (Fordist regime)
4. **Ten_skills-Free_entry-No_fin.lsd**: Tenure skills, free entry with shock
5. **Ten_skills-Free_entry-Full_fin.lsd**: Full model with all features
6. **Ten_skills-Free_entry-Bas_fin.lsd**: Basic financial market with shock

## Code Quality Standards

All code follows:
- **PEP 8** style guide
- **Type hints** throughout
- **Google-style docstrings**
- **NumPy** vectorization where possible
- **Comprehensive testing**

## References

- Dosi et al. (2010). Schumpeter meeting Keynes. JEDC 34:1748-1767
- Dosi et al. (2015). Fiscal and monetary policies. JEDC 52:166-189
- Dosi et al. (2017). When more flexibility yields more fragility. JEDC 81:162-186
- Dosi et al. (2018). Causes and consequences of hysteresis. ICC 27:1015-1044
- Dosi et al. (2019). Supply-side policies interaction. JEBO 162:360-388
- Dosi et al. (2020). Impact of deunionization. ICC dtaa025

## License

GNU General Public License v3.0

## Authors

Python implementation: [Implementation Team]
Original model: Marcelo C. Pereira, Andrea Roventini, and contributors
