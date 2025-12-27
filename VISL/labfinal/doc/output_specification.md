# 输出数据规范

## 1. 输出数据类型

### 1.1 标量指标 (Scalar Metrics)

所有标量指标都以 `torch.Tensor`标量形式返回，支持自动微分：

#### 1.1.1 线长指标

```python
hpwl: torch.Tensor (标量)               # 加权半周长线长总和
rmst_wl: torch.Tensor (标量)            # 基于Steiner树的线长（可选）
weighted_average_wl: torch.Tensor       # 加权平均线长（可选）
```

**数值范围**: [0, +∞)
**单位**: 与输入坐标单位一致
**计算公式**:

```python
HPWL = Σ(net_weight[i] * ((max_x[i] - min_x[i]) + (max_y[i] - min_y[i])))
```

#### 1.1.2 密度指标

```python
density_cost: torch.Tensor (标量)       # 密度违规总代价
max_density: torch.Tensor (标量)        # 最大密度值（相对值）
overflow_ratio: torch.Tensor (标量)     # 溢出率（相对于总面积）
```

**数值范围**:

- `density_cost`: [0, +∞)，越小越好
- `max_density`: [0, +∞)，1.0表示目标密度
- `overflow_ratio`: [0, 1.0]，0表示无溢出

#### 1.1.3 空白面积指标

```python
whitespace: torch.Tensor (标量)         # 绝对空白面积
utilization: torch.Tensor (标量)        # 面积利用率
```

**数值范围**:

- `whitespace`: [0, total_chip_area]
- `utilization`: [0, 1.0]，越接近目标利用率越好

#### 1.1.4 Feedthrough指标

```python
feedthrough_count: torch.Tensor (标量)  # 穿越模块的网线数量
feedthrough_ratio: torch.Tensor (标量) # 相对于总网线数的比例
```

**数值范围**:

- `feedthrough_count`: [0, num_nets]，整数值
- `feedthrough_ratio`: [0, 1.0]

#### 1.1.5 路由拥塞指标

```python
avg_route_utilization: torch.Tensor (标量)  # 平均路由利用率
max_route_utilization: torch.Tensor (标量)  # 最大路由利用率
route_overflow_ratio: torch.Tensor (标量)   # 拥塞区域比例
```

### 1.2 张量指标 (Tensor Metrics)

#### 1.2.1 密度分布图

```python
density_map: torch.Tensor[num_bins_x, num_bins_y]  # 密度分布
```

**含义**: 每个网格单元的密度值
**数值范围**: [0, +∞)
**单位**: 面积密度（面积/网格面积）

#### 1.2.2 路由利用率图

```python
route_utilization_map: torch.Tensor[num_bins_x, num_bins_y]  # 路由利用率分布
horizontal_utilization: torch.Tensor[num_bins_x, num_bins_y] # 水平方向利用率
vertical_utilization: torch.Tensor[num_bins_x, num_bins_y]   # 垂直方向利用率
```

**含义**: 每个网格的路由资源利用率
**数值范围**: [0, +∞)，1.0表示满载

## 2. 输出格式

### 2.1 实时评估输出

#### 2.1.1 EvalMetrics对象

```python
class EvalMetrics:
    # 基本信息
    iteration: int                      # 迭代次数
    eval_time: float                   # 评估耗时（秒）
  
    # 目标函数
    objective: torch.Tensor            # 总目标函数值
  
    # 核心指标
    hpwl: torch.Tensor                 # 线长
    density_cost: torch.Tensor         # 密度代价
    overflow: torch.Tensor             # 溢出率
    max_density: torch.Tensor          # 最大密度
    feedthrough: torch.Tensor          # Feedthrough数量
    utilization: torch.Tensor          # 利用率
    route_utilization: torch.Tensor    # 路由拥塞
  
    # 扩展指标（可选）
    whitespace: torch.Tensor           # 空白面积
    wirelength: torch.Tensor           # 未加权线长
    timing_cost: torch.Tensor          # 时序代价（如果启用）
```

#### 2.1.2 字符串格式输出

```python
def __str__(self):
    return (f"iteration: {self.iteration:6d}, "
            f"HPWL {self.hpwl:.3E}, "
            f"Overflow {self.overflow:.3f}, "
            f"MaxDensity {self.max_density:.3f}, "
            f"Feedthrough {self.feedthrough:4.0f}, "
            f"Utilization {self.utilization:.2f}, "
            f"RouteUtil {self.route_utilization:.3f}, "
            f"time {self.eval_time*1000:.1f}ms")
```

