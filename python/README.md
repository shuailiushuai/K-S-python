# K+S ABM Model - Python Implementation

This directory contains a complete Python reproduction of the K+S (Keynes+Schumpeter) Agent-Based Model originally implemented in C++/LSD.

## Overview

The K+S model is a general disequilibrium, stock-and-flow consistent, agent-based macroeconomic model with:
- **Heterogeneous agents**: Workers, Capital-good firms (Firm1), Consumption-good firms (Firm2), and Banks
- **Bounded rationality**: Agents follow behavioral rules rather than optimization
- **Endogenous dynamics**: Innovation, entry/exit, labor market matching
- **Stock-flow consistency**: All financial flows are tracked and balanced

## Model Architecture

### Implementation Choice: Pure Python + NumPy

We chose **pure Python with NumPy** over Mesa 3.0 for the following reasons:

1. **Complex equation sequencing**: The model requires precise control over the order in which equations are evaluated within each time step (as defined in `timeStep` equation)
2. **Stock-flow consistency**: Requires careful tracking of all financial stocks and flows with exact ordering
3. **Performance**: NumPy arrays provide efficient computation for large numbers of agents
4. **Flexibility**: Direct control over simulation flow without framework constraints
5. **Dependencies**: The model has complex cross-agent dependencies that don't fit standard Mesa schedulers

### Model Structure

```
python/
├── README.md                 # This file
├── ks_model.py              # Main model class and orchestration
├── agents/
│   ├── __init__.py
│   ├── firm1.py            # Capital-good firms (innovation, R&D)
│   ├── firm2.py            # Consumption-good firms (production)
│   ├── worker.py           # Workers (job search, consumption)
│   ├── bank.py             # Banks (credit allocation)
│   ├── vintage.py          # Machine vintages
│   └── government.py       # Government and Central Bank
├── markets/
│   ├── __init__.py
│   ├── labor_market.py     # Job search and matching
│   ├── goods_market.py     # Consumption goods trading
│   ├── capital_market.py   # Machine tools trading
│   └── financial_market.py # Credit and banking
├── utils/
│   ├── __init__.py
│   ├── parameters.py       # Model parameters and configuration
│   ├── statistics.py       # Data collection and statistics
│   └── random_utils.py     # Random number generation utilities
├── visualization/
│   ├── __init__.py
│   └── plots.py            # Visualization functions
├── config/
│   ├── baseline.json       # Baseline configuration
│   └── parameters.json     # Default parameters
├── tests/
│   ├── __init__.py
│   └── test_model.py       # Unit tests
├── run_simulation.py       # Main simulation script
└── requirements.txt        # Python dependencies
```

## Key Components

### Agents

1. **Capital-Good Firms (Firm1)**: 
   - Perform R&D (innovation and imitation)
   - Produce heterogeneous machines with different productivities
   - Set prices using cost-plus markup
   - Compete via technology diffusion

2. **Consumption-Good Firms (Firm2)**:
   - Form adaptive demand expectations
   - Produce using machines and labor
   - Manage vintage capital stock
   - Set variable markups based on competitiveness
   - Entry/exit based on market share and net worth

3. **Workers**:
   - Search for jobs across firms
   - Accumulate skills (vintage and tenure)
   - Consume goods with their income
   - Can be unemployed and receive benefits

4. **Banks**:
   - Collect deposits
   - Provide loans to firms
   - Subject to capital adequacy constraints
   - Use pecking order for credit allocation

5. **Government & Central Bank**:
   - Set interest rates (Taylor rule)
   - Collect taxes and pay benefits
   - Manage public debt
   - Bail out failed banks

### Markets

1. **Labor Market**: Decentralized search-and-match with firm-specific job queues
2. **Goods Market**: Replicator dynamics with competitiveness-based market shares
3. **Capital Market**: Network-based trading with client relationships
4. **Financial Market**: Credit rationing based on firm financial health

## Usage

### Installation

```bash
cd python
pip install -r requirements.txt
```

### Running Simulations

```python
from ks_model import KSModel

# Create and run model with default parameters
model = KSModel()
model.run(time_steps=500)

# Access results
results = model.get_statistics()
model.plot_results()
```

### Configuration

Edit `config/parameters.json` to modify model parameters. Key parameters:

- `F10`, `F20`: Initial number of firms in each sector
- `Ls0`: Initial labor force size
- `B`: Number of banks
- `TregChg`: Time of regime change (0 = no change)
- See `description.txt` in root directory for full parameter list

## Validation

The model has been validated against the original C++ implementation:

- Stock-flow consistency checks pass
- Aggregate dynamics match qualitatively
- Microeconomic distributions are similar
- See `tests/` for validation tests

## References

- Dosi et al. (2010). Schumpeter meeting Keynes. Journal of Economic Dynamics and Control.
- Dosi et al. (2015). Fiscal and monetary policies in complex evolving economies. JEDC.
- Dosi et al. (2017). When more flexibility yields more fragility. JEDC.
- Dosi et al. (2018). Causes and consequences of hysteresis. Industrial and Corporate Change.

## License

Copyright Marcelo C. Pereira. Distributed under the GNU General Public License.
Python implementation by GitHub Copilot based on original C++ code.
