# K+S Model Simulation Bug Analysis and Fixes
# K+S模型仿真程序错误分析和修复

**Date**: 2025-10-13  
**Issue**: Simulation produces constant values with no dynamics

## Problem Statement / 问题描述

The simulation report showed completely static values across all periods:
- GDP (real): 80.00 (constant for all 100 periods)
- GDP (nominal): 80.00 → 1.00 (wrong value)
- Unemployment: 0.00% (constant)
- All profits: $0.00
- All sales: $0.00
- All government variables: $0.00
- No dynamics, no growth, no fluctuations

仿真报告显示所有周期的值完全静态：
- 实际GDP：80.00（所有100个周期都不变）
- 名义GDP：80.00 → 1.00（错误值）
- 失业率：0.00%（不变）
- 所有利润：$0.00
- 所有销售：$0.00
- 所有政府变量：$0.00
- 无动态、无增长、无波动

## Root Cause Analysis / 根本原因分析

Through systematic debugging, three critical bugs were identified that completely prevented the model from functioning:

### Bug 1: Wage-Consumption Circular Dependency / 工资-消费循环依赖

**Location**: `country.py::time_step()`

**Problem**: The time step sequence had wages computed AFTER consumption demand:
```
6. _consumption_and_sales() 
   └─> _compute_desired_consumption() [needs W (wages)]
7. _financial_operations() 
   └─> computes labor._W [sets wages]
```

This created a chicken-and-egg problem:
- Period 1: Cd uses W from period 0 (which is 0) → Cd = 0
- No demand → no sales → GDP incorrect

问题：时间步序列在消费需求之后计算工资，造成鸡生蛋蛋生鸡的问题。

**Evidence**:
```python
# Before fix:
W (wages): 1000.0
Cd (desired consumption): 0.0  # Should be 1000!
```

**Fix**: Created `_compute_wages()` method and moved it BEFORE `_consumption_and_sales()`:
```python
def time_step(self):
    ...
    self._production_and_pricing()
    self._compute_wages()              # NEW: Compute wages first
    self._consumption_and_sales()       # Then use wages in demand
    self._financial_operations()
    ...
```

**Result**: 
```python
# After fix:
W (wages): 1000.0
Cd (desired consumption): 1000.0  # ✓ Correct!
```

### Bug 2: Zero Market Shares / 市场份额为零

**Location**: `country.py::_initialize_consumption_sector()`

**Problem**: Market shares (_f2) were never initialized for consumption firms. All firms had `_f2 = 0.0`.

The demand allocation algorithm checks:
```python
if f2[j] > 0:  # This condition was ALWAYS FALSE!
    # Allocate demand...
```

Since all f2 = 0, no demand was ever allocated to any firm, resulting in:
- Zero sales (S2 = 0)
- Zero demand fulfilled (D2 = 0)
- Incorrect GDP

问题：消费品公司的市场份额（_f2）从未初始化，所有公司的_f2 = 0.0，导致需求分配算法永远不会分配需求。

**Evidence**:
```python
# Before fix:
Firm 0: f2=0.0, p2=1.2, Q2e=2.0, D2=0.0, S2=0.0
```

**Fix**: Initialize market shares equally for all firms:
```python
def _initialize_consumption_sector(self):
    F20 = int(sector._F20)
    initial_market_share = 1.0 / F20 if F20 > 0 else 0.0
    
    for i in range(F20):
        firm = Firm2(...)
        firm._f2 = initial_market_share  # NEW: Equal market share
```

**Result**:
```python
# After fix:
Firm 0: f2=0.02, p2=1.2, Q2e=2.0, D2=2.0, S2=2.4  # ✓ Non-zero!
```

### Bug 3: Firm Labor Count Not Tracked / 公司劳动力数量未追踪

**Location**: `country.py::_production_and_pricing()`

**Problem**: Workers were assigned to firms in `_labor_market_matching()`, but the firm's labor count variable (`_L2`) was never updated. When computing wages:

```python
def compute_total_wages(self):
    L2 = self.read("_L2")      # Returns 0!
    w2avg = self.read("_w2avg") # Returns 0!
    W2 = L2 * w2avg            # Always 0!
```

This resulted in:
- Zero wage costs (W2 = 0)
- Zero profits (Pi2 = S2 - W2 = 0 because S2 was also 0)

问题：工人被分配给公司后，公司的劳动力数量变量（_L2）从未更新，导致工资计算为零。

**Evidence**:
```python
# Before fix:
Actual workers in firm: 2
L2 (from variable): 0        # Not updated!
W2 (wages): 0.0              # Wrong!
Pi2 (profit): 0.0            # Wrong!
```

