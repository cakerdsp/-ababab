#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
线长计算模块 - Wirelength Calculation Module

实现各种线长估算算法，包括HPWL、RMST等
Implements various wirelength estimation algorithms including HPWL, RMST, etc.
"""

import numpy as np
import math
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from ..data.structures import FloorplanDesign, Net, Module


@dataclass
class WirelengthResult:
    """线长计算结果 - Wirelength calculation result"""
    total_hpwl: float
    total_rmst: float
    net_details: Dict[str, Dict[str, float]]
    avg_wirelength: float
    max_wirelength: float
    critical_nets: List[str]


def calculate_hpwl(design: FloorplanDesign) -> float:
    """
    计算半周长线长 (Half-Perimeter Wirelength)
    Calculate Half-Perimeter Wirelength
    
    Args:
        design: 布图设计
        
    Returns:
        总HPWL值
    """
    total_hpwl = 0.0
    
    for net in design.nets.values():
        if len(net.pins) < 2:
            continue
            
        # 获取所有引脚位置
        pin_positions = []
        for module_name, pin_name in net.pins:
            module = design.get_module(module_name)
            if module is None:
                continue
                
            # 计算引脚的绝对位置
            if pin_name in module.pins:
                pin_pos = module.get_pin_position(pin_name)
                if pin_pos:
                    pin_positions.append(pin_pos)
            else:
                # 如果没有具体引脚信息，使用模块中心
                center = module.get_center()
                pin_positions.append(center)
        
        if len(pin_positions) < 2:
            continue
            
        # 计算边界框
        xs = [pos[0] for pos in pin_positions]
        ys = [pos[1] for pos in pin_positions]
        
        hpwl = (max(xs) - min(xs)) + (max(ys) - min(ys))
        total_hpwl += hpwl * net.weight
    
    return total_hpwl


def calculate_rmst(design: FloorplanDesign) -> float:
    """
    计算矩形最小生成树线长 (Rectilinear Minimum Spanning Tree)
    Calculate Rectilinear Minimum Spanning Tree wirelength
    
    Args:
        design: 布图设计
        
    Returns:
        总RMST值
    """
    total_rmst = 0.0
    
    for net in design.nets.values():
        if len(net.pins) < 2:
            continue
            
        # 获取所有引脚位置
        pin_positions = []
        for module_name, pin_name in net.pins:
            module = design.get_module(module_name)
            if module is None:
                continue
                
            if pin_name in module.pins:
                pin_pos = module.get_pin_position(pin_name)
                if pin_pos:
                    pin_positions.append(pin_pos)
            else:
                center = module.get_center()
                pin_positions.append(center)
        
        if len(pin_positions) < 2:
            continue
            
        # 简化的RMST计算（Prim算法）
        rmst_length = _calculate_mst_manhattan(pin_positions)
        total_rmst += rmst_length * net.weight
    
    return total_rmst


def _calculate_mst_manhattan(points: List[Tuple[float, float]]) -> float:
    """
    使用Manhattan距离计算最小生成树
    Calculate MST using Manhattan distance
    """
    if len(points) <= 1:
        return 0.0
    
    n = len(points)
    visited = [False] * n
    min_cost = [float('inf')] * n
    min_cost[0] = 0
    
    total_cost = 0.0
    
    for _ in range(n):
        # 找到未访问的最小成本节点
        u = -1
        for v in range(n):
            if not visited[v] and (u == -1 or min_cost[v] < min_cost[u]):
                u = v
        
        visited[u] = True
        total_cost += min_cost[u]
        
        # 更新相邻节点的成本
        for v in range(n):
            if not visited[v]:
                # Manhattan距离
                dist = abs(points[u][0] - points[v][0]) + abs(points[u][1] - points[v][1])
                if dist < min_cost[v]:
                    min_cost[v] = dist
    
    return total_cost


def calculate_steiner_wirelength(design: FloorplanDesign) -> float:
    """
    计算Steiner树线长估算
    Calculate Steiner tree wirelength estimation
    
    使用HPWL的0.8倍作为Steiner树的近似
    Use 0.8 * HPWL as Steiner tree approximation
    """
    hpwl = calculate_hpwl(design)
    return hpwl * 0.8  # 经验系数


class WirelengthCalculator:
    """
    线长计算器类 - Wirelength Calculator Class
    
    提供多种线长计算方法和详细分析
    Provides various wirelength calculation methods and detailed analysis
    """
    
    def __init__(self, method: str = 'hpwl'):
        """
        初始化线长计算器
        
        Args:
            method: 计算方法 ('hpwl', 'rmst', 'steiner')
        """
        self.method = method
        self.supported_methods = ['hpwl', 'rmst', 'steiner']
        
        if method not in self.supported_methods:
            raise ValueError(f"Unsupported method: {method}. Supported: {self.supported_methods}")
    
    def calculate(self, design: FloorplanDesign) -> float:
        """计算总线长"""
        if self.method == 'hpwl':
            return calculate_hpwl(design)
        elif self.method == 'rmst':
            return calculate_rmst(design)
        elif self.method == 'steiner':
            return calculate_steiner_wirelength(design)
        else:
            raise ValueError(f"Unknown method: {self.method}")
    
    def detailed_analysis(self, design: FloorplanDesign) -> WirelengthResult:
        """
        详细的线长分析
        Detailed wirelength analysis
        
        Returns:
            WirelengthResult: 详细的分析结果
        """
        hpwl = calculate_hpwl(design)
        rmst = calculate_rmst(design)
        
        net_details = {}
        net_lengths = []
        
        for net in design.nets.values():
            if len(net.pins) < 2:
                continue
                
            # 计算单个网线的HPWL
            net_hpwl = self._calculate_net_hpwl(design, net)
            net_details[net.name] = {
                'hpwl': net_hpwl,
                'weight': net.weight,
                'degree': net.get_degree(),
                'weighted_length': net_hpwl * net.weight
            }
            net_lengths.append(net_hpwl)
        
        # 找出关键网线（长度最大的前10%）
        if net_lengths:
            threshold = np.percentile(net_lengths, 90)
            critical_nets = [name for name, details in net_details.items() 
                           if details['hpwl'] >= threshold]
        else:
            critical_nets = []
        
        return WirelengthResult(
            total_hpwl=hpwl,
            total_rmst=rmst,
            net_details=net_details,
            avg_wirelength=np.mean(net_lengths) if net_lengths else 0.0,
            max_wirelength=max(net_lengths) if net_lengths else 0.0,
            critical_nets=critical_nets
        )
    
    def _calculate_net_hpwl(self, design: FloorplanDesign, net: Net) -> float:
        """计算单个网线的HPWL"""
        if len(net.pins) < 2:
            return 0.0
            
        pin_positions = []
        for module_name, pin_name in net.pins:
            module = design.get_module(module_name)
            if module is None:
                continue
                
            if pin_name in module.pins:
                pin_pos = module.get_pin_position(pin_name)
                if pin_pos:
                    pin_positions.append(pin_pos)
            else:
                center = module.get_center()
                pin_positions.append(center)
        
        if len(pin_positions) < 2:
            return 0.0
            
        xs = [pos[0] for pos in pin_positions]
        ys = [pos[1] for pos in pin_positions]
        
        return (max(xs) - min(xs)) + (max(ys) - min(ys))
    
    def get_congestion_map(self, design: FloorplanDesign, grid_size: int = 50) -> np.ndarray:
        """
        生成拥塞热力图
        Generate congestion heatmap
        
        Args:
            design: 布图设计
            grid_size: 网格大小
            
        Returns:
            拥塞矩阵
        """
        bbox = design.get_bounding_box()
        if bbox[2] <= bbox[0] or bbox[3] <= bbox[1]:
            return np.zeros((grid_size, grid_size))
        
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        
        congestion_map = np.zeros((grid_size, grid_size))
        
        for net in design.nets.values():
            if len(net.pins) < 2:
                continue
                
            # 获取网线的边界框
            pin_positions = []
            for module_name, pin_name in net.pins:
                module = design.get_module(module_name)
                if module is None:
                    continue
                    
                center = module.get_center()
                pin_positions.append(center)
            
            if len(pin_positions) < 2:
                continue
                
            xs = [pos[0] for pos in pin_positions]
            ys = [pos[1] for pos in pin_positions]
            
            # 将网线影响区域映射到网格
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            
            # 转换为网格坐标
            grid_min_x = int((min_x - bbox[0]) / width * grid_size)
            grid_max_x = int((max_x - bbox[0]) / width * grid_size)
            grid_min_y = int((min_y - bbox[1]) / height * grid_size)
            grid_max_y = int((max_y - bbox[1]) / height * grid_size)
            
            # 限制在有效范围内
            grid_min_x = max(0, min(grid_min_x, grid_size - 1))
            grid_max_x = max(0, min(grid_max_x, grid_size - 1))
            grid_min_y = max(0, min(grid_min_y, grid_size - 1))
            grid_max_y = max(0, min(grid_max_y, grid_size - 1))
            
            # 增加拥塞值
            for i in range(grid_min_y, grid_max_y + 1):
                for j in range(grid_min_x, grid_max_x + 1):
                    congestion_map[i, j] += net.weight
        
        return congestion_map


def self_check_wirelength() -> bool:
    """
    线长模块自检功能
    Self-check functionality for wirelength module
    """
    print("🔧 线长模块 (wirelength) 自检")
    
    try:
        # 创建测试设计
        from ..data.structures import FloorplanDesign, Module, Net, ModuleType
        
        design = FloorplanDesign("test_wirelength")
        
        # 添加测试模块
        m1 = Module("m1", ModuleType.SOFT, width=100, height=100, x=0, y=0, area=10000)
        m2 = Module("m2", ModuleType.SOFT, width=100, height=100, x=200, y=0, area=10000)
        m3 = Module("m3", ModuleType.SOFT, width=100, height=100, x=400, y=0, area=10000)
        
        design.add_module(m1)
        design.add_module(m2)
        design.add_module(m3)
        
        # 添加测试网线
        net1 = Net("net1", [("m1", "pin1"), ("m2", "pin1")])  # 应该是200的距离
        net2 = Net("net2", [("m1", "pin2"), ("m3", "pin2")])  # 应该是400的距离
        net3 = Net("net3", [("m1", "pin3"), ("m2", "pin3"), ("m3", "pin3")])  # 多引脚网线
        
        design.add_net(net1)
        design.add_net(net2)
        design.add_net(net3)
        
        # 测试各个函数
        hpwl = calculate_hpwl(design)
        rmst = calculate_rmst(design)
        steiner = calculate_steiner_wirelength(design)
        
        # 验证基本合理性
        if hpwl < 0:
            print(f"❌ calculate_hpwl() 错误: 负值 {hpwl}")
            return False
        
        if rmst < 0:
            print(f"❌ calculate_rmst() 错误: 负值 {rmst}")
            return False
        
        if steiner < 0:
            print(f"❌ calculate_steiner_wirelength() 错误: 负值 {steiner}")
            return False
        
        # 验证关系：通常HPWL >= RMST >= Steiner
        if hpwl < rmst * 0.8:  # 允许一些误差
            print(f"❌ 线长关系异常: HPWL({hpwl}) < RMST({rmst})")
            return False
        
        # 测试WirelengthCalculator
        calculator = WirelengthCalculator(method='hpwl')
        calc_hpwl = calculator.calculate(design)
        
        if abs(calc_hpwl - hpwl) > 1e-6:
            print(f"❌ WirelengthCalculator 不一致: {calc_hpwl} vs {hpwl}")
            return False
        
        # 测试详细分析
        result = calculator.detailed_analysis(design)
        if not isinstance(result, WirelengthResult):
            print(f"❌ detailed_analysis() 返回类型错误")
            return False
        
        # 测试拥塞地图
        congestion_map = calculator.get_congestion_map(design)
        if congestion_map.shape != (50, 50):
            print(f"❌ get_congestion_map() 尺寸错误: {congestion_map.shape}")
            return False
        
        print("✅ 线长模块自检通过")
        print(f"   - HPWL: {hpwl:.2f}")
        print(f"   - RMST: {rmst:.2f}")
        print(f"   - Steiner: {steiner:.2f}")
        print(f"   - 网线数量: {len(result.net_details)}")
        print(f"   - 关键网线: {len(result.critical_nets)}")
        print(f"   - 拥塞地图: {congestion_map.shape}, 最大值: {congestion_map.max():.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ 线长模块自检失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def output_wirelength_debug_info(design: FloorplanDesign, prefix: str = "  ") -> str:
    """
    输出线长模块的调试信息
    Output debug information for wirelength module
    """
    try:
        hpwl = calculate_hpwl(design)
        rmst = calculate_rmst(design)
        steiner = calculate_steiner_wirelength(design)
        
        calculator = WirelengthCalculator(method='hpwl')
        result = calculator.detailed_analysis(design)
        congestion_map = calculator.get_congestion_map(design)
        
        debug_info = f"{prefix}=== 线长模块调试信息 ===\n"
        debug_info += f"{prefix}线长估算:\n"
        debug_info += f"{prefix}  - HPWL: {hpwl:.2f}\n"
        debug_info += f"{prefix}  - RMST: {rmst:.2f}\n"
        debug_info += f"{prefix}  - Steiner: {steiner:.2f}\n"
        debug_info += f"{prefix}网线统计:\n"
        debug_info += f"{prefix}  - 总网线数: {len(design.nets)}\n"
        debug_info += f"{prefix}  - 有效网线数: {len(result.net_details)}\n"
        debug_info += f"{prefix}  - 关键网线数: {len(result.critical_nets)}\n"
        debug_info += f"{prefix}  - 平均线长: {result.avg_wirelength:.2f}\n"
        debug_info += f"{prefix}  - 最大线长: {result.max_wirelength:.2f}\n"
        debug_info += f"{prefix}拥塞分析:\n"
        debug_info += f"{prefix}  - 网格大小: {congestion_map.shape}\n"
        debug_info += f"{prefix}  - 最大拥塞: {congestion_map.max():.2f}\n"
        debug_info += f"{prefix}  - 平均拥塞: {congestion_map.mean():.2f}\n"
        debug_info += f"{prefix}  - 高拥塞区域: {(congestion_map > congestion_map.mean() + congestion_map.std()).sum()}\n"
        
        # 列出关键网线
        if result.critical_nets:
            debug_info += f"{prefix}关键网线: {', '.join(result.critical_nets[:5])}"
            if len(result.critical_nets) > 5:
                debug_info += f" (共 {len(result.critical_nets)} 个)"
            debug_info += "\n"
        
        return debug_info
        
    except Exception as e:
        return f"{prefix}线长模块调试信息获取失败: {e}\n"


# 导出函数和类
__all__ = [
    'calculate_hpwl',
    'calculate_rmst',
    'calculate_steiner_wirelength',
    'WirelengthCalculator',
    'WirelengthResult',
    'self_check_wirelength',
    'output_wirelength_debug_info'
] 