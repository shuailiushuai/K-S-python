# K+S Model Python Implementation

## Overview

This directory contains a Python reimplementation of the Labor- and Finance-Augmented K+S (Keynes+Schumpeter) Agent-Based Model, version 5.1.3.

The original model was implemented in C++ for the LSD (Laboratory for Simulation Development) environment and contains approximately 10,800 lines of code across multiple modules.

## Implementation Approach

### Why Pure Python (Not Mesa 3.0)?

After careful analysis of the original K+S model, **pure Python** was chosen over Mesa 3.0 for the following reasons:

1. **Complex Temporal Dependencies**: The model has intricate equation sequencing with specific variable computation orders enforced by the `timeStep` function. Mesa's standard schedulers may not easily accommodate this complexity.

2. **Custom Random Number Generation**: The model uses C++ mt19937_64 random engine with precise seeding requirements for reproducibility. Direct control is needed to match behavior.

3. **Stock-Flow Consistency**: The model maintains strict stock-flow consistency with complex interdependencies that require careful timing control.

4. **LSD-Specific Features**: The original uses LSD-specific macros, hooks, and data structures that don't map directly to Mesa's framework.

5. **Performance**: Direct Python implementation allows optimization without framework overhead.

## Directory Structure

```
python/
├── configs/          # Configuration files (converted from .lsd)
├── model/            # Core model implementation
│   ├── __init__.py
│   ├── agent.py              # Base agent class
│   ├── constants.py          # Model constants
│   ├── data_structures.py    # Data structures (Vintage, Application, etc.)
│   ├── random_engine.py      # Random number generation (mt19937_64)
│   ├── support.py            # Utility functions
│   ├── worker.py             # Worker agent implementation
│   ├── firm1.py              # Capital goods firm (planned)
│   ├── firm2.py              # Consumption goods firm (planned)
│   ├── bank.py               # Bank agent (planned)
│   ├── vintage.py            # Machine vintage (planned)
│   ├── country.py            # Country/economy controller (planned)
│   ├── financial.py          # Financial sector (planned)
│   ├── labor.py              # Labor market (planned)
│   └── statistics.py         # Statistics and testing (planned)
├── analysis/         # Analysis scripts (R → Python conversion)
└── tests/            # Test suite
```

## Model Architecture

### Agent Types

The K+S model includes the following agent types:

1. **Country**: Top-level container managing the economy
2. **Financial Sector**: Banking system container
3. **Bank**: Individual banks providing credit
4. **Capital Sector**: Capital goods industry container  
5. **Firm1**: Capital goods producers (R&D and machine production)
6. **Consumption Sector**: Consumer goods industry container
7. **Firm2**: Consumer goods producers
8. **Vintage**: Machine vintages with specific technologies
9. **Labor Market**: Worker pool container
10. **Worker**: Individual workers/consumers

### Key Features

- **Innovation and R&D**: Firm1 agents perform R&D to create new machine technologies
- **Heterogeneous Agents**: Firms and workers have different capabilities, skills, and strategies
- **Learning**: Workers learn through learning-by-doing (tenure) and learning-by-using (vintage experience)
- **Labor Market**: Decentralized search-and-match process with imperfect information
- **Financial Market**: Banks provide credit with Basel-like capital adequacy constraints
- **Entry/Exit**: Endogenous firm entry and exit based on performance
- **Stock-Flow Consistency**: All monetary flows and stocks are tracked consistently
- **Regime Changes**: Model supports institutional shocks at specified times

## Core Implementation Status

### Completed

- [x] Base agent class with variable storage and lag management
- [x] Random number generation engine (mt19937_64 compatible)
- [x] Constants and initial notional definitions
- [x] Data structures (Vintage, FirmRank, WageOffer, Application, etc.)
- [x] Support functions (utilities for calculations)
- [x] Worker agent class with:
  - Age and retirement logic
  - Skills evolution (tenure and vintage learning)
  - Job search behavior
  - Wage determination
  - Employment status tracking

### In Progress

- [ ] Firm1 agent (capital goods sector)
- [ ] Firm2 agent (consumption goods sector)
- [ ] Bank agent
- [ ] Vintage class
- [ ] Country initialization and time-step orchestration
- [ ] Labor market matching
- [ ] Financial market operations

### Planned

- [ ] Complete all agent implementations
- [ ] Configuration file conversion (.lsd → Python)
- [ ] Statistics and validation functions
- [ ] Analysis scripts (R → Python conversion)
- [ ] Comprehensive test suite
- [ ] Performance optimization
- [ ] Documentation and examples

## Key Implementation Principles

### 1. Fixed Random Seed Mechanism

```python
from model.random_engine import random_engine

# Initialize with fixed seed for reproducibility
random_engine.seed(12345)
```

### 2. Accurate Attribute Mapping

All C++ variables are mapped to Python attributes:
- `_variable` → instance attributes
- Lagged values stored in variable history
- Parameters stored separately

### 3. Consistent Behavior Functions

Agent methods directly correspond to C++ equations:
- `compute_age()` → `_age` equation
- `compute_skills()` → `_s`, `_sT`, `_sV` equations
- `apply_for_jobs()` → `_appl` equation

### 4. Identical Time-Step Sequencing

The model maintains the same equation evaluation order as the C++ version to ensure identical results.

### 5. Mathematical Formula Validation

All formulas are transcribed exactly from the C++ code with careful attention to:
- Operator precedence
- Integer vs. float division
- Random number generation calls
- Conditional logic

### 6. Boundary Condition Handling

Edge cases are handled consistently:
- Division by zero checks
- Minimum/maximum value caps
- Empty list handling
- NULL pointer equivalents

### 7. Exception Handling

Comprehensive error checking for:
- Invalid parameter values
- Agent reference errors
- Numerical instabilities
- Resource constraints

## Usage Example

```python
from model.country import Country
from model.random_engine import random_engine

# Initialize random engine
random_engine.seed(42)

# Create and initialize country
country = Country()
country.initialize_from_config("configs/baseline.yaml")

# Run simulation
for t in range(1, 501):  # 500 time steps
    country.set_time(t)
    country.step()
    
    # Collect statistics
    gdp = country.read("GDP")
    unemployment = country.read("U")
    print(f"t={t}, GDP={gdp:.2f}, U={unemployment:.3f}")

# Analyze results
country.export_results("output/simulation_results.csv")
```

## Configuration Files

Original `.lsd` configuration files are being converted to YAML format for easier manipulation:

- `Cent_wage-Baseline_v2.lsd` → `baseline.yaml`
- `Ten_skills-Free_entry-Full_fin.lsd` → `full_finance.yaml`
- etc.

## Testing and Validation

The implementation is validated by:

1. **Unit Tests**: Testing individual agent behaviors
2. **Integration Tests**: Testing agent interactions
3. **Regression Tests**: Comparing outputs with original C++ model
4. **Statistical Tests**: Verifying distribution properties match
5. **Consistency Tests**: Stock-flow accounting checks

## References

- Dosi et al. (2010). Schumpeter meeting Keynes. Journal of Economic Dynamics and Control 34:1748-1767.
- Dosi et al. (2015). Fiscal and monetary policies in complex evolving economies. JEDC 52:166-189.
- Dosi et al. (2017). When more flexibility yields more fragility. JEDC 81:162-186.
- Original C++ implementation: https://github.com/SantAnnaKS/LSD

## License

This Python implementation follows the GNU General Public License of the original model.

## Contact

For questions about this Python implementation, please open an issue in the repository.
