# K+S Agent-Based Model - Python Implementation

This is a complete Python replication of the K+S (Keynes+Schumpeter) Agent-Based Macroeconomic Model, originally implemented in C++ for the LSD (Laboratory for Simulation Development) platform.

## Model Description

The K+S model is a general disequilibrium, stock-and-flow consistent, agent-based model featuring:

- **Four types of heterogeneous agents:**
  - Workers/Consumers
  - Capital-good firms (Firm1)
  - Consumption-good firms (Firm2)
  - Banks

- **Key features:**
  - Endogenous innovation and imitation in capital goods sector
  - Heterogeneous machine vintages with different productivities
  - Decentralized labor market with search and matching
  - Banking sector with credit constraints and capital adequacy rules
  - Government fiscal policy and central bank monetary policy
  - Firm entry and exit dynamics
  - Full stock-flow consistency

## Directory Structure

```
python/
├── agents/               # Agent implementations
│   ├── base.py          # Base agent class
│   ├── worker.py        # Worker agent
│   ├── firm1.py         # Capital goods firm
│   ├── firm2.py         # Consumption goods firm
│   └── bank.py          # Bank agent
├── markets/             # Market/sector containers
│   └── __init__.py      # Labor, Capital, Consumption, Financial sectors
├── utils/               # Utility functions
│   ├── random_gen.py    # Random number generation
│   └── support.py       # Support functions
├── config_parser.py     # LSD configuration file parser
├── config.yaml          # Parsed configuration
├── model.py             # Main Country/Model class
└── run_simulation.py    # Simulation runner script
```

## Installation

### Requirements

- Python 3.8 or higher
- NumPy
- PyYAML

Install dependencies:

```bash
pip install numpy pyyaml
```

Or use the requirements file:

```bash
cd python
pip install -r requirements.txt
```

## Usage

### Running a Simulation

```bash
cd python
python run_simulation.py config.yaml --seed 1 --steps 500
```

### Command Line Options

- `config`: Path to YAML configuration file (required)
- `--seed`: Random seed for reproducibility (default: 1)
- `--steps`: Number of simulation steps (default: from config)
- `--output`: Output file for results JSON (optional)

### Example

```bash
# Run benchmark configuration for 500 steps
python run_simulation.py config.yaml --seed 42 --steps 500 --output results.json
```

### Using in Python Code

```python
from model import run_simulation

# Run simulation
country = run_simulation('config.yaml', seed=1, steps=500)

# Get results
results = country.get_results()
print(f"Final GDP: {results['GDPnom']:.2f}")
print(f"Unemployment: {results['unemployment_rate']*100:.2f}%")
```

## Configuration

The model uses YAML configuration files parsed from the original LSD `.lsd` files.

### Parsing LSD Configuration Files

To parse a new LSD configuration file:

```bash
python config_parser.py ../Cent_wage-Benchmark_v1.lsd output_config.yaml
```

### Key Configuration Parameters

#### Country-Level
- `TregChg`: Regime change period (0 = no change)
- `tr`: Tax rate
- `gG`: Growth rate of fixed public expenditure
- `Crec`: Unfilled consumption recovery limit

#### Financial Sector
- `B`: Number of banks
- `Lambda`: Credit limit multiple
- `tauB`: Minimum bank capital adequacy rate
- `rT`: Target prime interest rate
- `EqB0`: Initial bank equity

#### Capital Goods Sector
- `F10`: Initial number of Firm1
- `nu`: R&D investment rate
- `xi`: Share of R&D in innovation
- `mu1`: Firm1 markup
- `m1`: Worker output per period

#### Consumption Goods Sector
- `F20`: Initial number of Firm2
- `mu20`: Initial Firm2 markup
- `b`: Payback period for scrapping
- `eta`: Technical lifetime of machines
- `chi`: Replicator dynamics selectivity

#### Labor Market
- `Ls0`: Initial labor supply
- `delta`: Labor force growth rate
- `omega`: Job applications per employed worker
- `omegaU`: Job applications per unemployed worker
- `phi`: Unemployment benefit rate
- `w0min`: Minimum wage

## Model Features

### Fixed Random Seed

The model implements fixed random seed mechanisms to ensure reproducibility:

```python
from utils import set_seed
set_seed(42)  # All random operations will be deterministic
```

### Agent Classes

All agents inherit from `BaseAgent` and implement:
- Variable tracking with lag support
- Parameter management
- Hook system for agent relationships
- `initialize()` and `step()` methods

### Time Step Execution Order

Following the original C++ implementation, each time step executes in this order:

1. Financial sector updates interest rates
2. Consumption goods firms form expectations
3. Capital goods firms conduct R&D
4. Labor market matching
5. Production in both sectors
6. Consumption goods market clearing
7. Capital goods orders
8. Financial updates
9. Government fiscal operations
10. Macroeconomic aggregates calculation
11. Firm entry/exit

### Mathematical Formulas

All mathematical formulas are verified against the C++ implementation:

- **R&D success probabilities:**
  ```
  P_inn = 1 - (1 + RD_inn)^(-ζ₁)
  P_imi = 1 - (1 + RD_imi)^(-ζ₂)
  ```

- **Markup adjustment:**
  ```
  μ₂(t) = μ₂(t-1) × (1 + υ × Δf₂)
  ```

- **Replicator dynamics:**
  ```
  Δf₂ = χ × f₂ × (E₂ - Ē₂)
  ```

## Implementation Notes

### Completeness

This implementation includes:

✅ Core agent classes (Worker, Firm1, Firm2, Bank)
✅ All market/sector containers
✅ Random number generation with fixed seed
✅ Configuration parsing from LSD files
✅ Main simulation engine
✅ Time-step scheduling matching C++ order
✅ Key equation logic from all header files

### Simplifications

Some aspects are simplified in this version:
- Full worker-level learning dynamics can be extended
- Complete credit pecking order can be fully implemented
- Entry/exit dynamics use simplified rules
- Some edge cases may need additional handling

### Extensibility

The modular architecture allows easy extension:
- Add new agent types by subclassing `BaseAgent`
- Extend equations by adding methods to agent classes
- Modify behavior through configuration parameters
- Add custom output and analysis

## Validation

To validate against the C++ model:

1. Use identical configuration parameters
2. Set same random seed
3. Compare key outputs (GDP, unemployment, etc.)
4. Check intermediate agent states

## References

Original model papers:
- Dosi et al. (2010). "Schumpeter meeting Keynes." *JEDC* 34:1748-1767
- Dosi et al. (2015). "Fiscal and monetary policies in complex evolving economies." *JEDC* 52:166-189
- Dosi et al. (2017). "When more flexibility yields more fragility." *JEDC* 81:162-186

## License

This implementation follows the GNU General Public License, matching the original K+S model license.

## Authors

Python implementation based on the C++ code by Marcelo C. Pereira, University of Campinas.
Original K+S model developed by Andrea Roventini and contributors.

## Support

For issues or questions about the Python implementation, please refer to the original C++ code and documentation in the repository root directory.
