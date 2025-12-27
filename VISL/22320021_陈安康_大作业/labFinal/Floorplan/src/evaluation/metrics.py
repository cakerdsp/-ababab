#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
评估指标 - Evaluation Metrics

布图质量评估的核心指标计算模块
Core metrics calculation module for floorplan quality evaluation
"""

import numpy as np
import math
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

from ..data.structures import FloorplanDesign, Module, Net, ModuleType, EvaluationResult


# EvaluationResult已移至data.structures避免重复定义


class FloorplanEvaluator:
    """
    布图评估器 - Floorplan Evaluator
    
    提供布图质量评估的统一接口
    Provides unified interface for floorplan quality evaluation
    """
    
    def __init__(self, 
                 area_weight: float = 0.5,
                 wirelength_weight: float = 0.5,
                 feedthrough_weight: float = 0.0,
                 whitespace_weight: float = 0.0):
        """
        初始化评估器
        
        Args:
            area_weight: 面积权重
            wirelength_weight: 线长权重
            feedthrough_weight: Feedthrough权重
            whitespace_weight: 空白空间权重
        """
        self.area_weight = area_weight
        self.wirelength_weight = wirelength_weight
        self.feedthrough_weight = feedthrough_weight
        self.whitespace_weight = whitespace_weight
        
        # 归一化参数
        self.normalization_factors = {}
        
    def evaluate(self, design: FloorplanDesign) -> float:
        """
        评估布图设计，返回单一代价值
        
        Args:
            design: 布图设计
            
        Returns:
            代价值（越小越好）
        """
        result = evaluate_floorplan(design)
        
        return result.get_weighted_cost(
            self.area_weight,
            self.wirelength_weight,
            self.feedthrough_weight,
            self.whitespace_weight
        )
    
    def detailed_evaluate(self, design: FloorplanDesign) -> EvaluationResult:
        """详细评估，返回完整的评估结果"""
        return evaluate_floorplan(design)
    
    def set_normalization_factors(self, factors: Dict[str, float]):
        """设置归一化因子"""
        self.normalization_factors = factors
    
    def update_weights(self, **kwargs):
        """更新权重"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


def calculate_area(design: FloorplanDesign) -> float:
    """
    计算布图总面积
    Calculate total floorplan area
    
    Args:
        design: 布图设计
        
    Returns:
        总面积
    """
    if not design.modules:
        return 0.0
    
    # 计算边界框
    bbox = design.get_bounding_box()
    
    if bbox[2] <= bbox[0] or bbox[3] <= bbox[1]:
        return 0.0
    
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    
    return width * height


def calculate_wirelength(design: FloorplanDesign, method: str = "hpwl") -> float:
    """
    计算总线长
    Calculate total wirelength
    
    Args:
        design: 布图设计
        method: 计算方法 ("hpwl", "rmst", "steiner")
        
    Returns:
        总线长
    """
    if not design.nets:
        return 0.0
    
    total_length = 0.0
    
    for net in design.nets.values():
        if len(net.pins) < 2:
            continue
        
        # 获取网线连接的模块位置
        pin_positions = []
        
        for module_name, pin_name in net.pins:
            if module_name in design.modules:
                module = design.modules[module_name]
                
                # 实际计算Pin位置（考虑Pin偏移）
                if pin_name in module.pins:
                    pin = module.pins[pin_name]
                    pin_x = module.x + pin.x_offset
                    pin_y = module.y + pin.y_offset
                else:
                    # 如果找不到具体Pin，使用模块中心
                    pin_x, pin_y = module.get_center()
                
                pin_positions.append((pin_x, pin_y))
        
        if len(pin_positions) < 2:
            continue
        
        # 根据方法计算网线长度
        if method == "hpwl":
            net_length = _calculate_hpwl(pin_positions)
        elif method == "rmst":
            net_length = _calculate_rmst(pin_positions)
        else:
            # 默认使用HPWL
            net_length = _calculate_hpwl(pin_positions)
        
        total_length += net_length * net.weight
    
    return total_length


