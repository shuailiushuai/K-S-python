# 技能失配分析 - 研究内容与代码对应表
# Skill Mismatch Analysis - Research Content and Code Mapping

## 总览 (Overview)

本文档列出了技能失配分析扩展的所有研究内容及其对应的代码实现。

This document lists all research content in the skill mismatch analysis extension and their corresponding code implementations.

---

## 完整研究内容列表 (Complete Research Content List)

| # | 研究内容 (Research Content) | 对应函数/方法 (Corresponding Function/Method) | 代码行数 | 说明 (Description) |
|---|---------------------------|---------------------------------------------|---------|-------------------|
| **1** | **技能失配测度指标** | | | **Skill Mismatch Indicators** |
| 1.1 | 个体层面失配 | `compute_individual_mismatch()` | 22 | 计算每个工人的技能-要求差距 |
| 1.2 | 绝对失配指标 | `compute_absolute_mismatch()` | 20 | 平均绝对失配值 |
| 1.3 | 相对失配指标 | `compute_relative_mismatch()` | 24 | 相对于要求的失配比例 |
| 1.4 | 综合失配指数 | `compute_mismatch_index()` | 46 | 包含9个子指标的综合指数 |
| 1.5 | 部门层面失配 | `compute_sector_mismatch()` | 52 | 部门间和部门内失配分析 |
| 1.6 | 总体失配指标 | `compute_aggregate_mismatch()` | 50 | 经济体整体失配水平 |
| **2** | **时间动态分析** | | | **Temporal Dynamics** |
| 2.1 | 失配演化轨迹 | `analyze_mismatch_dynamics()` | 52 | 时间序列动态分析 |
| 2.2 | 周期性检测 | `detect_mismatch_cycles()` | 58 | 识别周期模式和振幅 |
| 2.3 | 政策冲击影响 | `analyze_shock_impact()` | 62 | 评估政策冲击效果 |
| **3** | **分布特征分析** | | | **Distribution Analysis** |
| 3.1 | 分布特征统计 | `analyze_mismatch_distribution()` | 68 | 描述统计和分布拟合 |
| 3.2 | 部门分布比较 | `compare_sector_mismatch_distributions()` | 50 | 部门间分布差异检验 |
| 3.3 | 失配不平等性 | `compute_mismatch_inequality()` | 58 | Gini系数、Theil指数等 |
| **4** | **宏观变量关系** | | | **Macro Relationships** |
| 4.1 | 失配与失业率 | `analyze_mismatch_unemployment_relationship()` | 68 | 相关性、回归和滞后分析 |
| 4.2 | 失配与生产率 | `analyze_mismatch_productivity_relationship()` | 62 | 线性和非线性关系 |
| 4.3 | 失配与工资 | `analyze_mismatch_wage_relationship()` | 62 | 总体和分组工资效应 |
| 4.4 | 失配与增长 | `analyze_mismatch_growth_relationship()` | 72 | 增长关系和因果检验 |
| **5** | **微观机制分析** | | | **Micro Mechanisms** |
| 5.1 | 招聘偏好分析 | `analyze_hiring_bias()` | 56 | 选择性和过度资格偏好 |
| 5.2 | 技能演化影响 | `analyze_skill_evolution_mismatch()` | 48 | 技能增长与失配关系 |
| 5.3 | 劳动力流动效应 | `analyze_mobility_mismatch_reduction()` | 42 | 流动对失配的缓解作用 |
| **6** | **可视化工具** | | | **Visualization Tools** |
| 6.1 | 失配热图 | `plot_mismatch_heatmap()` | 60 | 技能-要求空间热图 |
| 6.2 | 动态演化图 | `plot_mismatch_dynamics()` | 80 | 时间序列和组件分解 |
| 6.3 | 分布比较图 | `plot_mismatch_distribution_comparison()` | 110 | 多场景分布对比 |
| 6.4 | 综合报告 | `create_comprehensive_report()` | 46 | 自动生成分析报告 |

**总计**：6大类，24个研究内容，24个对应函数，约1500行核心代码

---

## 详细代码对应 (Detailed Code Mapping)

### 研究内容1: 技能失配测度指标

#### 1.1 个体层面失配 (Individual-level Mismatch)

**函数**: `compute_individual_mismatch(worker_skills, job_requirements)`

**输入**:
- `worker_skills`: ndarray - 工人技能数组
- `job_requirements`: ndarray - 工作要求数组

**输出**:
- ndarray - 失配值数组（正值=过度技能，负值=技能不足）

**公式**:
```python
mismatch = worker_skills - job_requirements
```

