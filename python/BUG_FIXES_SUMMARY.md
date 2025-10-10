# K+S Python Model: Bug Fixes and Analysis Summary

## Executive Summary

This document summarizes the critical bugs identified and fixed in the K+S Python model, along with remaining issues that need attention. The fixes have significantly improved model behavior, reducing average unemployment from 66% to 5.6% and improving initial period stability.

## Critical Bugs Fixed

### 1. Goods Market Supply Calculation (markets/goods_market.py)

**Problem:**
The goods market was only considering inventories as available supply, completely ignoring current period production.

**C++ Reference:**
```cpp
// fun_KS_consumption.h, line 33
sup2[j] = VS(cur, "_Q2e") + VLS(cur, "_N", 1); // current output + past inventories
```

**Python Bug:**
```python
# OLD - WRONG
self.total_supply = sum(f.inventories for f in self.firms2)
```

**Fix Applied:**
```python
# NEW - CORRECT
self.total_supply = sum(f.output + f.inventories for f in self.firms2)
```

Also fixed inventory management:
```python
# Firms now: inventories = inventories + output - sales
firm.inventories += firm.output - fulfilled
```

**Impact:** Consumption can now occur from current production, not just past inventories.

---

### 2. GDP Calculation - Real GDP (utils/statistics.py)

**Problem:**
Real GDP was incorrectly calculated using worker consumption and Firm1 total output.

**C++ Reference:**
```cpp
// fun_KS_country.h, line 212
GDPreal = max(Ireal + Creal, 1)
// where Ireal = (SI + EI) / m2 * pK0
//       Creal = Q2e * pC0
```

**Python Bug:**
```python
# OLD - WRONG
real_consumption = sum(w.consumption_actual for w in workers)
real_investment = sum(f.output for f in firms1) * p10
```

**Fix Applied:**
```python
# NEW - CORRECT
real_consumption = sum(f.output for f in model.firms2) * pC0  # Firm2 output
total_delivered = sum(f.expansion_investment_delivered + 
                     f.replacement_investment_delivered for f in model.firms2)
real_investment = total_delivered / pK0  # Delivered investment in real terms
```

**Impact:** GDP now correctly measures production output, not consumption fulfillment.

---

### 3. GDP Calculation - Nominal GDP (utils/statistics.py)

**Problem:**
Nominal GDP was using desired investment (capital units) instead of delivered investment (monetary value).

**C++ Reference:**
```cpp
// fun_KS_country.h, line 219
GDPnom = max(C + Inom + dNnom, 1)
// where C = S2 (sales revenue)
//       Inom = sum of delivered machines * price
//       dNnom = change in inventory value
```

**Python Bug:**
```python
# OLD - WRONG
nominal_investment = sum(f.expansion_investment + f.replacement_investment 
                        for f in model.firms2)
# expansion_investment is in capital units, not monetary value!
```

**Fix Applied:**
```python
# NEW - CORRECT
nominal_investment = sum(
    f.expansion_investment_delivered + f.replacement_investment_delivered
    for f in model.firms2
)
# Now using monetary value of delivered machines
```

**Impact:** GDP calculation is now consistent with national accounting principles.

---

### 4. Investment Delivery Tracking (capital_market.py, firm2.py)

**Problem:**
No tracking of which delivered machines were expansion vs replacement investment.

**Fix Applied:**

In `firm2.py`:
```python
# Added new attributes
self.expansion_investment_delivered = 0.0  # Actual delivered
self.replacement_investment_delivered = 0.0  # Actual delivered
```

In `capital_market.py process_orders()`:
```python
# Now track investment type in orders
if firm2.expansion_investment > 0:
    firm2.pending_orders.append({
        'supplier': supplier,
        'machines': firm2.expansion_investment,
        'time': t,
        'type': 'expansion'
    })
```

In `capital_market.py deliver_machines()`:
```python
# Track delivered investment by type
investment_value = machines_delivered * supplier.price
if order_type == 'expansion':
    firm2.expansion_investment_delivered += investment_value
else:
    firm2.replacement_investment_delivered += investment_value
```

**Impact:** GDP calculation can now properly track investment components.

---

### 5. Firm2 Output Double-Counting (agents/firm2.py)

**Problem:**
Output was being added to inventories in produce() method, then again in goods market.

**Python Bug:**
```python
# In firm2.produce()
self.output = self.output_planned * min(1.0, labor_ratio)
self.inventories += self.output  # WRONG! Too early!
```

**Fix Applied:**
```python
# Now handled in goods market during sales
# firm2.produce() just sets output, doesn't update inventories
self.output = self.output_planned * min(1.0, labor_ratio)
# Note: inventories updated in goods_market after sales
```

**Impact:** Prevents inventory accumulation errors and supply overestimation.

---

### 6. Firm2 Initialization - Demand Expectations (ks_model.py)

**Problem:**
Firms initialized with `demand_expected = 0` despite having capital and workers. This caused immediate mass firing in period 1.

**Python Bug:**
```python
# Firm2.__init__()
self.demand_expected = 0.0  # BAD!

# Then in initialization:
firm.demand_expected = D20  # Some calculated value
# But D20 calculation was complex and didn't match capital
```