def _calculate_hpwl(positions: List[Tuple[float, float]]) -> float:
    """计算半周线长 (Half-Perimeter Wire Length)"""
    if len(positions) < 2:
        return 0.0
    
    xs = [pos[0] for pos in positions]
    ys = [pos[1] for pos in positions]
    
    return (max(xs) - min(xs)) + (max(ys) - min(ys))


def _calculate_rmst(positions: List[Tuple[float, float]]) -> float:
    """计算递归最小生成树长度 (Rectilinear Minimum Spanning Tree)"""
    if len(positions) < 2:
        return 0.0
    
    if len(positions) == 2:
        p1, p2 = positions
        return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])
    
    # 简化版MST计算 - 使用Prim算法
    n = len(positions)
    visited = [False] * n
    min_cost = [float('inf')] * n
    min_cost[0] = 0
    
    total_cost = 0.0
    
    for _ in range(n):
        # 找到最小代价的未访问节点
        u = -1
        for v in range(n):
            if not visited[v] and (u == -1 or min_cost[v] < min_cost[u]):
                u = v
        
        visited[u] = True
        total_cost += min_cost[u]
        
        # 更新相邻节点的代价
        for v in range(n):
            if not visited[v]:
                # 曼哈顿距离
                dist = abs(positions[u][0] - positions[v][0]) + abs(positions[u][1] - positions[v][1])
                min_cost[v] = min(min_cost[v], dist)
    
    return total_cost


def calculate_feedthrough(design: FloorplanDesign) -> int:
    """
    计算Feedthrough数量 - 改进的真实算法
    Calculate feedthrough count using improved real algorithm
    
    Feedthrough是指网线需要穿越其他模块的情况。
    这里使用更准确的算法：对每个网线构建最小生成树，检查连线穿越的模块数量。
    
    Args:
        design: 布图设计
        
    Returns:
        Feedthrough数量
    """
    feedthrough_count = 0
    
    for net in design.nets.values():
        if len(net.pins) < 2:
            continue
        
        # 获取网线连接的Pin位置
        pin_positions = []
        pin_modules = []
        
        for module_name, pin_name in net.pins:
            if module_name in design.modules:
                module = design.modules[module_name]
                pin_modules.append(module)
                
                # 计算实际Pin位置
                if pin_name in module.pins:
                    pin = module.pins[pin_name]
                    pin_x = module.x + pin.x_offset
                    pin_y = module.y + pin.y_offset
                else:
                    pin_x, pin_y = module.get_center()
                
                pin_positions.append((pin_x, pin_y))
        
        if len(pin_positions) < 2:
            continue
        
        # 构建网线的最小生成树（使用Manhattan距离）
        mst_edges = _build_mst_edges(pin_positions)
        
        # 对每条MST边，检查它穿越了多少个模块
        for edge_start, edge_end in mst_edges:
            start_pos = pin_positions[edge_start]
            end_pos = pin_positions[edge_end]
            start_module = pin_modules[edge_start]
            end_module = pin_modules[edge_end]
            
            # 检查这条边穿越了多少个其他模块
            for other_module in design.modules.values():
                if (other_module != start_module and 
                    other_module != end_module and
                    other_module.module_type != ModuleType.TERMINAL):
                    
                    if _line_intersects_module_accurate(start_pos, end_pos, other_module):
                        feedthrough_count += 1
    
    return feedthrough_count


def _build_mst_edges(positions: List[Tuple[float, float]]) -> List[Tuple[int, int]]:
    """
    构建最小生成树的边列表
    Build MST edge list using Prim's algorithm
    """
    if len(positions) < 2:
        return []
    
    n = len(positions)
    visited = [False] * n
    min_cost = [float('inf')] * n
    parent = [-1] * n
    min_cost[0] = 0
    
    edges = []
    
    for _ in range(n):
        # 找到最小代价的未访问节点
        u = -1
        for v in range(n):
            if not visited[v] and (u == -1 or min_cost[v] < min_cost[u]):
                u = v
        
        visited[u] = True
        
        # 添加边（除了根节点）
        if parent[u] != -1:
            edges.append((parent[u], u))
        
        # 更新相邻节点的代价
        for v in range(n):
            if not visited[v]:
                # 曼哈顿距离
                dist = abs(positions[u][0] - positions[v][0]) + abs(positions[u][1] - positions[v][1])
                if dist < min_cost[v]:
                    min_cost[v] = dist
                    parent[v] = u
    
    return edges


