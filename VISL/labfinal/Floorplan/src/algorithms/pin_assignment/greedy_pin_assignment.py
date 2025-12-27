#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
贪心法Pin分配算法
基于贪心策略的Pin分配实现
"""

import math
import time
from typing import List, Tuple, Dict, Set, Optional
from dataclasses import dataclass

from ...data.structures import FloorplanDesign, Module, ModuleType


@dataclass 
class GreedyPinAssignmentConfig:
    """贪心Pin分配配置"""
    expansion_ratio: float = 1.2
    verbose: bool = False


class GreedyPinAssignment:
    """贪心法Pin分配器"""
    
    def __init__(self, expansion_ratio: float = 1.2, verbose: bool = False):
        self.expansion_ratio = expansion_ratio
        self.verbose = verbose
        
        # 性能统计
        self.assignment_count = 0
        self.total_assignment_time = 0.0
    
    def assign_pins(self, design: FloorplanDesign) -> FloorplanDesign:
        """执行Pin分配"""
        start_time = time.time()
        
        # 获取需要布置的Pin
        pins = [m for m in design.modules.values() if m.module_type == ModuleType.TERMINAL]
        
        if not pins:
            return design

        # 计算当前芯片尺寸
        chip_width, chip_height = self._calculate_chip_size(design)

        # 检查周长是否足够容纳所有Pin
        perimeter = 2 * (int(chip_width) + int(chip_height))

        # 如果Pin数量超过可用位置，扩展芯片
        if len(pins) > perimeter:
            chip_width, chip_height = self._expand_chip_for_pins(chip_width, chip_height, len(pins))
        
        # 更新设计的芯片尺寸为整数
        design.chip_width = int(chip_width)
        design.chip_height = int(chip_height)
        
        # 获取Pin网络信息
        pin_networks = self._get_pin_networks(design)
        
        # 贪心分配Pin
        if hasattr(design, '_layout_bounds'):
            min_x, min_y, max_x, max_y = design._layout_bounds
            self._assign_pins_greedy_with_bounds(pins, design, min_x, min_y, max_x, max_y, pin_networks)
        else:
            # 后备方案
            self._assign_pins_greedy(pins, design, int(chip_width), int(chip_height), pin_networks)
        
        # 更新统计信息
        self.assignment_count += 1
        self.total_assignment_time += time.time() - start_time
        
        return design
    
    def _assign_pins_greedy_with_bounds(self, pins: List[Module], design: FloorplanDesign, 
                                       min_x: float, min_y: float, max_x: float, max_y: float,
                                       pin_networks: Dict[str, List[str]]):
        """使用实际布局边界进行贪心分配Pin"""
        # 生成基于实际边界的边缘位置
        edge_positions = self._generate_edge_positions_with_bounds(min_x, min_y, max_x, max_y)
        used_positions = set()
        
        # 按网络参与度排序Pin
        sorted_pins = sorted(pins, key=lambda p: len(pin_networks.get(p.name, [])), reverse=True)
        
        # 为每个Pin找到最佳位置
        for pin in sorted_pins:
            best_position = self._find_best_position_with_bounds(pin, design, edge_positions, used_positions, pin_networks)
            
            if best_position:
                pin.set_position(float(best_position[0]), float(best_position[1]))
                used_positions.add(best_position)
    
    def _generate_edge_positions_with_bounds(self, min_x: float, min_y: float, max_x: float, max_y: float) -> List[Tuple[int, int]]:
        """基于实际边界生成边缘位置"""
        positions = []
        
        width = int(max_x - min_x)
        height = int(max_y - min_y)
        
        # 下边缘
        for x in range(width + 1):
            positions.append((int(min_x + x), int(min_y)))
        
        # 右边缘
        for y in range(1, height):
            positions.append((int(max_x), int(min_y + y)))
        
        # 上边缘
        for x in range(width, -1, -1):
            positions.append((int(min_x + x), int(max_y)))
        
        # 左边缘
        for y in range(height - 1, 0, -1):
            positions.append((int(min_x), int(min_y + y)))
        
        return positions
    
    def _find_best_position_with_bounds(self, pin: Module, design: FloorplanDesign, 
                                       edge_positions: List[Tuple[int, int]], 
                                       used_positions: Set[Tuple[int, int]],
                                       pin_networks: Dict[str, List[str]]) -> Optional[Tuple[int, int]]:
        """为Pin找到最佳位置（使用实际边界）"""
        available_positions = [pos for pos in edge_positions if pos not in used_positions]
        
        if not available_positions:
            return None
        
        # 计算Pin的重心
        gravity_center = self._calculate_pin_gravity_center(pin, design, pin_networks)
        
        # 找到离重心最近的位置
        best_position = None
        min_distance = float('inf')
        
        for pos in available_positions:
            distance = math.sqrt((pos[0] - gravity_center[0]) ** 2 + (pos[1] - gravity_center[1]) ** 2)
            if distance < min_distance:
                min_distance = distance
                best_position = pos
        
        return best_position
    
    def _get_pin_networks(self, design: FloorplanDesign) -> Dict[str, List[str]]:
        """获取Pin的网络连接信息"""
        pin_networks = {}
        
        # 初始化Pin网络字典
        for module in design.modules.values():
            if module.module_type == ModuleType.TERMINAL:
                pin_networks[module.name] = []
        
        # 遍历所有网络，建立Pin到网络的映射
        for net_name, net in design.nets.items():
            for module_name, pin_name in net.pins:
                if module_name in pin_networks:
                    pin_networks[module_name].append(net_name)
        
        return pin_networks
    
    def _assign_pins_greedy(self, pins: List[Module], design: FloorplanDesign, 
                           chip_width: int, chip_height: int, pin_networks: Dict[str, List[str]]):
        """贪心分配Pin"""
        # 生成边缘位置
        edge_positions = self._generate_edge_positions(chip_width, chip_height)
        used_positions = set()
        
        # 按网络参与度排序Pin
        sorted_pins = sorted(pins, key=lambda p: len(pin_networks.get(p.name, [])), reverse=True)
        
        # 为每个Pin找到最佳位置
        for pin in sorted_pins:
            best_position = self._find_best_position(pin, design, edge_positions, used_positions, pin_networks)
            
            if best_position:
                pin.set_position(float(best_position[0]), float(best_position[1]))
                used_positions.add(best_position)
    
    def _find_best_position(self, pin: Module, design: FloorplanDesign, 
                           edge_positions: List[Tuple[int, int]], 
                           used_positions: Set[Tuple[int, int]],
                           pin_networks: Dict[str, List[str]]) -> Optional[Tuple[int, int]]:
        """为Pin找到最佳位置"""
        available_positions = [pos for pos in edge_positions if pos not in used_positions]
        
        if not available_positions:
            return None
        
        # 计算Pin的重心
        gravity_center = self._calculate_pin_gravity_center(pin, design, pin_networks)
        
        # 找到离重心最近的位置
        best_position = None
        min_distance = float('inf')
        
        for pos in available_positions:
            distance = math.sqrt((pos[0] - gravity_center[0]) ** 2 + (pos[1] - gravity_center[1]) ** 2)
            if distance < min_distance:
                min_distance = distance
                best_position = pos
        
        return best_position
    
    def _calculate_pin_gravity_center(self, pin: Module, design: FloorplanDesign, 
                                     pin_networks: Dict[str, List[str]]) -> Tuple[float, float]:
        """计算Pin的重心位置"""
        connected_nets = pin_networks.get(pin.name, [])
        
        if not connected_nets:
            return (design.chip_width / 2, design.chip_height / 2)
        
        # 收集所有连接的模块位置
        connected_positions = []
        
        for net_name in connected_nets:
            if net_name in design.nets:
                net = design.nets[net_name]
                for module_name, pin_name in net.pins:
                    if module_name != pin.name and module_name in design.modules:
                        module = design.modules[module_name]
                        if module.module_type != ModuleType.TERMINAL:
                            center = module.get_center()
                            connected_positions.append(center)
        
        if not connected_positions:
            return (design.chip_width / 2, design.chip_height / 2)
        
        # 计算重心
        avg_x = sum(pos[0] for pos in connected_positions) / len(connected_positions)
        avg_y = sum(pos[1] for pos in connected_positions) / len(connected_positions)
        
        return (avg_x, avg_y)
    
    def _calculate_chip_size(self, design: FloorplanDesign) -> Tuple[float, float]:
        """计算基于宏模块的芯片尺寸"""
        macro_modules = [m for m in design.modules.values() 
                        if m.module_type in [ModuleType.SOFT, ModuleType.HARD]]
        
        if not macro_modules:
            return 100.0, 100.0
        
        min_x = min(m.x for m in macro_modules)
        min_y = min(m.y for m in macro_modules)
        max_x = max(m.x + m.width for m in macro_modules)
        max_y = max(m.y + m.height for m in macro_modules)
        
        # 芯片边界应该是包围所有宏模块的最小矩形
        chip_width = math.ceil(max_x)
        chip_height = math.ceil(max_y)
        
        # 存储边界信息供Pin分配使用
        design._layout_bounds = (min_x, min_y, max_x, max_y)
        
        return max(chip_width, 10), max(chip_height, 10)
    
    def _expand_chip_for_pins(self, width: float, height: float, pin_count: int) -> Tuple[float, float]:
        """扩展芯片以容纳Pin"""
        current_perimeter = 2 * (int(width) + int(height))
        
        while current_perimeter < pin_count:
            width *= self.expansion_ratio
            height *= self.expansion_ratio
            current_perimeter = 2 * (int(width) + int(height))
        
        return math.ceil(width), math.ceil(height)
    
    def _generate_edge_positions(self, width: int, height: int) -> List[Tuple[int, int]]:
        """生成边缘位置"""
        positions = []
        
        # 下边缘
        for x in range(width + 1):
            positions.append((x, 0))
        
        # 右边缘
        for y in range(1, height):
            positions.append((width, y))
        
        # 上边缘
        for x in range(width, -1, -1):
            positions.append((x, height))
        
        # 左边缘
        for y in range(height - 1, 0, -1):
            positions.append((0, y))
        
        return positions
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        avg_time = self.total_assignment_time / max(1, self.assignment_count)
        
        return {
            'algorithm': 'GreedyPinAssignment',
            'assignment_count': self.assignment_count,
            'total_time': self.total_assignment_time,
            'avg_time_per_assignment': avg_time,
            'expansion_ratio': self.expansion_ratio
        } 