# K+S Python Implementation - Project Overview

## 📁 What's in This Repository

This repository contains the original **K+S (Keynes+Schumpeter) Agent-Based Model** in C++ (for LSD), along with a **new Python reimplementation** in the `python/` directory.

### Repository Contents

```
K-S-python/
├── python/                          # ✨ NEW: Python implementation
│   ├── model/                       # Core model code
│   │   ├── agent.py                 # ✅ Base agent class
│   │   ├── worker.py                # ✅ Worker agents
│   │   ├── firm1.py                 # ✅ Capital goods firms
│   │   └── ...                      # ⚠️ Other agents (in progress)
│   ├── configs/                     # Configuration files
│   ├── analysis/                    # Analysis scripts
│   ├── example_worker.py            # ✅ Working example
│   ├── example_firm1.py             # ✅ Working example
│   ├── README.md                    # Full Python documentation
│   ├── QUICKSTART.md                # Quick start guide (EN + 中文)
│   ├── IMPLEMENTATION_PLAN.md       # Development roadmap
│   ├── FINAL_SUMMARY.md             # Status & statistics
│   └── 实现总结.md                   # Chinese summary
│
├── fun_KS*.cpp, fun_KS*.h           # Original C++ implementation
├── *.lsd                            # Configuration files
├── *.R                              # R analysis scripts
├── description.txt                  # Model documentation
└── model_options.txt                # Model options
```

---

## 🐍 Python Implementation (NEW!)

### Quick Start

```bash
cd python
pip install numpy
python example_worker.py    # See worker skills evolution
python example_firm1.py     # See firm innovation & R&D
```

### What's Working ✅

1. **Worker Agents** (100% complete)
   - Skills learning (tenure + vintage)
   - Job search behavior
   - Employment tracking
   - Validated with 10-period simulation

2. **Firm1 Agents** (80% complete)
   - R&D process (innovation + imitation)
   - Technology selection
   - Competition dynamics
   - Validated with multi-firm example

3. **Infrastructure** (100% complete)
   - Agent framework
   - Random number generation (reproducible)
   - Data structures
   - Utilities

### What's Next ⚠️

- Firm2 agents (consumption goods)
- Bank agents (financial sector)
- Labor market matching
- Country-level orchestration
- Configuration system
- Analysis tools

**Current Status:** ~35% complete (~2,750 lines)

### Documentation

📖 **Start Here:**
- **[QUICKSTART.md](python/QUICKSTART.md)** - Quick start guide (English + 中文)
- **[README.md](python/README.md)** - Full documentation
- **[FINAL_SUMMARY.md](python/FINAL_SUMMARY.md)** - Complete status report

📋 **Planning:**
- **[IMPLEMENTATION_PLAN.md](python/IMPLEMENTATION_PLAN.md)** - Development roadmap
- **[实现总结.md](python/实现总结.md)** - Chinese summary

### Why Python? (Why Not Mesa?)

After analyzing the original model, **pure Python** was chosen over Mesa 3.0 because:
- Complex temporal dependencies requiring precise equation sequencing
- Custom random number generation for reproducibility
- Stock-flow consistency needs
- LSD-specific features (hooks, lagged variables)

Full reasoning in [README.md](python/README.md).

---

## 🔬 Original C++ Implementation

### Model Description

The K+S model is a general disequilibrium, stock-and-flow consistent, agent-based model featuring:

- **Capital goods firms**: R&D, innovation, machine production
- **Consumption goods firms**: Production, investment, competition
- **Workers**: Skills, job search, consumption
- **Banks**: Credit supply, capital adequacy
- **Government & Central Bank**: Fiscal/monetary policy

**Version:** 5.1.3  
**Code:** ~10,800 lines of C++  
**Environment:** LSD 8.0+

### Configuration Files (.lsd)

Ready-to-use scenarios:
- `Cent_wage-Baseline_v2.lsd` - 2015 JEDC paper configuration
- `Ten_skills-Free_entry-Full_fin.lsd` - 2019 paper (full finance)
- `No_skills-Fix_entry-No_fin.lsd` - 2017 paper (Fordist regime)
- And more...

