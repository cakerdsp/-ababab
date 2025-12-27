# 两阶段布图优化系统配置说明

## 可用配置文件

- **two_phase_ga_btree.yaml**: 遗传算法 + B*Tree表示
- **two_phase_sa_sp.yaml**: 模拟退火 + 序列对表示
- **simple_two_phase.yaml**: 简化配置，快速测试
- **complete_parameters_example.yaml**: 完整参数配置参考

## 使用方法

```bash
cd Floorplan
python main.py config/two_phase_ga_btree.yaml
python main.py config/two_phase_sa_sp.yaml
python main.py config/simple_two_phase.yaml
```

## 主要参数说明

### 算法选择

- **algorithm.name**: simulated_annealing | genetic
- **algorithm.representation**: sequence_pair | btree
- **algorithm.max_iterations**: 推荐500-2000

### Pin分配算法

- **uniform_edge**: 最快速，均匀分布
- **center_of_gravity**: 平衡质量和速度
- **greedy**: 质量最好但最慢

### 评估权重

- **hpwl**: 线长权重，推荐0.5-2.0
- **area**: 面积权重，推荐0.3-1.0
- **feedthrough**: 穿透权重，推荐5.0-20.0

### 可视化配置

- **output.visualization.enabled**: 启用可视化
- **output.visualization.draw_frequency**: 绘图频率
- **output.visualization.image_format**: 图像格式

## 推荐配置

### 快速测试

```yaml
algorithm:
  max_iterations: 100
pin_assignment:
  algorithm: "uniform_edge"
output:
  visualization:
    enabled: false
```

### 标准配置

```yaml
algorithm:
  max_iterations: 1000
pin_assignment:
  algorithm: "center_of_gravity"
output:
  visualization:
    enabled: true
```

### 高质量配置

```yaml
algorithm:
  max_iterations: 2000
pin_assignment:
  algorithm: "greedy"
```

## 重要说明

1. Pin只能放置在芯片边缘的整数坐标
2. 系统默认启用严格合法性检查
3. Pin分配算法质量和速度成反比
4. 大规模问题建议关闭可视化节约内存