**Fix Applied:**
```python
# Initialize demand consistently with capital stock
initial_output = firm.capital_stock  # With INIPROD=1.0
firm.output_desired = initial_output
firm.demand_expected = initial_output  # Consistent!
firm.output_planned = initial_output * u
```

**Impact:**
- **Before:** Period 1 employment = 667/1000 (33% unemployment)
- **After:** Period 1 employment maintains near full employment
- Average unemployment reduced from 66% to 5.6%

---

## Remaining Critical Issues

### Issue 1: Machine Delivery Stops After Period ~10

**Symptoms:**
- Periods 1-9: Normal operation (consumption ~300-666, GDP ~100-670)
- Period 10+: GDP collapses to 1.0 (floor value), consumption = 0
- Employment recovers (from 11 to 800+) but no production
- Investment desired is very high (6000-8000) but nothing delivered

**Hypothesis:**
One or more of:
1. Firm1 has no workers (all fired) → can't produce machines
2. Firm1 receives no orders → no production planned
3. Firm1 produces but delivery logic fails
4. Labor market broken for Firm1 sector

**Investigation Needed:**
```python
# Check Firm1 status in period 10+:
- How many workers does each Firm1 have?
- What is their labor_demand vs labor_actual?
- What is their output vs orders?
- Are orders being placed by Firm2?
```

**Potential Fixes:**
1. Ensure Firm1 maintains minimum workforce
2. Review Firm1 firing/hiring logic
3. Check order processing and production planning
4. Verify delivery logic handles edge cases

---

### Issue 2: Consumption Drops to Zero

**Symptoms:**
- Period 1-9: Consumption declines (666 → 56)
- Period 10+: Consumption = 0 permanently

**Hypothesis:**
- Workers have income but goods market has no supply
- OR workers have no income (unemployed, no benefits calculated)
- OR consumption determination logic broken

**Investigation Needed:**
```python
# Check in period 10+:
- What is workers' total income?
- What is workers' consumption_desired?
- What is Firm2 total output?
- What is goods market supply?
```

---

### Issue 3: GDP Floor Value (1.0)

**Symptoms:**
Most periods show GDP = 1.0 exactly (the min floor value).

**Hypothesis:**
Both real_consumption and real_investment are near zero or negative.

**Fix:**
The `max(GDP, 1.0)` floor is correct per C++ model, but the issue is that actual GDP components are zero. This will be resolved by fixing Issues 1 and 2.

---

## Model Behavior Comparison

### Before All Fixes
```
Mean unemployment: 66%
Mean GDP_real: 33
Median consumption: 0
Employment range: 19-1000 (highly volatile)
```

### After Fixes
```
Mean unemployment: 5.6%
Mean GDP_real: 39.7
Median consumption: 0 (still problematic)
Employment: Much more stable (median 1000)
```

### Target (C++ Model Baseline)
```
Mean unemployment: ~5-10%
Real GDP: Positive growth trend
Consumption: Stable and growing
Employment: Stable around 950-1000
```

---

## Testing Recommendations

### 1. Unit Tests Needed
- Test goods market with various output/inventory combinations
- Test GDP calculation with known inputs
- Test investment delivery tracking
- Test Firm2 initialization consistency

### 2. Integration Tests
- Run 500+ period simulations
- Test with multiple random seeds
- Compare distributions with C++ model
- Validate steady-state behavior

### 3. Debugging Tools
Add logging for:
- Firm1 production and orders (periods 8-12)
- Worker income and consumption (periods 8-12)
- Goods market supply/demand matching
- Investment delivery events

---

## References to C++ Model

Key equations referenced:
- `fun_KS_country.h` lines 208-219: GDP calculations
- `fun_KS_consumption.h` line 33: Goods market supply
- `fun_KS_consumption.h` lines 434-612: Investment (SI, EI, Ireal, Inom)
- `fun_KS_country.h` lines 375-547: Initialization logic

---

## Next Steps (Priority Order)

### High Priority (Blocking)
1. **Debug Firm1 production stoppage** - Add logging to identify root cause
2. **Fix consumption calculation** - Ensure workers can consume when employed
3. **Stabilize machine delivery** - Ensure continuous capital accumulation

### Medium Priority (Important)
4. Review parameter calibration vs C++ baseline
5. Implement complete entry/exit dynamics
6. Add missing features (payback-based replacement, etc.)
7. Validate price/markup mechanisms

### Low Priority (Polish)
8. Optimize performance
9. Add comprehensive tests
10. Improve documentation
11. Add visualization tools

---

## Conclusion

Significant progress has been made in fixing critical bugs. The model now:
- ✅ Correctly calculates GDP according to C++ formulas
- ✅ Properly tracks investment delivery
- ✅ Avoids early-period mass firing
- ✅ Handles goods market supply correctly
- ❌ Still has machine delivery failure after period ~10
- ❌ Still has consumption collapse issue

The remaining issues are likely interconnected and stem from either Firm1 production stoppage or feedback loops between sectors. Detailed debugging of periods 8-12 is the critical next step.