### Analysis Scripts (.R)

R scripts for analyzing simulation results:
- `KS-aggregates.R` - Macroeconomic aggregates
- `KS-sector-1.R` - Capital goods sector analysis
- `KS-sector-2-pool.R` - Consumption goods sector
- `KS-workers.R` - Worker-level analysis
- `KS-elementary-effects-SA.R` - Sensitivity analysis
- And more...

### Documentation

- **[description.txt](description.txt)** - Complete model description
- **[model_options.txt](model_options.txt)** - Configuration options
- **[modelinfo.txt](modelinfo.txt)** - Additional information

---

## 📊 Comparison: C++ vs Python

| Aspect | C++ (Original) | Python (New) |
|--------|----------------|--------------|
| **Status** | ✅ Complete | ⚠️ 35% complete |
| **Lines of Code** | ~10,800 | ~1,500 (core) |
| **Environment** | LSD 8.0+ | Pure Python |
| **Dependencies** | LSD framework | numpy, yaml, pandas |
| **Random Engine** | mt19937_64 | ✅ Compatible |
| **Validation** | Published papers | ⚠️ In progress |
| **Performance** | Fast (C++) | Moderate (Python) |
| **Extensibility** | Medium | ✅ High |
| **Documentation** | Good | ✅ Excellent |

---

## 🎯 Use Cases

### Use Original C++ If:
- ✅ You need the complete, validated model
- ✅ You want to replicate published results
- ✅ You have LSD installed
- ✅ Performance is critical

### Use Python Version If:
- ✅ You want to understand the model internals
- ✅ You need to extend/modify the model
- ✅ You prefer Python ecosystem
- ✅ You want clear, documented code
- ⚠️ You can wait for completion (or contribute!)

---

## 🤝 Contributing

The Python implementation is ~35% complete. Contributions welcome!

**Priority areas:**
1. Firm2 agent implementation
2. Bank agent implementation  
3. Labor market matching
4. Configuration system
5. Testing framework

See [IMPLEMENTATION_PLAN.md](python/IMPLEMENTATION_PLAN.md) for details.

---

## 📚 References

### Original Papers

- Dosi et al. (2010). Schumpeter meeting Keynes: A policy-friendly model of endogenous growth and business cycles. *Journal of Economic Dynamics and Control* 34:1748-1767.

- Dosi et al. (2015). Fiscal and monetary policies in complex evolving economies. *Journal of Economic Dynamics and Control* 52:166-189.

- Dosi et al. (2017). When more flexibility yields more fragility: the microfoundations of Keynesian aggregate unemployment. *Journal of Economic Dynamics and Control* 81:162-186.

- Dosi et al. (2018). Causes and consequences of hysteresis: aggregate demand, productivity, employment. *Industrial and Corporate Change* 27:1015-1044.

### Links

- **LSD**: https://github.com/SantAnnaKS/LSD
- **Original K+S**: Developed by Andrea Roventini and contributors

---

## 📄 License

GNU General Public License

---

## 💬 Contact

For questions about:
- **C++ implementation**: See LSD/K+S documentation
- **Python implementation**: Open an issue on GitHub

---

## 🗺️ Quick Navigation

### I want to...

**...run the Python examples**
→ Go to [python/QUICKSTART.md](python/QUICKSTART.md)

**...understand the Python implementation**
→ Read [python/README.md](python/README.md)

**...see the implementation status**
→ Check [python/FINAL_SUMMARY.md](python/FINAL_SUMMARY.md)

**...contribute to Python version**
→ Review [python/IMPLEMENTATION_PLAN.md](python/IMPLEMENTATION_PLAN.md)

**...use the original C++ model**
→ Read [description.txt](description.txt)

**...understand the model theory**
→ See references above and description.txt

---

**Status:** Python version ~35% complete | Original C++ complete  
**Last Updated:** 2024  
**Maintained By:** Community contributions welcome
