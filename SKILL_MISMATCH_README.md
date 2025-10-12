# 技能失配分析扩展快速入门
# Skill Mismatch Analysis Extension - Quick Start Guide

## 简介 (Introduction)

本扩展为K+S模型添加了全面的技能失配分析功能。技能失配(Skill Mismatch)是指劳动力市场中工人技能与工作要求之间的不匹配，是影响劳动力市场效率、生产率和经济增长的关键因素。

This extension adds comprehensive skill mismatch analysis capabilities to the K+S model. Skill mismatch refers to the gap between worker skills and job requirements in the labor market, a key factor affecting labor market efficiency, productivity, and economic growth.

## 核心功能 (Key Features)

### 1. 六大分析类别 (Six Analysis Categories)

#### 📊 失配测度指标 (Mismatch Indicators)
- 个体层面：绝对失配、相对失配、失配方向
- 部门层面：部门间差异、内部离散度
- 总体层面：失配指数、技能基尼系数

#### 📈 时间动态分析 (Temporal Dynamics)
- 失配演化轨迹和趋势
- 周期性模式检测
- 政策冲击影响评估

#### 📉 分布特征分析 (Distribution Analysis)
- 失配分布的统计特征
- 部门间分布差异比较
- 失配不平等性测度

#### 🔗 宏观关系分析 (Macro Relationships)
- 失配与失业率
- 失配与生产率
- 失配与工资水平
- 失配与经济增长

#### 🔬 微观机制分析 (Micro Mechanisms)
- 招聘偏好与过度筛选
- 技能演化与失配动态
- 劳动力流动的失配缓解效应

#### 📊 可视化工具 (Visualization Tools)
- 失配热图
- 时间动态图
- 分布比较图
- 综合分析报告

## 快速开始 (Quick Start)

### 安装依赖 (Install Dependencies)

```bash
cd /home/runner/work/K-S-python/K-S-python/python
pip install -r requirements.txt
```

### 运行示例 (Run Examples)

```bash
python examples/example_skill_mismatch.py
```

这将运行7个完整示例，展示所有分析功能并生成可视化结果。

This will run 7 complete examples, demonstrating all analysis functions and generating visualizations.

### 基本用法 (Basic Usage)

```python
from analysis.skill_mismatch_analysis import SkillMismatchAnalyzer
import numpy as np

# 创建分析器 (Create analyzer)
analyzer = SkillMismatchAnalyzer()

# 模拟数据 (Simulate data)
worker_skills = np.random.normal(1.2, 0.3, 1000)
job_requirements = np.random.normal(1.0, 0.2, 1000)

# 计算失配指标 (Compute mismatch indicators)
mismatch_index = analyzer.compute_mismatch_index(worker_skills, job_requirements)
print(f"Over-skilling rate: {mismatch_index['over_skilling_rate']:.2%}")
print(f"Under-skilling rate: {mismatch_index['under_skilling_rate']:.2%}")
print(f"Match rate: {mismatch_index['match_rate']:.2%}")
```

## 主要分析方法 (Main Analysis Methods)

### 失配指标计算 (Mismatch Indicators)

```python
# 个体失配 (Individual mismatch)
individual_mismatch = analyzer.compute_individual_mismatch(skills, requirements)

# 绝对失配 (Absolute mismatch)
abs_mismatch = analyzer.compute_absolute_mismatch(skills, requirements)

# 综合失配指数 (Comprehensive mismatch index)
mismatch_idx = analyzer.compute_mismatch_index(skills, requirements)

# 部门失配 (Sector mismatch)
sector_mismatch = analyzer.compute_sector_mismatch(
    sector1_skills, sector2_skills, 
    sector1_prod, sector2_prod
)

# 总体失配 (Aggregate mismatch)
agg_mismatch = analyzer.compute_aggregate_mismatch(all_skills, avg_productivity)
```

### 时间动态分析 (Temporal Analysis)

```python
# 失配动态 (Mismatch dynamics)
dynamics = analyzer.analyze_mismatch_dynamics(
    time_series_skills, 
    time_series_prod
)

# 周期检测 (Cycle detection)
cycles = analyzer.detect_mismatch_cycles(mismatch_series, window=20)

# 冲击影响 (Shock impact)
shock_impact = analyzer.analyze_shock_impact(
    mismatch_series, 
    shock_time=200,
    window_before=50, 
    window_after=50
)
```

### 宏观关系分析 (Macro Relationships)