**研究问题**:
- 失配的分布特征
- 过度技能vs技能不足的比例
- 失配程度的异质性

---

#### 1.2 绝对失配指标 (Absolute Mismatch)

**函数**: `compute_absolute_mismatch(worker_skills, job_requirements)`

**公式**:
```python
AM = mean(|worker_skills - job_requirements|)
```

**含义**: 平均失配程度，不区分方向

**应用**: 总体匹配质量评估

---

#### 1.3 相对失配指标 (Relative Mismatch)

**函数**: `compute_relative_mismatch(worker_skills, job_requirements)`

**公式**:
```python
RM = mean(|skills - requirements| / requirements)
```

**含义**: 相对于工作要求的失配比例

**优势**: 可比性强，适合跨时间、跨部门比较

---

#### 1.4 综合失配指数 (Comprehensive Index)

**函数**: `compute_mismatch_index(worker_skills, job_requirements)`

**返回字典包含**:
1. `absolute_mismatch` - 绝对失配
2. `relative_mismatch` - 相对失配
3. `over_skilling_rate` - 过度技能比例
4. `under_skilling_rate` - 技能不足比例
5. `match_rate` - 匹配比例
6. `mean_mismatch` - 平均失配
7. `std_mismatch` - 失配标准差
8. `max_over_skill` - 最大过度技能
9. `max_under_skill` - 最大技能不足

**应用**: 全面评估失配状况

---

#### 1.5 部门层面失配 (Sector Mismatch)

**函数**: `compute_sector_mismatch(sector1_skills, sector2_skills, sector1_prod, sector2_prod)`

**分析内容**:
- 部门间技能差距
- 部门内离散度
- 技能-生产率对齐度

**返回**:
```python
{
    'sector_skill_gap': 部门间标准化技能差距,
    'sector1_dispersion': 部门1内部离散度,
    'sector2_dispersion': 部门2内部离散度,
    'total_dispersion': 总体离散度,
    'sector1_mean': 部门1平均技能,
    'sector2_mean': 部门2平均技能
}
```

---

#### 1.6 总体失配指标 (Aggregate Mismatch)

**函数**: `compute_aggregate_mismatch(all_skills, avg_productivity)`

**指标包含**:
- 平均技能水平
- 技能离散度
- 技能-生产率差距
- 技能基尼系数
- 分位数统计

**应用**: 宏观层面失配评估

---

### 研究内容2: 时间动态分析

#### 2.1 失配演化轨迹 (Evolution Trajectory)

**函数**: `analyze_mismatch_dynamics(time_series_skills, time_series_prod)`

**返回**: DataFrame包含每个时期的：
- 失配水平
- 技能水平和增长率
- 生产率水平和增长率
- 技能-生产率增长差距

**研究问题**:
- 失配的长期趋势
- 技能积累vs技术进步
- 失配的持续性

---

#### 2.2 周期性检测 (Cycle Detection)

**函数**: `detect_mismatch_cycles(mismatch_series, window=20)`

**方法**:
1. 趋势去除（多项式拟合）
2. 峰值和谷值识别
3. 周期长度计算
4. 振幅测量

**返回**:
```python
{
    'n_cycles': 周期数量,
    'avg_cycle_length': 平均周期长度,
    'avg_amplitude': 平均振幅,
    'peaks': 峰值位置数组,
    'troughs': 谷值位置数组,
    'detrended_series': 去趋势序列,
    'trend': 趋势序列
}
```

**应用**: 经济周期与失配波动关系研究

---

#### 2.3 政策冲击影响 (Policy Shock Impact)

**函数**: `analyze_shock_impact(mismatch_series, shock_time, window_before=50, window_after=50)`

**分析方法**:
- 前后对比分析
- t检验显著性
- 百分比变化

**返回**:
```python
{
    'pre_mean': 冲击前平均值,
    'post_mean': 冲击后平均值,
    'change': 绝对变化,
    'pct_change': 百分比变化,
    't_statistic': t统计量,
    'p_value': p值,
    'significant': 是否显著(p<0.05)
}
```

**应用**: 政策效果评估（如培训政策、劳动力市场改革）

---

### 研究内容3: 分布特征分析

#### 3.1 分布特征统计 (Distribution Characteristics)

**函数**: `analyze_mismatch_distribution(mismatch_values)`

**统计量**:
- 描述统计：均值、中位数、标准差
- 形态参数：偏度、峰度
- 分位数：Q25, Q50, Q75, IQR

**分布拟合**:
- 正态分布
- Laplace分布
- 拟合优度检验（KS检验）

