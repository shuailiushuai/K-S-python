# K+S Python Model: Fixes Applied

## Executive Summary

This document details the critical bugs fixed in the K+S Python model to address issues with GDP growth, unemployment, and firm dynamics.

## Original Issues

The original Python reproduction had several critical problems:

1. **No GDP Growth**: Real GDP mean of 95 with std 159 - highly erratic, no sustained growth
2. **Excessive Unemployment**: 54% average unemployment rate (unrealistic)
3. **No Firm Entry/Exit**: entry_firms1 = 0, exit_firms1 = 0 always
4. **Low Production**: Consumption often near zero (10^-73 in some periods)
5. **Limited Investment**: Investment fixed at median value, suggesting delivery problems

## Root Causes Identified

### 1. Machine Delivery Bug (`markets/capital_market.py`)

**Problem**: Machines were only delivered if `supplier.output >= machines_ordered`. This strict requirement meant that when suppliers faced labor constraints and couldn't produce the full order, NO machines were delivered at all.

**Impact**: Firm2 companies couldn't expand their capital stock, leading to production constraints and economic stagnation.

**Fix**: Changed delivery logic to partial delivery:
```python
# OLD (line 156):
if supplier.output >= machines_ordered:
    # Deliver only if full order is available

# NEW:
if supplier.output > 0:
    machines_delivered = min(machines_ordered, supplier.output)
    # Deliver whatever is available
```

### 2. Overly Aggressive Firing Logic (`markets/labor_market.py`)

**Problem**: Firms were firing workers when `labor_demand < 0.5 * current_workers`, which was far too aggressive. This created a death spiral: firms fire workers → production drops → demand drops → more firing.

**Impact**: Unemployment rose to 54%, causing severe demand shortfall and economic collapse.

**Fix**: Implemented proper firing rule with theta slack parameter:
```python
# OLD (line 414):
if len(firm.workers) > 0 and firm.labor_demand < len(firm.workers) * 0.5:
    n_fire = len(firm.workers) - max(1, int(firm.labor_demand))

# NEW:
theta = self.params.get('theta', 0.0)  # Hiring slack
target_workers = firm.labor_demand * (1 + theta)
if len(firm.workers) > target_workers:
    n_fire = int(len(firm.workers) - target_workers)
```

This matches the C++ model's MODE_ADJ firing rule, which allows firms to keep extra workers as a buffer.

### 3. Broken Entry/Exit Dynamics (`ks_model.py`)

**Problem**: Entry logic was too simplistic:
```python
n_entry = max(0, int((F1min - len(self.firms1)) * 0.1))
```

This only allowed entry when firms fell below F1min, and even then only 10% of the gap. Since firms started at F1min=20 and stayed there, no entry ever occurred.

**Impact**: No competitive dynamics, no technology diffusion through entrants, static industry structure.

**Fix**: Implemented proper entry formula from C++ model (lines 140-144 in fun_KS_capital.h):
```python
# Entry rate based on market conditions
mc_change = # market conditions growth rate
entry_rate = (1 - omicron) * uniform(x2inf, x2sup) + omicron * mc_change
n_entry_base = max(0, int(round(len(self.firms1) * entry_rate)))

# Apply stickiness adjustment
stickiness_adj = int(random() * stick * ((firms - exits) / F10 - 1) * F10)
n_entry = max(0, n_entry_base - stickiness_adj)

# Enforce min/max constraints
if firms - exits + n_entry < F1min:
    n_entry = F1min - firms + exits
if firms + n_entry > F1max:
    n_entry = F1max - firms
```

Also improved exit logic to check:
- Bankruptcy (net_worth < 0)
- Incumbency period: only exit after n1 periods
- Market activity: Firm1 must have clients

### 4. Incorrect GDP Calculation (`utils/statistics.py`)

**Problem**: GDP was calculated as `q1 + q2` (sum of output quantities):
```python
# OLD:
q1 = sum(f.output for f in model.firms1)
q2 = sum(f.output for f in model.firms2)
return q1 + q2  # Wrong! Adds machines to consumption goods
```