```python
# 失配与失业 (Mismatch and unemployment)
unemp_rel = analyzer.analyze_mismatch_unemployment_relationship(
    mismatch_series, 
    unemployment_series
)

# 失配与生产率 (Mismatch and productivity)
prod_rel = analyzer.analyze_mismatch_productivity_relationship(
    mismatch_series, 
    productivity_series
)

# 失配与工资 (Mismatch and wages)
wage_rel = analyzer.analyze_mismatch_wage_relationship(
    mismatch_series, 
    wage_series
)

# 失配与增长 (Mismatch and growth)
growth_rel = analyzer.analyze_mismatch_growth_relationship(
    mismatch_series, 
    gdp_growth_series
)
```

### 可视化 (Visualization)

```python
# 失配热图 (Mismatch heatmap)
analyzer.plot_mismatch_heatmap(
    skill_levels, 
    requirement_levels, 
    values,
    save_path="mismatch_heatmap.png"
)

# 动态图 (Dynamics plot)
analyzer.plot_mismatch_dynamics(
    time_points, 
    mismatch_series,
    components={'Structural': ..., 'Cyclical': ...},
    shock_time=200,
    save_path="mismatch_dynamics.png"
)

# 分布比较 (Distribution comparison)
analyzer.plot_mismatch_distribution_comparison(
    {'Fordist': data1, 'Competitive': data2},
    save_path="distribution_comparison.png"
)
```

## 示例输出 (Example Output)

### 失配指标 (Mismatch Indicators)

```
Mismatch Index:
   absolute_mismatch: 0.3269
   relative_mismatch: 0.3577
   over_skilling_rate: 0.6330  (63.3% of workers)
   under_skilling_rate: 0.2560  (25.6% of workers)
   match_rate: 0.1110  (11.1% of workers)
```

### 时间动态 (Temporal Dynamics)

```
Mismatch Dynamics:
   Average mismatch: 0.0641
   Mismatch trend: 0.0661
   Number of cycles: 19
   Average cycle length: 27.33 periods
   
Policy Shock Impact (t=200):
   Pre-shock mismatch: 0.0910
   Post-shock mismatch: 0.0244
   Change: -73.15% (statistically significant)
```

### 宏观关系 (Macro Relationships)

```
Mismatch and Unemployment:
   Correlation: 0.8301 (p=0.0000) ***
   Regression slope: 0.2607
   R²: 0.6891
   
Mismatch and Productivity:
   Correlation: -0.4098 (p=0.0000) ***
   Linear slope: -0.4368
   R²: 0.1679
```

## 研究应用案例 (Research Applications)

### 案例1: 制度比较研究

比较Fordist和Competitive劳动力市场制度下的技能失配差异：

```python
# 加载两种制度的仿真结果
analyzer = SkillMismatchAnalyzer(folder="data", base_name="regime_comparison")
analyzer.load_data()

# 比较失配分布
fordist_mismatch = extract_mismatch(regime="Fordist")
competitive_mismatch = extract_mismatch(regime="Competitive")

comparison = analyzer.compare_sector_mismatch_distributions(
    fordist_mismatch, 
    competitive_mismatch
)
```

### 案例2: 培训政策评估

评估政府培训政策对技能失配的影响：

```python
# 分析政策冲击
shock_impact = analyzer.analyze_shock_impact(
    mismatch_series,
    shock_time=200,  # 政策实施时点
    window_before=50,
    window_after=50
)

print(f"Policy effectiveness: {shock_impact['pct_change']:.2f}%")
print(f"Statistically significant: {shock_impact['significant']}")
```

### 案例3: 技术变革影响

分析技术冲击对失配动态的影响：

```python
# 分析失配演化
dynamics = analyzer.analyze_mismatch_dynamics(
    skill_series, 
    productivity_series
)

# 检测周期性
cycles = analyzer.detect_mismatch_cycles(mismatch_series)
print(f"Technology-skill cycles: {cycles['avg_cycle_length']:.1f} periods")
```

## 与K+S仿真集成 (Integration with K+S Simulation)

### 从仿真结果提取数据

```python
from run_simulation import run_ks_simulation
from analysis.skill_mismatch_analysis import analyze_skill_mismatch

# 运行仿真 (Run simulation)
results = run_ks_simulation(
    config_file="configs/baseline.yaml",
    n_runs=10
)

# 提取技能数据 (Extract skill data)
worker_skills = results['worker_data']['_s']  # Compound skills
tenure_skills = results['worker_data']['_sT']  # Tenure skills
vintage_skills = results['worker_data']['_sV']  # Vintage skills
productivity = results['firm_data']['A2']  # Productivity

# 失配分析 (Mismatch analysis)
analyzer = analyze_skill_mismatch(folder="results", base_name="baseline")
```

