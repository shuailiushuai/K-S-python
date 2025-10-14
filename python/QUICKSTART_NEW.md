# K+S Model - Quick Start Guide

## Installation

```bash
cd python
pip install -r requirements.txt
```

## Quick Run

```bash
python run_example.py
```

This runs a scaled-down simulation (100 workers, 5+10 firms) for 20 periods.

## Basic Usage

```python
from model import KSModel

# Initialize with config
model = KSModel('config/model_config.yaml', seed=1)

# Run simulation
results = model.run(periods=100)

# View results
print(f"GDP: ${results['GDP'][-1]:.2f}")
print(f"Unemployment: {results['unemployment'][-1]:.1%}")
```

## Model Complete!

✅ All markets operational (labor, goods, capital)
✅ Government & central bank functional
✅ 18-stage time-step sequence
✅ ~3,500 lines of Python code

See README.md for full documentation.
