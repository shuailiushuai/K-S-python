# K+S Model Python Implementation - Quick Start Guide

## English Version

### What is This?

This is a Python reimplementation of the K+S (Keynes+Schumpeter) Agent-Based Model, a sophisticated economic simulation featuring innovation, labor markets, and financial dynamics.

### Current Status

✅ **Working Components:**
- Worker agents with skills evolution
- Firm1 agents with R&D and innovation
- Random number generation (reproducible)
- Base infrastructure

⚠️ **In Development:** (~35% complete)
- Firm2, Bank, Labor market, Financial sector
- Full model integration
- Configuration and analysis tools

### Installation

```bash
cd python
pip install -r requirements.txt
```

### Quick Examples

#### Example 1: Worker Skills Evolution

```bash
python example_worker.py
```

**What it demonstrates:**
- Worker aging and retirement
- Skills learning (tenure + vintage)
- Job search behavior
- Employment transitions

**Output:**
```
Period 1: Age 26, Skills 0.4000 (unemployed)
Period 5: Hired in sector 2!
Period 10: Age 35, Skills 0.4323 (employed)
```

#### Example 2: Firm Innovation and R&D

```bash
python example_firm1.py
```

**What it demonstrates:**
- R&D investment decisions
- Innovation process (stochastic)
- Imitation from competitors
- Technology improvement
- Price competition

**Output:**
```
Firm 1: Atau: 1.100 → 1.182 ✓ IMPROVED (innovation)
Firm 2: Atau: 1.200 → 1.199 - same
Firm 3: Atau: 1.300 → 1.357 ✓ IMPROVED (innovation)
```

### Project Structure

```
python/
├── model/              # Core model code
│   ├── agent.py        # Base agent class ✅
│   ├── worker.py       # Worker agents ✅
│   ├── firm1.py        # Capital goods firms ✅
│   └── ...             # Other agents (in progress)
├── configs/            # Configuration files
├── analysis/           # Analysis scripts
├── example_*.py        # Working examples ✅
└── README.md          # Full documentation
```

### Key Features

#### 1. Reproducible Results
```python
from model.random_engine import random_engine
random_engine.seed(42)  # Fixed seed
```

#### 2. Worker Learning
- **Tenure skills**: Improve through work experience
- **Vintage skills**: Learn specific machine technologies
- **Training**: Government programs for unemployed

#### 3. Firm Innovation
- **Innovation**: Create new technologies (Beta distribution)
- **Imitation**: Copy from successful competitors
- **Competition**: Better technology → lower prices

### Next Steps

1. **Run the examples** to see the model in action
2. **Read README.md** for detailed documentation
3. **Check IMPLEMENTATION_PLAN.md** for development roadmap
4. **See FINAL_SUMMARY.md** for comprehensive status

### Contributing

The model is ~35% complete. Major components needed:
- Firm2 agents (consumption goods)
- Bank agents (financial system)
- Labor market matching
- Country-level orchestration

---

## 中文版本

### 这是什么？

这是K+S（凯恩斯+熊彼特）基于代理的模型的Python重新实现，是一个复杂的经济模拟系统，包含创新、劳动力市场和金融动态。

### 当前状态

✅ **已完成组件：**
- 具有技能演化的工人代理
- 具有R&D和创新的企业1代理
- 随机数生成（可重现）
- 基础架构

⚠️ **开发中：** （约35%完成）
- 企业2、银行、劳动力市场、金融部门
- 完整模型集成
- 配置和分析工具

### 安装

```bash
cd python
pip install -r requirements.txt
```

### 快速示例

#### 示例1：工人技能演化

```bash
python example_worker.py
```

**展示内容：**
- 工人年龄和退休
- 技能学习（任期+老式）
- 求职行为
- 就业转换

**输出：**
```
第1期：年龄26，技能0.4000（失业）
第5期：在部门2被雇佣！
第10期：年龄35，技能0.4323（就业）
```

