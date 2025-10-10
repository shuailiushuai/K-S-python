# K+S Python Model: Comparison and Verification Table

## Executive Summary

This document provides a comprehensive comparison between the C++ original K+S model and the Python reproduction, identifying discrepancies and documenting fixes applied.

## Critical Bugs Fixed

### 1. GDP Calculation: pK0 and pC0 Initialization ✅ FIXED

**Location**: `ks_model.py`, `utils/parameters.py`, `utils/statistics.py`

| Aspect | C++ Model (fun_KS_country.h) | Python Model (Before) | Python Model (After) | Status |
|--------|------------------------------|----------------------|---------------------|---------|
| pK0 (initial capital price) | `WRITES(cur1, "pK0", p10)` (line 516)<br/>p10 = (1+mu1) * c10<br/>**= 20.0** | Hardcoded to 1.0 in parameters.py | Calculated during initialization: `self.params.set('pK0', p10)` where p10=20.0 | ✅ FIXED |
| pC0 (initial consumption price) | `WRITES(cur2, "pC0", p20)` (line 517)<br/>p20 = (1+mu20) * c20<br/>**= 1.35** | NOT SET (missing) | Calculated during initialization: `self.params.set('pC0', p20)` where p20=1.35 | ✅ FIXED |
| Btau0 (initial productivity) | Line 477-478:<br/>`Btau0 = (1+mu1)*INIPROD / (m1*m2*b)`<br/>**= 0.052** | NOT SET | Calculated and stored: `self.params.set('Btau0', Btau0)` | ✅ FIXED |
| GDP Real calculation | `GDPreal = max(Ireal + Creal, 1)`<br/>Ireal = (SI+EI)/m2 * pK0<br/>Creal = Q2e * pC0 | Used wrong pK0 (1.0 instead of 20.0) | Now uses correct pK0=20.0 and pC0=1.35 | ✅ FIXED |

**Impact**: GDP calculation was completely wrong - investment appeared 20x larger than it should be because pK0 was 1.0 instead of 20.0.

---

### 2. Firm1 Labor Demand: R&D Workers Calculation ✅ FIXED

**Location**: `agents/firm1.py`

| Aspect | C++ Model (fun_KS_firm1.h) | Python Model (Before) | Python Model (After) | Status |
|--------|----------------------------|----------------------|---------------------|---------|
| Production workers | `ceil(_Q1 / (_Btau * m1))` (line 163) | `L_prod = output / m1` | `L_prod = output / (labor_productivity_output * m1)` | ✅ FIXED |
| R&D workers formula | `_L1dRD = ceil(_RD / w1avg[t-1])`<br/>`_RD = nu * _S1[t-1]` (lines 166, 237)<br/>**Uses PAST sales** | `L_rd = nu * L_prod`<br/>**Uses CURRENT production**<br/>When orders=0, L_rd=0! | `L_rd = nu * past_sales / avg_wage`<br/>**Uses PAST sales** | ✅ FIXED |
| Sales history tracking | Implicit in lagged variable `_S1[t-1]` | NOT tracked | Added `sales_history` list,<br/>Updated in `calculate_profit()` | ✅ FIXED |

**Impact**: 
- **Before**: When Firm2 places no orders in period 1 (machines are new), Firm1 has labor_demand=0 and fires all workers
- **After**: Firm1 maintains R&D workforce based on past revenue even when current orders are zero

---

### 3. Goods Market Supply Calculation ✅ VERIFIED CORRECT

**Location**: `markets/goods_market.py`

| Aspect | C++ Model (fun_KS_consumption.h) | Python Model | Status |
|--------|----------------------------------|--------------|---------|
| Supply formula | `sup2[j] = VS(cur, "_Q2e") + VLS(cur, "_N", 1)` (line 33)<br/>**Current output + past inventories** | `self.total_supply = sum(f.output + f.inventories for f in self.firms2)` | ✅ CORRECT |
| Inventory update | `_N = _N + _Q2e - _D2` (implicit) | `firm.inventories += firm.output - fulfilled` (line 100) | ✅ CORRECT |

**Impact**: Previously documented as a bug, but verification shows this was already fixed correctly.