**Fix**: Update firm labor variables during production and write to lag storage:
```python
def _production_and_pricing(self):
    for firm in con_sector.firms:
        workers_in_firm = sum(1 for w in self.workers 
                             if w._employed == 2 and w._employer == firm)
        firm._L2 = workers_in_firm
        firm.write("_L2", workers_in_firm)  # NEW: Write to storage
        
        # Compute average wage
        if workers_in_firm > 0:
            wages = [w._wReal for w in self.workers 
                    if w._employed == 2 and w._employer == firm]
            firm._w2avg = sum(wages) / len(wages)
        firm.write("_w2avg", firm._w2avg)  # NEW: Write to storage
```

Also added write call for sales:
```python
for firm in con_sector.firms:
    firm._S2 = firm._p2 * firm._D2
    firm.write("_S2", firm._S2)  # NEW: Write to storage
```

**Result**:
```python
# After fix:
L2 (workers): 2
W2 (wages): 2.00             # ✓ Correct!
Pi2 (profit): -2.00          # ✓ Non-zero!
```

## Summary of Changes / 更改总结

### Files Modified:
- `python/model/country.py`

### Methods Changed:
1. `time_step()` - Added `_compute_wages()` call before `_consumption_and_sales()`
2. `_compute_wages()` - NEW method to compute wages before consumption demand
3. `_production_and_pricing()` - Added firm labor tracking and write() calls
4. `_consumption_and_sales()` - Added write() call for sales
5. `_initialize_consumption_sector()` - Initialize market shares
6. `_financial_operations()` - Removed duplicate wage computation

### Lines Changed: ~70

## Before and After Comparison / 修复前后对比

| Metric | Before | After | Status |
|--------|--------|-------|--------|
| Wages (W) | 1000.0 | 1000.0 | ✓ |
| Desired Consumption (Cd) | 0.0 | 1000.0 | ✓ Fixed |
| Sales (S2) | 0.0 | 96.0 | ✓ Fixed |
| Demand Fulfilled (D2) | 0.0 | 80.0 | ✓ Fixed |
| Nominal GDP | 1.0 | 96.0 | ✓ Fixed |
| Sector Profits | 0.0 | -0.65 | ✓ Fixed |
| Debt/GDP Ratio | 0.0% | -3.3% → -46.3% | ✓ Dynamic |
| Average Wage Growth | No | $1.09 → $1.21 | ✓ Dynamic |

## Simulation Results / 仿真结果

### Before Fixes (原始结果):
```
Period   GDP(real)    GDP(nom)     Unemp%     Debt/GDP%
1        80.00        1.00         0.00       0.00
2        80.00        80.00        0.00       0.00
...
100      80.00        80.00        0.00       0.00

Sales: $0.00
Profits: $0.00
```

### After Fixes (修复后):
```
Period   GDP(real)    GDP(nom)     Unemp%     Debt/GDP%
1        80.00        96.00        0.00       -3.33
2        80.00        96.00        0.00       -6.58
...
20       80.00        96.00        0.00       -46.26

Sales: $96.00
Profits: $-0.65
Average Wage: $1.09 → $1.21
```

## Model Status / 模型状态

### ✅ Fixed Issues:
1. Wage computation timing
2. Market share initialization
3. Firm labor tracking
4. Sales and wage variable storage
5. Demand allocation functioning
6. Profit calculation working
7. GDP calculation correct
8. Some dynamics appearing (wage growth, debt changes)

### ⚠️ Remaining Issues:
1. GDP still constant (no growth)
2. Unemployment always 0% (full employment assumed)
3. Profits negative (pricing needs adjustment)
4. Government debt negative (accounting error)
5. No market competition or dynamics
6. No business cycles
7. No productivity growth mechanism

## Recommendations / 建议

### High Priority:
1. **Fix pricing mechanism** to ensure average profits > 0
2. **Add unemployment** by making labor matching less than perfect
3. **Implement market share dynamics** based on firm competitiveness
4. **Fix government accounting** to prevent negative debt

### Medium Priority:
5. Add productivity growth (innovation, R&D effects)
6. Implement firm entry/exit based on profitability
7. Add inventory dynamics for price adjustment
8. Implement proper business cycle mechanisms

### Low Priority:
9. Add heterogeneous worker skills
10. Implement credit constraints
11. Add financial sector dynamics
12. Implement policy shocks and regime changes

## Testing / 测试

To verify the fixes:
```bash
cd /home/runner/work/K-S-python/K-S-python/python
python run_simulation.py --periods 20
```

Expected behavior:
- Sales > 0
- Profits ≠ 0
- Nominal GDP ≈ 96
- Some variables changing over time

## Conclusion / 结论

The three critical bugs prevented any economic activity in the model:
1. No consumption demand (Cd = 0) due to wage timing
2. No demand allocation due to zero market shares
3. No wage costs due to labor count not tracked

All three are now fixed, and the model shows basic functioning. However, significant work remains to implement proper economic dynamics, growth mechanisms, and realistic market behavior.

这三个关键错误阻止了模型中的任何经济活动。现已全部修复，模型显示基本功能。但仍需大量工作来实现适当的经济动态、增长机制和现实的市场行为。
