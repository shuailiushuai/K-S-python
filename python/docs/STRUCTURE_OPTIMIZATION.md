# K+S Model Directory Structure Optimization

## Current Structure Analysis

```
python/
├── configs/              # ✅ Good - Configuration files
├── model/                # ✅ Good - Core model components
│   ├── agents/          # Could organize better
│   └── utils/           # Could organize better
├── examples/            # ❌ Scattered - example_*.py files in root
├── tests/               # ❌ Scattered - test_*.py files in root
├── tools/               # ❌ Mixed - utility scripts
└── docs/                # ❌ Scattered - *.md files in root
```

## Current Issues

1. **Example files scattered** - example_*.py files in root directory
2. **Test files scattered** - test_*.py files in root directory  
3. **Documentation scattered** - Multiple .md files in root
4. **Utility scripts mixed** - convert_lsd_to_yaml.py, verify_completeness.py in root
5. **Model files could be better organized** - All agents in single model/ dir

## Proposed Optimized Structure

```
python/
├── ks_model/                    # Main package (renamed from 'model')
│   ├── __init__.py
│   ├── agents/                  # Agent implementations
│   │   ├── __init__.py
│   │   ├── base.py             # Base Agent class (from agent.py)
│   │   ├── worker.py           # Worker agent
│   │   ├── firm1.py            # Capital goods firm
│   │   ├── firm2.py            # Consumption goods firm
│   │   ├── bank.py             # Bank agent
│   │   └── vintage.py          # Vintage machine
│   ├── sectors/                 # Sector containers
│   │   ├── __init__.py
│   │   ├── capital.py          # Capital sector (from country.py)
│   │   ├── consumption.py      # Consumption sector (from country.py)
│   │   ├── financial.py        # Financial sector (from country.py)
│   │   └── labor.py            # Labor market
│   ├── core/                    # Core model components
│   │   ├── __init__.py
│   │   ├── country.py          # Country orchestrator
│   │   ├── statistics.py       # Statistics collector
│   │   └── entry_exit.py       # Entry/exit dynamics
│   ├── utils/                   # Utility modules
│   │   ├── __init__.py
│   │   ├── constants.py        # Model constants
│   │   ├── data_structures.py  # Data structures
│   │   ├── random_engine.py    # Random number generation
│   │   └── support.py          # Support functions
│   └── config.py               # Configuration loading (from ../config.py)
│
├── configs/                     # Configuration files (YAML)
│   ├── baseline.yaml
│   ├── cent_wage_baseline_v2.yaml
│   └── ... (other configs)
│
├── examples/                    # Example usage scripts
│   ├── __init__.py
│   ├── basic_simulation.py     # (from example_simulation.py)
│   ├── agent_examples.py       # Combine example_*.py files
│   └── scenarios.py            # (from example_scenarios.py)
│
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── test_integration.py
│   ├── test_validation.py
│   ├── test_stock_flow.py      # (from test_stock_flow_consistency.py)
│   ├── test_entry_exit.py
│   └── test_complete.py        # (from test_complete_model.py)
│
├── tools/                       # Utility tools
│   ├── convert_configs.py      # (from convert_lsd_to_yaml.py)
│   └── verify.py               # (from verify_completeness.py)
│
├── docs/                        # Documentation
│   ├── README.md               # Main documentation
│   ├── QUICKSTART.md
│   ├── SIMULATION_GUIDE.md
│   ├── CONFIG_COMPARISON.md
│   └── ... (other docs)
│
├── run_simulation.py           # Main CLI entry point (stays in root)
├── setup.py                    # Package setup (new)
├── requirements.txt            # Dependencies
└── README.md                   # Quick overview with links to docs/
```

## Benefits of New Structure

### 1. Better Organization
- **Clear separation**: agents, sectors, core, utils
- **Logical grouping**: Related files together
- **Easier navigation**: Find what you need quickly

### 2. Professional Package Structure
- Standard Python package layout
- Can be installed with `pip install -e .`
- Importable as `from ks_model import Country`

### 3. Cleaner Root Directory
- Only essential files in root
- Examples, tests, tools in subdirectories
- Documentation in dedicated folder

### 4. Better Maintainability
- Clear responsibilities for each module
- Easier to understand code organization
- Simpler to add new features

### 5. Scalability
- Easy to add new agents (in agents/)
- Easy to add new sectors (in sectors/)
- Easy to add new utilities (in utils/)

## Migration Plan

### Step 1: Create New Package Structure
```bash
mkdir -p ks_model/{agents,sectors,core,utils}
mkdir -p examples tests tools docs
```

### Step 2: Move Core Model Files
```bash
# Agents
mv model/agent.py ks_model/agents/base.py
mv model/worker.py ks_model/agents/
mv model/firm1.py ks_model/agents/
mv model/firm2.py ks_model/agents/
mv model/bank.py ks_model/agents/
mv model/vintage.py ks_model/agents/

# Sectors (extract from country.py)
# Split country.py into sectors/ and core/

# Core
mv model/statistics.py ks_model/core/
mv model/entry_exit.py ks_model/core/

# Utils
mv model/constants.py ks_model/utils/
mv model/data_structures.py ks_model/utils/
mv model/random_engine.py ks_model/utils/
mv model/support.py ks_model/utils/
```

### Step 3: Move Examples and Tests
```bash
mv example_*.py examples/
mv test_*.py tests/
```

### Step 4: Move Tools and Docs
```bash
mv convert_lsd_to_yaml.py tools/convert_configs.py
mv verify_completeness.py tools/verify.py
mv *.md docs/ (except main README.md)
```

### Step 5: Update All Imports
- Update imports throughout codebase
- Update __init__.py files
- Create new __init__.py where needed

### Step 6: Add setup.py
- Create proper package setup
- Define entry points
- Specify dependencies

## Implementation Decision

**Recommendation**: Implement a **moderate** restructuring:

1. **Keep** the current model/ directory structure (already good)
2. **Organize** scattered files into subdirectories
3. **Maintain** backward compatibility
4. **Focus** on immediate improvements without breaking changes

This approach:
- ✅ Improves organization
- ✅ Minimal disruption
- ✅ Easy to implement
- ✅ Can evolve later if needed

## Moderate Restructuring Plan

```
python/
├── model/                      # Core model (unchanged)
│   ├── agents/                # NEW: organize agents
│   └── ...
├── configs/                    # Configs (already good)
├── examples/                   # NEW: organize examples
├── tests/                      # NEW: organize tests
├── tools/                      # NEW: organize tools
├── docs/                       # NEW: organize docs
├── run_simulation.py          # Main entry point
└── README.md                  # Overview
```

This is the recommended approach for this task.
