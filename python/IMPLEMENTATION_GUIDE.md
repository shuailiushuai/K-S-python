# K+S ABM Model - Python Implementation Guide

## Complete Model Documentation

### 1. Model Overview

The K+S (Keynes + Schumpeter) model is a stock-flow consistent agent-based macroeconomic model that combines:
- **Keynesian** aggregate demand dynamics
- **Schumpeterian** technological innovation and creative destruction

#### Key Features:
- Heterogeneous agents with bounded rationality
- Endogenous innovation and productivity growth
- Labor market search-and-match
- Credit constraints and financial instability
- Stock-flow consistency (all financial flows are tracked)

### 2. Model Structure

#### 2.1 Agents

**Capital-Good Firms (Firm1)**
- Engage in R&D (innovation and imitation)
- Produce heterogeneous machines
- Set prices via cost-plus markup
- Compete through technology

**Consumption-Good Firms (Firm2)**
- Form adaptive demand expectations
- Produce consumption goods using machines and labor
- Manage vintage capital stock
- Set variable markups based on competitiveness
- Entry/exit based on performance

**Workers**
- Search for jobs (employed can also search)
- Accumulate skills (vintage + tenure)
- Consume with their income
- Receive unemployment benefits if jobless

**Banks**
- Collect deposits from firms and workers
- Provide loans subject to capital adequacy
- Use pecking order for credit rationing
- Can fail and require bailout

**Government**
- Collects taxes
- Pays unemployment benefits
- Provides worker training
- Manages public debt

**Central Bank**
- Sets prime interest rate (Taylor rule)
- Bails out failed banks

#### 2.2 Markets

**Labor Market**
- Decentralized search-and-match
- Workers apply to multiple firms
- Firms post vacancies with wage offers
- No guaranteed market clearing

**Goods Market**
- Workers demand consumption goods
- Replicator dynamics for market shares
- Rationing if supply < demand

**Capital Market**
- Network-based supplier-customer relationships
- Technology diffusion through client networks
- Machine orders and delivery

**Financial Market**
- Credit demand from firms
- Credit supply from banks (Basel constraints)
- Pecking order allocation

### 3. Time Step Sequence

Each time step follows a precise sequence (from `timeStep` equation):

1. **Central Bank**: Update interest rates (Taylor rule)
2. **Financial Market**: Update interest rate structure
3. **Firms2**: Form expectations, plan production, determine labor demand, plan investment
4. **Firms1**: Receive machine orders, plan production, determine labor demand
5. **Workers**: Submit job applications
6. **Labor Market**: Match workers to jobs
7. **Production**: Firms produce with actual labor
8. **Prices**: Firms set prices
9. **Government**: Determine expenditure
10. **Workers**: Determine consumption
11. **Goods Market**: Match demand and supply
12. **Profits**: Firms calculate profits and pay taxes
13. **Banks**: Calculate profits and pay taxes
14. **Government**: Collect taxes, update debt
15. **Aggregates**: Calculate macro variables
16. **Entry/Exit**: Handle firm dynamics
17. **Credit Scores**: Banks update firm credit classes

### 4. Key Parameters

#### Production and Technology
- `nu`: R&D intensity (share of revenue)
- `xi`: Innovation vs imitation split
- `zeta1`, `zeta2`: R&D success elasticities
- `x1inf`, `x1sup`: Innovation bounds
- `m1`: Labor productivity in capital sector
- `m2`: Machine productivity in consumption sector
- `b`: Machine payback period
- `eta`: Machine technical lifetime

#### Market Dynamics
- `chi`: Competitiveness selectivity
- `gamma`: Client network parameter
- `omega1`, `omega2`, `omega3`: Competitiveness weights (price, delivery, quality)
- `mu1`: Capital-good firm markup
- `mu20`: Initial consumption-good firm markup
- `upsilon`: Markup adjustment speed

#### Labor Market
- `omega`: Job applications by employed
- `omegaU`: Job applications by unemployed
- `phi`: Unemployment benefit rate
- `theta`: Slack when hiring
- `Tc`: Contract term
- `Tr`: Retirement age
- `psi1`-`psi6`: Wage determination parameters
- `tauT`: Tenure learning rate
- `tauU`: Skills decay rate

#### Financial System
- `Lambda`: Credit multiple
- `tauB`: Bank capital adequacy ratio
- `muD`, `muDeb`, `muRes`: Interest rate spreads
- `dB`, `d1`, `d2`: Dividend rates

#### Government and Policy
- `tr`: Tax rate
- `phi`: Unemployment benefit ratio
- `Gamma`: Training coverage
- `rT`: Target interest rate
- `gammaPi`, `gammaU`: Taylor rule weights

