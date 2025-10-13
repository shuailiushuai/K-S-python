# K+S Python Implementation - Quick Start Guide

## Installation

```bash
cd python
pip install -r requirements.txt
```

## Running the Model

```python
from model import KSModel

# Initialize model with configuration
model = KSModel('config/model_config.yaml', seed=1)

# Run simulation for 100 periods
results = model.run(periods=100)

# View results
print(f"Final GDP: {results['GDP'][-1]:.2f}")
print(f"Unemployment: {results['unemployment'][-1]:.2%}")
print(f"Total Debt: {results['total_debt'][-1]:.2f}")

# Export results
model.export_results('results.csv')
```

## Model Structure

### Agents

The model includes four agent types:

1. **Workers** - Search for jobs, learn skills, consume goods
2. **Banks** - Provide credit, manage deposits, implement Basel rules
3. **Firm1** (Capital-Good Firms) - Innovate, produce machines
4. **Firm2** (Consumption-Good Firms) - Produce goods using capital and labor

### Configuration

All parameters are loaded from `config/model_config.yaml`. Key parameters include:

```yaml
# Firm counts
Capital.F10: 50           # Initial capital-good firms
Consumption.F20: 200      # Initial consumption-good firms
Labor.Ls0: 250000         # Initial workers
Financial.B: 1            # Number of banks

# R&D parameters
Capital.nu: 0.04          # R&D share of revenue
Capital.alpha1: 3.0       # Innovation Beta parameter
Capital.xi: 0.5           # Innovation vs imitation share

# Market parameters
Consumption.chi: 1.0      # Replicator dynamics intensity
Consumption.mu20: 0.2     # Initial markup
```

See `config/model_config.yaml` for all 229 parameters.

## Code Example: Agent Behavior

### Worker Learning

```python
# Worker learns skills while employed
worker.update_skills_employed(
    tau_t=0.01,              # Learning rate
    flag_worker_lbu=3        # Both tenure and vintage learning
)

# Worker skills deteriorate when unemployed
worker.update_skills_unemployed(
    tau_u=0.01,              # Deterioration rate
    sigma=1.0,               # Public skill level
    flag_worker_lbu=3,
    has_training=False
)
```

### Firm1 Innovation

```python
# Capital-good firm innovates
success = firm1.innovate(
    alpha1=3.0, beta1=3.0,   # Beta distribution parameters
    xi=0.5,                   # R&D share for innovation
    x1_inf=-0.15,             # Lower productivity bound
    x1_sup=0.15,              # Upper productivity bound
    zeta1=0.3                 # R&D elasticity
)

if success:
    print(f"New productivity: {firm1._Atau:.3f}")
```

### Bank Credit Allocation

```python
# Bank ranks firms by net-wealth-to-sales ratio
rankings = bank.rank_clients(sector=2)

# Allocate credit according to pecking order
requested = {firm: firm._CD2 for firm in firm2_list}
allocated = bank.allocate_credit(sector=2, requested_credit=requested)
```

## Testing the Implementation

```python
# Test basic initialization
def test_initialization():
    model = KSModel('config/model_config.yaml', seed=1)
    assert len(model.workers) > 0
    assert len(model.firms1) > 0
    assert len(model.firms2) > 0
    assert len(model.banks) > 0
    print("✓ Initialization test passed")

# Test reproducibility
def test_reproducibility():
    model1 = KSModel('config/model_config.yaml', seed=42)
    model1.run(periods=10)
    
    model2 = KSModel('config/model_config.yaml', seed=42)
    model2.run(periods=10)
    
    assert model1.aggregates['GDP'] == model2.aggregates['GDP']
    print("✓ Reproducibility test passed")

# Run tests
test_initialization()
test_reproducibility()
```

## Architecture Overview

```
KSModel
├── Initialization
│   ├── Load configuration (229 parameters)
│   ├── Initialize random engine (seed)
│   ├── Create agents (Workers, Banks, Firm1, Firm2)
│   └── Set up initial conditions
│
├── Time Step (for each period)
│   ├── Central bank updates rates
│   ├── Banks compute credit supply
│   ├── Labor market (job search & matching)
│   ├── Firm1: R&D, innovation, production
│   ├── Firm2: Demand expectations, investment, production
│   ├── Goods market (consumption allocation)
│   ├── Financial results (profits, taxes)
│   ├── Market shares (replicator dynamics)
│   ├── Entry/exit processes
│   └── Aggregate statistics
│
└── Results
    ├── Time series data for all variables
    ├── Agent-level histories
    └── Export to CSV/Excel
```

## Key Features

### 1. Reproducibility
- Fixed random seed (MT19937_64)
- Deterministic execution
- Same results across runs with same seed

### 2. Flexibility
- All parameters in YAML configuration
- Easy to modify and experiment
- Multiple scenarios supported

### 3. Extensibility
- Modular agent design
- Easy to add new agent types
- Market mechanisms separate from agents

### 4. Mathematical Fidelity
- All formulas from original C++ code
- Beta distributions for R&D
- Replicator dynamics for competition
- Pecking order credit allocation

## Next Steps for Development

To complete the full model implementation:

1. **Implement Labor Market** (`markets/labor_market.py`)
   - Job application collection
   - Firm hiring sequences
   - Worker-firm matching

2. **Implement Goods Market** (`markets/goods_market.py`)
   - Demand allocation
   - Market clearing
   - Rationing

3. **Implement Capital Market** (`markets/capital_market.py`)
   - Machine ordering
   - Supplier selection
   - Delivery

4. **Add Government Operations** (`government.py`)
   - Tax collection
   - Unemployment benefits
   - Public debt management

5. **Complete Entry/Exit** (in agents)
   - Bankruptcy detection
   - Exit processing
   - Entry rate computation

6. **Validation**
   - Compare outputs with C++ version
   - Verify stock-flow consistency
   - Test parameter sensitivity

## Troubleshooting

### Import Errors
```bash
# Ensure dependencies are installed
pip install -r requirements.txt

# Check Python version (3.8+ required)
python --version
```

### Configuration Issues
```python
# Verify configuration loaded
import yaml
with open('config/model_config.yaml', 'r') as f:
    config = yaml.safe_load(f)
print(f"Loaded {len(config)} parameters")
```

### Memory Issues
```python
# Reduce number of agents for testing
config['Labor.Ls0'] = 1000      # Fewer workers
config['Consumption.F20'] = 50  # Fewer firms
```

## References

- **Original Paper**: Dosi et al. (2010). "Schumpeter meeting Keynes: A policy-friendly model of endogenous growth and business cycles." Journal of Economic Dynamics and Control.

- **Original Code**: C++ implementation with LSD framework (v5.1.3)

- **This Implementation**: Python reimplementation maintaining mathematical fidelity

## Support

For issues or questions:
1. Check `README.md` for detailed documentation
2. See `IMPLEMENTATION.md` for technical details
3. Review agent code in `agents/` directory
4. Consult original papers for model theory

---

**Status**: Core agent logic complete. Market coordination in progress.
**License**: GNU General Public License (as per original)