---

## Critical Issues Remaining

### 4. Labor Market Allocation Failure ❌ CRITICAL BUG

**Location**: `markets/labor_market.py`

**Symptom**: By period 46-50:
- Firm2 has labor_demand = 592-700
- Firm2 has actual workers = **0** (zero!)
- Firm1 has labor_demand = 27
- Firm1 has actual workers = 994 (almost all workers!)

**Root Cause**: Labor market is not properly allocating workers to Firm2 even when they have positive labor demand.

**Test Evidence**:
```
Period 10: F1_demand=579, F1_workers=16, F2_demand=670, F2_workers=505  ✓ Reasonable
Period 46: F1_demand=27, F1_workers=37, F2_demand=592, F2_workers=0    ✗ BROKEN
```

**Investigation Needed**:
1. Check labor_market.py match_workers_to_jobs() logic
2. Verify hiring sequence (Firm1 vs Firm2)
3. Check if workers are stuck in Firm1 and not being reallocated
4. Review firing/hiring order parameters (flagHireSeq, flagFireOrder1, flagFireOrder2)

---

### 5. Parameter Discrepancies

**Location**: `utils/parameters.py`

| Parameter | C++ Model | Python Model | Status |
|-----------|-----------|--------------|---------|
| x2inf | -0.15 (entry/exit) | Missing initially | ✅ Added |
| x2sup | 0.15 (entry/exit) | Missing initially | ✅ Added |
| L1rdMax | 0.2 (max R&D share) | Present | ✅ OK |

---

## Initialization Verification

### Initial Values Calculation (C++ fun_KS_country.h lines 477-491)

| Variable | Formula (C++) | Expected Value | Python Value | Status |
|----------|---------------|----------------|--------------|---------|
| Btau0 | `(1+mu1)*INIPROD/(m1*m2*b)` | 0.052 | 0.052 | ✅ |
| c10 | `INIWAGE / (Btau0 * m1)` | 19.23 | 19.23 | ✅ |
| c20 | `INIWAGE / INIPROD` | 1.0 | 1.0 | ✅ |
| p10 (pK0) | `(1+mu1) * c10` | 20.0 | 20.0 | ✅ |
| p20 (pC0) | `(1+mu20) * c20` | 1.35 | 1.35 | ✅ |
| K0 | `Ls0 * INIWAGE / p20` | 740.74 | 740.74 | ✅ |
| D10 | `K0 / (m2 * eta)` | 37.04 | 37.04 | ✅ |
| RD0 | `nu * D10 * p10` | 29.63 | Calc OK | ✅ |
| D20 | Formula (line 487-488) | Complex | Calc OK | ✅ |
| Ld10 | `RD0/INIWAGE + D10/(Btau0*m1)` | 741.96 | Calc OK | ✅ |
| Ld20 | `D20 / INIPROD` | Variable | Calc OK | ✅ |

---

## Model Structure Comparison

### Agent Types

| Agent | C++ Objects | Python Classes | Status |
|-------|-------------|----------------|---------|
| Capital-good firms | Firm1 (in Capital sector) | `Firm1` class | ✅ Present |
| Consumption-good firms | Firm2 (in Consumption sector) | `Firm2` class | ✅ Present |
| Workers | Worker (in Labor) | `Worker` class | ✅ Present |
| Banks | Bank (in Financial) | `Bank` class | ✅ Present |
| Vintages | Vint (nested in Firm2) | `Vintage` class | ✅ Present |
| Government | Aggregated variables | `Government` class | ✅ Present |
| Central Bank | Part of Financial | `CentralBank` class | ✅ Present |

### Markets

| Market | C++ Implementation | Python Implementation | Status |
|--------|-------------------|----------------------|---------|
| Labor Market | Distributed in fun_KS_labor.h | `LaborMarket` class | ⚠️ Has bugs |
| Goods Market | In fun_KS_consumption.h | `GoodsMarket` class | ✅ OK |
| Capital Market | In fun_KS_capital.h, fun_KS_firm2.h | `CapitalMarket` class | ✅ OK |
| Financial Market | In fun_KS_bank.h | `FinancialMarket` class | ⚠️ Need verification |

