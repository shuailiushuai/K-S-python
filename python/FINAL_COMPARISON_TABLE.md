# K+S Python Model: Comprehensive Comparison and Fixes Applied

## Executive Summary

This document provides a systematic comparison between the C++ original K+S model and the Python reproduction, documenting all discrepancies found and fixes applied.

## Date: 2025-10-10

---

## Part 1: Critical Bugs Fixed

### 1. Firm1 Negative Output Bug ✅ FIXED

**File**: `python/agents/firm1.py`, method `produce()`

**Problem**: 
- When R&D workers exceeded total workers (rd_workers > labor_actual), production workers became NEGATIVE
- This caused output to become negative (e.g., -1095 in period 1)
- Formula was: `production_workers = labor_actual - rd_workers` could be < 0

**C++ Reference**: 
- `fun_KS_firm1.h`, lines 411-440, equation `_Q1e`
- Line 440: `RESULT( max( v[0], 0 ) )` ensures output is never negative
- Complex allocation logic prevents R&D from consuming all workers

**Fix Applied**:
```python
# Before:
production_workers = self.labor_actual - self.rd_workers
self.output = min(self.output, production_workers * m1)

# After:
max_rd_workers = min(self.labor_actual, 
                    self.labor_actual * L1rdMax,  # L1rdMax = 0.2 (20% max)
                    self.rd_workers)
actual_rd_workers = max(0, max_rd_workers)
production_workers = max(0, self.labor_actual - actual_rd_workers)
max_output = production_workers * self.labor_productivity_output * m1
self.output = max(0, min(self.output, max_output))
```

**Impact**: Output is now guaranteed to be non-negative.

---

### 2. Initial Labor Allocation Bug ✅ FIXED

**File**: `python/ks_model.py`, method `_assign_initial_employment()`

**Problem**:
- Initial labor allocation was arbitrary: `labor_per_firm1 = (total_workers - labor_firm2) / F1`
- Did not use the correctly calculated Ld10 and Ld20 values
- Firm1 firms got only ~10 workers each when they needed ~37 workers

**C++ Reference**:
- `fun_KS_country.h`, lines 477-491
- Lines 489-490: `Ld10 = RD0 / INIWAGE + D10 / (Btau0 * m1)` and `Ld20 = D20 / INIPROD`
- These formulas calculate the correct initial labor demands

**Fix Applied**:
```python
# Store calculated labor demands
self.params.set('Ld10', Ld10)  # Total: 742 workers
self.params.set('Ld20', Ld20)  # Total: 839 workers

# Use these in employment assignment
labor_per_firm1 = Ld10 / F1  # 742 / 20 = 37.1 workers per firm
labor_per_firm2 = Ld20 / F2  # 839 / 100 = 8.4 workers per firm
```

**Note**: Total labor demand (1581) exceeds supply (1000). This is CORRECT per C++ model - the labor market handles the shortage naturally.

**Impact**: Initial labor allocation now matches C++ formulas.

---

### 3. pK0 and pC0 Initialization ✅ ALREADY FIXED

**File**: `python/ks_model.py`, methods `_initialize_firms1()` and `_initialize_firms2()`

**Status**: VERIFIED CORRECT

**C++ Reference**:
- `fun_KS_country.h`, lines 516-517
- `WRITES(cur1, "pK0", p10)` where p10 = (1+mu1) * c10 = 20.0
- `WRITES(cur2, "pC0", p20)` where p20 = (1+mu20) * c20 = 1.35

**Python Implementation**:
```python
# Line 178 in _initialize_firms1():
self.params.set('pK0', p10)  # p10 = 20.0 ✓

# Line 234 in _initialize_firms2():
self.params.set('pC0', p20)  # p20 = 1.35 ✓
```

**Impact**: GDP calculations now use correct initial prices.

---

### 4. Firm1 R&D Labor Calculation ✅ ALREADY FIXED

**File**: `python/agents/firm1.py`, method `determine_labor_demand()`

**Status**: VERIFIED CORRECT

**C++ Reference**:
- `fun_KS_firm1.h`, lines 308-323, equation `_RD`
- Line 313: `v[1] = VL( "_S1", 1 )` - uses PAST sales (lagged)
- Line 401, equation `_L1dRD`: `RESULT( ceil( V( "_RD" ) / VLS( PARENT, "w1avg", 1 ) ) )`

