# K+S Model Configuration Comparison

## LSD to YAML Conversion Summary

This document describes the 10 configuration files converted from LSD format to YAML format.

## Converted Files

| LSD File | YAML File | Purpose |
|----------|-----------|----------|
| Cent_wage-Baseline_v2.lsd | cent_wage_baseline_v2.yaml | Centralized wage, baseline configuration (v2) |
| Cent_wage-Benchmark_v1.lsd | cent_wage_benchmark_v1.yaml | Centralized wage, benchmark configuration (v1) |
| No_skills-Fix_entry-No_fin.lsd | no_skills_fix_entry_no_fin.yaml | No skills, fixed entry, minimal finance |
| Sim1.lsd | sim1.yaml | Simulation scenario 1 |
| Sim2.lsd | sim2.yaml | Simulation scenario 2 |
| Ten_skills-Free_entry-Bas_fin.lsd | ten_skills_free_entry_bas_fin.yaml | Ten skills, free entry, basic finance |
| Ten_skills-Free_entry-Full_fin.lsd | ten_skills_free_entry_full_fin.yaml | Ten skills, free entry, full finance |
| Ten_skills-Free_entry-No_fin.lsd | ten_skills_free_entry_no_fin.yaml | Ten skills, free entry, no finance |
| sa-ee.lsd | sa_ee.yaml | Sensitivity analysis - Elementary Effects |
| sa-sobol.lsd | sa_sobol.yaml | Sensitivity analysis - Sobol indices |

## Key Differences Between Configurations

### 1. Wage Mechanism
- **Centralized**: All firms offer same wage based on economy-wide conditions
- **Decentralized**: Firms set individual wages based on local conditions

### 2. Skills System
- **No skills**: All workers have identical productivity
- **Ten skills**: Workers differentiated by skill levels (10 categories)

### 3. Entry/Exit Dynamics
- **Fixed entry**: Number of firms remains constant
- **Free entry**: Firms can enter/exit based on profitability

### 4. Financial System
- **No finance**: Minimal banking (1 bank, fixed rates)
- **Basic finance**: Multiple banks with credit constraints
- **Full finance**: Complete banking system with Basel rules

## YAML Format Benefits

1. **Human-readable**: Easy to understand and edit
2. **Version control friendly**: Clean diffs in git
3. **Standard format**: Works with many tools and languages
4. **Type-safe**: Clear data types (numbers, strings, lists)
5. **Hierarchical**: Natural representation of model structure
6. **Comments**: Full support for documentation inline

## Usage

```python
import yaml
from pathlib import Path

# Load a configuration
with open('configs/baseline.yaml') as f:
    config = yaml.safe_load(f)

# Access parameters
periods = config['simulation']['periods']
tax_rate = config['country']['tr']
```
