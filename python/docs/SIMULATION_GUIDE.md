# K+S Model - Simulation Guide

## Quick Start

### Basic Simulation

Run a simulation with default parameters:

```bash
python run_simulation.py --periods 50
```

### Using Configuration Files

Run with a YAML configuration:

```bash
python run_simulation.py --config configs/baseline.yaml --periods 100
```

### Saving Results

Export results to CSV:

```bash
python run_simulation.py --config configs/baseline.yaml --output results.csv
```

## Configuration Files

Configuration files are in YAML format and contain all model parameters.

### Structure

```yaml
# Country-level parameters
country:
  flagCons: 2                 # Consumption mode
  flagGovExp: 2               # Government expenditure mode
  tr: 0.2                     # Tax rate (20%)
  # ... more parameters

# Capital goods sector
capital:
  F10: 20                     # Initial firms
  mu1: 0.1                    # Mark-up
  nu: 0.04                    # R&D rate
  # ... more parameters

# Consumption goods sector
consumption:
  F20: 50                     # Initial firms
  mu20: 0.2                   # Initial mark-up
  b: 3.0                      # Payback period
  # ... more parameters

# Financial sector
financial:
  B: 5                        # Number of banks
  tauB: 0.08                  # Capital adequacy (8%)
  rT: 0.03                    # Target rate (3%)
  # ... more parameters

# Labor market
labor:
  Ls0: 10000                  # Labor supply
  Lscale: 10                  # Scaling factor
  phi: 0.5                    # Unemployment benefit rate
  # ... more parameters

# Simulation settings
simulation:
  periods: 100                # Simulation length
  seed: 42                    # Random seed
  warmup: 20                  # Warm-up periods
```

### Key Parameters

#### Model Flags

- `flagCons` (0-2): How consumers handle forced savings
  - 0: Ignore past unfulfilled demand
  - 1: Spend all accumulated savings
  - 2: Gradually spend savings (default)

- `flagGovExp` (0-3): Government expenditure mode
  - 0: Work-or-die (minimal support)
  - 1: Minimum income + growth
  - 2: Unemployment benefits (default)
  - 3: Counter-cyclical spending

- `flagTax` (0-2): Tax system
  - 0: No taxes
  - 1: Basic taxation (default)
  - 2: Full taxation with dividend tax

- `flagWorkerLBU` (0-3): Worker learning-by-using
  - 0: No learning
  - 1: Learning by vintage only (default)
  - 2: Learning by tenure only
  - 3: Both vintage and tenure

#### Capital Sector

- `F10`: Initial number of capital goods firms
- `F1min`, `F1max`: Min/max firm count
- `mu1`: Mark-up on unit cost (e.g., 0.1 = 10%)
- `nu`: R&D investment rate as fraction of sales (e.g., 0.04 = 4%)
- `x1inf`, `x1sup`: Innovation improvement bounds

#### Consumption Sector

- `F20`: Initial number of consumption goods firms
- `F2min`, `F2max`: Min/max firm count
- `mu20`: Initial mark-up
- `b`: Payback period for investment decisions
- `eta`: Machine lifetime (periods)
- `f2min`: Market share threshold for exit

#### Financial Sector

- `B`: Number of banks
- `tauB`: Minimum capital adequacy ratio (Basel, typically 0.08)
- `rT`: Central bank target interest rate
- `muDeb`, `muD`: Spreads for debt and deposits

#### Labor Market

- `Ls0`: Total labor supply
- `Lscale`: Scaling factor (workers/agent, for performance)
- `Tc`: Work contract term (periods)
- `Tr`: Work life duration (periods until retirement)
- `phi`: Unemployment benefit rate (fraction of average wage)
- `omega`, `omegaU`: Number of job applications (employed/unemployed)

## Command-Line Options

### run_simulation.py

```
usage: run_simulation.py [-h] [--config CONFIG] [--periods PERIODS] 
                         [--output OUTPUT] [--no-report]

K+S Model Simulation Runner

optional arguments:
  -h, --help            Show this help message and exit
  --config CONFIG, -c CONFIG
                        Path to configuration file (YAML)
  --periods PERIODS, -p PERIODS
                        Number of periods to simulate (overrides config)
  --output OUTPUT, -o OUTPUT
                        Output file path for results (CSV)
  --no-report           Skip summary report
```