**Python Implementation**:
```python
# Uses sales_history to track past sales
if hasattr(self, 'sales_history') and len(self.sales_history) > 0:
    past_sales = self.sales_history[-1]
else:
    past_sales = self.revenue

if past_sales > 0:
    rd_expenditure = nu * past_sales  # nu = 0.04
    L_rd = rd_expenditure / self.avg_wage
```

**Impact**: Firm1 maintains R&D workforce based on past performance, not current orders.

---

## Part 2: Critical Issues Remaining

### Issue 1: Model Collapse After Period 1 ❌ CRITICAL

**Symptoms**:
- Period 1: GDP=781, Unemployment=37.5%, Employment=625 workers
- Period 10: GDP=1.58, Unemployment=98.9%, Employment=11 workers
- Period 50: GDP=1.00, Unemployment=93.1%, Employment=69 workers

**Analysis**:
The model experiences rapid employment collapse, with workers being massively fired and not rehired. Possible causes:

1. **Labor Market Matching Failure**: Workers apply to firms, but matching fails
2. **Firing Too Aggressive**: Firms fire workers when labor_demand drops
3. **Expectation Formation Failure**: Firm2 demand expectations collapse, leading to zero labor demand
4. **Missing Sector-Level Labor Allocation**: C++ has sophisticated L1rd allocation (fun_KS_capital.h lines 331-378) that Python lacks

**C++ Reference - Labor Allocation**:
```c
// fun_KS_capital.h, lines 331-380, equation "L1rd"
v[0] = min( v[3], min( v[1], round( VS( LABSUPL1, "Ls" ) * V( "L1rdMax" ) ) ) );

// Distribute workers among firms
CYCLE( cur, "Firm1" ) {
    v[8] = ceil( v[7] * v[0] / v[3] );  // Proportional R&D allocation
    v[9] = round( ( v[6] - v[7] ) * ( v[1] - v[0] ) / ( v[2] - v[3] ) );  // Production workers
    // ... (complex allocation logic)
}
```

**Python Implementation**: MISSING - No sector-level labor allocation mechanism

**Recommended Fix**: Implement sector-level labor allocation logic in `labor_market.py` to match C++ model.

---

### Issue 2: Firm2 Gets No Workers ❌ CRITICAL

**Symptoms**:
- Diagnostics show Firm2 employment drops from 578 to 0 workers rapidly
- Firm1 captures most workers despite lower labor demand

**Possible Causes**:
1. **Hiring Sequence**: flagHireSeq parameter may prioritize Firm1
2. **Application Distribution**: Workers may apply more to Firm1 (larger firms)
3. **Wage Offers**: Firm2 wages may be too low to attract workers

**C++ Reference**:
- Labor market equations in `fun_KS_labor.h` and `fun_KS_capital.h` (hires1) and `fun_KS_consumption.h` (hires2)
- Separate hiring processes for each sector with different rules

**Recommended Fix**: 
1. Review and fix `match_workers_to_jobs()` in `labor_market.py`
2. Ensure Firm2 can compete for workers
3. Check flagHireSeq and flagHireOrder parameters

---

### Issue 3: Firm1 Output Stays at Zero ⚠️ MAJOR

**Symptoms**:
- After period 1, Firm1 output is consistently 0.00
- Despite having orders and some workers
- Sales occur (suggesting delivery of old stock?)

**Analysis**:
Even with the production fix, Firm1 can't produce enough to meet orders because:
- With Btau0 = 0.052 and m1 = 1.0
- 1 worker produces: 0.052 machines per period
- To produce 50 machines needs: 50 / 0.052 = 961 workers!
- But typical Firm1 has only 10-40 workers

**Possible Issues**:
1. **Btau0 too low**: Initial productivity may be incorrectly calculated
2. **Order scaling**: Orders may not account for production capacity
3. **Missing production adjustment**: C++ may adjust orders based on capacity

**C++ Reference**:
- Line 477: `Btau0 = ( 1 + mu1 ) * INIPROD / ( m1 * m2 * VS( cur2, "b" ) )`
- With parameters: (1 + 0.04) * 1.0 / (1.0 * 1.0 * 20) = 0.052 ✓ CORRECT