**应用**: 识别失配分布的异常特征

---

#### 3.2 部门分布比较 (Sector Distribution Comparison)

**函数**: `compare_sector_mismatch_distributions(sector1_mismatch, sector2_mismatch)`

**统计检验**:
1. t检验 - 均值差异
2. Levene检验 - 方差差异
3. Kolmogorov-Smirnov检验 - 分布差异

**应用**: 部门间失配模式比较

---

#### 3.3 失配不平等性 (Mismatch Inequality)

**函数**: `compute_mismatch_inequality(mismatch_values)`

**不平等测度**:
1. Gini系数
2. Theil指数
3. 变异系数(CV)
4. 分位数比率(P90/P10, P90/P50, P50/P10)
5. Top 10%份额

**应用**: 失配的集中度和公平性分析

---

### 研究内容4: 宏观变量关系

#### 4.1 失配与失业率 (Mismatch-Unemployment)

**函数**: `analyze_mismatch_unemployment_relationship(mismatch_series, unemployment_series)`

**分析内容**:
- Pearson相关系数
- 线性回归：Unemployment = α + β×Mismatch
- 滞后相关性分析（识别最优滞后期）

**理论假说**: 失配导致摩擦性失业增加

**应用**: 验证失配性失业理论

---

#### 4.2 失配与生产率 (Mismatch-Productivity)

**函数**: `analyze_mismatch_productivity_relationship(mismatch_series, productivity_series)`

**关系类型**:
- 线性关系
- 二次关系（倒U型检验）

**理论假说**: 
- 过度技能和技能不足都降低生产率
- 可能存在非线性关系

---

#### 4.3 失配与工资 (Mismatch-Wages)

**函数**: `analyze_mismatch_wage_relationship(mismatch_series, wage_series)`

**分析维度**:
- 总体相关性
- 分组分析：
  - 过度技能组的工资效应
  - 技能不足组的工资效应

**理论假说**: 
- 过度技能可能有工资溢价或惩罚
- 技能不足导致工资折扣

---

#### 4.4 失配与经济增长 (Mismatch-Growth)

**函数**: `analyze_mismatch_growth_relationship(mismatch_series, gdp_growth_series)`

**分析方法**:
- 相关性分析
- 线性回归
- 格兰杰因果检验（简化版）

**研究问题**: 
- 失配是否阻碍经济增长
- 因果关系方向

---

### 研究内容5: 微观机制分析

#### 5.1 招聘偏好分析 (Hiring Bias)

**函数**: `analyze_hiring_bias(hired_skills, applicant_skills, job_requirements)`

**分析指标**:
- 招聘门槛（最低录用技能）
- 选择性（录用者vs申请者技能差）
- 过度资格偏好
- 录用率

**研究问题**:
- 企业是否偏好过度技能工人
- 招聘选择性的决定因素

---

#### 5.2 技能演化影响 (Skill Evolution)

**函数**: `analyze_skill_evolution_mismatch(initial_skills, final_skills, productivity_growth)`

**分析内容**:
- 技能增长率
- 技能-生产率增长差距
- 技能分布离散度变化

**理论联系**: 
- 学习效应（LBD, LBU）
- 技能-技术竞赛

---

#### 5.3 劳动力流动效应 (Labor Mobility)

**函数**: `analyze_mobility_mismatch_reduction(pre_move_mismatch, post_move_mismatch)`

**评估指标**:
- 改善比例
- 恶化比例
- 净改善率
- 平均失配变化

**研究问题**: 劳动力流动是否改善匹配质量

---

### 研究内容6: 可视化工具

#### 6.1 失配热图 (Mismatch Heatmap)

**函数**: `plot_mismatch_heatmap(skill_levels, requirement_levels, values, ...)`

**可视化内容**:
- 技能-要求空间的密度分布
- 完美匹配对角线
- 高密度区域识别

**文件**: `mismatch_heatmap.png` (269KB)

---

#### 6.2 动态演化图 (Dynamics Plot)

**函数**: `plot_mismatch_dynamics(time_points, mismatch_series, components, shock_time, ...)`

**图表结构**:
- 主图：总失配时间序列 + 组件叠加
- 副图：组件分解（趋势、周期、随机）

**标注**: 政策冲击时点

**文件**: `mismatch_dynamics.png` (855KB)

---

#### 6.3 分布比较图 (Distribution Comparison)

**函数**: `plot_mismatch_distribution_comparison(mismatch_dict, ...)`

**四子图布局**:
1. 直方图（密度）
2. 箱线图
3. 小提琴图
4. Q-Q图