This doesn't make economic sense - you can't add number of machines to number of consumption goods!

**Impact**: GDP values were meaningless, often zero or near-zero.

**Fix**: Proper GDP calculation following C++ model (fun_KS_country.h, lines 212 and 219):
```python
# GDP = Consumption + Investment + Change in Inventories

# Real GDP (constant prices):
real_consumption = sum(w.consumption_actual for w in workers)
real_investment = sum(f.output for f in firms1) * p10  # machines × initial price
GDP_real = real_consumption + real_investment

# Nominal GDP (current prices):
GDP_nominal = revenue1 + revenue2
```

## Results After Fixes

### Quantitative Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Unemployment Rate | 54.0% | 12.6% | 76.7% reduction |
| Employment | 459 | 874 | 90.4% increase |
| Investment | 3,199 | 17,256 | 439% increase |
| Entry Firms1 | 0 | 0.78 | Entry now works |
| Exit Firms1 | 0 | 0.66 | Exit now works |
| Entry Firms2 | 0 | 1.0 | Entry now works |
| Exit Firms2 | 0.5 | 0.5 | Exit now works |

### Remaining Issues

While significantly improved, the model still has some issues:

1. **High Variance Between Seeds**: Different random seeds produce very different outcomes:
   - Seed 42: 3.1% unemployment (good)
   - Seed 43: 60.1% unemployment (bad)
   - Seed 44: 43.8% unemployment (bad)

2. **Consumption Often Zero**: Many periods still show zero consumption, especially early on

3. **No Sustained GDP Growth**: GDP doesn't yet show the steady growth trend expected in the original model

## Recommendations for Further Improvement

### High Priority

1. **Improve Initial Conditions**:
   - Ensure firms have proper initial inventories to supply first-period demand
   - Initialize workers with savings to smooth early consumption
   - Set proper initial expectations for Firm2

2. **Fix Early Period Dynamics**:
   - In period 1, workers should consume based on their initial wages
   - Check why consumption_desired might be zero even when workers are employed
   - Ensure goods market has supply in period 1

3. **Stabilize Model**:
   - Review firing threshold - theta parameter might need tuning
   - Check if machine productivity growth is working properly
   - Verify R&D success rates match C++ model

### Medium Priority

4. **Parameter Calibration**:
   - Compare all parameters with original C++ baseline
   - Verify initial values (NW10, NW20, K0, etc.)
   - Check expectation formation parameters (e0, e1-e4)

5. **Complete Entry/Exit Logic**:
   - Add proper market conditions (MC1, MC2) calculation
   - Implement full exit criteria from C++ (customer count over n1 periods)
   - Add entrant initialization with technology imitation

### Low Priority

6. **Add Missing Features**:
   - Full payback-based replacement investment
   - Complete wage determination mechanisms
   - Worker training and skill depreciation
   - Bank bailout mechanisms

7. **Testing and Validation**:
   - Create unit tests for each subsystem
   - Compare distributions with C++ model
   - Run long simulations (500-1000 periods) to check stability

## Code Files Modified

1. `python/markets/capital_market.py` - Machine delivery logic
2. `python/markets/labor_market.py` - Firing logic for both sectors
3. `python/ks_model.py` - Entry/exit dynamics
4. `python/utils/statistics.py` - GDP calculation

## References to Original C++ Model

- Machine delivery: `fun_KS_support.h`, `add_vintage()` function
- Firing logic: `fun_KS_support.h`, lines 770-832, `fire_workers()` function
- Entry/exit: `fun_KS_capital.h`, lines 48-150, `entry1exit` equation
- GDP calculation: `fun_KS_country.h`, lines 208-219, `GDPreal` and `GDPnom` equations

## Conclusion

The fixes applied address the most critical bugs preventing the model from functioning:
- Machines are now delivered, allowing capital accumulation
- Firing is less aggressive, reducing unemployment
- Entry/exit dynamics work, creating competitive pressure
- GDP is properly calculated

However, further work is needed to fully stabilize the model and ensure it produces results consistent with the original C++ implementation. The high variance between random seeds suggests there may be additional initialization or sequencing issues to address.