### Examples

```bash
# Basic simulation with default settings
python run_simulation.py

# Load configuration and run 200 periods
python run_simulation.py -c configs/baseline.yaml -p 200

# Run and save results
python run_simulation.py -c configs/baseline.yaml -o my_results.csv

# Run without report (faster)
python run_simulation.py -p 50 --no-report
```

## Output Format

### Console Output

The simulation produces a summary report with:

1. **Time Series Overview**: Sample of periods showing GDP, unemployment, debt
2. **Summary Statistics**: Averages for key indicators (post-warmup)
3. **Labor Market**: Employment, unemployment, wages
4. **Sector Statistics**: Firms, production, prices, profits
5. **Government**: Expenditure, taxes, deficit, debt

### CSV Output

When using `--output`, results are saved with columns:

- `Period`: Time period
- `GDPreal`: Real GDP
- `GDPnom`: Nominal GDP
- `Unemployment`: Unemployment rate (0-1)
- `Inflation`: Inflation rate (currently 0, TBD)
- `Debt`: Government debt
- `Deficit`: Government deficit

## Creating Custom Configurations

1. Copy an existing configuration:
   ```bash
   cp configs/baseline.yaml configs/my_scenario.yaml
   ```

2. Edit parameters as needed:
   ```yaml
   country:
     tr: 0.15                  # Lower tax rate
   
   capital:
     nu: 0.06                  # More R&D investment
   
   consumption:
     f2min: 0.002              # Higher exit threshold
   ```

3. Run your scenario:
   ```bash
   python run_simulation.py -c configs/my_scenario.yaml
   ```

## Typical Scenarios

### High Innovation

Increase R&D investment:
```yaml
capital:
  nu: 0.08                    # Double R&D rate
  x1sup: 0.5                  # Higher innovation potential
```

### Tight Credit

Increase banking regulation:
```yaml
financial:
  tauB: 0.12                  # Higher capital requirement
  muDeb: 0.05                 # Higher interest spread
```

### Generous Welfare

Increase government support:
```yaml
country:
  flagGovExp: 3               # Counter-cyclical spending

labor:
  phi: 0.7                    # Higher unemployment benefits
  theta: 0.3                  # More training
```

### Flexible Labor Market

Adjust labor parameters:
```yaml
labor:
  Tc: 6                       # Shorter contracts
  omega: 3                    # More job applications
  chi: 0.7                    # Higher search probability
```

## Troubleshooting

### "Configuration file not found"
- Check the path to your YAML file
- Use relative or absolute paths

### "Invalid configuration"
- Check YAML syntax (proper indentation)
- Ensure required sections exist
- Verify parameter ranges (e.g., 0 ≤ tr ≤ 1)

### Simulation diverges or crashes
- Reduce time steps or check parameter values
- Try default configuration first
- Check for extreme parameter combinations

### Very slow simulation
- Reduce `Ls0` (labor supply)
- Increase `Lscale` (labor scaling)
- Reduce number of firms (F10, F20)
- Reduce simulation periods

## Performance Tips

For faster simulations:

1. **Scale down agents**:
   ```yaml
   capital:
     F10: 10                   # Fewer firms
   consumption:
     F20: 20
   labor:
     Ls0: 5000                 # Smaller labor force
     Lscale: 20                # Higher scaling
   ```

2. **Skip reporting**:
   ```bash
   python run_simulation.py --no-report
   ```

3. **Reduce periods**:
   ```bash
   python run_simulation.py -p 50
   ```

## Next Steps

- Explore different scenarios by modifying parameters
- Compare results across configurations
- Analyze time series data from CSV exports
- Experiment with policy interventions
- Validate results against economic theory

For more information, see:
- `FINAL_SUMMARY.md` - Implementation status
- `README.md` - Complete documentation
- `IMPLEMENTATION_PLAN.md` - Development roadmap
- `example_*.py` - Individual agent examples
