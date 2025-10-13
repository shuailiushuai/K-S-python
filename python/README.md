# K+S ABM Model - Python Implementation

## Overview

This is a Python reimplementation of the Labor- and finance-augmented K+S (Schumpeter meeting Keynes) Agent-Based Model originally developed in C++ using the LSD framework.

The K+S model is a general disequilibrium, stock-and-flow consistent, agent-based model with heterogeneous workers, firms, and banks. It analyzes macro- and microeconomic dynamics including productivity growth, GDP evolution, and the coupled operation of labor and financial markets.

## Model Description

### Agent Types

1. **Workers/Consumers** (`agents/worker.py`)
   - Search for jobs in labor market
   - Learn skills through tenure (learning-by-doing) and vintage (learning-by-using)
   - Consume goods with their income
   - May receive unemployment benefits

2. **Capital-Good Firms (Firm1)** (`agents/firm1.py`)
   - Invest in R&D for innovation and imitation
   - Produce heterogeneous machines with evolving productivity
   - Compete through technological advancement
   - Supply machines to consumption-good firms

3. **Consumption-Good Firms (Firm2)** (`agents/firm2.py`)
   - Combine machines and labor to produce consumption goods
   - Form adaptive demand expectations
   - Manage capital stock with vintages
   - Compete on price, quality, and delivery

4. **Banks** (`agents/bank.py`)
   - Collect deposits from firms and workers
   - Provide loans to firms with credit limits
   - Follow Basel-like capital adequacy rules
   - May receive central bank bailouts

5. **Central Bank and Government** (aggregated in model)
   - Central bank sets prime interest rate (Taylor rule)
   - Government levies taxes, pays unemployment benefits
   - Provides worker training
   - Manages public debt

## Project Structure

```
python/
├── agents/                   # Agent classes
│   ├── worker.py            # Worker agent
│   ├── bank.py              # Bank agent
│   ├── firm1.py             # Capital-good firm agent
│   └── firm2.py             # Consumption-good firm agent
├── markets/                  # Market mechanisms (to be implemented)
│   ├── labor_market.py      # Job search and matching
│   ├── goods_market.py      # Consumption goods market
│   ├── capital_market.py    # Machine orders and supply
│   └── financial_market.py  # Credit allocation
├── utils/                    # Utility functions
│   ├── core_utils.py        # Random engine, moving averages
│   └── data_structures.py   # Data structures (Vintage, FirmRank, etc.)
├── config/                   # Configuration
│   ├── lsd_parser.py        # LSD file parser
│   └── model_config.yaml    # Parsed parameters (229 parameters)
├── model.py                 # Main model orchestration (to be completed)
├── requirements.txt         # Dependencies
└── README.md               # This file
```

## Configuration

The model is configured using parameters extracted from the original `Cent_wage-Benchmark_v1.lsd` file. The configuration includes:

- **Financial Parameters**: Banking sector, credit rules, interest rates
- **Capital Market Parameters**: R&D, innovation, machine productivity
- **Consumer Market Parameters**: Demand expectations, pricing, investment
- **Labor Parameters**: Skills, wages, job search, unemployment

See `config/model_config.yaml` for all 229 parameters.

## Key Features Implemented

### Random Number Generation
- Fixed seed mechanism using MT19937_64 (Mersenne Twister)
- Ensures reproducibility across runs
- Compatible with original C++ implementation

### Agent Attributes
- Complete attribute mapping from C++ code
- Time series tracking for historical values
- Lazy evaluation for computed variables

### Core Algorithms
- **Innovation and Imitation**: Beta-distributed R&D outcomes
- **Credit Allocation**: Pecking order based on net-wealth-to-sales ratio
- **Labor Market**: Decentralized search-and-match with reservation wages
- **Market Share Dynamics**: Replicator dynamics for firm competition

### Stock-Flow Consistency
- Proper tracking of financial flows
- Balance sheet accounting for all agents
- Government budget constraint enforcement

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Parse configuration (already done)
cd config
python lsd_parser.py ../../Cent_wage-Benchmark_v1.lsd
```

## Usage (After Full Implementation)

```python
from model import KSModel

# Initialize model with configuration
model = KSModel('config/model_config.yaml', seed=1)

# Run simulation
results = model.run(periods=1000)

# Analyze results
model.plot_time_series(['GDP', 'unemployment', 'inflation'])
model.export_results('results.csv')
```

## Implementation Status

### Completed
- ✅ Project structure
- ✅ Configuration parser (229 parameters extracted)
- ✅ Random number generator with fixed seed
- ✅ Core utility functions
- ✅ Data structures (Vintage, FirmRank, WageOffer, Application)
- ✅ Worker agent (complete)
- ✅ Bank agent (complete)
- ✅ Firm1 agent (capital-good, complete)
- ✅ Firm2 agent (consumption-good, complete)

### To Be Completed
- ⬜ Market mechanisms (labor, goods, capital, financial)
- ⬜ Government and Central Bank logic
- ⬜ Entry/exit processes
- ⬜ Model orchestration and time-stepping
- ⬜ Statistics aggregation
- ⬜ Validation tests
- ⬜ Full documentation

## Technical Notes

### Design Principles

1. **Minimal Changes**: The implementation follows the C++ code structure as closely as possible
2. **Modularity**: Agents, markets, and utilities are separated
3. **Extensibility**: Easy to add new agent types or market mechanisms
4. **Reproducibility**: Fixed random seed ensures identical results

### Key Differences from C++

- Python uses classes instead of LSD objects
- Time series stored as lists instead of LSD lagged values
- Markets implemented as separate modules instead of embedded equations
- Configuration loaded from YAML instead of .lsd file structure

### Mathematical Fidelity

All mathematical formulas from the original C++ implementation are preserved:
- Innovation/imitation using Beta distributions
- Replicator dynamics for market shares
- Markup pricing rules
- Credit allocation algorithms
- Skill learning curves

## References

### Original Papers
- Dosi et al. (2010). Schumpeter meeting Keynes. Journal of Economic Dynamics and Control 34:1748-1767
- Dosi et al. (2015). Fiscal and monetary policies in complex evolving economies. Journal of Economic Dynamics and Control 52:166-189
- Dosi et al. (2017). When more flexibility yields more fragility. Journal of Economic Dynamics and Control 81:162-186
- Dosi et al. (2018). Causes and consequences of hysteresis. Industrial and Corporate Change 27:1015-1044

### Original Implementation
- C++ version: LSD framework (https://github.com/SantAnnaKS/LSD)
- Version: 5.1.3 (Labor and finance extensions)
- Copyright: Marcelo C. Pereira, University of Campinas

## Contributing

This is a faithful reimplementation. Changes should maintain compatibility with the original C++ version's behavior and results.

## License

Distributed under the GNU General Public License (as per original code).

## Contact

For questions about the original model, refer to the papers above.
For questions about this Python implementation, see the repository issues.