**Recommended Investigation**: Check order fulfillment logic in `capital_market.py`

---

## Part 3: Initialization Verification

### Initial Parameter Values (C++ vs Python)

| Parameter | C++ Value | Python Value | Formula | Status |
|-----------|-----------|--------------|---------|--------|
| Btau0 | 0.052 | 0.052 | (1+mu1)*INIPROD/(m1*m2*b) | ✅ MATCH |
| c10 | 19.23 | 19.23 | INIWAGE/(Btau0*m1) | ✅ MATCH |
| c20 | 1.00 | 1.00 | INIWAGE/INIPROD | ✅ MATCH |
| p10 (pK0) | 20.00 | 20.00 | (1+mu1)*c10 | ✅ MATCH |
| p20 (pC0) | 1.35 | 1.35 | (1+mu20)*c20 | ✅ MATCH |
| K0 | 740.74 | 740.74 | Ls0*INIWAGE/p20 | ✅ MATCH |
| D10 | 37.04 | 37.04 | K0/(m2*eta) | ✅ MATCH |
| RD0 | 29.63 | 29.63 | nu*D10*p10 | ✅ MATCH |
| Ld10 | 741.88 | 741.88 | RD0/INIWAGE + D10/(Btau0*m1) | ✅ MATCH |
| Ld20 | 838.69 | 838.69 | D20/INIPROD | ✅ MATCH |

**Conclusion**: All initialization formulas are correctly implemented and produce matching values.

---

## Part 4: Model Structure Comparison

### Agent Classes

| Agent Type | C++ Object | Python Class | Methods C++ | Methods Python | Status |
|------------|------------|--------------|-------------|----------------|--------|
| Capital Firm | Firm1 | Firm1 | 22 equations | 9 methods | ⚠️ Incomplete |
| Consumption Firm | Firm2 | Firm2 | 54 equations | 12 methods | ⚠️ Incomplete |
| Worker | Worker | Worker | 17 equations | 11 methods | ⚠️ Incomplete |
| Bank | Bank | Bank | 21 equations | 11 methods | ⚠️ Incomplete |
| Vintage | Vint | Vintage | - | - | ✅ Present |

### Market Mechanisms

| Market | C++ File | Python File | Equations C++ | Methods Python | Status |
|--------|----------|-------------|---------------|----------------|--------|
| Labor | fun_KS_labor.h | labor_market.py | 16 | 5 | ❌ Missing sector allocation |
| Capital | fun_KS_capital.h | capital_market.py | 34 | 3 | ⚠️ Incomplete |
| Goods | fun_KS_consumption.h | goods_market.py | 68 | 1 | ⚠️ Incomplete |
| Financial | fun_KS_financial.h | financial_market.py | 29 | 6 | ⚠️ Incomplete |

**Key Missing Feature**: Sector-level labor allocation mechanism (C++ `L1rd` equation)

---

## Part 5: Time Step Sequencing

### C++ Sequence (fun_KS.cpp, lines 92-129)

1. Central bank updates interest rates
2. Financial market updates rate structure
3. **Firm2**: Expectations → Production planning → Labor demand → Investment demand
4. **Capital market**: Process orders
5. **Firm1**: Production planning → Labor demand
6. **Labor market**: Firing → Worker applications → Matching → R&D allocation
7. **Production**: Firm1 and Firm2 produce with actual labor
8. **Pricing**: Set prices
9. **Government**: Expenditure
10. **Workers**: Consumption
11. **Goods market**: Matching
12. **Profits and taxes**: Calculate and pay
13. **Aggregates**: Calculate GDP, etc.
14. **Entry/Exit**: Firm dynamics
15. **Credit scores**: Update

### Python Sequence (ks_model.py, lines 430-531)

Matches C++ sequence ✅, but individual step implementations have bugs.

---

## Part 6: Critical Equations Status