def _line_intersects_module_accurate(point1: Tuple[float, float], 
                                   point2: Tuple[float, float], 
                                   module: Module) -> bool:
    """
    精确的线段与模块相交检测
    Accurate line-module intersection detection
    
    使用Manhattan路径（L形路径）检测，更符合实际布线情况
    """
    x1, y1 = point1
    x2, y2 = point2
    
    # 模块边界
    mx1, my1, mx2, my2 = module.get_bounding_box()
    
    # Manhattan路径有两种可能：先水平后垂直，或先垂直后水平
    # 路径1: (x1,y1) -> (x2,y1) -> (x2,y2)
    path1_intersects = (
        _horizontal_line_intersects_rect(x1, x2, y1, mx1, my1, mx2, my2) or
        _vertical_line_intersects_rect(x2, y1, y2, mx1, my1, mx2, my2)
    )
    
    # 路径2: (x1,y1) -> (x1,y2) -> (x2,y2)  
    path2_intersects = (
        _vertical_line_intersects_rect(x1, y1, y2, mx1, my1, mx2, my2) or
        _horizontal_line_intersects_rect(x1, x2, y2, mx1, my1, mx2, my2)
    )
    
    # 如果两种路径都穿越模块，则确实需要feedthrough
    return path1_intersects and path2_intersects


def _horizontal_line_intersects_rect(x1: float, x2: float, y: float,
                                   rect_x1: float, rect_y1: float, 
                                   rect_x2: float, rect_y2: float) -> bool:
    """检查水平线段是否与矩形相交"""
    if y < rect_y1 or y > rect_y2:
        return False
    
    line_left = min(x1, x2)
    line_right = max(x1, x2)
    
    return not (line_right <= rect_x1 or line_left >= rect_x2)


def _vertical_line_intersects_rect(x: float, y1: float, y2: float,
                                 rect_x1: float, rect_y1: float,
                                 rect_x2: float, rect_y2: float) -> bool:
    """检查垂直线段是否与矩形相交"""
    if x < rect_x1 or x > rect_x2:
        return False
    
    line_bottom = min(y1, y2)
    line_top = max(y1, y2)
    
    return not (line_top <= rect_y1 or line_bottom >= rect_y2)


def _line_intersects_module(point1: Tuple[float, float], 
                           point2: Tuple[float, float], 
                           module: Module) -> bool:
    """检查线段是否与模块相交"""
    x1, y1 = point1
    x2, y2 = point2
    
    # 模块边界
    mx1, my1, mx2, my2 = module.get_bounding_box()
    
    # 简化的相交检测 - 检查线段是否穿越模块的边界框
    # 更精确的实现需要使用线段与矩形相交算法
    
    # 如果线段的两个端点都在模块外的同一侧，则不相交
    if (x1 < mx1 and x2 < mx1) or (x1 > mx2 and x2 > mx2):
        return False
    if (y1 < my1 and y2 < my1) or (y1 > my2 and y2 > my2):
        return False
    
    # 简化判断：如果线段跨越模块边界，则认为相交
    x_intersect = (x1 <= mx2 and x2 >= mx1) or (x2 <= mx2 and x1 >= mx1)
    y_intersect = (y1 <= my2 and y2 >= my1) or (y2 <= my2 and y1 >= my1)
    
    return x_intersect and y_intersect