**示例输出**:

```
iteration:    100, HPWL 1.234E+06, Overflow 0.123, MaxDensity 1.456, 
Feedthrough  234, Utilization 0.85, RouteUtil 0.067, time 45.2ms
```

### 2.2 文件输出格式

#### 2.2.1 JSON报告格式

```json
{
  "evaluation_summary": {
    "timestamp": "2024-01-15T10:30:45.123Z",
    "iteration": 100,
    "design_name": "example_design",
    "algorithm": "DREAMPlace",
    "version": "4.0"
  },
  "metrics": {
    "objective": {
      "value": 2.456789e6,
      "unit": "cost_units"
    },
    "wirelength": {
      "hpwl": 1.234567e6,
      "unit": "distance_units",
      "weighted": true
    },
    "density": {
      "overflow_cost": 1.123456e5,
      "overflow_ratio": 0.123,
      "max_density": 1.456,
      "target_density": 0.8,
      "bins": {"x": 32, "y": 32}
    },
    "feedthrough": {
      "count": 234,
      "ratio": 0.156,
      "total_nets": 1500
    },
    "area": {
      "utilization": 0.85,
      "whitespace": 1.234e4,
      "total_area": 8.765e4,
      "unit": "area_units"
    },
    "routing": {
      "avg_utilization": 0.067,
      "max_utilization": 0.234,
      "overflow_ratio": 0.012
    }
  },
  "performance": {
    "eval_time_ms": 45.2,
    "memory_usage_mb": 128.5,
    "gpu_utilization": 0.78
  },
  "quality_assessment": {
    "overall_score": 8.5,
    "wirelength_grade": "A",
    "density_grade": "B+", 
    "feedthrough_grade": "A-",
    "routing_grade": "A"
  }
}
```

#### 2.2.2 CSV数据格式

```csv
iteration,timestamp,hpwl,density_cost,overflow,max_density,feedthrough,utilization,route_util,eval_time_ms,objective
100,2024-01-15T10:30:45,1234567.89,112345.67,0.123,1.456,234,0.85,0.067,45.2,2456789.01
101,2024-01-15T10:30:47,1230445.67,108234.56,0.118,1.445,232,0.85,0.065,44.8,2450123.45
102,2024-01-15T10:30:49,1225678.90,105123.45,0.115,1.434,230,0.85,0.063,45.1,2443567.89
```

#### 2.2.3 详细评估报告 (.txt)

```
================================================================================
DREAMPlace 布图质量评估报告
================================================================================
设计信息:
  设计名称:           example_design
  评估时间:           2024-01-15 10:30:45
  迭代次数:           100
  算法版本:           DREAMPlace 4.0

设计规模:
  节点总数:           10,000
  可移动节点:         8,500
  固定节点:           1,200
  填充节点:           300
  网线总数:           15,000
  引脚总数:           45,000

芯片信息:
  芯片尺寸:           1000 × 800 μm²
  总面积:             800,000 μm²
  目标利用率:         85%
  目标密度:           80%

================================================================================
评估结果:
================================================================================

1. 线长指标:
   半周长线长 (HPWL):          1,234,567.89 μm
   平均网线长度:               82.3 μm
   长网线数量 (>500μm):        23
   线长评级:                   A (优秀)

2. 密度指标:
   密度违规代价:               112,345.67
   溢出率:                     12.3%
   最大密度:                   145.6% (相对目标密度)
   密度热点数量:               5
   密度评级:                   B+ (良好)

3. 空白面积指标:
   面积利用率:                 85.0%
   空白面积:                   12,340 μm²
   空白面积比例:               1.5%
   利用率评级:                 A (优秀)

4. Feedthrough指标:
   穿越网线数量:               234
   Feedthrough比例:            1.56%
   最大穿越模块:               sb15 (12个网线穿越)
   Feedthrough评级:            A- (优良)

5. 路由拥塞指标:
   平均路由利用率:             6.7%
   最大路由利用率:             23.4%
   拥塞区域比例:               1.2%
   路由评级:                   A (优秀)

================================================================================
性能统计:
================================================================================
   评估耗时:                   45.2 ms
   内存使用:                   128.5 MB
   GPU利用率:                  78%

================================================================================
质量评估:
================================================================================
   综合评分:                   8.5/10
   推荐操作:                   继续优化密度分布
   关键问题:                   存在5个密度热点区域
   优化建议:                   调整密度权重或增加全局移动步长

================================================================================
```