| Equation | C++ Location | Python Location | Status | Issues |
|----------|--------------|-----------------|--------|--------|
| GDPreal | fun_KS_country.h:208 | utils/statistics.py | ✅ CORRECT | Uses correct pK0, pC0 |
| GDPnom | fun_KS_country.h:215 | utils/statistics.py | ✅ CORRECT | - |
| _Atau (R&D) | fun_KS_firm1.h:18 | agents/firm1.py:do_rd() | ✅ CORRECT | - |
| _L1d (labor) | fun_KS_firm1.h:389 | agents/firm1.py:determine_labor_demand() | ✅ CORRECT | - |
| _L1rd (R&D labor) | fun_KS_firm1.h:397 | agents/firm1.py:determine_labor_demand() | ✅ CORRECT | Uses past sales |
| _Q1e (output) | fun_KS_firm1.h:411 | agents/firm1.py:produce() | ✅ FIXED | Was negative, now fixed |
| L1rd (sector R&D) | fun_KS_capital.h:331 | - | ❌ MISSING | **CRITICAL MISSING** |
| entry1exit | fun_KS_capital.h:48 | ks_model.py:_handle_entry_exit() | ⚠️ Simplified | - |
| hires1 | fun_KS_capital.h:221 | labor_market.py:match_workers_to_jobs() | ⚠️ Different | - |
| hires2 | fun_KS_consumption.h:227 | labor_market.py:match_workers_to_jobs() | ⚠️ Different | - |

---

## Part 7: Recommendations

### High Priority (Blocking)

1. **Implement Sector-Level Labor Allocation** ❗
   - Add L1rd equation logic (C++ fun_KS_capital.h lines 331-380)
   - Distribute workers proportionally within each sector
   - Enforce L1rdMax limit (default 20%)

2. **Fix Labor Market Matching** ❗
   - Debug why Firm2 loses all workers
   - Check hiring sequence and priorities
   - Verify worker application distribution

3. **Review Firm2 Expectation Formation** 
   - Check if demand_expected is being calculated correctly
   - Verify adaptive expectation parameters (e0, e1-e5)

### Medium Priority

4. **Complete Capital Market Implementation**
   - Add proper order cancellation logic
   - Implement delivery constraints
   - Add supplier switching mechanism

5. **Complete Missing Equations**
   - Add all 54 Firm2 equations from C++
   - Add all 22 Firm1 equations from C++
   - Add missing labor market equations

### Low Priority

6. **Performance Optimization**
   - Consider vectorization where appropriate
   - Profile slow sections

7. **Testing and Validation**
   - Create unit tests for each subsystem
   - Run Monte Carlo simulations
   - Compare distributions with C++ model

---

## Part 8: Test Results

### Before Fixes
- Mean unemployment: 66%
- Employment: 459 workers
- GDP collapses immediately

### After Current Fixes
- Period 1: GDP=781, Unemployment=37.5%, Employment=625 ✓ Good start
- Period 10: GDP=1.58, Unemployment=98.9%, Employment=11 ❌ Collapse
- Model still unstable

### Target (C++ Model)
- Steady unemployment: 5-10%
- Stable employment: 950-1000
- Sustained GDP growth

---

## Part 9: Files Modified

### Fixed ✅
1. `python/agents/firm1.py` - produce() method
2. `python/ks_model.py` - _initialize_firms1(), _initialize_firms2(), _assign_initial_employment()

### Need Fixes ❌
1. `python/markets/labor_market.py` - Add sector allocation, fix matching
2. `python/agents/firm2.py` - Verify expectation formation
3. `python/markets/capital_market.py` - Complete implementation

---

## Conclusion

**Progress Made**:
- ✅ Fixed critical Firm1 negative output bug
- ✅ Fixed initial labor allocation formulas
- ✅ Verified pK0, pC0, Btau0 initialization is correct
- ✅ Verified Firm1 R&D labor calculation is correct

**Critical Issues Remaining**:
- ❌ Model collapses after period 1 (GDP drops from 781 to 1.58)
- ❌ Employment drops from 625 to 11 workers by period 10
- ❌ Missing sector-level labor allocation mechanism
- ❌ Firm2 loses all workers rapidly

**Next Priority**: 
1. Implement sector-level labor allocation (L1rd equation)
2. Fix labor market matching to prevent Firm2 worker loss
3. Debug expectation formation to prevent demand collapse

---

*Document Created: 2025-10-10*
*Last Updated: 2025-10-10*
