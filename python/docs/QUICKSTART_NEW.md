# K+S Model Python Implementation - Quick Start Guide

## What's Available Now

The K+S model Python implementation now has **all core agent types** implemented:

- ✅ **Worker** - Labor supply, skills, job search
- ✅ **Firm1** - Capital goods, R&D, innovation
- ✅ **Firm2** - Consumption goods, production, investment
- ✅ **Vintage** - Machine vintages, scrapping
- ✅ **Bank** - Credit, interest rates, balance sheet
- ✅ **Labor Market** - Search-and-match, hiring

**Current Status: 65% Complete** | 7 Working Examples | 2,865 Lines of Code

---

## Installation

```bash
cd python
pip install numpy
```

That's it! Only numpy is required.

---

## Running Examples

### 1. Worker Agent - Skills and Job Search

```bash
python example_worker.py
```

**Demonstrates:**
- Worker aging and retirement
- Skills evolution (tenure and vintage learning)
- Job search behavior
- Employment transitions

### 2. Firm1 - R&D and Innovation

```bash
python example_firm1.py
```

**Demonstrates:**
- R&D expenditure calculation
- Innovation process (Beta-distributed improvements)
- Imitation (distance-based technology copying)
- Technology selection (cost minimization)
- Competitive dynamics

### 3. Firm2 - Production and Investment

```bash
python example_firm2.py
```

**Demonstrates:**
- 5 demand expectation modes
- Production planning with inventories
- Investment decisions (expansion + substitution)
- Labor demand calculation
- Wage setting with premiums
- Pricing with mark-up
- Supplier selection

### 4. Vintage - Machine Generations

```bash
python example_firm2.py
```

**Demonstrates:**
- Vintage tracking
- Scrapping decisions (age and economic)
- Production from vintages

### 5. Bank - Credit Operations

```bash
python example_bank.py
```

**Demonstrates:**
- Credit supply (capital adequacy, leverage)
- Credit allocation using pecking order
- Interest rate setting
- Balance sheet management
- Profit calculation
- Bankruptcy detection

### 6. Labor Market - Matching

```bash
python example_labor.py
```

**Demonstrates:**
- Job applications
- Search and matching
- 4 hiring modes (wage, skills, tenure, efficiency)
- Unemployment statistics
- Wage and skill averages
- Government training

---

## Quick Code Examples

### Create a Worker

```python
from model import Worker, Agent, random_engine

# Set seed for reproducibility
random_engine.seed(42)

# Create labor market parent
labor = Agent("Labor", None)
labor.set_param("Tr", 40)  # Retirement age

# Create worker
worker = Worker(worker_id=1, parent=labor)
worker.initialize(age=25, tc=12, w_res=1.0, sv0=0.9)

# Simulate
for t in range(10):
    worker.compute_age(tr=40)
    worker.compute_skills(...)
    worker.update_lags()
```

### Create a Firm1 (Capital Goods)

```python
from model import Firm1, Agent

# Create capital sector parent
capital = Agent("Capital", None)
capital.write("w1avg", 1.0, 1)

# Create firm
firm = Firm1(firm_id=1, parent=capital)
firm.write("_Atau", 1.0, 1)
firm.write("_Btau", 1.0, 1)

# R&D and innovation
params = {
    'xi': 0.5, 'zeta1': 3.0, 'zeta2': 3.0,
    'alpha1': 3.0, 'beta1': 3.0,
    'x1inf': -0.15, 'x1sup': 0.15,
    # ... other params
}
Atau_new, Btau_new = firm.compute_innovation_imitation(params)
```

### Create a Firm2 (Consumption Goods)

```python
from model import Firm2, Agent

# Create consumption sector parent
consumption = Agent("Consumption", None)

# Create firm
firm = Firm2(firm_id=1, parent=consumption)
init_params = {
    'entry_time': 0,
    'A2': 1.2,
    'NW2': 50.0,
    'mu2': 0.2
}
firm.initialize(init_params)

# Demand expectation
exp_params = {'e': 4, 'rho': 0.9}
demand = firm.compute_demand_expectation(mode=4, params=exp_params)

# Production planning
prod = firm.compute_desired_production(u=0.1)
```

### Create a Bank

```python
from model import Bank, Agent

# Create financial sector parent
financial = Agent("Financial", None)
financial.write("r", 0.03, 1)  # Base rate

# Create bank
bank = Bank(bank_id=1, parent=financial)
init_params = {
    'bank_id': 1,
    'NWb': 15.0,
    'Depo': 80.0,
    'Loans': 70.0,
    'lambda': 0.05
}
bank.initialize(init_params)

# Credit supply
credit_params = {'alpha': 0.08, 'betaB': 0.9, 'lambda': 0.05}
total_credit = bank.compute_total_credit(credit_params)

# Allocate to firms
allocated, allocations = bank.allocate_credit_sector1(firms, demand)
```

### Use Labor Market

```python
from model import LaborMarket, create_application

# Create labor market
labor = LaborMarket(parent=country)

# Collect applications
apps = [create_application(w) for w in workers if w._employed == 0]

# Match to firms
matches = labor.match_sector1(firms, apps, hiring_mode=1)  # Skills-based

# Execute matches
labor.execute_matches(matches)

# Statistics
Ue, U, Us = labor.compute_unemployment_rate(workers)
wAvg = labor.compute_average_wage(workers)
```

---

## Key Concepts

### Agent Hierarchy

```
Country (root)
├── Financial Sector
│   └── Banks
├── Capital Sector
│   └── Firm1 agents
├── Consumption Sector
│   ├── Firm2 agents
│   └── Vintages (children of Firm2)
└── Labor Market
    └── Workers
```