#### 示例2：企业创新和R&D

```bash
python example_firm1.py
```

**展示内容：**
- R&D投资决策
- 创新过程（随机）
- 从竞争对手模仿
- 技术改进
- 价格竞争

**输出：**
```
企业1：生产率：1.100 → 1.182 ✓ 改进（创新）
企业2：生产率：1.200 → 1.199 - 相同
企业3：生产率：1.300 → 1.357 ✓ 改进（创新）
```

### 项目结构

```
python/
├── model/              # 核心模型代码
│   ├── agent.py        # 基础代理类 ✅
│   ├── worker.py       # 工人代理 ✅
│   ├── firm1.py        # 资本品企业 ✅
│   └── ...             # 其他代理（进行中）
├── configs/            # 配置文件
├── analysis/           # 分析脚本
├── example_*.py        # 工作示例 ✅
└── README.md          # 完整文档
```

### 关键特性

#### 1. 可重现结果
```python
from model.random_engine import random_engine
random_engine.seed(42)  # 固定种子
```

#### 2. 工人学习
- **任期技能**：通过工作经验提高
- **老式技能**：学习特定机器技术
- **培训**：失业者的政府项目

#### 3. 企业创新
- **创新**：创建新技术（Beta分布）
- **模仿**：复制成功竞争对手
- **竞争**：更好的技术 → 更低的价格

### 下一步

1. **运行示例**查看模型运行情况
2. **阅读README.md**获取详细文档
3. **查看IMPLEMENTATION_PLAN.md**了解开发路线图
4. **参考FINAL_SUMMARY.md**获取全面状态

### 贡献

模型约35%完成。需要的主要组件：
- 企业2代理（消费品）
- 银行代理（金融系统）
- 劳动力市场匹配
- 国家级协调

---

## Common Issues / 常见问题

### Issue: Module not found
**Solution:** Make sure you're in the `python/` directory and have installed dependencies:
```bash
cd python
pip install -r requirements.txt
```

### Issue: Import errors
**Solution:** Python needs to find the `model` package. Run from the `python/` directory:
```bash
python example_worker.py  # ✅ Correct
# Not: python model/example_worker.py  # ❌ Wrong
```

### 问题：找不到模块
**解决方案：** 确保您在`python/`目录中并已安装依赖项：
```bash
cd python
pip install -r requirements.txt
```

### 问题：导入错误
**解决方案：** Python需要找到`model`包。从`python/`目录运行：
```bash
python example_worker.py  # ✅ 正确
# 不是: python model/example_worker.py  # ❌ 错误
```

---

## Resources / 资源

### Documentation / 文档
- **README.md** - Full documentation / 完整文档
- **IMPLEMENTATION_PLAN.md** - Development plan / 开发计划
- **FINAL_SUMMARY.md** - Status and statistics / 状态和统计
- **实现总结.md** - Chinese summary / 中文摘要

### References / 参考文献
- Dosi et al. (2010). Schumpeter meeting Keynes. JEDC 34:1748-1767.
- Dosi et al. (2015). Fiscal and monetary policies. JEDC 52:166-189.
- Dosi et al. (2017). When more flexibility yields more fragility. JEDC 81:162-186.

### Support / 支持
- Open an issue on GitHub / 在GitHub上开issue
- Check documentation / 查看文档
- Review examples / 查看示例

---

## Quick Command Reference / 快速命令参考

```bash
# Install / 安装
pip install -r requirements.txt

# Run examples / 运行示例
python example_worker.py    # Worker agent / 工人代理
python example_firm1.py     # Firm innovation / 企业创新

# Future (when complete) / 未来（完成后）
python run_simulation.py    # Full model / 完整模型
python analyze_results.py   # Analysis / 分析
```

---

**Status:** 35% Complete | 35%完成  
**Last Updated:** 2024 | 最后更新：2024  
**License:** GNU GPL | 许可：GNU GPL