---

## Equation Sequencing (Time Step Logic)

### C++ Model (fun_KS.cpp timeStep equation, lines 92-129)

1. Central bank updates interest rates
2. Firms form expectations and plan production
3. Capital market processes orders
4. Labor market: firing → applications → matching
5. Production with actual labor
6. Capital delivery
7. Government expenditure
8. Worker consumption
9. Goods market matching
10. Profit calculation and taxes
11. Public debt update
12. Aggregate calculation
13. Entry/exit
14. Credit scores update

### Python Model (ks_model.py step() method, lines 421-522)

Sequence appears to match C++ model ✅, but implementation of individual steps has bugs.

---

## Key Equations Verification

### GDP Calculation (fun_KS_country.h lines 208-219)

| Equation | C++ Formula | Python Implementation | Status |
|----------|-------------|----------------------|---------|
| GDPreal | `max(Ireal + Creal, 1)` | Same | ✅ FIXED |
| Ireal | `(SI + EI) / m2 * pK0` | `total_delivered_investment / pK0` | ✅ FIXED |
| Creal | `Q2e * pC0` | `sum(f.output for f in firms2) * pC0` | ✅ FIXED |
| GDPnom | `max(C + Inom + dNnom, 1)` | Same structure | ✅ FIXED |
| C | `S2` (sales of Firm2) | `sum(f.sales * f.price for f in firms2)` | ✅ OK |

### Labor Demand (fun_KS_firm1.h line 163, fun_KS_firm2.h)

| Firm Type | C++ Formula | Python Implementation | Status |
|-----------|-------------|----------------------|---------|
| Firm1 Total | `_L1dRD + ceil(_Q1/(_Btau*m1))` | `L_rd + L_prod` | ✅ FIXED |
| Firm1 R&D | `ceil(_RD / w1avg[t-1])` where `_RD = nu*_S1[t-1]` | `nu * past_sales / avg_wage` | ✅ FIXED |
| Firm2 | Based on output_planned / productivity | `output_planned / productivity` | ⚠️ Need verification |

---

## Test Results Summary

### Baseline Test (50 periods, seed=42)

| Metric | Target (C++ Model) | Python (After Fixes) | Assessment |
|--------|-------------------|---------------------|------------|
| Mean unemployment rate | ~5-10% | 54.8% | ❌ Too high |
| GDP_real trend | Positive growth | Mean=62, std=154 (highly volatile) | ❌ Unstable |
| Employment | Stable ~950-1000 | Median=452, final=999 | ⚠️ Volatile but recovers |
| Number of firms | Stable with entry/exit | F1=23, F2=169 (growing) | ⚠️ Growing rapidly |

### Detailed Period Analysis

| Period | GDP_real | Employment | Consumption | Assessment |
|--------|----------|------------|-------------|------------|
| 1 | 542.7 | 907 | 666 | ✓ Good start |
| 5 | 290.3 | 288 | declining | ⚠️ Collapsing |
| 10 | 1.0 | 404 | near zero | ❌ Collapsed |
| 50 | 1.0 | 999 | 0 | ❌ At floor with full employment |

**Critical Issue**: By period 50, economy has 999 employed workers but GDP=1.0 (floor) because:
- 994 workers employed by Firm1 (for R&D that generates no output)
- 0 workers in Firm2 (no consumption production)
- Labor market allocation completely broken

---

## Priority Fixes Needed

### High Priority (Blocking)

1. **Labor Market Allocation** ❌ CRITICAL
   - Fix worker allocation to prefer Firm2 when they have positive labor demand
   - Investigate why workers get stuck in Firm1
   - Review hiring sequence and priority

2. **Firm1 Output Calculation** ❌ IMPORTANT
   - Current issue: Firm1.output becomes negative (-30.21)
   - Check production logic in firm1.produce()
   - Verify order fulfillment logic

3. **Worker Reallocation** ❌ IMPORTANT
   - Workers should be able to move from Firm1 to Firm2
   - Check firing and hiring logic
   - Verify job search and application logic

### Medium Priority