def calculate_whitespace(design: FloorplanDesign) -> float:
    """
    计算空白空间比例
    Calculate whitespace ratio
    
    Args:
        design: 布图设计
        
    Returns:
        空白空间比例 (0-1)
    """
    total_area = calculate_area(design)
    
    if total_area <= 0:
        return 0.0
    
    # 计算所有模块的总面积
    modules_area = sum(module.area for module in design.modules.values()
                      if module.module_type != ModuleType.TERMINAL)
    
    if modules_area >= total_area:
        return 0.0
    
    whitespace_area = total_area - modules_area
    return whitespace_area / total_area


def check_overlaps(design: FloorplanDesign) -> Tuple[float, int]:
    """
    检查模块重叠
    Check module overlaps
    
    Args:
        design: 布图设计
        
    Returns:
        (重叠面积, 重叠对数)
    """
    modules = [m for m in design.modules.values() 
               if m.module_type != ModuleType.TERMINAL]
    
    total_overlap_area = 0.0
    overlap_count = 0
    
    for i in range(len(modules)):
        for j in range(i + 1, len(modules)):
            module1 = modules[i]
            module2 = modules[j]
            
            overlap_area = _calculate_overlap_area(module1, module2)
            if overlap_area > 0:
                total_overlap_area += overlap_area
                overlap_count += 1
    
    return total_overlap_area, overlap_count


def _calculate_overlap_area(module1: Module, module2: Module) -> float:
    """计算两个模块的重叠面积"""
    bbox1 = module1.get_bounding_box()
    bbox2 = module2.get_bounding_box()
    
    # 计算重叠矩形
    left = max(bbox1[0], bbox2[0])
    bottom = max(bbox1[1], bbox2[1])
    right = min(bbox1[2], bbox2[2])
    top = min(bbox1[3], bbox2[3])
    
    if left >= right or bottom >= top:
        return 0.0
    
    return (right - left) * (top - bottom)


def evaluate_floorplan(design: FloorplanDesign) -> EvaluationResult:
    """
    综合评估布图设计
    Comprehensive evaluation of floorplan design
    
    Args:
        design: 布图设计
        
    Returns:
        评估结果
    """
    result = EvaluationResult()
    
    # 基础指标
    result.area = calculate_area(design)
    result.wirelength = calculate_wirelength(design)
    result.feedthrough_count = calculate_feedthrough(design)  # 修复字段名称
    result.whitespace_ratio = calculate_whitespace(design)    # 修复字段名称
    result.hpwl = result.wirelength  # 添加HPWL字段
    
    # 几何信息
    bbox = design.get_bounding_box()
    if bbox[2] > bbox[0] and bbox[3] > bbox[1]:
        result.chip_width = bbox[2] - bbox[0]
        result.chip_height = bbox[3] - bbox[1]
        result.aspect_ratio = result.chip_width / result.chip_height
    
    # 利用率
    result.utilization = design.calculate_utilization()
    
    # 网线统计
    if design.nets:
        net_lengths = []
        for net in design.nets.values():
            if len(net.pins) >= 2:
                pin_positions = []
                for module_name, pin_name in net.pins:
                    if module_name in design.modules:
                        module = design.modules[module_name]
                        
                        # 实际计算Pin位置（考虑Pin偏移）
                        if pin_name in module.pins:
                            pin = module.pins[pin_name]
                            pin_x = module.x + pin.x_offset
                            pin_y = module.y + pin.y_offset
                        else:
                            # 如果找不到具体Pin，使用模块中心
                            pin_x, pin_y = module.get_center()
                        
                        pin_positions.append((pin_x, pin_y))
                
                if len(pin_positions) >= 2:
                    length = _calculate_hpwl(pin_positions)
                    net_lengths.append(length)
        
        if net_lengths:
            result.max_net_length = max(net_lengths)
            result.avg_net_length = sum(net_lengths) / len(net_lengths)
    
    # 重叠检查
    result.overlap_area, result.overlap_count = check_overlaps(design)
    
    return result


# 便捷函数
def quick_evaluate(design: FloorplanDesign, 
                  area_weight: float = 0.5,
                  wirelength_weight: float = 0.5,
                  feedthrough_weight: float = 0.0,
                  whitespace_weight: float = 0.0) -> float:
    """
    快速评估，返回加权代价
    Quick evaluation, returns weighted cost
    """
    result = evaluate_floorplan(design)
    return result.get_weighted_cost(area_weight, wirelength_weight, 
                                   feedthrough_weight, whitespace_weight)