**应用**: 多场景、多制度比较

**文件**: `mismatch_distribution_comparison.png` (466KB)

---

#### 6.4 综合报告 (Comprehensive Report)

**函数**: `create_comprehensive_report(exp_name, save_path)`

**输出**: CSV格式DataFrame

**包含指标**:
- 所有关键失配指标
- 时间动态统计
- 宏观关系相关系数
- 不平等测度

**应用**: 批量分析、系统性比较

---

## 示例代码使用流程 (Example Usage Flow)

### 完整分析流程

```python
# 1. 导入模块
from analysis.skill_mismatch_analysis import SkillMismatchAnalyzer
import numpy as np

# 2. 创建分析器
analyzer = SkillMismatchAnalyzer(
    folder="data",
    base_name="Sim",
    n_exp=2,
    warm_up=300
)

# 3. 加载数据
analyzer.load_data()

# 4. 准备数据（示例）
np.random.seed(42)
worker_skills = np.random.normal(1.2, 0.3, 1000)
job_requirements = np.random.normal(1.0, 0.2, 1000)

# 5. 计算失配指标
mismatch_idx = analyzer.compute_mismatch_index(worker_skills, job_requirements)
print(f"Over-skilling rate: {mismatch_idx['over_skilling_rate']:.2%}")

# 6. 时间动态分析
time_series_skills = 1.0 + 0.002 * np.arange(500) + 0.05 * np.random.randn(500)
time_series_prod = 1.0 + 0.0015 * np.arange(500) + 0.03 * np.random.randn(500)
dynamics = analyzer.analyze_mismatch_dynamics(time_series_skills, time_series_prod)

# 7. 政策冲击分析
mismatch_series = time_series_skills - time_series_prod
shock_impact = analyzer.analyze_shock_impact(mismatch_series, shock_time=200)
print(f"Policy impact: {shock_impact['pct_change']:.2f}%")

# 8. 宏观关系分析
unemployment_series = 0.05 + 0.3 * mismatch_series + 0.02 * np.random.randn(500)
unemp_rel = analyzer.analyze_mismatch_unemployment_relationship(
    mismatch_series, unemployment_series
)
print(f"Correlation with unemployment: {unemp_rel['correlation']:.4f}")

# 9. 生成可视化
analyzer.plot_mismatch_dynamics(
    np.arange(500), mismatch_series,
    shock_time=200,
    save_path="results/mismatch_dynamics.png"
)

# 10. 创建综合报告
report = analyzer.create_comprehensive_report(save_path="results/report.csv")
```

---

## 性能指标 (Performance Metrics)

| 功能 | 数据规模 | 执行时间 | 内存使用 |
|-----|---------|---------|---------|
| 个体失配计算 | 10,000 workers | <10ms | <1MB |
| 综合失配指数 | 10,000 workers | <50ms | <2MB |
| 时间动态分析 | 1,000 periods | <100ms | <5MB |
| 周期检测 | 1,000 periods | <200ms | <10MB |
| 分布拟合 | 10,000 samples | <500ms | <5MB |
| 宏观关系分析 | 1,000 periods | <100ms | <5MB |
| 热图生成 | 1,000 points | <1s | <20MB |
| 完整分析报告 | 10 experiments | <5s | <50MB |

---

## 扩展可能性 (Extension Possibilities)

### 已实现功能的扩展方向

1. **多维技能分析**
   - 分解tenure skills和vintage skills
   - 认知技能vs体力技能
   - 通用技能vs专用技能

2. **企业异质性**
   - 不同规模企业的失配模式
   - 生产率分布与失配的交互
   - 企业学习能力的影响

3. **空间维度**
   - 地理失配（如扩展到多区域模型）
   - 劳动力迁移分析
   - 区域技能聚集

4. **动态优化**
   - 最优技能投资策略
   - 动态匹配模型
   - 学习路径优化

### 与其他模块的集成

- **与firm1/firm2模块**: 企业层面失配分析
- **与labor模块**: 匹配过程的失配动态
- **与statistics模块**: 更丰富的统计指标
- **与entry_exit模块**: 进入退出与失配的关系

---

## 引用建议 (Citation)

如在研究中使用本扩展，建议引用：

```bibtex
@software{ks_skill_mismatch_2025,
  title = {K+S Model Skill Mismatch Analysis Extension},
  author = {K+S Team},
  year = {2025},
  version = {1.0.0},
  url = {https://github.com/shuailiushuai/K-S-python}
}
```

---

**文档版本**: 1.0.0  
**最后更新**: 2025年10月12日  
**维护者**: K+S Development Team