### Variable Storage

- **Current value:** `agent.read("_var", 0)` or `agent._var`
- **Lagged value:** `agent.read("_var", 1)` for t-1
- **Write value:** `agent.write("_var", value, lag)`
- **Update lags:** `agent.update_lags()` at end of period

### Random Numbers

```python
from model.random_engine import random_engine

# Set seed for reproducibility
random_engine.seed(12345)

# Generate random numbers
u = random_engine.uniform(0, 1)
n = random_engine.normal(0, 1)
b = random_engine.beta(3, 3)
```

### Time Stepping

Each agent typically follows this pattern per period:

1. Read lagged values from previous period
2. Compute current period values
3. Write current values
4. Update lags for next period

```python
for t in range(1, 101):
    # Compute current period
    value = agent.compute_something(params)
    agent.write("_var", value)
    
    # Prepare for next period
    agent.update_lags()
```

---

## Agent Capabilities

### Worker
- **Methods:** `compute_age()`, `compute_skills()`, `apply_for_jobs()`, `compute_wage_request()`
- **Key Variables:** `_age`, `_employed`, `_s`, `_sT`, `_sV`, `_w`, `_Te`, `_Tu`
- **Learning:** Tenure (learning-by-doing), Vintage (learning-by-using)

### Firm1
- **Methods:** `compute_innovation_imitation()`, `compute_rd_expenditure()`, `compute_price()`, `compute_labor_demand()`
- **Key Variables:** `_Atau`, `_Btau`, `_p1`, `_RD`, `_L1d`, `_f1`, `_NW1`
- **Core Feature:** Endogenous technical change through R&D

### Firm2
- **Methods:** `compute_demand_expectation()`, `compute_desired_production()`, `compute_investment_plan()`, `select_supplier()`
- **Key Variables:** `_D2e`, `_Q2d`, `_A2`, `_L2d`, `_w2o`, `_p2`, `_f2`
- **Modes:** 5 demand expectation modes, multiple wage/hiring modes

### Vintage
- **Methods:** `compute_scrapping()`, `compute_labor_required()`, `compute_production()`
- **Key Variables:** `_IDvint`, `_tVint`, `_Avint`, `_nVint`, `_toUseVint`
- **Core Feature:** Machine generation tracking with learning-by-using

### Bank
- **Methods:** `compute_total_credit()`, `allocate_credit_sector1/2()`, `compute_profits()`
- **Key Variables:** `_TC`, `_Loans`, `_Depo`, `_NWb`, `_iB`, `_fB`
- **Core Feature:** Credit rationing via pecking order

### Labor Market
- **Methods:** `match_sector1/2()`, `compute_unemployment_rate()`, `train_unemployed()`
- **Key Variables:** `_Ue`, `_U`, `_wAvg`, `_sAvg`, `_Ltrain`
- **Modes:** 4 hiring modes, multiple firing rules

---

## Parameter Reference

### Common Parameters

```python
# Model-wide
Tr = 40          # Retirement age
Tc = 12          # Contract term
delta = 0.01     # Population growth

# Firm1
nu = 0.04        # R&D share of sales
xi = 0.5         # Innovation share of R&D
mu1 = 0.1        # Mark-up sector 1
m1 = 1.0         # Machine modularity sector 1

# Firm2
e = 4            # Demand memory
u = 0.1          # Target utilization
mu20 = 0.2       # Initial mark-up sector 2
m2 = 5.0         # Machine modularity sector 2
b = 10           # Payback period

# Bank
alpha = 0.08     # Capital adequacy ratio
betaB = 0.9      # Leverage ratio
lambda = 0.05    # Reserve requirement

# Labor
Gamma = 0.5      # Training coverage
tauT = 0.02      # Tenure learning rate
tauG = 0.05      # Training learning rate
```

---

## What's Not Yet Available

### Cannot Do Yet
- ❌ Run complete multi-period simulation
- ❌ Full time-step coordination
- ❌ Government fiscal operations
- ❌ Central bank monetary policy
- ❌ Aggregate statistics calculation
- ❌ Stock-flow consistency checks

### Coming Soon
- Country orchestrator (in development)
- Full simulation runner
- Configuration system
- Testing framework
- Validation against C++ model

---

## Getting Help

### Documentation
- `README.md` - Full project documentation
- `IMPLEMENTATION_PLAN.md` - Development roadmap
- `FINAL_SUMMARY.md` - Original status report
- `COMPLETION_SUMMARY.md` - Recent progress summary

### Examples
All examples are self-contained and demonstrate specific functionality:
- `example_worker.py` - Worker behavior
- `example_firm1.py` - Innovation and R&D
- `example_firm2.py` - Production and investment
- `example_bank.py` - Credit and finance
- `example_labor.py` - Labor market matching

### Code Structure
- `model/agent.py` - Base agent class
- `model/worker.py` - Worker implementation
- `model/firm1.py` - Capital goods firms
- `model/firm2.py` - Consumption goods firms
- `model/vintage.py` - Machine vintages
- `model/bank.py` - Banks
- `model/labor.py` - Labor market
- `model/support.py` - Utility functions
- `model/data_structures.py` - Data classes

---

## Tips

1. **Always set random seed** for reproducible results
2. **Initialize agents** with `initialize()` method
3. **Update lags** at end of each period with `update_lags()`
4. **Check examples** for usage patterns
5. **Use type hints** in your code for clarity
6. **Read from lag 1** for previous period values
7. **Write to lag 0** for current period values

---

**Version:** 5.1.3-python  
**Status:** 65% Complete - Core Agents Operational  
**Last Updated:** October 11, 2025