### 2.3 可视化输出

#### 2.3.1 实时可视化数据

```python
class VisualizationData:
    # 位置信息
    node_positions: np.ndarray[num_nodes, 2]    # 节点位置
    node_sizes: np.ndarray[num_nodes, 2]        # 节点尺寸
  
    # 连接信息
    net_connections: List[List[Tuple[float, float]]]  # 网线连接
  
    # 热力图数据
    density_heatmap: np.ndarray[num_bins_x, num_bins_y]      # 密度热力图
    congestion_heatmap: np.ndarray[num_bins_x, num_bins_y]   # 拥塞热力图
  
    # 统计信息
    metrics_history: pd.DataFrame                     # 历史指标数据
```

#### 2.3.2 图表生成接口

```python
def generate_plots(eval_metrics, output_dir):
    # 1. 指标趋势图
    plot_metrics_trend(eval_metrics.get_history(), 
                      save_path=f"{output_dir}/metrics_trend.png")
  
    # 2. 密度热力图
    plot_density_heatmap(eval_metrics.density_map,
                        save_path=f"{output_dir}/density_heatmap.png")
  
    # 3. 布局可视化
    plot_placement_layout(eval_metrics.get_positions(),
                         save_path=f"{output_dir}/layout.png")
  
    # 4. 拥塞分析图
    plot_congestion_analysis(eval_metrics.route_utilization_map,
                            save_path=f"{output_dir}/congestion.png")
```

## 3. 输出数据流

### 3.1 实时输出流

```python
# 优化过程中的实时输出
for iteration in optimization_loop:
    # 执行一步优化
    pos = optimizer.step()
  
    # 评估当前状态
    metrics = evaluator.evaluate(pos)
  
    # 实时输出
    if iteration % log_interval == 0:
        print(metrics)  # 控制台输出
        logger.log_metrics(metrics)  # 日志记录
        writer.add_scalar('HPWL', metrics.hpwl, iteration)  # TensorBoard
```

### 3.2 批量输出

```python
# 优化完成后的批量输出
def save_final_results(evaluator, output_dir):
    # 1. 保存最终指标
    final_metrics = evaluator.get_final_metrics()
    with open(f"{output_dir}/final_metrics.json", 'w') as f:
        json.dump(final_metrics.to_dict(), f, indent=2)
  
    # 2. 保存历史数据
    history_df = evaluator.get_metrics_history()
    history_df.to_csv(f"{output_dir}/metrics_history.csv", index=False)
  
    # 3. 生成评估报告
    report = generate_detailed_report(final_metrics)
    with open(f"{output_dir}/evaluation_report.txt", 'w') as f:
        f.write(report)
  
    # 4. 保存可视化图表
    generate_plots(final_metrics, output_dir)
```

## 4. 输出数据的使用

### 4.1 优化反馈

```python
# 目标函数计算
objective = (wirelength_weight * metrics.hpwl + 
            density_weight * metrics.density_cost +
            feedthrough_weight * metrics.feedthrough)

# 梯度反向传播
objective.backward()
```

### 4.2 收敛判断

```python
def check_convergence(metrics_history):
    if len(metrics_history) < 10:
        return False
      
    recent_objectives = [m.objective for m in metrics_history[-10:]]
    improvement = (recent_objectives[0] - recent_objectives[-1]) / recent_objectives[0]
  
    return improvement < convergence_threshold
```

### 4.3 质量分析

```python
def analyze_quality(metrics):
    quality_report = {
        'wirelength_quality': 'excellent' if metrics.hpwl < hpwl_target else 'needs_improvement',
        'density_quality': 'good' if metrics.overflow < 0.1 else 'poor',
        'feedthrough_quality': 'excellent' if metrics.feedthrough < ft_target else 'acceptable',
        'overall_quality': compute_overall_score(metrics)
    }
    return quality_report
```

这套输出规范提供了完整的评估结果表示和分析能力，支持实时监控、批量分析和质量评估等多种应用场景。