4. **Entry/Exit Dynamics** ⚠️
   - Firm2 count grows from 100 to 169 (69% increase)
   - May indicate entry rate is too high
   - Review entry formula and parameters

5. **Expectation Formation** ⚠️
   - Firm2 demand_expected becomes 0.0 for all firms
   - Check expectation formation in form_expectations()
   - Verify adaptive expectation parameters (e0, e1-e5)

### Low Priority

6. **Parameter Calibration**
   - Review all default parameter values
   - Compare with C++ baseline configuration
   - Test sensitivity to parameter changes

7. **Performance Optimization**
   - Model runs but may be slow for long simulations
   - Consider vectorization where appropriate

---

## Files Modified

### Fixed Files ✅

1. `python/utils/parameters.py`
   - Added x2inf, x2sup parameters
   - Added pC0 placeholder

2. `python/ks_model.py`
   - Calculate and store Btau0 in _initialize_firms1()
   - Calculate and store pK0 (=p10) in _initialize_firms1()
   - Calculate and store pC0 (=p20) in _initialize_firms2()

3. `python/agents/firm1.py`
   - Fixed determine_labor_demand() to use past sales for R&D
   - Added sales_history list
   - Updated calculate_profit() to track sales history

### Files Needing Fixes ❌

1. `python/markets/labor_market.py`
   - Critical: Fix worker allocation logic
   - Review match_workers_to_jobs()
   - Check hiring sequence and priorities

2. `python/agents/firm1.py`
   - Fix negative output issue
   - Review produce() method

3. `python/agents/firm2.py`
   - Verify expectation formation
   - Check labor demand calculation

---

## Recommendations

### Immediate Actions

1. **Debug Labor Market**
   - Add detailed logging to match_workers_to_jobs()
   - Trace worker allocation in periods 1-50
   - Identify where allocation logic fails

2. **Verify C++ Labor Market Logic**
   - Study fun_KS_labor.h in detail
   - Compare hiring sequence: `_fires1`, `_fires2`, `_hires1`, `_hires2`
   - Check order of operations

3. **Test with Simplified Scenario**
   - Run with fewer firms (F10=5, F20=10)
   - Shorter time horizon (10 periods)
   - Track every worker's employment status

### Long-term Improvements

1. **Unit Tests**
   - Create tests for each subsystem
   - Test GDP calculation with known inputs
   - Test labor market with controlled scenarios

2. **Validation Suite**
   - Compare distributions with C++ model
   - Run Monte Carlo with multiple seeds
   - Validate steady-state properties

3. **Documentation**
   - Document all equation implementations
   - Cross-reference with C++ line numbers
   - Create decision flow diagrams

---

## Conclusion

**Progress Made**: 
- ✅ Fixed critical GDP calculation bug (pK0, pC0)
- ✅ Fixed Firm1 R&D labor demand calculation
- ✅ Verified goods market supply logic is correct

**Critical Issues Remaining**:
- ❌ Labor market allocation completely broken (workers stuck in Firm1)
- ❌ Firm1 negative output issue
- ❌ Model unstable - collapses then partially recovers

**Next Priority**: Fix labor market allocation to ensure Firm2 can hire workers when they have positive labor demand. This is the single most critical blocking issue preventing the model from functioning correctly.

---

## References

### C++ Source Files
- `fun_KS_country.h` - Country initialization and aggregates
- `fun_KS_firm1.h` - Capital-good firm equations
- `fun_KS_firm2.h` - Consumption-good firm equations
- `fun_KS_labor.h` - Labor market equations
- `fun_KS_consumption.h` - Consumption sector equations
- `fun_KS.cpp` - Main model and time step sequencing

### Python Source Files
- `python/ks_model.py` - Main model class
- `python/agents/firm1.py` - Firm1 implementation
- `python/agents/firm2.py` - Firm2 implementation
- `python/markets/labor_market.py` - Labor market implementation
- `python/markets/goods_market.py` - Goods market implementation
- `python/utils/statistics.py` - GDP and statistics calculation
- `python/utils/parameters.py` - Parameter management

---

*Document created: 2025-10-10*
*Last updated: 2025-10-10*