### 5. Implementation Choices

#### Why Pure Python (not Mesa 3.0)?

1. **Complex Equation Sequencing**: The model requires precise control over when each variable is computed
2. **Stock-Flow Consistency**: All financial flows must be tracked carefully
3. **Interdependencies**: Many cross-agent dependencies that don't fit standard Mesa schedulers
4. **Performance**: NumPy arrays more efficient for large numbers of agents
5. **Flexibility**: Direct control over all aspects of simulation

### 6. Usage Examples

#### Basic Simulation
```python
from ks_model import KSModel

# Create model with default parameters
model = KSModel(seed=42)

# Run simulation
model.run(time_steps=500)

# Get results
stats = model.get_statistics()
print(f"Final GDP: {stats['GDP_real'][-1]}")
print(f"Final Unemployment: {stats['unemployment_rate'][-1]*100:.1f}%")

# Save results
model.save_results("results.csv")

# Plot key variables
model.plot_results()
```

#### Custom Configuration
```python
from ks_model import KSModel

# Load custom configuration
model = KSModel(config_file="config/my_config.json", seed=42)
model.run(time_steps=1000)
```

#### Regime Change Experiment
```python
from ks_model import KSModel

# Model with regime change at t=200
model = KSModel(seed=42)
model.params.set('TregChg', 200)

# Set post-change parameters
model.params.set('omegaChg', 0.5)  # More job search after change
model.params.set('trChg', 0.15)  # Higher taxes after change

model.run(time_steps=500)
```

### 7. Validation

The Python implementation reproduces key stylized facts:

1. **Endogenous growth** through R&D and innovation
2. **Business cycles** from demand fluctuations
3. **Skewed firm size distribution** (fat-tailed)
4. **Persistent unemployment** above equilibrium
5. **Financial instability** with credit cycles

### 8. Comparison with Original C++ Version

#### Similarities:
- All agent types and behaviors
- Complete equation set
- Time step sequencing
- Stock-flow consistency
- Parameter structure

#### Differences:
- Python is ~10x slower than C++ (but more readable)
- Some simplified data structures (no LSD-specific constructs)
- Slightly different random number generation
- Results will differ in exact values but match qualitatively

### 9. Extensions and Customization

The modular structure allows easy extensions:

#### Adding New Agent Behaviors
Edit agent classes in `agents/` directory

#### Modifying Market Mechanisms
Edit market classes in `markets/` directory

#### Adding New Variables
Update `Statistics` class in `utils/statistics.py`

#### New Visualizations
Add functions to `visualization/plots.py`

### 10. Known Limitations

1. **Initial Conditions**: Some variables start at zero and need "burn-in" period
2. **Performance**: Large-scale simulations (>10,000 agents) may be slow
3. **Validation**: Quantitative validation against C++ version incomplete
4. **Documentation**: Some complex mechanisms simplified

### 11. Troubleshooting

#### GDP stays at zero:
- Model needs initialization period for production to start
- Check that firms have workers and capital
- Verify labor market is matching workers to firms

#### Unemployment at 100%:
- Check labor market matching logic
- Verify firms are posting vacancies
- Check wage offer mechanism

#### Model crashes:
- Check for division by zero in calculations
- Verify all agents have required attributes
- Check list indices and bounds

### 12. Future Improvements

1. **Performance optimization** with Numba/Cython
2. **Complete validation** against original model
3. **Additional configurations** (all paper scenarios)
4. **Sensitivity analysis** tools
5. **Interactive visualization** dashboard
6. **Parallel execution** for Monte Carlo experiments

### 13. References

**Key Papers:**
- Dosi et al. (2010). "Schumpeter meeting Keynes". JEDC 34:1748-1767
- Dosi et al. (2015). "Fiscal and monetary policies in complex evolving economies". JEDC 52:166-189
- Dosi et al. (2017). "When more flexibility yields more fragility". JEDC 81:162-186
- Dosi et al. (2018). "Causes and consequences of hysteresis". ICC 27:1015-1044

**Original Implementation:**
- LSD (Laboratory for Simulation Development): https://github.com/SantAnnaKS/LSD
- Original K+S code by Marcelo C. Pereira and Andrea Roventini

### 14. Contact and Contributions

This Python implementation was created to make the K+S model more accessible to researchers who prefer Python over C++/LSD. Contributions, bug reports, and suggestions are welcome!

---

**License**: GNU General Public License (same as original model)
**Python Implementation**: Based on K+S version 5.1.3 by Marcelo C. Pereira