def self_check_metrics() -> bool:
    """
    度量模块自检功能
    Self-check functionality for metrics module
    """
    print("🔧 度量模块 (metrics) 自检")
    
    try:
        # 创建测试设计
        design = FloorplanDesign("test_metrics")
        
        # 添加测试模块
        from ..data.structures import Module, Net, ModuleType
        m1 = Module("m1", ModuleType.SOFT, width=100, height=50, x=0, y=0, area=5000)
        m2 = Module("m2", ModuleType.HARD, width=80, height=60, x=120, y=0, area=4800)
        design.add_module(m1)
        design.add_module(m2)
        
        # 添加测试网线
        net1 = Net("net1", [("m1", "pin1"), ("m2", "pin1")])
        design.add_net(net1)
        
        # 测试各个函数
        area = calculate_area(design)
        wirelength = calculate_wirelength(design)
        feedthrough = calculate_feedthrough(design)
        whitespace = calculate_whitespace(design)
        
        # 验证结果合理性
        if area <= 0:
            print(f"❌ calculate_area() 错误: {area}")
            return False
        
        if wirelength < 0:
            print(f"❌ calculate_wirelength() 错误: {wirelength}")
            return False
        
        if feedthrough < 0:
            print(f"❌ calculate_feedthrough() 错误: {feedthrough}")
            return False
        
        if not 0 <= whitespace <= 1:
            print(f"❌ calculate_whitespace() 错误: {whitespace}")
            return False
        
        print("✅ 度量模块自检通过")
        print(f"   - 面积计算: {area}")
        print(f"   - 线长计算: {wirelength:.2f}")
        print(f"   - Feedthrough计算: {feedthrough}")
        print(f"   - 空白区域: {whitespace:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ 度量模块自检失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def output_metrics_debug_info(design: FloorplanDesign, prefix: str = "  ") -> str:
    """
    输出度量模块的调试信息
    Output debug information for metrics module
    """
    try:
        area = calculate_area(design)
        wirelength = calculate_wirelength(design)
        feedthrough = calculate_feedthrough(design)
        whitespace = calculate_whitespace(design)
        
        debug_info = f"{prefix}=== 度量模块调试信息 ===\n"
        debug_info += f"{prefix}模块总数: {len(design.modules)}\n"
        debug_info += f"{prefix}网线总数: {len(design.nets)}\n"
        debug_info += f"{prefix}总面积: {area:.0f}\n"
        debug_info += f"{prefix}线长估算: {wirelength:.2f}\n"
        debug_info += f"{prefix}Feedthrough数量: {feedthrough}\n"
        debug_info += f"{prefix}空白区域比例: {whitespace:.3f}\n"
        
        # 模块统计
        from ..data.structures import ModuleType
        soft_count = sum(1 for m in design.modules.values() if m.module_type == ModuleType.SOFT)
        hard_count = sum(1 for m in design.modules.values() if m.module_type == ModuleType.HARD)
        terminal_count = sum(1 for m in design.modules.values() if m.module_type == ModuleType.TERMINAL)
        
        debug_info += f"{prefix}模块类型分布:\n"
        debug_info += f"{prefix}  - 软模块: {soft_count}\n"
        debug_info += f"{prefix}  - 硬模块: {hard_count}\n"
        debug_info += f"{prefix}  - 端口: {terminal_count}\n"
        
        return debug_info
        
    except Exception as e:
        return f"{prefix}度量模块调试信息获取失败: {e}\n"


# 导出主要函数和类
__all__ = [
    'EvaluationResult',
    'FloorplanEvaluator',
    'evaluate_floorplan',
    'calculate_area',
    'calculate_wirelength',
    'calculate_feedthrough',
    'calculate_whitespace',
    'check_overlaps',
    'quick_evaluate',
    'self_check_metrics',
    'output_metrics_debug_info'
] 