## 理论背景 (Theoretical Background)

### 技能失配的类型 (Types of Skill Mismatch)

1. **过度技能 (Over-skilling)**
   - 工人技能高于工作要求
   - 可能导致：工作不满意、生产率损失、人才流失
   
2. **技能不足 (Under-skilling)**
   - 工人技能低于工作要求
   - 可能导致：生产率低下、质量问题、培训需求

3. **技能错配 (Skill Mismatch)**
   - 技能类型不匹配（即使水平相当）
   - 结构性失配问题

### 失配的经济影响 (Economic Impact)

- **微观层面**: 工资惩罚、就业不稳定、职业满意度下降
- **中观层面**: 企业生产率损失、人力资源浪费
- **宏观层面**: 经济增长放缓、劳动力市场效率下降

### K+S模型中的失配机制

1. **技能异质性**: 工人具有不同的tenure和vintage技能
2. **学习机制**: 在职学习(LBD)和使用学习(LBU)
3. **匹配过程**: 搜索-匹配机制，考虑技能要求
4. **部门差异**: 资本品部门vs消费品部门的技能需求差异

## 高级功能 (Advanced Features)

### 自定义失配定义

```python
# 定义自定义失配函数
def custom_mismatch(skills, requirements, threshold=0.1):
    """Custom mismatch with tolerance threshold"""
    diff = skills - requirements
    # Only count as mismatch if beyond threshold
    return np.where(np.abs(diff) > threshold, diff, 0)

# 使用自定义函数
custom_mm = custom_mismatch(worker_skills, job_requirements, threshold=0.15)
```

### 批量分析多个实验

```python
# 分析多个实验配置
experiments = ['Fordist', 'Competitive', 'Baseline']
results = {}

for exp in experiments:
    analyzer = SkillMismatchAnalyzer(
        folder=f"data/{exp}",
        base_name="Sim",
        n_exp=10
    )
    analyzer.load_data()
    results[exp] = analyzer.create_comprehensive_report()

# 比较结果
import pandas as pd
comparison = pd.concat(results, names=['Experiment', 'Run'])
```

### 并行处理

```python
from multiprocessing import Pool

def analyze_single_run(run_id):
    analyzer = SkillMismatchAnalyzer(
        folder=f"data/run_{run_id}",
        base_name="Sim"
    )
    return analyzer.compute_mismatch_index(skills, requirements)

# 并行分析多个运行
with Pool(processes=4) as pool:
    results = pool.map(analyze_single_run, range(100))
```

## 性能优化建议 (Performance Tips)

1. **向量化计算**: 所有主要函数都使用NumPy向量化操作
2. **数据预处理**: 在分析前清理和标准化数据
3. **内存管理**: 对大规模数据使用分块处理
4. **缓存结果**: 重复使用的计算结果应缓存

## 故障排除 (Troubleshooting)

### 常见问题

**Q: 导入模块失败**
```bash
# 确保安装了所有依赖
pip install -r requirements.txt
```

**Q: 数据格式不兼容**
```python
# 确保数据格式正确
assert isinstance(skills, np.ndarray)
assert skills.shape == requirements.shape
```

**Q: 可视化无法显示**
```python
# 在无显示环境中，保存到文件
analyzer.plot_mismatch_dynamics(..., save_path="output.png")
```

## 参考文献 (References)

### 技能失配理论
- McGowan & Andrews (2015). "Skill mismatch and public policy in OECD countries."
- Quintini (2011). "Over-qualified or under-skilled."
- Pellizzari & Fichen (2017). "A new measure of skill mismatch."

### K+S模型
- Dosi et al. (2018). "Causes and consequences of hysteresis."
- Dosi et al. (2019). "The effects of labour market reforms."
- Dosi et al. (2020). "More is different ... and complex!"

## 贡献指南 (Contributing)

欢迎贡献新的分析方法和改进！请：

1. Fork仓库
2. 创建特性分支
3. 提交更改
4. 发起Pull Request

## 许可证 (License)

本扩展遵循K+S模型的原始许可证（GNU General Public License）。

## 联系方式 (Contact)

- GitHub Issues: [K-S-python/issues](https://github.com/shuailiushuai/K-S-python/issues)
- 文档: `SKILL_MISMATCH_ANALYSIS.md`

---

**版本 (Version)**: 1.0.0  
**最后更新 (Last Updated)**: 2025年10月12日  
**作者 (Author)**: GitHub Copilot / K+S Team
