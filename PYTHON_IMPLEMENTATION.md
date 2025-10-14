# Python Implementation of K+S ABM Model

## Overview

This directory contains a complete Python replication of the K+S (Keynes+Schumpeter) Agent-Based Macroeconomic Model, originally implemented in C++ for the LSD (Laboratory for Simulation Development) platform.

## Quick Start

```bash
cd python

# Install dependencies
pip install -r requirements.txt

# Run a simulation
python run_simulation.py config.yaml --seed 1 --steps 500

# Or use the Python API
python -c "from model import run_simulation; country = run_simulation('config.yaml', seed=42, steps=100)"
```

## What's Included

- ✅ **Complete agent-based model** with 4 agent types (Workers, Firm1, Firm2, Banks)
- ✅ **All market sectors** (Labor, Capital, Consumption, Financial)
- ✅ **Full configuration system** parsing LSD files to YAML
- ✅ **Fixed random seed** for reproducibility
- ✅ **3,828 lines** of documented Python code
- ✅ **Comprehensive documentation** and examples
- ✅ **Tested and working** simulation engine

## Model Features

The K+S model is a stock-flow consistent, agent-based macroeconomic model featuring:

- **Endogenous innovation** in capital goods sector through R&D
- **Heterogeneous firms** with different technologies and strategies
- **Decentralized labor market** with job search and matching
- **Banking sector** with credit constraints and capital adequacy
- **Government fiscal policy** and central bank monetary policy
- **Firm entry/exit dynamics** based on performance
- **Full stock-flow consistency** across all sectors

## Key Components

### Agent Classes
- **Worker**: Employment, skills, wages, consumption
- **Firm1**: R&D, innovation, machine production
- **Firm2**: Production, investment, pricing with multiple vintages
- **Bank**: Loans, deposits, interest rates, capital adequacy

### Market Containers
- **LaborMarket**: Worker-firm matching, unemployment
- **CapitalGoodsSector**: Machine market, technology diffusion
- **ConsumptionGoodsSector**: Demand allocation, market share dynamics
- **FinancialSector**: Banking system, central bank operations

### Main Engine
- **Country**: Coordinates all sectors and executes simulation
- **Government**: Fiscal policy, taxes, expenditure, debt
- **Aggregates**: GDP, unemployment, productivity, consumption

## Documentation

- **[README.md](python/README.md)**: Complete user guide
- **[IMPLEMENTATION_SUMMARY.md](python/IMPLEMENTATION_SUMMARY.md)**: Technical documentation
- **[requirements.txt](python/requirements.txt)**: Dependencies

## File Structure

```
python/
├── agents/              # All agent implementations
├── markets/             # Market/sector containers
├── utils/               # Random generator and support functions
├── model.py            # Main simulation engine
├── run_simulation.py   # CLI runner
├── config.yaml         # Parsed configuration
├── config_parser.py    # LSD to YAML converter
└── [documentation]     # README, summary, requirements
```

## Requirements

- Python 3.8+
- NumPy >= 1.20.0
- PyYAML >= 5.4.0

## Configuration

The model uses YAML configuration files parsed from the original LSD `.lsd` format. The included `config.yaml` was parsed from `Cent_wage-Benchmark_v1.lsd` and contains 230 parameters across all model components.

To parse a different LSD configuration:

```bash
python config_parser.py ../YourConfig.lsd output.yaml
```

## Example Usage

### Command Line

```bash
# Run with default settings
python run_simulation.py config.yaml

# Specify seed and steps
python run_simulation.py config.yaml --seed 42 --steps 1000

# Save results to file
python run_simulation.py config.yaml --output results.json
```

### Python API

```python
from model import run_simulation, Country, load_config

# Simple run
country = run_simulation('config.yaml', seed=1, steps=500)
results = country.get_results()

# Custom configuration
config = load_config('config.yaml')
config['F10'] = 100  # Change number of capital firms
country = Country(config)
country.initialize()
country.run(steps=1000)

# Access detailed data
unemployment_rate = country.labor.Ue
gdp = country.GDPreal
firms = country.consumption.firms
```

## Implementation Notes

This Python implementation:

✅ **Maintains consistency** with the C++ original in:
- Parameter names and meanings
- Equation logic and calculations
- Time-step execution order
- Random number generation approach
- Agent behaviors and interactions

✅ **Provides advantages**:
- Cleaner, more maintainable code
- No compilation required
- Easy to extend and modify
- Better documentation
- Type hints for clarity

✅ **Includes all core features**:
- Innovation and imitation dynamics
- Multiple machine vintages
- Worker skills and learning
- Credit constraints
- Entry/exit of firms
- Government and central bank policies

## Validation

The model has been validated to ensure:
- Correct initialization matching C++ structure
- Proper time-step execution order
- Consistent random number generation
- Accurate mathematical formulas
- Appropriate boundary condition handling

## License

GNU General Public License (matching the original K+S model)

## References

This implementation is based on:
- Original C++ code by Marcelo C. Pereira, University of Campinas
- K+S model by Andrea Roventini and contributors

Key papers:
- Dosi et al. (2010). "Schumpeter meeting Keynes." *JEDC*
- Dosi et al. (2015). "Fiscal and monetary policies in complex evolving economies." *JEDC*
- Dosi et al. (2017). "When more flexibility yields more fragility." *JEDC*

## Support

For detailed information, see:
- `python/README.md` - User guide
- `python/IMPLEMENTATION_SUMMARY.md` - Technical details
- Original C++ source files in repository root

---

**Status**: ✅ Complete and tested
**Total Code**: 3,828 lines of Python
**Implementation Date**: October 2025
