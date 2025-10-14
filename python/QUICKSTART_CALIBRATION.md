# Quick Start Guide for K+S Model Parameter Calibration

This guide helps you get started with parameter calibration for the K+S model after all critical bugs have been fixed.

## Installation

```bash
cd python
pip install -r requirements.txt
```

## Step 1: Verify Model Works

Run the extended validation test to confirm the model is operational:

```bash
python test_extended_validation.py --periods 50 --seed 42
```

**Expected output:**
```
✓ Completed all 50 periods without crashes
✓ Mean employment: ~50-60%
✓ GDP remains finite and reasonable
```

This confirms all critical bugs are fixed and core dynamics work correctly.

## Step 2: Understand Current Behavior

The model runs stably but shows elevated unemployment (~50%). This is a **parameter calibration issue**, not a bug.

Key observations:
- Initial employment: 90%
- Stabilizes at: ~50%
- GDP: Fluctuates but remains positive
- No crashes or explosions

## Step 3: Parameter Sensitivity Analysis

### Test Demand Expectations

```bash
python parameter_tuning_tool.py --preset demand --periods 100
```

This tests the `Consumption.e0` parameter (animal spirits) with values: 0.3, 0.5, 0.7, 0.9, 1.0

**What to look for:**
- Higher employment with lower `e0` values?
- Stability across all values?
- GDP patterns

### Test Wage Adjustment

```bash
python parameter_tuning_tool.py --preset wage --periods 100
```

This tests the `Labor.psi3` parameter (wage-unemployment elasticity) with values: -0.1, -0.3, -0.5, -0.7

**What to look for:**
- Better employment with more negative `psi3`?
- Wage-unemployment feedback
- Market clearing

### Test Production Capacity

```bash
python parameter_tuning_tool.py --preset production --periods 100
```

This tests the `Consumption.u` parameter (target capacity utilization) with values: 0.7, 0.8, 0.9, 0.95

**What to look for:**
- Higher employment with higher `u`?
- Production constraints
- Capital utilization

### Custom Parameter Tests

```bash
# Test any parameter
python parameter_tuning_tool.py \
  --param Consumption.chi \
  --values 0.5,1.0,1.5,2.0 \
  --periods 100 \
  --seed 42
```

## Step 4: Interpret Results

### Good Signs (Model Working Correctly)
- ✓ All simulations complete without crashes
- ✓ GDP remains finite (no NaN/Inf)
- ✓ Employment responds to parameter changes
- ✓ Market shares sum to 1.0

### Parameter Calibration Goals
- Target employment: 70-90%
- Target GDP growth: 2-4% per period
- Target inflation: 1-3% per period
- Stable dynamics (no explosions)

### Example Output Interpretation

```
Value           Mean Emp.       Final Emp.      Mean GDP        Status
-------------------------------------------------------------------------------
0.3             65.2%           68.0%           $52.31          ✓ OK
0.5             58.1%           55.0%           $48.22          ✓ OK
0.7             52.3%           50.0%           $45.18          ✓ OK
1.0             48.9%           48.0%           $42.05          ✓ OK

Best value for employment: Consumption.e0 = 0.3
```

**Interpretation:** Lower `e0` (0.3) gives higher employment → firms plan more optimistically.

## Step 5: Multi-Parameter Optimization

Once you identify promising individual parameters, test combinations:

```python
from parameter_tuning_tool import test_multiple_parameters

param_configs = [
    {'Consumption.e0': 0.3, 'Labor.psi3': -0.5},
    {'Consumption.e0': 0.3, 'Labor.psi3': -0.7},
    {'Consumption.e0': 0.5, 'Consumption.u': 0.9},
    # Add more combinations
]

results = test_multiple_parameters(param_configs, periods=100, seed=42)
```

## Step 6: Extended Validation

Once you find good parameters, validate extensively:

```bash
# Long simulation
python test_extended_validation.py --periods 200 --seed 42

# Multiple seeds
python test_extended_validation.py --periods 100 --seed 123
python test_extended_validation.py --periods 100 --seed 456
python test_extended_validation.py --periods 100 --seed 789
```

## Step 7: Document Your Findings

Create a calibration report:

```markdown
# Parameter Calibration Results

## Objective
Achieve 70-90% employment with stable GDP growth

## Parameters Tested
- Consumption.e0: Animal spirits weight
- Labor.psi3: Wage-unemployment elasticity
- Consumption.u: Capacity utilization

## Best Configuration
- Consumption.e0 = 0.3
- Labor.psi3 = -0.5
- Consumption.u = 0.9

## Results
- Mean employment: 75.2%
- Mean GDP: $58.40
- Stability: 200 periods without issues

## Validation
Tested with 5 random seeds, all show similar behavior.
```

## Common Parameters to Tune

### Demand & Production
- `Consumption.e0`: Animal spirits (0-1)
- `Consumption.e1`, `e2`, `e3`: Expectation weights
- `Consumption.u`: Target capacity utilization (0-1)
- `Consumption.chi`: Investment sensitivity (>0)

### Labor & Wages
- `Labor.psi1`: Inflation adjustment (0-1)
- `Labor.psi2`: Productivity adjustment (0-1)
- `Labor.psi3`: Unemployment adjustment (<0)
- `Labor.psi4`: Firm productivity adjustment (≥0)
- `Labor.psi5`: Vacancy adjustment (≥0)
- `Labor.phi`: Unemployment benefit ratio (0-1)

### Market Dynamics
- `Consumption.omega1`: Price competitiveness weight
- `Consumption.omega2`: Unfilled demand weight
- `Consumption.omega3`: Quality competitiveness weight
- `Consumption.upsilon`: Markup adjustment speed

### Government & Finance
- `Country.tr`: Tax rate
- `Financial.rT`: Prime rate target
- `Financial.phi_pi`: Inflation weight in Taylor rule
- `Financial.phi_u`: Unemployment weight in Taylor rule

## Troubleshooting

### Simulations Crash
- Check that parameters are in valid ranges
- Review error messages
- Start with default parameters and change one at a time

### Employment Too Low
- Decrease `Consumption.e0` (more optimistic expectations)
- Increase magnitude of `Labor.psi3` (wages adjust faster)
- Increase `Consumption.u` (higher capacity utilization)
- Increase `Consumption.chi` (more aggressive investment)

### Employment Too High (>95%)
- Increase `Consumption.e0` (more conservative expectations)
- Decrease magnitude of `Labor.psi3` (wages adjust slower)
- Decrease `Consumption.u` (lower capacity utilization)

### GDP Volatility
- Adjust expectation formation (`e0`, `e1`, `e2`, `e3`)
- Tune markup adjustment (`upsilon`)
- Review fiscal policy (`tr`, `phi`)

### Inflation Issues
- Adjust Taylor rule parameters (`phi_pi`, `phi_u`)
- Review markup dynamics (`mu20`, `upsilon`)
- Check wage adjustment parameters

## Advanced Topics

### Latin Hypercube Sampling
Use scipy to sample parameter space efficiently:

```python
from scipy.stats import qmc

# Define parameter ranges
ranges = {
    'Consumption.e0': (0.2, 1.0),
    'Labor.psi3': (-0.7, -0.1),
    'Consumption.u': (0.7, 0.95),
}

# Generate samples
sampler = qmc.LatinHypercube(d=len(ranges))
samples = sampler.random(n=100)

# Scale to ranges
param_configs = []
for sample in samples:
    config = {}
    for i, (param, (low, high)) in enumerate(ranges.items()):
        config[param] = low + sample[i] * (high - low)
    param_configs.append(config)

# Test all configurations
results = test_multiple_parameters(param_configs, periods=100)
```

### Machine Learning for Optimization
Use scikit-learn to identify promising regions:

```python
from sklearn.ensemble import RandomForestRegressor

# Fit model to predict employment from parameters
X = [list(r['params'].values()) for r in results]
y = [r['employment_mean'] for r in results]

model = RandomForestRegressor()
model.fit(X, y)

# Find best parameters
best_idx = model.predict(X).argmax()
best_params = results[best_idx]['params']
```

## Getting Help

- Review documentation in `MODEL_READINESS_REPORT.md`
- Check existing issues on GitHub
- Compare with C++ implementation if available
- Use debug scripts (`test_*_debug.py`) to trace behavior

## Summary

1. ✅ Verify model works with `test_extended_validation.py`
2. 🔬 Test individual parameters with `parameter_tuning_tool.py`
3. 🎯 Identify promising parameter values
4. 🔄 Test parameter combinations
5. 📊 Validate extensively with multiple seeds
6. 📝 Document your calibrated parameters

**The model is working correctly - calibration is a research task to find parameter values that match your target behavior.**
